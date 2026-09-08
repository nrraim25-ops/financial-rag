# Financial Document RAG Assistant (Starter)

A small, working RAG pipeline for answering questions over financial
documents (fund factsheets, SIDs, etc.), built as a hackathon/interview
starting point. Comes with a synthetic sample fund factsheet so it runs
end-to-end with zero manual data prep.

**This is a template.** In a real 24-hour test, you'll swap in whatever data
you're given, adjust the prompt/chunking to that domain, and extend from
here — you should not turn this in as-is.

## Architecture

```
PDF(s) in data/
   │
   ▼
src/ingest.py       -- extract text + tables (table-aware, since financial
   │                    PDFs are full of tables that naive splitters mangle)
   ▼
src/vectorstore.py  -- chunk -> local embeddings (sentence-transformers)
   │                    -> FAISS index (swap-in interface for a hosted
   │                    vector DB later, see "Scaling" below)
   ▼
src/rag_pipeline.py -- retrieve top-k chunks -> build a guarded prompt ->
   │                    call Gemini for grounded generation, with citations
   ▼
app.py              -- Streamlit chat UI, with rate limiting + source panel
```

## Setup (VS Code / local)

1. **Clone and enter the repo**
   ```bash
   git clone <your-repo-url>
   cd financial-rag-starter
   ```

2. **Create a virtual environment** (VS Code will usually prompt you to do
   this automatically when you open the folder — pick "Yes" — or do it
   manually):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # on Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key**
   ```bash
   cp .env.example .env
   ```
   Open `.env` in VS Code and paste your Gemini API key into
   `GOOGLE_API_KEY`. Get a free one at https://aistudio.google.com/apikey
   if you don't have one. **Never commit `.env`** — it's already in
   `.gitignore`.

5. **Generate the sample document** (already generated once, but you can
   regenerate anytime):
   ```bash
   python scripts/generate_sample_pdf.py
   ```
   This writes `data/sample_fund_factsheet.pdf` — a fictional mutual fund
   factsheet with fund facts, performance, and top holdings tables, used to
   test the pipeline end-to-end.

6. **Build the index**
   ```bash
   python scripts/build_index.py
   ```
   This reads every PDF in `data/`, chunks it, embeds it locally, and saves
   a FAISS index to `index_store/`. Re-run this any time you add/change
   documents.

7. **Run the app**
   ```bash
   streamlit run app.py
   ```
   This opens a browser tab (usually `http://localhost:8501`). Try asking:
   - "What is the expense ratio for the direct plan?"
   - "What are the top 3 holdings?"
   - "What was the 5 year CAGR versus the benchmark?"
   - "What is the fund's phone number?" (should say it's not in the
     documents — this checks your hallucination guardrail works)

8. **Run the tests**
   ```bash
   pytest tests/ -v
   ```

## Push to GitHub

```bash
git init
git add .
git commit -m "Financial RAG starter"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

Before pushing, double check `.env` is NOT staged:
```bash
git status   # .env should NOT appear in the list
```
If it does, run `git rm --cached .env` before committing.

## Security notes (what's implemented, and what to say out loud in your pitch)

| Concern | What this repo does |
|---|---|
| Secret management | Gemini API key loaded only from `.env` / environment variables, never hardcoded. `.env` is git-ignored. Docker image never bakes in secrets — injected at runtime. |
| Prompt injection via documents | Retrieved chunks are wrapped in explicit `<document_chunk>` delimiters and the system prompt tells the model to treat that block as inert data, never instructions. A lightweight regex flag also surfaces chunks containing injection-like phrases so a human can review them (`src/security.py`). |
| Input abuse / oversized queries | `sanitize_query()` strips control characters and hard-caps query length before it ever reaches the LLM call. |
| Rate limiting / cost control | Simple per-session in-memory limiter (`RateLimiter`) caps requests per minute. Called out in code as needing to move to Redis for a multi-instance deployment. |
| Hallucinated financial figures | System prompt explicitly forbids answering numeric questions from outside knowledge and requires the model to say "not in the provided documents" when the context doesn't contain the answer. Citations (page numbers) are shown for every answer so a user can verify. |
| Least privilege / container hygiene | Dockerfile runs as a non-root user; no secrets in image layers. |
| Data governance | Embeddings run **locally** via sentence-transformers — raw document text is never sent to a third party just to compute embeddings. Only the final retrieved snippets + the user's question go to the LLM API. |

Things you'd add with more time (good to mention in the interview even if
unbuilt): PII detection/redaction on both queries and documents, structured
audit logging of every Q&A pair for compliance review, an actual auth layer
(this demo has no login), and a moderation/guardrail model pass on outputs
before they're shown to the user.

## Scaling notes (what to say if asked "how would this handle 10,000 users?")

- **Stateless app layer**: `app.py` holds no persistent state beyond the
  Streamlit session — you can run N replicas behind a load balancer.
- **Vector store**: FAISS-on-disk is fine for a demo/single fund. For
  production scale (many funds, frequent updates, multi-instance reads),
  swap `VectorStore` for a managed vector DB (Pinecone, Weaviate, Milvus, or
  pgvector) — the class already exposes a narrow `build/search/save/load`
  interface so this is a contained change, not a rewrite.
- **Ingestion as a job, not a request**: document ingestion/embedding
  (`scripts/build_index.py`) should run as an async batch job / queue
  consumer in production, not inline with user requests, so a large new
  document upload doesn't block the chat API.
- **Caching**: identical/near-identical queries can be cached (embedding +
  answer) to cut both latency and LLM cost — not implemented here, but a
  natural next step (e.g. a Redis cache keyed on the sanitized query).
- **Rate limiting**: move `RateLimiter` from in-memory to Redis so limits
  are enforced globally across replicas, not per-process.
- **Observability**: add structured logging + tracing (e.g. latency per
  pipeline stage: retrieval vs. generation) so you can see where scaling
  bottlenecks actually are before optimizing blindly.

## What's intentionally minimal (say this out loud, don't hide it)

- No hybrid (BM25 + dense) retrieval or reranking yet — good extension if
  you have time on the day, since financial queries often mix exact terms
  ("Nifty 500 TRI") with semantic ones.
- No auth/user management.
- Single-node FAISS, not a production vector DB.
- No async/streaming responses in the UI yet.

Being explicit about these tradeoffs and *why* you made them under a 24-hour
constraint is usually worth more to interviewers than silently shipping a
more "complete" but unexplained system.
