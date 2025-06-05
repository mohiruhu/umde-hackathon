from abc import ABC, abstractmethod
from typing import Dict, Any

class ValidationRule(ABC):
    rule_id: str
    name: str
    layer: int

    @abstractmethod
    def validate(self, row: Dict[str, Any]) -> list[str]:
        ...
