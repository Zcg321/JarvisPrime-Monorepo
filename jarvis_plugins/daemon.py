from __future__ import annotations
import asyncio, os, time
from typing import Optional
from .savepoint import SavepointLogger

INTERVAL_SEC = int(os.getenv("JARVIS_DAEMON_INTERVAL", "60"))

async def _loop():
    sp = SavepointLogger()
    while True:
        try:
            sp.create({"heartbeat": time.time()}, tag="daemon")
        except Exception:
            pass
        await asyncio.sleep(INTERVAL_SEC)

def attach(app):
    @app.on_event("startup")
    async def _start():
        if os.getenv("JARVIS_DAEMON_ENABLE", "0") == "1":
            app.state._daemon_task = asyncio.create_task(_loop())
    @app.on_event("shutdown")
    async def _stop():
        t = getattr(app.state, "_daemon_task", None)
        if t: t.cancel()
