"""Explainable candidate-to-job matching."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skills import extract_skills


def match_candidate(resume_text: str, job_description: str) -> dict:
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_description))
    matching = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)

    documents = [resume_text or "", job_description or ""]
    try:
        vectors = TfidfVectorizer(stop_words="english").fit_transform(documents)
        semantic_score = float(cosine_similarity(vectors[0], vectors[1])[0][0])
    except ValueError:
        semantic_score = 0.0

    skill_score = len(matching) / len(job_skills) if job_skills else 0.0
    overall = round((semantic_score * 0.45 + skill_score * 0.55) * 100, 1)
    return {
        "score": overall,
        "semantic_score": round(semantic_score * 100, 1),
        "skill_score": round(skill_score * 100, 1),
        "matching_skills": matching,
        "missing_skills": missing,
        "resume_skills": sorted(resume_skills),
        "required_skills": sorted(job_skills),
    }
