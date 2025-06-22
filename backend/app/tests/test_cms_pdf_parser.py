import os
import pytest
from pathlib import Path
from backend.app.parsers.cms_pdf_parser import extract_chunks_and_generate_rules_sync, write_trc_rules_with_history, write_cms_rules_yml

@pytest.fixture
def sample_pdf_path() -> str:
    return os.path.abspath(
        os.path.join("backend", "app", "resources", "CMS_Plan_Comm_User_Guide_v17.8.pdf")
    )

@pytest.fixture
def sample_xlsx_path() -> str:
    """Fixture for sample XLSX file path."""
    return os.path.abspath(
        os.path.join("backend", "app", "resources", "CEM 837 DME Edits.xlsx")
    )

@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory for tests."""
    return tmp_path / "output"

def test_extract_pdf_rules(sample_pdf_path: str, tmp_output_dir: Path) -> None:
    """Test basic PDF rule extraction functionality."""
    tmp_output_dir.mkdir(parents=True, exist_ok=True)
    
    rules = extract_chunks_and_generate_rules_sync(
        source_path=sample_pdf_path,
        filetype="pdf",
        output_dir=tmp_output_dir,
        start_page=65,
        end_page=66
    )
    
    assert isinstance(rules, list)
    # Basic validation that rules have expected structure
    for rule in rules:
        assert "rule_id" in rule
        assert "title" in rule
        assert "definition" in rule
        assert "confidence" in rule
        assert "extraction_chain" in rule

def test_extract_rules_with_manual_review(sample_pdf_path: str, tmp_output_dir: Path) -> None:
    """Test rule extraction with manual review output."""
    tmp_output_dir.mkdir(parents=True, exist_ok=True)
    manual_review_path = tmp_output_dir / "manual_review.json"
    
    rules = extract_chunks_and_generate_rules_sync(
        source_path=sample_pdf_path,
        filetype="pdf",
        output_dir=tmp_output_dir,
        start_page=65,
        end_page=66,
        manual_review_output_path=manual_review_path
    )
    
    assert isinstance(rules, list)
    # Check if manual review file is created when needed
    if any(rule.get("manual_review_required", False) for rule in rules):
        assert manual_review_path.exists()

def test_export_writes_valid_files(tmp_output_dir: Path, sample_pdf_path: str) -> None:
    """Test that export functions write valid files."""
    tmp_output_dir.mkdir(parents=True, exist_ok=True)
    
    rules = extract_chunks_and_generate_rules_sync(
        source_path=sample_pdf_path,
        filetype="pdf",
        output_dir=tmp_output_dir,
        start_page=65,
        end_page=66
    )
    
    yml_path = tmp_output_dir / "cms_rules.yml"

    # Test TRC rules with history (writes to output_dir)
    write_trc_rules_with_history(rules, tmp_output_dir)
    
    # Test CMS rules YML
    write_cms_rules_yml(rules, yml_path)

    # Verify files exist and have content
    trc_json_path = tmp_output_dir / "trc_rules.json"
    assert trc_json_path.exists() and trc_json_path.stat().st_size > 0
    assert yml_path.exists() and yml_path.stat().st_size > 0
    
    # Verify extractedrules directory is created
    extractedrules_dir = tmp_output_dir / "extractedrules"
    assert extractedrules_dir.exists()
    
    # Check that at least one timestamped file was created
    rule_files = list(extractedrules_dir.glob("rules_*.json"))
    assert len(rule_files) > 0

def test_extract_xlsx_rules(sample_xlsx_path: str, tmp_output_dir: Path) -> None:
    """Test XLSX rule extraction functionality."""
    tmp_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Skip test if XLSX file doesn't exist
    if not os.path.exists(sample_xlsx_path):
        pytest.skip(f"XLSX test file not found: {sample_xlsx_path}")
    
    rules = extract_chunks_and_generate_rules_sync(
        source_path=sample_xlsx_path,
        filetype="xlsx",
        output_dir=tmp_output_dir
    )
    
    assert isinstance(rules, list)
    # Basic validation that rules have expected structure
    for rule in rules:
        assert "rule_id" in rule
        assert "title" in rule
        assert "definition" in rule
        assert "source_type" in rule

def test_trace_logging(sample_pdf_path: str, tmp_output_dir: Path) -> None:
    """Test that trace logs are properly created."""
    tmp_output_dir.mkdir(parents=True, exist_ok=True)
    
    rules = extract_chunks_and_generate_rules_sync(
        source_path=sample_pdf_path,
        filetype="pdf",
        output_dir=tmp_output_dir,
        start_page=65,
        end_page=66
    )
    
    assert isinstance(rules, list)  # Basic validation
    
    # Check that trace directory and files are created
    trace_dir = tmp_output_dir / "trace"
    assert trace_dir.exists()
    
    trace_files = list(trace_dir.glob("validation_trace_*.json"))
    assert len(trace_files) > 0
    
    # Verify trace file has content
    trace_file = trace_files[0]
    assert trace_file.stat().st_size > 0
