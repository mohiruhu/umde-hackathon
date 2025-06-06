from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

from backend.app.services.rule_publisher import publish_rule_metadata

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/publish")
async def publish_rule_metadata_route():
    try:
        publish_rule_metadata()
        return JSONResponse(status_code=200, content={"message": "Rules published successfully."})
    except Exception as e:
        logger.exception("Failed to publish rule metadata")
        return JSONResponse(status_code=500, content={"error": str(e)})

