import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch
from backend.app.services.rule_publisher import serialize_rules, get_output_path, get_s3_client
from backend.app.rules.base import ValidationRule


from typing import List, Dict, Any, cast

class DummyRule(ValidationRule):
    def __init__(self, rule_id:str="R1", name:str="Test Rule", layer:int=1, description:str="desc"):
        self.rule_id = rule_id
        self.name = name
        self.layer = layer
        self.description = description
        self.severity = "High"
        self.doc_link = "http://example.com"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        return []


def test_serialize_rules_basic():
    rules = cast(List[ValidationRule], [DummyRule()])
    output = serialize_rules(rules)
    data = json.loads(output)
    assert isinstance(data, list)
    assert data[0]["id"] == "R1"
    assert data[0]["name"] == "Test Rule"
    assert data[0]["layer"] == 1
    assert "description" in data[0]

def test_get_output_path_env_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LOCAL_RULE_OUTPUT_PATH", str(tmp_path))
    path = get_output_path("test.json")
    assert path.endswith("test.json")
    assert os.path.exists(tmp_path)


def test_get_output_path_env_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("LOCAL_RULE_OUTPUT_PATH", raising=False)
    with pytest.raises(ValueError):
        get_output_path("test.json")


def test_get_s3_client_mocked():
    with patch("backend.app.services.rule_publisher.boto3.client") as mock_client:
        client = get_s3_client()
        assert mock_client.called
        assert client is not None

def test_serialize_rules_handles_exceptions():
    class BadRule(ValidationRule):
        def __init__(self): pass
        def validate(self, row: Dict[str, Any]) -> List[str]: return []
    rules = cast(List[ValidationRule], [BadRule()])
    output = serialize_rules(rules)
    assert isinstance(output, str)
    assert "[]" in output or "{}" in output  # tolerate empty fallback

def test_get_output_path_invalid(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LOCAL_RULE_OUTPUT_PATH", "/invalid<>path")
    with pytest.raises(OSError):
        get_output_path("fail.json")


