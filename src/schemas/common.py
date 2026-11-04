from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class ResponseMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 timestamp of response generation"
    )
    source: str = Field(
        default="urja-ops",
        description="Source identifier"
    )
    freshness: Optional[str] = Field(
        default=None,
        description="ISO-8601 timestamp of when underlying data was synchronized from upstream"
    )


class PaginationMeta(ResponseMeta):
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total matching items across all pages")
    total_pages: int = Field(..., ge=0, description="Total available pages")


class ResponseEnvelope(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(default=True, description="Indicates request success status")
    data: T = Field(..., description="Payload data")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")


class PaginatedResponseEnvelope(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(default=True, description="Indicates request success status")
    data: List[T] = Field(default_factory=list, description="Paginated items list")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable explanation of error")
    details: Optional[Any] = Field(default=None, description="Optional diagnostic details")


class ErrorEnvelope(BaseModel):
    success: bool = Field(default=False, description="Always false for error envelopes")
    error: ErrorDetail = Field(..., description="Error detail information")
    request_id: Optional[str] = Field(default=None, description="Trace request identifier")
