"""Document text extraction for PDF, DOCX, and plain text uploads."""

from io import BytesIO
from pathlib import Path


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if suffix == ".docx":
        from docx import Document
        document = Document(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8", errors="replace").strip()
    raise ValueError("Supported resume formats are PDF, DOCX, TXT, and MD")
