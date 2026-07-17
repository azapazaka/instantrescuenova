from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import HealthDocumentAnalysis
from app.schemas.health_documents import HealthDocumentRead
from app.services.ai import get_provider
from app.services.pdf import validate_pdf_upload
from app.services.rag import retrieve

router = APIRouter(prefix="/api/health-documents", tags=["health-documents"])


@router.post("", response_model=HealthDocumentRead)
async def create_analysis(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    data = await file.read()
    filename = file.filename or "document.pdf"

    text, page_count = validate_pdf_upload(filename, file.content_type, data, settings)

    chunks, _mode = retrieve(
        db,
        "питание физическая активность сердце анализы показатели крови давление " + text[:500],
    )

    provider = get_provider()
    result = provider.analyze_health_document(filename, text, page_count, chunks)

    analysis = HealthDocumentAnalysis(
        user_id=user_id,
        original_filename=filename,
        status=result.analysis_status,
        document_summary=result.document_summary,
        structured_result=result.model_dump(mode="json"),
        sources=[s.model_dump(mode="json") for s in _collect_sources(result)],
        ai_mode=provider.mode,
    )
    # The uploaded PDF is deliberately never persisted — only the structured
    # analysis is. `data` goes out of scope here and is not written anywhere.
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def _collect_sources(result) -> list:
    seen: dict[str, object] = {}
    for advice in [*result.nutrition_advice, *result.activity_advice]:
        for source in advice.sources:
            seen.setdefault(source.url, source)
    return list(seen.values())


@router.get("", response_model=list[HealthDocumentRead])
def list_analyses(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(HealthDocumentAnalysis)
        .filter(HealthDocumentAnalysis.user_id == user_id)
        .order_by(HealthDocumentAnalysis.created_at.desc())
        .all()
    )


@router.get("/{analysis_id}", response_model=HealthDocumentRead)
def get_analysis(
    analysis_id: int,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = (
        db.query(HealthDocumentAnalysis)
        .filter(HealthDocumentAnalysis.id == analysis_id, HealthDocumentAnalysis.user_id == user_id)
        .first()
    )
    if not analysis:
        raise ApiError(404, "DOCUMENT_NOT_FOUND", "Анализ не найден.")
    return analysis
