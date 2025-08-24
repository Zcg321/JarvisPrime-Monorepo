from typing import Dict, Any, Type
from pydantic import BaseModel

REGISTRY: Dict[str, Dict[str, Any]] = {}


def register(name: str, args_model: Type[BaseModel], response_schema: Dict[str, Any]) -> None:
    REGISTRY[name] = {
        "name": name,
        "version": "v1",
        "args_schema": args_model.schema(),
        "response_schema": response_schema,
    }


def list_tools() -> Dict[str, Any]:
    return {"tools": list(REGISTRY.values())}
