import logging
from typing import Optional, Dict, Any, Callable

from backend.app.models import (
    deepseek_classifier_ai,
    zephyr_7b_classifier_ai,
    local_llm_ai,
    flan_t5_handler_ai,
    non_ai_classifier
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ------------------- CONFIGURATION (Default + UI-Override Support) -------------------
DEFAULT_CONFIDENCE_THRESHOLDS: Dict[str, float] = {
    "zephyr": 0.8,
    "deepseek": 0.8,
    "local_llm": 0.75,
    "flan_t5": 0.0  # Always accept if something is returned
}

DEFAULT_RETRY_LIMIT: int = 1
DEFAULT_MODEL_SEQUENCE: list[str] = ["zephyr", "local_llm", "flan_t5", "non_ai"]

# ------------------- MODEL INTERFACES -------------------
def wrap_zephyr(text: str) -> Optional[Dict[str, Any]]:
    """Wrapper for Zephyr 7B to normalize function signature"""
    return zephyr_7b_classifier_ai.zephyr7B_extract_rule(text, layout_data=None)

def wrap_deepseek(text: str) -> Optional[Dict[str, Any]]:
    """Wrapper for DeepSeek to ensure consistent function signature"""
    return deepseek_classifier_ai.deepseek_extract_rule(text)

def wrap_local_llm(text: str) -> Optional[Dict[str, Any]]:
    """Wrapper for Local LLM to ensure consistent function signature"""
    return local_llm_ai.extract_with_local_llm(text)

def wrap_flan_t5(text: str) -> Optional[Dict[str, Any]]:
    """Wrapper for FLAN-T5 to ensure consistent function signature"""
    return flan_t5_handler_ai.extract_with_confidence(text)

def wrap_non_ai(text: str) -> Optional[Dict[str, Any]]:
    """Wrapper for non-AI classifier to ensure consistent return format"""
    result = non_ai_classifier.extract_rule(text)
    if result:
        return result
    return None

# ------------------- MODEL REGISTRY -------------------
# FIX: All functions now have the same signature: (str) -> Optional[Dict[str, Any]]
MODEL_REGISTRY: Dict[str, Callable[[str], Optional[Dict[str, Any]]]] = {
    "zephyr": wrap_zephyr,
    "deepseek": wrap_deepseek,
    "local_llm": wrap_local_llm,
    "flan_t5": wrap_flan_t5,
    "non_ai": wrap_non_ai
}

def get_runtime_config() -> Dict[str, Any]:
    """Placeholder for UI-driven runtime config override"""
    return {
        "confidence_thresholds": DEFAULT_CONFIDENCE_THRESHOLDS,
        "retry_limit": DEFAULT_RETRY_LIMIT,
        "model_sequence": DEFAULT_MODEL_SEQUENCE
    }

# ------------------- MAIN FALLBACK ORCHESTRATOR -------------------
def extract_rule_with_fallback(rule_text: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to extract a CMS rule from the input text using the configured model sequence.
    Falls back through models until one succeeds or all fail.
    No retries. Each model is called once.
    """
    config = get_runtime_config()
    thresholds: Dict[str, float] = config.get("confidence_thresholds", {})
    model_sequence: list[str] = config.get("model_sequence", [])

    for model_name in model_sequence:
        model_fn: Optional[Callable[[str], Optional[Dict[str, Any]]]] = MODEL_REGISTRY.get(model_name)
        if not model_fn:
            logger.warning(f"Model '{model_name}' is not registered.")
            continue

        try:
            logger.info(f"🔍 Trying model '{model_name}' (single attempt)")
            result = model_fn(rule_text)

            if not result:
                logger.info(f"Model '{model_name}' returned no result.")
                continue

            label: Optional[str] = result.get("label") or result.get("rule_id")
            confidence = result.get("confidence", "n/a")
            threshold: float = thresholds.get(model_name, 0.0)

            logger.info(f"Model '{model_name}' → label: {label}, confidence: {confidence}")

            if not label:
                logger.info(f"No label extracted by model '{model_name}'. Skipping.")
                continue

            # Accept if confidence is missing or not numeric
            if confidence == "n/a" or not isinstance(confidence, (int, float, str)):
                result["source"] = model_name
                return result

            try:
                confidence_float = float(confidence)
                if confidence_float >= threshold:
                    result["source"] = model_name
                    return result
                else:
                    logger.info(f"Model '{model_name}' below confidence threshold ({confidence_float} < {threshold}). Skipping.")
            except (ValueError, TypeError):
                logger.warning(f"Invalid confidence format from model '{model_name}': {confidence}")
                continue

        except Exception as e:
            logger.warning(f"Model '{model_name}' failed: {e}")
            continue

    logger.warning("🚨 All model layers failed or did not meet thresholds.")
    return None

# ------------------- TEST ENTRY -------------------
if __name__ == "__main__":
    sample_text = "Reject with TRC008 if the beneficiary identifier is not found."
    result = extract_rule_with_fallback(sample_text)
    print("Final extracted rule:", result)
