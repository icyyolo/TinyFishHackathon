from datetime import datetime, timezone
from typing import List, Optional, Union

from sqlalchemy import func, select

from app.errors import NotFoundError
from app.extensions import db
from app.models import JobIngestionRun, NormalizedJobPosting, NormalizedSkill, RawJobPosting, SkillSynonym


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def merge_unique_strings(existing, incoming) -> list[str]:
    merged = []
    seen = set()
    for value in list(existing or []) + list(incoming or []):
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(cleaned)
    return merged


class JobAggregationRepository:
    def create_run(
        self,
        connector_type: str,
        connector_name: str,
        source_label: str,
        source_url: Optional[str],
        request_payload: dict,
        requested_job_count: int,
    ) -> JobIngestionRun:
        run = JobIngestionRun(
            connector_type=connector_type,
            connector_name=connector_name,
            source_label=source_label,
            source_url=source_url,
            status="queued",
            request_payload=request_payload,
            requested_job_count=requested_job_count,
            metrics_json={},
        )
        db.session.add(run)
        db.session.commit()
        return run

    def mark_run_started(self, run_id: str, fetched_job_count: int) -> JobIngestionRun:
        run = self._get_run_model(run_id)
        run.status = "running"
        run.started_at = utcnow()
        run.fetched_job_count = fetched_job_count
        db.session.commit()
        return run

    def finalize_run(self, run_id: str, status: str, metrics_json: dict) -> dict:
        run = self._get_run_model(run_id)
        run.status = status
        run.parsed_job_count = metrics_json.get("parsed_jobs", 0)
        run.normalized_job_count = metrics_json.get("normalized_jobs", 0)
        run.deduplicated_job_count = metrics_json.get("deduplicated_jobs", 0)
        run.failed_job_count = metrics_json.get("failed_jobs", 0)
        run.metrics_json = metrics_json
        run.completed_at = utcnow()
        db.session.commit()
        return run.to_dict()

    def fail_run(self, run_id: str, error_message: str, metrics_json: Optional[dict] = None) -> dict:
        db.session.rollback()
        run = self._get_run_model(run_id)
        run.status = "failed"
        run.metrics_json = metrics_json or run.metrics_json
        run.error_summary = {"message": error_message}
        run.completed_at = utcnow()
        db.session.commit()
        return run.to_dict()

    def get_run(self, run_id: str) -> dict:
        return self._get_run_model(run_id).to_dict()

    def create_raw_job(
        self,
        run_id: str,
        source_connector: str,
        source_name: str,
        source_job_id: Optional[str],
        source_url: Optional[str],
        apply_url: Optional[str],
        raw_payload: dict,
    ) -> RawJobPosting:
        raw_job = RawJobPosting(
            ingestion_run_id=run_id,
            source_connector=source_connector,
            source_name=source_name,
            source_job_id=source_job_id,
            source_url=source_url,
            apply_url=apply_url,
            processing_status="queued",
            raw_payload=raw_payload,
            extracted_payload={},
        )
        db.session.add(raw_job)
        db.session.commit()
        return raw_job

    def update_raw_job(self, raw_job_id: str, **fields) -> dict:
        db.session.rollback()
        raw_job = self._get_raw_job_model(raw_job_id)
        for key, value in fields.items():
            setattr(raw_job, key, value)
        db.session.commit()
        return raw_job.to_dict()

    def get_retryable_raw_jobs(
        self,
        run_id: Optional[str] = None,
        raw_job_ids: Optional[List[str]] = None,
        limit: int = 25,
    ) -> list[RawJobPosting]:
        query = select(RawJobPosting).where(
            RawJobPosting.processing_status.in_(["failed_parsing", "failed_normalization"])
        )
        if run_id:
            query = query.where(RawJobPosting.ingestion_run_id == run_id)
        if raw_job_ids:
            query = query.where(RawJobPosting.id.in_(raw_job_ids))
        query = query.order_by(RawJobPosting.updated_at.desc()).limit(limit)
        return list(db.session.scalars(query).all())

    def find_job_by_deduplication_key(self, deduplication_key: Optional[str]) -> Optional[NormalizedJobPosting]:
        if not deduplication_key:
            return None
        return db.session.scalar(
            select(NormalizedJobPosting).where(NormalizedJobPosting.deduplication_key == deduplication_key)
        )

    def find_similar_job_candidates(self, company_name: str, role_key: str) -> list[NormalizedJobPosting]:
        return list(
            db.session.scalars(
                select(NormalizedJobPosting)
                .where(func.lower(NormalizedJobPosting.company_name) == company_name.lower())
                .where(NormalizedJobPosting.role_key == role_key)
                .order_by(NormalizedJobPosting.updated_at.desc())
                .limit(10)
            ).all()
        )

    def create_normalized_job(self, payload: dict) -> NormalizedJobPosting:
        job = NormalizedJobPosting(**payload)
        db.session.add(job)
        db.session.commit()
        return job

    def merge_into_normalized_job(
        self,
        job: NormalizedJobPosting,
        payload: dict,
        raw_job_id: str,
        run_id: str,
    ) -> NormalizedJobPosting:
        job.description = self._prefer_longer_text(job.description, payload.get("description"))
        job.description_summary = self._prefer_longer_text(
            job.description_summary, payload.get("description_summary")
        )
        job.locations = merge_unique_strings(job.locations, payload.get("locations"))
        job.industries = merge_unique_strings(job.industries, payload.get("industries"))
        job.normalized_skills = merge_unique_strings(
            job.normalized_skills, payload.get("normalized_skills")
        )
        job.core_skills = merge_unique_strings(job.core_skills, payload.get("core_skills"))
        job.preferred_skills = merge_unique_strings(
            job.preferred_skills, payload.get("preferred_skills")
        )
        job.salary_text = self._prefer_longer_text(job.salary_text, payload.get("salary_text"))
        job.salary_min = job.salary_min if job.salary_min is not None else payload.get("salary_min")
        job.salary_max = job.salary_max if job.salary_max is not None else payload.get("salary_max")
        job.salary_currency = job.salary_currency or payload.get("salary_currency")
        job.salary_period = job.salary_period or payload.get("salary_period")
        job.company_size = job.company_size or payload.get("company_size")
        job.company_type = job.company_type or payload.get("company_type")
        job.job_type = job.job_type or payload.get("job_type")
        job.work_arrangement = job.work_arrangement or payload.get("work_arrangement")
        job.seniority_level = job.seniority_level or payload.get("seniority_level")
        job.posted_at = self._newest_datetime(job.posted_at, payload.get("posted_at"))
        job.source = job.source or payload.get("source")
        job.source_url = job.source_url or payload.get("source_url")
        job.apply_url = job.apply_url or payload.get("apply_url")
        job.source_count = max(1, (job.source_count or 1) + 1)
        job.last_ingested_at = payload.get("last_ingested_at") or utcnow()

        metadata = dict(job.metadata_json or {})
        incoming = payload.get("metadata_json") or {}
        metadata["source_labels"] = merge_unique_strings(
            metadata.get("source_labels"), incoming.get("source_labels")
        )
        metadata["source_urls"] = merge_unique_strings(
            metadata.get("source_urls"), incoming.get("source_urls")
        )
        metadata["apply_urls"] = merge_unique_strings(
            metadata.get("apply_urls"), incoming.get("apply_urls")
        )
        metadata["ingestion_run_ids"] = merge_unique_strings(
            metadata.get("ingestion_run_ids"), [run_id]
        )
        metadata["raw_job_ids"] = merge_unique_strings(metadata.get("raw_job_ids"), [raw_job_id])
        job.metadata_json = metadata

        db.session.commit()
        return job

    def list_ingested_jobs(
        self,
        limit: int,
        offset: int,
        source: Optional[str] = None,
        role: Optional[str] = None,
    ) -> dict:
        base_query = select(NormalizedJobPosting)
        if source:
            base_query = base_query.where(func.lower(NormalizedJobPosting.source) == source.lower())
        if role:
            base_query = base_query.where(func.lower(NormalizedJobPosting.role_name) == role.lower())

        total = db.session.scalar(select(func.count()).select_from(base_query.subquery())) or 0
        jobs = list(
            db.session.scalars(
                base_query.order_by(NormalizedJobPosting.updated_at.desc()).offset(offset).limit(limit)
            ).all()
        )

        raw_counts = {}
        if jobs:
            job_ids = [job.id for job in jobs]
            count_rows = db.session.execute(
                select(RawJobPosting.normalized_job_id, func.count(RawJobPosting.id))
                .where(RawJobPosting.normalized_job_id.in_(job_ids))
                .group_by(RawJobPosting.normalized_job_id)
            ).all()
            raw_counts = {job_id: count for job_id, count in count_rows}

        items = []
        for job in jobs:
            payload = job.to_dict()
            payload["raw_job_count"] = raw_counts.get(job.id, 0)
            payload["dedupe_sources"] = len((job.metadata_json or {}).get("source_labels", []))
            items.append(payload)

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": items,
        }

    def fetch_metrics(self, connector_type: Optional[str] = None) -> dict:
        run_query = select(JobIngestionRun)
        if connector_type:
            run_query = run_query.where(JobIngestionRun.connector_type == connector_type)

        total_runs = db.session.scalar(select(func.count()).select_from(run_query.subquery())) or 0
        total_raw_jobs = db.session.scalar(select(func.count()).select_from(RawJobPosting)) or 0
        total_normalized_jobs = db.session.scalar(select(func.count()).select_from(NormalizedJobPosting)) or 0

        run_status_rows = db.session.execute(
            select(JobIngestionRun.status, func.count(JobIngestionRun.id)).group_by(JobIngestionRun.status)
        ).all()
        raw_status_rows = db.session.execute(
            select(RawJobPosting.processing_status, func.count(RawJobPosting.id)).group_by(
                RawJobPosting.processing_status
            )
        ).all()
        connector_rows = db.session.execute(
            select(JobIngestionRun.connector_type, func.count(JobIngestionRun.id)).group_by(
                JobIngestionRun.connector_type
            )
        ).all()

        recent_runs = [
            run.to_dict()
            for run in db.session.scalars(
                select(JobIngestionRun).order_by(JobIngestionRun.created_at.desc()).limit(5)
            ).all()
        ]

        parsed_jobs = sum(run.get("parsed_job_count", 0) for run in recent_runs)
        deduplicated_jobs = sum(run.get("deduplicated_job_count", 0) for run in recent_runs)
        duplicate_rate = round((deduplicated_jobs / parsed_jobs) * 100, 2) if parsed_jobs else 0.0

        return {
            "total_runs": total_runs,
            "total_raw_jobs": total_raw_jobs,
            "total_normalized_jobs": total_normalized_jobs,
            "duplicate_rate_pct": duplicate_rate,
            "run_status_counts": {status: count for status, count in run_status_rows},
            "raw_status_counts": {status: count for status, count in raw_status_rows},
            "connector_counts": {status: count for status, count in connector_rows},
            "recent_runs": recent_runs,
        }

    def get_or_create_skill(self, raw_skill: str) -> NormalizedSkill:
        normalized_raw = self._normalize_text(raw_skill)
        synonym = db.session.scalar(select(SkillSynonym).where(SkillSynonym.synonym == normalized_raw))
        if synonym:
            return db.session.get(NormalizedSkill, synonym.normalized_skill_id)

        canonical_name = self._title_skill(raw_skill)
        skill = db.session.scalar(
            select(NormalizedSkill).where(NormalizedSkill.canonical_name == canonical_name)
        )
        if not skill:
            skill = NormalizedSkill(
                canonical_name=canonical_name,
                category="unclassified",
                aliases=[raw_skill],
                is_emerging=False,
            )
            db.session.add(skill)
            db.session.flush()
        else:
            aliases = merge_unique_strings(skill.aliases, [raw_skill])
            skill.aliases = aliases

        existing_synonym = db.session.scalar(
            select(SkillSynonym).where(SkillSynonym.synonym == normalized_raw)
        )
        if not existing_synonym:
            db.session.add(
                SkillSynonym(
                    normalized_skill_id=skill.id,
                    synonym=normalized_raw,
                    confidence=0.8,
                )
            )
        db.session.commit()
        return skill

    def _get_run_model(self, run_id: str) -> JobIngestionRun:
        run = db.session.get(JobIngestionRun, run_id)
        if not run:
            raise NotFoundError("Job ingestion run not found.")
        return run

    def _get_raw_job_model(self, raw_job_id: str) -> RawJobPosting:
        raw_job = db.session.get(RawJobPosting, raw_job_id)
        if not raw_job:
            raise NotFoundError("Raw job posting not found.")
        return raw_job

    def _normalize_text(self, value: str) -> str:
        return " ".join(str(value).strip().lower().replace("/", " ").replace("-", " ").split())

    def _title_skill(self, value: str) -> str:
        parts = [part for part in str(value).strip().split() if part]
        titled = []
        for part in parts:
            if part.upper() in {"AI", "ML", "AWS", "SQL", "CI/CD", "API", "APIs"}:
                titled.append(part.upper())
            else:
                titled.append(part.capitalize())
        return " ".join(titled)

    def _prefer_longer_text(self, current: Optional[str], incoming: Optional[str]) -> Optional[str]:
        if not incoming:
            return current
        if not current:
            return incoming
        return incoming if len(incoming) > len(current) else current

    def _newest_datetime(self, current, incoming):
        if not incoming:
            return current
        if not current:
            return incoming
        return incoming if incoming > current else current
