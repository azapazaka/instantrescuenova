"""Retrieval over the curated guideline corpus.

Why RAG and not just a system prompt: a health recommendation that cites WHO can
be checked by the user and their doctor. One that comes from the model's memory
cannot, and LLMs invent plausible-looking citations. Every chunk in rag_corpus/
was copied from the named URL by hand, so a citation the UI renders is a real
document the user can open.

Two retrieval paths:
- Postgres + pgvector: cosine search over multilingual MiniLM embeddings.
- Anything else (SQLite in tests, no model downloaded): lexical overlap.

The lexical path is a genuine fallback, not a pretend one — it returns real
chunks with real URLs, just ranked more crudely. The API reports which path ran
so the UI never implies more rigour than was actually applied.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import GuidelineChunk

CORPUS_DIR = Path(__file__).resolve().parents[2] / "rag_corpus"
EMBEDDING_DIM = 384


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---"):
        raise ValueError("chunk is missing YAML frontmatter")
    _, block, body = raw.split("---", 2)
    meta: dict = {}
    for line in block.strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    if "year" in meta and meta["year"]:
        meta["year"] = int(meta["year"])
    return meta, body.strip()


def load_corpus() -> list[dict]:
    chunks = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        chunks.append({**meta, "content": body})
    return chunks


@lru_cache(maxsize=1)
def _encoder():
    """Load the embedding model once. None if unavailable — caller falls back."""
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(get_settings().embedding_model)
    except Exception:
        return None


def embed(texts: list[str]) -> Optional[list[list[float]]]:
    model = _encoder()
    if model is None:
        return None
    return model.encode(texts, normalize_embeddings=True).tolist()


def _is_postgres(db: Session) -> bool:
    return db.bind.dialect.name == "postgresql"


def index_corpus(db: Session) -> dict:
    """Load rag_corpus/ into the database, embedding when possible.

    Idempotent: re-running updates content in place, so editing a chunk and
    re-indexing is the normal workflow.
    """
    chunks = load_corpus()
    vectors = embed([f"{c['title']}. {c['content']}" for c in chunks]) if _is_postgres(db) else None

    for index, chunk in enumerate(chunks):
        row = db.query(GuidelineChunk).filter(GuidelineChunk.slug == chunk["slug"]).first()
        if row is None:
            row = GuidelineChunk(slug=chunk["slug"])
            db.add(row)
        row.title = chunk["title"]
        row.org = chunk["org"]
        row.url = chunk["url"]
        row.year = chunk.get("year")
        row.section = chunk.get("section")
        row.content = chunk["content"]
    db.commit()

    if vectors:
        for chunk, vector in zip(chunks, vectors):
            db.execute(
                text("update guideline_chunks set embedding = :v where slug = :s"),
                {"v": str(vector), "s": chunk["slug"]},
            )
        db.commit()

    return {
        "chunks": len(chunks),
        "embedded": bool(vectors),
        "mode": "vector" if vectors else "lexical",
    }


_WORD = re.compile(r"\w+", re.UNICODE)


def _lexical_search(db: Session, query: str, k: int) -> list[GuidelineChunk]:
    terms = {w.lower() for w in _WORD.findall(query) if len(w) > 3}
    rows = db.query(GuidelineChunk).all()
    if not terms:
        return rows[:k]

    def overlap(row: GuidelineChunk) -> int:
        haystack = f"{row.title} {row.section or ''} {row.content}".lower()
        return sum(1 for term in terms if term in haystack)

    ranked = sorted(rows, key=overlap, reverse=True)
    return [row for row in ranked if overlap(row) > 0][:k] or ranked[:k]


def retrieve(db: Session, query: str, k: Optional[int] = None) -> tuple[list[dict], str]:
    """Return (chunks, mode) most relevant to `query`."""
    k = k or get_settings().rag_top_k

    if _is_postgres(db):
        vectors = embed([query])
        if vectors:
            rows = db.execute(
                text(
                    """
                    select slug, title, org, url, year, section, content,
                           1 - (embedding <=> cast(:v as vector)) as score
                    from guideline_chunks
                    where embedding is not null
                    order by embedding <=> cast(:v as vector)
                    limit :k
                    """
                ),
                {"v": str(vectors[0]), "k": k},
            ).mappings().all()
            if rows:
                return [dict(row) for row in rows], "vector"

    chunks = _lexical_search(db, query, k)
    return (
        [
            {
                "slug": c.slug, "title": c.title, "org": c.org, "url": c.url,
                "year": c.year, "section": c.section, "content": c.content, "score": None,
            }
            for c in chunks
        ],
        "lexical",
    )


def as_sources(chunks: list[dict]) -> list[dict]:
    """Chunks -> citation payload for the API response."""
    return [
        {
            "title": c["title"],
            "org": c["org"],
            "url": c["url"],
            "year": c.get("year"),
            "section": c.get("section"),
        }
        for c in chunks
    ]
