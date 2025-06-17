from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc009009R(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC009"
        self.name = "009-R"
        self.layer = 1
        self.field = "TODO_FIELD"
        self.severity = "u"
        self.confidence = "medium"
        self.tags = []
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=185"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        # ⚠️ Confidence: Low — fallback presence check
        if not row.get("beneficiary_id"):
            return ["Missing or invalid beneficiary id"]
        return []
