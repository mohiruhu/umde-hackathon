from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class RuleTrc013013A(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "TRC013"
        self.name = "013-A"
        self.layer = 1
        self.field = "TODO_FIELD"
        self.severity = "u"
        self.confidence = "medium"
        self.tags = []
        self.doc_link = "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf#page=186"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        # 🤷 Unknown field — logic not generated
        return []
