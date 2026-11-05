# Task T0402 � Spec FR-030-FR-042 � Plan Nine-step cycle (463-517)
from __future__ import annotations

import logging
from typing import Any

from sqlmodel import Session, select

from .. import models
from . import runner

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, agent=None):
        self.agent = agent

    def get_or_create_conversation(self, db: Session, user_id: str, conversation_id: int | None):
        if conversation_id is not None:
            conv = db.get(models.Conversation, conversation_id)
            if not conv or conv.user_id != user_id:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail='Conversation not found')
            return conv
        conv = models.Conversation(user_id=user_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    def load_history(self, db: Session, conversation_id: int):
        stmt = select(models.Message).where(models.Message.conversation_id == conversation_id).order_by(models.Message.created_at, models.Message.id)
        return db.exec(stmt).all()

    async def handle_chat(self, db: Session, user_id: str, message: str, conversation_id: int | None = None):
        conv = self.get_or_create_conversation(db, user_id, conversation_id)
        history = self.load_history(db, conv.id)
        # build input items (simplified)
        input_items = []
        for h in history:
            if h.role == 'user':
                input_items.append({'role': 'user', 'content': h.content})
            elif h.role == 'assistant':
                input_items.append({'role': 'assistant', 'content': h.content})
        # store user message
        user_msg = models.Message(user_id=user_id, conversation_id=conv.id, role='user', content=message)
        db.add(user_msg)
        db.commit()
        # run agent
        agent = self.agent or runner.build_agent()
        try:
            result = await runner.run_agent(agent, input_items + [{'role': 'user', 'content': message}], context={'user_id': user_id})
        except Exception:
            logger.exception('Chat agent request failed for user_id=%s', user_id)
            from fastapi import HTTPException
            raise HTTPException(status_code=502, detail='Assistant unavailable') from None
        # extract response
        response_text = getattr(result, 'final_output', None) or getattr(result, 'output', None) or str(result)
        if isinstance(response_text, list):
            # try to flatten
            try:
                response_text = ' '.join(str(x) for x in response_text)
            except Exception:
                response_text = str(response_text)
        # extract tool calls
        tool_calls = []
        try:
            for item in getattr(result, 'new_items', []) or []:
                if hasattr(item, 'type') and item.type == 'tool_call_item':
                    raw = getattr(item, 'raw_item', None)
                    name = getattr(raw, 'name', None) or getattr(item, 'name', None)
                    args = getattr(raw, 'arguments', None) or {}
                    if isinstance(args, str):
                        try:
                            import json
                            args = json.loads(args)
                        except Exception:
                            args = {}
                    tool_calls.append({'name': name, 'arguments': args})
        except Exception:
            tool_calls = []
        # store assistant
        asst_msg = models.Message(user_id=user_id, conversation_id=conv.id, role='assistant', content=str(response_text))
        db.add(asst_msg)
        try:
            conv.updated_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            db.add(conv)
        except Exception:
            logger.exception('Failed to update conversation timestamp for conversation_id=%s', conv.id)
        db.commit()
        return {'conversation_id': conv.id, 'response': str(response_text), 'tool_calls': tool_calls}
