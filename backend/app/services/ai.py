from app.models import DailyCheckIn, UserProfile
from app.schemas.ecg import ECGAnalysisResult
from app.schemas.recommendations import HealthRecommendationResult


class MockAIProvider:
    def generate_health_recommendation(
        self, profile: UserProfile, checkin: DailyCheckIn | None
    ) -> HealthRecommendationResult:
        sleep = checkin.sleep_hours if checkin else 6
        energy = checkin.energy_level if checkin else 5
        stress = checkin.stress_level if checkin else 5
        soreness = checkin.muscle_soreness if checkin else 4
        has_pain = bool(checkin and checkin.pain_or_discomfort)

        if sleep < 6 or energy <= 4 or stress >= 8 or has_pain:
            readiness = "low"
            intensity = "low"
            focus = "восстановление и мягкое движение"
        elif energy >= 8 and stress <= 4 and soreness <= 4:
            readiness = "high"
            intensity = "moderate"
            focus = "уверенная активность без перегруза"
        else:
            readiness = "moderate"
            intensity = "moderate"
            focus = "сбалансированная нагрузка и контроль усталости"

        safety = None
        avoid = ["Интенсивные интервалы без разминки", "Тренировку через боль"]
        if has_pain:
            safety = (
                "Вы отметили дискомфорт. Сегодня лучше выбрать щадящую активность "
                "и обсудить устойчивую или усиливающуюся боль со специалистом."
            )
            avoid.append("Упражнения, усиливающие дискомфорт")

        return HealthRecommendationResult(
            summary=(
                f"Сегодня оптимален режим: {focus}. План учитывает сон {sleep:g} ч, "
                f"энергию {energy}/10 и стресс {stress}/10."
            ),
            readiness={
                "level": readiness,
                "explanation": "Оценка основана на сне, энергии, стрессе и мышечной усталости.",
            },
            today_focus=focus.capitalize(),
            movement={
                "title": "Движение на сегодня",
                "recommendation": "30-40 минут ходьбы, mobility или легкая силовая работа.",
                "intensity": intensity,
                "duration": "25-40 минут",
                "reasoning": "Такой объем поддержит активность без лишней нагрузки на восстановление.",
            },
            recovery={
                "recommendation": "Добавьте 10 минут дыхания, растяжку и спокойный вечерний режим.",
                "reasoning": "Это снижает нагрузку на нервную систему и помогает качеству сна.",
            },
            nutrition={
                "recommendation": "Держите воду рядом и добавьте белок к основным приемам пищи.",
                "reasoning": "Гидратация и белок поддерживают энергию и восстановление.",
            },
            sleep={
                "recommendation": "Поставьте цель лечь на 30 минут раньше обычного.",
                "reasoning": "Небольшой сдвиг режима проще удержать и он заметно влияет на восстановление.",
            },
            things_to_avoid=avoid,
            important_notes=[
                "Это не медицинский диагноз.",
                "При выраженных симптомах обратитесь к врачу или в экстренную службу.",
            ],
            medical_safety_message=safety,
        )

    def analyze_ecg_document(self, filename: str, text: str, page_count: int) -> ECGAnalysisResult:
        limited_text = text[:1200].strip()
        summary = (
            "Документ распознан как PDF с результатами ЭКГ. В mock-режиме система "
            "показывает безопасный пример структурированного объяснения."
        )
        if limited_text:
            summary += " В документе найден текстовый слой, поэтому часть информации можно читать напрямую."

        return ECGAnalysisResult(
            document_type="ECG report",
            analysis_status="completed",
            document_summary=summary,
            detected_measurements=[
                {"name": "Heart rate", "value": "Не удалось надежно определить из документа", "source_page": 1},
                {"name": "QRS", "value": "Не удалось надежно определить из документа", "source_page": 1},
                {"name": "QTc", "value": "Не удалось надежно определить из документа", "source_page": 1},
            ],
            observations=[
                {
                    "title": "Требуется врачебная интерпретация",
                    "description": "AI-assisted обзор помогает подготовить вопросы, но не заменяет заключение специалиста.",
                    "importance": "moderate",
                    "source_page": 1,
                }
            ],
            possible_patterns=[
                {
                    "name": "Недостаточно данных для уверенного паттерна",
                    "explanation": "Mock-режим не делает диагностических выводов и не придумывает показатели.",
                    "confidence": "low",
                }
            ],
            signal_or_document_quality={
                "level": "fair" if page_count else "poor",
                "explanation": f"PDF содержит {page_count} стр.; исходный файл не сохраняется после анализа.",
            },
            recommended_next_steps=[
                "Сравните результат с официальным заключением ЭКГ.",
                "Обсудите непонятные показатели с врачом.",
            ],
            questions_for_doctor=[
                "Какие показатели ЭКГ требуют внимания именно в моем случае?",
                "Есть ли ограничения по физической активности?",
            ],
            urgent_flags=[],
            limitations=[
                "Это AI-assisted объяснение, а не диагноз.",
                "Mock-режим не анализирует изображение как реальная multimodal модель.",
                "Показатели не извлекаются, если они не видны надежно.",
            ],
        )
