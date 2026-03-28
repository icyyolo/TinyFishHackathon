from app.errors import ValidationError


WORK_ARRANGEMENT_MAP = {
    "remote": "remote",
    "remote-first": "remote",
    "work from home": "remote",
    "wfh": "remote",
    "hybrid": "hybrid",
    "onsite": "onsite",
    "on-site": "onsite",
    "in office": "onsite",
    "flexible": "flexible",
    "any": "flexible",
}

JOB_TYPE_MAP = {
    "full-time": "full_time",
    "full time": "full_time",
    "permanent": "full_time",
    "part-time": "part_time",
    "part time": "part_time",
    "contract": "contract",
    "internship": "internship",
    "intern": "internship",
    "temporary": "contract",
    "freelance": "freelance",
}

INDUSTRY_MAP = {
    "tech": "technology",
    "software": "technology",
    "it": "technology",
    "fintech": "fintech",
    "finance": "financial_services",
    "banking": "financial_services",
    "health": "healthcare",
    "health tech": "healthcare",
    "healthcare": "healthcare",
    "education": "education",
    "edtech": "education",
    "ecommerce": "ecommerce",
    "e-commerce": "ecommerce",
    "retail": "retail",
    "logistics": "logistics",
    "manufacturing": "manufacturing",
    "government": "government",
    "nonprofit": "nonprofit",
    "media": "media",
}

COMPANY_SIZE_MAP = {
    "startup": "startup",
    "small": "small",
    "small business": "small",
    "mid": "mid_market",
    "mid-size": "mid_market",
    "mid market": "mid_market",
    "enterprise": "enterprise",
    "large": "enterprise",
}

COMPANY_TYPE_MAP = {
    "product": "product",
    "product company": "product",
    "services": "services",
    "service": "services",
    "consulting": "services",
    "startup": "startup",
    "enterprise": "enterprise",
    "government": "government",
    "nonprofit": "nonprofit",
}

CURRENCY_MAP = {
    "usd": "USD",
    "us$": "USD",
    "$": "USD",
    "sgd": "SGD",
    "s$": "SGD",
    "eur": "EUR",
    "gbp": "GBP",
}

PERIOD_MAP = {
    "year": "annual",
    "yearly": "annual",
    "annual": "annual",
    "month": "monthly",
    "monthly": "monthly",
    "hour": "hourly",
    "hourly": "hourly",
}

LOCATION_MAP = {
    "sg": "Singapore",
    "singapore": "Singapore",
    "nyc": "New York, NY, United States",
    "new york": "New York, NY, United States",
    "sf": "San Francisco, CA, United States",
    "san francisco": "San Francisco, CA, United States",
    "kl": "Kuala Lumpur, Malaysia",
    "kuala lumpur": "Kuala Lumpur, Malaysia",
    "remote": "Remote",
}


class PreferenceNormalizer:
    def normalize(self, payload: dict) -> dict:
        defaults_applied = {}

        target_roles = self._normalize_roles(payload.get("target_roles", []))

        work_arrangements, work_defaulted = self._normalize_multi_enum(
            payload.get("work_arrangement"),
            WORK_ARRANGEMENT_MAP,
            default_values=["hybrid"],
            field_name="work_arrangement",
        )
        defaults_applied["work_arrangement"] = work_defaulted

        industries = self._normalize_multi_enum(
            payload.get("industries", []),
            INDUSTRY_MAP,
            default_values=[],
            field_name="industries",
        )[0]

        locations, locations_defaulted = self._normalize_locations(payload.get("locations", []))
        defaults_applied["locations"] = locations_defaulted

        job_types, job_defaulted = self._normalize_multi_enum(
            payload.get("job_type"),
            JOB_TYPE_MAP,
            default_values=["full_time"],
            field_name="job_type",
        )
        defaults_applied["job_type"] = job_defaulted

        salary_expectations, salary_defaults = self._normalize_salary(
            payload.get("salary_expectations")
        )
        defaults_applied["salary_expectations"] = salary_defaults

        company_sizes = self._normalize_multi_enum(
            payload.get("company_size", []),
            COMPANY_SIZE_MAP,
            default_values=[],
            field_name="company_size",
        )[0]
        company_types = self._normalize_multi_enum(
            payload.get("company_type", []),
            COMPANY_TYPE_MAP,
            default_values=[],
            field_name="company_type",
        )[0]

        normalized = {
            "target_roles": target_roles,
            "work_arrangement": {
                "primary": work_arrangements[0],
                "allowed": work_arrangements,
            },
            "industries": industries,
            "locations": locations,
            "job_type": {
                "primary": job_types[0],
                "allowed": job_types,
            },
            "salary_expectations": salary_expectations,
            "company": {
                "sizes": company_sizes,
                "types": company_types,
            },
        }

        matching_strategy = self._build_matching_strategy(normalized)

        return {
            "normalized_preferences": normalized,
            "defaults_applied": defaults_applied,
            "matching_strategy": matching_strategy,
        }

    def _normalize_roles(self, roles: list[str]) -> list[str]:
        cleaned = []
        seen = set()
        for role in roles or []:
            value = self._clean_text(role)
            if not value:
                continue
            canonical = " ".join(part.capitalize() for part in value.split())
            key = canonical.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(canonical)
        return cleaned

    def _normalize_locations(self, values) -> tuple[list[str], bool]:
        items = self._as_list(values)
        if not items:
            return ["Remote"], True

        normalized = []
        seen = set()
        for value in items:
            cleaned = self._clean_text(value)
            canonical = LOCATION_MAP.get(cleaned.lower(), cleaned.title())
            key = canonical.lower()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(canonical)
        return normalized, False

    def _normalize_salary(self, value) -> tuple[dict, dict]:
        value = value or {}
        if isinstance(value, str):
            raise ValidationError("salary_expectations must be an object, not a string.")

        currency = value.get("currency")
        period = value.get("period")
        defaults = {
            "currency": currency is None,
            "period": period is None,
        }

        canonical_currency = CURRENCY_MAP.get(str(currency).strip().lower(), "USD") if currency else "USD"
        canonical_period = PERIOD_MAP.get(str(period).strip().lower(), "annual") if period else "annual"

        normalized = {
            "min_amount": value.get("min_amount"),
            "max_amount": value.get("max_amount"),
            "currency": canonical_currency,
            "period": canonical_period,
        }
        return normalized, defaults

    def _normalize_multi_enum(self, values, mapping: dict, default_values: list[str], field_name: str):
        items = self._as_list(values)
        if not items:
            return default_values, True

        normalized = []
        seen = set()
        for item in items:
            cleaned = self._clean_text(item).lower()
            if not cleaned:
                continue
            canonical = mapping.get(cleaned)
            if not canonical:
                raise ValidationError(
                    f"Unsupported value '{item}' for {field_name}.",
                    payload={"supported_values": sorted(set(mapping.values()))},
                )
            if canonical in seen:
                continue
            seen.add(canonical)
            normalized.append(canonical)

        return normalized or default_values, False if normalized else True

    def _build_matching_strategy(self, normalized: dict) -> dict:
        salary = normalized["salary_expectations"]
        filters = {
            "target_roles": normalized["target_roles"],
            "work_arrangements": normalized["work_arrangement"]["allowed"],
            "industries": normalized["industries"],
            "locations": normalized["locations"],
            "job_types": normalized["job_type"]["allowed"],
            "salary_currency": salary["currency"],
            "minimum_salary": salary["min_amount"],
            "company_sizes": normalized["company"]["sizes"],
            "company_types": normalized["company"]["types"],
        }

        ranking_signals = [
            {
                "signal": "target_role_alignment",
                "weight": 0.35,
                "description": "Boost jobs whose title or normalized role taxonomy matches the preferred target roles.",
            },
            {
                "signal": "location_arrangement_fit",
                "weight": 0.20,
                "description": "Boost jobs whose location and remote policy match the normalized location and work arrangement preferences.",
            },
            {
                "signal": "industry_preference",
                "weight": 0.15,
                "description": "Boost jobs in preferred industries but do not necessarily hard-filter unless required by the product.",
            },
            {
                "signal": "employment_type_fit",
                "weight": 0.10,
                "description": "Boost jobs matching the preferred job type, such as full-time or internship.",
            },
            {
                "signal": "salary_fit",
                "weight": 0.10,
                "description": "Increase rank when a job salary band overlaps or exceeds the candidate's normalized expectation.",
            },
            {
                "signal": "company_profile_fit",
                "weight": 0.10,
                "description": "Use company size and company type preferences as soft ranking signals.",
            },
        ]

        ranking_examples = [
            {
                "example": "Hard filter",
                "logic": "Only keep jobs where job_type is in allowed job types and work arrangement is in allowed work arrangements.",
            },
            {
                "example": "Role score",
                "logic": "Add +35 points when a job's normalized role taxonomy overlaps with the preferred target roles.",
            },
            {
                "example": "Salary score",
                "logic": "Add +10 points when the job's max salary is above the preferred minimum salary in the same currency or convertible band.",
            },
            {
                "example": "Company fit score",
                "logic": "Add +5 to +10 points when the employer size or company type matches stated preferences.",
            },
        ]

        return {
            "filters": filters,
            "ranking_signals": ranking_signals,
            "ranking_examples": ranking_examples,
        }

    def _as_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _clean_text(self, value) -> str:
        return str(value).strip()
