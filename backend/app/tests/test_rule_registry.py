from backend.app.rule_registry import discover_rules

def test_rules_are_discoverable():
    rules = discover_rules()
    assert len(rules) >= 1, "No rules were discovered"

def test_rules_have_required_fields():
    rules = discover_rules()
    for rule in rules:
        assert hasattr(rule, "rule_id"), f"{rule} missing rule_id"
        assert hasattr(rule, "name"), f"{rule} missing name"
        assert hasattr(rule, "layer"), f"{rule} missing layer"
        assert hasattr(rule, "severity"), f"{rule} missing severity"
        assert hasattr(rule, "doc_link"), f"{rule} missing doc_link"
        assert callable(rule.validate), f"{rule} is missing a validate() method"
