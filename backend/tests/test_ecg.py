from io import BytesIO

from pypdf import PdfWriter


def _pdf_bytes():
    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def test_ecg_rejects_non_pdf(client):
    response = client.post(
        "/api/ecg-analyses",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE"


def test_ecg_rejects_corrupted_pdf(client):
    response = client.post(
        "/api/ecg-analyses",
        files={"file": ("ecg.pdf", b"not a real pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CORRUPTED_PDF"


def test_ecg_successful_mock_analysis_and_history(client):
    response = client.post(
        "/api/ecg-analyses",
        files={"file": ("ECG_Report_July.pdf", _pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "ECG_Report_July.pdf"
    assert data["status"] == "completed"
    assert data["structured_result"]["analysis_status"] == "completed"

    history = client.get("/api/ecg-analyses")
    assert history.status_code == 200
    assert history.json()[0]["original_filename"] == "ECG_Report_July.pdf"
