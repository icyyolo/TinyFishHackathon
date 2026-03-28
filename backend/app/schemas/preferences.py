from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError as PydanticError, field_validator, model_validator

from app.errors import ValidationError


class SalaryExpectationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_amount: int | None = Field(default=None, ge=0)
    max_amount: int | None = Field(default=None, ge=0)
    currency: str | None = None
    period: str | None = None

    @model_validator(mode="after")
    def validate_range(self):
        if self.min_amount is not None and self.max_amount is not None and self.max_amount < self.min_amount:
            raise ValueError("salary_expectations.max_amount must be greater than or equal to min_amount")
        return self


class PreferencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_roles: list[str] = Field(default_factory=list)
    work_arrangement: str | list[str] | None = None
    industries: list[str] | str = Field(default_factory=list)
    locations: list[str] | str = Field(default_factory=list)
    job_type: str | list[str] | None = None
    salary_expectations: SalaryExpectationPayload | None = None
    company_size: list[str] | str = Field(default_factory=list)
    company_type: list[str] | str = Field(default_factory=list)

    @field_validator("target_roles", "industries", "locations", "company_size", "company_type", mode="before")
    @classmethod
    def coerce_list_fields(cls, value: Any):
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


class NormalizePreferencesPayload(PreferencePayload):
    pass


class UpsertPreferencesPayload(PreferencePayload):
    pass


def validate_payload(schema_class, payload):
    try:
        return schema_class.model_validate(payload)
    except PydanticError as error:
        raise ValidationError("Payload validation failed.", payload={"details": error.errors()}) from error
