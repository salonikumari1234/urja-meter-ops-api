from typing import Dict
from pydantic import BaseModel, Field, ConfigDict


class OperationalSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_meters: int = Field(..., ge=0, description="Total meters tracked in portal")
    total_transformers: int = Field(..., ge=0, description="Total distribution transformers")
    status_breakdown: Dict[str, int] = Field(
        ...,
        description="Counts grouped by installation status (Installed, Faulty, Decommissioned)"
    )
    make_breakdown: Dict[str, int] = Field(
        ...,
        description="Counts grouped by manufacturer (HPL, Genus, Secure, Allied, L&T)"
    )
    phase_breakdown: Dict[str, int] = Field(
        ...,
        description="Counts grouped by phase (single, three)"
    )
    install_type_breakdown: Dict[str, int] = Field(
        ...,
        description="Counts grouped by installation wiring type (Whole Current, CT Operated)"
    )
    build_breakdown: Dict[str, int] = Field(
        ...,
        description="Counts grouped by firmware/build generation (legacy, v2)"
    )
    freshness: str = Field(..., description="Timestamp of when upstream inventory was synchronized")
