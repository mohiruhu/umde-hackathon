from typing import Protocol, Dict, Any

class ValidationRule(Protocol):
    name: str
    layer: int # New: declare layer (1–4)

    def validate(self, row: Dict[str, Any]) -> list[str]:
        """Return a list of validation errors for this row."""
        ...

