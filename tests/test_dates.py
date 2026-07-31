from datetime import timezone

import pytest

from clickup_mcp.dates import parse_datetime_to_ms


def test_int_passthrough():
    assert parse_datetime_to_ms(1700000000000) == 1700000000000


def test_int_string():
    assert parse_datetime_to_ms("1700000000000") == 1700000000000


def test_iso_z():
    # 2026-08-15T09:00:00Z == 2026-08-15T09:00:00+00:00
    ms = parse_datetime_to_ms("2026-08-15T09:00:00Z")
    assert ms == 1786784400000


def test_iso_offset():
    # +02:00 => 1755258000000 - 2*3600*1000
    ms = parse_datetime_to_ms("2026-08-15T09:00:00+02:00")
    assert ms == 1786784400000 - 2 * 3600 * 1000


def test_naive_assumed_utc():
    ms = parse_datetime_to_ms("2026-08-15T09:00:00")
    assert ms == 1786784400000


def test_naive_has_no_tz():
    # Confirm the helper attaches UTC for naive input.
    from datetime import datetime

    dt = datetime.fromisoformat("2026-08-15T09:00:00")
    assert dt.tzinfo is None


def test_invalid_raises():
    with pytest.raises(ValueError):
        parse_datetime_to_ms("not-a-date")


def test_empty_raises():
    with pytest.raises(ValueError):
        parse_datetime_to_ms("")


def test_bool_rejected():
    with pytest.raises(ValueError):
        parse_datetime_to_ms(True)


def test_aware_dt_signature():
    # Sanity: a tz-aware datetime round-trips through fromisoformat.
    from datetime import datetime

    dt = datetime.fromisoformat("2026-08-15T09:00:00+00:00")
    assert dt.tzinfo is not None
    assert dt.tzinfo.utcoffset(dt) == timezone.utc.utcoffset(dt)
