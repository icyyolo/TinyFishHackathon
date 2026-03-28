from flask import Flask
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.api import register_blueprints
from app.config import Config
from app.errors import AppError
from app.extensions import db
from app.services.job_seed import seed_job_catalog
from app.services.skill_seed import seed_skill_catalog
from app.utils.responses import error_response


NORMALIZED_JOB_POSTING_COMPAT_COLUMNS = {
    "description": "TEXT",
    "posted_at": "DATETIME",
    "salary_text": "TEXT",
    "apply_url": "TEXT",
    "deduplication_key": "VARCHAR(255)",
    "source_count": "INTEGER DEFAULT 1",
    "last_ingested_at": "DATETIME",
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config())

    db.init_app(app)
    with app.app_context():
        from app.models import (
            ExtractedSkill,
            GeneratedQuestion,
            JobIngestionRun,
            NormalizedJobPosting,
            NormalizedSkill,
            OnboardingAnswer,
            OnboardingSession,
            RawJobPosting,
            RoleSkillMapping,
            RoleSkillTrend,
            SkillSynonym,
            TinyFishIngestionRun,
            User,
            UserPreference,
            UserPreferenceHistory,
        )

        db.create_all()
        ensure_aggregation_schema_compatibility()
        seed_skill_catalog()
        seed_job_catalog()

    register_blueprints(app)
    register_error_handlers(app)

    return app


def ensure_aggregation_schema_compatibility() -> None:
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    if "normalized_job_postings" not in tables:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("normalized_job_postings")}
    for column_name, column_type in NORMALIZED_JOB_POSTING_COMPAT_COLUMNS.items():
        if column_name in existing_columns:
            continue
        db.session.execute(
            text(f"ALTER TABLE normalized_job_postings ADD COLUMN {column_name} {column_type}")
        )
    if "source_count" not in existing_columns:
        db.session.execute(text("UPDATE normalized_job_postings SET source_count = 1 WHERE source_count IS NULL"))
    db.session.commit()


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return error_response(error.message, error.status_code, error.payload)

    @app.errorhandler(413)
    def handle_payload_too_large(_error):
        return error_response("Uploaded file exceeds the configured size limit.", 413)

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error: SQLAlchemyError):
        db.session.rollback()
        if app.config["DEBUG"]:
            raise error
        return error_response("A database error occurred.", 500)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        if app.config["DEBUG"]:
            raise error
        return error_response("An unexpected server error occurred.", 500)
