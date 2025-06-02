from rule_registry import discover_rules

if __name__ == "__main__":
    rules = discover_rules()
    print(f"Discovered {len(rules)} rule(s):")
    for rule in rules:
        print(f" - {rule.rule_id}: {rule.name} (Layer {rule.layer})")
