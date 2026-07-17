"""The corpus is the product's evidence base; malformed chunks are a real defect."""

import re

from app.services.rag import CORPUS_DIR, as_sources, load_corpus

REQUIRED = {"slug", "title", "org", "url", "content"}


def test_corpus_is_not_empty():
    assert len(load_corpus()) >= 10


def test_every_chunk_has_required_metadata():
    for chunk in load_corpus():
        missing = REQUIRED - set(chunk)
        assert not missing, f"{chunk.get('slug')} is missing {missing}"


def test_every_chunk_cites_a_real_https_url():
    """A citation the user cannot open is worse than no citation."""
    for chunk in load_corpus():
        assert chunk["url"].startswith("https://"), chunk["slug"]


def test_sources_come_from_trusted_organisations():
    allowed = ("who.int", "escardio.org", "heart.org")
    for chunk in load_corpus():
        assert any(domain in chunk["url"] for domain in allowed), chunk["url"]


def test_slugs_are_unique_and_match_filenames():
    seen = set()
    for path in sorted(CORPUS_DIR.glob("*.md")):
        chunk = next(c for c in load_corpus() if c["slug"] == path.stem)
        assert chunk["slug"] not in seen
        seen.add(chunk["slug"])


def test_content_is_substantive():
    for chunk in load_corpus():
        assert len(chunk["content"]) > 100, f"{chunk['slug']} is too thin to ground advice"


def test_as_sources_strips_content():
    """Citations sent to the client must not carry the full chunk body."""
    sources = as_sources(load_corpus()[:2])
    assert sources and all("content" not in s for s in sources)
    assert all(s["url"] and s["title"] and s["org"] for s in sources)


def test_retrieval_finds_activity_guidance(client):
    """Lexical fallback path (tests run on SQLite, so no pgvector)."""
    from app.core.database import SessionLocal
    from app.services.rag import retrieve

    db = SessionLocal()
    try:
        chunks, mode = retrieve(db, "физическая активность пожилые люди 65 лет", k=3)
        assert mode == "lexical"
        assert chunks
        assert any("активност" in c["title"].lower() for c in chunks)
    finally:
        db.close()
