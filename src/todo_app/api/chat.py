# Task T0403
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from .. import auth
from ..database import get_db
from ..chat.schemas import ChatRequest, ChatResponse
from ..chat.service import ChatService

router = APIRouter(tags=['chat'])
logger = logging.getLogger(__name__)


@router.post('/api/{user_id}/chat', response_model=ChatResponse)
async def chat_endpoint(
    user_id: str,
    request: Request,
    claims = Depends(auth.get_token_claims),
    db: Session = Depends(get_db),
):
    try:
        if hasattr(auth, 'get_path_user'):
            try:
                user = auth.get_path_user(user_id, claims=claims, db=db)
            except TypeError:
                user = auth.get_path_user(user_id, claims=claims)
        else:
            sub = claims.get('sub') if isinstance(claims, dict) else getattr(claims, 'sub', None)
            if sub != user_id:
                raise HTTPException(status_code=403, detail='Path user does not match token')
    except HTTPException:
        raise
    except Exception:
        logger.exception('Chat auth check failed for user_id=%s', user_id)
        raise HTTPException(status_code=403, detail='Path user does not match token')
    try:
        body = await request.json()
    except Exception:
        logger.exception('Chat request JSON failed for user_id=%s', user_id)
        raise HTTPException(status_code=400, detail='Invalid request')
    try:
        req = ChatRequest(**body)
    except Exception:
        logger.exception('Chat request validation failed for user_id=%s', user_id)
        raise HTTPException(status_code=400, detail='Invalid request')
    if not req.message or not str(req.message).strip():
        raise HTTPException(status_code=400, detail='message required')
    service = ChatService()
    try:
        result = await service.handle_chat(db, user_id, str(req.message).strip(), req.conversation_id)
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception('Chat endpoint failed for user_id=%s', user_id)
        raise HTTPException(status_code=502, detail='Assistant unavailable')
