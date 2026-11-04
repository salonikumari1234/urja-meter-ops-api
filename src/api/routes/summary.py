from fastapi import APIRouter, Depends
from src.api.dependencies.auth import require_api_key
from src.schemas.common import ResponseEnvelope, ResponseMeta
from src.schemas.summary import OperationalSummary
from src.services.hierarchy_service import hierarchy_service

router = APIRouter(
    prefix="/summary",
    tags=["Operational Summary"],
    dependencies=[Depends(require_api_key)]
)


@router.get(
    "",
    response_model=ResponseEnvelope[OperationalSummary],
    summary="Get Operations Overview",
    description="Returns aggregate counts and distributions for meter makes, phases, installation statuses, firmware builds, and transformer totals."
)
async def get_summary():
    summary, freshness = await hierarchy_service.get_operational_summary()
    return ResponseEnvelope(
        success=True,
        data=summary,
        meta=ResponseMeta(freshness=freshness)
    )
