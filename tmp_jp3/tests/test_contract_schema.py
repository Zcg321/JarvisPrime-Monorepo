from typing import List, Literal

from pydantic import BaseModel, ValidationError


class FileSpec(BaseModel):
    path: str
    op: Literal["write", "append", "delete"]
    encoding: Literal["utf-8", "base64"]
    content: str = ""


class TaskContract(BaseModel):
    summary: str
    files: List[FileSpec]
    commands: List[str]
    next_suggestion: str


def test_contract_schema():
    good = {
        "summary": "hi",
        "files": [{
            "path": "foo.txt",
            "op": "write",
            "encoding": "utf-8",
            "content": "hello"
        }],
        "commands": ["echo hi"],
        "next_suggestion": "next"
    }
    assert TaskContract.model_validate(good)
    bad = good.copy()
    bad["files"][0]["op"] = "oops"
    try:
        TaskContract.model_validate(bad)
    except ValidationError:
        return
    assert False, "validation should fail"
