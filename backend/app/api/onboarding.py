from flask import Blueprint, request

from app.errors import ValidationError
from app.schemas.onboarding import (
    CreateSessionPayload,
    GenerateQuestionsPayload,
    SaveAnswersPayload,
    UpdateSessionPayload,
    validate_payload,
)
from app.services.onboarding_service import OnboardingService
from app.utils.responses import success_response


onboarding_bp = Blueprint("onboarding", __name__)
service = OnboardingService()


@onboarding_bp.post("/session")
def create_session():
    payload = validate_payload(CreateSessionPayload, request.get_json(silent=True) or {})
    session = service.create_session(payload)
    return success_response(session, message="Onboarding session created.", status=201)


@onboarding_bp.get("/session/<session_id>")
def get_session(session_id: str):
    session = service.get_session(session_id)
    return success_response(session)


@onboarding_bp.put("/session/<session_id>")
def update_session(session_id: str):
    payload = validate_payload(UpdateSessionPayload, request.get_json(silent=True) or {})
    session = service.update_session(session_id, payload)
    return success_response(session, message="Onboarding session updated.")


@onboarding_bp.post("/session/<session_id>/resume")
def upload_resume(session_id: str):
    if "resume" not in request.files:
        raise ValidationError("Resume file is required under form field 'resume'.")

    session = service.upload_resume(session_id, request.files["resume"])
    return success_response(session, message="Resume uploaded and parsed.")


@onboarding_bp.post("/session/<session_id>/questions/generate")
def generate_questions(session_id: str):
    payload = validate_payload(
        GenerateQuestionsPayload, request.get_json(silent=True) or {}
    )
    result = service.generate_questions(session_id, payload.max_questions)
    return success_response(result, message="Follow-up questions generated.")


@onboarding_bp.post("/session/<session_id>/answers")
def save_answers(session_id: str):
    payload = validate_payload(SaveAnswersPayload, request.get_json(silent=True) or {})
    session = service.save_answers(session_id, payload)
    return success_response(session, message="Answers saved.")


@onboarding_bp.post("/session/<session_id>/finalize")
def finalize_session(session_id: str):
    session = service.finalize_session(session_id)
    return success_response(session, message="Onboarding profile finalized.")