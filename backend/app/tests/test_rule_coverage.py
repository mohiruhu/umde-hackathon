from pathlib import Path
from backend.app.rule_registry import discover_rules

def test_all_rules_have_tests():
    test_root = Path("backend/app/tests/test_rules")
    existing_tests = {f.stem for f in test_root.rglob("test_*.py")}

    missing_tests: list[str] = []
    for rule in discover_rules():
        rule_id = rule.rule_id.lower().replace("-", "_")
        rule_name = rule.name.lower().replace("-", "_").replace(" ", "_")
        expected_test_name = f"test_rule_{rule_id}_{rule_name}"
        if expected_test_name not in existing_tests:
            missing_tests.append(expected_test_name)

    assert not missing_tests, f"Missing test files for: {missing_tests}"


