from app.matching import match_candidate
from app.skills import extract_skills


def test_extracts_aliases_and_skills():
    assert extract_skills("Built RESTful APIs with Python and ML") == ["machine learning", "python", "rest api"]


def test_match_reports_missing_skills_and_score():
    result = match_candidate(
        "Python developer building REST APIs with FastAPI",
        "Need a Python engineer with FastAPI, Docker, and PostgreSQL",
    )
    assert result["score"] > 0
    assert "python" in result["matching_skills"]
    assert "docker" in result["missing_skills"]
