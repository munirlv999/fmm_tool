"""General helper utilities."""

import os
from typing import List, Optional


def norm_space(s: str) -> str:
    """Normalize whitespace."""
    return " ".join(s.strip().split())


def lower_norm(s: str) -> str:
    """Normalize and lowercase."""
    return norm_space(s).lower()


def bool_parse(s: str) -> bool:
    """Parse boolean from string."""
    low = s.strip().lower()
    if low in ("1", "true", "yes", "y", "on"):
        return True
    if low in ("0", "false", "no", "n", "off"):
        return False
    raise ValueError("Gunakan 1/0 atau true/false")


def bytes_to_hex(b: bytes) -> str:
    """Convert bytes to uppercase hex."""
    return b.hex().upper()


def hex_to_bytes(s: str, expect_len: Optional[int] = None) -> bytes:
    """Convert hex string to bytes."""
    h = s.strip().replace(" ", "").replace("0x", "").upper()
    if len(h) % 2 != 0:
        h = "0" + h
    b = bytes.fromhex(h)
    if expect_len is not None and len(b) != expect_len:
        raise ValueError(f"Panjang bytes harus {expect_len}, sekarang {len(b)}.")
    return b


def split_camel(s: str) -> List[str]:
    """Split camelCase string."""
    out, cur = [], ""
    for ch in s:
        if ch.isupper() and cur:
            out.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def clear_screen():
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


# Club status mapping
CLUB_STATUS_MAP = {
    0: "National",
    1: "Professional",
    2: "Semi Pro",
    3: "Amateur",
    22: "Unknown",
}


def club_status_show(v: int) -> str:
    """Show club status with name."""
    name = CLUB_STATUS_MAP.get(v, "Unknown")
    return f"{name} ({v})"
