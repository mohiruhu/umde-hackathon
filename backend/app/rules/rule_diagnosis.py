from rules.base import ValidationRule
from typing import List, Dict, Any

class DiagnosisCodeRule(ValidationRule):
    rule_id = "D001"
    name = "Missing Diagnosis Code"
    layer = 1
    severity = "error"
    doc_link = "https://docs.cms.gov/errors/d001"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        if not row.get("diagnosis_code"):
            errors.append("Diagnosis code is missing.")
        return errors
