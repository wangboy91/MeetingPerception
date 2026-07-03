from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.http import router as http_router
from app.api.websocket import router as websocket_router

app = FastAPI(title="Meeting Copilot AI Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "http://127.0.0.1:1420"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(http_router)
app.include_router(websocket_router)
