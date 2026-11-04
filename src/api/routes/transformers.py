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
from src.schemas.transformer import Transformer, TransformerDetail
from src.services.transformer_service import transformer_service

router = APIRouter(
    prefix="/transformers",
    tags=["Distribution Transformers"],
    dependencies=[Depends(require_api_key)]
)


@router.get(
    "",
    response_model=PaginatedResponseEnvelope[Transformer],
    summary="List Distribution Transformers",
    description="Retrieve distribution transformers with rated capacity (kVA), feeder codes, and attached meter counts."
)
async def list_transformers(
    search: Optional[str] = Query(None, description="Search term matching transformer code or name"),
    feeder_code: Optional[str] = Query(None, description="Filter by upstream feeder code (e.g., F-001)"),
    sort_by: str = Query("code", description="Sort by field (code, name, feeder_code, capacity_kva, meter_count)"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order ('asc' or 'desc')"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
):
    items, total, freshness = await transformer_service.list_transformers(
        search=search,
        feeder_code=feeder_code,
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
    "/{code}",
    response_model=ResponseEnvelope[TransformerDetail],
    summary="Get Transformer Details",
    description="Retrieve a specific transformer along with the full roster of connected meters."
)
async def get_transformer_detail(
    code: str = Path(..., description="Distribution transformer code, e.g., DT-001")
):
    transformer, freshness = await transformer_service.get_transformer(code)
    return ResponseEnvelope(
        success=True,
        data=transformer,
        meta=ResponseMeta(freshness=freshness)
    )
