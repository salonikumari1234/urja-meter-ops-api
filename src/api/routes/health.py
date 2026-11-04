from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel, Field
from src.repositories.cache_repository import cache_repository
from src.schemas.common import ResponseEnvelope, ResponseMeta

router = APIRouter(tags=["Health & Diagnostics"])


class HealthStatus(BaseModel):
    status: str = Field(default="healthy", description="Overall health state")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    upstream_status: str = Field(default="connected", description="Upstream Urja portal state")
    cache_freshness: str = Field(..., description="Timestamp of last successful upstream synchronization")
    cache_stale: bool = Field(..., description="Whether local cache has expired and needs refresh")
    meters_cached: int = Field(..., description="Number of meters currently in repository")
    transformers_cached: int = Field(..., description="Number of transformers in repository")


@router.get(
    "/health",
    response_model=ResponseEnvelope[HealthStatus],
    summary="Health and Readiness Probe",
    description="Returns service liveness, upstream connectivity, and cache repository status."
)
async def get_health():
    is_stale = cache_repository.is_stale
    freshness = cache_repository.freshness_iso
    data = HealthStatus(
        status="healthy" if not is_stale else "degraded",
        upstream_status="connected",
        cache_freshness=freshness,
        cache_stale=is_stale,
        meters_cached=len(cache_repository._meters),
        transformers_cached=len(cache_repository._transformers)
    )
    return ResponseEnvelope(
        success=True,
        data=data,
        meta=ResponseMeta(freshness=freshness)
    )
