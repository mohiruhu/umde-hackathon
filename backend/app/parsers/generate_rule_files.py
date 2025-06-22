import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any
from slugify import slugify

from app.shared.logger_setup import get_logger
from backend.app.services.L1L2autoRules_logic_generator import generate_l1_l2_logic

base_dir = Path(__file__).resolve().parent.parent  # up to backend/app
logger: logging.Logger = get_logger(__name__)

RULES_BASE_DIR = base_dir / "app" / "rules"
AUTO_LAYERS = {"1", "2"}
MANUAL_LAYERS = {"3", "4"}

RULE_TEMPLATE = '''from backend.app.rules.base import ValidationRule
from typing import Dict, Any, List

class {class_name}(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "{rule_id}"  
        self.name = "{name}"
        self.layer = {layer}
        self.field = "{field}"
        self.severity = "{severity}"
        self.confidence = "{confidence}"
        self.tags = {tags}
        self.doc_link = "{doc_link}"

    def validate(self, row: Dict[str, Any]) -> List[str]:
        {logic}
'''

def format_class_name(name: str) -> str:
    parts = [p.capitalize() for p in slugify(name).replace("-", "_").split("_")]
    return "Rule" + "".join(parts)

def generate_rule_filename(rule_id: str, name: str) -> str:
    slug = slugify(name)[:50]
    safe_slug = re.sub(r'[^a-zA-Z0-9_]', '_', slug)  # replaces - with _
    return f"rule_{rule_id.lower()}_{safe_slug}.py"

def write_rule_file(rule: Dict[str, Any], overwrite: bool = False) -> bool:
    try:
        rule_id = rule["rule_id"]
        name = rule.get("name", rule_id)
        description = rule.get("definition", "")
        layer = str(rule.get("layer", "4"))
        field = rule.get("field", "TODO_FIELD")
        severity = rule.get("severity", "medium")
        confidence = rule.get("confidence", "medium")
        tags = rule.get("tags", [])
        doc_link = rule.get("doc_link", f"https://cms.gov/trc/{rule_id}")

        is_auto = layer in AUTO_LAYERS
        folder = RULES_BASE_DIR / ("automatic" if is_auto else "manual")
        folder.mkdir(parents=True, exist_ok=True)

        filename = generate_rule_filename(rule_id, name)
        filepath = folder / filename

        # ✅ Conditional overwrite logic
        if filepath.exists():
            if is_auto and not overwrite:
                logger.warning(f"Skipping existing auto rule (use --overwrite to override): {filepath}")
                return False
            elif not is_auto:
                logger.info(f"Manual rule already exists, skipping write: {filepath}")
                return False

        class_name = format_class_name(f"{rule_id}_{name}")

        if is_auto:
            logic = generate_l1_l2_logic(description, layer)
            if not logic:
                logger.warning(f"Skipping L{layer} rule due to failed logic generation: {rule_id}")
                return False
            logic_block = logic + "\n        return []"
        else:
            logic_block = f'"""CMS Description:\n{description}\n\nTODO: Implement logic manually."""\n        return []'

        code = RULE_TEMPLATE.format(
            class_name=class_name,
            rule_id=rule_id,
            name=name.replace('"', '\\"'),
            layer=layer,
            field=field,
            severity=severity,
            confidence=confidence,
            tags=json.dumps(tags),
            doc_link=doc_link,
            logic=logic_block
        )

        with open(filepath, "w", encoding="utf-8", buffering=1) as f:
            f.write(code)
            f.flush()

        if is_auto:
            logger.info(f"Wrote auto rule: {filepath.relative_to(RULES_BASE_DIR.parent)}")
        else:
            logger.info(f"Stub generated for {rule_id} under {filepath.parent.name}/")

        return True

    except Exception as e:
        logger.error(f"Failed to write rule {rule.get('rule_id', 'UNKNOWN')}: {e}")
        return False

def generate_rules(rules: List[Dict[str, Any]], overwrite: bool = False) -> None:
    total = len(rules)
    written = 0
    for rule in rules:
        try:
            success = write_rule_file(rule, overwrite=overwrite)
            if success:
                written += 1
        except Exception as e:
            logger.error(f"❌ Failed to process rule {rule.get('rule_id', 'UNKNOWN')}: {e}")
    logger.info(f"📦 Rule generation complete. {written}/{total} rules written.")

if __name__ == "__main__":
    input_path = base_dir.parent / "data" / "trc_rules.json"
    with input_path.open("r", encoding="utf-8") as f:
        all_rules: List[Dict[str, Any]] = json.load(f)
    generate_rules(all_rules, overwrite=False)
