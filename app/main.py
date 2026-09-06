from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .database import add_application, add_job, init_db, list_applications, list_jobs
from .documents import extract_text
from .matching import match_candidate
from .skills import extract_skills


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="TalentLens API", version="0.1.0", lifespan=lifespan)


class JobCreate(BaseModel):
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    location: str = ""
    description: str = Field(min_length=20)


class MatchRequest(BaseModel):
    resume_text: str = Field(min_length=20)
    job_description: str = Field(min_length=20)


class ApplicationCreate(BaseModel):
    job_id: int
    status: str = "Saved"
    notes: str = ""


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/resume/analyze")
async def analyze_resume(file: UploadFile = File(...)) -> dict:
    try:
        text = extract_text(file.filename or "resume.txt", await file.read())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if not text:
        raise HTTPException(status_code=400, detail="The uploaded document did not contain readable text")
    return {"filename": file.filename, "text": text, "skills": extract_skills(text)}


@app.post("/match")
def match(request: MatchRequest) -> dict:
    return match_candidate(request.resume_text, request.job_description)


@app.get("/jobs")
def jobs() -> list[dict]:
    return list_jobs()


@app.post("/jobs")
def create_job(job: JobCreate) -> dict:
    return add_job(job.title, job.company, job.location, job.description)


@app.get("/applications")
def applications() -> list[dict]:
    return list_applications()


@app.post("/applications")
def create_application(application: ApplicationCreate) -> dict:
    return add_application(application.job_id, application.status, application.notes)
