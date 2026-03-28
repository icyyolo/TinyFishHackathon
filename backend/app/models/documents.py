from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SerializerMixin:
    def to_dict(self) -> dict:
        payload = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            payload[column.name] = value
        return payload


class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    onboarding_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class OnboardingSession(db.Model, SerializerMixin):
    __tablename__ = "onboarding_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), index=True, default="draft", nullable=False)
    profile: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    resume: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    completion: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    finalized_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class OnboardingAnswer(db.Model, SerializerMixin):
    __tablename__ = "onboarding_answers"
    __table_args__ = (UniqueConstraint("session_id", "question_id", name="uq_answer_session_question"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("onboarding_sessions.id"), index=True, nullable=False)
    question_id: Mapped[str] = mapped_column(String(36), ForeignKey("generated_questions.id"), index=True, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class ExtractedSkill(db.Model, SerializerMixin):
    __tablename__ = "extracted_skills"
    __table_args__ = (UniqueConstraint("session_id", "skill", name="uq_skill_session_skill"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("onboarding_sessions.id"), index=True, nullable=False)
    skill: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="resume", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class GeneratedQuestion(db.Model, SerializerMixin):
    __tablename__ = "generated_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("onboarding_sessions.id"), index=True, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), index=True, default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class UserPreference(db.Model, SerializerMixin):
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, index=True, nullable=False)
    raw_preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    normalized_preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    ranking_profile: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    defaults_applied: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class UserPreferenceHistory(db.Model, SerializerMixin):
    __tablename__ = "user_preference_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    preference_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_preferences.id"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, default="update")
    changed_fields: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class NormalizedSkill(db.Model, SerializerMixin):
    __tablename__ = "normalized_skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    canonical_name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aliases: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_emerging: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class SkillSynonym(db.Model, SerializerMixin):
    __tablename__ = "skill_synonyms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    normalized_skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("normalized_skills.id"), index=True, nullable=False)
    synonym: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class RoleSkillMapping(db.Model, SerializerMixin):
    __tablename__ = "role_skill_mappings"
    __table_args__ = (UniqueConstraint("target_role_key", "normalized_skill_id", name="uq_role_skill_mapping"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    target_role_key: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    target_role_name: Mapped[str] = mapped_column(String(120), nullable=False)
    normalized_skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("normalized_skills.id"), index=True, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    skill_frequency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_job_postings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    aggregation_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class RoleSkillTrend(db.Model, SerializerMixin):
    __tablename__ = "role_skill_trends"
    __table_args__ = (
        UniqueConstraint("target_role_key", "normalized_skill_id", "snapshot_date", name="uq_role_skill_trend_snapshot"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    target_role_key: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    target_role_name: Mapped[str] = mapped_column(String(120), nullable=False)
    normalized_skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("normalized_skills.id"), index=True, nullable=False)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    skill_frequency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    job_posting_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class NormalizedJobPosting(db.Model, SerializerMixin):
    __tablename__ = "normalized_job_postings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    external_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    role_key: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    role_name: Mapped[str] = mapped_column(String(120), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    company_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    locations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    work_arrangement: Mapped[str] = mapped_column(String(50), nullable=False, default="hybrid")
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, default="full_time")
    industries: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    seniority_level: Mapped[str] = mapped_column(String(50), nullable=False, default="mid")
    years_experience_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    years_experience_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    salary_period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    normalized_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    core_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    preferred_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    description_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class TinyFishIngestionRun(db.Model, SerializerMixin):
    __tablename__ = "tinyfish_ingestion_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider_run_id: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    target_role_key: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    target_role_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False, default="queued")
    request_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    tinyfish_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ingestion_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
