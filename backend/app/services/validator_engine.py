from rules.rule_diagnosis import DiagnosisRequiredRule

class ValidatorEngine:
    def __init__(self):
        self.rules = [DiagnosisRequiredRule()]  # Add more as needed

    def validate_rows(self, rows: list[dict]) -> list[dict]:
        results = []
        for i, row in enumerate(rows, start=1):
            row_errors = []
            for rule in self.rules:
                row_errors.extend(rule.validate(row))
            results.append({
                "row": i,
                "valid": not row_errors,
                "errors": row_errors
            })
        return results
