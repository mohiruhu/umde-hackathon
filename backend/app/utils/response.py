import logging
from datetime import datetime, timezone
from fastapi.responses import JSONResponse
from typing import Any, Dict

logger = logging.getLogger(__name__)

def error_response(
    status_code: int,
    path: str,
    error: str,
    details: Any
) -> JSONResponse:
    """
    Standard error response for API endpoints.

    Includes timestamp, path, status, human-readable error, and details payload.
    Also logs the error for operational visibility.
    """
    payload: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status_code": status_code,
        "path": path,
        "error": error,
        "details": details
    }

    # Log the structured error for ops or debug use
    logger.error(f"[{status_code}] {error} @ {path} | Details: {details}")

    return JSONResponse(status_code=status_code, content=payload)
