import pytest
from typing import List, Any
from backend.app.models import model_orchestrator_ai

# ------------------- TEST CASES -------------------

@pytest.mark.parametrize("input_text,expected_keywords", [
    ("Reject with TRC008 if the beneficiary identifier is not found.", ["TRC008"]),
    ("This is a completely unrelated sentence with no rule.", []),
    ("Reject with TRC005 if date is not valid.", ["TRC005"]),
    ("Death prior to enrollment will result in TRC009 rejection.", ["TRC009"]),
])
def test_extract_best_rule_with_fallback(input_text: str, expected_keywords: List[str]) -> None:
    result = model_orchestrator_ai.extract_best_rule_with_fallback(input_text)
    if expected_keywords:
        assert result is not None, f"Expected result for keywords {expected_keywords}, got None"
        assert "label" in result
        assert "rule_id" in result["label"]
        assert result["label"]["rule_id"] in expected_keywords, f"Expected one of {expected_keywords} in result: {result['label']['rule_id']}"
    else:
        assert result is None, f"Expected no rule match, got: {result}"


def test_empty_input_returns_none() -> None:
    assert model_orchestrator_ai.extract_best_rule_with_fallback("") is None


def test_invalid_input_type_returns_none() -> None:
    assert model_orchestrator_ai.extract_best_rule_with_fallback(None) is None  # type: ignore
    assert model_orchestrator_ai.extract_best_rule_with_fallback(12345) is None  # type: ignore


# ------------------- EDGE CASES -------------------
def test_case_insensitivity() -> None:
    text = "REJECT WITH trc008 IF THE BENEFICIARY IDENTIFIER IS NOT FOUND."
    result = model_orchestrator_ai.extract_best_rule_with_fallback(text)
    assert result is not None and result["label"]["rule_id"] == "TRC008"


def test_partial_fallback_logic(monkeypatch: Any) -> None:
    # Simulate DeepSeek + Local LLM + FLAN failing to force fallback to non-AI
    monkeypatch.setattr("backend.app.models.deepseek_classifier_ai.extract_with_confidence", lambda x: None)  # type: ignore
    monkeypatch.setattr("backend.app.models.local_llm_ai.extract_with_confidence", lambda x: None)  # type: ignore
    monkeypatch.setattr("backend.app.models.flan_t5_handler_ai.extract_with_confidence", lambda x: None)  # type: ignore

    text = "death prior to enrollment"
    result = model_orchestrator_ai.extract_best_rule_with_fallback(text)
    assert result is not None and "TRC009" in result["label"]["rule_id"]
