
from unittest.mock import patch, MagicMock
from app.models.deepseek_classifier_ai import classify_with_deepseek


@patch("backend.app.models.deepseek_client_ai.requests.post")
def test_classify_with_deepseek_include(mock_post: MagicMock):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = [{
        "generated_text": "INCLUDE"
    }]
    result = classify_with_deepseek("The enrollee must be validated.")
    assert result == "include"


@patch("backend.app.models.deepseek_client_ai.requests.post")
def test_classify_with_deepseek_exclude(mock_post: MagicMock):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = [{
        "generated_text": "EXCLUDE"
    }]
    result = classify_with_deepseek("Informational note about eligibility.")
    assert result == "exclude"


@patch("backend.app.models.deepseek_client_ai.requests.post")
def test_classify_with_deepseek_invalid_response(mock_post: MagicMock):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = [{}]  # missing 'generated_text'
    result = classify_with_deepseek("Missing output test")
    assert result is None


@patch("backend.app.models.deepseek_client_ai.requests.post")
def test_classify_with_deepseek_http_error(mock_post: MagicMock):
    mock_post.return_value.status_code = 500
    result = classify_with_deepseek("Trigger HTTP error")
    assert result is None

@patch("backend.app.models.deepseek_client_ai.requests.post")
def test_classify_with_deepseek_trims_output(mock_post: MagicMock):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = [{"generated_text": " INCLUDE\\n"}]
    result = classify_with_deepseek("Extra whitespace test")
    assert result == "include"
