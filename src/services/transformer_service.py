from typing import List, Optional, Tuple
from src.clients.portal_client import UrjaPortalClient
from src.core.exceptions import ResourceNotFoundError
from src.repositories.cache_repository import CacheRepository, cache_repository
from src.schemas.transformer import Transformer, TransformerDetail


class TransformerService:
    def __init__(
        self,
        repo: Optional[CacheRepository] = None,
        client: Optional[UrjaPortalClient] = None
    ):
        self.repo = repo or cache_repository
        self.client = client or UrjaPortalClient()

    async def list_transformers(
        self,
        search: Optional[str] = None,
        feeder_code: Optional[str] = None,
        sort_by: str = "code",
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Transformer], int, str]:
        await self.repo.ensure_synced(self.client)
        items, total = self.repo.query_transformers(
            search=search,
            feeder_code=feeder_code,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit
        )
        return items, total, self.repo.freshness_iso

    async def get_transformer(self, code: str) -> Tuple[TransformerDetail, str]:
        await self.repo.ensure_synced(self.client)
        transformer = self.repo.get_transformer_detail(code)
        if not transformer:
            raise ResourceNotFoundError(resource="Transformer", identifier=code)
        return transformer, self.repo.freshness_iso


transformer_service = TransformerService()
