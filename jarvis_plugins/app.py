from __future__ import annotations

import os
from fastapi import FastAPI
from .middleware import AutoresurrectMiddleware
from .routers import router as plugins_router
from .daemon import attach as _daemon_attach


def build_app() -> FastAPI:
    app = FastAPI(title="Jarvis Plugins", version="0.1.0")
    app.add_middleware(AutoresurrectMiddleware)
    app.include_router(plugins_router)
    _daemon_attach(app)
    return app


# For uvicorn entrypoint: uvicorn jarvis_plugins.app:app --reload --port 8099
app = build_app()


# If you want to mount inside an existing FastAPI app:
#   from jarvis_plugins.app import build_app
#   other_app.mount("/plugins", build_app())
