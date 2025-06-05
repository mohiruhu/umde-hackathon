from backend.app.rules.rule_diagnosis import DiagnosisRequiredRule

def test_valid_row_passes():
    rule = DiagnosisRequiredRule()
    assert rule.validate({"DiagnosisCode": "E11.9"}) == []

def test_invalid_row_fails():
    rule = DiagnosisRequiredRule()
    errors = rule.validate({})
    assert "DiagnosisCode is missing" in errors
