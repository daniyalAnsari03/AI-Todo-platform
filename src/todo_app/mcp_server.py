# Task T0201 · Spec FR-050–FR-057 · Plan §MCP tool contracts (382–412)
from __future__ import annotations

import logging
import re
import sys

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.context import Context

from . import task_service
from .database import get_engine
from sqlmodel import Session

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s %(message)s', stream=sys.stderr, force=True)

mcp = MCPServer("todo-tasks")
logger = logging.getLogger(__name__)


def _safe_error_message(err: Exception | str | None) -> str:
    text = str(err or '')
    text = re.sub(r"(?i)sk-[A-Za-z0-9]+", 'sk-[REDACTED]', text)
    text = re.sub(r"(?i)(token|secret|key)\s*[:=]\s*['\"]?[^\s,;]+", r'\1=[REDACTED]', text)
    text = re.sub(r"(?i)DATABASE_URL\s*[:=]\s*[^\s,;]+", 'DATABASE_URL=[REDACTED]', text)
    return text


def _safe_exception_for_logging(err: BaseException) -> BaseException:
    args = getattr(err, 'args', ()) or ()
    sanitized_args = tuple(_safe_error_message(arg) for arg in args)
    try:
        return type(err)(*sanitized_args)
    except TypeError:
        return type(err)(str(sanitized_args[0]) if sanitized_args else '')


def _log_redacted_exception(err: BaseException, message: str) -> None:
    safe_err = _safe_exception_for_logging(err)
    logger.exception(message, _safe_error_message(str(err)), exc_info=(type(err), safe_err, err.__traceback__))


def _extract_meta_from_context(context: Context | None = None) -> dict | None:
    if context is None:
        return None

    meta = getattr(context, 'meta', None)
    if isinstance(meta, dict):
        return meta

    request_context = getattr(context, 'request_context', None)
    if request_context is not None:
        meta = getattr(request_context, 'meta', None)
        if isinstance(meta, dict):
            return meta
        params = getattr(request_context, 'params', None)
        if isinstance(params, dict):
            maybe_meta = params.get('_meta')
            if isinstance(maybe_meta, dict):
                return maybe_meta

    return None


def _resolve_tool_user_id(user_id: str | None, context: Context | None = None) -> str:
    meta = _extract_meta_from_context(context)
    meta_user_id = None if meta is None else meta.get('user_id') or meta.get('user')
    if user_id is not None:
        explicit = str(user_id)
        if meta_user_id is not None and str(meta_user_id) != explicit:
            raise ValueError('user_id mismatch between request metadata and tool arguments')
        return explicit
    if meta_user_id is not None:
        return str(meta_user_id)
    raise ValueError('missing user_id in request context')


def _get_session():
    engine = get_engine()
    return Session(engine)


@mcp.tool()
def add_task(user_id: str | None = None, title: str | None = None, description: str | None = None, *, context: Context | None = None) -> dict:
    try:
        resolved_user_id = _resolve_tool_user_id(user_id, context)
        if title is None:
            raise task_service.InvalidTaskInput('title required')
        with _get_session() as session:
            res = task_service.add_task(session, resolved_user_id, title, description)
            return res
    except task_service.InvalidTaskInput as e:
        _log_redacted_exception(e, 'add_task failed: %s')
        return {"error": "invalid_input", "message": str(e)}
    except Exception as e:
        _log_redacted_exception(e, 'add_task failed: %s')
        return {"error": "invalid_input", "message": "invalid input"}


@mcp.tool()
def list_tasks(user_id: str | None = None, status: str = "all", *, context: Context | None = None) -> dict:
    try:
        resolved_user_id = _resolve_tool_user_id(user_id, context)
        with _get_session() as session:
            res = task_service.list_tasks(session, resolved_user_id, status=status)
            return {"tasks": res}
    except task_service.InvalidTaskInput as e:
        _log_redacted_exception(e, 'list_tasks failed: %s')
        return {"error": "invalid_input", "message": str(e)}
    except Exception as e:
        _log_redacted_exception(e, 'list_tasks failed: %s')
        return {"error": "invalid_input", "message": "invalid input"}


@mcp.tool()
def complete_task(user_id: str | None = None, task_id: int | None = None, *, context: Context | None = None) -> dict:
    try:
        resolved_user_id = _resolve_tool_user_id(user_id, context)
        if task_id is None:
            raise task_service.InvalidTaskInput('task_id required')
        with _get_session() as session:
            res = task_service.complete_task(session, resolved_user_id, task_id)
            return res
    except task_service.TaskNotFound:
        return {"error": "not_found", "message": "task not found"}
    except Exception as e:
        _log_redacted_exception(e, 'complete_task failed: %s')
        return {"error": "not_found", "message": "task not found"}


@mcp.tool()
def delete_task(user_id: str | None = None, task_id: int | None = None, *, context: Context | None = None) -> dict:
    try:
        resolved_user_id = _resolve_tool_user_id(user_id, context)
        if task_id is None:
            raise task_service.InvalidTaskInput('task_id required')
        with _get_session() as session:
            res = task_service.delete_task(session, resolved_user_id, task_id)
            return res
    except task_service.TaskNotFound:
        return {"error": "not_found", "message": "task not found"}
    except Exception as e:
        _log_redacted_exception(e, 'delete_task failed: %s')
        return {"error": "not_found", "message": "task not found"}


@mcp.tool()
def update_task(user_id: str | None = None, task_id: int | None = None, title: str | None = None, description: str | None = None, *, context: Context | None = None) -> dict:
    if title is None and description is None:
        return {"error": "invalid_input", "message": "no fields to update"}
    try:
        resolved_user_id = _resolve_tool_user_id(user_id, context)
        if task_id is None:
            raise task_service.InvalidTaskInput('task_id required')
        with _get_session() as session:
            res = task_service.update_task(session, resolved_user_id, task_id, title=title, description=description)
            return res
    except task_service.TaskNotFound:
        return {"error": "not_found", "message": "task not found"}
    except task_service.InvalidTaskInput as e:
        _log_redacted_exception(e, 'update_task failed: %s')
        return {"error": "invalid_input", "message": str(e)}
    except Exception as e:
        _log_redacted_exception(e, 'update_task failed: %s')
        return {"error": "invalid_input", "message": "invalid input"}


if __name__ == "__main__":
    mcp.run()
