"""FMM26 staff role .dat record formats.

Covers officials.dat, coaches.dat, physios.dat, scouts.dat.

Common physical layout of every file:

    offset 0 : 8-byte header  03 01 74 61 64 2e 01 00 ("\x03\x01tad.\x01\x00")
    offset 8 : 4-byte little-endian i32 record count
    offset 12: count records back to back, fixed size each.

    - coaches.dat  / physios.dat / scouts.dat  -> 7-byte records
    - officials.dat                            -> 99-byte records

All four files use an i32 count (verified: body length / record size is an exact
integer and records run precisely to EOF for every file).

Reuses ReaderEx / WriterEx from core.binary.
"""

import struct
from dataclasses import dataclass
from typing import Optional

from .binary import ReaderEx, WriterEx

HEADER = b"\x03\x01tad.\x01\x00"


# ---------------------------------------------------------------------------
# officials.dat : fixed 99-byte records
# ---------------------------------------------------------------------------
@dataclass
class OfficialRec:
    """One 99-byte official (referee) record.

    Field layout (byte offsets / sizes):
        idx          u32 @ 0   sequential row index 0..N-1
        person_uid   u32 @ 4   reference to the person record (distinct per official)
        record_uid   u32 @ 8   reference/manager uid (mostly sequential runs)
        rep_current  u16 @12   current reputation           (1..200)
        rep_home     u16 @14   home reputation              (1..200)
        rep_world    u16 @16   world reputation             (scaled)
        attrs        bytes[6] @18  six attribute bytes
        f24          u8  @24   flag (0/1)
        f25          u8  @25   flag (0/1)
        official_type u8 @26   official type/category (0..5)
        f27          u8  @27   reserved (0)
        f28          u8  @28   reserved (0)
        opaque       bytes[70] @29..98  variable-length middle run (contains
                                      0xFF retirement-date / free-role sentinel
                                      bytes) + 4 trailing zero bytes at 95..98

    The middle run (offset 29..94) begins with a constant 2-byte marker `6c 07`
    (u16 0x076c = 1900) and then a variable-length run of role-specific values
    terminated by 0xFF bytes. Because it is variable in content but the record
    is fixed at 99 bytes, it is preserved verbatim as `opaque`.
    """

    idx: int
    person_uid: int
    record_uid: int
    rep_current: int
    rep_home: int
    rep_world: int
    attrs: bytes
    f24: int
    f25: int
    official_type: int
    f27: int
    f28: int
    opaque: bytes

    @classmethod
    def read(cls, r: ReaderEx) -> "OfficialRec":
        rec = cls(
            idx=r.read_u32(),
            person_uid=r.read_u32(),
            record_uid=r.read_u32(),
            rep_current=r.read_u16(),
            rep_home=r.read_u16(),
            rep_world=r.read_u16(),
            attrs=r.read_bytes(6),
            f24=r.read_u8(),
            f25=r.read_u8(),
            official_type=r.read_u8(),
            f27=r.read_u8(),
            f28=r.read_u8(),
            opaque=r.read_bytes(70),
        )
        return rec

    def write(self, w: WriterEx):
        w.write_u32(self.idx)
        w.write_u32(self.person_uid)
        w.write_u32(self.record_uid)
        w.write_u16(self.rep_current)
        w.write_u16(self.rep_home)
        w.write_u16(self.rep_world)
        if len(self.attrs) != 6:
            raise ValueError("official attrs must be 6 bytes")
        w.write_bytes(self.attrs)
        w.write_u8(self.f24)
        w.write_u8(self.f25)
        w.write_u8(self.official_type)
        w.write_u8(self.f27)
        w.write_u8(self.f28)
        if len(self.opaque) != 70:
            raise ValueError("official opaque must be 70 bytes")
        w.write_bytes(self.opaque)

    OFFICIAL_SIZE = 99


# ---------------------------------------------------------------------------
# coaches.dat / physios.dat / scouts.dat : fixed 7-byte records
# ---------------------------------------------------------------------------
@dataclass
class StaffRec:
    """One 7-byte staff role record (coach / physio / scout).

    Field layout:
        id      u32 @0  person id (sequential run; 0xFFFFFFFF = -1 marks a
                        deleted/empty person slot, which is why ids are not
                        perfectly contiguous).
        attr1   u8  @4  role attribute
        attr2   u8  @5  role attribute
        attr3   u8  @6  role attribute

    Observation ranges per role (whole file):
        coaches: attr1 1..7, attr2 1..3, attr3 1..3
        physios: attr1 1..2, attr2 1..3, attr3 1..3
        scouts : attr1 1..4, attr2 1..3, attr3 1..3
    """

    id: int
    attr1: int
    attr2: int
    attr3: int

    @classmethod
    def read(cls, r: ReaderEx) -> "StaffRec":
        return cls(id=r.read_u32(), attr1=r.read_u8(), attr2=r.read_u8(), attr3=r.read_u8())

    def write(self, w: WriterEx):
        w.write_u32(self.id)
        w.write_u8(self.attr1)
        w.write_u8(self.attr2)
        w.write_u8(self.attr3)

    STAFF_SIZE = 7


# Aliases with semantically distinct names for clarity.
CoachRec = StaffRec
PhysioRec = StaffRec
ScoutRec = StaffRec


# ---------------------------------------------------------------------------
# Container helpers
# ---------------------------------------------------------------------------
def read_records(path: str, rec_cls, rec_size: int, expected_size: Optional[int] = None):
    """Read header + count + all records from a staff .dat file."""
    with open(path, "rb") as f:
        raw = f.read()
    hdr = raw[:8]
    if hdr != HEADER:
        raise ValueError(f"{path}: unexpected header {hdr.hex()}")
    count = struct.unpack("<I", raw[8:12])[0]
    body = raw[12:]
    if len(body) != count * rec_size:
        raise ValueError(
            f"{path}: body {len(body)} != count*{rec_size}={count*rec_size}"
        )
    r = ReaderEx(__import__("io").BytesIO(body))
    recs = [rec_cls.read(r) for _ in range(count)]
    if expected_size is not None and len(recs) != expected_size:
        raise ValueError(f"{path}: got {len(recs)} records, expected {expected_size}")
    return hdr, count, recs


def write_records(hdr: bytes, recs, rec_cls, rec_size: int) -> bytes:
    """Serialize header + count + records back to bytes."""
    import io
    buf = io.BytesIO()
    w = WriterEx(buf)
    w.write_bytes(hdr)
    w.write_i32(len(recs))
    for rec in recs:
        rec.write(w)
    return buf.getvalue()


def verify_roundtrip(path: str, rec_cls, rec_size: int) -> bool:
    """Return True if a read-then-write cycle reproduces the file byte-for-byte."""
    with open(path, "rb") as f:
        original = f.read()
    hdr, count, recs = read_records(path, rec_cls, rec_size)
    rebuilt = write_records(hdr, recs, rec_cls, rec_size)
    return rebuilt == original
