from flask import Blueprint, request

from app.schemas.preferences import (
    NormalizePreferencesPayload,
    UpsertPreferencesPayload,
    validate_payload,
)
from app.services.preferences_service import PreferenceService
from app.utils.responses import success_response


preferences_bp = Blueprint("preferences", __name__)
service = PreferenceService()


@preferences_bp.get("/<user_id>")
def fetch_preferences(user_id: str):
    result = service.fetch_preferences(user_id)
    return success_response(result)


@preferences_bp.post("/<user_id>")
def create_or_update_preferences(user_id: str):
    payload = validate_payload(UpsertPreferencesPayload, request.get_json(silent=True) or {})
    result = service.upsert_preferences(user_id, payload)
    return success_response(result, message="User preferences saved.")


@preferences_bp.post("/normalize")
def normalize_preferences():
    payload = validate_payload(NormalizePreferencesPayload, request.get_json(silent=True) or {})
    result = service.normalize_preferences(payload)
    return success_response(result, message="Preference values normalized.")
