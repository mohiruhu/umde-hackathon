import importlib
import pkgutil
import inspect
from rules.base import ValidationRule
from types import ModuleType
from typing import List

def discover_rules(package: str = "rules") -> List[ValidationRule]:
    discovered_rules = []

    for _, module_name, _ in pkgutil.iter_modules([package]):
        module: ModuleType = importlib.import_module(f"{package}.{module_name}")

        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and hasattr(obj, "validate")
                and hasattr(obj, "rule_id")
                and hasattr(obj, "layer")
                and hasattr(obj, "severity")
                and hasattr(obj, "doc_link")
            ):
                discovered_rules.append(obj())

    return discovered_rules
