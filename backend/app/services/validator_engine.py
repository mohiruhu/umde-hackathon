from rules.rule_diagnosis import DiagnosisRequiredRule
from typing import Dict, Any

class ValidatorEngine:
    def __init__(self):
        self.rules = [DiagnosisRequiredRule()]  # Add more as needed

    def validate_rows(self, rows: list[dict] , fast_fail: bool = True) -> list[dict]:
        results = []
        
        # Group rules by layer (1 to 4)
        layered_rules = {i: [] for i in range(1, 5)}
        for rule in self.rules:
            layered_rules[rule.layer].append(rule)

        for i, row in enumerate(rows, start=1):
            row_errors = []
            for layer in range(1, 5):  # Run from L1 → L4
                for rule in layered_rules[layer]:
                    messages = rule.validate(row)
                    for msg  in messages:
                        row_errors.append({
                            "rule": rule.name,
                            "rule_id": rule.rule_id,
                            "layer": rule.layer,
                            "severity": rule.severity,
                            "message": msg,
                            "doc_link": rule.doc_link
                        })
                if fast_fail and row_errors:
                    break  # ✅ Skip higher layers if errors found
                        
            results.append({
                "row": i,
                "valid": not row_errors,
                "errors": row_errors            
            })
        return results
