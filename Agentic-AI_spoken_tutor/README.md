# AI Speaking Tutor

This project is a full-stack spoken English platform that combines learner practice, Business English onboarding, teacher monitoring, recruiter screening, QA-governed question management, and deterministic assessment scoring.

## What Is Included

- Frontend: browser application served from FastAPI at `/`
- Backend: FastAPI APIs for auth, learner practice, teacher, recruiter, and QA workflows
- Database: SQLAlchemy-backed persistence with SQLite for local development and PostgreSQL-ready configuration via `DATABASE_URL`
- Agent modules: scoring, feedback, monitoring, recruiter, orchestration, and QA workflows
- Seeded content: pre-approved IELTS, CEFR, and Business English question bank items

## Project Architecture

```text
Agentic-AI_spoken_tutor/
	backend/
		api/                  FastAPI routes and request schemas
		agents/               Modular workflow engines
		core/                 Runtime configuration
		data/                 Seed loaders and question bank
		db/                   SQLAlchemy engine, models, bootstrap
		qa_engine/            QA lifecycle logic and persistence
		stores/               Database-backed domain persistence APIs
	frontend/
		index.html            Browser app shell for auth and role dashboards
	scripts/
		smoke-test.ps1        API flow verification
		auth-smoke-test.ps1   Auth and onboarding verification
	data_store/
		spoken_tutor.db       Local SQLite database generated at runtime
```

## Core Runtime Components

1. Auth and user management
2. Learner onboarding with goal-to-pathway mapping
3. Business English profiling fields
4. Practice session delivery and scoring
5. Feedback and progress tracking
6. Teacher class management and analytics
7. Recruiter screening pack management
8. QA-governed question bank lifecycle

## Local Development Setup

1. Open a terminal at the workspace root.
2. Start the API server:

```powershell
$env:PYTHONPATH="D:\spoken-tuter-new\spoken-tuter-new\Agentic-AI_spoken_tutor"; .venv\Scripts\python.exe -m uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8001
```

3. Open the app in the browser:

```text
http://127.0.0.1:8001/
```

4. Optional API docs:

```text
http://127.0.0.1:8001/docs
```

## Environment Variables

- `DATABASE_URL`: defaults to local SQLite database under `data_store/spoken_tutor.db`
- `SESSION_HOURS`: auth session expiration window, default `12`

## Verification Scripts

Run authentication flow verification:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\auth-smoke-test.ps1 -BaseUrl "http://127.0.0.1:8001"
```

Run broader backend flow verification:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke-test.ps1 -BaseUrl "http://127.0.0.1:8001"
```
