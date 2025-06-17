from typing import List, Dict, Any, Optional
import pdfplumber
import logging
import json
import yaml
from pathlib import Path
from backend.app.parsers.description_cleaner import clean_description
from backend.app.models.layer_classifier import infer_layer_with_metadata
from backend.app.models.model_orchestrator_ai import extract_best_rule_with_fallback
from backend.app.parsers.trc_or_rule_identifier import detect_trc_id_from_text
from backend.app.parsers.cms_schema_inferencer import CMSSchemaInferencer

# Setup module-specific logger to logs/cms_parser.log
log_dir = Path(__file__).resolve().parents[3] / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "cms_parser.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ],
    force=True
)
logger = logging.getLogger("cms_parser")

FORCED_HIGH_RISK = {
    "TRC004", "TRC006", "TRC007", "TRC008", "TRC021", "TRC232", "TRC205", "TRC310", "TRC258", "TRC257"
}

MEMBER_KEYWORDS = {"BENE", "NAME", "DOB", "ID", "ADDRESS", "GENDER", "SSN"}

def extract_targeted_trcs_from_pdf(
    pdf_path: str,
    start_page: int,
    end_page: int,
    mode: str = "inferencer",
    manual_review_output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    extracted: List[Dict[str, Any]] = []
    skipped_rules: List[Dict[str, Any]] = []
    seen_trcs: set[str] = set()

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_number in range(start_page, end_page + 1):
                logger.info(f"\nStarting Page {page_number}")
                try:
                    tables = pdf.pages[page_number - 1].extract_tables()
                    logger.info(f"Found {len(tables)} tables on page {page_number}")
                except Exception as err:
                    logger.warning(f"Page {page_number} skipped: {err}")
                    continue

                for table in tables:
                    for row in table:
                        if not row or all(c is None or str(c).strip() == '' for c in row):
                            continue

                        row_text = " ".join(str(c).strip() for c in row if c)
                        trc_id = detect_trc_id_from_text(row_text)
                        if not trc_id or trc_id in seen_trcs:
                            continue

                        logger.info(f"Start TRC {trc_id}")
                        seen_trcs.add(trc_id)
                        desc = row_text

                        try:
                            result = extract_best_rule_with_fallback(desc)
                            if result:
                                rule_struct = result["label"]
                                source = result["source"]
                                logger.info(f"Model '{source}' selected for TRC {trc_id}")
                            else:
                                logger.warning(f"Rule extraction failed for TRC {trc_id}")
                                skipped_rules.append({
                                    "trc_id": trc_id,
                                    "source_page": page_number,
                                    "classification_source": "model",
                                    "extraction_chain": [],
                                    "raw_row": desc
                                })
                                continue

                            if "informational" in desc.lower():
                                logger.info(f"Skipping informational TRC {trc_id}")
                                continue

                            extraction_chain = rule_struct.get("extraction_chain", [])
                            if mode in {"llm", "full"}:
                                extraction_chain.append(source)

                            if mode == "full" and extraction_chain and extraction_chain[-1] != "inferencer":
                                filtered_row = [str(cell) for cell in row if cell is not None]
                                backup = CMSSchemaInferencer().infer(filtered_row, trc_id)
                                for key in ["field", "severity", "title", "short_definition"]:
                                    if not rule_struct.get(key) or rule_struct[key] in {"unknown", "", None}:
                                        backup_value = backup.get(key)
                                        if backup_value is not None:
                                            rule_struct[key] = backup_value

                            definition = clean_description(rule_struct.get("definition", desc) or desc)
                            layer, reason, inferred_tags = infer_layer_with_metadata(trc_id, definition)

                            tags: List[str] = []
                            if any(k in desc.upper() for k in MEMBER_KEYWORDS):
                                tags.append("member")
                            if trc_id in FORCED_HIGH_RISK:
                                tags.append("high-risk")
                            tags = sorted(set(tags + inferred_tags))

                            rule: dict[str, str | Any | int | Dict[str, str]] = {
                                "rule_id": trc_id,
                                "title": rule_struct.get("title", trc_id),
                                "short_definition": rule_struct.get("short_definition", desc[:80]),
                                "definition": definition,
                                "field": rule_struct.get("field", "unknown"),
                                "plan_action": rule_struct.get("plan_action", "review manually"),
                                "layer": str(layer),
                                "tags": tags,
                                "severity": rule_struct.get("severity", "U"),
                                "confidence": rule_struct.get("confidence", "partial"),
                                "extraction_chain": extraction_chain,
                                "doc_link": f"https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page={page_number}",
                                "source_page": page_number,
                                "classification_source": source,
                                "layer_reason": reason,
                                "raw_row": row_text
                            }

                            logger.info(f"Included TRC {trc_id} via {extraction_chain}")
                            extracted.append(rule)

                        except Exception as e:
                            logger.warning(f"Failed to extract TRC {trc_id} on page {page_number}: {e}")

    except Exception as e:
        logger.error(f"Failed to open or process PDF: {e}")

    logger.info("\nExtraction Summary:")
    logger.info(f"Total extracted TRCs: {len(extracted)}")
    if manual_review_output_path:
        write_manual_review_log(skipped_rules, manual_review_output_path)
    return extracted

def write_trc_rules_json(rules: List[Dict[str, Any]], output_path: Path) -> None:
    try:
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
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(minimal_rules, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved trc_rules.json to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write trc_rules.json: {e}")

def write_cms_rules_yml(rules: List[Dict[str, Any]], output_path: Path) -> None:
    try:
        enabled_trcs = [r["rule_id"] for r in rules]
        tags: Dict[str, List[str]] = {r["rule_id"]: r.get("tags", []) for r in rules}

        yml_data = {
            "enabled_trcs": sorted(enabled_trcs),
            "excluded_trcs": [],
            "tags": tags
        }

        with output_path.open("w", encoding="utf-8") as f:
            yaml.dump(yml_data, f, sort_keys=False)

        logger.info(f"Saved cms_rules.yml to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write cms_rules.yml: {e}")

def write_manual_review_log(skipped: List[Dict[str, Any]], output_path: Path) -> None:
    try:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(skipped, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved manual review log to {output_path} with {len(skipped)} skipped rules")
    except Exception as e:
        logger.error(f"Failed to write manual review log: {e}")
