import time
import concurrent.futures
from typing import List, Dict, Any
from backend.app.rules.base import ValidationRule
from backend.app.rule_registry import discover_rules

class ValidatorEngine:
    def __init__(self):
        self.rules: List[ValidationRule] = discover_rules()

    def validate_rows(self, rows: List[Dict[str, Any]], fast_fail: bool = True, debug: bool = False) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        summary = {"critical": 0, "warning": 0, "info": 0}

        # Organize rules by layer
        layered_rules: Dict[int, List[ValidationRule]] = {i: [] for i in range(1, 5)}
        for rule in self.rules:
            layered_rules[rule.layer].append(rule)

        for i, row in enumerate(rows, start=1):
            row_errors: List[Dict[str, Any]] = []
            row_start = time.perf_counter()

            for layer in range(1, 5):
                def run_rule(rule: ValidationRule):
                    return rule, rule.validate(row)

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_map = {executor.submit(run_rule, r): r for r in layered_rules[layer]}
                    for future in concurrent.futures.as_completed(future_map):
                        rule = future_map[future]
                        try:
                            rule, messages = future.result()
                            messages = messages or []
                        except Exception as e:
                            print(f"⚠️ Rule {rule.__class__.__name__} failed on row {i}: {e}")
                            continue

                        for msg in messages:
                            row_errors.append({
                                "message": msg,
                                "rule": rule.name,
                                "rule_id": rule.rule_id,
                                "layer": rule.layer,
                                "severity": rule.severity,
                                "row": i,
                                "doc_link": rule.doc_link,
                                "tags": getattr(rule, "tags", [])
                            })

                            if rule.severity == "c":
                                summary["critical"] += 1
                            elif rule.severity == "w":
                                summary["warning"] += 1
                            else:
                                summary["info"] += 1

                        if fast_fail and row_errors:
                            break

                if fast_fail and row_errors:
                    break

            duration = time.perf_counter() - row_start
            results.append({
                "row": i,
                "errors": row_errors,
                "duration_ms": round(duration * 1000, 2) if debug else None
            })

        return {
            "results": results,
            "summary": summary
        }
