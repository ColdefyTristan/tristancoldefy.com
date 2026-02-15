from datetime import datetime, UTC
from zoneinfo import ZoneInfo


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


PARIS = ZoneInfo("Europe/Paris")


def today_paris_date():
    return datetime.now(PARIS).date()
