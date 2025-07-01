import logging,json
from functools import lru_cache
from typing import Optional, Tuple, Any, Dict

import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration  # type: ignore
from backend.app.config.config_loader_ai import MODEL_DIR_FLAN_T5

# ------------------- CONFIG -------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MAX_INPUT_LENGTH = 512
MAX_OUTPUT_LENGTH = 128

# ------------------- LOGGING -------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ------------------- LOADER -------------------
@lru_cache(maxsize=1)
def load_model() -> Tuple[Any, Any]:  # type: ignore
    try:
        logger.info("Loading FLAN-T5 tokenizer and model from %s", MODEL_DIR_FLAN_T5)
        tokenizer = T5Tokenizer.from_pretrained(MODEL_DIR_FLAN_T5)  # type: ignore
        model = T5ForConditionalGeneration.from_pretrained(MODEL_DIR_FLAN_T5)  # type: ignore
        model.to(DEVICE)  # type: ignore
        model.eval()
        return tokenizer, model  # type: ignore
    except Exception as e:
        logger.exception("Failed to load FLAN-T5 model: %s", str(e))
        raise

# ------------------- INFERENCE -------------------
def extract_rule(text: str, max_input_length: int = MAX_INPUT_LENGTH, max_output_length: int = MAX_OUTPUT_LENGTH) -> Optional[str]:
    result = extract_with_confidence(text)
    return result["label"] if result else None

def flan_extract_rule(text: str) -> Optional[Dict[str, Any]]:
    """
    Structured rule extractor for fallback orchestration using FLAN-T5.
    The model is expected to return a JSON string. We parse and validate it.
    """
    try:
        tokenizer, model = load_model()

        logger.info("🧠 Running FLAN-T5 structured rule extraction")
        prompt = (
            "Extract the following fields from the CMS validation rule:\n"
            "- rule_id\n"
            "- field\n"
            "- condition\n"
            "- is_required\n"
            "- regex_pattern\n"
            "- value_set_name\n"
            "- dependent_field\n"
            "- conditional_on_presence_of\n\n"
            f"TRC Rule: {text}\n\n"
            "Respond only in valid JSON."
        )

        input_ids = tokenizer.encode(
            prompt,
            return_tensors="pt",
            max_length=MAX_INPUT_LENGTH,
            truncation=True
        ).to(DEVICE)

        output_ids = model.generate(
            input_ids,
            max_length=MAX_OUTPUT_LENGTH,
            num_beams=4,
            early_stopping=True
        )

        decoded = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
        logger.debug(f"FLAN raw decoded: {decoded}")

        if decoded.startswith("{"):
            parsed = json.loads(decoded)
            if isinstance(parsed, dict):
                parsed["classification_source"] = "flan"
                parsed["extraction_chain"] = ["flan"]
                return parsed #type: ignore
        logger.warning("FLAN output was not a valid JSON object.")
    except Exception as e:
        logger.warning(f"FLAN structured extraction failed: {e}")
    return None


def extract_with_confidence(text: str, max_input_length: int = MAX_INPUT_LENGTH, max_output_length: int = MAX_OUTPUT_LENGTH) -> Optional[Dict[str, str]]:
    if not text:
        logger.warning("Invalid input provided to extract_with_confidence: %s", text)
        return None

    try:
        tokenizer, model = load_model()  # type: ignore

        logger.debug("Tokenizing input text...")
        input_ids = tokenizer.encode(  # type: ignore
            text,
            return_tensors="pt",
            max_length=max_input_length,
            truncation=True
        ).to(DEVICE)

        logger.debug("Generating output from FLAN-T5 model...")
        output_ids = model.generate(  # type: ignore
            input_ids,
            max_length=max_output_length,
            num_beams=4,
            early_stopping=True
        )

        decoded_output = tokenizer.decode(output_ids[0], skip_special_tokens=True)  # type: ignore
        logger.info("FLAN-T5 output: %s", decoded_output)  # type: ignore
        return {"label": decoded_output, "confidence": "high"}  # consistent with orchestrator

    except Exception as e:
        logger.exception("FLAN-T5 inference failed: %s", str(e))
        return None

# ------------------- TEST ENTRY -------------------
if __name__ == "__main__":
    sample_input = "Extract and classify the TRC rule from this CMS description: 'Reject with TRC008 if the beneficiary identifier is not found.'"
    print("Predicted rule:", extract_with_confidence(sample_input))
