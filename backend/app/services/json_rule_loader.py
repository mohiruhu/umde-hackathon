import json
from typing import List, Dict

class JSONRule:
    def __init__(self, rule_dict: Dict):
        self.rule_id = rule_dict.get("rule_id")
        self.name = rule_dict.get("name")
        self.description = rule_dict.get("description")
        self.layer = rule_dict.get("layer")
        self.cms_code = rule_dict.get("cms_code")

    def validate(self, row: Dict) -> List[str]:
        # Placeholder logic: This is a stub until actual logic is provided
        return []

def load_rules_from_json(path: str) -> List[JSONRule]:
    with open(path, "r", encoding="utf-8") as f:
        rule_dicts = json.load(f)

    rules = [JSONRule(rule) for rule in rule_dicts]
    return rules
