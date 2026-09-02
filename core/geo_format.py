"""Binary record formats for FMM26 geographic .dat files (city.dat, continent.dat).

Header (both files): 8 bytes ``03 01 74 61 64 2e 01 00`` then a 4-byte
little-endian i32 record count.

city.dat
--------
Each record is a FIXED 20-byte block (the count-7812th/last record in the
shipped file is truncated to 18 bytes, i.e. missing the trailing id i16):

    [0:4]   i32    name_ref    -- opaque, monotonic per-record value. The
                                 database is sorted by it. NOT plaintext and
                                 not decodable to a city name from the record
                                 alone (see report).
    [4:6]   u16    nation_marker -- small per-nation-group marker (0x00__).
    [6:10]  f32    latitude
    [10:14] f32    longitude
    [14:16] u16    region      -- opaque region/state field
    [16:18] u16    flags       -- high byte varies per group, low byte 0/1
    [18:20] i16    id          -- sequential 1..N (the primary key)

Continent.dat
-------------
Variable-length records:

    string   name      (i32 len + bytes)
    u32      color     (0x000003ff for the 6 full records)
    u8       unk       (always 0)
    bytes[3] abbr
    string   demonym   (i32 len + bytes)
    u8       unk2      (always 0)
    i16      id

The last "World" record in the shipped file is truncated: it carries the
name/color/unk/abbr but only 2 of the 4 demonym-length bytes, and lacks the
demonym/unk2/id. GeoRec.read() detects this and stores the leftover bytes in
``raw_tail`` so the record round-trips byte-identically.

Both readers use a "remaining bytes" check so a truncated record's partial
bytes are preserved (read_bytes() in ReaderEx would otherwise swallow them).
"""

import os
from dataclasses import dataclass

from .binary import ReaderEx, WriterEx

HEADER = b"\x03\x01tad\x2e\x01\x00"


def _remaining(r: ReaderEx) -> int:
    """Number of bytes left in the stream from the current position."""
    cur = r.tell()
    r.seek(0, os.SEEK_END)
    end = r.tell()
    r.seek(cur)
    return end - cur


@dataclass
class CityRec:
    """Fixed 20-byte city record (last shipped record is 18 bytes)."""

    name_ref: int
    nation_marker: int
    latitude: float
    longitude: float
    region: int
    flags: int
    id: int
    truncated: bool = False
    raw_tail: bytes = b""

    @staticmethod
    def read(r: ReaderEx) -> "CityRec":
        name_ref = r.read_i32()
        nation_marker = r.read_u16()
        lat = r.read_f32()
        lon = r.read_f32()
        region = r.read_u16()
        flags = r.read_u16()
        if _remaining(r) < 2:
            # truncated record (last one): only the id is missing.
            tail = r.read_bytes(_remaining(r))
            return CityRec(name_ref, nation_marker, lat, lon, region, flags,
                           0, True, tail)
        ident = r.read_i16()
        return CityRec(name_ref, nation_marker, lat, lon, region, flags, ident)

    def write(self, w: WriterEx):
        w.write_i32(self.name_ref)
        w.write_u16(self.nation_marker)
        w.write_f32(self.latitude)
        w.write_f32(self.longitude)
        w.write_u16(self.region)
        w.write_u16(self.flags)
        if not self.truncated:
            w.write_i16(self.id)
        w.write_bytes(self.raw_tail)


@dataclass
class ContinentRec:
    """Variable-length continent record (last "World" record is truncated)."""

    name: str
    color: int
    unk: int
    abbr: bytes
    demonym: str
    unk2: int
    id: int
    truncated: bool = False
    raw_tail: bytes = b""

    @staticmethod
    def read(r: ReaderEx) -> "ContinentRec":
        name = r.read_string()
        color = r.read_u32()
        unk = r.read_u8()
        abbr = r.read_bytes(3)
        if _remaining(r) < 4:
            # truncated record: not enough bytes for the demonym length prefix.
            tail = r.read_bytes(_remaining(r))
            return ContinentRec(name, color, unk, abbr, "", 0, 0, True, tail)
        demonym = r.read_string()
        unk2 = r.read_u8()
        ident = r.read_i16()
        return ContinentRec(name, color, unk, abbr, demonym, unk2, ident)

    def write(self, w: WriterEx):
        w.write_string(self.name)
        w.write_u32(self.color)
        w.write_u8(self.unk)
        w.write_bytes(self.abbr)
        if not self.truncated:
            w.write_string(self.demonym)
            w.write_u8(self.unk2)
            w.write_i16(self.id)
        w.write_bytes(self.raw_tail)