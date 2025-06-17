from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc310310R(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC310"
        self.name = "310-R"
        self.layer = 4
        self.field = "TODO_FIELD"
        self.severity = "r"
        self.confidence = "medium"
        self.tags = ['cms-critical']
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=186"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        """CMS Description:
310-R MMP OPT-OUT REJECTED; INVALID OPT-OUT CODE

TODO: Implement logic manually."""
        return []
