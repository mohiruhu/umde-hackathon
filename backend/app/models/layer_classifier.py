# I will verify the enhanced `infer_layer_with_metadata` function to ensure it's type-correct and compatible with Pylance.
import re
from typing import Tuple, List, Dict

HIGH_RISK_CODES = {
    "TRC004", "TRC006", "TRC007", "TRC008", "TRC021", "TRC232"
}

L1_KEYWORDS = {"must be present", "must not be null", "is required", "cannot be empty"}
L2_KEYWORDS = {"must be 5 digits", "must be in format", "must match", "must be numeric", "invalid format"}
L3_KEYWORDS = {"if", "when", "dependent on", "conditional", "based on", "in combination with"}
L4_KEYWORDS = {"claim will be rejected", "results in denial", "cms will reject", "must not be submitted", "violates trc"}

def infer_layer_with_metadata(code: str, definition: str) -> Tuple[int, Dict[str, str], List[str]]:
    """
    Infers the validation layer, source of inference, and associated tags.

    Args:
        code: TRC code string (e.g., "TRC004")
        definition: Textual rule definition extracted from CMS guide

    Returns:
        Tuple of:
            - layer: int (1 through 4)
            - reason: dict with 'source' and 'detail'
            - tags: list of strings
    """
    norm_code = code.strip().upper()
    norm_def = definition.strip().lower()
    tags: List[str] = []

    # High-risk TRC override
    if norm_code in HIGH_RISK_CODES:
        tags.append("cms-critical")
        return 4, {"source": "trc_id", "detail": norm_code}, tags

    # Keyword-based override
    for kw in L4_KEYWORDS:
        if kw in norm_def:
            tags.append("cms-critical")
            return 4, {"source": "keyword", "detail": kw}, tags

    for kw in L3_KEYWORDS:
        if kw in norm_def:
            return 3, {"source": "keyword", "detail": kw}, tags

    for kw in L2_KEYWORDS:
        if kw in norm_def:
            return 2, {"source": "keyword", "detail": kw}, tags

    for kw in L1_KEYWORDS:
        if kw in norm_def:
            return 1, {"source": "keyword", "detail": kw}, tags

    # Heuristic fallback based on TRC code family
    if re.match(r"TRC0\d{2}", norm_code):
        return 1, {"source": "fallback", "detail": "TRC0xx"}, tags
    elif re.match(r"TRC1\d{2}", norm_code):
        return 2, {"source": "fallback", "detail": "TRC1xx"}, tags
    elif re.match(r"TRC2\d{2}", norm_code):
        return 3, {"source": "fallback", "detail": "TRC2xx"}, tags

    # Final fallback
    tags.append("cms-critical")
    return 4, {"source": "fallback", "detail": "uncertain"}, tags




