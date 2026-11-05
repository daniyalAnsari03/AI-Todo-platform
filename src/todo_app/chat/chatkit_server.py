# Task T0502 � Spec FR-010, FR-083 � Plan ChatKit server
from __future__ import annotations

# Task T8109 — Spec amendment; Plan §Approved-Scope Amendment Plan.
import logging
from contextlib import AsyncExitStack
from typing import AsyncIterator, Any

try:
    from chatkit.server import ChatKitServer
    from chatkit.agents import simple_to_agent_input, stream_agent_response, AgentContext
    from chatkit.types import ThreadMetadata, UserMessageItem, ThreadStreamEvent
except Exception:
    ChatKitServer = object

from .store import SqlModelChatKitStore
from ..database import get_engine
from . import runner

logger = logging.getLogger(__name__)


class TodoChatKitServer(ChatKitServer):
    def __init__(self):
        store = SqlModelChatKitStore(get_engine())
        super().__init__(store)

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        agent = runner.build_agent()
        items = []
        try:
            store = self.store
            page = await store.load_thread_items(thread.id, None, 50, 'asc', context)
            items = await simple_to_agent_input(page.data) if page.data else []
        except Exception:
            logger.exception('ChatKit load of thread items failed for thread_id=%s', getattr(thread, 'id', None))
            items = []
        if input_user_message is not None:
            items = (
                await simple_to_agent_input([input_user_message])
                if not items
                else items
            )
        agent_context = AgentContext(thread=thread, store=self.store, request_context=context)
        from agents import Runner

        user_id = getattr(context, 'user_id', None)
        if not user_id:
            raise ValueError('missing verified user context')
        try:
            async with AsyncExitStack() as mcp_servers:
                for mcp_server in agent.mcp_servers:
                    await mcp_servers.enter_async_context(mcp_server)
                result = Runner.run_streamed(
                    agent,
                    input=items,
                    context=agent_context,
                )
                async for event in stream_agent_response(agent_context, result):
                    yield event
        except Exception:
            logger.exception('ChatKit agent run failed for thread_id=%s', getattr(thread, 'id', None))
            raise


_server = None


def get_server():
    global _server
    if _server is None:
        _server = TodoChatKitServer()
    return _server
