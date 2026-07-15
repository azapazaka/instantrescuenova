# Caspian Care

Caspian Care is a frontend-first health-tech MVP for personalized daily guidance, ECG PDF explanation, and fall-detection safety alerts.

## Overview

The product is built as a monorepo:

- `backend/` - FastAPI, SQLAlchemy 2.x, SQLite, mock AI provider, PDF validation, safety incident flow.
- `frontend/` - React, TypeScript, Vite, Tailwind CSS, TanStack Query, Lucide icons.

The default mode is safe demo mode. AI output is deterministic mock data and is clearly marked as `Demo AI Mode`.

## Core Features

### AI Health Recommendations

Users fill a health profile and a daily check-in. The backend stores both, runs the mock AI provider, validates structured data through Pydantic schemas, and returns a daily plan with readiness, movement, recovery, sleep, nutrition, things to avoid, and safety notes.

### ECG PDF Analysis

Users upload a PDF manually and click `Начать анализ`. The backend validates extension, MIME type, size, page count, and PDF readability. It extracts text where possible and stores only the structured analysis result, not the original PDF.

### Fall Detection

The Safety page supports emergency contacts, Telegram pairing code UX, demo devices, incident history, and a `Simulate Fall` action. Demo simulation calls the backend and creates a real `FallIncident` through the same safety service used by device events.

## Local Development

Backend:

```powershell
cd C:\instantrescuenova\backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd C:\instantrescuenova\frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

## Environment Variables

Copy `.env.example` to `.env` for backend configuration.

Important variables:

- `AI_MODE=mock` - default deterministic demo AI mode.
- `DATABASE_URL=sqlite:///./caspian_care.db` - local SQLite database.
- `MAX_PDF_UPLOAD_MB=20` - ECG PDF upload limit.
- `MAX_ECG_PDF_PAGES=10` - max ECG PDF pages.
- `TELEGRAM_BOT_TOKEN=` - optional real Telegram integration credential.
- `DEVICE_EVENT_COOLDOWN_SECONDS=60` - prevents duplicate alert storms.
- `ENABLE_DEMO_MODE=true` - enables `/api/demo/simulate-fall`.

## AI Real Mode

The app currently ships with a mock provider and a clean service boundary in `backend/app/services/ai.py`. To connect real AI, add a real provider implementation behind the same methods:

- `generate_health_recommendation(...)`
- `analyze_ecg_document(...)`

Keep API keys only on the backend and validate structured output before saving.

## Telegram Pairing

When a contact is created, the backend generates a pairing code such as `ABC123`. The UI shows:

```text
/start ABC123
```

A future Telegram bot webhook should match that code, save `telegram_chat_id`, and set the contact status to `connected`.

## Device API

Create a device from the Safety UI or:

```http
POST /api/devices
```

Future ESP32/wearable hardware should call:

```http
POST /api/devices/{device_id}/fall-events
Authorization: Bearer DEVICE_SECRET
Content-Type: application/json
```

```json
{
  "event_timestamp": "2026-07-15T18:42:00Z",
  "confidence": 0.91,
  "sensor_data": {
    "freefall_g": 0.32,
    "impact_g": 3.1,
    "stillness_std": 0.08
  }
}
```

The backend validates the token, checks duplicate/cooldown rules, creates an incident, and attempts notifications.

## Testing

Backend:

```powershell
python -m pytest backend/tests -q
```

Frontend:

```powershell
cd frontend
npm run build
```

## Medical Safety Disclaimer

Caspian Care provides AI-assisted explanations and lifestyle guidance. It does not diagnose disease, prescribe medication, cancel medication, or replace professional medical care.
