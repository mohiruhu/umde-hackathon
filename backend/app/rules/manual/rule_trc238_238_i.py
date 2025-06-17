from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc238238I(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC238"
        self.name = "238-I"
        self.layer = 3
        self.field = "TODO_FIELD"
        self.severity = "r"
        self.confidence = "medium"
        self.tags = []
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=329"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        """CMS Description:
238-I RRB REJECTED PART B REDUCTION, DELAYED PROCESSING

TODO: Implement logic manually."""
        return []
