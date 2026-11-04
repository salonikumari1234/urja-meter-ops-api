import pytest
from src.repositories.cache_repository import cache_repository


def test_query_meters_search():
    items, total = cache_repository.query_meters(search="SE33962")
    assert total == 1
    assert items[0].meter_id == "J100000"


def test_query_meters_make_filter():
    items, total = cache_repository.query_meters(make="Genus")
    assert total == 1
    assert items[0].make == "Genus"


def test_query_meters_phase_filter():
    items, total = cache_repository.query_meters(phase_type="single")
    assert total == 2


def test_query_meters_status_filter():
    items, total = cache_repository.query_meters(status="Faulty")
    assert total == 1
    assert items[0].meter_id == "J100002"


def test_query_meters_pagination():
    items, total = cache_repository.query_meters(page=1, limit=2)
    assert len(items) == 2
    assert total == 3

    items_p2, total_p2 = cache_repository.query_meters(page=2, limit=2)
    assert len(items_p2) == 1
    assert total_p2 == 3


def test_query_transformers():
    items, total = cache_repository.query_transformers(search="DT-001")
    assert total == 1
    assert items[0].code == "DT-001"
    assert items[0].meter_count == 2


def test_get_transformer_detail():
    detail = cache_repository.get_transformer_detail("DT-001")
    assert detail is not None
    assert detail.code == "DT-001"
    assert len(detail.meters) == 2
    assert {m.meter_id for m in detail.meters} == {"J100000", "J100001"}


def test_get_summary():
    summary = cache_repository.get_summary()
    assert summary.total_meters == 3
    assert summary.total_transformers == 2
    assert summary.status_breakdown.get("Installed") == 1
    assert summary.status_breakdown.get("Faulty") == 1
    assert summary.status_breakdown.get("Decommissioned") == 1
