from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SessionCreate(BaseModel):
    title: str | None = None


class SessionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    title: str | None
    created_at: datetime


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    session_id: int
    role: str
    content: str
    sql_generated: str | None
    result_rows: list | None
    created_at: datetime
