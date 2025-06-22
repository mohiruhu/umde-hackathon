from typing import List, Dict, Any, Optional, Literal
from collections import Counter
import logging
import json
import yaml
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from jsonschema import validate

from backend.app.models.layer_classifier import infer_layer_with_metadata
from backend.app.models.model_orchestrator_ai import extract_best_rule_with_fallback
from backend.app.parsers.cms_schema_inferencer import CMSSchemaInferencer
from backend.app.parsers.rule_chunk_parser import parse_pdf_rules, parse_xlsx_rules

# Setup module-specific logger to logs/cms_parser.log
log_dir = Path(__file__).resolve().parents[3] / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "cms_parser.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(module)s | %(message)s",  # << enhanced format
    handlers=[
        logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger("cms_parser")

async def process_chunk(
    chunk: Dict[str, Any],
    schema_infer: CMSSchemaInferencer
) -> Optional[Dict[str, Any]]:
    text = chunk.get("definition") or chunk.get("raw_row", "")
    try:
        # Note: If extract_best_rule_with_fallback is not async, we can wrap it
        result = extract_best_rule_with_fallback(text)
        if not result:
            return None

        rule_struct = result.get("label", {})
        source_model = result.get("source", "unknown")
        extraction_chain = rule_struct.get("extraction_chain", [])
        if source_model not in extraction_chain:
            extraction_chain.append(source_model)

        backup = schema_infer.infer(text, chunk.get("rule_id", "unknown"))
        layer, reason, inferred_tags = infer_layer_with_metadata(chunk.get("rule_id", ""), text)

        return {
            "rule": {
                "rule_id": chunk.get("rule_id", rule_struct.get("rule_id")),
                "title": rule_struct.get("title", backup.get("title")),
                "short_definition": rule_struct.get("short_definition", text[:80]),
                "definition": rule_struct.get("definition", text),
                "field": rule_struct.get("field", backup.get("field")),
                "plan_action": rule_struct.get("plan_action", "review manually"),
                "layer": str(layer),
                "tags": sorted(set(inferred_tags)),
                "severity": rule_struct.get("severity", backup.get("severity")),
                "confidence": rule_struct.get("confidence", "partial"),
                "extraction_chain": extraction_chain,
                "doc_link": chunk.get("doc", ""),
                "source_page": chunk.get("meta", {}).get("page"),
                "classification_source": source_model,
                "layer_reason": reason,
                "source_type": chunk.get("source_type"),
                "raw_row": text,
                "manual_review_required": rule_struct.get("fallback_used", False)
            },
            "trace": {
                "rule_id": chunk.get("rule_id", rule_struct.get("rule_id")),
                "source_model": source_model,
                "extraction_chain": extraction_chain,
                "confidence": rule_struct.get("confidence", ""),
                "fallback_used": rule_struct.get("fallback_used", False),
                "source_page": chunk.get("meta", {}).get("page"),
                "doc": chunk.get("doc"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    except Exception as e:
        logger.warning(f"Failed to extract rule from chunk {chunk.get('rule_id', '')}: {e}")
        return None


async def extract_chunks_and_generate_rules(
    source_path: str,
    filetype: Literal["pdf", "xlsx"],
    output_dir: Path,
    start_page: int = 1,
    end_page: Optional[int] = None,
    manual_review_output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Extract CMS rules from PDF or XLSX source using AI enrichment pipeline.
    
    Args:
        source_path: File path to the CMS source document.
        filetype: 'pdf' or 'xlsx'.
        output_dir: Directory path for output files and trace logs.
        start_page: Starting page (PDF only).
        end_page: Ending page (PDF only).
        manual_review_output_path: Optional path to save rules needing review.

    Returns:
        A list of fully extracted and enriched rule dictionaries.
    """
    path = Path(source_path)
    chunks: List[Dict[str, Any]] = []
    extracted_rules: List[Dict[str, Any]] = []
    skipped_chunks: List[Dict[str, Any]] = []
    source_counter: Counter[str] = Counter()
    schema_infer = CMSSchemaInferencer()
    trace_log: List[Dict[str, Any]] = []

    try:
        if filetype == "pdf":
            chunks = parse_pdf_rules(str(path), start_page, end_page or 2000)
        elif filetype == "xlsx":
            chunks = parse_xlsx_rules(str(path))
        else:
            raise ValueError(f"Unsupported file type: {filetype}")
    except Exception as e:
        logger.error(f"Failed to parse {filetype.upper()} file: {e}")
        return []

    logger.info(f"Loaded {len(chunks)} rule chunks from {filetype.upper()} file: {path.name}")

    # ================================
    # BEGIN PARALLELISM + BATCH PROCESSING
    # ================================
    # Create async tasks for parallel processing
    tasks = [process_chunk(chunk, schema_infer) for chunk in chunks]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    extracted_rules = []
    trace_log = []
    skipped_chunks = []

    for result, chunk in zip(results, chunks):
        if isinstance(result, Exception):
            logger.warning(f"Exception processing chunk {chunk.get('rule_id', '')}: {result}")
            skipped_chunks.append(chunk)
        elif result is None:
            skipped_chunks.append(chunk)
        elif isinstance(result, dict) and "rule" in result and "trace" in result:
            extracted_rules.append(result["rule"])
            trace_log.append(result["trace"])
            source_counter[chunk.get("source_type", "unknown")] += 1
        else:
            logger.warning(f"Unexpected result type for chunk {chunk.get('rule_id', '')}: {type(result)}")
            skipped_chunks.append(chunk)

    logger.info("Extraction Summary")
    logger.info(f"Total extracted rules: {len(extracted_rules)}")
    logger.info(f"Total skipped chunks: {len(skipped_chunks)}")
    for source, count in source_counter.items():
        logger.info(f"Extracted from {source.upper()}: {count} rules")

    if manual_review_output_path:
        to_review = [r for r in extracted_rules if r.get("manual_review_required")]
        write_manual_review_log(to_review, manual_review_output_path)
        logger.info(f"Manual review log written to: {manual_review_output_path}")

    trace_path = output_dir / "trace"
    trace_path.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    trace_file = trace_path / f"validation_trace_{ts}.json"

    with open(trace_file, "w", encoding="utf-8") as f:
        json.dump(trace_log, f, indent=2, ensure_ascii=False)

        logger.info(f"Validation trace log written to {trace_file}")


    
    return extracted_rules

def write_trc_rules_with_history(rules: List[Dict[str, Any]], output_dir: Path) -> None:
    """
    Writes trc_rules.json and a timestamped JSON history file to the extractedrules folder.
    """
    try:
        # Ensure paths
        schema_path = Path(__file__).resolve().parents[3] / "schemas" / "minimal_rule_schema.json"
        with open(schema_path, "r") as f:
            minimal_schema = json.load(f)
        
        main_path = output_dir / "trc_rules.json"
        history_dir = output_dir / "extractedrules"
        history_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        history_path = history_dir / f"rules_{timestamp}.json"

        # Extract minimal rules
        minimal_rules = [
            {
                "rule_id": r["rule_id"],
                "title": r["title"],
                "short_definition": r["short_definition"],
                "definition": r["definition"],
                "field": r["field"],
                "plan_action": r["plan_action"],
                "layer": r["layer"],
                "tags": r["tags"],
                "severity": r["severity"],
                "doc_link": r["doc_link"],
                "meta": {
                    "source_page": r["source_page"],
                    "classification_source": r["classification_source"],
                    "layer_reason": r["layer_reason"],
                    "raw_row": r["raw_row"],
                    "confidence": r.get("confidence", ""),
                    "extraction_chain": r.get("extraction_chain", [])
                }
            }
            for r in rules
        ]

        validate(instance=minimal_rules, schema=minimal_schema)

        # Write main file
        with main_path.open("w", encoding="utf-8") as f:
            json.dump(minimal_rules, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved trc_rules.json to {main_path}")

        # Write versioned snapshot
        with history_path.open("w", encoding="utf-8") as f:
            json.dump(minimal_rules, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved historical rule snapshot to {history_path}")

    except Exception as e:
        logger.error(f"Failed to write TRC rule JSON files: {e}")

def write_cms_rules_yml(rules: List[Dict[str, Any]], output_path: Path) -> None:
    try:
        enabled_rules = sorted(r["rule_id"] for r in rules)
        tags = {
            r["rule_id"]: r["tags"]
            for r in rules
            if r.get("tags")
        }

        yml_data = {
            "enabled_rules": enabled_rules,
            "excluded_trcs": [],
            "tags": tags
        }

        validate_cms_yml_structure(yml_data)

        with output_path.open("w", encoding="utf-8") as f:
            yaml.dump(yml_data, f, sort_keys=False)

        logger.info(f"Saved cms_rules.yml to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write cms_rules.yml: {e}")


def write_manual_review_log(skipped_rules: List[Dict[str, Any]], output_path: Path) -> None:
    """Writes a log of skipped rules to a file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(skipped_rules, f, indent=4)
        logger.info(f"Manual review log written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write manual review log: {e}")


def validate_cms_yml_structure(data: Dict[str, Any]) -> None:
    if "enabled_rules" not in data or not isinstance(data["enabled_rules"], list):
        raise ValueError("cms_rules.yml must include 'enabled_rules' as a list")

    if "tags" not in data or not isinstance(data["tags"], dict):
        raise ValueError("cms_rules.yml must include 'tags' as a dict")

    if "excluded_trcs" in data and not isinstance(data["excluded_trcs"], list):
        raise ValueError("'excluded_trcs' must be a list if provided")

def extract_chunks_and_generate_rules_sync(
    source_path: str,
    filetype: Literal["pdf", "xlsx"],
    output_dir: Path,
    start_page: int = 1,
    end_page: Optional[int] = None,
    manual_review_output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for the async extract_chunks_and_generate_rules function.
    This allows the function to be called from non-async contexts.
    """
    return asyncio.run(extract_chunks_and_generate_rules(
        source_path=source_path,
        filetype=filetype,
        output_dir=output_dir,
        start_page=start_page,
        end_page=end_page,
        manual_review_output_path=manual_review_output_path
    ))

