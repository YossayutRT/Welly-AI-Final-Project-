# Welly FastAPI Backend

## Run

```bash
cd Welly_BlackEnd
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Environment

Copy `.env.example` into your shell environment or set the variables manually.

- Put `.env` in either the project root or `Welly_BlackEnd/.env`; the backend now loads both automatically.
- `GROQ_API_KEY`: optional for LLM-generated answers. If missing, the backend still starts and returns retrieval-based fallback answers.
- `WELLY_EMBEDDINGS_LOCAL_ONLY`: defaults to `true` so the backend can reuse locally cached embedding models.
- `WELLY_MODEL_PATH`: optional absolute path to a local embedding model snapshot. If unset, the backend will try to resolve the model from the Hugging Face cache automatically.
