from typing import Optional, Tuple
from src.clients.portal_client import UrjaPortalClient
from src.repositories.cache_repository import CacheRepository, cache_repository
from src.schemas.hierarchy import ElectricalHierarchySummary
from src.schemas.summary import OperationalSummary


class HierarchyService:
    def __init__(
        self,
        repo: Optional[CacheRepository] = None,
        client: Optional[UrjaPortalClient] = None
    ):
        self.repo = repo or cache_repository
        self.client = client or UrjaPortalClient()

    async def get_electrical_hierarchy(self) -> Tuple[ElectricalHierarchySummary, str]:
        await self.repo.ensure_synced(self.client)
        return self.repo.get_hierarchy_summary(), self.repo.freshness_iso

    async def get_operational_summary(self) -> Tuple[OperationalSummary, str]:
        await self.repo.ensure_synced(self.client)
        return self.repo.get_summary(), self.repo.freshness_iso


hierarchy_service = HierarchyService()
