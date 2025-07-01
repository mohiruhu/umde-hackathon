import yaml
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FIXED: Correct path to config directory
UMDE_YML_PATH = Path(__file__).resolve().parent.parent / "config" / "umde_input_fields.yml"

REQUIRED_STRUCTURE = {
    "member_fields": list,
    "edps_high_risk_fields": list
}

def load_umde_input_fields() -> Dict[str, Any]:
    try:
        with UMDE_YML_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            validate_umde_yml(data)
            return data
    except Exception as e:
        logger.error(f"Failed to load umde_input_fields.yml: {e}")
        raise


def validate_umde_yml(data: Dict[str, Any]) -> None:
    for key, expected_type in REQUIRED_STRUCTURE.items():
        if key not in data:
            raise ValueError(f"Missing required key: {key}")
        if not isinstance(data[key], expected_type):
            raise TypeError(f"{key} must be of type {expected_type.__name__}, got {type(data[key]).__name__}")

def update_member_fields_from_rules(rules: List[Dict[str, Any]]) -> None:
    try:
        config = load_umde_input_fields()
        existing = set(config.get("member_fields", []))
        
        # FIXED: Handle None values properly - filter out None before using string methods
        new_fields = {
            field for r in rules
            if (field := r.get("field")) is not None and field.startswith("member_")
        }
        
        # FIXED: Type is now clearly set[str], no None values
        updated = sorted(existing.union(new_fields))
        config["member_fields"] = updated

        with UMDE_YML_PATH.open("w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, sort_keys=False)

        print(f"✅ Updated member_fields in {UMDE_YML_PATH.name} with {len(new_fields - existing)} new entries.")

    except Exception as e:
        raise RuntimeError(f"Failed to update umde_input_fields.yml: {e}")
