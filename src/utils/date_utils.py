from datetime import datetime, timezone
from typing import Optional


def parse_indian_datetime(dt_str: str) -> Optional[datetime]:
    """
    Parses dates in 'DD/MM/YYYY HH:MM' or 'DD/MM/YYYY' format into UTC datetimes.
    """
    if not dt_str or not isinstance(dt_str, str):
        return None
    dt_str = dt_str.strip()
    try:
        # Check standard DD/MM/YYYY HH:MM
        dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    try:
        # Check date-only DD/MM/YYYY
        dt = datetime.strptime(dt_str, "%d/%m/%Y")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    try:
        # Fallback to standard ISO format
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def format_iso_utc(dt: Optional[datetime]) -> Optional[str]:
    """Formats a datetime as standard ISO-8601 string with UTC indicator."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()
