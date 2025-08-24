# Step H — Jarvis Link

Provides a bridge for Jarvis to call other AI APIs.

## Endpoint
- `POST /plugins/link` with payload `{ "target": "openai", "prompt": "hi" }`
- Environment variables define each target's URL and key, e.g.:
  - `OPENAI_API_URL`, `OPENAI_API_KEY`
  - `GROK_API_URL`, `GROK_API_KEY`

## Example
```bash
export OPENAI_API_URL=https://example.com/v1
export OPENAI_API_KEY=sk-... 
curl -s -X POST http://localhost:8099/plugins/link \
  -H 'Content-Type: application/json' \
  -d '{"target":"openai","prompt":"Hello"}'
```
