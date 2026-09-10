from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


from app.providers.schemas import map_to_requirement_type


class VerificationAPIRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bid_submission_id: int = Field(gt=0)
    bid_document_id: int | None = Field(default=None, gt=0)
    verification_type: str = Field(min_length=1, max_length=100)
    identifier: str = Field(min_length=1, max_length=255)


class VerificationAPIResponse(BaseModel):
    id: int
    bid_submission_id: int
    bid_document_id: int | None
    requirement_type: str = ""
    identifier: str
    status: str = ""
    verified_data: dict | None = None
    source: str = ""
    checked_at: datetime
    created_at: datetime

    # Retained fields for full API backward compatibility
    provider: str
    verification_type: str
    verification_status: str
    source_mode: str | None = None
    message: str | None = None
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def populate_api_response_fields(self):
        if not self.source and self.provider:
            self.source = self.provider

        if not self.status and self.verification_status:
            self.status = self.verification_status

        if not self.requirement_type:
            self.requirement_type = map_to_requirement_type(
                self.verification_type or self.provider
            )

        return self
