# TalentLens

TalentLens is an AI-assisted recruitment and job-matching MVP. It parses resumes, extracts skills, compares candidates with job descriptions, identifies gaps, and tracks applications.

## What works now

- PDF, DOCX, TXT, and Markdown resume extraction
- Explainable skill extraction with aliases such as `ML` and `RESTful APIs`
- Hybrid matching: TF-IDF semantic similarity plus skill coverage
- FastAPI REST API with OpenAPI docs
- Streamlit dashboard for matching, job storage, and application tracking
- Local sign-in and account creation with hashed passwords
- Multi-platform job discovery links and customer support assistant
- SQLite persistence for local development
- Pytest coverage for the matching core and API health check

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the API. In another terminal, run `streamlit run dashboard.py` and open `http://localhost:8501`.

The dashboard opens with a local Sign in / Create account screen. Accounts are stored in the local SQLite database with PBKDF2 password hashes. This is appropriate for local development; production should add HTTPS, email verification, password reset, rate limiting, and server-managed sessions.

Run tests with:

```powershell
pytest
```

## API examples

Create a job with `POST /jobs`, analyze a resume with `POST /resume/analyze`, and send resume/job text to `POST /match`.

## Roadmap

The next production increments are JWT authentication, PostgreSQL migrations, persisted resumes and match history, an optional LLM provider for cover letters, richer entity extraction, and role-based recruiter workflows. The current matching engine is deliberately deterministic so its results are transparent and testable.

## Docker

```powershell
docker compose up --build
```
