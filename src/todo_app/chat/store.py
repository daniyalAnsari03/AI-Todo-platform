# Task T0501 � Spec FR-010, FR-083 � Plan ChatKit store
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlmodel import Session, select

from .. import models


class SqlModelChatKitStore:
    def __init__(self, engine):
        self.engine = engine

    def _session(self):
        from sqlmodel import Session
        return Session(self.engine)

    def generate_thread_id(self, context: Any) -> str:
        return f'thread_{uuid.uuid4()}'

    def generate_item_id(self, item_type: Any, thread: Any, context: Any) -> str:
        return f'item_{uuid.uuid4()}'

    async def load_thread(self, thread_id: str, context: Any):
        from chatkit.types import ThreadMetadata
        with self._session() as db:
            conv = None
            # try numeric
            try:
                if thread_id.isdigit():
                    conv = db.get(models.Conversation, int(thread_id))
            except Exception:
                import logging
                logging.getLogger(__name__).exception('Failed to load thread %s as numeric conversation', thread_id)
            if not conv:
                stmt = select(models.Conversation).where(models.Conversation.chat_thread_id == thread_id)
                conv = db.exec(stmt).first()
            if not conv:
                raise Exception('not found')
            return ThreadMetadata(id=thread_id, created_at=conv.created_at)

    async def save_thread(self, thread: Any, context: Any):
        with self._session() as db:
            user_id = getattr(context, 'user_id', None)
            # try to find
            conv = None
            try:
                tid = getattr(thread, 'id')
                if isinstance(tid, str) and tid.isdigit():
                    conv = db.get(models.Conversation, int(tid))
            except Exception:
                import logging
                logging.getLogger(__name__).exception('Failed to resolve saved thread for %s', getattr(thread, 'id', None))
            if not conv and user_id:
                stmt = select(models.Conversation).where(models.Conversation.chat_thread_id == getattr(thread, 'id'))
                conv = db.exec(stmt).first()
            if not conv:
                conv = models.Conversation(user_id=user_id, chat_thread_id=getattr(thread, 'id'))
                db.add(conv)
            else:
                if not conv.chat_thread_id:
                    conv.chat_thread_id = getattr(thread, 'id')
                db.add(conv)
            db.commit()

    async def load_threads(self, limit: int, after: str | None, order: str, context: Any):
        from chatkit.store import Page
        from chatkit.types import ThreadMetadata
        with self._session() as db:
            user_id = getattr(context, 'user_id', None)
            stmt = select(models.Conversation).where(models.Conversation.user_id == user_id)
            convs = db.exec(stmt).all()
            data = []
            for c in convs:
                tid = c.chat_thread_id or str(c.id)
                data.append(ThreadMetadata(id=tid, created_at=c.created_at))
            return Page(data=data, has_more=False)

    async def load_thread_items(self, thread_id: str, after: str | None, limit: int, order: str, context: Any):
        from chatkit.store import Page
        with self._session() as db:
            conv = await self._get_conv(db, thread_id)
            if not conv:
                raise Exception('not found')
            stmt = select(models.Message).where(models.Message.conversation_id == conv.id).order_by(models.Message.created_at, models.Message.id)
            msgs = db.exec(stmt).all()
            items = []
            try:
                from chatkit.types import UserMessageItem, AssistantMessageItem
                from chatkit.types import UserMessageTextContent, AssistantMessageContent
                for m in msgs:
                    if m.role == 'user':
                        items.append(UserMessageItem(id=str(m.id), thread_id=thread_id, content=[UserMessageTextContent(text=m.content)], created_at=m.created_at, attachments=[], inference_options={}))
                    elif m.role == 'assistant':
                        items.append(AssistantMessageItem(id=str(m.id), thread_id=thread_id, content=[AssistantMessageContent(text=m.content, annotations=[])], created_at=m.created_at))
            except Exception:
                import logging
                logging.getLogger(__name__).exception('Failed to serialize thread items for thread_id=%s', thread_id)
            return Page(data=items, has_more=False)

    async def add_thread_item(self, thread_id: str, item: Any, context: Any):
        with self._session() as db:
            conv = await self._get_conv(db, thread_id)
            if not conv:
                raise Exception('not found')
            user_id = conv.user_id
            try:
                itype = getattr(item, 'type')
                if itype == 'user_message':
                    content = ''
                    for c in getattr(item, 'content', []) or []:
                        if hasattr(c, 'text'):
                            content += c.text
                    msg = models.Message(user_id=user_id, conversation_id=conv.id, role='user', content=content)
                    db.add(msg)
                elif itype == 'assistant_message':
                    content = ''
                    for c in getattr(item, 'content', []) or []:
                        if hasattr(c, 'text'):
                            content += c.text
                    msg = models.Message(user_id=user_id, conversation_id=conv.id, role='assistant', content=content)
                    db.add(msg)
            except Exception:
                import logging
                logging.getLogger(__name__).exception('Failed to persist thread item for thread_id=%s', thread_id)
            db.commit()

    async def save_item(self, thread_id: str, item: Any, context: Any):
        await self.add_thread_item(thread_id, item, context)

    async def load_item(self, thread_id: str, item_id: str, context: Any):
        raise Exception('not implemented')

    async def delete_thread(self, thread_id: str, context: Any):
        with self._session() as db:
            conv = await self._get_conv(db, thread_id)
            if conv:
                db.delete(conv)
                db.commit()

    async def delete_thread_item(self, thread_id: str, item_id: str, context: Any):
        pass

    async def save_attachment(self, attachment: Any, context: Any):
        raise NotImplementedError()

    async def load_attachment(self, attachment_id: str, context: Any):
        raise NotImplementedError()

    async def delete_attachment(self, attachment_id: str, context: Any):
        raise NotImplementedError()

    async def _get_conv(self, db: Session, thread_id: str):
        try:
            if thread_id.isdigit():
                c = db.get(models.Conversation, int(thread_id))
                if c:
                    return c
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Failed to look up conversation by numeric thread_id=%s', thread_id)
        stmt = select(models.Conversation).where(models.Conversation.chat_thread_id == thread_id)
        return db.exec(stmt).first()
