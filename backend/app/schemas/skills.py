from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError as PydanticError

from app.errors import ValidationError


class SkillRadarQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    target_role: str = Field(min_length=2)


class SkillTrendQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_role: str = Field(min_length=2)
    window_days: int = Field(default=90, ge=7, le=365)
    limit: int = Field(default=10, ge=1, le=25)


class TinyFishIngestionStartPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_url: HttpUrl
    target_role: str = Field(min_length=2)
    max_jobs: int = Field(default=20, ge=1, le=100)
    browser_profile: str | None = None
    proxy_enabled: bool = False
    proxy_country_code: str | None = None
    goal_override: str | None = None


class TinyFishRunQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=3)


def validate_payload(schema_class, payload):
    try:
        return schema_class.model_validate(payload)
    except PydanticError as error:
        raise ValidationError("Payload validation failed.", payload={"details": error.errors()}) from error
