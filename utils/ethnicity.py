"""Ethnicity mapping utilities."""

from typing import List


ETH_MAP_NUM_TO_NAME = {
    0: "NorthenEuropean",
    1: "MediteranianHispanic",
    2: "NorthAfricanMiddleEastern",
    3: "AfricanCaribean",
    4: "Asian",
    5: "SouthEastAsian",
    6: "PacificIslander",
    7: "NativeAmerican",
    8: "NativeAustralian",
    9: "MixedRace",
    10: "EastAsian",
    11: "Unknown",
}

ETH_MAP_NAME_TO_NUM = {v.lower(): k for k, v in ETH_MAP_NUM_TO_NAME.items()}


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


def eth_show(v: int) -> str:
    """Show ethnicity with pretty name."""
    nm = ETH_MAP_NUM_TO_NAME.get(v, "Unknown")
    pretty = " ".join([w for w in split_camel(nm)]).strip()
    return f"{pretty} ({v})"


def eth_parse(s: str) -> int:
    """Parse ethnicity from string."""
    s2 = s.strip().lower().replace("_", " ").replace("-", " ")
    if s2.isdigit():
        return int(s2)
    s3 = s2.replace(" ", "")
    for k, v in ETH_MAP_NAME_TO_NUM.items():
        kk = k.replace(" ", "")
        if kk == s3:
            return v
    if s2 in ETH_MAP_NAME_TO_NUM:
        return ETH_MAP_NAME_TO_NUM[s2]
    raise ValueError("Ethnicity tidak valid (pakai angka atau nama).")
