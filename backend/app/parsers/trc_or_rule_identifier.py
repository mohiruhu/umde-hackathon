import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)
logger.propagate = True


def detect_trc_id_from_text(text: str) -> Optional[str]:
    """
    Liberal TRC ID extractor that can find a TRC ID in free text.
    Example matches: "TRC004", "TRC-004", "trc 004", etc.
    """
    match = re.search(r"TRC\s*[-:]?\s*(\d{3})", text, re.IGNORECASE)
    if match:
        trc_id = f"TRC{match.group(1)}"
        logger.debug(f"[TRC Detector] Found TRC ID: {trc_id} in text: {text[:60]}")
        return trc_id
    return None


def detect_trc_id_from_row(cells: List[str], enabled_trcs: set[str]) -> str:
    """
    Strict TRC ID extractor that validates against enabled_trcs set.
    Used where YAML or pre-filtered TRCs are required.
    """
    for cell in cells:
        cleaned = cell.replace("\n", " ").strip().upper()
        tokens = cleaned.replace("–", " ").replace("-", " ").split()

        for token in tokens:
            token = token.strip()

            if token.startswith("TRC") and len(token) >= 6 and token[3:6].isdigit():
                base = f"TRC{token[3:6]}"
                if base in enabled_trcs:
                    logger.debug(f"[TRC Detector] Matched strict TRC ID: {base}")
                    return base

            elif len(token) >= 5 and token[:3].isdigit() and token[3] in {"-", " "} and token[4].isalpha():
                base = f"TRC{token[:3]}"
                if base in enabled_trcs:
                    logger.debug(f"[TRC Detector] Matched fallback TRC ID: {base}")
                    return base

            elif token.isdigit() and len(token) == 3:
                base = f"TRC{token}"
                if base in enabled_trcs:
                    logger.debug(f"[TRC Detector] Matched numeric TRC ID: {base}")
                    return base

    raise ValueError("Unable to identify TRC ID from row")


