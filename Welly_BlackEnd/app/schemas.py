from __future__ import annotations

from pydantic import BaseModel, Field


class SourceItem(BaseModel):
    table: str | None = None
    row_index: int | None = None
    retrieved_from: str | None = None
    method: str | None = None
    source: str | None = None
    title: str | None = None
    food_item: str | None = None
    doc_type: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=4, ge=1, le=10)


class ChatResponse(BaseModel):
    question: str
    intent: str
    answer: str
    sources: list[SourceItem] = Field(default_factory=list)
    llm_enabled: bool
    used_context_fallback: bool = False


class HealthResponse(BaseModel):
    status: str
    ready: bool
    llm_enabled: bool
    model_name: str
    model_path: str | None = None
    llm_model: str
    startup_error: str | None = None
    loaded_tables: list[str] = Field(default_factory=list)
