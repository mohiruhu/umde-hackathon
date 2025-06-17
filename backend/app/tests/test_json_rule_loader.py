import json
import pytest
from pathlib import Path
from backend.app.services.json_rule_loader import load_rules_from_json, JSONRule


VALID_RULES = [
    {
        "rule_id": "R001",
        "name": "Test Rule",
        "description": "Some TRC rule description.",
        "layer": 2,
        "cms_code": "TRC-112",
        "severity": "Medium",
        "doc_link": "http://cms.gov/rules/R001"
    }
]

INVALID_JSON = "{ bad: json, no_quotes: true }"


def test_load_valid_json_rules(tmp_path: Path):
    file_path = tmp_path / "rules.json"
    file_path.write_text(json.dumps(VALID_RULES), encoding="utf-8")
    rules = load_rules_from_json(str(file_path))
    assert isinstance(rules, list)
    assert isinstance(rules[0], JSONRule)
    assert rules[0].rule_id == "R001"
    assert rules[0].layer == 2


def test_load_json_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_rules_from_json("non_existent_file.json")


def test_load_invalid_json(tmp_path: Path):
    file_path = tmp_path / "invalid.json"
    file_path.write_text(INVALID_JSON, encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_rules_from_json(str(file_path))