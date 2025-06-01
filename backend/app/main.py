from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import validate
from routes.upload import router as upload_router  # ✅ using FastAPI-style router


app = FastAPI(title="UMDE Validator")

# ✅ CORS middleware (FastAPI native)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register FastAPI routers
app.include_router(upload_router, prefix="/upload")
app.include_router(validate.router, prefix="/validate")

@app.get("/")
async def root():
    return {"message": "UMDE backend is alive 🚀"}
