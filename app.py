
import os
import streamlit as st

from src.config import settings
from src.vectorstore import VectorStore
from src.rag_pipeline import RagPipeline
from src.security import RateLimiter

st.set_page_config(page_title="Bluepeak Fund Assistant", page_icon="📊", layout="centered")

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* App title block */
.app-header {
    padding: 1.5rem 0 1rem 0;
    border-bottom: 1px solid #E4E1DA;
    margin-bottom: 1.5rem;
}
.app-header h1 {
    font-size: 1.6rem;
    font-weight: 600;
    color: #1F2430;
    margin-bottom: 0.15rem;
}
.app-header p {
    font-size: 0.9rem;
    color: #6B7280;
    margin: 0;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
    border: 1px solid #E4E1DA;
}

/* Buttons */
.stButton>button, [data-testid="stChatInput"] textarea {
    border-radius: 8px;
}

/* Source citation chips */
.source-chip {
    display: inline-block;
    background: #F0EEE7;
    border: 1px solid #E4E1DA;
    border-radius: 6px;
    padding: 0.2rem 0.6rem;
    margin: 0.15rem 0.3rem 0.15rem 0;
    font-size: 0.78rem;
    color: #1F2430;
}
.source-chip b { color: #8A6D2F; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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


st.markdown(
    """
    <div class="app-header">
        <h1>Bluepeak Fund Assistant</h1>
        <p>Answers are grounded in the loaded fund documents, with page-level citations.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

pipeline = load_pipeline()

if pipeline is None:
    st.info(
        "**No documents indexed yet.**\n\n"
        "Run `python scripts/build_index.py` in your terminal, then reload this page."
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

            chip_html = "".join(
                f'<span class="source-chip"><b>p.{src.page}</b> {os.path.basename(src.source)}</span>'
                for src in result.sources
            )
            st.markdown(chip_html, unsafe_allow_html=True)
            with st.expander("View retrieved passages"):
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
