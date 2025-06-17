from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc257257F(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC257"
        self.name = "257-F"
        self.layer = 3
        self.field = "TODO_FIELD"
        self.severity = "f"
        self.confidence = "medium"
        self.tags = []
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=189"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        """CMS Description:
257-F FAILED; BIRTH DATE INVALID FOR DATABASE INSERTION

TODO: Implement logic manually."""
        return []
