import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from src.clients.portal_client import UrjaPortalClient
from src.config.settings import settings
from src.core.logging import logger
from src.schemas.meter import (
    GeoCoordinates,
    HierarchyNode,
    MeterDetail,
    MeterHierarchy,
    MeterListItem
)
from src.schemas.transformer import Transformer, TransformerDetail
from src.schemas.summary import OperationalSummary
from src.schemas.hierarchy import HierarchyTreeNode, ElectricalHierarchySummary


class CacheRepository:
    """
    In-memory caching and query layer for normalized Urja meter operations data.
    Provides sub-millisecond local filtering, pagination, and sorting while
    minimizing load on the upstream portal.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._synced_at: Optional[datetime] = None
        self._meters: Dict[str, MeterDetail] = {}
        self._transformers: Dict[str, Transformer] = {}
        self._dt_to_meter_ids: Dict[str, List[str]] = {}

    @property
    def is_stale(self) -> bool:
        if self._synced_at is None:
            return True
        elapsed = (datetime.now(timezone.utc) - self._synced_at).total_seconds()
        return elapsed > settings.cache_ttl_meters_seconds

    @property
    def freshness_iso(self) -> str:
        if not self._synced_at:
            return datetime.now(timezone.utc).isoformat()
        return self._synced_at.isoformat()

    async def ensure_synced(self, client: UrjaPortalClient, force: bool = False) -> None:
        """Ensures that in-memory cache is populated and fresh."""
        if settings.environment.lower() in ("test", "testing"):
            return

        if not self.is_stale and not force:
            return

        async with self._lock:
            # Double-check inside lock
            if not self.is_stale and not force:
                return

            logger.info("Synchronizing meter and transformer data from upstream portal...")
            raw_meters = await client.fetch_all_meters_export()
            raw_dts = await client.fetch_all_transformers()

            new_meters: Dict[str, MeterDetail] = {}
            new_transformers: Dict[str, Transformer] = {}
            dt_map: Dict[str, List[str]] = {}

            # Process transformers
            for dt_item in raw_dts:
                code = dt_item.get("code")
                if not code:
                    continue
                new_transformers[code] = Transformer(
                    code=code,
                    name=dt_item.get("name", ""),
                    feeder_code=dt_item.get("feederCode", ""),
                    capacity_kva=int(dt_item.get("capacityKva", 0)),
                    meter_count=0
                )
                dt_map[code] = []

            # Process meters
            for item in raw_meters:
                m_id = item.get("meterId")
                if not m_id:
                    continue

                # Parse hierarchy
                hier_raw = item.get("hierarchy", {})
                meter_hier: Optional[MeterHierarchy] = None
                if hier_raw:
                    meter_hier = MeterHierarchy(
                        zone=HierarchyNode(
                            name=hier_raw.get("zone", {}).get("name", ""),
                            code=hier_raw.get("zone", {}).get("code", "")
                        ),
                        circle=HierarchyNode(
                            name=hier_raw.get("circle", {}).get("name", ""),
                            code=hier_raw.get("circle", {}).get("code", "")
                        ),
                        division=HierarchyNode(
                            name=hier_raw.get("division", {}).get("name", ""),
                            code=hier_raw.get("division", {}).get("code", "")
                        ),
                        subdivision=HierarchyNode(
                            name=hier_raw.get("subdivision", {}).get("name", ""),
                            code=hier_raw.get("subdivision", {}).get("code", "")
                        ),
                        substation=HierarchyNode(
                            name=hier_raw.get("substation", {}).get("name", ""),
                            code=hier_raw.get("substation", {}).get("code", "")
                        ),
                        feeder=HierarchyNode(
                            name=hier_raw.get("feeder", {}).get("name", ""),
                            code=hier_raw.get("feeder", {}).get("code", "")
                        ),
                        dt=HierarchyNode(
                            name=hier_raw.get("dt", {}).get("name", ""),
                            code=hier_raw.get("dt", {}).get("code", "")
                        )
                    )

                # Parse coordinates
                geo_raw = item.get("geo")
                geo_coords: Optional[GeoCoordinates] = None
                if geo_raw and geo_raw.get("lat") is not None and geo_raw.get("lng") is not None:
                    try:
                        geo_coords = GeoCoordinates(
                            latitude=float(geo_raw["lat"]),
                            longitude=float(geo_raw["lng"])
                        )
                    except (ValueError, TypeError):
                        geo_coords = None

                dt_code = item.get("dtCode", "")
                detail = MeterDetail(
                    meter_id=m_id,
                    serial_no=item.get("serialNo", ""),
                    make=item.get("make", ""),
                    phase_type=item.get("phaseType", ""),
                    install_status=item.get("installStatus", ""),
                    install_type=item.get("installType"),
                    build=item.get("build"),
                    dt_code=dt_code,
                    geo=geo_coords,
                    hierarchy=meter_hier
                )
                new_meters[m_id] = detail

                # Link meter to DT
                if dt_code in dt_map:
                    dt_map[dt_code].append(m_id)
                else:
                    dt_map[dt_code] = [m_id]

            # Update meter counts on transformers
            for dt_code, m_ids in dt_map.items():
                if dt_code in new_transformers:
                    new_transformers[dt_code].meter_count = len(m_ids)

            self._meters = new_meters
            self._transformers = new_transformers
            self._dt_to_meter_ids = dt_map
            self._synced_at = datetime.now(timezone.utc)
            logger.info(
                f"Sync completed successfully. Cached {len(self._meters)} meters "
                f"and {len(self._transformers)} distribution transformers."
            )

    def get_meter(self, meter_id: str) -> Optional[MeterDetail]:
        return self._meters.get(meter_id)

    def query_meters(
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
    ) -> Tuple[List[MeterListItem], int]:
        """Filters, sorts, and paginates meter records in memory."""
        results = list(self._meters.values())

        # 1. Text Search across meterId, serialNo, dtCode
        if search:
            q = search.lower().strip()
            results = [
                m for m in results
                if q in m.meter_id.lower() or q in m.serial_no.lower() or q in m.dt_code.lower()
            ]

        # 2. Attribute Filters
        if make:
            results = [m for m in results if m.make.lower() == make.lower()]
        if phase_type:
            results = [m for m in results if m.phase_type.lower() == phase_type.lower()]
        if status:
            results = [m for m in results if m.install_status.lower() == status.lower()]
        if install_type:
            results = [
                m for m in results
                if m.install_type and m.install_type.lower() == install_type.lower()
            ]
        if dt_code:
            results = [m for m in results if m.dt_code.lower() == dt_code.lower()]

        # 3. Sorting
        reverse = (sort_order.lower() == "desc")
        if hasattr(MeterDetail, sort_by):
            results.sort(key=lambda m: getattr(m, sort_by) or "", reverse=reverse)
        else:
            results.sort(key=lambda m: m.meter_id, reverse=reverse)

        total = len(results)

        # 4. Pagination
        start = (page - 1) * limit
        end = start + limit
        paginated = results[start:end]

        # Cast to MeterListItem (excludes full hierarchy tree for list efficiency)
        items = [
            MeterListItem(
                meter_id=m.meter_id,
                serial_no=m.serial_no,
                make=m.make,
                phase_type=m.phase_type,
                install_status=m.install_status,
                install_type=m.install_type,
                build=m.build,
                dt_code=m.dt_code,
                geo=m.geo
            )
            for m in paginated
        ]

        return items, total

    def query_transformers(
        self,
        search: Optional[str] = None,
        feeder_code: Optional[str] = None,
        sort_by: str = "code",
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Transformer], int]:
        """Filters, sorts, and paginates distribution transformer records."""
        results = list(self._transformers.values())

        if search:
            q = search.lower().strip()
            results = [r for r in results if q in r.code.lower() or q in r.name.lower()]

        if feeder_code:
            results = [r for r in results if r.feeder_code.lower() == feeder_code.lower()]

        reverse = (sort_order.lower() == "desc")
        if hasattr(Transformer, sort_by):
            results.sort(key=lambda t: getattr(t, sort_by) or "", reverse=reverse)
        else:
            results.sort(key=lambda t: t.code, reverse=reverse)

        total = len(results)
        start = (page - 1) * limit
        end = start + limit
        return results[start:end], total

    def get_transformer_detail(self, code: str) -> Optional[TransformerDetail]:
        """Returns transformer along with attached meter records."""
        t = self._transformers.get(code)
        if not t:
            return None

        attached_meter_ids = self._dt_to_meter_ids.get(code, [])
        attached_meters = [
            MeterListItem(
                meter_id=m.meter_id,
                serial_no=m.serial_no,
                make=m.make,
                phase_type=m.phase_type,
                install_status=m.install_status,
                install_type=m.install_type,
                build=m.build,
                dt_code=m.dt_code,
                geo=m.geo
            )
            for m_id in attached_meter_ids
            if (m := self._meters.get(m_id)) is not None
        ]

        return TransformerDetail(
            code=t.code,
            name=t.name,
            feeder_code=t.feeder_code,
            capacity_kva=t.capacity_kva,
            meter_count=len(attached_meters),
            meters=attached_meters
        )

    def get_summary(self) -> OperationalSummary:
        """Computes system-wide operational metrics and distributions."""
        status_counts: Dict[str, int] = {}
        make_counts: Dict[str, int] = {}
        phase_counts: Dict[str, int] = {}
        install_type_counts: Dict[str, int] = {}
        build_counts: Dict[str, int] = {}

        for m in self._meters.values():
            status_counts[m.install_status] = status_counts.get(m.install_status, 0) + 1
            make_counts[m.make] = make_counts.get(m.make, 0) + 1
            phase_counts[m.phase_type] = phase_counts.get(m.phase_type, 0) + 1
            if m.install_type:
                install_type_counts[m.install_type] = install_type_counts.get(m.install_type, 0) + 1
            if m.build:
                build_counts[m.build] = build_counts.get(m.build, 0) + 1

        return OperationalSummary(
            total_meters=len(self._meters),
            total_transformers=len(self._transformers),
            status_breakdown=status_counts,
            make_breakdown=make_counts,
            phase_breakdown=phase_counts,
            install_type_breakdown=install_type_counts,
            build_breakdown=build_counts,
            freshness=self.freshness_iso
        )

    def get_hierarchy_summary(self) -> ElectricalHierarchySummary:
        """Reconstructs the hierarchical tree representation of the electrical grid."""
        zones: Dict[str, HierarchyTreeNode] = {}
        unique_zones = set()
        unique_circles = set()
        unique_divisions = set()
        unique_subdivisions = set()
        unique_substations = set()
        unique_feeders = set()
        unique_dts = set()

        for m in self._meters.values():
            if not m.hierarchy:
                continue
            h = m.hierarchy
            z_code = h.zone.code
            unique_zones.add(z_code)
            unique_circles.add(h.circle.code)
            unique_divisions.add(h.division.code)
            unique_subdivisions.add(h.subdivision.code)
            unique_substations.add(h.substation.code)
            unique_feeders.add(h.feeder.code)
            unique_dts.add(h.dt.code)

            if z_code not in zones:
                zones[z_code] = HierarchyTreeNode(name=h.zone.name, code=z_code, meter_count=0)
            zones[z_code].meter_count += 1

        return ElectricalHierarchySummary(
            total_zones=len(unique_zones),
            total_circles=len(unique_circles),
            total_divisions=len(unique_divisions),
            total_subdivisions=len(unique_subdivisions),
            total_substations=len(unique_substations),
            total_feeders=len(unique_feeders),
            total_dts=len(unique_dts),
            total_meters=len(self._meters),
            tree=list(zones.values())
        )


cache_repository = CacheRepository()
