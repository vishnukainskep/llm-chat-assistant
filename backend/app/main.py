from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import config
from app.routes.ask import router as ask_router

app = FastAPI(title="Gemini FastAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "FastAPI backend is running"}

# Test POST endpoint
@app.post("/test")
def test_post(data: dict):
    return {"received": data}

# Include the ask router
app.include_router(ask_router)
