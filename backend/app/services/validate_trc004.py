from typing import Optional

def validate_trc004(member_record: dict[str, str | None]) -> Optional[str]:
    """
    Validates that Member ID is present and non-empty.
    Returns error message if invalid, otherwise None.
    """
    raw_id = member_record.get("member_id", None)

    member_id = raw_id.strip() if isinstance(raw_id, str) else ""

    if not member_id:
        return "TRC004: Missing or invalid Member ID"

    return None