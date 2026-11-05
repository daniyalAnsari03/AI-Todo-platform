# Task T0402 � Spec FR-030-FR-042 � Plan Chat service schemas
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: Optional[int] = None


class ToolCall(BaseModel):
    name: str
    arguments: dict = {}


class ChatResponse(BaseModel):
    conversation_id: int
    response: str
    tool_calls: list[dict] = []
