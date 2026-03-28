from flask import Blueprint, request

from app.schemas.jobs import JobMatchDetailQuery, JobRecommendationsQuery, validate_payload
from app.services.job_matching_service import JobMatchingService
from app.utils.responses import success_response


jobs_bp = Blueprint("jobs", __name__)
service = JobMatchingService()


@jobs_bp.get("/recommendations")
def fetch_recommended_jobs():
    payload = validate_payload(JobRecommendationsQuery, request.args.to_dict())
    result = service.fetch_recommended_jobs(payload.user_id, payload.limit)
    return success_response(result)


@jobs_bp.get("/<job_id>/match")
def fetch_job_match(job_id: str):
    payload = validate_payload(
        JobMatchDetailQuery,
        {"user_id": request.args.get("user_id"), "job_id": job_id},
    )
    result = service.fetch_job_match_detail(payload.user_id, payload.job_id)
    return success_response(result)
