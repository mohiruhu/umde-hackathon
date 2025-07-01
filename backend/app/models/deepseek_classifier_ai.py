import requests
import logging
import json
from typing import Optional, Dict, Any, cast
from backend.app.config.config_loader_ai import HF_API_TOKEN, HF_MODEL_DEEPSEEK

logger = logging.getLogger(__name__)
logger.propagate = True

HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL_DEEPSEEK}"
headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}


def layoutlm_extract_rule(rule_text: str, layout_data: str) -> Optional[Dict[str, Any]]:
    """
    Extracts structured CMS rule data from a TRC rule chunk using LayoutLM via Hugging Face API.
    Returns a dictionary with fields like rule_id, field, condition, etc., or None on failure.
    """

    prompt = f"""You are an expert in CMS TRC rule analysis. Read the rule below and extract the following fields:
- rule_id: The TRC code (e.g., TRC003)
- field: The CMS field being validated
- condition: What must be true about the field
- is_required: true/false depending on whether the field must be present
- regex_pattern: any expected format (e.g., MMDDCCYY)
- value_set_name: if the field must belong to a set
- dependent_field: any field this one depends on
- conditional_on_presence_of: only if rule applies when another field is present

Additionally, you will also consider the **layout** of the document in your extraction process (positions and spatial context).

TRC Rule: {rule_text}
Layout Information: {layout_data}
"""

    payload: Dict[str, Any] = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.2,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and data and isinstance(data[0], dict):
            generated_text = data[0].get("generated_text") #type: ignore
            if isinstance(generated_text, str):
                stripped: str = generated_text.strip()
                if stripped.startswith("{"):
                    try:
                        parsed = json.loads(stripped)
                        if isinstance(parsed, dict):
                            # Help Pylance with type: cast to Dict[str, Any]
                            parsed = cast(Dict[str, Any], parsed)
                            parsed["classification_source"] = "layoutlm"
                            parsed["extraction_chain"] = ["layoutlm"]
                            return parsed
                        logger.warning("Parsed JSON is not a dict.")
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON decode failed: {e}")
                else:
                    logger.warning("LayoutLM response did not start with JSON.")
            else:
                logger.warning("LayoutLM response missing 'generated_text' as string.")
        else:
            logger.warning("LayoutLM response format was invalid.")

    except Exception as e:
        logger.warning(f"LayoutLM rule extraction failed: {e}")

    return None

def deepseek_extract_rule(rule_text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts structured CMS rule data from a TRC rule chunk using DeepSeek via Hugging Face API.
    Returns a dictionary with fields like rule_id, field, condition, etc., or None on failure.
    """

    prompt = f"""You are an expert in CMS TRC rule analysis. Read the rule below and extract the following fields:
- rule_id: The TRC code (e.g., TRC003)
- field: The CMS field being validated
- condition: What must be true about the field
- is_required: true/false depending on whether the field must be present
- regex_pattern: any expected format (e.g., MMDDCCYY)
- value_set_name: if the field must belong to a set
- dependent_field: any field this one depends on
- conditional_on_presence_of: only if rule applies when another field is present

Respond in JSON format.

TRC Rule: {rule_text}
"""

    payload: Dict[str, Any] = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.2,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and data and isinstance(data[0], dict):
            generated_text = data[0].get("generated_text") #type: ignore
            if isinstance(generated_text, str):
                stripped: str = generated_text.strip()
                if stripped.startswith("{"):
                    try:
                        parsed = json.loads(stripped)
                        if isinstance(parsed, dict):
                            # Help Pylance with type: cast to Dict[str, Any]
                            parsed = cast(Dict[str, Any], parsed)
                            parsed["classification_source"] = "deepseek"
                            parsed["extraction_chain"] = ["deepseek"]
                            return parsed
                        logger.warning("Parsed JSON is not a dict.")
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON decode failed: {e}")
                else:
                    logger.warning("DeepSeek response did not start with JSON.")
            else:
                logger.warning("DeepSeek response missing 'generated_text' as string.")
        else:
            logger.warning("DeepSeek response format was invalid.")

    except Exception as e:
        logger.warning(f"DeepSeek rule extraction failed: {e}")

    return None