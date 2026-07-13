"""
Chunking strategies for RAG.

Supports:
  - Fixed-size with overlap
  - Sentence-aware splitting
  - Recursive character splitting (LangChain-style)
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    index: int
    start_char: int
    end_char: int
    metadata: dict


# ---------------------------------------------------------------------------
# Fixed-size chunker
# ---------------------------------------------------------------------------
def chunk_fixed(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
    metadata: dict | None = None,
) -> list[Chunk]:
    """Split text into fixed-size character chunks with overlap."""
    metadata = metadata or {}
    chunks: list[Chunk] = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(
            Chunk(
                text=text[start:end],
                index=idx,
                start_char=start,
                end_char=end,
                metadata=metadata,
            )
        )
        idx += 1
        start += chunk_size - overlap
    return chunks


# ---------------------------------------------------------------------------
# Sentence-aware chunker
# ---------------------------------------------------------------------------
_SENTENCE_ENDINGS = re.compile(r"(?<=[.!?])\s+")


def chunk_sentences(
    text: str,
    max_tokens_approx: int = 300,
    overlap_sentences: int = 1,
    metadata: dict | None = None,
) -> list[Chunk]:
    """Group sentences into chunks, estimating tokens at ~4 chars each."""
    metadata = metadata or {}
    sentences = _SENTENCE_ENDINGS.split(text)
    chunks: list[Chunk] = []
    current: list[str] = []
    idx = 0
    pos = 0

    for sentence in sentences:
        projected = sum(len(s) for s in current) + len(sentence)
        if projected > max_tokens_approx * 4 and current:
            chunk_text = " ".join(current)
            chunks.append(
                Chunk(
                    text=chunk_text,
                    index=idx,
                    start_char=pos,
                    end_char=pos + len(chunk_text),
                    metadata=metadata,
                )
            )
            idx += 1
            pos += len(chunk_text)
            current = current[-overlap_sentences:] if overlap_sentences else []
        current.append(sentence)

    if current:
        chunk_text = " ".join(current)
        chunks.append(
            Chunk(
                text=chunk_text,
                index=idx,
                start_char=pos,
                end_char=pos + len(chunk_text),
                metadata=metadata,
            )
        )
    return chunks


# ---------------------------------------------------------------------------
# Recursive character chunker (mirrors LangChain RecursiveCharacterTextSplitter)
# ---------------------------------------------------------------------------
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _recursive_split(text: str, separators: list[str], chunk_size: int, overlap: int) -> list[str]:
    if not text:
        return []
    sep = separators[0]
    if not sep:
        # character-level split
        return [text[i: i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

    parts = text.split(sep)
    results: list[str] = []
    current = ""
    for part in parts:
        candidate = (current + sep + part).strip() if current else part
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                results.append(current)
            if len(part) > chunk_size:
                results.extend(_recursive_split(part, separators[1:], chunk_size, overlap))
                current = ""
            else:
                current = part
    if current:
        results.append(current)
    return results


def chunk_recursive(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
    metadata: dict | None = None,
) -> list[Chunk]:
    metadata = metadata or {}
    raw_chunks = _recursive_split(text, _SEPARATORS, chunk_size, overlap)
    chunks: list[Chunk] = []
    pos = 0
    for idx, chunk_text in enumerate(raw_chunks):
        chunks.append(
            Chunk(
                text=chunk_text,
                index=idx,
                start_char=pos,
                end_char=pos + len(chunk_text),
                metadata=metadata,
            )
        )
        pos += len(chunk_text)
    return chunks
