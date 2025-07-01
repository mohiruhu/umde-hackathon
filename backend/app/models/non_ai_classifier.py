from typing import Optional, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)

INCLUDE_KEYWORDS = ["beneficiary", "enrollment", "effective date", "identification", "not found"]
EXCLUDE_KEYWORDS = ["payment", "report", "transmission", "file layout"]

TRC_HARDCODED_RULES = {
    "trc008": "TRC008: Beneficiary not found",
    "trc005": "TRC005: Invalid date format",
    "trc009": "TRC009: Date of death precedes effective date",
}


def extract_rule(text: str) -> Optional[Dict[str, Any]]:
    """
    Proper non-AI fallback that returns dict instead of string.
    """
    if not text:
        return None

    text_lower = text.lower()

    for key, label in TRC_HARDCODED_RULES.items():
        if key in text_lower:
            rule_id = key.upper()
            return {
                "label": {
                    "rule_id": rule_id,
                    "title": label,
                    "definition": text.strip(),
                    "short_definition": label,
                    "field": "unknown",
                    "plan_action": "review manually",
                    "layer": "4",
                    "severity": "U",
                    "confidence": "n/a",
                    "fallback_used": True,
                },
                "rule_id": rule_id,
                "confidence": "n/a"
            }

    match = re.search(r"trc(\d{3})", text_lower)
    if match:
        rule_id = f"TRC{match.group(1)}"
        return {
            "label": {
                "rule_id": rule_id,
                "title": f"{rule_id} Rule",
                "definition": text.strip(),
                "short_definition": text[:80],
                "field": "unknown",
                "plan_action": "review manually",
                "layer": "4",
                "severity": "U",
                "confidence": "n/a",
                "fallback_used": True,
            },
            "rule_id": rule_id,
            "confidence": "n/a"
        }

    return None
