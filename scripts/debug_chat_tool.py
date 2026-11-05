# Task T0203 · Spec FR-050–FR-057 · Plan §MCP tool contracts (382–412)
from __future__ import annotations

import asyncio
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

db_path = Path(tempfile.mkdtemp(prefix='todo-debug-')) / 'todo_debug.sqlite'
WRAPPER = """
import asyncio
import os
import sqlite3
import sys
import traceback
from pathlib import Path

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents.testing import ScriptedModel, assistant_message, function_call

ROOT = Path(__ROOT__)
SRC = ROOT / 'src'
DB_PATH = Path(__DB_PATH__)

ENV = os.environ.copy()
ENV['DATABASE_URL'] = f'sqlite:///{DB_PATH}'
ENV['PYTHONPATH'] = str(SRC) + os.pathsep + ENV.get('PYTHONPATH', '')

async def main() -> None:
    model = ScriptedModel([
        [function_call('add_task', {'title': 'Buy groceries'}, call_id='call_1')],
        [assistant_message('Added the task.')],
    ])
    from todo_app import database
    database.configure_engine(f'sqlite:///{DB_PATH}')
    database.init_db()
    server = MCPServerStdio(
        params={
            'command': sys.executable,
            'args': ['-m', 'todo_app.mcp_server'],
            'cwd': str(ROOT),
            'env': ENV,
        },
        client_session_timeout_seconds=30,
        tool_meta_resolver=lambda ctx: {'user_id': 'user-verified'},
    )
    agent = Agent(
        name='debug-mcp-agent',
        model=model,
        instructions='Use the available tool for task creation and never invent user IDs.',
        mcp_servers=[server],
    )
    try:
        async with server:
            result = await Runner.run(
                agent,
                input=[{'role': 'user', 'content': 'Add a task to buy groceries.'}],
                context={'user_id': 'user-verified'},
            )
            print('RUN_RESULT', result.final_output if hasattr(result, 'final_output') else result)
    except Exception as exc:  # pragma: no cover - debug script output
        print('EXCEPTION', type(exc).__name__, exc)
        traceback.print_exc()
    finally:
        try:
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute(
                "SELECT user_id, title, description FROM todo_item ORDER BY id"
            ).fetchall()
            print('ROWS', rows)
            conn.close()
        except Exception as exc:  # pragma: no cover - debug script output
            print('ROW_CHECK_ERROR', type(exc).__name__, exc)

asyncio.run(main())
""".replace('__ROOT__', repr(str(ROOT))).replace('__DB_PATH__', repr(str(db_path)))


def _run_debug() -> None:
    debug_env = os.environ.copy()
    debug_env['PYTHONPATH'] = str(SRC) + os.pathsep + debug_env.get('PYTHONPATH', '')
    proc = subprocess.run(
        [sys.executable, '-c', WRAPPER],
        cwd=str(ROOT),
        env=debug_env,
        capture_output=True,
        text=True,
    )
    print('=== stdout ===')
    print(proc.stdout.strip() or '<empty>')
    print('=== stderr ===')
    print(proc.stderr.strip() or '<empty>')
    print(f'=== exit={proc.returncode} ===')


if __name__ == '__main__':
    _run_debug()
