from backend.app.rule_registry import discover_rules
from typing import List, Dict, Any
from backend.app.rules.base import ValidationRule

class ValidatorEngine:
    def __init__(self):
        self.rules: List[ValidationRule] = discover_rules()

    def validate_rows(self, rows: List[Dict[str, Any]], fast_fail: bool = True) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        # Organize rules by layer
        layered_rules: Dict[int, List[ValidationRule]] = {i: [] for i in range(1, 5)}
        for rule in self.rules:
            layered_rules[rule.layer].append(rule)

        for i, row in enumerate(rows, start=1):
            row_errors: List[Dict[str, Any]] = []

            for layer in range(1, 5):
                for rule in layered_rules[layer]:
                    messages: List[str] = rule.validate(row)

                    for msg in messages:
                        row_errors.append({
                            "message": msg,
                            "rule": rule.name,
                            "rule_id": rule.rule_id,
                            "layer": rule.layer,
                            "severity": rule.severity,
                            "row": i,
                            "doc_link": rule.doc_link
                        })

                if fast_fail and row_errors:
                    break

            results.append({
                "row": i,
                "errors": row_errors
            })

        return results
