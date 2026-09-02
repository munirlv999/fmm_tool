"""Date utilities for packed i32 date format."""

import datetime
from typing import Optional


def _to_i16(u16: int) -> int:
    """Convert unsigned 16-bit to signed."""
    return u16 - 0x10000 if (u16 & 0x8000) else u16


def decode_packed_date_i32(raw: int) -> Optional[datetime.date]:
    """Decode packed i32 to date."""
    if raw == -1:
        return None
    u = raw & 0xFFFFFFFF
    stored_day = _to_i16(u & 0xFFFF)
    year = _to_i16((u >> 16) & 0xFFFF)
    if stored_day == -1 or year == -1 or year <= 0:
        return None
    try:
        base = datetime.date(year, 1, 1)
        return base + datetime.timedelta(days=stored_day)
    except Exception:
        return None


def pack_date_to_i32(d: Optional[datetime.date]) -> int:
    """Pack date to i32."""
    if d is None:
        return -1
    stored_day = d.timetuple().tm_yday - 1
    year = d.year
    u = ((year & 0xFFFF) << 16) | (stored_day & 0xFFFF)
    return u - 0x100000000 if (u & 0x80000000) else u


def parse_date_or_int32(s: str) -> int:
    """Parse date string or int."""
    s = s.strip()
    if s.lower() in ("null", "none", ""):
        return -1
    if "-" in s:
        y, m, d = s.split("-")
        dt = datetime.date(int(y), int(m), int(d))
        return pack_date_to_i32(dt)
    return int(s)


def describe_date(raw: int) -> str:
    """Get string representation of packed date."""
    dt = decode_packed_date_i32(raw)
    return "-" if dt is None else dt.isoformat()


# Alias for compatibility
date_to_int32 = pack_date_to_i32
