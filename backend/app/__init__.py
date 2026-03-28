from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from app.api import register_blueprints
from app.config import Config
from app.errors import AppError
from app.extensions import db
from app.services.job_seed import seed_job_catalog
from app.services.skill_seed import seed_skill_catalog
from app.utils.responses import error_response


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config())

    db.init_app(app)
    with app.app_context():
        from app.models import (
            ExtractedSkill,
            GeneratedQuestion,
            NormalizedJobPosting,
            NormalizedSkill,
            OnboardingAnswer,
            OnboardingSession,
            RoleSkillMapping,
            RoleSkillTrend,
            SkillSynonym,
            TinyFishIngestionRun,
            User,
            UserPreference,
            UserPreferenceHistory,
        )

        db.create_all()
        seed_skill_catalog()
        seed_job_catalog()

    register_blueprints(app)
    register_error_handlers(app)

    return app


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
