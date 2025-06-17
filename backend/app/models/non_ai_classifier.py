import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ------------------- SHARED KEYWORD RULES -------------------
INCLUDE_KEYWORDS = ["beneficiary", "enrollment", "effective date", "identification", "not found"]
EXCLUDE_KEYWORDS = ["payment", "report", "transmission", "file layout"]

TRC_HARDCODED_RULES = {
    "trc008": "TRC008: Beneficiary not found",
    "trc005": "TRC005: Invalid date format",
    "trc009": "TRC009: Date of death precedes effective date",
}

# ------------------- NON-AI FALLBACK -------------------
def extract_rule_keyword_fallback(text: str) -> Optional[str]:
    """
    Simple rule-based keyword fallback extractor. Only used when all AI-based extraction fails.

    Args:
        text (str): The input rule description from CMS or similar.

    Returns:
        Optional[str]: A simplified, deterministic classification or None if no rule is found.
    """
    if not text:
        return None

    text_lower = text.lower()

    for key, label in TRC_HARDCODED_RULES.items():
        if key in text_lower:
            return label

    match = re.search(r"trc(\d{3})", text_lower)
    if match:
        return f"TRC{match.group(1)}: Rule identified from text"

    return None


def is_eligible_rule(text: str) -> bool:
    """
    Heuristic check for determining if the rule is likely eligible for inclusion
    in cms_rules.yml based on common member/non-member rule patterns.

    Args:
        text (str): TRC rule description

    Returns:
        bool: True if eligible, False if not
    """
    if not text:
        return False

    text_lower = text.lower()

    if any(keyword in text_lower for keyword in INCLUDE_KEYWORDS) and not any(keyword in text_lower for keyword in EXCLUDE_KEYWORDS):
        return True

    return False
