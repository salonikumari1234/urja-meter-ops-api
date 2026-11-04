import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from src.api.dependencies.auth import require_api_key
from src.schemas.common import (
    PaginationMeta,
    PaginatedResponseEnvelope,
    ResponseEnvelope,
    ResponseMeta
)
from src.schemas.meter import MeterDetail, MeterListItem, MeterPhase, MeterStatus
from src.schemas.energy import MeterEnergyResponse
from src.services.meter_service import meter_service
from src.services.energy_service import energy_service

router = APIRouter(
    prefix="/meters",
    tags=["Meters"],
    dependencies=[Depends(require_api_key)]
)


@router.get(
    "",
    response_model=PaginatedResponseEnvelope[MeterListItem],
    summary="List and Filter Meters",
    description="Query meters with full-text search and attribute filters for make, phase, status, and DT code."
)
async def list_meters(
    search: Optional[str] = Query(None, description="Search term matching meter ID or hardware serial"),
    make: Optional[str] = Query(None, description="Filter by manufacturer (HPL, Genus, Secure, Allied, L&T)"),
    phase_type: Optional[MeterPhase] = Query(None, description="Filter by phase ('single' or 'three')"),
    status: Optional[MeterStatus] = Query(None, description="Filter by status ('Installed', 'Faulty', 'Decommissioned')"),
    install_type: Optional[str] = Query(None, description="Filter by installation type ('Whole Current', 'CT Operated')"),
    dt_code: Optional[str] = Query(None, description="Filter by Distribution Transformer code (e.g. DT-001)"),
    sort_by: str = Query("meter_id", description="Field to sort by (meter_id, serial_no, make, install_status)"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order ('asc' or 'desc')"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
):
    phase_str = phase_type.value if phase_type else None
    status_str = status.value if status else None

    items, total, freshness = await meter_service.list_meters(
        search=search,
        make=make,
        phase_type=phase_str,
        status=status_str,
        install_type=install_type,
        dt_code=dt_code,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit
    )

    total_pages = math.ceil(total / limit) if total > 0 else 0

    return PaginatedResponseEnvelope(
        success=True,
        data=items,
        meta=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            freshness=freshness
        )
    )


@router.get(
    "/{meter_id}",
    response_model=ResponseEnvelope[MeterDetail],
    summary="Get Meter Details",
    description="Retrieve comprehensive nameplate specifications, coordinates, and 7-level electrical hierarchy."
)
async def get_meter_detail(
    meter_id: str = Path(..., description="Unique meter identifier, e.g., J100000")
):
    meter, freshness = await meter_service.get_meter(meter_id)
    return ResponseEnvelope(
        success=True,
        data=meter,
        meta=ResponseMeta(freshness=freshness)
    )


@router.get(
    "/{meter_id}/readings",
    response_model=ResponseEnvelope[MeterEnergyResponse],
    summary="Get Meter Interval Readings",
    description="Fetch historical 30-minute interval readings including active energy (kWh), apparent energy (kVAh), and Phase R voltage."
)
async def get_meter_readings(
    meter_id: str = Path(..., description="Unique meter identifier"),
    start_date: Optional[str] = Query(None, description="Start date filter (DD/MM/YYYY or ISO-8601)"),
    end_date: Optional[str] = Query(None, description="End date filter (DD/MM/YYYY or ISO-8601)"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum readings to return (most recent)")
):
    response, freshness = await energy_service.get_meter_energy(
        meter_id=meter_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    return ResponseEnvelope(
        success=True,
        data=response,
        meta=ResponseMeta(freshness=freshness)
    )
