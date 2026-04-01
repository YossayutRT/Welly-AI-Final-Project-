from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .schemas import ChatRequest, ChatResponse, HealthResponse
from .service import WellyRAGService

logging.basicConfig(level=logging.INFO)

settings = get_settings()
rag_service = WellyRAGService(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        rag_service.initialize()
    except Exception as exc:
        rag_service.startup_error = str(exc)
        logging.exception("Backend startup failed")
    app.state.rag_service = rag_service
    yield


app = FastAPI(
    title="Welly AI Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(**rag_service.health())


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    if not rag_service.ready:
        detail = rag_service.startup_error or "Backend is still loading"
        raise HTTPException(status_code=503, detail=detail)

    response = rag_service.ask(payload.message, k=payload.k)
    return ChatResponse(**response)


@app.get("/api/suggestions")
def suggestions(query: str = Query(min_length=1, max_length=200)) -> dict[str, list[str]]:
    if not rag_service.ready:
        detail = rag_service.startup_error or "Backend is still loading"
        raise HTTPException(status_code=503, detail=detail)
    return {"items": rag_service.suggest_food_names(query)}
