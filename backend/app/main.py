from fastapi import FastAPI
from app.routes import validate

app = FastAPI(title="UMDE Validator")

# Include the route
app.include_router(validate.router, prefix="/validate")

@app.get("/")
async def root():
    return {"message": "UMDE backend is alive 🚀"}
