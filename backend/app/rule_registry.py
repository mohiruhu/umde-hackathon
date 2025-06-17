# backend/app/rule_registry.py
import importlib.util
import inspect
from pathlib import Path
from typing import List

from backend.app.rules.base import ValidationRule

RULES_DIR = Path(__file__).parent / "rules"
SUBFOLDERS = ["automatic", "manual"]

def import_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        return module
    return None

def discover_rules() -> List[ValidationRule]:
    all_rules: List[ValidationRule] = []

    for folder in SUBFOLDERS:
        rule_folder = RULES_DIR / folder
        if not rule_folder.exists():
            continue

        for file in rule_folder.glob("*.py"):
            module_name = f"{folder}.{file.stem}"
            module = import_module_from_path(module_name, file)
            if not module:
                continue

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, ValidationRule) and obj is not ValidationRule:
                    try:
                        instance = obj()
                        all_rules.append(instance)
                        print(f"[Info] Loaded: {instance.rule_id} - {instance.name}")
                    except Exception as e:
                        print(f"⚠️ Failed to instantiate rule in {file.name}: {e}")

    return all_rules
