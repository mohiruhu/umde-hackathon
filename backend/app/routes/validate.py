from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import csv
import io

from services.validator_engine import ValidatorEngine


router = APIRouter()
engine = ValidatorEngine()  # ✅ Create engine instance

@router.get("/ping")
async def ping():
    return {"message": "Validator route ready"}

@router.post("/")
async def validate_file(file: UploadFile = File(...)):
    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "No file uploaded"})

    try:
        content = await file.read()
        decoded = content.decode()
        reader = csv.DictReader(io.StringIO(decoded))
        rows = list(reader)

        results = engine.validate_rows(rows)

        return {
            "status": "ok",
            "filename": file.filename,
            "records_checked": len(rows),
            "errors_found": sum(1 for r in results if not r["valid"]),
            "results": results
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
