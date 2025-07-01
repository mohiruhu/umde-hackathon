# config_loader_ai.py
import os
from dotenv import load_dotenv

# ------------------- ENV LOADER -------------------
load_dotenv()

# ------------------- CONFIG ACCESS -------------------

def get_config(key: str, default: str = "") -> str:
    return os.getenv(key, default)

# Shortcut access for known keys
HF_API_TOKEN = get_config("HF_API_TOKEN")

# Not using now, until we  have a paid DeepSeek account, ignore the model name here
HF_MODEL_DEEPSEEK = get_config("HF_MODEL_DEEPSEEK", "impira/layoutlm-document-qa") 

HF_MODEL_ZEPHYR = get_config("HF_MODEL_ZEPHYR", "HuggingFaceH4/zephyr-7b-beta")
OLLAMA_MODEL = get_config("OLLAMA_MODEL", "gemma:2b")
OLLAMA_ENDPOINT = get_config("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
MODEL_DIR_FLAN_T5 = get_config("MODEL_DIR_FLAN_T5", "./models/flan-t5-cms")


#https://api-inference.huggingface.co/models/impira/layoutlm-document-qa


def safe_float(value: str, fallback: float) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        print(f"Warning: Invalid float value '{value}', using fallback {fallback}.")
        return fallback


# Optional: Confidence thresholds
THRESHOLDS = {
    "deepseek": safe_float(get_config("DEEPSEEK_CONFIDENCE_THRESHOLD", "0.8"), 0.8),
    "zephyr": safe_float(get_config("ZEPHYR_CONFIDENCE_THRESHOLD", "0.8"), 0.8),
    "local_llm": safe_float(get_config("LOCAL_LLM_CONFIDENCE_THRESHOLD", "0.75"), 0.75),
    "flan_t5": safe_float(get_config("FLAN_T5_CONFIDENCE_THRESHOLD", "0.0"), 0.0),
}


