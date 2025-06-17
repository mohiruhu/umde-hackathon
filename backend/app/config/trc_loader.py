from pathlib import Path
import yaml
base_dir = Path(__file__).resolve().parent
yaml_path = base_dir / "cms_rules.yml"

def load_enabled_trcs() -> list[str]:
    yaml_path = base_dir / "cms_rules.yml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("enabled_trcs", [])