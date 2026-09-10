from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AuditLogBase(BaseModel):
    """Base Pydantic schema for AuditLog."""

    action: str = Field(..., max_length=100, description="Audit action name")
    entity_type: str = Field(..., max_length=100, description="Target entity type")
    entity_id: int | None = Field(default=None, description="Target entity ID")
    bid_submission_id: int | None = Field(default=None, description="Associated Bid Submission ID")
    old_value: dict | None = Field(default=None, description="Previous state snapshot")
    new_value: dict | None = Field(default=None, description="New state snapshot")
    details: str | dict | None = Field(default=None, description="Additional context or details")
    ip_address: str | None = Field(default=None, max_length=45, description="Client IP address")


class AuditLogCreate(AuditLogBase):
    """Schema for creating a new audit log record."""

    user_id: int | None = Field(default=None, description="Authenticated user ID")


class AuditLogResponse(AuditLogBase):
    """Response schema for returning an audit log record."""

    id: int
    user_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """Paginated list response schema for audit logs."""

    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(from_attributes=True)
