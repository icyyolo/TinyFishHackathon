import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.errors import NotFoundError, ValidationError
from app.extensions import db
from app.models import (
    NormalizedSkill,
    RoleSkillMapping,
    RoleSkillTrend,
    SkillSynonym,
    TinyFishIngestionRun,
)
from app.repositories.skill_radar_repository import role_key


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TinyFishIngestionRepository:
    def get_run(self, provider_run_id: str):
        run = db.session.scalar(
            select(TinyFishIngestionRun).where(
                TinyFishIngestionRun.provider_run_id == provider_run_id
            )
        )
        if not run:
            raise NotFoundError("TinyFish ingestion run not found.")
        return run.to_dict()

    def create_run(
        self,
        provider_run_id: str,
        target_role_name: str,
        source_url: str,
        request_payload: dict,
        status: str,
    ):
        run = TinyFishIngestionRun(
            provider_run_id=provider_run_id,
            target_role_key=role_key(target_role_name),
            target_role_name=target_role_name,
            source_url=source_url,
            status=status,
            request_payload=request_payload,
        )
        db.session.add(run)
        db.session.commit()
        return run.to_dict()

    def update_run(self, provider_run_id: str, **fields):
        run = db.session.scalar(
            select(TinyFishIngestionRun).where(
                TinyFishIngestionRun.provider_run_id == provider_run_id
            )
        )
        if not run:
            raise NotFoundError("TinyFish ingestion run not found.")
        for key, value in fields.items():
            setattr(run, key, value)
        db.session.commit()
        return run.to_dict()

    def ingest_role_skills_from_jobs(self, provider_run_id: str, result_payload: dict):
        run = db.session.scalar(
            select(TinyFishIngestionRun).where(
                TinyFishIngestionRun.provider_run_id == provider_run_id
            )
        )
        if not run:
            raise NotFoundError("TinyFish ingestion run not found.")

        jobs = self._extract_jobs(result_payload)
        if not jobs:
            raise ValidationError("TinyFish run did not return any job data to ingest.")

        skill_counts = {}
        total_jobs = len(jobs)
        total_skill_mentions = 0

        for job in jobs:
            raw_skills = self._extract_job_skills(job)
            normalized_names = set()
            for raw_skill in raw_skills:
                skill = self._get_or_create_normalized_skill(raw_skill)
                normalized_names.add(skill.canonical_name)
            for skill_name in normalized_names:
                skill_counts[skill_name] = skill_counts.get(skill_name, 0) + 1
            total_skill_mentions += len(normalized_names)

        if not skill_counts:
            raise ValidationError("TinyFish run completed, but no skills could be extracted from the result.")

        RoleSkillMapping.query.filter_by(target_role_key=run.target_role_key).delete()

        snapshot_time = utcnow()
        aggregated = []
        for skill_name, count in sorted(skill_counts.items(), key=lambda item: (-item[1], item[0])):
            skill = db.session.scalar(
                select(NormalizedSkill).where(NormalizedSkill.canonical_name == skill_name)
            )
            frequency = count / total_jobs
            importance = min(1.0, round((0.7 * frequency) + (0.3 * (count / max(total_skill_mentions, 1))), 4))
            is_core = frequency >= 0.55

            mapping = RoleSkillMapping(
                target_role_key=run.target_role_key,
                target_role_name=run.target_role_name,
                normalized_skill_id=skill.id,
                importance_score=importance,
                skill_frequency=round(frequency, 4),
                is_core=is_core,
                source_job_postings=total_jobs,
                aggregation_metadata={
                    "aggregation_source": "tinyfish",
                    "provider_run_id": provider_run_id,
                    "source_url": run.source_url,
                },
            )
            db.session.add(mapping)

            trend = RoleSkillTrend(
                target_role_key=run.target_role_key,
                target_role_name=run.target_role_name,
                normalized_skill_id=skill.id,
                snapshot_date=snapshot_time,
                skill_frequency=round(frequency, 4),
                importance_score=importance,
                job_posting_count=total_jobs,
            )
            db.session.add(trend)

            aggregated.append(
                {
                    "skill": skill_name,
                    "job_count": count,
                    "skill_frequency": round(frequency, 4),
                    "importance_score": importance,
                    "is_core": is_core,
                }
            )

        summary = {
            "provider_run_id": provider_run_id,
            "target_role": run.target_role_name,
            "jobs_ingested": total_jobs,
            "skills_aggregated": len(aggregated),
            "top_skills": aggregated[:10],
            "ingested_at": snapshot_time.isoformat(),
        }

        run.status = "INGESTED"
        run.tinyfish_response = result_payload
        run.ingestion_summary = summary
        run.ingested_at = snapshot_time
        db.session.commit()

        return summary

    def _extract_jobs(self, result_payload: dict) -> list[dict]:
        if isinstance(result_payload, dict):
            for key in ("jobs", "postings", "results", "job_postings"):
                value = result_payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return []

    def _extract_job_skills(self, job: dict) -> list[str]:
        values = []
        for key in ("skills", "required_skills", "preferred_skills"):
            field = job.get(key)
            if isinstance(field, list):
                values.extend([str(item).strip() for item in field if str(item).strip()])
            elif isinstance(field, str):
                values.extend([part.strip() for part in field.split(",") if part.strip()])
        return values

    def _get_or_create_normalized_skill(self, raw_skill: str):
        normalized_raw = self._normalize_text(raw_skill)
        synonym = db.session.scalar(
            select(SkillSynonym).where(SkillSynonym.synonym == normalized_raw)
        )
        if synonym:
            return db.session.get(NormalizedSkill, synonym.normalized_skill_id)

        skill = db.session.scalar(
            select(NormalizedSkill).where(
                NormalizedSkill.canonical_name == self._title_skill(raw_skill)
            )
        )
        if not skill:
            skill = NormalizedSkill(
                canonical_name=self._title_skill(raw_skill),
                category="unclassified",
                aliases=[raw_skill],
                is_emerging=False,
            )
            db.session.add(skill)
            db.session.flush()

        synonym = SkillSynonym(
            normalized_skill_id=skill.id,
            synonym=normalized_raw,
            confidence=0.8,
        )
        db.session.add(synonym)
        db.session.flush()
        return skill

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
