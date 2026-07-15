from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import ECGAnalysis
from app.schemas.ecg import ECGAnalysisRead
from app.services.ai import MockAIProvider
from app.services.pdf import validate_pdf_upload

router = APIRouter(prefix="/api/ecg-analyses", tags=["ecg"])


@router.post("", response_model=ECGAnalysisRead)
async def create_ecg_analysis(file: UploadFile = File(...), db: Session = Depends(get_db)):
    settings = get_settings()
    data = await file.read()
    text, page_count = validate_pdf_upload(file.filename or "document.pdf", file.content_type, data, settings)
    result = MockAIProvider().analyze_ecg_document(file.filename or "document.pdf", text, page_count)
    analysis = ECGAnalysis(
        user_id=1,
        original_filename=file.filename or "document.pdf",
        status="completed",
        document_summary=result.document_summary,
        structured_result=result.model_dump(),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@router.get("", response_model=list[ECGAnalysisRead])
def list_ecg_analyses(db: Session = Depends(get_db)):
    return db.query(ECGAnalysis).filter(ECGAnalysis.user_id == 1).order_by(ECGAnalysis.created_at.desc()).all()


@router.get("/{analysis_id}", response_model=ECGAnalysisRead)
def get_ecg_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(ECGAnalysis).filter(ECGAnalysis.id == analysis_id, ECGAnalysis.user_id == 1).first()
    if not analysis:
        raise ApiError(404, "ECG_ANALYSIS_NOT_FOUND", "Анализ ЭКГ не найден.")
    return analysis
