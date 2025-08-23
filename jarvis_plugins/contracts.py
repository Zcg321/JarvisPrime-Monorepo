from __future__ import annotations
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError

# Example, extensible schemas. Add your tool schemas here.
class ToolReply(BaseModel):
    tool: str = Field(..., min_length=1, description="Tool name to invoke")
    args: Dict[str, Any] = Field(default_factory=dict, description="JSON-serializable arguments")
    trace_id: Optional[str] = Field(None, description="Optional trace for lineage")

# Registry for named schemas
SCHEMAS = {
    "ToolReply": ToolReply,
}

def validate_against_schema(obj: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
    if schema_name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {schema_name}")
    model = SCHEMAS[schema_name]
    inst = model.model_validate(obj)
    return inst.model_dump()
