import logging
from typing import Optional, Dict, Any, Callable

from backend.app.models import (
    deepseek_classifier_ai,
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
DEFAULT_CONFIDENCE_THRESHOLDS = {
    "deepseek": 0.8,
    "local_llm": 0.75,
    "flan_t5": 0.0  # Always accept if something is returned
}

DEFAULT_RETRY_LIMIT = 1
DEFAULT_MODEL_SEQUENCE = ["deepseek", "local_llm", "flan_t5", "non_ai"]

# ------------------- WRAPPERS -------------------
def wrap_deepseek(text: str) -> Optional[Dict[str, Any]]:
    label = deepseek_classifier_ai.classify_with_deepseek(text)
    return {"label": label, "confidence": 1.0} if label else None

def wrap_non_ai(text: str) -> Optional[Dict[str, Any]]:
    label = non_ai_classifier.extract_rule_keyword_fallback(text)
    return {"label": label, "confidence": "n/a"} if label else None

# ------------------- MODEL REGISTRY -------------------
MODEL_REGISTRY: Dict[str, Callable[[str], Optional[Dict[str, Any]]]] = {
    "deepseek": wrap_deepseek,
    "local_llm": local_llm_ai.extract_with_confidence,
    "flan_t5": flan_t5_handler_ai.extract_with_confidence,
    "non_ai": wrap_non_ai,
}

def get_runtime_config() -> Dict[str, Any]:
    # Placeholder for UI-driven runtime config override
    return {
        "confidence_thresholds": DEFAULT_CONFIDENCE_THRESHOLDS,
        "retry_limit": DEFAULT_RETRY_LIMIT,
        "model_sequence": DEFAULT_MODEL_SEQUENCE
    }

# ------------------- MAIN FALLBACK ORCHESTRATOR -------------------
def extract_best_rule_with_fallback(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        logger.warning("No input provided to rule extraction pipeline.")
        return None

    config = get_runtime_config()
    thresholds = config["confidence_thresholds"]
    retry_limit = config["retry_limit"]
    model_sequence = config["model_sequence"]

    for model_name in model_sequence:
        model_fn = MODEL_REGISTRY.get(model_name)
        if not model_fn:
            logger.warning(f"Model '{model_name}' is not recognized in registry. Skipping.")
            continue

        for attempt in range(retry_limit):
            try:
                logger.info(f"Attempting model '{model_name}' (attempt {attempt + 1})")
                result = model_fn(text)
                if not result:
                    logger.warning(f"Model '{model_name}' returned no result.")
                    break

                label = result.get("label")
                confidence = result.get("confidence")
                threshold = thresholds.get(model_name, 0.0)

                if label:
                    if confidence == "n/a" or not isinstance(confidence, (int, float, str)):
                        logger.info(f"Model '{model_name}' returned result without numeric confidence. Accepting.")
                        return {"label": label, "source": model_name}
                    try:
                        if float(confidence) >= threshold:
                            logger.info(f"Model '{model_name}' passed confidence threshold ({confidence} >= {threshold}).")
                            return {"label": label, "source": model_name}
                        else:
                            logger.info(f"Model '{model_name}' below confidence threshold ({confidence} < {threshold}). Skipping.")
                    except Exception:
                        logger.warning(f"Model '{model_name}' returned unparseable confidence value: {confidence}")
            except Exception as e:
                logger.exception(f"Model '{model_name}' failed on attempt {attempt + 1}: {e}")
                break

    logger.warning("All model layers failed or returned insufficient confidence.")
    return None



# ------------------- TEST ENTRY -------------------
if __name__ == "__main__":
    sample_text = "Reject with TRC008 if the beneficiary identifier is not found."
    result = extract_best_rule_with_fallback(sample_text)
    print("Final extracted rule:", result)
