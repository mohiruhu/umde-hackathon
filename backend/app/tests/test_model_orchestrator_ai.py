import pytest
from typing import List, Any
from backend.app.models import model_orchestrator_ai

# ------------------- TEST CASES -------------------

@pytest.mark.parametrize("input_text,expected_keywords", [
    ("Reject with TRC008 if the beneficiary identifier is not found.", ["TRC008", "beneficiary identifier"]),
    ("This is a completely unrelated sentence with no rule.", []),
    ("Reject with TRC005 if date is not valid.", ["TRC005"]),
    ("Death prior to enrollment will result in TRC009 rejection.", ["TRC009"]),
])
def test_extract_best_rule(input_text: str, expected_keywords: List[str]) -> None:
    result = model_orchestrator_ai.extract_best_rule_with_fallback(input_text)
    if expected_keywords:
        assert result is not None, f"Expected result for keywords {expected_keywords}, got None"
        assert "label" in result
        assert any(keyword in result["label"] for keyword in expected_keywords), f"Expected one of {expected_keywords} in result: {result}"
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
    assert result is not None and "label" in result and "TRC008" in result["label"]


def test_partial_fallback_logic(monkeypatch: Any) -> None:
    # Simulate DeepSeek + Local LLM + FLAN failing to force fallback to non-AI
    monkeypatch.setattr("backend.app.models.deepseek_classifier_ai.classify_with_deepseek", lambda x: None)  # type: ignore
    monkeypatch.setattr("backend.app.models.local_llm_ai.extract_with_confidence", lambda x: None)  # type: ignore
    monkeypatch.setattr("backend.app.models.flan_t5_handler_ai.extract_with_confidence", lambda x: None)  # type: ignore

    text = "death prior to enrollment"
    result = model_orchestrator_ai.extract_best_rule_with_fallback(text)
    assert result is not None and "label" in result and "TRC009" in result["label"]


@pytest.mark.parametrize(
    "input_text, expected_keywords",
    [
        (
            "Reject with TRC008 if the beneficiary identifier is not found.",
            ["TRC008", "beneficiary identifier"],
        ),
        (
            "The claim should be denied with TRC code 23 if service is not covered.",
            ["TRC", "23", "service not covered"],
        ),
    ],
)
def test_extract_best_rule_with_fallback(input_text: str, expected_keywords: List[str]) -> None:
    result = model_orchestrator_ai.extract_best_rule_with_fallback(input_text)
    assert result is not None
    if expected_keywords:
        assert "label" in result
        assert any(keyword in result["label"] for keyword in expected_keywords), f"Expected one of {expected_keywords} in result: {result}"
    else:
        assert result is None, f"Expected no rule match, got: {result}"
