import os
import pytest
from backend.app.parsers.cms_pdf_parser import extract_trc_rules_from_pdf

@pytest.fixture
def sample_pdf_path() -> str:
    return os.path.abspath(
        os.path.join("backend", "app", "resources", "CMS_Plan_Comm_User_Guide_v17.8.pdf")
    )

def test_extract_trc_rules(sample_pdf_path:str)-> None:
    rules = extract_trc_rules_from_pdf(sample_pdf_path, page_number=68)

    assert isinstance(rules, list), "Output should be a list"
    assert len(rules) > 0, "Should extract at least one rule"

    rule = rules[0]
    assert "rule_id" in rule and rule["rule_id"].startswith("TRC")
    assert "name" in rule
    assert "description" in rule
    assert "definition" in rule
    assert "layer" in rule
