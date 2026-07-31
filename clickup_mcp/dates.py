"""Date / time conversion helpers.

ClickUp stores dates as Unix timestamps in *milliseconds*. Accepting raw
integers is error-prone for an LLM, so the public tools also accept ISO-8601
strings (and integer strings) which are converted here.
"""

from datetime import datetime, timezone


def parse_datetime_to_ms(value: int | str) -> int:
    """Convert a value to a Unix timestamp in milliseconds.

    Accepts:

    * an ``int`` (assumed to already be in milliseconds) - returned as-is;
    * a numeric string like ``"1700000000000"`` - parsed as an int;
    * an ISO-8601 datetime string such as ``"2026-08-15T09:00:00Z"`` or
      ``"2026-08-15 09:00:00+02:00"`` - converted to ms. Naive datetimes are
      assumed to be in UTC.

    Raises:
        ValueError: If the value cannot be parsed.
    """
    if isinstance(value, bool):  # bool is a subclass of int - reject it
        raise ValueError(f"Invalid date value: {value!r}")

    if isinstance(value, int):
        return value

    text = str(value).strip()
    if not text:
        raise ValueError("Empty date value")

    # Pure integer string -> already in milliseconds.
    if text.lstrip("-").isdigit():
        return int(text)

    # ISO-8601. ``datetime.fromisoformat`` (3.11+) accepts offsets; the replace
    # handles the trailing "Z" shorthand for older parsers.
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)
