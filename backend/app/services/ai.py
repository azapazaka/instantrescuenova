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
            focus = "восстановление"
        elif energy >= 8 and stress <= 4 and soreness <= 4:
            readiness = "high"
            intensity = "moderate"
            focus = "активный день"
        else:
            readiness = "moderate"
            intensity = "moderate"
            focus = "умеренная нагрузка"

        safety = None
        avoid = ["Интенсивные интервалы", "Тренировку через боль"]
        if has_pain:
            safety = (
                "Есть дискомфорт. Выберите щадящую нагрузку."
            )
            avoid.append("Движения, усиливающие боль")

        return HealthRecommendationResult(
            summary=(
                f"Фокус на сегодня: {focus}. Сон {sleep:g} ч, энергия {energy}/10, стресс {stress}/10."
            ),
            readiness={
                "level": readiness,
                "explanation": "По сну, энергии, стрессу и усталости.",
            },
            today_focus=focus.capitalize(),
            movement={
                "title": "Движение",
                "recommendation": "25-40 минут ходьбы или легкой тренировки.",
                "intensity": intensity,
                "duration": "25-40 минут",
                "reasoning": "Достаточно для тонуса без перегруза.",
            },
            recovery={
                "recommendation": "10 минут растяжки и спокойный вечер.",
                "reasoning": "Поможет восстановиться.",
            },
            nutrition={
                "recommendation": "Вода в течение дня, белок в основные приемы пищи.",
                "reasoning": "Поддержит энергию.",
            },
            sleep={
                "recommendation": "Поставьте цель лечь на 30 минут раньше обычного.",
                "reasoning": "Это простой шаг для восстановления.",
            },
            things_to_avoid=avoid,
            important_notes=[
                "Это не медицинский диагноз.",
                "При сильных симптомах обратитесь к врачу.",
            ],
            medical_safety_message=safety,
        )

    def analyze_ecg_document(self, filename: str, text: str, page_count: int) -> ECGAnalysisResult:
        limited_text = text[:1200].strip()
        summary = (
            "PDF с результатами ЭКГ принят. Ниже краткий разбор документа."
        )
        if limited_text:
            summary += " В файле найден текстовый слой."

        return ECGAnalysisResult(
            document_type="ECG report",
            analysis_status="completed",
            document_summary=summary,
            detected_measurements=[
                {"name": "Пульс", "value": "Не удалось надежно определить из документа", "source_page": 1},
                {"name": "QRS", "value": "Не удалось надежно определить из документа", "source_page": 1},
                {"name": "QTc", "value": "Не удалось надежно определить из документа", "source_page": 1},
            ],
            observations=[
                {
                    "title": "Требуется врачебная интерпретация",
                    "description": "Разбор помогает подготовить вопросы, но не заменяет заключение специалиста.",
                    "importance": "moderate",
                    "source_page": 1,
                }
            ],
            possible_patterns=[
                {
                    "name": "Недостаточно данных для уверенного паттерна",
                    "explanation": "Диагностический вывод не формируется.",
                    "confidence": "low",
                }
            ],
            signal_or_document_quality={
                "level": "fair" if page_count else "poor",
                "explanation": f"Страниц: {page_count}.",
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
                "Это не диагноз.",
                "Качество разбора зависит от качества PDF.",
                "Показатели не извлекаются, если они не видны надежно.",
            ],
        )
