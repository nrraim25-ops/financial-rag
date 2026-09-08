"""
Central config. All secrets come from environment variables (loaded from .env
via python-dotenv) - NEVER hardcode API keys in source.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env in project root if present


class Settings:
    # --- LLM provider (Gemini) ---
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    # Free-tier-eligible as of writing; check https://ai.google.dev/gemini-api/docs/models
    # for the current list since Google renames/deprecates models fairly often.
    GENERATION_MODEL: str = os.getenv("GENERATION_MODEL", "gemini-2.5-flash")

    # --- Embeddings (local, no external API call -> no data leaves the machine) ---
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

    # --- Chunking ---
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "120"))

    # --- Retrieval ---
    TOP_K: int = int(os.getenv("TOP_K", "5"))

    # --- Security ---
    MAX_QUERY_CHARS: int = int(os.getenv("MAX_QUERY_CHARS", "500"))
    RATE_LIMIT_PER_MIN: int = int(os.getenv("RATE_LIMIT_PER_MIN", "20"))

    # --- Paths ---
    INDEX_DIR: str = os.getenv("INDEX_DIR", "index_store")
    DATA_DIR: str = os.getenv("DATA_DIR", "data")

    def validate(self):
        missing = []
        if not self.GOOGLE_API_KEY:
            missing.append("GOOGLE_API_KEY")
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Copy .env.example to .env and fill in your key."
            )


settings = Settings()
