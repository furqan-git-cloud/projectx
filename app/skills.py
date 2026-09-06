"""Small, explainable skill vocabulary used by the MVP matcher."""

SKILLS = {
    "python", "java", "javascript", "typescript", "sql", "postgresql", "mysql",
    "fastapi", "django", "flask", "react", "node.js", "rest api", "graphql",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux", "pandas",
    "numpy", "scikit-learn", "machine learning", "nlp", "tensorflow", "pytorch",
    "communication", "leadership", "project management", "agile", "scrum",
    "research", "data analysis", "excel", "power bi", "tableau", "figma",
}

ALIASES = {
    "postgres": "postgresql",
    "restful api": "rest api",
    "rest apis": "rest api",
    "ml": "machine learning",
    "natural language processing": "nlp",
    "js": "javascript",
    "ts": "typescript",
}


def extract_skills(text: str) -> list[str]:
    normalized = " ".join(text.lower().split())
    found = set()
    for skill in SKILLS:
        if skill in normalized:
            found.add(skill)
    for alias, canonical in ALIASES.items():
        if alias in normalized:
            found.add(canonical)
    return sorted(found)
