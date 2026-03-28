from dataclasses import dataclass
from typing import Optional

from app.repositories import JobMatchingRepository
from app.services.preference_normalizer import PreferenceNormalizer
from app.utils.responses import serialize_document


SENIORITY_TARGETS = {
    "intern": 0.0,
    "junior": 1.5,
    "mid": 3.5,
    "senior": 6.0,
    "lead": 8.0,
    "principal": 10.0,
}


@dataclass
class FactorScore:
    name: str
    score: float
    weight: float
    reason: str
    active: bool = True


class JobMatchingService:
    DEFAULT_WEIGHTS = {
        "skill_match": 0.35,
        "preference_match": 0.20,
        "location_match": 0.10,
        "work_arrangement_match": 0.10,
        "seniority_fit": 0.15,
        "salary_fit": 0.10,
    }

    def __init__(self) -> None:
        self.repository = JobMatchingRepository()
        self.preference_normalizer = PreferenceNormalizer()

    def fetch_recommended_jobs(self, user_id: str, limit: int = 10):
        context = self._build_user_context(user_id)
        jobs = self.repository.list_jobs()
        scored = [self._score_job(context, job) for job in jobs]
        scored.sort(key=lambda item: (-item["match_score"], item["job"]["title"]))

        return serialize_document(
            {
                "user_id": user_id,
                "ranking_pipeline": {
                    "summary": "Normalize user and job data, compute modular factor scores, then rank by weighted match score.",
                    "steps": [
                        "Build user context from onboarding profile, latest session, extracted skills, and saved preferences.",
                        "Load normalized job postings and compare each one against user context.",
                        "Score skill match, preference match, location match, work arrangement match, seniority fit, and optional salary fit.",
                        "Reweight active factors and generate explainable summaries for ranked jobs.",
                    ],
                    "weights": self.DEFAULT_WEIGHTS,
                },
                "jobs": [self._compact_recommendation(item) for item in scored[:limit]],
            }
        )

    def fetch_job_match_detail(self, user_id: str, job_id: str):
        context = self._build_user_context(user_id)
        job = self.repository.get_job(job_id)
        return serialize_document(self._score_job(context, job))

    def _score_job(self, context: dict, job: dict):
        matched_skills, missing_skills, skill_score, skill_reason = self._score_skill_match(context, job)
        matched_preferences, preference_misses, preference_score, preference_reason = self._score_preference_match(context, job)
        location_score, location_reason = self._score_location_match(context, job)
        arrangement_score, arrangement_reason = self._score_work_arrangement_match(context, job)
        seniority_score, seniority_reason = self._score_seniority_fit(context, job)
        salary_score, salary_reason, salary_active = self._score_salary_fit(context, job)

        factor_scores = [
            FactorScore("skill_match", skill_score, self.DEFAULT_WEIGHTS["skill_match"], skill_reason),
            FactorScore("preference_match", preference_score, self.DEFAULT_WEIGHTS["preference_match"], preference_reason),
            FactorScore("location_match", location_score, self.DEFAULT_WEIGHTS["location_match"], location_reason),
            FactorScore("work_arrangement_match", arrangement_score, self.DEFAULT_WEIGHTS["work_arrangement_match"], arrangement_reason),
            FactorScore("seniority_fit", seniority_score, self.DEFAULT_WEIGHTS["seniority_fit"], seniority_reason),
            FactorScore("salary_fit", salary_score, self.DEFAULT_WEIGHTS["salary_fit"], salary_reason, active=salary_active),
        ]

        active_weights = sum(item.weight for item in factor_scores if item.active)
        weighted_total = sum(item.score * item.weight for item in factor_scores if item.active)
        match_score = round((weighted_total / active_weights) * 100, 2) if active_weights else 0.0

        lower_score_reasons = preference_misses + self._derive_lower_score_reasons(factor_scores, missing_skills)
        summary = self._build_summary(matched_skills, missing_skills, matched_preferences, lower_score_reasons, match_score)

        return {
            "job": job,
            "match_score": match_score,
            "explanation": {
                "summary": summary,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "matched_preferences": matched_preferences,
                "lower_score_reasons": self._dedupe(lower_score_reasons),
                "factor_scores": [
                    {
                        "factor": item.name,
                        "score": round(item.score, 4),
                        "weight": item.weight,
                        "active": item.active,
                        "reason": item.reason,
                    }
                    for item in factor_scores
                ],
            },
        }

    def _compact_recommendation(self, scored: dict):
        explanation = scored["explanation"]
        return {
            "job_id": scored["job"]["id"],
            "title": scored["job"]["title"],
            "company_name": scored["job"]["company_name"],
            "match_score": scored["match_score"],
            "locations": scored["job"]["locations"],
            "work_arrangement": scored["job"]["work_arrangement"],
            "seniority_level": scored["job"]["seniority_level"],
            "summary": explanation["summary"],
            "matched_skills": explanation["matched_skills"][:5],
            "missing_skills": explanation["missing_skills"][:5],
            "matched_preferences": explanation["matched_preferences"][:4],
        }

    def _build_user_context(self, user_id: str):
        user = self.repository.get_user(user_id)
        latest_session = self.repository.get_latest_session(user_id)
        preference_record = self.repository.get_user_preferences(user_id)
        skill_lookup = self.repository.get_skill_lookup()

        onboarding_profile = user.get("onboarding_profile") or {}
        session_profile = (latest_session or {}).get("profile", {})

        if preference_record:
            normalized_preferences = preference_record.get("normalized_preferences") or {}
        else:
            inferred_payload = {
                "target_roles": onboarding_profile.get("target_roles") or session_profile.get("target_roles") or [],
                "locations": (onboarding_profile.get("work_preferences") or {}).get("locations") or (session_profile.get("work_preferences") or {}).get("locations") or [],
                "work_arrangement": (onboarding_profile.get("work_preferences") or {}).get("remote_preference") or (session_profile.get("work_preferences") or {}).get("remote_preference"),
                "job_type": (onboarding_profile.get("work_preferences") or {}).get("employment_type") or (session_profile.get("work_preferences") or {}).get("employment_type"),
                "salary_expectations": {},
            }
            normalized_preferences = self.preference_normalizer.normalize(inferred_payload)["normalized_preferences"]

        years_experience = self._extract_years_experience(onboarding_profile, session_profile)
        skills = self._build_user_skill_profile(onboarding_profile, session_profile, latest_session, skill_lookup)
        return {"user": user, "preferences": normalized_preferences, "years_experience": years_experience, "skills": skills}

    def _build_user_skill_profile(self, onboarding_profile: dict, session_profile: dict, latest_session: Optional[dict], lookup: dict):
        aggregated = {}
        self._merge_skill_source(aggregated, (onboarding_profile.get("skills") or {}).get("user_selected", []), "manual_profile", 1.0, lookup)
        self._merge_skill_source(aggregated, (onboarding_profile.get("skills") or {}).get("extracted", []), "ai_profile", 0.8, lookup)
        self._merge_skill_source(aggregated, (onboarding_profile.get("resume_insights") or {}).get("skills", []), "ai_resume", 0.75, lookup)
        self._merge_skill_source(aggregated, (session_profile.get("skills") or {}).get("user_selected", []), "manual_session", 1.0, lookup)
        self._merge_skill_source(aggregated, (session_profile.get("skills") or {}).get("extracted", []), "ai_session", 0.8, lookup)
        if latest_session:
            for row in self.repository.get_extracted_skills_for_session(latest_session["id"]):
                self._merge_skill_source(aggregated, [row["skill"]], row.get("source", "ai_resume"), float(row.get("confidence", 0.75)), lookup)
        return aggregated

    def _merge_skill_source(self, aggregated: dict, skills: list[str], source: str, confidence: float, lookup: dict):
        for raw_skill in skills or []:
            normalized = self._normalize_skill(raw_skill, lookup)
            if not normalized:
                continue
            key = normalized["canonical_name"].lower()
            existing = aggregated.get(key)
            if not existing:
                aggregated[key] = {"skill": normalized["canonical_name"], "confidence": confidence, "sources": [source], "raw_matches": [raw_skill]}
            else:
                existing["confidence"] = max(existing["confidence"], confidence)
                if source not in existing["sources"]:
                    existing["sources"].append(source)
                if raw_skill not in existing["raw_matches"]:
                    existing["raw_matches"].append(raw_skill)

    def _score_skill_match(self, context: dict, job: dict):
        user_skills = context["skills"]
        core_skills = job.get("core_skills") or []
        preferred_skills = [skill for skill in (job.get("preferred_skills") or []) if skill not in core_skills]
        all_skills = core_skills + preferred_skills
        matched = []
        missing = []
        weighted_total = 0.0
        weighted_matched = 0.0
        for skill in all_skills:
            is_core = skill in core_skills
            skill_weight = 1.0 if is_core else 0.6
            weighted_total += skill_weight
            user_skill = user_skills.get(skill.lower())
            if user_skill:
                weighted_matched += skill_weight * user_skill["confidence"]
                matched.append({"skill": skill, "confidence": round(user_skill["confidence"], 4), "is_core": is_core})
            else:
                missing.append({"skill": skill, "is_core": is_core, "priority": "high" if is_core else "medium"})
        score = (weighted_matched / weighted_total) if weighted_total else 0.0
        return matched, missing, score, f"Matched {len(matched)} of {len(all_skills)} normalized job skills."

    def _score_preference_match(self, context: dict, job: dict):
        prefs = context["preferences"] or {}
        matched = []
        misses = []
        components = []
        target_roles = prefs.get("target_roles") or []
        if target_roles:
            role_match = job["role_name"] in target_roles or job["title"] in target_roles
            components.append(1.0 if role_match else 0.2)
            if role_match:
                matched.append(f"Role aligns with target roles: {job['role_name']}")
            else:
                misses.append("Selected role is outside the user's preferred target roles.")
        preferred_industries = prefs.get("industries") or []
        if preferred_industries:
            overlap = sorted(set(preferred_industries).intersection(set(job.get("industries") or [])))
            components.append(1.0 if overlap else 0.25)
            if overlap:
                matched.append(f"Industry match: {', '.join(overlap)}")
            else:
                misses.append("Industry does not match the user's saved preferences.")
        preferred_job_types = (prefs.get("job_type") or {}).get("allowed") or []
        if preferred_job_types:
            job_type_match = job.get("job_type") in preferred_job_types
            components.append(1.0 if job_type_match else 0.2)
            if job_type_match:
                matched.append(f"Job type match: {job.get('job_type')}")
            else:
                misses.append("Job type differs from the user's preferred employment type.")
        preferred_company_sizes = (prefs.get("company") or {}).get("sizes") or []
        if preferred_company_sizes:
            size_match = job.get("company_size") in preferred_company_sizes
            components.append(1.0 if size_match else 0.35)
            if size_match:
                matched.append(f"Company size match: {job.get('company_size')}")
            else:
                misses.append("Company size is outside the user's preferred range.")
        preferred_company_types = (prefs.get("company") or {}).get("types") or []
        if preferred_company_types:
            type_match = job.get("company_type") in preferred_company_types
            components.append(1.0 if type_match else 0.35)
            if type_match:
                matched.append(f"Company type match: {job.get('company_type')}")
            else:
                misses.append("Company type differs from the user's preferences.")
        score = sum(components) / len(components) if components else 0.6
        return matched, misses, score, "Preference score derived from target role, industry, job type, and company profile alignment."

    def _score_location_match(self, context: dict, job: dict):
        preferred_locations = (context["preferences"] or {}).get("locations") or []
        if not preferred_locations:
            return 0.6, "No explicit location preference was saved, so location match is neutral."
        if "Remote" in preferred_locations and "Remote" in (job.get("locations") or []):
            return 1.0, "Job supports remote work, which matches the user's location preference."
        overlap = sorted(set(preferred_locations).intersection(set(job.get("locations") or [])))
        if overlap:
            return 1.0, f"Job location overlaps with preferred locations: {', '.join(overlap)}."
        return 0.2, "Job location does not align well with the user's saved locations."

    def _score_work_arrangement_match(self, context: dict, job: dict):
        allowed = ((context["preferences"] or {}).get("work_arrangement") or {}).get("allowed") or []
        if not allowed:
            return 0.6, "No explicit work arrangement preference was saved, so this factor is neutral."
        if job.get("work_arrangement") in allowed:
            return 1.0, f"Work arrangement matches the user's preference: {job.get('work_arrangement')}."
        return 0.15, "Work arrangement differs from the user's preferred setup."

    def _score_seniority_fit(self, context: dict, job: dict):
        years = context.get("years_experience")
        if years is None:
            return 0.55, "Years of experience are missing, so seniority fit is estimated conservatively."
        job_min = job.get("years_experience_min")
        job_max = job.get("years_experience_max")
        if job_min is not None and years < job_min:
            gap = job_min - years
            score = 0.7 if gap <= 1 else 0.35 if gap <= 2 else 0.1
            return score, f"User experience is below the preferred range for this role by about {round(gap, 1)} years."
        if job_max is not None and years > job_max:
            gap = years - job_max
            score = 0.8 if gap <= 1 else 0.5 if gap <= 2 else 0.35
            return score, f"User experience is above the stated range by about {round(gap, 1)} years."
        target = SENIORITY_TARGETS.get(job.get("seniority_level"), 3.5)
        delta = abs(years - target)
        score = 1.0 if delta <= 1 else 0.8 if delta <= 2 else 0.6
        return score, f"Experience level fits the job's seniority band ({job.get('seniority_level')})."

    def _score_salary_fit(self, context: dict, job: dict):
        salary_pref = ((context["preferences"] or {}).get("salary_expectations") or {})
        min_amount = salary_pref.get("min_amount")
        currency = salary_pref.get("currency")
        if min_amount is None or not job.get("salary_min") or not job.get("salary_max"):
            return 0.0, "Salary fit was not scored because salary data is missing on the user or job side.", False
        if currency and job.get("salary_currency") and currency != job.get("salary_currency"):
            return 0.35, "Salary currencies do not match, so salary fit is discounted.", True
        if job.get("salary_max") >= min_amount:
            return 1.0, "Job salary band overlaps or exceeds the user's minimum expected salary.", True
        gap_ratio = max(0.0, (min_amount - job.get("salary_max")) / max(min_amount, 1))
        return max(0.0, 1.0 - gap_ratio), "Job salary is below the user's preferred minimum, reducing the score.", True

    def _extract_years_experience(self, onboarding_profile: dict, session_profile: dict):
        basic_profile = onboarding_profile.get("basic_profile") or onboarding_profile.get("basic_info") or {}
        session_basic = session_profile.get("basic_info") or {}
        return basic_profile.get("years_of_experience") or session_basic.get("years_of_experience")

    def _normalize_skill(self, value: str, lookup: dict):
        normalized = " ".join(str(value).strip().lower().replace("/", " ").replace("-", " ").split())
        return lookup.get(normalized)

    def _derive_lower_score_reasons(self, factor_scores: list[FactorScore], missing_skills: list[dict]):
        reasons = [factor.reason for factor in factor_scores if factor.active and factor.score < 0.6]
        if missing_skills:
            reasons.append(f"Missing important job skills: {', '.join(item['skill'] for item in missing_skills[:5])}.")
        return reasons

    def _build_summary(self, matched_skills: list[dict], missing_skills: list[dict], matched_preferences: list[str], lower_score_reasons: list[str], score: float):
        positives = []
        if matched_skills:
            positives.append(f"matched skills like {', '.join(item['skill'] for item in matched_skills[:3])}")
        if matched_preferences:
            positives.append(matched_preferences[0].lower())
        negatives = []
        if missing_skills:
            negatives.append(f"missing skills such as {', '.join(item['skill'] for item in missing_skills[:3])}")
        if lower_score_reasons:
            negatives.append(lower_score_reasons[0].rstrip('.').lower())
        positive_text = ", ".join(positives) if positives else "limited direct alignment"
        negative_text = f" Lower score drivers include {'; '.join(negatives)}." if negatives else ""
        return f"This job scored {score:.1f} because it has {positive_text}.{negative_text}"

    def _dedupe(self, values: list[str]):
        seen = set()
        result = []
        for value in values:
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(value)
        return result
