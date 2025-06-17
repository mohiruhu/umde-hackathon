from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc210210A(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC210"
        self.name = "210-A"
        self.layer = 3
        self.field = "TODO_FIELD"
        self.severity = "u"
        self.confidence = "medium"
        self.tags = []
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=190"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        """CMS Description:
210-A POS ENROLLMENT ACCEPTED

TODO: Implement logic manually."""
        return []
