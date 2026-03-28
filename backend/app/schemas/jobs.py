from pydantic import BaseModel, ConfigDict, Field, ValidationError as PydanticError

from app.errors import ValidationError


class JobRecommendationsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    limit: int = Field(default=10, ge=1, le=50)


class JobMatchDetailQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    job_id: str


def validate_payload(schema_class, payload):
    try:
        return schema_class.model_validate(payload)
    except PydanticError as error:
        raise ValidationError("Payload validation failed.", payload={"details": error.errors()}) from error
