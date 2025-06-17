from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc003003F(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC003"
        self.name = "003-F"
        self.layer = 1
        self.field = "TODO_FIELD"
        self.severity = "u"
        self.confidence = "medium"
        self.tags = []
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=185"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        # ⚠️ Confidence: Low — fallback presence check
        if not row.get("contract_number"):
            return ["Missing or invalid contract number"]
        return []
