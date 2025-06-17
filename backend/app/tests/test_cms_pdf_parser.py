import os
import pytest
from pathlib import Path
from backend.app.parsers.cms_pdf_parser import extract_targeted_trcs_from_pdf, write_trc_rules_json, write_cms_rules_yml

@pytest.fixture
def sample_pdf_path() -> str:
    return os.path.abspath(
        os.path.join("backend", "app", "resources", "CMS_Plan_Comm_User_Guide_v17.8.pdf")
    )

def test_extract_inferencer_mode(sample_pdf_path: str) -> None:
    rules = extract_targeted_trcs_from_pdf(sample_pdf_path, start_page=65, end_page=66, mode="inferencer")
    assert isinstance(rules, list)
    for rule in rules:
        assert rule["confidence"] == "partial"
        assert rule["extraction_chain"] == ["inferencer"]

def test_extract_llm_mode(sample_pdf_path: str) -> None:
    rules = extract_targeted_trcs_from_pdf(sample_pdf_path, start_page=65, end_page=66, mode="llm")
    assert isinstance(rules, list)
    for rule in rules:
        assert "deepseek" in rule["extraction_chain"] or "local-llm" in rule["extraction_chain"]
        assert rule["confidence"] in {"high", "medium"}

def test_extract_full_mode(sample_pdf_path: str) -> None:
    rules = extract_targeted_trcs_from_pdf(sample_pdf_path, start_page=65, end_page=66, mode="full")
    assert isinstance(rules, list)
    for rule in rules:
        assert any(src in rule["extraction_chain"] for src in ["deepseek", "local-llm", "inferencer"])
        assert "confidence" in rule

def test_export_writes_valid_files(tmp_path: Path, sample_pdf_path: str) -> None:
    rules = extract_targeted_trcs_from_pdf(sample_pdf_path, start_page=65, end_page=66, mode="inferencer")
    json_path = tmp_path / "trc_rules.json"
    yml_path = tmp_path / "cms_rules.yml"

    write_trc_rules_json(rules, json_path)
    write_cms_rules_yml(rules, yml_path)

    assert json_path.exists() and json_path.stat().st_size > 0
    assert yml_path.exists() and yml_path.stat().st_size > 0
