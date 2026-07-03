# AI Service

FastAPI service that owns the future VAD, ASR, context, event detection, LLM, and storage pipeline.

## Run

```bash
cd services/ai-service
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
```

## Endpoints

- `GET /health`
- `POST /api/meetings`
- `WS /ws/meetings/{session_id}`
