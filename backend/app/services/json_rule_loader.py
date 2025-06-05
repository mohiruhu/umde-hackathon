import json
from typing import List, Dict, Any

from rules.base import ValidationRule  # ✅ Required for subclassing

class JSONRule(ValidationRule):
    def __init__(self, rule_dict: Dict[str, Any]):
        self.rule_id = rule_dict.get("rule_id", "")
        self.name = rule_dict.get("name", "")
        self.description = rule_dict.get("description", "")
        self.layer = rule_dict.get("layer", 1)
        self.cms_code = rule_dict.get("cms_code", "")

    def validate(self, row: Dict[str, Any]) -> List[str]:
        # Placeholder: JSON-based rules can define behavior later
        return []

def load_rules_from_json(path: str) -> List[JSONRule]:
    with open(path, "r", encoding="utf-8") as f:
        rule_dicts = json.load(f)

    rules = [JSONRule(rule) for rule in rule_dicts]
    return rules
