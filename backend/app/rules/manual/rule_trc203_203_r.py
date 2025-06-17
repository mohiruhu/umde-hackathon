from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc203203R(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC203"
        self.name = "203-R"
        self.layer = 3
        self.field = "TODO_FIELD"
        self.severity = "u"
        self.confidence = "medium"
        self.tags = []
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=185"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        """CMS Description:
203-R RX PCN NOT VALID

TODO: Implement logic manually."""
        return []
