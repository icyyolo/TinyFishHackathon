from collections import defaultdict
from datetime import datetime, timezone

from app.errors import NotFoundError
from app.repositories import SkillRadarRepository
from app.repositories.skill_radar_repository import role_key
from app.utils.responses import serialize_document


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SkillRadarService:
    def __init__(self) -> None:
        self.repository = SkillRadarRepository()

    def fetch_skill_radar(self, user_id: str, target_role: str):
        user = self.repository.get_user(user_id)
        role_mappings = self.repository.get_role_skill_mappings(target_role)
        if not role_mappings:
            raise NotFoundError("No normalized skill mapping found for the selected target role.")

        user_skill_profile = self._build_user_skill_profile(user_id, user)
        trend_map = self._build_trend_movement_map(target_role)

        matched_skills = []
        missing_core_skills = []
        emerging_skills = []
        radar_axes = []
        core_count = 0
        matched_core_count = 0
        total_importance = 0.0
        matched_importance = 0.0

        for item in role_mappings:
            skill_meta = item["skill"]
            canonical_name = skill_meta["canonical_name"]
            user_skill = user_skill_profile.get(canonical_name.lower())
            trend_movement = trend_map.get(canonical_name.lower(), 0.0)
            total_importance += item["importance_score"]

            axis = {
                "skill": canonical_name,
                "category": skill_meta.get("category"),
                "role_importance": round(item["importance_score"], 4),
                "job_frequency": round(item["skill_frequency"], 4),
                "user_strength": round(user_skill["confidence"], 4) if user_skill else 0.0,
                "gap": round(max(item["importance_score"] - (user_skill["confidence"] if user_skill else 0.0), 0.0), 4),
                "is_core": item["is_core"],
                "trend_movement": round(trend_movement, 4),
            }
            radar_axes.append(axis)

            if item["is_core"]:
                core_count += 1

            if user_skill:
                matched_importance += item["importance_score"]
                if item["is_core"]:
                    matched_core_count += 1
                matched_skills.append(
                    {
                        "skill": canonical_name,
                        "category": skill_meta.get("category"),
                        "role_importance": round(item["importance_score"], 4),
                        "job_frequency": round(item["skill_frequency"], 4),
                        "confidence": round(user_skill["confidence"], 4),
                        "sources": user_skill["sources"],
                        "raw_matches": user_skill["raw_matches"],
                    }
                )
            elif item["is_core"]:
                missing_core_skills.append(
                    {
                        "skill": canonical_name,
                        "category": skill_meta.get("category"),
                        "role_importance": round(item["importance_score"], 4),
                        "job_frequency": round(item["skill_frequency"], 4),
                        "recommended_priority": "high" if item["importance_score"] >= 0.8 else "medium",
                    }
                )

            if skill_meta.get("is_emerging") or trend_movement >= 0.08:
                emerging_skills.append(
                    {
                        "skill": canonical_name,
                        "category": skill_meta.get("category"),
                        "trend_movement": round(trend_movement, 4),
                        "role_importance": round(item["importance_score"], 4),
                        "job_frequency": round(item["skill_frequency"], 4),
                        "has_skill": bool(user_skill),
                        "confidence": round(user_skill["confidence"], 4) if user_skill else 0.0,
                    }
                )

        core_coverage_pct = round((matched_core_count / core_count) * 100, 2) if core_count else 0.0
        weighted_match_score = round((matched_importance / total_importance) * 100, 2) if total_importance else 0.0

        return serialize_document(
            {
                "user_id": user_id,
                "target_role": role_mappings[0]["target_role_name"],
                "generated_at": utcnow_iso(),
                "algorithm": {
                    "summary": "Normalize user skills, match them against role-skill mappings, bucket gaps by core/emerging signals, and score coverage using role importance and extraction confidence.",
                    "steps": [
                        "Normalize user profile and resume-extracted skills using canonical skill names and synonym mappings.",
                        "Join normalized user skills against role-specific skill requirements and importance scores.",
                        "Classify matched skills, missing core skills, and emerging skills using role mapping and trend movement.",
                        "Calculate chart-friendly radar axes and summary coverage metrics for the frontend.",
                    ],
                },
                "matched_skills": matched_skills,
                "missing_core_skills": missing_core_skills,
                "emerging_skills": sorted(emerging_skills, key=lambda item: (-item["trend_movement"], -item["role_importance"])),
                "summary": {
                    "core_coverage_pct": core_coverage_pct,
                    "weighted_match_score": weighted_match_score,
                    "matched_count": len(matched_skills),
                    "missing_core_count": len(missing_core_skills),
                    "emerging_count": len(emerging_skills),
                },
                "chart": {
                    "radar_axes": radar_axes[:12],
                    "bucket_counts": {
                        "matched_skills": len(matched_skills),
                        "missing_core_skills": len(missing_core_skills),
                        "emerging_skills": len(emerging_skills),
                    },
                    "top_gaps": missing_core_skills[:6],
                },
            }
        )

    def fetch_trending_skills(self, target_role: str, window_days: int = 90, limit: int = 10):
        trend_rows = self.repository.get_role_skill_trends(target_role, window_days=window_days)
        if not trend_rows:
            raise NotFoundError("No trend data found for the selected target role.")

        grouped = defaultdict(list)
        target_role_name = trend_rows[0]["target_role_name"]
        for row in trend_rows:
            grouped[row["skill"]["canonical_name"].lower()].append(row)

        skills = []
        chart_series = []
        for rows in grouped.values():
            rows.sort(key=lambda item: item["snapshot_date"])
            first = rows[0]
            latest = rows[-1]
            first_frequency = first["skill_frequency"]
            latest_frequency = latest["skill_frequency"]
            movement = latest_frequency - first_frequency
            movement_pct = round((movement / first_frequency) * 100, 2) if first_frequency else None
            direction = "up" if movement > 0.02 else "down" if movement < -0.02 else "stable"

            skill_summary = {
                "skill": latest["skill"]["canonical_name"],
                "category": latest["skill"].get("category"),
                "is_emerging": latest["skill"].get("is_emerging", False),
                "latest_frequency": round(latest_frequency, 4),
                "previous_frequency": round(first_frequency, 4),
                "movement": round(movement, 4),
                "movement_pct": movement_pct,
                "direction": direction,
                "importance_score": round(latest["importance_score"], 4),
                "job_posting_count": latest["job_posting_count"],
                "series": [
                    {
                        "date": point["snapshot_date"],
                        "frequency": round(point["skill_frequency"], 4),
                        "importance_score": round(point["importance_score"], 4),
                    }
                    for point in rows
                ],
            }
            skills.append(skill_summary)
            chart_series.append(
                {
                    "skill": skill_summary["skill"],
                    "points": skill_summary["series"],
                }
            )

        skills.sort(key=lambda item: (-item["movement"], -item["importance_score"]))

        return serialize_document(
            {
                "target_role": target_role_name,
                "window_days": window_days,
                "generated_at": utcnow_iso(),
                "trend_calculation": {
                    "summary": "Trend movement compares the latest normalized skill frequency against the earliest frequency inside the selected time window.",
                    "formula": "movement = latest_frequency - earliest_frequency; movement_pct = movement / earliest_frequency",
                    "signals": [
                        "skill_frequency reflects how often a skill appears in aggregated job posting data for the role",
                        "importance_score reflects normalized role relevance",
                        "direction is up, stable, or down based on movement thresholds",
                    ],
                },
                "skills": skills[:limit],
                "chart": {
                    "series": chart_series[:limit],
                    "top_movers": skills[:limit],
                },
            }
        )

    def _build_user_skill_profile(self, user_id: str, user: dict):
        lookup = self.repository.get_skill_lookup()
        profile = user.get("onboarding_profile") or {}
        latest_session = self.repository.get_latest_session(user_id)
        aggregated = {}

        self._merge_skill_source(
            aggregated,
            profile.get("skills", {}).get("user_selected", []),
            source="manual_profile",
            confidence=1.0,
            lookup=lookup,
        )
        self._merge_skill_source(
            aggregated,
            profile.get("skills", {}).get("extracted", []),
            source="ai_profile",
            confidence=0.8,
            lookup=lookup,
        )
        self._merge_skill_source(
            aggregated,
            profile.get("resume_insights", {}).get("skills", []),
            source="ai_resume",
            confidence=0.75,
            lookup=lookup,
        )

        if latest_session:
            session_profile = latest_session.get("profile", {})
            self._merge_skill_source(
                aggregated,
                session_profile.get("skills", {}).get("user_selected", []),
                source="manual_session",
                confidence=1.0,
                lookup=lookup,
            )
            extracted_rows = self.repository.get_extracted_skills_for_session(latest_session["id"])
            for row in extracted_rows:
                self._merge_skill_source(
                    aggregated,
                    [row["skill"]],
                    source=row.get("source", "ai_resume"),
                    confidence=float(row.get("confidence", 0.75)),
                    lookup=lookup,
                )

        return aggregated

    def _merge_skill_source(self, aggregated: dict, skills: list[str], source: str, confidence: float, lookup: dict):
        for raw_skill in skills or []:
            normalized = self._normalize_skill(raw_skill, lookup)
            if not normalized:
                continue
            key = normalized["canonical_name"].lower()
            existing = aggregated.get(key)
            if not existing:
                aggregated[key] = {
                    "skill": normalized["canonical_name"],
                    "confidence": confidence,
                    "sources": [source],
                    "raw_matches": [raw_skill],
                    "category": normalized.get("category"),
                }
                continue
            existing["confidence"] = max(existing["confidence"], confidence)
            if source not in existing["sources"]:
                existing["sources"].append(source)
            if raw_skill not in existing["raw_matches"]:
                existing["raw_matches"].append(raw_skill)

    def _normalize_skill(self, value: str, lookup: dict):
        normalized = " ".join(str(value).strip().lower().replace("/", " ").replace("-", " ").split())
        return lookup.get(normalized)

    def _build_trend_movement_map(self, target_role: str):
        rows = self.repository.get_role_skill_trends(target_role, window_days=90)
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["skill"]["canonical_name"].lower()].append(row)
        movement_map = {}
        for skill, points in grouped.items():
            points.sort(key=lambda item: item["snapshot_date"])
            movement_map[skill] = points[-1]["skill_frequency"] - points[0]["skill_frequency"]
        return movement_map
