from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc225225I(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC225"
        self.name = "225-I"
        self.layer = 3
        self.field = "TODO_FIELD"
        self.severity = "u"
        self.confidence = "medium"
        self.tags = []
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=328"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        """CMS Description:
225-I EXCEEDS SSA BENEFIT & SAFETY NET AMOUNT

TODO: Implement logic manually."""
        return []
