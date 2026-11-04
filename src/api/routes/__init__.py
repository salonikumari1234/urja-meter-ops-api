from fastapi import APIRouter
from .health import router as health_router
from .meters import router as meters_router
from .transformers import router as transformers_router
from .hierarchy import router as hierarchy_router
from .summary import router as summary_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(meters_router)
api_router.include_router(transformers_router)
api_router.include_router(hierarchy_router)
api_router.include_router(summary_router)

__all__ = ["api_router"]
