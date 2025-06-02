from typing import Dict, Any
from rules.base import ValidationRule
from config import RULES_DOC_BASE_URL

class DiagnosisRequiredRule:
    name = "DiagnosisRequired"
    rule_id = "RULE-001"
    layer = 1  # Field-level check
    severity = "error"
    doc_link = f"{RULES_DOC_BASE_URL}/diagnosis-required"

    def validate(self, row: Dict[str, Any]) -> list[str]:
        errors = []
        if not row.get("DiagnosisCode"):
            errors.append("DiagnosisCode is missing")
        return errors
