from dotenv import load_dotenv
import os


env_file = os.getenv("ENV_FILE", ".env.local")
load_dotenv(dotenv_path=env_file)

print("✅ LOCAL_RULE_OUTPUT_PATH:", os.getenv("LOCAL_RULE_OUTPUT_PATH"))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime, timezone
from backend.app.shared.response import error_response  # ✅ use central helper

from app.routes.rule_api_publish import router as rule_publish_router

from backend.app.routes import validate
from backend.app.routes.upload import router as upload_router
from fastapi.openapi.utils import get_openapi


app = FastAPI(
    title="UMDE Validator",
    version="0.1.0"
)

def custom_openapi():
    if app.openapi_schema:
        del app.openapi_schema  # 🧨 force clear any cached version
    app.openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes
    )
    return app.openapi_schema

app.openapi = custom_openapi

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
app.include_router(rule_publish_router, prefix="/rules")


# ✅ Health check
@app.get("/ping", response_model=None)
async def ping ():
    return {
        "message": "UMDE backend is alive 🚀",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ✅ Friendly root route
@app.get("/", response_model=None)
async def root():
    return {
        "message": "Welcome to UMDE 🧠 Validator API!",
        "status": "Try /ping, /upload, or /validate",
        "docs": "/docs",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
