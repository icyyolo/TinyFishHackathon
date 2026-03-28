import hashlib
import json
import re
from datetime import datetime, timezone
from time import monotonic, sleep
from urllib.parse import urlparse

from flask import current_app

from app.errors import AppError, ValidationError
from app.repositories import JobAggregationRepository
from app.repositories.skill_radar_repository import role_key
from app.services.job_aggregation_connectors import JobConnectorRegistry
from app.services.preference_normalizer import (
    COMPANY_SIZE_MAP,
    COMPANY_TYPE_MAP,
    INDUSTRY_MAP,
    JOB_TYPE_MAP,
    LOCATION_MAP,
    PERIOD_MAP,
    WORK_ARRANGEMENT_MAP,
)
from app.services.tinyfish_client import TinyFishClient
from app.utils.responses import serialize_document


SENIORITY_KEYWORDS = {
    "intern": "intern",
    "junior": "junior",
    "associate": "junior",
    "mid": "mid",
    "senior": "senior",
    "staff": "senior",
    "lead": "lead",
    "principal": "lead",
    "head": "lead",
}

CURRENCY_HINTS = {
    "usd": "USD",
    "us$": "USD",
    "$": "USD",
    "sgd": "SGD",
    "s$": "SGD",
    "eur": "EUR",
    "gbp": "GBP",
}


TINYFISH_TERMINAL_FAILURES = {"FAILED", "ERROR", "CANCELLED", "TIMED_OUT", "EXPIRED"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobAggregationService:
    def __init__(self) -> None:
        self.repository = JobAggregationRepository()
        self.connectors = JobConnectorRegistry()

    def start_ingestion(self, payload):
        request_payload = payload.model_dump(mode="json", exclude_none=True)
        connector = self.connectors.get_connector(request_payload["connector_type"])
        connector_name = request_payload.get("connector_name") or connector.connector_name
        raw_jobs = connector.fetch_jobs(request_payload)
        return self._ingest_jobs(request_payload, connector_name, raw_jobs)

    def sync_linkedin_jobs(self, payload):
        request_payload = payload.model_dump(mode="json", exclude_none=True)
        client = TinyFishClient()
        tinyfish_payload = self._build_linkedin_tinyfish_payload(request_payload)
        tinyfish_response = client.start_async_run(tinyfish_payload)
        provider_run_id = tinyfish_response.get("run_id") or tinyfish_response.get("id")
        if not provider_run_id:
            raise ValidationError(
                "TinyFish did not return a run_id for the LinkedIn ingestion request.",
                payload={"tinyfish_response": tinyfish_response},
            )

        remote_run = self._wait_for_tinyfish_run(
            client,
            provider_run_id,
            timeout_seconds=request_payload["wait_timeout_seconds"],
            poll_interval_seconds=request_payload["poll_interval_seconds"],
        )
        remote_status = ((remote_run or {}).get("status") or "QUEUED").upper()

        if remote_status != "COMPLETED":
            return serialize_document(
                {
                    "status": "pending",
                    "provider_run_id": provider_run_id,
                    "target_role": request_payload["target_role"],
                    "linkedin_url": request_payload["linkedin_url"],
                    "tinyfish": {
                        "run_id": provider_run_id,
                        "status": remote_status,
                        "response": remote_run or tinyfish_response,
                    },
                    "message": "TinyFish is still processing the LinkedIn job search. Recommendations will use the current normalized job index until the run completes.",
                }
            )

        extracted_jobs = self._extract_jobs_from_tinyfish(
            remote_run.get("result") or remote_run,
            request_payload,
        )
        if not extracted_jobs:
            raise ValidationError(
                "TinyFish completed, but no LinkedIn job postings could be extracted.",
                payload={"provider_run_id": provider_run_id, "tinyfish": remote_run},
            )

        ingestion_request = {
            "connector_type": "tinyfish_linkedin",
            "connector_name": "TinyFish LinkedIn Connector",
            "source_label": "LinkedIn via TinyFish",
            "source_url": request_payload["linkedin_url"],
            "jobs": extracted_jobs,
            "metadata": {
                "provider_run_id": provider_run_id,
                "target_role": request_payload["target_role"],
                "max_jobs": request_payload["max_jobs"],
            },
        }
        ingestion_result = self._ingest_jobs(
            ingestion_request,
            ingestion_request["connector_name"],
            extracted_jobs,
        )

        return serialize_document(
            {
                "status": "completed",
                "provider_run_id": provider_run_id,
                "target_role": request_payload["target_role"],
                "linkedin_url": request_payload["linkedin_url"],
                "tinyfish": {
                    "run_id": provider_run_id,
                    "status": remote_status,
                },
                "ingestion": ingestion_result,
            }
        )

    def _ingest_jobs(self, request_payload: dict, connector_name: str, raw_jobs: list[dict]):
        source_label = request_payload.get("source_label") or connector_name
        source_url = request_payload.get("source_url")

        run = self.repository.create_run(
            connector_type=request_payload["connector_type"],
            connector_name=connector_name,
            source_label=source_label,
            source_url=source_url,
            request_payload=request_payload,
            requested_job_count=len(raw_jobs),
        )

        metrics = {
            "requested_jobs": len(raw_jobs),
            "fetched_jobs": 0,
            "parsed_jobs": 0,
            "normalized_jobs": 0,
            "deduplicated_jobs": 0,
            "failed_jobs": 0,
        }
        preview = []

        try:
            self.repository.mark_run_started(run.id, fetched_job_count=len(raw_jobs))
            metrics["fetched_jobs"] = len(raw_jobs)

            for raw_job in raw_jobs:
                result = self._process_raw_job(run.id, request_payload, raw_job)
                if result["status"] in {"normalized", "deduplicated"}:
                    metrics["parsed_jobs"] += 1
                    metrics[f"{result['status']}_jobs"] += 1
                    if len(preview) < 5:
                        preview.append(result["job"])
                else:
                    metrics["failed_jobs"] += 1

            if metrics["failed_jobs"] and metrics["parsed_jobs"]:
                final_status = "completed_with_errors"
            elif metrics["failed_jobs"]:
                final_status = "failed"
            else:
                final_status = "completed"

            run_payload = self.repository.finalize_run(run.id, final_status, metrics)
            return serialize_document(
                {
                    "run": run_payload,
                    "metrics": metrics,
                    "connectors": self.connectors.list_connectors(),
                    "jobs_preview": preview,
                }
            )
        except Exception as error:
            self.repository.fail_run(run.id, str(error), metrics)
            raise

    def fetch_metrics(self, connector_type: str | None = None):
        return serialize_document(
            {
                "metrics": self.repository.fetch_metrics(connector_type),
                "connectors": self.connectors.list_connectors(),
            }
        )

    def list_ingested_jobs(self, limit: int, offset: int, source: str | None = None, role: str | None = None):
        return serialize_document(self.repository.list_ingested_jobs(limit, offset, source=source, role=role))

    def retry_failed_jobs(self, payload):
        request_payload = payload.model_dump(mode="json", exclude_none=True)
        jobs = self.repository.get_retryable_raw_jobs(
            run_id=request_payload.get("run_id"),
            raw_job_ids=request_payload.get("raw_job_ids"),
            limit=request_payload.get("limit", 25),
        )

        retried = []
        succeeded = 0
        failed = 0
        for raw_job in jobs:
            run = self.repository.get_run(raw_job.ingestion_run_id)
            request_context = run.get("request_payload") or {}
            result = self._process_existing_raw_job(raw_job, request_context)
            retried.append(result)
            if result["status"] in {"normalized", "deduplicated"}:
                succeeded += 1
            else:
                failed += 1

        return serialize_document(
            {
                "retried_count": len(jobs),
                "succeeded_count": succeeded,
                "failed_count": failed,
                "results": retried,
            }
        )

    def _process_raw_job(self, run_id: str, request_context: dict, raw_job: dict) -> dict:
        source_name = raw_job.get("source") or request_context.get("source_label") or request_context.get("connector_name") or request_context["connector_type"]
        source_url = raw_job.get("source_url") or request_context.get("source_url")
        apply_url = raw_job.get("apply_url") or raw_job.get("job_url") or raw_job.get("url") or source_url
        raw_record = self.repository.create_raw_job(
            run_id=run_id,
            source_connector=request_context["connector_type"],
            source_name=source_name,
            source_job_id=raw_job.get("source_job_id") or raw_job.get("external_id"),
            source_url=source_url,
            apply_url=apply_url,
            raw_payload=raw_job,
        )
        return self._process_existing_raw_job(raw_record, request_context)

    def _process_existing_raw_job(self, raw_record, request_context: dict) -> dict:
        raw_job_id = raw_record.id
        raw_payload = dict(raw_record.raw_payload or {})
        attempts = int(raw_record.processing_attempts or 0) + 1
        try:
            normalized_payload = self._normalize_job_payload(raw_payload, request_context, raw_record.ingestion_run_id, raw_job_id)
            existing = self._find_duplicate(normalized_payload)
            if existing:
                job = self.repository.merge_into_normalized_job(
                    existing,
                    normalized_payload,
                    raw_job_id=raw_job_id,
                    run_id=raw_record.ingestion_run_id,
                )
                status = "deduplicated"
            else:
                job = self.repository.create_normalized_job(normalized_payload)
                status = "normalized"

            self.repository.update_raw_job(
                raw_job_id,
                normalized_job_id=job.id,
                processing_status=status,
                processing_attempts=attempts,
                deduplication_key=normalized_payload.get("deduplication_key"),
                extracted_payload=serialize_document(normalized_payload),
                parse_error=None,
                processed_at=utcnow(),
            )
            return {"raw_job_id": raw_job_id, "status": status, "job": job.to_dict()}
        except ValidationError as error:
            self.repository.update_raw_job(
                raw_job_id,
                processing_status="failed_parsing",
                processing_attempts=attempts,
                parse_error=error.message,
                extracted_payload={"details": serialize_document(error.payload)},
                processed_at=utcnow(),
            )
            return {"raw_job_id": raw_job_id, "status": "failed", "error": error.message}
        except Exception as error:
            self.repository.update_raw_job(
                raw_job_id,
                processing_status="failed_normalization",
                processing_attempts=attempts,
                parse_error=str(error),
                extracted_payload={},
                processed_at=utcnow(),
            )
            return {"raw_job_id": raw_job_id, "status": "failed", "error": str(error)}

    def _normalize_job_payload(self, raw_job: dict, request_context: dict, run_id: str, raw_job_id: str) -> dict:
        title = self._require_text(raw_job.get("title"), "title")
        company_name = self._require_text(
            raw_job.get("company_name") or raw_job.get("company"),
            "company",
        )
        description = self._clean_multiline_text(
            raw_job.get("description") or raw_job.get("description_summary") or ""
        )
        locations = self._normalize_locations(raw_job.get("locations") or raw_job.get("location"))
        work_arrangement = self._normalize_work_arrangement(raw_job.get("work_arrangement"), locations)
        posted_at = self._parse_datetime(raw_job.get("posted_at") or raw_job.get("posted_date"))
        salary_text = self._clean_text(raw_job.get("salary_text") or raw_job.get("salary")) or None
        salary = self._parse_salary(salary_text)
        source = raw_job.get("source") or request_context.get("source_label") or request_context.get("connector_type")
        source_url = raw_job.get("source_url") or request_context.get("source_url")
        apply_url = raw_job.get("apply_url") or raw_job.get("job_url") or raw_job.get("url") or source_url
        role_name = self._normalize_role_name(raw_job.get("role_name") or title)
        role_key_value = role_key(role_name)
        industries = self._normalize_industries(raw_job.get("industries"))
        job_type = self._normalize_job_type(raw_job.get("job_type"))
        company_size = self._normalize_company_size(raw_job.get("company_size"))
        company_type = self._normalize_company_type(raw_job.get("company_type"))
        seniority = self._normalize_seniority(raw_job.get("seniority_level"), title)
        normalized_skills = self._normalize_skills(raw_job.get("skills"))
        core_skills = self._normalize_skills(raw_job.get("required_skills"))
        preferred_skills = self._normalize_skills(raw_job.get("preferred_skills"))
        all_skills = self._merge_unique(normalized_skills, core_skills, preferred_skills)
        if not description and not all_skills:
            raise ValidationError("Job description or skills are required to normalize a posting.")

        deduplication_key = self._build_deduplication_key(
            title=title,
            company_name=company_name,
            locations=locations,
            work_arrangement=work_arrangement,
            seniority=seniority,
        )

        return {
            "external_id": raw_job.get("external_id") or raw_job.get("source_job_id"),
            "title": title,
            "role_key": role_key_value,
            "role_name": role_name,
            "company_name": company_name,
            "company_size": company_size,
            "company_type": company_type,
            "description": description or None,
            "description_summary": self._summarize_description(description),
            "locations": locations,
            "work_arrangement": work_arrangement,
            "job_type": job_type,
            "industries": industries,
            "seniority_level": seniority,
            "posted_at": posted_at,
            "years_experience_min": raw_job.get("years_experience_min"),
            "years_experience_max": raw_job.get("years_experience_max"),
            "salary_text": salary_text,
            "salary_min": salary.get("min"),
            "salary_max": salary.get("max"),
            "salary_currency": salary.get("currency"),
            "salary_period": salary.get("period"),
            "normalized_skills": all_skills,
            "core_skills": core_skills,
            "preferred_skills": preferred_skills,
            "source": source,
            "source_url": source_url,
            "apply_url": apply_url,
            "deduplication_key": deduplication_key,
            "source_count": 1,
            "last_ingested_at": utcnow(),
            "metadata_json": {
                "source_connector": request_context.get("connector_type"),
                "source_labels": [source] if source else [],
                "source_urls": [source_url] if source_url else [],
                "apply_urls": [apply_url] if apply_url else [],
                "ingestion_run_ids": [run_id],
                "raw_job_ids": [raw_job_id],
                "description_hash": self._hash_text(description),
                "source_hostname": self._hostname(source_url or apply_url),
            },
        }

    def _find_duplicate(self, normalized_payload: dict):
        direct_match = self.repository.find_job_by_deduplication_key(
            normalized_payload.get("deduplication_key")
        )
        if direct_match:
            return direct_match

        candidates = self.repository.find_similar_job_candidates(
            normalized_payload["company_name"], normalized_payload["role_key"]
        )
        for candidate in candidates:
            similarity = self._similarity_score(candidate, normalized_payload)
            if similarity >= 0.78:
                return candidate
        return None

    def _similarity_score(self, candidate, incoming: dict) -> float:
        title_score = self._jaccard(
            self._tokenize(candidate.title),
            self._tokenize(incoming["title"]),
        )
        skill_score = self._jaccard(
            set(candidate.normalized_skills or []),
            set(incoming.get("normalized_skills") or []),
        )
        location_score = self._jaccard(
            set(candidate.locations or []),
            set(incoming.get("locations") or []),
        )
        return round((0.5 * title_score) + (0.35 * skill_score) + (0.15 * location_score), 4)

    def _build_linkedin_tinyfish_payload(self, request_payload: dict) -> dict:
        browser_profile = request_payload.get(
            "browser_profile",
            current_app.config["TINYFISH_DEFAULT_BROWSER_PROFILE"],
        )
        payload = {
            "url": request_payload["linkedin_url"],
            "goal": request_payload.get("goal_override")
            or self._build_linkedin_goal(request_payload["target_role"], request_payload["max_jobs"]),
            "browser_profile": browser_profile,
        }
        if request_payload.get(
            "proxy_enabled",
            current_app.config["TINYFISH_DEFAULT_PROXY_ENABLED"],
        ):
            payload["proxy_config"] = {
                "enabled": True,
                "country_code": request_payload.get(
                    "proxy_country_code",
                    current_app.config["TINYFISH_DEFAULT_PROXY_COUNTRY_CODE"],
                ),
            }
        return payload

    def _build_linkedin_goal(self, target_role: str, max_jobs: int) -> str:
        return (
            f"Open the LinkedIn jobs page and extract up to {max_jobs} job postings relevant to '{target_role}'. "
            "Return JSON only with this schema: { jobs: [ { title, company_name, description, location, work_arrangement, posted_at, salary_text, apply_url, job_url, job_type, seniority_level, skills, required_skills, preferred_skills } ] }. "
            "Use arrays for every skill field, keep the job posting URL when available, and exclude duplicates or sponsored non-job cards."
        )

    def _wait_for_tinyfish_run(
        self,
        client: TinyFishClient,
        provider_run_id: str,
        timeout_seconds: int,
        poll_interval_seconds: int,
    ) -> dict:
        deadline = monotonic() + timeout_seconds
        latest_run = {"status": "QUEUED", "run_id": provider_run_id}

        while monotonic() < deadline:
            latest_run = client.get_run(provider_run_id)
            status = str(latest_run.get("status") or "UNKNOWN").upper()
            if status == "COMPLETED":
                return latest_run
            if status in TINYFISH_TERMINAL_FAILURES:
                raise AppError(
                    "TinyFish LinkedIn ingestion failed.",
                    status_code=502,
                    payload={
                        "provider_run_id": provider_run_id,
                        "tinyfish": latest_run,
                    },
                )
            remaining = deadline - monotonic()
            if remaining <= 0:
                break
            sleep(min(poll_interval_seconds, max(0.5, remaining)))

        return latest_run

    def _extract_jobs_from_tinyfish(self, payload, request_payload: dict) -> list[dict]:
        parsed_payload = self._maybe_parse_json(payload)
        jobs = []
        if isinstance(parsed_payload, list):
            jobs = [item for item in parsed_payload if isinstance(item, dict)]
        elif isinstance(parsed_payload, dict):
            jobs = self._extract_job_array(parsed_payload)

        normalized_jobs = []
        for item in jobs:
            normalized = self._normalize_tinyfish_job(item, request_payload)
            if normalized:
                normalized_jobs.append(normalized)
        return normalized_jobs[: request_payload["max_jobs"]]

    def _extract_job_array(self, payload: dict) -> list[dict]:
        for key in ("jobs", "postings", "results", "job_postings"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        for key in ("result", "output", "data"):
            nested = payload.get(key)
            parsed_nested = self._maybe_parse_json(nested)
            if isinstance(parsed_nested, list):
                return [item for item in parsed_nested if isinstance(item, dict)]
            if isinstance(parsed_nested, dict):
                nested_jobs = self._extract_job_array(parsed_nested)
                if nested_jobs:
                    return nested_jobs
        return []

    def _normalize_tinyfish_job(self, job: dict, request_payload: dict) -> dict | None:
        title = self._pick_first(job, "title", "job_title", "position", "role")
        company = self._pick_first(job, "company_name", "company", "employer", "organization")
        if not self._clean_text(title) or not self._clean_text(company):
            return None

        description = self._pick_first(job, "description", "job_description", "summary")
        apply_url = self._pick_first(job, "apply_url", "job_url", "url", "link", "linkedin_url")
        normalized = {
            "source_job_id": self._pick_first(job, "source_job_id", "job_id", "external_id", "id"),
            "external_id": self._pick_first(job, "external_id", "job_id", "id"),
            "title": title,
            "company_name": company,
            "description": description,
            "description_summary": self._pick_first(job, "description_summary", "summary") or description,
            "location": self._pick_first(job, "location", "job_location"),
            "locations": self._coerce_list(job.get("locations")),
            "work_arrangement": self._pick_first(job, "work_arrangement", "work_mode", "remote_type", "workplace_type"),
            "posted_at": self._pick_first(job, "posted_at", "posted_date", "date_posted", "listed_at"),
            "salary_text": self._pick_first(job, "salary_text", "salary", "compensation"),
            "source": "LinkedIn",
            "source_url": request_payload["linkedin_url"],
            "apply_url": apply_url,
            "url": apply_url,
            "job_url": apply_url,
            "role_name": request_payload["target_role"],
            "job_type": self._pick_first(job, "job_type", "employment_type"),
            "industries": self._coerce_list(job.get("industries")),
            "company_size": self._pick_first(job, "company_size"),
            "company_type": self._pick_first(job, "company_type"),
            "seniority_level": self._pick_first(job, "seniority_level", "seniority"),
            "skills": self._coerce_list(job.get("skills")),
            "required_skills": self._coerce_list(job.get("required_skills")),
            "preferred_skills": self._coerce_list(job.get("preferred_skills")),
        }
        if not normalized["description"] and not any(
            normalized[key] for key in ("skills", "required_skills", "preferred_skills")
        ):
            return None
        return normalized

    def _pick_first(self, payload: dict, *keys: str):
        for key in keys:
            value = payload.get(key)
            if value is None:
                continue
            if isinstance(value, str):
                cleaned = self._clean_text(value)
                if cleaned:
                    return cleaned
            elif value:
                return value
        return None

    def _coerce_list(self, value) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            items = value
        elif isinstance(value, str):
            separators = ["\n", ";", ",", "|"]
            items = [value]
            for separator in separators:
                if separator in value:
                    items = value.split(separator)
                    break
        else:
            items = [value]

        normalized = []
        seen = set()
        for item in items:
            cleaned = self._clean_text(item)
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(cleaned)
        return normalized

    def _maybe_parse_json(self, payload):
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                return payload
        return payload

    def _normalize_locations(self, value) -> list[str]:
        items = self._as_list(value)
        if not items:
            return ["Remote"]

        normalized = []
        seen = set()
        for item in items:
            for part in str(item).split(","):
                cleaned = self._clean_text(part)
                if not cleaned:
                    continue
                canonical = LOCATION_MAP.get(cleaned.lower(), cleaned.title())
                key = canonical.lower()
                if key in seen:
                    continue
                seen.add(key)
                normalized.append(canonical)
        return normalized or ["Remote"]

    def _normalize_work_arrangement(self, value, locations: list[str]) -> str:
        cleaned = self._clean_text(value).lower()
        if cleaned:
            return WORK_ARRANGEMENT_MAP.get(cleaned, cleaned.replace(" ", "_"))
        if any(location.lower() == "remote" for location in locations):
            return "remote"
        return "hybrid"

    def _normalize_job_type(self, value) -> str:
        cleaned = self._clean_text(value).lower()
        if not cleaned:
            return "full_time"
        return JOB_TYPE_MAP.get(cleaned, cleaned.replace("-", "_").replace(" ", "_"))

    def _normalize_industries(self, value) -> list[str]:
        normalized = []
        seen = set()
        for item in self._as_list(value):
            cleaned = self._clean_text(item).lower()
            if not cleaned:
                continue
            canonical = INDUSTRY_MAP.get(cleaned, cleaned.replace("-", "_").replace(" ", "_"))
            if canonical in seen:
                continue
            seen.add(canonical)
            normalized.append(canonical)
        return normalized

    def _normalize_company_size(self, value) -> str | None:
        cleaned = self._clean_text(value).lower()
        if not cleaned:
            return None
        return COMPANY_SIZE_MAP.get(cleaned, cleaned.replace("-", "_").replace(" ", "_"))

    def _normalize_company_type(self, value) -> str | None:
        cleaned = self._clean_text(value).lower()
        if not cleaned:
            return None
        return COMPANY_TYPE_MAP.get(cleaned, cleaned.replace("-", "_").replace(" ", "_"))

    def _normalize_seniority(self, explicit_value, title: str) -> str:
        cleaned = self._clean_text(explicit_value).lower()
        if cleaned:
            return SENIORITY_KEYWORDS.get(cleaned, cleaned.replace(" ", "_"))
        title_lower = title.lower()
        for token, canonical in SENIORITY_KEYWORDS.items():
            if token in title_lower:
                return canonical
        return "mid"

    def _normalize_role_name(self, value: str) -> str:
        cleaned = self._clean_text(value)
        return " ".join(part.capitalize() for part in cleaned.split())

    def _normalize_skills(self, value) -> list[str]:
        skills = []
        seen = set()
        for item in self._as_list(value):
            if isinstance(item, str):
                pieces = [part.strip() for part in item.split(",") if part.strip()]
            else:
                pieces = [str(item).strip()]
            for piece in pieces:
                skill = self.repository.get_or_create_skill(piece)
                key = skill.canonical_name.lower()
                if key in seen:
                    continue
                seen.add(key)
                skills.append(skill.canonical_name)
        return skills

    def _parse_salary(self, salary_text: str | None) -> dict:
        if not salary_text:
            return {"min": None, "max": None, "currency": None, "period": None}

        text = salary_text.lower()
        currency = None
        for hint, canonical in CURRENCY_HINTS.items():
            if hint in text:
                currency = canonical
                break

        period = None
        for hint, canonical in PERIOD_MAP.items():
            if hint in text:
                period = canonical
                break

        matches = re.findall(r"(\d[\d,]*\.?\d*)\s*([kK]?)", salary_text)
        amounts = []
        for number_text, suffix in matches:
            value = float(number_text.replace(",", ""))
            if suffix:
                value *= 1000
            amounts.append(value)
        if not amounts:
            return {"min": None, "max": None, "currency": currency, "period": period}
        if len(amounts) == 1:
            return {"min": amounts[0], "max": amounts[0], "currency": currency, "period": period}
        return {
            "min": min(amounts[:2]),
            "max": max(amounts[:2]),
            "currency": currency,
            "period": period,
        }

    def _parse_datetime(self, value):
        cleaned = self._clean_text(value)
        if not cleaned:
            return None
        normalized = cleaned.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    parsed = datetime.strptime(cleaned, fmt)
                    break
                except ValueError:
                    parsed = None
            if parsed is None:
                return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _build_deduplication_key(
        self,
        title: str,
        company_name: str,
        locations: list[str],
        work_arrangement: str,
        seniority: str,
    ) -> str:
        base = "|".join(
            [
                self._slug(title),
                self._slug(company_name),
                self._slug(locations[0] if locations else "remote"),
                self._slug(work_arrangement),
                self._slug(seniority),
            ]
        )
        return hashlib.sha1(base.encode("utf-8")).hexdigest()

    def _summarize_description(self, description: str) -> str | None:
        cleaned = self._clean_multiline_text(description)
        if not cleaned:
            return None
        return cleaned[:280]

    def _hash_text(self, value: str) -> str | None:
        cleaned = self._clean_multiline_text(value)
        if not cleaned:
            return None
        return hashlib.sha1(cleaned.encode("utf-8")).hexdigest()

    def _hostname(self, url: str | None) -> str | None:
        if not url:
            return None
        parsed = urlparse(url)
        return parsed.netloc or None

    def _tokenize(self, value: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if token}

    def _jaccard(self, left, right) -> float:
        left_set = set(left or [])
        right_set = set(right or [])
        if not left_set and not right_set:
            return 1.0
        if not left_set or not right_set:
            return 0.0
        return len(left_set & right_set) / len(left_set | right_set)

    def _merge_unique(self, *collections) -> list[str]:
        merged = []
        seen = set()
        for collection in collections:
            for item in collection or []:
                key = str(item).strip().lower()
                if not key or key in seen:
                    continue
                seen.add(key)
                merged.append(str(item).strip())
        return merged

    def _require_text(self, value, field_name: str) -> str:
        cleaned = self._clean_text(value)
        if not cleaned:
            raise ValidationError(f"{field_name} is required for job normalization.")
        return cleaned

    def _as_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _clean_text(self, value) -> str:
        if value is None:
            return ""
        return " ".join(str(value).strip().split())

    def _clean_multiline_text(self, value) -> str:
        if value is None:
            return ""
        return "\n".join(line.strip() for line in str(value).splitlines() if line.strip()).strip()

    def _slug(self, value: str) -> str:
        return "-".join(re.findall(r"[a-z0-9]+", str(value).lower()))
