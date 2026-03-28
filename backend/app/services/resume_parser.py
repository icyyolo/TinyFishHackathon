import re
from io import BytesIO

from docx import Document
from pypdf import PdfReader

from app.errors import ValidationError


SKILL_KEYWORDS = [
    "python",
    "flask",
    "django",
    "fastapi",
    "java",
    "spring",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "node",
    "mongodb",
    "sql",
    "postgresql",
    "mysql",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "git",
    "rest api",
    "graphql",
    "machine learning",
    "data analysis",
    "communication",
    "leadership",
    "project management",
]

ROLE_KEYWORDS = [
    "software engineer",
    "backend engineer",
    "frontend engineer",
    "full stack developer",
    "data analyst",
    "data scientist",
    "product manager",
    "ui/ux designer",
    "devops engineer",
    "qa engineer",
    "business analyst",
]

EDUCATION_PATTERN = re.compile(
    r"\b(bachelor|master|phd|diploma|degree|bsc|msc|mba|computer science|engineering|information systems)\b",
    re.IGNORECASE,
)


class ResumeParserService:
    def parse_resume(self, filename: str, file_bytes: bytes) -> dict:
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in {"pdf", "docx", "txt"}:
            raise ValidationError("Unsupported resume format. Allowed types: pdf, docx, txt.")

        text = self._extract_text(extension, file_bytes)
        if not text.strip():
            raise ValidationError("Resume could not be parsed into readable text.")

        extracted_skills = self._extract_keywords(text, SKILL_KEYWORDS)
        education = self._extract_education(text)
        role_keywords = self._extract_keywords(text, ROLE_KEYWORDS)

        return {
            "filename": filename,
            "parsed_text_excerpt": text[:1200],
            "skills": extracted_skills,
            "education": education,
            "role_keywords": role_keywords,
        }

    def _extract_text(self, extension: str, file_bytes: bytes) -> str:
        if extension == "txt":
            return file_bytes.decode("utf-8", errors="ignore")
        if extension == "pdf":
            reader = PdfReader(BytesIO(file_bytes))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if extension == "docx":
            document = Document(BytesIO(file_bytes))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        raise ValidationError("Unsupported file type.")

    def _extract_keywords(self, text: str, keywords: list[str]) -> list[str]:
        lowered = text.lower()
        matches = []
        for keyword in keywords:
            if keyword in lowered:
                matches.append(keyword.title() if keyword.islower() else keyword)
        return self._unique(matches)

    def _extract_education(self, text: str) -> list[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        matches = []
        for line in lines:
            if EDUCATION_PATTERN.search(line):
                matches.append(line[:180])
        return self._unique(matches[:5])

    def _unique(self, values: list[str]) -> list[str]:
        seen = set()
        unique_values = []
        for value in values:
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            unique_values.append(value)
        return unique_values