from typing import Protocol, Dict, Any

class ValidationRule(Protocol):
    name: str
    rule_id: str  #Missing from Protocol (but used in rules)
    layer: int # New: declare layer (1–4)
    severity: str  # e.g., "error" or "warning"
    doc_link: str  # optional link to CMS or internal rule reference

    def validate(self, row: Dict[str, Any]) -> list[str]:
        """Return a list of validation errors for this row."""
        ...

