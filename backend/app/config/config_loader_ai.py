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
HF_MODEL = get_config("HF_MODEL", "deepseek-ai/DeepSeek-R1-0528")
OLLAMA_MODEL = get_config("OLLAMA_MODEL", "mistral")
OLLAMA_ENDPOINT = get_config("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
MODEL_DIR_FLAN_T5 = get_config("MODEL_DIR_FLAN_T5", "./models/flan-t5-cms")

def safe_float(value: str, fallback: float) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        print(f"Warning: Invalid float value '{value}', using fallback {fallback}.")
        return fallback


# Optional: Confidence thresholds
THRESHOLDS = {
    "deepseek": safe_float(get_config("DEEPSEEK_CONFIDENCE_THRESHOLD", "0.8"), 0.8),
    "local_llm": safe_float(get_config("LOCAL_LLM_CONFIDENCE_THRESHOLD", "0.75"), 0.75),
    "flan_t5": safe_float(get_config("FLAN_T5_CONFIDENCE_THRESHOLD", "0.0"), 0.0),
}


