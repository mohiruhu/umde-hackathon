from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse


router = APIRouter()

@router.get("/ping")
async def ping():
    return {"message": "Validator route ready"}

@router.post("/")
async def validate_file(file: UploadFile = File(...)):
    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "No file uploaded"})

    content = await file.read()
    
    # TODO: Pass content to actual validation logic
    # For now, echo back the filename and dummy result
    return {
        "status": "ok",
        "message": f"Received file {file.filename}",
        "records_checked": 0,
        "errors": []
    }
