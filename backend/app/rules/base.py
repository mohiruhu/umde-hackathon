from abc import ABC, abstractmethod
from typing import Dict, Any

class ValidationRule(ABC):
    rule_id: str
    name: str
    layer: int
    severity: str  # ✅ add this
    doc_link: str  # ✅ and this

    @abstractmethod
    def validate(self, row: Dict[str, Any]) -> list[str]:
        ...
