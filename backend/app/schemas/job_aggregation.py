from typing import List, Optional, Union

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

    source_job_id: Optional[str] = None
    external_id: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    company_name: Optional[str] = None
    description: Optional[str] = None
    description_summary: Optional[str] = None
    location: Optional[Union[str, List[str]]] = None
    locations: Optional[List[str]] = None
    work_arrangement: Optional[str] = None
    posted_date: Optional[str] = None
    posted_at: Optional[str] = None
    salary_text: Optional[str] = None
    salary: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    apply_url: Optional[str] = None
    url: Optional[str] = None
    job_url: Optional[str] = None
    role_name: Optional[str] = None
    job_type: Optional[str] = None
    industries: Optional[Union[List[str], str]] = None
    company_size: Optional[str] = None
    company_type: Optional[str] = None
    seniority_level: Optional[str] = None
    years_experience_min: Optional[float] = None
    years_experience_max: Optional[float] = None
    skills: Optional[Union[List[str], str]] = None
    required_skills: Optional[Union[List[str], str]] = None
    preferred_skills: Optional[Union[List[str], str]] = None


class JobAggregationRunPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connector_type: str = Field(default="manual", min_length=2)
    connector_name: Optional[str] = None
    source_label: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    jobs: list[RawJobInput] = Field(min_length=1)
    metadata: dict = Field(default_factory=dict)


class LinkedInTinyFishIngestionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    linkedin_url: HttpUrl
    target_role: str = Field(min_length=2, max_length=120)
    max_jobs: int = Field(default=12, ge=1, le=25)
    wait_timeout_seconds: int = Field(default=20, ge=5, le=90)
    poll_interval_seconds: int = Field(default=3, ge=1, le=15)
    browser_profile: Optional[str] = None
    proxy_enabled: Optional[bool] = None
    proxy_country_code: Optional[str] = Field(default=None, min_length=2, max_length=2)
    goal_override: Optional[str] = Field(default=None, min_length=10, max_length=2000)

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, value: HttpUrl):
        host = (value.host or "").lower()
        if "linkedin.com" not in host:
            raise ValueError("linkedin_url must point to linkedin.com.")
        return value


class JobAggregationMetricsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connector_type: Optional[str] = None


class JobAggregationListJobsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    source: Optional[str] = None
    role: Optional[str] = None


class RetryFailedJobsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: Optional[str] = None
    raw_job_ids: Optional[List[str]] = None
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

    run_id: Optional[str] = None


def validate_payload(schema_class, payload):
    try:
        return schema_class.model_validate(payload)
    except PydanticError as error:
        raise ValidationError("Payload validation failed.", payload={"details": error.errors()}) from error
