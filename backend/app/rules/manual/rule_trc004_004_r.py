from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc004004R(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC004"
        self.name = "004-R"
        self.layer = 4
        self.field = "TODO_FIELD"
        self.severity = "u"
        self.confidence = "medium"
        self.tags = ['cms-critical']
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=185"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        """CMS Description:
004-R BENEFICIARY NAME REQUIRED

TODO: Implement logic manually."""
        return []
