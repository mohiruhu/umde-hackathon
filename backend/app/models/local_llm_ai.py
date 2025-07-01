import logging
import json
import requests
import re
from typing import Optional, Dict, Any
from backend.app.config.config_loader_ai import OLLAMA_ENDPOINT, OLLAMA_MODEL

logger = logging.getLogger("local_llm_structure_fallback_ai")


def extract_with_local_llm(text_block: str) -> Optional[Dict[str, Any]]:
    """
    Extracts structured CMS rule using a local Ollama-hosted model (e.g., Mistral).
    Returns: JSON-compatible Python dictionary with rule_id, title, short_definition, etc.
    """
    logger.info("🌐 Calling Ollama model locally for rule structure extraction")

    prompt = (
        "You are a CMS compliance rules expert. Analyze the following validation rule text and return a structured JSON object "
        "with the following fields:\n"
        "- rule_id\n"
        "- title\n"
        "- short_definition\n"
        "- definition\n"
        "- field\n"
        "- severity (e.g., R, U, I)\n"
        "- plan_action (e.g., 'reject record', 'flag for manual review')\n\n"
        "If no rule_id is explicitly available, use 'GENERIC_RULE_001'.\n"
        f"Rule Text:\n{text_block}\n\n"
        "Respond only with valid JSON."
    )

    try:
        response = requests.post(OLLAMA_ENDPOINT, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=60)
        response.raise_for_status()
        result = response.json().get("response", "").strip()

        logger.debug(f"📥 Ollama raw response: {result}")

        json_start = result.find("{")
        if json_start != -1:
            json_block = result[json_start:]
            json_block = re.sub(r"\\n", " ", json_block)
            json_block = re.sub(r"\\t", " ", json_block)
            json_block = re.sub(r"\\r", "", json_block)
            json_block = json_block.encode("utf-8").decode("unicode_escape")

            parsed = json.loads(json_block)
            parsed["confidence"] = "medium"
            parsed["label"] = parsed.get("rule_id", "GENERIC_RULE_001") + ": " + parsed.get("short_definition", "")
            logger.info(f"✅ Ollama extracted rule: {parsed.get('label', 'UNKNOWN')}")
            return parsed
        else:
            logger.warning("⚠️ No JSON structure detected in Ollama response.")

    except Exception as e:
        logger.warning(f"❌ Ollama inference failed: {e}")

    return None

def mistral_extract_rule(text_block: str) -> Optional[Dict[str, Any]]:
    """
    Wrapper for extract_with_local_llm that standardizes output for rule fallback orchestration.
    """
    result = extract_with_local_llm(text_block)
    if result:
        result["classification_source"] = "mistral"
        result["extraction_chain"] = ["mistral"]
        return result
    return None

def extract_with_confidence(text_block: str) -> Optional[Dict[str, str]]:
    result = extract_with_local_llm(text_block)
    if result and "label" in result:
        return {"label": result["label"], "confidence": result.get("confidence", "medium")}
    return None
