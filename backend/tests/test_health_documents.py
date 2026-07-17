"""PDF upload validation and analysis storage."""

import io

from pypdf import PdfWriter


def _pdf_bytes(pages: int = 1) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _upload(client, data: bytes, name: str = "analysis.pdf", mime: str = "application/pdf"):
    return client.post("/api/health-documents", files={"file": (name, data, mime)})


def test_upload_creates_analysis(client):
    response = _upload(client, _pdf_bytes())
    assert response.status_code == 200
    body = response.json()
    assert body["original_filename"] == "analysis.pdf"
    # No Groq key in tests, so the row must honestly record mock mode.
    assert body["ai_mode"] == "mock"
    assert body["structured_result"]["limitations"]


def test_non_pdf_is_rejected(client):
    response = _upload(client, b"not a pdf at all", name="notes.txt", mime="text/plain")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE"


def test_corrupted_pdf_is_rejected(client):
    response = _upload(client, b"%PDF-1.4 broken garbage")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CORRUPTED_PDF"


def test_too_many_pages_is_rejected(client):
    response = _upload(client, _pdf_bytes(pages=25))
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "TOO_MANY_PAGES"


def test_analysis_history_is_listed(client):
    _upload(client, _pdf_bytes())
    history = client.get("/api/health-documents").json()
    assert len(history) == 1


def test_missing_analysis_returns_404(client):
    assert client.get("/api/health-documents/9999").status_code == 404
