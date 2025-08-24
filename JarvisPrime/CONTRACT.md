# CodeOps Contract

```json
{
  "summary": "...",
  "files": [
    {"path": "...", "op": "write|append|delete", "encoding": "utf-8|base64", "content": "..."}
  ],
  "commands": ["pytest -q", "npm test --silent"],
  "next_suggestion": "..."
}
```

Paths must be relative (no `..`). The executor will touch at most 15 files per task.
