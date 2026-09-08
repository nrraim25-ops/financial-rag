"""
Streamlit UI for the financial-document RAG assistant.

Run:
    streamlit run app.py
"""
import os
import streamlit as st

from src.config import settings
from src.vectorstore import VectorStore
from src.rag_pipeline import RagPipeline
from src.security import RateLimiter

st.set_page_config(page_title="Financial Document Assistant", page_icon="📊", layout="centered")

# --- Rate limiter, one per server process (see README for scaling notes) ---
if "rate_limiter" not in st.session_state:
    st.session_state.rate_limiter = RateLimiter(settings.RATE_LIMIT_PER_MIN)

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

if "history" not in st.session_state:
    st.session_state.history = []


@st.cache_resource(show_spinner="Loading index...")
def load_pipeline():
    if not os.path.exists(os.path.join(settings.INDEX_DIR, "index.faiss")):
        return None
    store = VectorStore(settings.EMBEDDING_MODEL)
    store.load(settings.INDEX_DIR)
    return RagPipeline(store)


st.title("📊 Financial Document Assistant")
st.caption("RAG over fund factsheets — answers are grounded in the source documents, with citations.")

pipeline = load_pipeline()

if pipeline is None:
    st.warning(
        "No index found yet. Run `python scripts/build_index.py` in your terminal first "
        "(after adding your GOOGLE_API_KEY to .env), then reload this page."
    )
    st.stop()

for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])

query = st.chat_input("Ask about the fund's returns, holdings, fees...")

if query:
    if not st.session_state.rate_limiter.allow(st.session_state.session_id):
        st.error("Rate limit reached. Please wait a minute before asking again.")
        st.stop()

    st.session_state.history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Retrieving and generating..."):
                result = pipeline.answer(query)
            st.markdown(result.answer)

            with st.expander(f"Sources ({len(result.sources)} chunks retrieved)"):
                for i, src in enumerate(result.sources, start=1):
                    st.markdown(f"**{i}. {os.path.basename(src.source)} — page {src.page}** (`{src.chunk_type}`, score {src.score:.3f})")
                    st.text(src.text[:400] + ("..." if len(src.text) > 400 else ""))

            if result.flagged_chunks:
                st.info(
                    f"Note: {result.flagged_chunks} retrieved chunk(s) contained text patterns "
                    "resembling embedded instructions and were treated strictly as inert data."
                )

            st.session_state.history.append({"role": "assistant", "content": result.answer})
        except ValueError as e:
            st.error(f"Invalid input: {e}")
        except Exception as e:
            st.error("Something went wrong generating the answer. Please try again.")
            st.exception(e)
