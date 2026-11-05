# Task T0503
from __future__ import annotations

# Task T8105 — Spec FR-004–FR-005; Plan §Design and Execution, step 3.
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from sqlmodel import Session

from .. import auth
from ..database import get_db

router = APIRouter(tags=['chatkit'])
logger = logging.getLogger(__name__)


@router.post('/api/{user_id}/chatkit')
async def chatkit_endpoint(
    user_id: str,
    request: Request,
    claims = Depends(auth.get_token_claims),
    db: Session = Depends(get_db),
):
    try:
        if hasattr(auth, 'get_path_user'):
            try:
                auth.get_path_user(user_id, claims=claims, db=db)
            except TypeError:
                auth.get_path_user(user_id, claims=claims)
        else:
            sub = claims.get('sub') if isinstance(claims, dict) else getattr(claims, 'sub', None)
            if sub != user_id:
                raise HTTPException(status_code=403, detail='Path user does not match token')
    except HTTPException:
        raise
    except Exception:
        logger.exception('ChatKit auth check failed for user_id=%s', user_id)
        raise HTTPException(status_code=403, detail='Path user does not match token')
    try:
        from ..chat import chatkit_server
        body = await request.body()
        ctx = type('Ctx', (), {'user_id': user_id})()
        server = chatkit_server.get_server()
        result = await server.process(body, ctx)
        try:
            from chatkit.server import StreamingResult
            if isinstance(result, StreamingResult):
                return StreamingResponse(result, media_type='text/event-stream')
        except Exception:
            logger.exception('ChatKit stream detection failed for user_id=%s', user_id)
        if hasattr(result, 'json'):
            return Response(content=result.json, media_type='application/json')
        return result
    except Exception:
        logger.exception('ChatKit endpoint failed for user_id=%s', user_id)
        raise HTTPException(status_code=502, detail='ChatKit unavailable')
