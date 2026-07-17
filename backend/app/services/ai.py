"""AI provider boundary.

`get_provider()` returns the real Groq-backed provider when a key is configured
and the deterministic mock otherwise. Both satisfy the same interface, so the
API layer never branches on which one is live — it just records `ai_mode` on the
row so the UI can badge mock output honestly instead of passing it off as AI.
"""

from __future__ import annotations

from typing import Optional

from app.core.config import get_settings
from app.models import DailyCheckIn, UserProfile
from app.schemas.health_documents import HealthDocumentResult
from app.schemas.recommendations import HealthRecommendationResult


class MockAIProvider:
    """Deterministic rule-based output. No network, no key, no surprises.

    This exists so a fresh clone runs, and so a Groq outage during a demo
    degrades to something sane. It is explicitly labelled in the UI: rules are
    not AI, and pretending otherwise would misrepresent the system.
    """

    mode = "mock"

    def generate_health_recommendation(
        self,
        profile: UserProfile,
        checkin: Optional[DailyCheckIn],
        hr_insight: Optional[dict] = None,
        chunks: Optional[list[dict]] = None,
    ) -> HealthRecommendationResult:
        sleep = checkin.sleep_hours if checkin else 6
        energy = checkin.energy_level if checkin else 5
        stress = checkin.stress_level if checkin else 5
        soreness = checkin.muscle_soreness if checkin else 4
        has_pain = bool(checkin and checkin.pain_or_discomfort)

        severity = (hr_insight or {}).get("severity", "normal")
        hr_concerning = severity in {"elevated", "high"}

        if sleep < 6 or energy <= 4 or stress >= 8 or has_pain or hr_concerning:
            readiness, intensity, focus = "low", "low", "восстановление"
        elif energy >= 8 and stress <= 4 and soreness <= 4:
            readiness, intensity, focus = "high", "moderate", "активный день"
        else:
            readiness, intensity, focus = "moderate", "moderate", "умеренная нагрузка"

        avoid = ["Интенсивные интервалы", "Тренировку через боль"]
        safety = None
        if has_pain:
            safety = "Есть дискомфорт. Выберите щадящую нагрузку."
            avoid.append("Движения, усиливающие боль")
        if hr_concerning:
            safety = (
                "Показатели пульса за последнее окно отклоняются от вашей нормы. "
                "Это не диагноз — но сегодня стоит снизить нагрузку и обсудить показатели с врачом."
            )

        sources = _sources_from(chunks)

        return HealthRecommendationResult(
            summary=f"Фокус на сегодня: {focus}. Сон {sleep:g} ч, энергия {energy}/10, стресс {stress}/10.",
            readiness={"level": readiness, "explanation": "По сну, энергии, стрессу, усталости и пульсу."},
            today_focus=focus.capitalize(),
            movement={
                "title": "Движение",
                "recommendation": "25-40 минут ходьбы или легкой тренировки.",
                "intensity": intensity,
                "duration": "25-40 минут",
                "reasoning": "Достаточно для тонуса без перегруза.",
                "sources": sources,
            },
            recovery={
                "recommendation": "10 минут растяжки и спокойный вечер.",
                "reasoning": "Поможет восстановиться.",
                "sources": [],
            },
            nutrition={
                "recommendation": "Вода в течение дня, белок в основные приемы пищи, меньше соли.",
                "reasoning": "Поддержит энергию и давление.",
                "sources": sources,
            },
            sleep={
                "recommendation": "Поставьте цель лечь на 30 минут раньше обычного.",
                "reasoning": "Это простой шаг для восстановления.",
                "sources": [],
            },
            things_to_avoid=avoid,
            important_notes=[
                "Это не медицинский диагноз.",
                "При сильных симптомах обратитесь к врачу.",
                "Ответ сформирован набором правил (демо-режим), а не языковой моделью.",
            ],
            medical_safety_message=safety,
            heart_rate_insight=_insight_payload(hr_insight),
        )

    def analyze_health_document(
        self,
        filename: str,
        document_text: str,
        page_count: int,
        chunks: Optional[list[dict]] = None,
    ) -> HealthDocumentResult:
        limited = document_text[:1200].strip()
        summary = "Документ принят. Ниже краткий разбор."
        if limited:
            summary += " В файле найден текстовый слой."
        sources = _sources_from(chunks)

        return HealthDocumentResult(
            document_type="Медицинский документ",
            analysis_status="limited",
            document_summary=summary,
            detected_measurements=[],
            observations=[
                {
                    "title": "Требуется врачебная интерпретация",
                    "description": "Разбор помогает подготовить вопросы, но не заменяет заключение специалиста.",
                    "importance": "moderate",
                    "source_page": 1,
                }
            ],
            nutrition_advice=[
                {
                    "recommendation": "Ограничьте соль до 5 г в день, добавьте овощи и цельные злаки.",
                    "reasoning": "Базовая рекомендация ВОЗ и AHA для здоровья сердца.",
                    "sources": sources,
                }
            ],
            activity_advice=[
                {
                    "recommendation": "150 минут умеренной активности в неделю, силовые 2 раза в неделю.",
                    "reasoning": "Норма ВОЗ для людей 65 лет и старше.",
                    "sources": sources,
                }
            ],
            document_quality={
                "level": "fair" if limited else "poor",
                "explanation": f"Страниц: {page_count}. Показатели не извлекались: демо-режим без языковой модели.",
            },
            recommended_next_steps=["Сравните результат с официальным заключением врача."],
            questions_for_doctor=[
                "Какие показатели требуют внимания именно в моем случае?",
                "Есть ли ограничения по физической активности?",
            ],
            urgent_flags=[],
            limitations=[
                "Это не диагноз.",
                "Показатели из документа не извлекались: демо-режим без языковой модели.",
            ],
        )


def _sources_from(chunks: Optional[list[dict]]) -> list[dict]:
    from app.services.rag import as_sources

    return as_sources(chunks or [])


def _insight_payload(hr_insight: Optional[dict]) -> Optional[dict]:
    if not hr_insight:
        return None
    from app.services.anomaly import top_factors

    return {
        "summary": hr_insight.get("summary", ""),
        "severity": hr_insight.get("severity", "normal"),
        "average_bpm": hr_insight.get("average_bpm"),
        "resting_bpm": hr_insight.get("resting_bpm"),
        "contributions": top_factors(hr_insight.get("contributions", [])),
    }


def get_provider():
    settings = get_settings()
    if settings.groq_api_key:
        from app.services.llm import GroqAIProvider

        return GroqAIProvider()
    return MockAIProvider()
