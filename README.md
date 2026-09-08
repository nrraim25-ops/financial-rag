# Financial Document RAG Assistant

RAG pipeline for answering questions over financial documents (fund factsheets, SIDs, etc.), with grounded, cited answers via Gemini. Ships with a synthetic sample fund factsheet so it runs end-to-end out of the box.

## Architecture

```
PDF(s) in data/
   │
   ▼
ingest.py       -- table-aware text + table extraction (pdfplumber)
   ▼
vectorstore.py  -- chunk -> local embeddings (sentence-transformers) -> FAISS
   ▼
rag_pipeline.py -- retrieve top-k -> guarded prompt -> Gemini generation w/ citations
   ▼
app.py          -- Streamlit chat UI
```

## Setup

```bash
git clone https://github.com/nrraim25-ops/financial-rag-starter.git
cd financial-rag-starter
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # add your GOOGLE_API_KEY (free: https://aistudio.google.com/apikey)
python scripts/build_index.py    # builds the FAISS index from data/*.pdf
streamlit run app.py
```

Run tests:
```bash
pytest tests/ -v
```

## Security

- API key loaded from `.env` only, never hardcoded; `.env` is git-ignored.
- Query input sanitized and length-capped before hitting the LLM.
- Retrieved document chunks are wrapped in explicit delimiters and the system prompt instructs the model to treat them as data, never instructions (prompt-injection mitigation). Suspicious chunks are flagged.
- Per-session rate limiting on requests.
- Model is instructed to answer only from retrieved context and say when something isn't in the documents, rather than guessing numbers.
- Docker image runs as non-root; no secrets baked into the image.

## Scaling

- `VectorStore` exposes a narrow `build/search/save/load` interface — swapping FAISS for a managed vector DB (Pinecone, Weaviate, pgvector) is a single-file change.
- App layer is stateless; can run multiple replicas behind a load balancer.
- Ingestion (`build_index.py`) should run as an async job/queue consumer in production, not inline with requests.
- Rate limiter is in-memory here; move to Redis for multi-instance deployments.

## Known limitations

- No hybrid (BM25 + dense) retrieval or reranking yet.
- No auth/user management.
- Single-node FAISS, not a production vector DB.
- No streaming responses in the UI.

## License

MIT
