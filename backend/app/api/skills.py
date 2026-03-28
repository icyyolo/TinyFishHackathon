from flask import Blueprint, request

from app.schemas.skills import (
    SkillRadarQuery,
    SkillTrendQuery,
    TinyFishIngestionStartPayload,
    TinyFishRunQuery,
    validate_payload,
)
from app.services.skill_radar_service import SkillRadarService
from app.services.tinyfish_ingestion_service import TinyFishIngestionService
from app.utils.responses import success_response


skills_bp = Blueprint("skills", __name__)
radar_service = SkillRadarService()
tinyfish_service = TinyFishIngestionService()


@skills_bp.get("/radar")
def fetch_skill_radar():
    payload = validate_payload(SkillRadarQuery, request.args.to_dict())
    result = radar_service.fetch_skill_radar(payload.user_id, payload.target_role)
    return success_response(result)


@skills_bp.get("/trends")
def fetch_trending_skills():
    payload = validate_payload(SkillTrendQuery, request.args.to_dict())
    result = radar_service.fetch_trending_skills(
        target_role=payload.target_role,
        window_days=payload.window_days,
        limit=payload.limit,
    )
    return success_response(result)


@skills_bp.post("/ingest/tinyfish/start")
def start_tinyfish_ingestion():
    payload = validate_payload(
        TinyFishIngestionStartPayload, request.get_json(silent=True) or {}
    )
    result = tinyfish_service.start_ingestion(payload)
    return success_response(result, message="TinyFish ingestion started.", status=202)


@skills_bp.get("/ingest/tinyfish/runs/<run_id>")
def get_tinyfish_run(run_id: str):
    payload = validate_payload(TinyFishRunQuery, {"run_id": run_id})
    result = tinyfish_service.get_run_status(payload.run_id)
    return success_response(result)


@skills_bp.post("/ingest/tinyfish/runs/<run_id>/ingest")
def ingest_tinyfish_run(run_id: str):
    payload = validate_payload(TinyFishRunQuery, {"run_id": run_id})
    result = tinyfish_service.ingest_completed_run(payload.run_id)
    return success_response(result, message="TinyFish run ingested into skill trends.")
