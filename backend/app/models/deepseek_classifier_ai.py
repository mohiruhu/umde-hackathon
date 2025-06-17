import requests
import logging
from typing import Optional
from backend.app.config.config_loader_ai import HF_API_TOKEN, HF_MODEL

logger = logging.getLogger(__name__)
logger.propagate = True

HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}


def classify_with_deepseek(description: str) -> Optional[str]:
    """
    Classifies a TRC rule description using Hugging Face-hosted DeepSeek model.
    Returns 'include', 'exclude', or None if the model fails or returns invalid output.
    """
    logger.info("⚙️ DeepSeek module initialized")

    prompt = (
        "You are a CMS validation expert. Determine if the following TRC rule should be used "
        "for data validation or skipped as informational.\n\n"
        f"TRC Description: \"{description}\"\n\n"
        "Respond with one word only: INCLUDE or EXCLUDE."
    )

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 20,
            "temperature": 0.0,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        logger.debug(f"[DeepSeek] Raw response: {data}")

        if isinstance(data, list) and "generated_text" in data[0]:
            output = data[0]["generated_text"].strip().upper()  # type: ignore
            logger.info(f"🧠 DeepSeek classified: '{description}' → {output}")

            if "INCLUDE" in output:
                return "include"
            elif "EXCLUDE" in output:
                return "exclude"
            else:
                logger.warning(f"[DeepSeek] Unexpected classification label: {output}")
        else:
            logger.warning(f"[DeepSeek] Invalid response format: {data}")

    except Exception as e:
        logger.warning(f"DeepSeek classification failed: {e}")

    return None
