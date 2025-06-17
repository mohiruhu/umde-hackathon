from typing import Optional, Tuple, List

# field → (normalized name, expected type, enum values if any)
FIELD_HINTS = {
    "beneficiary name": ("beneficiary_name", "str", None),
    "birth date": ("birth_date", "date", None),
    "effective date": ("effective_date", "date", None),
    "zip code": ("zip_code", "int", None),
    "gender": ("gender", "str", ["M", "F"]),
    "contract number": ("contract_number", "str", None),
    "beneficiary identifier": ("beneficiary_id", "str", None),
    "disenrollment reason code": ("disenrollment_reason_code", "str", None),
    "beneficiary": ("beneficiary_id", "str", None),
    "beneficiary match": ("beneficiary_id", "str", None),
    "beneficiary id": ("beneficiary_id", "str", None),
}


def normalize_field(raw: str) -> Tuple[Optional[str], Optional[str], Optional[List[str]]]:
    raw = raw.lower()
    for phrase, (field, ftype, enum) in FIELD_HINTS.items():
        if phrase in raw:
            return field, ftype, enum
    return None, None, None


def generate_l1_l2_logic(definition: str, layer: str) -> Optional[str]:
    defn = definition.lower()
    field, ftype, enum_values = normalize_field(defn)

    if not field:
        return "# 🤷 Unknown field — logic not generated"

    comments: List[str] = []

    # Layer 1 — Required presence
    if "required" in defn or "must be present" in defn or "not found" in defn:
        comments.append("# 💡 Confidence: High — interpreted as required field")
        logic = f'if not row.get("{field}"):\n            return ["Missing {field.replace("_", " ")}"]'

    # Layer 2 — Format checks
    elif enum_values:
        comments.append("# 💡 Confidence: High — enum constraint detected")
        options = ", ".join(f'"{v}"' for v in enum_values)
        logic = f'if row.get("{field}") not in [{options}]:\n            return ["Invalid {field.replace("_", " ")}"]'

    elif "5 digits" in defn:
        comments.append("# 💡 Confidence: High — zip code format")
        logic = f'if not re.fullmatch(r"\\d{{5}}", str(row.get("{field}", ""))):\n            return ["Invalid zip code format (5 digits)"]'

    elif ftype == "date" or "invalid date" in defn:
        comments.append("# ⚠️ Confidence: Medium — assumed date validation")
        logic = f'''from datetime import datetime
        try:
            datetime.strptime(row.get("{field}", ""), "%Y-%m-%d")
        except Exception:
            return ["Invalid {field.replace("_", " ")} format (YYYY-MM-DD)"]'''

    else:
        comments.append("# ⚠️ Confidence: Low — fallback presence check")
        logic = f'if not row.get("{field}"):\n            return ["Missing or invalid {field.replace("_", " ")}"]'

    return "\n        ".join(comments) + "\n        " + logic
