from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc209209R(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC209"
        self.name = "209-R"
        self.layer = 3
        self.field = "TODO_FIELD"
        self.severity = "r"
        self.confidence = "medium"
        self.tags = []
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=185"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        """CMS Description:
209-R 4RX CHANGE REJECTED, INVALID CHANGE EFFECTIVE DATE

TODO: Implement logic manually."""
        return []
