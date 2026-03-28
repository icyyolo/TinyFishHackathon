import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select

from app.errors import NotFoundError, ValidationError
from app.extensions import db
from app.models import (
    ExtractedSkill,
    NormalizedSkill,
    OnboardingSession,
    RoleSkillMapping,
    RoleSkillTrend,
    SkillSynonym,
    User,
)


def role_key(value: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-")


class SkillRadarRepository:
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

    def get_latest_session(self, user_id: str):
        parsed_user_id = self.parse_id(user_id, "user_id")
        session = db.session.scalar(
            select(OnboardingSession)
            .where(OnboardingSession.user_id == parsed_user_id)
            .order_by(desc(OnboardingSession.updated_at))
        )
        return session.to_dict() if session else None

    def get_extracted_skills_for_session(self, session_id: str):
        parsed_session_id = self.parse_id(session_id, "session_id")
        rows = db.session.scalars(
            select(ExtractedSkill).where(ExtractedSkill.session_id == parsed_session_id)
        ).all()
        return [row.to_dict() for row in rows]

    def get_skill_lookup(self):
        skills = db.session.scalars(select(NormalizedSkill)).all()
        synonyms = db.session.scalars(select(SkillSynonym)).all()

        skill_records = {skill.id: skill.to_dict() for skill in skills}
        alias_map = {}
        for skill in skills:
            record = skill.to_dict()
            alias_map[self._normalize_text(skill.canonical_name)] = record
            for alias in skill.aliases or []:
                alias_map[self._normalize_text(alias)] = record

        for synonym in synonyms:
            skill_record = skill_records.get(synonym.normalized_skill_id)
            if skill_record:
                alias_map[self._normalize_text(synonym.synonym)] = skill_record

        return alias_map

    def get_role_skill_mappings(self, target_role: str):
        target_role_key = role_key(target_role)
        rows = db.session.execute(
            select(RoleSkillMapping, NormalizedSkill)
            .join(NormalizedSkill, RoleSkillMapping.normalized_skill_id == NormalizedSkill.id)
            .where(RoleSkillMapping.target_role_key == target_role_key)
            .order_by(desc(RoleSkillMapping.importance_score), desc(RoleSkillMapping.skill_frequency))
        ).all()
        return [
            {
                **mapping.to_dict(),
                "skill": skill.to_dict(),
            }
            for mapping, skill in rows
        ]

    def get_role_skill_trends(self, target_role: str, window_days: int = 90):
        target_role_key = role_key(target_role)
        start_date = datetime.now(timezone.utc) - timedelta(days=window_days)
        rows = db.session.execute(
            select(RoleSkillTrend, NormalizedSkill)
            .join(NormalizedSkill, RoleSkillTrend.normalized_skill_id == NormalizedSkill.id)
            .where(
                RoleSkillTrend.target_role_key == target_role_key,
                RoleSkillTrend.snapshot_date >= start_date,
            )
            .order_by(RoleSkillTrend.snapshot_date.asc())
        ).all()
        return [
            {
                **trend.to_dict(),
                "skill": skill.to_dict(),
            }
            for trend, skill in rows
        ]

    def get_distinct_role_names(self):
        rows = db.session.execute(
            select(RoleSkillMapping.target_role_key, func.max(RoleSkillMapping.target_role_name))
            .group_by(RoleSkillMapping.target_role_key)
        ).all()
        return {key: name for key, name in rows}

    def _normalize_text(self, value: str) -> str:
        return " ".join(str(value).strip().lower().replace("/", " ").replace("-", " ").split())
