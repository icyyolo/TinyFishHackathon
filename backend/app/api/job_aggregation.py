from flask import Blueprint, request

from app.schemas.job_aggregation import (
    JobAggregationListJobsQuery,
    JobAggregationMetricsQuery,
    JobAggregationRunPayload,
    LinkedInTinyFishIngestionPayload,
    RetryFailedJobsPayload,
    validate_payload,
)
from app.services.job_aggregation_service import JobAggregationService
from app.utils.responses import success_response


job_aggregation_bp = Blueprint("job_aggregation", __name__)
service = JobAggregationService()


@job_aggregation_bp.post("/runs")
def start_ingestion_run():
    payload = validate_payload(JobAggregationRunPayload, request.get_json(silent=True) or {})
    result = service.start_ingestion(payload)
    return success_response(result, status=201)


@job_aggregation_bp.post("/linkedin/sync")
def sync_linkedin_jobs():
    payload = validate_payload(LinkedInTinyFishIngestionPayload, request.get_json(silent=True) or {})
    result = service.sync_linkedin_jobs(payload)
    status = 201 if result.get("status") == "completed" else 202
    return success_response(result, status=status)


@job_aggregation_bp.get("/linkedin/poll/<provider_run_id>")
def poll_linkedin_run(provider_run_id: str):
    target_role = request.args.get("target_role", "")
    linkedin_url = request.args.get("linkedin_url", "")
    result = service.poll_linkedin_run(provider_run_id, target_role, linkedin_url)
    return success_response(result)


@job_aggregation_bp.get("/metrics")
def fetch_ingestion_metrics():
    payload = validate_payload(JobAggregationMetricsQuery, request.args.to_dict())
    result = service.fetch_metrics(payload.connector_type)
    return success_response(result)


@job_aggregation_bp.get("/jobs")
def list_ingested_jobs():
    payload = validate_payload(JobAggregationListJobsQuery, request.args.to_dict())
    result = service.list_ingested_jobs(
        limit=payload.limit,
        offset=payload.offset,
        source=payload.source,
        role=payload.role,
    )
    return success_response(result)


@job_aggregation_bp.post("/retry-failed")
def retry_failed_jobs():
    payload = validate_payload(RetryFailedJobsPayload, request.get_json(silent=True) or {})
    result = service.retry_failed_jobs(payload)
    return success_response(result)
