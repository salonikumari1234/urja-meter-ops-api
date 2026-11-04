from fastapi import APIRouter, Depends
from src.api.dependencies.auth import require_api_key
from src.schemas.common import ResponseEnvelope, ResponseMeta
from src.schemas.hierarchy import ElectricalHierarchySummary
from src.services.hierarchy_service import hierarchy_service

router = APIRouter(
    prefix="/hierarchy",
    tags=["Electrical Hierarchy"],
    dependencies=[Depends(require_api_key)]
)


@router.get(
    "",
    response_model=ResponseEnvelope[ElectricalHierarchySummary],
    summary="Get Electrical Grid Hierarchy",
    description="Returns the full hierarchical breakdown across Zones, Circles, Divisions, Subdivisions, Substations, Feeders, and Transformers."
)
async def get_grid_hierarchy():
    summary, freshness = await hierarchy_service.get_electrical_hierarchy()
    return ResponseEnvelope(
        success=True,
        data=summary,
        meta=ResponseMeta(freshness=freshness)
    )
