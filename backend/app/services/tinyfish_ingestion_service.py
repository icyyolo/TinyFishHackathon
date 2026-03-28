from datetime import datetime, timezone

from flask import current_app

from app.errors import ValidationError
from app.repositories import TinyFishIngestionRepository
from app.services.tinyfish_client import TinyFishClient
from app.utils.responses import serialize_document


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TinyFishIngestionService:
    def __init__(self) -> None:
        self.repository = TinyFishIngestionRepository()

    def start_ingestion(self, payload):
        client = TinyFishClient()
        request_payload = payload.model_dump(mode="json", exclude_none=True)
        browser_profile = request_payload.get(
            "browser_profile", current_app.config["TINYFISH_DEFAULT_BROWSER_PROFILE"]
        )

        tinyfish_payload = {
            "url": request_payload["source_url"],
            "goal": request_payload.get("goal_override")
            or self._build_goal(request_payload["target_role"], request_payload["max_jobs"]),
            "browser_profile": browser_profile,
        }

        if request_payload.get("proxy_enabled", current_app.config["TINYFISH_DEFAULT_PROXY_ENABLED"]):
            tinyfish_payload["proxy_config"] = {
                "enabled": True,
                "country_code": request_payload.get(
                    "proxy_country_code",
                    current_app.config["TINYFISH_DEFAULT_PROXY_COUNTRY_CODE"],
                ),
            }

        response = client.start_async_run(tinyfish_payload)
        run_id = response.get("run_id") or response.get("id")
        if not run_id:
            raise ValidationError(
                "TinyFish did not return a run_id.",
                payload={"tinyfish_response": response},
            )

        run = self.repository.create_run(
            provider_run_id=run_id,
            target_role_name=request_payload["target_role"],
            source_url=request_payload["source_url"],
            request_payload={
                "requested_at": utcnow_iso(),
                "tinyfish_payload": tinyfish_payload,
                "backend_request": request_payload,
            },
            status="QUEUED",
        )

        return serialize_document(
            {
                "run": run,
                "tinyfish": response,
                "next_step": "Poll GET /api/skills/ingest/tinyfish/runs/<run_id> until status is COMPLETED, then call POST /api/skills/ingest/tinyfish/runs/<run_id>/ingest.",
            }
        )

    def get_run_status(self, run_id: str):
        client = TinyFishClient()
        remote_run = client.get_run(run_id)
        local_run = self.repository.update_run(
            run_id,
            status=remote_run.get("status", "UNKNOWN"),
            tinyfish_response=remote_run,
        )
        return serialize_document(
            {
                "run": local_run,
                "tinyfish": remote_run,
            }
        )

    def ingest_completed_run(self, run_id: str):
        client = TinyFishClient()
        remote_run = client.get_run(run_id)
        status = remote_run.get("status", "UNKNOWN")
        local_run = self.repository.update_run(
            run_id,
            status=status,
            tinyfish_response=remote_run,
        )
        if status != "COMPLETED":
            raise ValidationError(
                "TinyFish run is not completed yet.",
                payload={"status": status, "run": local_run},
            )

        summary = self.repository.ingest_role_skills_from_jobs(
            run_id,
            remote_run.get("result") or {},
        )
        updated_local_run = self.repository.get_run(run_id)
        return serialize_document(
            {
                "run": updated_local_run,
                "tinyfish": remote_run,
                "ingestion_summary": summary,
            }
        )

    def _build_goal(self, target_role: str, max_jobs: int) -> str:
        return (
            f"Open the provided website and extract up to {max_jobs} job postings relevant to the role '{target_role}'. "
            "Return JSON only with this schema: { target_role, jobs: [ { title, company, location, posted_at, skills, required_skills, preferred_skills } ] }. "
            "Each skill field must be an array of plain skill names. Exclude duplicates and non-job pages."
        )
