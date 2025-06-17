from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ValidationRule(ABC):
    rule_id: str
    name: str
    layer: int  # 1 through 4
    severity: str  # e.g., "error", "warning", "info"
    doc_link: str  # link to CMS or internal documentation

    @abstractmethod
    def validate(self, row: Dict[str, Any]) -> List[str]:
        """
        Return a list of error messages if validation fails for the given row.
        """
        pass
