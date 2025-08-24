from fastapi import HTTPException
try:
    from jarvis_plugins.json_guard import JSONGuard
except Exception:
    JSONGuard = None  # type: ignore

def ensure_json(text: str) -> dict:
    if JSONGuard is None:
        raise HTTPException(status_code=503, detail="JSONGuard unavailable")
    try:
        data, _ = JSONGuard.extract_and_validate(text)
        return data
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
