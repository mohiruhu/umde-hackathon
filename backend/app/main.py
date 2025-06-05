from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime, timezone
from utils.response import error_response  # ✅ use central helper

from routes import validate
from routes.upload import router as upload_router

app = FastAPI(title="UMDE Validator")

# ✅ CORS middleware (FastAPI native)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Exception Handlers

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response(
        status_code=422,
        path=str(request.url.path),
        error="Validation failed",
        details=exc.errors()
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return error_response(
        status_code=exc.status_code,
        path=str(request.url.path),
        error=exc.detail,
        details=[]
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return error_response(
        status_code=500,
        path=str(request.url.path),
        error="An unexpected error occurred",
        details=[{"message": str(exc)}]
    )

# ✅ Routers
app.include_router(upload_router, prefix="/upload")
app.include_router(validate.router, prefix="/validate")

# ✅ Health check
@app.get("/")
async def root():
    return {
        "message": "UMDE backend is alive 🚀",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
