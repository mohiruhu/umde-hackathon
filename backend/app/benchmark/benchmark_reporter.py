import os
import json
import csv
from typing import Any
from collections import Counter, defaultdict

from backend.app.rule_registry import discover_rules


def generate_benchmark_report(save_to_file: bool = True) -> dict[str, Any]:
    rules = discover_rules()
    total = len(rules)

    if total == 0:
        return {"error": "No rules discovered."}

    layer_dist: defaultdict[int, list[Any]] = defaultdict(list)
    confidence_counter: Counter[str] = Counter()
    todo_rules: list[dict[str, Any]] = []
    broken_rules: list[dict[str, Any]] = []
    inconsistent_logic: list[dict[str, Any]] = []

    for rule in rules:
        rule_id = getattr(rule, "rule_id", "unknown")
        name = getattr(rule, "name", "unknown")
        layer = getattr(rule, "layer", 0)
        confidence = getattr(rule, "confidence", "unknown")
        has_validate = callable(getattr(rule, "validate", None))

        # --- 1. Broken rule detection
        if rule_id == "unknown" or name == "unknown" or layer == 0:
            broken_rules.append({
                "rule_id": rule_id,
                "name": name,
                "layer": layer,
                "confidence": confidence,
                "severity": "critical",
                "reason": "Missing required attribute(s)"
            })

        # --- 2. Inconsistent logic detection
        if layer in (1, 2) and (not has_validate or "todo" in confidence.lower()):
            inconsistent_logic.append({
                "rule_id": rule_id,
                "name": name,
                "layer": layer,
                "confidence": confidence,
                "severity": "warning",
                "reason": "L1/L2 rule missing logic or marked todo"
            })

        # --- Existing classification
        layer_dist[layer].append(rule)
        confidence_counter[confidence] += 1

        if "todo" in confidence.lower():
            todo_rules.append({
                "rule_id": rule_id,
                "name": name,
                "layer": layer,
                "confidence": confidence
            })

    # Sort by rule_id
    broken_rules.sort(key=lambda x: x["rule_id"])
    inconsistent_logic.sort(key=lambda x: x["rule_id"])

    # Combine for CSV export
    combined_export = broken_rules + inconsistent_logic

    # Prepare result
    result: dict[str, Any] = {
        "total_rules": total,
        "layer_distribution": {f"L{layer}": len(layer_dist[layer]) for layer in sorted(layer_dist)},
        "confidence_distribution": dict(confidence_counter),
        "todo_count": len(todo_rules),
        "todo_rules": todo_rules,
        "broken_rules": broken_rules,
        "inconsistent_logic_rules": inconsistent_logic,
        "auto_logic_rate": round((total - len(todo_rules)) / total * 100, 2),
    }

    if save_to_file:
        os.makedirs("benchmark", exist_ok=True)

        # Save JSON
        with open("benchmark/report.json", "w") as f:
            json.dump(result, f, indent=2)

        # Save CSV
        with open("benchmark/broken_rules.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["rule_id", "name", "layer", "confidence", "severity", "reason"])
            writer.writeheader()
            for row in combined_export:
                writer.writerow(row)

    return result


if __name__ == "__main__":
    print(json.dumps(generate_benchmark_report(), indent=2))
