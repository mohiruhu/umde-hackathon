# backend/app/routes/upload.py
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "No file selected"})

    _ = await file.read()
    
    # TODO: Optionally pass contents to /validate via internal call or shared function
    return {"message": "File received", "filename": file.filename}

