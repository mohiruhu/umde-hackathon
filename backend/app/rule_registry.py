import importlib
import pkgutil
import inspect
from rules.base import ValidationRule
from types import ModuleType
from typing import List
from services.json_rule_loader import load_rules_from_json, JSONRule

def discover_rules(package: str = "rules") -> List[ValidationRule]:
    discovered_rules = []

    for _, module_name, _ in pkgutil.iter_modules([package]):
        module: ModuleType = importlib.import_module(f"{package}.{module_name}")

        for name, obj in inspect.getmembers(module):
            if (
                    inspect.isclass(obj)
                    and issubclass(obj, ValidationRule)
                    and obj is not ValidationRule
            ):
                discovered_rules.append(obj())

    # Load external JSON rules
    try:
        json_rules: List[JSONRule] = load_rules_from_json("rules/trc_rules.json")
        discovered_rules.extend(json_rules)
    except FileNotFoundError:
        print("[Warning] No JSON rules loaded (rules/trc_rules.json not found)")
    except Exception as e:
        print(f"[Error] Failed to load JSON rules: {e}")

    return discovered_rules
