import os
import sys

# Configure test environment
os.environ["ENVIRONMENT"] = "test"

from datetime import datetime, timezone
from pathlib import Path
import pytest
from starlette.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import settings
settings.environment = "test"

from src.main import app
from src.repositories.cache_repository import CacheRepository, cache_repository
from src.clients.portal_client import UrjaPortalClient
from src.schemas.meter import GeoCoordinates, HierarchyNode, MeterDetail, MeterHierarchy
from src.schemas.transformer import Transformer


@pytest.fixture
def auth_headers():
    return {settings.api_key_header_name: settings.api_key_secret}


@pytest.fixture
def test_client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def mock_upstream_sync(monkeypatch):
    """Mocks upstream network calls so that test suite runs entirely offline and deterministically."""
    async def noop_sync(self, client, force=False):
        pass

    monkeypatch.setattr(CacheRepository, "ensure_synced", noop_sync)

    async def mock_fetch_energy(self, meter_id):
        return [
            {
                "timestamp": "23/06/2026 23:30",
                "kwh": "48438.74",
                "kvah": "52313.84",
                "voltR": "226"
            },
            {
                "timestamp": "24/06/2026 00:00",
                "kwh": "48440.10",
                "kvah": "52315.20",
                "voltR": "225"
            }
        ]

    monkeypatch.setattr(UrjaPortalClient, "fetch_meter_energy", mock_fetch_energy)


@pytest.fixture(autouse=True)
def populate_test_repository():
    """Populates cache_repository with clean, predictable test fixture data."""
    sample_meters = {
        "J100000": MeterDetail(
            meter_id="J100000",
            serial_no="SE33962",
            make="HPL",
            phase_type="single",
            install_status="Decommissioned",
            install_type="Whole Current",
            build="legacy",
            dt_code="DT-001",
            geo=GeoCoordinates(latitude=26.9389, longitude=75.8309),
            hierarchy=MeterHierarchy(
                zone=HierarchyNode(name="Jaipur Zone 1", code="Z-01"),
                circle=HierarchyNode(name="Circle 1", code="C-01"),
                division=HierarchyNode(name="Division 1", code="D-01"),
                subdivision=HierarchyNode(name="Subdivision 1", code="SD-01"),
                substation=HierarchyNode(name="Substation 1", code="SS-01"),
                feeder=HierarchyNode(name="Feeder 1", code="F-001"),
                dt=HierarchyNode(name="Malviya Nagar DT 1", code="DT-001")
            )
        ),
        "J100001": MeterDetail(
            meter_id="J100001",
            serial_no="SE33963",
            make="Genus",
            phase_type="three",
            install_status="Installed",
            install_type="CT Operated",
            build="v2",
            dt_code="DT-001",
            geo=GeoCoordinates(latitude=26.9400, longitude=75.8320),
            hierarchy=MeterHierarchy(
                zone=HierarchyNode(name="Jaipur Zone 1", code="Z-01"),
                circle=HierarchyNode(name="Circle 1", code="C-01"),
                division=HierarchyNode(name="Division 1", code="D-01"),
                subdivision=HierarchyNode(name="Subdivision 1", code="SD-01"),
                substation=HierarchyNode(name="Substation 1", code="SS-01"),
                feeder=HierarchyNode(name="Feeder 1", code="F-001"),
                dt=HierarchyNode(name="Malviya Nagar DT 1", code="DT-001")
            )
        ),
        "J100002": MeterDetail(
            meter_id="J100002",
            serial_no="SE33964",
            make="Secure",
            phase_type="single",
            install_status="Faulty",
            install_type="Whole Current",
            build="v2",
            dt_code="DT-002",
            geo=GeoCoordinates(latitude=26.9500, longitude=75.8400),
            hierarchy=MeterHierarchy(
                zone=HierarchyNode(name="Jaipur Zone 1", code="Z-01"),
                circle=HierarchyNode(name="Circle 1", code="C-01"),
                division=HierarchyNode(name="Division 1", code="D-01"),
                subdivision=HierarchyNode(name="Subdivision 1", code="SD-01"),
                substation=HierarchyNode(name="Substation 1", code="SS-01"),
                feeder=HierarchyNode(name="Feeder 2", code="F-002"),
                dt=HierarchyNode(name="Mansarovar DT 2", code="DT-002")
            )
        )
    }

    sample_transformers = {
        "DT-001": Transformer(
            code="DT-001",
            name="Malviya Nagar DT 1",
            feeder_code="F-001",
            capacity_kva=100,
            meter_count=2
        ),
        "DT-002": Transformer(
            code="DT-002",
            name="Mansarovar DT 2",
            feeder_code="F-002",
            capacity_kva=63,
            meter_count=1
        )
    }

    cache_repository._meters = sample_meters
    cache_repository._transformers = sample_transformers
    cache_repository._dt_to_meter_ids = {
        "DT-001": ["J100000", "J100001"],
        "DT-002": ["J100002"]
    }
    cache_repository._synced_at = datetime.now(timezone.utc)

    yield
