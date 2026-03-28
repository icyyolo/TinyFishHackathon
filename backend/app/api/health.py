from flask import Blueprint

from app.utils.responses import success_response


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return success_response({"status": "ok"}, message="Service is healthy.")