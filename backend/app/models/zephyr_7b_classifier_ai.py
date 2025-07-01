import requests
import logging
import json
from typing import Optional, Dict, Any, cast
from backend.app.config.config_loader_ai import HF_API_TOKEN, HF_MODEL_ZEPHYR

logger = logging.getLogger(__name__)
logger.propagate = True

HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL_ZEPHYR}"
headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

def zephyr7B_extract_rule(rule_text: str, layout_data: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Extracts structured CMS rule data from a TRC rule chunk using Zephyr 7B via Hugging Face API.
    Returns a dictionary with fields like rule_id, field, condition, etc., or None on failure.
    """
    
    # Improvement 1: Ensure consistent prompt format for Zephyr 7B
    # The prompt explicitly asks the model to extract rule fields

    layout_info = layout_data if layout_data else "No layout data available"
    prompt = f"""You are an expert in CMS TRC rule analysis. Read the rule below and extract the following fields:
- rule_id: The TRC code (e.g., TRC003)
- field: The CMS field being validated
- condition: What must be true about the field
- is_required: true/false depending on whether the field must be present
- regex_pattern: any expected format (e.g., MM/DD/YYYY)
- value_set_name: if the field must belong to a set
- dependent_field: any field this one depends on
- conditional_on_presence_of: only if rule applies when another field is present

Additionally, you will also consider the **layout** of the document in your extraction process (positions and spatial context).

TRC Rule: {rule_text}
Layout Information: {layout_info}
"""
    
    # Improvement 2: Ensure that layout data (bounding boxes, positions) are passed correctly
    # The layout data is passed as part of the input, so that Zephyr 7B can process layout-aware rule extraction.
    
    payload: Dict[str, Any] = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,  # Ensure the model has enough tokens for long rules
            "temperature": 0.2,  # Controlled output for rule extraction
            "return_full_text": False
        }
    }

    try:
        # Sending the request to the Zephyr 7B model API
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        # Improvement 3: Handling the model response and ensuring it's structured as expected
        data = response.json()

        # If the response contains a list and the first item has the expected dictionary structure
        if isinstance(data, list) and data and isinstance(data[0], dict):
            generated_text = data[0].get("generated_text")  # Get the generated text from Zephyr 7B # type: ignore
            if isinstance(generated_text, str):
                stripped: str = generated_text.strip()
                
                # Improvement 4: Ensure that the JSON is properly parsed
                if stripped.startswith("{"):
                    try:
                        parsed = json.loads(stripped)
                        if isinstance(parsed, dict):
                            # Improvement 5: Adding necessary metadata fields for consistency
                            parsed = cast(Dict[str, Any], parsed)
                            parsed["classification_source"] = "zephyr"
                            parsed["extraction_chain"] = ["zephyr"]
                            parsed["confidence"] = "high"
                            parsed["label"] = parsed.get("rule_id", "unknown")
                            return parsed
                        logger.warning("Parsed JSON is not a dict.")
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON decode failed: {e}")
                else:
                    logger.warning("Zephyr 7B response did not start with valid JSON.")
            else:
                logger.warning("Zephyr 7B response missing 'generated_text' as string.")
        else:
            logger.warning("Zephyr 7B response format was invalid.")
    
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout: Zephyr 7B model didn't respond within the allowed time.")
    except Exception as e:
        # Improved error handling and logging
        logger.warning(f"Zephyr 7B rule extraction failed: {e}")
    
    return None
