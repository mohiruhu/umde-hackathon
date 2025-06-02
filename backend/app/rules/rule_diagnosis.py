from typing import Dict, Any
from rules.base import ValidationRule

class DiagnosisRequiredRule:
    name = "DiagnosisRequired"
    layer = 1  # Field-level check

    def validate(self, row: Dict[str, Any]) -> list[str]:
        errors = []
        if not row.get("DiagnosisCode"):
            errors.append("DiagnosisCode is missing")
        return errors
