from pydantic import BaseModel, ConfigDict, Field
from app.providers.schemas import VerificationStatus


class ManualVerificationCreate(BaseModel):
    """Payload for recording a human-in-the-loop manual verification by a Procurement Officer."""

    model_config = ConfigDict(extra="forbid")

    bid_submission_id: int
    requirement_type: str = Field(min_length=1, max_length=100)
    identifier: str = Field(min_length=1, max_length=255)
    verification_status: VerificationStatus
    message: str | None = None
    reference_notes: str | None = Field(None, description="Officer notes and external portal reference IDs")
