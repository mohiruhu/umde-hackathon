import logging
from typing import Optional
from backend.app.models import (
    deepseek_classifier_ai,
    local_llm_ai,
    flan_t5_handler_ai,
    non_ai_classifier
)

# ------------------- LOGGING -------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ------------------- DYNAMIC CONFIG -------------------
MODEL_SEQUENCE = [
    "deepseek",
    "local_llm",
    "flan_t5",
    "non_ai"
]

CONFIDENCE_THRESHOLDS = {
    "deepseek": 0.8,
    "local_llm": 0.75,
    "flan_t5": 0.0  # always accept if available
}

# ------------------- ORCHESTRATOR -------------------
def extract_best_rule(text: str) -> Optional[str]:
    """
    Orchestrates multi-layered CMS rule extraction.
    Order determined by MODEL_SEQUENCE config.
    """
    if not text:
        logger.warning("Empty input provided to orchestrator.")
        return None

    for model_name in MODEL_SEQUENCE:
        try:
            logger.info(f"Attempting model: {model_name}")
            if model_name == "deepseek":
                result = deepseek_classifier_ai.extract_with_confidence(text)  # type: ignore
            elif model_name == "local_llm":
                result = local_llm_ai.extract_with_confidence(text)  # type: ignore
            elif model_name == "flan_t5":
                result = flan_t5_handler_ai.extract_with_confidence(text)  # type: ignore
            elif model_name == "non_ai":
                result = {"label": non_ai_classifier.extract_rule_keyword_fallback(text), "confidence": "n/a"}
            else:
                logger.warning(f"Unknown model: {model_name}")
                continue

            if result and result.get("label"):  # type: ignore
                confidence = result.get("confidence")  # type: ignore
                threshold = CONFIDENCE_THRESHOLDS.get(model_name, 0.0)

                if confidence == "n/a" or isinstance(confidence, str):
                    logger.info(f"Model '{model_name}' returned result without numeric confidence. Accepting.")
                    return result["label"]  # type: ignore

                try:
                    if confidence is not None and float(confidence) >= threshold:  # type: ignore
                        logger.info(f"Model '{model_name}' passed confidence threshold.")
                        return result["label"]  # type: ignore
                except ValueError:
                    logger.warning(f"Could not interpret confidence from {model_name}: {confidence}")
                    continue
        except Exception as e:
            logger.exception(f"Model '{model_name}' failed: {e}")

    logger.warning("All model layers failed or returned insufficient confidence.")
    return None


# ------------------- TEST ENTRY -------------------
if __name__ == "__main__":
    sample_text = "Reject with TRC008 if the beneficiary identifier is not found."
    result = extract_best_rule(sample_text)
    print("Final extracted rule:", result)
