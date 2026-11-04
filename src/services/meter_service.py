from typing import List, Optional, Tuple
from src.clients.portal_client import UrjaPortalClient
from src.core.exceptions import ResourceNotFoundError
from src.repositories.cache_repository import CacheRepository, cache_repository
from src.schemas.meter import MeterDetail, MeterListItem


class MeterService:
    def __init__(
        self,
        repo: Optional[CacheRepository] = None,
        client: Optional[UrjaPortalClient] = None
    ):
        self.repo = repo or cache_repository
        self.client = client or UrjaPortalClient()

    async def list_meters(
        self,
        search: Optional[str] = None,
        make: Optional[str] = None,
        phase_type: Optional[str] = None,
        status: Optional[str] = None,
        install_type: Optional[str] = None,
        dt_code: Optional[str] = None,
        sort_by: str = "meter_id",
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[MeterListItem], int, str]:
        """Lists and filters meters from repository, ensuring data freshness."""
        await self.repo.ensure_synced(self.client)
        items, total = self.repo.query_meters(
            search=search,
            make=make,
            phase_type=phase_type,
            status=status,
            install_type=install_type,
            dt_code=dt_code,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit
        )
        return items, total, self.repo.freshness_iso

    async def get_meter(self, meter_id: str) -> Tuple[MeterDetail, str]:
        """Retrieves a single meter with complete electrical hierarchy."""
        await self.repo.ensure_synced(self.client)
        meter = self.repo.get_meter(meter_id)
        if not meter:
            raise ResourceNotFoundError(resource="Meter", identifier=meter_id)
        return meter, self.repo.freshness_iso


meter_service = MeterService()
