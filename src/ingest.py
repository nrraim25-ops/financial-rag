"""
Ingestion: parse PDFs (text + tables) and chunk them for embedding.

Financial documents are table-heavy (holdings, returns, expense ratios).
Naive text splitters mangle tables into unreadable fragments, so tables are
extracted separately with pdfplumber and serialized as readable rows rather
than being flattened into the running text.
"""
from dataclasses import dataclass
import pdfplumber


@dataclass
class Chunk:
    text: str
    source: str
    page: int
    chunk_type: str  # "text" or "table"


def _table_to_text(table: list[list[str]]) -> str:
    if not table or not table[0]:
        return ""
    header, *rows = table
    header = [h.strip() if h else "" for h in header]
    lines = []
    for row in rows:
        row = [c.strip() if c else "" for c in row]
        pairs = [f"{h}: {v}" for h, v in zip(header, row) if h and v]
        if pairs:
            lines.append(", ".join(pairs))
    return "\n".join(lines)


def extract_pdf(path: str) -> list[Chunk]:
    """Extract text paragraphs and tables from a PDF, tagged by page."""
    chunks: list[Chunk] = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                chunks.append(Chunk(text=text.strip(), source=path, page=page_num, chunk_type="text"))

            for table in page.extract_tables():
                table_text = _table_to_text(table)
                if table_text:
                    chunks.append(Chunk(text=table_text, source=path, page=page_num, chunk_type="table"))
    return chunks


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Simple word-based sliding window splitter. Tables are NOT re-split -
    they're kept intact by the caller since breaking a table mid-row loses
    the numbers that matter most."""
    words = text.split()
    if not words:
        return []
    step = max(chunk_size - overlap, 1)
    pieces = []
    for start in range(0, len(words), step):
        piece = " ".join(words[start:start + chunk_size])
        if piece:
            pieces.append(piece)
        if start + chunk_size >= len(words):
            break
    return pieces


def chunk_document(path: str, chunk_size: int, overlap: int) -> list[Chunk]:
    """Full pipeline: extract, then split long text blocks (tables pass through whole)."""
    raw_chunks = extract_pdf(path)
    final_chunks: list[Chunk] = []

    for c in raw_chunks:
        if c.chunk_type == "table":
            final_chunks.append(c)
            continue
        for piece in split_text(c.text, chunk_size, overlap):
            final_chunks.append(Chunk(text=piece, source=c.source, page=c.page, chunk_type="text"))

    return final_chunks
