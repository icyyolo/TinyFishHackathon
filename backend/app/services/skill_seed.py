from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.extensions import db
from app.models import NormalizedSkill, RoleSkillMapping, RoleSkillTrend, SkillSynonym
from app.repositories.skill_radar_repository import role_key


SKILL_CATALOG = [
    {"canonical_name": "Python", "category": "programming_language", "aliases": ["python3", "py"], "is_emerging": False},
    {"canonical_name": "Flask", "category": "framework", "aliases": ["flask framework"], "is_emerging": False},
    {"canonical_name": "FastAPI", "category": "framework", "aliases": ["fast api"], "is_emerging": False},
    {"canonical_name": "SQL", "category": "database", "aliases": ["structured query language"], "is_emerging": False},
    {"canonical_name": "PostgreSQL", "category": "database", "aliases": ["postgres", "postgresql db"], "is_emerging": False},
    {"canonical_name": "Docker", "category": "devops", "aliases": ["containerization"], "is_emerging": False},
    {"canonical_name": "Kubernetes", "category": "devops", "aliases": ["k8s"], "is_emerging": False},
    {"canonical_name": "AWS", "category": "cloud", "aliases": ["amazon web services"], "is_emerging": False},
    {"canonical_name": "REST APIs", "category": "api", "aliases": ["rest api", "restful api"], "is_emerging": False},
    {"canonical_name": "GraphQL", "category": "api", "aliases": ["graphql api"], "is_emerging": False},
    {"canonical_name": "System Design", "category": "architecture", "aliases": ["distributed systems", "system architecture"], "is_emerging": False},
    {"canonical_name": "CI/CD", "category": "devops", "aliases": ["ci cd", "continuous integration", "continuous delivery"], "is_emerging": False},
    {"canonical_name": "Data Modeling", "category": "data", "aliases": ["data model design"], "is_emerging": False},
    {"canonical_name": "Pandas", "category": "analytics", "aliases": ["pandas library"], "is_emerging": False},
    {"canonical_name": "Tableau", "category": "analytics", "aliases": ["tableau dashboards"], "is_emerging": False},
    {"canonical_name": "Machine Learning", "category": "ai", "aliases": ["ml"], "is_emerging": False},
    {"canonical_name": "Experiment Design", "category": "analytics", "aliases": ["a b testing", "ab testing"], "is_emerging": False},
    {"canonical_name": "Prompt Engineering", "category": "ai", "aliases": ["prompt design"], "is_emerging": True},
    {"canonical_name": "AI Orchestration", "category": "ai", "aliases": ["agent orchestration", "llm orchestration"], "is_emerging": True},
    {"canonical_name": "Communication", "category": "soft_skill", "aliases": ["stakeholder communication"], "is_emerging": False},
]

ROLE_MAPPINGS = {
    "Backend Engineer": [
        {"skill": "Python", "importance": 0.96, "frequency": 0.88, "is_core": True, "postings": 1200, "trend_delta": 0.04},
        {"skill": "Flask", "importance": 0.68, "frequency": 0.39, "is_core": False, "postings": 450, "trend_delta": 0.03},
        {"skill": "FastAPI", "importance": 0.61, "frequency": 0.34, "is_core": False, "postings": 390, "trend_delta": 0.08},
        {"skill": "SQL", "importance": 0.90, "frequency": 0.84, "is_core": True, "postings": 1100, "trend_delta": 0.01},
        {"skill": "PostgreSQL", "importance": 0.78, "frequency": 0.70, "is_core": True, "postings": 870, "trend_delta": 0.02},
        {"skill": "REST APIs", "importance": 0.89, "frequency": 0.82, "is_core": True, "postings": 1120, "trend_delta": 0.01},
        {"skill": "Docker", "importance": 0.73, "frequency": 0.66, "is_core": True, "postings": 760, "trend_delta": 0.02},
        {"skill": "AWS", "importance": 0.76, "frequency": 0.63, "is_core": True, "postings": 810, "trend_delta": 0.02},
        {"skill": "System Design", "importance": 0.81, "frequency": 0.58, "is_core": True, "postings": 690, "trend_delta": 0.03},
        {"skill": "CI/CD", "importance": 0.64, "frequency": 0.50, "is_core": False, "postings": 610, "trend_delta": 0.02},
        {"skill": "Kubernetes", "importance": 0.56, "frequency": 0.42, "is_core": False, "postings": 520, "trend_delta": 0.05},
        {"skill": "GraphQL", "importance": 0.38, "frequency": 0.24, "is_core": False, "postings": 240, "trend_delta": 0.03},
        {"skill": "AI Orchestration", "importance": 0.33, "frequency": 0.16, "is_core": False, "postings": 160, "trend_delta": 0.12},
        {"skill": "Prompt Engineering", "importance": 0.27, "frequency": 0.12, "is_core": False, "postings": 110, "trend_delta": 0.11},
    ],
    "Data Analyst": [
        {"skill": "SQL", "importance": 0.95, "frequency": 0.90, "is_core": True, "postings": 980, "trend_delta": 0.01},
        {"skill": "Python", "importance": 0.82, "frequency": 0.72, "is_core": True, "postings": 880, "trend_delta": 0.02},
        {"skill": "Pandas", "importance": 0.78, "frequency": 0.68, "is_core": True, "postings": 710, "trend_delta": 0.03},
        {"skill": "Tableau", "importance": 0.71, "frequency": 0.61, "is_core": True, "postings": 690, "trend_delta": -0.01},
        {"skill": "Data Modeling", "importance": 0.60, "frequency": 0.44, "is_core": False, "postings": 450, "trend_delta": 0.02},
        {"skill": "Experiment Design", "importance": 0.58, "frequency": 0.38, "is_core": False, "postings": 340, "trend_delta": 0.04},
        {"skill": "Machine Learning", "importance": 0.44, "frequency": 0.26, "is_core": False, "postings": 280, "trend_delta": 0.05},
        {"skill": "Prompt Engineering", "importance": 0.25, "frequency": 0.10, "is_core": False, "postings": 120, "trend_delta": 0.10},
    ],
    "Product Manager": [
        {"skill": "Communication", "importance": 0.94, "frequency": 0.86, "is_core": True, "postings": 1030, "trend_delta": 0.00},
        {"skill": "Experiment Design", "importance": 0.72, "frequency": 0.46, "is_core": True, "postings": 420, "trend_delta": 0.04},
        {"skill": "SQL", "importance": 0.52, "frequency": 0.34, "is_core": False, "postings": 300, "trend_delta": 0.02},
        {"skill": "Data Modeling", "importance": 0.36, "frequency": 0.20, "is_core": False, "postings": 180, "trend_delta": 0.01},
        {"skill": "Prompt Engineering", "importance": 0.31, "frequency": 0.18, "is_core": False, "postings": 150, "trend_delta": 0.09},
        {"skill": "AI Orchestration", "importance": 0.28, "frequency": 0.12, "is_core": False, "postings": 100, "trend_delta": 0.11},
    ],
}


def seed_skill_catalog() -> None:
    existing = db.session.scalar(select(RoleSkillMapping.id).limit(1))
    if existing:
        return

    skill_map = {}
    for item in SKILL_CATALOG:
        skill = NormalizedSkill(
            canonical_name=item["canonical_name"],
            category=item["category"],
            aliases=item["aliases"],
            is_emerging=item["is_emerging"],
        )
        db.session.add(skill)
        db.session.flush()
        skill_map[item["canonical_name"]] = skill

        all_aliases = [item["canonical_name"], *(item.get("aliases") or [])]
        for alias in all_aliases:
            synonym = SkillSynonym(normalized_skill_id=skill.id, synonym=alias.lower(), confidence=1.0)
            db.session.add(synonym)

    now = datetime.now(timezone.utc)
    snapshot_offsets = [90, 60, 30, 0]
    snapshot_weights = [0.25, 0.5, 0.75, 1.0]

    for role_name, mappings in ROLE_MAPPINGS.items():
        for item in mappings:
            skill = skill_map[item["skill"]]
            mapping = RoleSkillMapping(
                target_role_key=role_key(role_name),
                target_role_name=role_name,
                normalized_skill_id=skill.id,
                importance_score=item["importance"],
                skill_frequency=item["frequency"],
                is_core=item["is_core"],
                source_job_postings=item["postings"],
                aggregation_metadata={
                    "aggregation_source": "starter_seed",
                    "role_job_postings": item["postings"],
                },
            )
            db.session.add(mapping)

            for offset, weight in zip(snapshot_offsets, snapshot_weights):
                frequency = max(0.01, min(0.99, item["frequency"] - (item["trend_delta"] * (1 - weight))))
                trend = RoleSkillTrend(
                    target_role_key=role_key(role_name),
                    target_role_name=role_name,
                    normalized_skill_id=skill.id,
                    snapshot_date=now - timedelta(days=offset),
                    skill_frequency=round(frequency, 4),
                    importance_score=item["importance"],
                    job_posting_count=max(1, int(item["postings"] * (0.85 + (weight * 0.15)))),
                )
                db.session.add(trend)

    db.session.commit()
