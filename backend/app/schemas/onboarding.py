import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError as PydanticError, field_validator

from app.errors import ValidationError


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[str]):
        if value is None:
            return value
        if not EMAIL_PATTERN.match(value):
            raise ValueError("email must be a valid email address")
        return value.lower()


class BasicProfilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: Optional[str] = None
    location: Optional[str] = None
    years_of_experience: Optional[float] = Field(default=None, ge=0)
    summary: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class EducationItemPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    institution: str
    degree: str
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = Field(default=None, ge=1900, le=2100)


class WorkPreferencesPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locations: list[str] = Field(default_factory=list)
    remote_preference: Optional[str] = None
    employment_type: Optional[str] = None
    salary_expectation: Optional[str] = None


class CreateSessionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: UserPayload
    basic_profile: BasicProfilePayload = Field(default_factory=BasicProfilePayload)
    education_background: list[EducationItemPayload] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    work_preferences: WorkPreferencesPayload = Field(default_factory=WorkPreferencesPayload)


class UpdateSessionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: Optional[UserPayload] = None
    basic_profile: Optional[BasicProfilePayload] = None
    education_background: Optional[list[EducationItemPayload]] = None
    skills: Optional[list[str]] = None
    target_roles: Optional[list[str]] = None
    work_preferences: Optional[WorkPreferencesPayload] = None
    status: Optional[str] = None


class GenerateQuestionsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_questions: int = Field(default=5, ge=1, le=10)


class AnswerPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    answer: str = Field(min_length=1)


class SaveAnswersPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answers: list[AnswerPayload] = Field(min_length=1)


def validate_payload(schema_class, payload):
    try:
        return schema_class.model_validate(payload)
    except PydanticError as error:
        raise ValidationError("Payload validation failed.", payload={"details": error.errors()}) from error