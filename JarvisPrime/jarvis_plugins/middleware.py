from __future__ import annotations
import traceback, json, time
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

try:
    from .savepoint import SavepointLogger
    _SP = SavepointLogger()
except Exception:
    _SP = None  # optional

class AutoresurrectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        try:
            return await call_next(request)
        except Exception as e:
            tb = traceback.format_exc()
            payload = {
                "when": time.time(),
                "error": str(e),
                "traceback": tb,
                "path": request.url.path,
                "method": request.method,
                "query": dict(request.query_params),
                "headers": {k: v for k, v in request.headers.items() if k.lower() in ["content-type","user-agent"]},
            }
            if _SP:
                try:
                    _SP.create(payload, tag="server-crash")
                except Exception:
                    pass
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False,
                    "error": "internal_error",
                    "message": "An unexpected error occurred. A savepoint was recorded.",
                    "path": payload["path"],
                },
            )
