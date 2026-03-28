from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    ValidationError as PydanticError,
    field_validator,
    model_validator,
)

from app.errors import ValidationError


class RawJobInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_job_id: str | None = None
    external_id: str | None = None
    title: str | None = None
    company: str | None = None
    company_name: str | None = None
    description: str | None = None
    description_summary: str | None = None
    location: str | list[str] | None = None
    locations: list[str] | None = None
    work_arrangement: str | None = None
    posted_date: str | None = None
    posted_at: str | None = None
    salary_text: str | None = None
    salary: str | None = None
    source: str | None = None
    source_url: str | None = None
    apply_url: str | None = None
    url: str | None = None
    job_url: str | None = None
    role_name: str | None = None
    job_type: str | None = None
    industries: list[str] | str | None = None
    company_size: str | None = None
    company_type: str | None = None
    seniority_level: str | None = None
    years_experience_min: float | None = None
    years_experience_max: float | None = None
    skills: list[str] | str | None = None
    required_skills: list[str] | str | None = None
    preferred_skills: list[str] | str | None = None


class JobAggregationRunPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connector_type: str = Field(default="manual", min_length=2)
    connector_name: str | None = None
    source_label: str | None = None
    source_url: HttpUrl | None = None
    jobs: list[RawJobInput] = Field(min_length=1)
    metadata: dict = Field(default_factory=dict)


class LinkedInTinyFishIngestionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    linkedin_url: HttpUrl
    target_role: str = Field(min_length=2, max_length=120)
    max_jobs: int = Field(default=12, ge=1, le=25)
    wait_timeout_seconds: int = Field(default=20, ge=5, le=90)
    poll_interval_seconds: int = Field(default=3, ge=1, le=15)
    browser_profile: str | None = None
    proxy_enabled: bool | None = None
    proxy_country_code: str | None = Field(default=None, min_length=2, max_length=2)
    goal_override: str | None = Field(default=None, min_length=10, max_length=2000)

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, value: HttpUrl):
        host = (value.host or "").lower()
        if "linkedin.com" not in host:
            raise ValueError("linkedin_url must point to linkedin.com.")
        return value


class JobAggregationMetricsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connector_type: str | None = None


class JobAggregationListJobsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    source: str | None = None
    role: str | None = None


class RetryFailedJobsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str | None = None
    raw_job_ids: list[str] | None = None
    limit: int = Field(default=25, ge=1, le=100)

    @model_validator(mode="after")
    def validate_selector(self):
        if self.run_id and self.raw_job_ids:
            return self
        if self.run_id or self.raw_job_ids:
            return self
        return self


class RetryFailedJobsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str | None = None


def validate_payload(schema_class, payload):
    try:
        return schema_class.model_validate(payload)
    except PydanticError as error:
        raise ValidationError("Payload validation failed.", payload={"details": error.errors()}) from error
