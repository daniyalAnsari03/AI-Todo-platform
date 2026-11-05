from __future__ import annotations

import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..auth import require_jwt_config
from ..database import init_db
from .tasks import router as tasks_router
from . import chat
from . import chatkit


logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s %(message)s', stream=sys.stderr, force=True)

app = FastAPI(title='Todo App API')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(tasks_router)
app.include_router(chat.router)
app.include_router(chatkit.router)


@app.on_event('startup')
def _startup():
    require_jwt_config()
    init_db()


def create_app() -> FastAPI:
    return app


def main() -> int:
    import uvicorn

    port = int(os.environ.get('PORT', '8000'))
    host = os.environ.get('HOST', '127.0.0.1')
    uvicorn.run('todo_app.api.app:app', host=host, port=port)
    return 0
