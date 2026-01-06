from datetime import datetime, UTC


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
