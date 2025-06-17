from fastapi import APIRouter, File, UploadFile, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union,cast
import tempfile
import os
import shutil
import pandas as pd  # 🔴🆕
import json, gzip  # 🔴🆕

from backend.app.services.validator_engine import ValidatorEngine



router = APIRouter()
validator = ValidatorEngine()




validation_response_example: Dict[str, Any] = {
    "summary": {
        "file_type": "csv",
        "total_rows": 2,
        "total_errors": 3,
        "rows_with_errors": 2,
        "execution_time_sec": 0.12
    },
    "results": [
        {
            "row_index": "0",
            "errors": [
                "Missing member_id",
                {"rule_id": "TRC006", "message": "DOB is in the future"}
            ],
            "debug_time_ms": 2.14
        },
        {
            "row_index": "1",
            "errors": [],
            "debug_time_ms": 1.12
        }
    ],
    "errors_by_row": {
        "0": [
            "Missing member_id",
            "TRC006: DOB is in the future"
        ]
    },

    "benchmark": {
                    "total_validation_time_ms": 138.7,
                    "mean_row_time_ms": 1.38,
                    "p95_row_time_ms": 1.80
                }
}



# --- Pydantic Models ---

class RowError(BaseModel):
    rule_id: Optional[str] = Field(None, description="The ID of the validation rule (e.g., TRC004)")
    message: Optional[str] = Field(None, description="The human-readable explanation of the error")

    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "TRC004",
                "message": "Missing member ID"
            }
        }

class RowResult(BaseModel):
    row_index: str
    errors: Optional[List[Union[str, RowError]]]
    debug_time_ms: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "row_index": "5",
                "errors": [
                    {"rule_id": "TRC004", "message": "Missing member ID"},
                    "Invalid gender code"
                ],
                "debug_time_ms": 1.42
            }
        }

class ValidationSummary(BaseModel):
    file_type: str
    total_rows: int
    total_errors: int
    rows_with_errors: int
    execution_time_sec: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "file_type": "csv",
                "total_rows": 100,
                "total_errors": 37,
                "rows_with_errors": 21,
                "execution_time_sec": 0.85
            }
        }

class BenchmarkStats(BaseModel):
    total_validation_time_ms: float
    mean_row_time_ms: float
    p95_row_time_ms: float

    class Config:
        json_schema_extra = {
            "example": {
                "total_validation_time_ms": 138.7,
                "mean_row_time_ms": 1.38,
                "p95_row_time_ms": 1.80
            }
        }



class ValidationResponse(BaseModel):
    summary: ValidationSummary
    results: List[RowResult]
    errors_by_row: Optional[Dict[str, List[str]]] = None
    benchmark: Optional[BenchmarkStats] = None




"""
    class Config:
        json_schema_extra = {
            "example": validation_response_example,
            
        }
    
"""




# --- Internal Utilities ---

def build_row_result(
    idx: int,
    errors: List[Union[str, RowError]],
    debug_time_ms: Optional[float] = None
) -> RowResult:
    return RowResult(
        row_index=str(idx),
        errors=errors,
        debug_time_ms=debug_time_ms
    )

def prettify_errors(errors: List[Union[str, Dict[str, str]]]) -> List[str]:
    return [
        f"{err['rule_id']}: {err['message']}" if isinstance(err, dict) and "rule_id" in err else str(err)
        for err in errors
    ]

# --- Route Definition ---
@router.post (
    "/",
    summary="Validate Member Data File",
    description="Upload `.csv`, `.csv.gz`, or `.json` file for CMS TRC rule validation.",
    tags=["Validator"],
    response_model=ValidationResponse,
    response_model_exclude_unset=False,
    responses={
        200: {
            "description": "Validation response",
            "content": {
                "application/json": {
                    "example": validation_response_example
                }
            }
        }
    }



)
async def validate_file(
    file: UploadFile = File(..., description="CSV, GZipped CSV, or JSON file with member records"),
    debug: bool = Query(False, description="Include per-row timing"),
    show_errors: bool = Query(False, description="Include simplified `errors_by_row`")
) -> Union[ValidationResponse, JSONResponse]:

    if not file.filename:
        return JSONResponse(content={"error": "No file uploaded."}, status_code=400)

    filename = file.filename.lower()
    if filename.endswith(".csv"):
        input_format = "csv"
    elif filename.endswith(".csv.gz"):
        input_format = "csv.gz"
    elif filename.endswith(".json"):
        input_format = "json"
    else:
        return JSONResponse(content={"error": "Unsupported file type. Must be .csv, .csv.gz or .json"}, status_code=400)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
    except Exception as e:
        return JSONResponse(content={"error": f"File save failed: {str(e)}"}, status_code=500)

    try:
        df: pd.DataFrame  # fixes "possibly unbound"
        if input_format == "csv":
            with open(temp_path, "r", encoding="utf-8") as f:
                df = pd.read_csv(f)  #  type: ignore
        elif input_format == "csv.gz":
            with gzip.open(temp_path, "rt", encoding="utf-8") as f:
                df = pd.read_csv(f) #  type: ignore
        elif input_format == "json":
            with open(temp_path, "r", encoding="utf-8") as f:
                df = pd.DataFrame(json.load(f))

        rows = cast(List[Dict[str, Any]], df.to_dict(orient="records"))  #  type: ignore
        validator = ValidatorEngine()
        raw_result = validator.validate_rows(rows, debug=debug)

        results: List[RowResult] = []
        debug_times: List[float] = []

        for item in raw_result["results"]:
            row_index = str(item.get("row", "0"))
            error_list: List[Union[str, Dict[str, Any]]] = item.get("errors", [])
            duration = item.get("duration_ms")

            if debug and duration:
                debug_times.append(duration)

            errors: List[Union[str, RowError]] = []
            for e in error_list:
                if isinstance(e, dict) and "rule_id" in e and "message" in e:
                    rule_id = cast(Optional[str], e["rule_id"])  # fixes constructor warning
                    message = cast(Optional[str], e["message"])
                    errors.append(RowError(rule_id=rule_id, message=message))
                else:
                    errors.append(str(e))

            results.append(RowResult(row_index=row_index, errors=errors, debug_time_ms=duration))

        def _prettify(e: Union[str, RowError, Dict[str, Any]]) -> str:
            if isinstance(e, RowError):
                return f"{e.rule_id}: {e.message}"
            if isinstance(e, dict) and "rule_id" in e:
                return f"{e['rule_id']}: {e['message']}"
            return str(e)

        errors_by_row = {
            r.row_index: [_prettify(e) for e in r.errors] for r in results if r.errors
        } if show_errors else None

        summary = ValidationSummary(
            file_type=input_format,
            total_rows=len(results),
            total_errors=sum(len(r.errors) if r.errors else 0 for r in results),
            rows_with_errors=sum(1 for r in results if r.errors),
            execution_time_sec=round(sum(debug_times) / 1000, 2) if debug_times else None
        )

        benchmark = BenchmarkStats(
            total_validation_time_ms=round(sum(debug_times), 2),
            mean_row_time_ms=round(sum(debug_times) / len(debug_times), 2),
            p95_row_time_ms=sorted(debug_times)[int(len(debug_times) * 0.95) - 1]
        ) if debug_times else None

        return ValidationResponse(
            summary=summary,
            results=results,
            errors_by_row=errors_by_row,
            benchmark=benchmark
        )

    except Exception as e:
        return JSONResponse(content={"error": f"Validation error: {str(e)}"}, status_code=500)




