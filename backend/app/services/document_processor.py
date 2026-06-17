import io
from pathlib import Path
from typing import Optional

import tiktoken

from app.config import settings


def extract_text(file_path: str, file_type: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_type == "txt":
        return path.read_text(encoding="utf-8", errors="replace")

    if file_type == "pdf":
        return _extract_pdf(path)

    if file_type == "docx":
        return _extract_docx(path)

    raise ValueError(f"Unsupported file type: {file_type}")


def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            texts.append(text)
    return "\n\n".join(texts)


def _extract_docx(path: Path) -> str:
    from docx import Document
    doc = Document(str(path))
    return "\n\n".join(p.text for p in doc.paragraphs)


def chunk_text(text: str, chunk_size: Optional[int] = None, overlap: Optional[int] = None) -> list[dict]:
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)

    chunks = []
    start = 0
    index = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)

        chunks.append({
            "content": chunk_text,
            "chunk_index": index,
            "token_count": len(chunk_tokens),
        })

        index += 1
        if end >= len(tokens):
            break
        start = end - overlap

    return chunks
