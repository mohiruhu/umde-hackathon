from typing import Dict, Any
from rules.base import ValidationRule

class DiagnosisRequiredRule:
    name = "DiagnosisRequired"
    rule_id = "RULE-001"
    layer = 1  # Field-level check
    severity = "error"
    doc_link = "https://example.com/rules/diagnosis-required"

    def validate(self, row: Dict[str, Any]) -> list[str]:
        errors = []
        if not row.get("DiagnosisCode"):
            errors.append("DiagnosisCode is missing")
        return errors
