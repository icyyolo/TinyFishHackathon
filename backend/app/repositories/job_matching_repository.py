import uuid

from sqlalchemy import desc, select

from app.errors import NotFoundError, ValidationError
from app.extensions import db
from app.models import (
    ExtractedSkill,
    NormalizedJobPosting,
    NormalizedSkill,
    OnboardingSession,
    SkillSynonym,
    User,
    UserPreference,
)


class JobMatchingRepository:
    def parse_id(self, value: str, field_name: str = "id") -> str:
        try:
            return str(uuid.UUID(value))
        except (ValueError, TypeError) as error:
            raise ValidationError(f"Invalid {field_name}.") from error

    def get_user(self, user_id: str):
        user = db.session.get(User, self.parse_id(user_id, "user_id"))
        if not user:
            raise NotFoundError("User not found.")
        return user.to_dict()

    def get_user_preferences(self, user_id: str):
        parsed_user_id = self.parse_id(user_id, "user_id")
        row = db.session.scalar(
            select(UserPreference).where(UserPreference.user_id == parsed_user_id)
        )
        return row.to_dict() if row else None

    def get_latest_session(self, user_id: str):
        parsed_user_id = self.parse_id(user_id, "user_id")
        row = db.session.scalar(
            select(OnboardingSession)
            .where(OnboardingSession.user_id == parsed_user_id)
            .order_by(desc(OnboardingSession.updated_at))
        )
        return row.to_dict() if row else None

    def get_extracted_skills_for_session(self, session_id: str):
        parsed_session_id = self.parse_id(session_id, "session_id")
        rows = db.session.scalars(
            select(ExtractedSkill).where(ExtractedSkill.session_id == parsed_session_id)
        ).all()
        return [row.to_dict() for row in rows]

    def list_jobs(self):
        rows = db.session.scalars(select(NormalizedJobPosting)).all()
        return [row.to_dict() for row in rows]

    def get_job(self, job_id: str):
        row = db.session.get(NormalizedJobPosting, self.parse_id(job_id, "job_id"))
        if not row:
            raise NotFoundError("Job not found.")
        return row.to_dict()

    def get_skill_lookup(self):
        skills = db.session.scalars(select(NormalizedSkill)).all()
        synonyms = db.session.scalars(select(SkillSynonym)).all()

        by_id = {skill.id: skill.to_dict() for skill in skills}
        lookup = {}
        for skill in skills:
            record = skill.to_dict()
            lookup[self._normalize_text(skill.canonical_name)] = record
            for alias in skill.aliases or []:
                lookup[self._normalize_text(alias)] = record

        for synonym in synonyms:
            skill_record = by_id.get(synonym.normalized_skill_id)
            if skill_record:
                lookup[self._normalize_text(synonym.synonym)] = skill_record
        return lookup

    def _normalize_text(self, value: str) -> str:
        return " ".join(str(value).strip().lower().replace("/", " ").replace("-", " ").split())
