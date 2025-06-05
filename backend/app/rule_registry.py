import importlib
import pkgutil
import inspect
import os
from types import ModuleType
from typing import List, cast

from backend.app.rules.base import ValidationRule
from backend.app.services.json_rule_loader import load_rules_from_json, JSONRule


def discover_rules(package: str = "rules") -> List[ValidationRule]:
    discovered_rules: List[ValidationRule] = []

    # Load all ValidationRule subclasses from Python modules
    for _, module_name, _ in pkgutil.iter_modules([package]):
        module: ModuleType = importlib.import_module(f"{package}.{module_name}")
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                cls = cast(type, obj)
                if issubclass(cls, ValidationRule) and cls is not ValidationRule:
                    discovered_rules.append(cls())
                    print(f"[Info] Loaded rule class: {name}")

    # Load external JSON-based rules
    try:
        current_dir = os.path.dirname(__file__)
        rules_path = os.path.join(current_dir, "rules", "trc_rules.json")
        json_rules: List[JSONRule] = load_rules_from_json(rules_path)
        discovered_rules.extend(json_rules)
    except FileNotFoundError:
        print("[Warning] No JSON rules loaded (rules/trc_rules.json not found)")
    except Exception as e:
        print(f"[Error] Failed to load JSON rules: {e}")

    return discovered_rules
