from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc222222I(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC222"
        self.name = "222-I"
        self.layer = 3
        self.field = "TODO_FIELD"
        self.severity = "u"
        self.confidence = "medium"
        self.tags = []
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=328"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        """CMS Description:
222-I BENE EXCLUDED FROM TRANSMISSION TO SSA/RRB

TODO: Implement logic manually."""
        return []
