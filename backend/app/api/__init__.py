from flask import Flask

from app.api.health import health_bp
from app.api.job_aggregation import job_aggregation_bp
from app.api.jobs import jobs_bp
from app.api.onboarding import onboarding_bp
from app.api.preferences import preferences_bp
from app.api.skills import skills_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(onboarding_bp, url_prefix="/api/onboarding")
    app.register_blueprint(preferences_bp, url_prefix="/api/preferences")
    app.register_blueprint(skills_bp, url_prefix="/api/skills")
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(job_aggregation_bp, url_prefix="/api/job-aggregation")
