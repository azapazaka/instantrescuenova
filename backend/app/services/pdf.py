from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.config import Settings
from app.core.errors import ApiError


def validate_pdf_upload(filename: str, content_type: str | None, data: bytes, settings: Settings) -> tuple[str, int]:
    if not filename.lower().endswith(".pdf") or content_type not in {
        "application/pdf",
        "application/x-pdf",
        "application/octet-stream",
    }:
        raise ApiError(400, "UNSUPPORTED_FILE", "Поддерживаются только PDF-файлы.")

    max_bytes = settings.max_pdf_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise ApiError(400, "PDF_TOO_LARGE", "Файл превышает допустимый размер.")

    try:
        reader = PdfReader(BytesIO(data))
        page_count = len(reader.pages)
        if page_count > settings.max_ecg_pdf_pages:
            raise ApiError(400, "TOO_MANY_PAGES", "PDF содержит слишком много страниц для MVP-анализа.")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except ApiError:
        raise
    except (PdfReadError, Exception) as exc:
        raise ApiError(400, "CORRUPTED_PDF", "Не удалось прочитать PDF-файл.") from exc

    return text, page_count
