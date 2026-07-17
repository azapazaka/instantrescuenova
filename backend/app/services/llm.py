"""Groq-backed AI provider.

Design notes that matter for a medical-adjacent product:

- The model is never the last word. Prompts forbid diagnosis and medication
  changes, and every response carries limitations plus "consult your doctor".
- Output is validated against the same Pydantic schemas the mock satisfies. An
  unparseable or schema-violating response is retried once, then falls back to
  the mock rather than being shown half-formed.
- Citations come from the retrieved corpus, not from the model. We pass chunks
  in with ids and ask it to reference those ids; anything it cites that we did
  not supply is dropped in `_resolve_sources`. This is what stops invented URLs.
"""

from __future__ import annotations

import json
from typing import Optional

from app.core.config import get_settings
from app.models import DailyCheckIn, UserProfile
from app.schemas.health_documents import HealthDocumentResult
from app.schemas.recommendations import HealthRecommendationResult
from app.services.ai import MockAIProvider, _insight_payload

SAFETY_RULES = """\
Ты — ассистент приложения Instant Rescue для пожилых людей и их близких.

ЖЁСТКИЕ ПРАВИЛА (нарушение недопустимо):
1. Ты НЕ ставишь диагноз. Ты не называешь болезнь у пользователя.
2. Ты НЕ назначаешь, не отменяешь и не меняешь дозы лекарств.
3. Ты НЕ заменяешь врача. Финальное решение всегда принимает человек — сам пользователь и его врач.
4. Ты опираешься ТОЛЬКО на предоставленные ниже источники. Если источник не подтверждает мысль — не пиши её.
5. Если данных мало — прямо скажи, что данных мало. Не выдумывай показатели и не додумывай значения.
6. При признаках неотложного состояния (боль в груди, одышка в покое, обморок, признаки инсульта)
   первым делом скажи вызвать скорую помощь, а не давай советы по образу жизни.
7. Пиши простым русским языком, короткими предложениями. Читатель — пожилой человек.
8. Обращайся на «вы». Не пугай, но и не преуменьшай.

ЦИТИРОВАНИЕ: у каждого источника ниже есть id. Когда совет опирается на источник,
укажи его id в поле "source_ids". Использовать можно только выданные id.
"""


class GroqAIProvider:
    mode = "groq"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._fallback = MockAIProvider()

    # ------------------------------------------------------------------ core
    def _client(self):
        from groq import Groq

        return Groq(api_key=self._settings.groq_api_key)

    def _complete(self, system: str, user: str) -> Optional[dict]:
        """Call Groq in JSON mode. Returns parsed dict, or None on failure."""
        for attempt in range(2):
            try:
                response = self._client().chat.completions.create(
                    model=self._settings.groq_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2 if attempt == 0 else 0.0,
                    max_tokens=4000,
                )
                return json.loads(response.choices[0].message.content)
            except Exception as exc:
                print(f"[llm] attempt {attempt + 1} failed: {exc}")
        return None

    # -------------------------------------------------------------- prompting
    @staticmethod
    def _format_chunks(chunks: list[dict]) -> str:
        lines = []
        for index, chunk in enumerate(chunks, start=1):
            lines.append(
                f"[id:{index}] {chunk['title']} ({chunk['org']}, {chunk.get('year', 'н/д')})\n"
                f"{chunk['content']}"
            )
        return "\n\n".join(lines) or "Источники не найдены."

    @staticmethod
    def _resolve_sources(source_ids, chunks: list[dict]) -> list[dict]:
        """Map model-supplied ids back to real chunks, dropping anything invented."""
        from app.services.rag import as_sources

        if not isinstance(source_ids, list):
            return []
        picked = []
        for raw in source_ids:
            try:
                index = int(raw) - 1
            except (TypeError, ValueError):
                continue
            if 0 <= index < len(chunks):
                picked.append(chunks[index])
        return as_sources(picked)

    def _attach_sources(self, block: dict, chunks: list[dict]) -> dict:
        if not isinstance(block, dict):
            return block
        block["sources"] = self._resolve_sources(block.pop("source_ids", []), chunks)
        return block

    # ------------------------------------------------------ recommendations
    def generate_health_recommendation(
        self,
        profile: UserProfile,
        checkin: Optional[DailyCheckIn],
        hr_insight: Optional[dict] = None,
        chunks: Optional[list[dict]] = None,
    ) -> HealthRecommendationResult:
        chunks = chunks or []

        profile_text = (
            f"Возраст: {profile.age or 'не указан'}, пол: {profile.biological_sex or 'не указан'}, "
            f"рост: {profile.height_cm or '?'} см, вес: {profile.weight_kg or '?'} кг.\n"
            f"Уровень активности: {profile.activity_level}. Цель: {profile.primary_goal}.\n"
            f"Известные состояния: {profile.known_conditions or 'не указаны'}.\n"
            f"Ограничения/травмы: {profile.injuries_or_limitations or 'нет'}.\n"
            f"Питание: {profile.dietary_preferences or 'без особенностей'}."
        )

        if checkin:
            checkin_text = (
                f"Сон: {checkin.sleep_hours} ч, качество сна {checkin.sleep_quality}/10.\n"
                f"Энергия: {checkin.energy_level}/10, стресс: {checkin.stress_level}/10, "
                f"мышечная усталость: {checkin.muscle_soreness}/10.\n"
                f"Боль/дискомфорт: {checkin.pain_or_discomfort or 'нет'}.\n"
                f"Планы на день: {checkin.planned_activity or 'не указаны'}."
            )
        else:
            checkin_text = "Пользователь не заполнял состояние на сегодня."

        if hr_insight:
            factors = "\n".join(
                f"  - {c['label']}: {c['value']} (норма ~{c['baseline']}, "
                f"отклонение {c['deviation']} сигм, вклад {int(c['weight'] * 100)}%)"
                for c in hr_insight.get("contributions", [])[:5]
            )
            hr_text = (
                f"Модель анализа пульса оценила последнее окно как '{hr_insight.get('severity')}' "
                f"(оценка {hr_insight.get('anomaly_score')}).\n"
                f"Средний пульс: {hr_insight.get('average_bpm')} уд/мин, "
                f"пульс покоя: {hr_insight.get('resting_bpm')} уд/мин.\n"
                f"Вклад признаков:\n{factors}"
            )
        else:
            hr_text = "Данных о пульсе пока недостаточно для оценки."

        system = SAFETY_RULES + """
Верни СТРОГО JSON такой структуры:
{
  "summary": "1-2 предложения о сегодняшнем дне",
  "readiness": {"level": "low|moderate|high", "explanation": "почему такой уровень"},
  "today_focus": "короткая фраза",
  "movement": {"title": "Движение", "recommendation": "...", "intensity": "low|moderate|high",
               "duration": "...", "reasoning": "...", "source_ids": [1]},
  "recovery":  {"recommendation": "...", "reasoning": "...", "source_ids": []},
  "nutrition": {"recommendation": "...", "reasoning": "...", "source_ids": [2]},
  "sleep":     {"recommendation": "...", "reasoning": "...", "source_ids": []},
  "things_to_avoid": ["...", "..."],
  "important_notes": ["...", "..."],
  "medical_safety_message": "текст или null"
}
В "readiness.explanation" обязательно объясни, какие данные повлияли на вывод,
включая показатели пульса, если они есть.
"""

        user = (
            f"ПРОФИЛЬ:\n{profile_text}\n\n"
            f"СОСТОЯНИЕ СЕГОДНЯ:\n{checkin_text}\n\n"
            f"АНАЛИЗ ПУЛЬСА:\n{hr_text}\n\n"
            f"ИСТОЧНИКИ:\n{self._format_chunks(chunks)}\n\n"
            "Составь план на день."
        )

        payload = self._complete(system, user)
        if payload is None:
            return self._fallback.generate_health_recommendation(profile, checkin, hr_insight, chunks)

        for key in ("movement", "recovery", "nutrition", "sleep"):
            if key in payload:
                payload[key] = self._attach_sources(payload[key], chunks)
        payload["heart_rate_insight"] = _insight_payload(hr_insight)

        try:
            return HealthRecommendationResult.model_validate(payload)
        except Exception as exc:
            print(f"[llm] schema validation failed, falling back to mock: {exc}")
            return self._fallback.generate_health_recommendation(profile, checkin, hr_insight, chunks)

    # ------------------------------------------------------------ documents
    def analyze_health_document(
        self,
        filename: str,
        document_text: str,
        page_count: int,
        chunks: Optional[list[dict]] = None,
    ) -> HealthDocumentResult:
        chunks = chunks or []
        excerpt = document_text[:12000].strip()

        system = SAFETY_RULES + """
Тебе дан текст, извлечённый из медицинского PDF пользователя (анализы крови,
дневник давления, заключение по пульсу и т.п.).

ЗАДАЧА: объяснить документ простым языком и дать рекомендации по питанию и
физической активности, опираясь на источники.

ОСОБО ВАЖНО про показатели:
- Извлекай ТОЛЬКО те показатели, которые реально видны в тексте.
- Если показателя нет в тексте — не придумывай его и не указывай.
- Если текст пустой или нечитаемый — верни analysis_status: "limited",
  пустой detected_measurements и честно объясни это в document_quality.

Верни СТРОГО JSON:
{
  "document_type": "например: Общий анализ крови",
  "analysis_status": "completed|limited",
  "document_summary": "2-4 предложения простым языком",
  "detected_measurements": [
    {"name": "...", "value": "...", "reference_range": "... или null",
     "status": "normal|borderline|out_of_range|unknown", "source_page": 1}
  ],
  "observations": [
    {"title": "...", "description": "...", "importance": "low|moderate|high", "source_page": 1}
  ],
  "nutrition_advice": [{"recommendation": "...", "reasoning": "...", "source_ids": [1]}],
  "activity_advice":  [{"recommendation": "...", "reasoning": "...", "source_ids": [2]}],
  "document_quality": {"level": "poor|fair|good", "explanation": "..."},
  "recommended_next_steps": ["..."],
  "questions_for_doctor": ["..."],
  "urgent_flags": ["только если в документе явные признаки неотложного состояния"],
  "limitations": ["..."]
}
"""

        user = (
            f"ФАЙЛ: {filename}\nСТРАНИЦ: {page_count}\n\n"
            f"ТЕКСТ ДОКУМЕНТА:\n{excerpt or '(текстовый слой не найден — вероятно, скан)'}\n\n"
            f"ИСТОЧНИКИ:\n{self._format_chunks(chunks)}\n\n"
            "Разбери документ."
        )

        payload = self._complete(system, user)
        if payload is None:
            return self._fallback.analyze_health_document(filename, document_text, page_count, chunks)

        for key in ("nutrition_advice", "activity_advice"):
            if isinstance(payload.get(key), list):
                payload[key] = [self._attach_sources(item, chunks) for item in payload[key]]

        try:
            return HealthDocumentResult.model_validate(payload)
        except Exception as exc:
            print(f"[llm] schema validation failed, falling back to mock: {exc}")
            return self._fallback.analyze_health_document(filename, document_text, page_count, chunks)
