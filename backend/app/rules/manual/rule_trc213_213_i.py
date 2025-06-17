from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc213213I(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC213"
        self.name = "213-I"
        self.layer = 3
        self.field = "TODO_FIELD"
        self.severity = "u"
        self.confidence = "medium"
        self.tags = []
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=328"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        """CMS Description:
213-I PREMIUM WITHHOLD OPTION CHANGE TO DIRECT BILL

TODO: Implement logic manually."""
        return []
