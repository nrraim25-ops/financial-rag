"""
Build (or rebuild) the FAISS index from all PDFs in the data/ directory.

Run this once after adding/changing documents:
    python scripts/build_index.py
"""
import os
import sys
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import settings
from src.ingest import chunk_document
from src.vectorstore import VectorStore


def main():
    pdf_paths = glob.glob(os.path.join(settings.DATA_DIR, "*.pdf"))
    if not pdf_paths:
        print(f"No PDFs found in {settings.DATA_DIR}/. Add a PDF and re-run.")
        return

    all_chunks = []
    for path in pdf_paths:
        print(f"Ingesting {path} ...")
        chunks = chunk_document(path, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        print(f"  -> {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"Embedding {len(all_chunks)} chunks with {settings.EMBEDDING_MODEL} ...")
    store = VectorStore(settings.EMBEDDING_MODEL)
    store.build(all_chunks)
    store.save(settings.INDEX_DIR)
    print(f"Index saved to {settings.INDEX_DIR}/")


if __name__ == "__main__":
    main()
