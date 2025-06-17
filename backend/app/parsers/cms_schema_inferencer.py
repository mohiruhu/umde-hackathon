import logging
from typing import List, Dict

logger = logging.getLogger(__name__)
logger.propagate = True

FIELD_MAP = {
    "birth": "dob",
    "date of birth": "dob",
    "first name": "member_name",
    "surname": "member_name",
    "name": "member_name",
    "gender": "gender",
    "beneficiary id": "member_id",
    "beneficiary": "member_id",
    "identifier": "member_id",
    "contract": "contract_number",
    "disenrollment reason": "disenrollment_reason",
    "effective date": "effective_date",
    "transaction code": "transaction_code"
}

class CMSSchemaInferencer:
    def infer(self, row_cells: List[str], rule_id: str) -> Dict[str, str]:
        inferred: Dict[str, str] = {}
        normalized = [c.strip() for c in row_cells if c and c.strip()]
        raw_text = " | ".join(normalized)

        logger.debug(f"[Inferencer] Raw row text: {raw_text[:100]}")

        inferred["rule_id"] = rule_id.upper()

        # Title inference (non-TRC cell with strongest signal)
        title = next((c for c in normalized if rule_id not in c), rule_id)
        inferred["title"] = title

        # Long and short definition
        definition_parts = [c for c in normalized if rule_id not in c]
        long_def = " ".join(definition_parts)
        short_def = long_def[:160] + "..." if len(long_def) > 160 else long_def

        inferred["definition"] = long_def
        inferred["short_definition"] = short_def

        logger.debug(f"[Inferencer] Title: {title}")
        logger.debug(f"[Inferencer] Short Def: {short_def[:60]}")

        # Severity inference
        severity = "U"
        for part in normalized:
            part_lower = part.lower()
            if "reject" in part_lower:
                severity = "R"
                break
            elif "fail" in part_lower:
                severity = "F"
                break
            elif "informational" in part_lower or "note" in part_lower:
                severity = "I"
        inferred["severity"] = severity

        logger.debug(f"[Inferencer] Severity inferred: {severity}")

        # Field inference
        field = "unknown"
        text_lower = raw_text.lower()
        for keyword, mapped_field in FIELD_MAP.items():
            if keyword in text_lower:
                field = mapped_field
                break
        inferred["field"] = field

        logger.debug(f"[Inferencer] Field inferred: {field}")

        inferred["raw_row"] = raw_text
        return inferred
