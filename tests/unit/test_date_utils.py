from datetime import datetime, timezone
import pytest
from src.utils.date_utils import format_iso_utc, parse_indian_datetime


def test_parse_indian_datetime_valid():
    dt = parse_indian_datetime("23/06/2026 23:30")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 6
    assert dt.day == 23
    assert dt.hour == 23
    assert dt.minute == 30
    assert dt.tzinfo == timezone.utc


def test_parse_indian_datetime_date_only():
    dt = parse_indian_datetime("23/06/2026")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 6
    assert dt.day == 23
    assert dt.hour == 0
    assert dt.minute == 0


def test_parse_indian_datetime_invalid():
    assert parse_indian_datetime("invalid-date") is None
    assert parse_indian_datetime("") is None
    assert parse_indian_datetime(None) is None


def test_format_iso_utc():
    dt = datetime(2026, 6, 23, 23, 30, tzinfo=timezone.utc)
    formatted = format_iso_utc(dt)
    assert formatted == "2026-06-23T23:30:00+00:00"
    assert format_iso_utc(None) is None
