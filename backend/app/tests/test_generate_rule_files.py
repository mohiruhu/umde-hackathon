import pytest
from pathlib import Path
from backend.app.parsers.generate_rule_files import write_rule_file, generate_rules

DUMMY_RULE_AUTO = {
    "rule_id": "TEST001",
    "name": "Enrollment Check",
    "definition": "If member is active, validate status code.",
    "layer": "1",
    "field": "status_code",
    "severity": "High",
    "confidence": "High",
    "tags": ["eligibility", "active"],
    "doc_link": "http://example.com/rules/TEST001"
}

DUMMY_RULE_MANUAL = {
    "rule_id": "TEST002",
    "name": "Manual Rule Example",
    "definition": "Plan must review address conflicts manually.",
    "layer": "4",
    "field": "address_line_1",
    "severity": "Medium",
    "confidence": "Low",
    "tags": ["manual", "address"],
    "doc_link": "http://example.com/rules/TEST002"
}


def test_write_auto_rule_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("backend.app.parsers.generate_rule_files.RULES_BASE_DIR", tmp_path)
    result = write_rule_file(DUMMY_RULE_AUTO, overwrite=True)
    assert result is True
    output_files = list(tmp_path.rglob("*.py"))
    assert len(output_files) == 1
    content = output_files[0].read_text()
    assert "ValidationRule" in content
    assert "validate" in content
    assert "return []" in content


def test_write_manual_rule_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("backend.app.parsers.generate_rule_files.RULES_BASE_DIR", tmp_path)
    result = write_rule_file(DUMMY_RULE_MANUAL, overwrite=True)
    assert result is True
    output_files = list(tmp_path.rglob("*.py"))
    assert len(output_files) == 1
    content = output_files[0].read_text()
    assert "TODO: Implement logic manually" in content


def test_generate_rules_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("backend.app.parsers.generate_rule_files.RULES_BASE_DIR", tmp_path)
    rules = [DUMMY_RULE_AUTO, DUMMY_RULE_MANUAL]
    generate_rules(rules, overwrite=True)
    assert len(list(tmp_path.rglob("*.py"))) == 2