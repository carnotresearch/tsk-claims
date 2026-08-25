"""
Chat endpoints (text-to-SQL via Gemini):
  POST /api/v1/chat/sessions                    — create session
  GET  /api/v1/chat/sessions                    — list my sessions
  GET  /api/v1/chat/sessions/{id}/messages      — message history
  POST /api/v1/chat/sessions/{id}/messages      — send message
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, hospital_scope
from app.database import get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import MessageCreate, MessageResponse, SessionCreate, SessionResponse
from app.services.chat_service import handle_message
from app.services.llm import get_llm_provider

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = ChatSession(user_id=current_user.id, title=body.title or "New Chat")
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.id.desc())
    )
    return result.scalars().all()


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = (
        await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id)
    )
    return result.scalars().all()


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: int,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
):
    session = (
        await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    llm = get_llm_provider()
    assistant_msg = await handle_message(
        db=db,
        session=session,
        user_content=body.content,
        llm=llm,
        hospital_id=scope,
    )
    return assistant_msg
