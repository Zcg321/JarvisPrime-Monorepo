from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

from .savepoint import SavepointLogger
from .voice_mirror import VoiceMirror
from .json_guard import JSONGuard

router = APIRouter(prefix="/plugins", tags=["plugins"])

# Models
class SavepointIn(BaseModel):
    tag: str = Field(default="savepoint")
    payload: Dict[str, Any] = Field(default_factory=dict)

class VoiceIn(BaseModel):
    text: str

class JSONIn(BaseModel):
    text: str


sp = SavepointLogger()
vm = VoiceMirror()


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "module": "jarvis_plugins"}


@router.post("/savepoint")
def create_savepoint(body: SavepointIn):
    return sp.create(payload=body.payload, tag=body.tag)


@router.get("/savepoint/recent")
def recent_savepoints(n: int = 10):
    return {"items": sp.recent(n=n)}


@router.post("/voice/reflect")
def voice_reflect(body: VoiceIn):
    return vm.reflect(body.text)


@router.post("/tools/validate_json")
def validate_json(body: JSONIn):
    try:
        data, mode = JSONGuard.extract_and_validate(body.text)
        return {"ok": True, "mode": mode, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/debug/crash")
def debug_crash():
    raise RuntimeError("boom")

class ContractIn(BaseModel):
    text: str
    schema: str = "ToolReply"

@router.post("/tools/validate_contract")
def validate_contract(body: ContractIn):
    from .json_guard import JSONGuard
    from .contracts import validate_against_schema
    try:
        payload, _ = JSONGuard.extract_and_validate(body.text)
        valid = validate_against_schema(payload, body.schema)
        return {"ok": True, "schema": body.schema, "data": valid}
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/rag/rebuild")
def rag_rebuild():
    from .dna_sync import rebuild
    return rebuild()


@router.get("/metrics")
def metrics():
    from .metrics import snapshot
    return snapshot()
