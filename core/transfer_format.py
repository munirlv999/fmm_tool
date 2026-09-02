"""FMM26 starting_* .dat binary record formats.

Reverse-engineered from the real FMM26 database. Each file shares the same
8-byte header ``03 01 74 61 64 2e 01 00`` followed by a 4-byte little-endian
i32 record count (verified: every file's count parses to an exact multiple of
the record size at EOF; starting_contracts count 111742 exceeds i16 range so
all six files definitively use i32).

Date encoding: packed i32 ``(year << 16) | dayOfYear``. A year of 1900
(0x076C) is used as the "no date / unset" sentinel for start dates.

Opaque/unknown fields are preserved as raw bytes so that a read -> write
roundtrip is byte-identical.
"""

from dataclasses import dataclass, field
from typing import List
from .binary import ReaderEx, WriterEx

HEADER = bytes.fromhex("03 01 74 61 64 2e 01 00")


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------
def unpack_fmm_date(packed: int):
    """Split a packed FMM date into (year, dayOfYear)."""
    day = packed & 0xFFFF
    year = packed >> 16
    return year, day


def pack_fmm_date(year: int, day: int) -> int:
    return ((year & 0xFFFF) << 16) | (day & 0xFFFF)


# ---------------------------------------------------------------------------
# FutureTransfer  (starting_transfers.dat) -- 54 bytes
#   person_id      i32  [ 0]
#   from_club      i32  [ 4]   (may be -1)
#   to_club        i32  [ 8]
#   reserved       i32  [12]   (always 0)
#   transfer_date  i32  [16]   packed date
#   future_date    i32  [20]   packed date
#   fee_kind       i16  [24]   (always 1 in dump)
#   transfer_fee   i32  [26]
#   opaque         bytes[24]   [30..53]  (wage/clauses; 0xFF unset)
# ---------------------------------------------------------------------------
@dataclass
class FutureTransferRec:
    person_id: int
    from_club: int
    to_club: int
    reserved: int
    transfer_date: int
    future_date: int
    fee_kind: int
    transfer_fee: int
    opaque: bytes = field(default=b"\xff" * 24)

    @classmethod
    def read(cls, r: ReaderEx) -> "FutureTransferRec":
        return cls(
            r.read_i32(), r.read_i32(), r.read_i32(), r.read_i32(),
            r.read_i32(), r.read_i32(), r.read_i16(), r.read_i32(),
            r.read_bytes(24),
        )

    def write(self, w: WriterEx):
        w.write_i32(self.person_id)
        w.write_i32(self.from_club)
        w.write_i32(self.to_club)
        w.write_i32(self.reserved)
        w.write_i32(self.transfer_date)
        w.write_i32(self.future_date)
        w.write_i16(self.fee_kind)
        w.write_i32(self.transfer_fee)
        w.write_bytes(self.opaque)


# ---------------------------------------------------------------------------
# Retirement  (starting_retirements.dat) -- 9 bytes
#   person_id       i32 [0]
#   retirement_date i32 [4]  packed date
#   reason          u8  [8]
# ---------------------------------------------------------------------------
@dataclass
class RetirementRec:
    person_id: int
    retirement_date: int
    reason: int

    @classmethod
    def read(cls, r: ReaderEx) -> "RetirementRec":
        return cls(r.read_i32(), r.read_i32(), r.read_u8())

    def write(self, w: WriterEx):
        w.write_i32(self.person_id)
        w.write_i32(self.retirement_date)
        w.write_u8(self.reason)


# ---------------------------------------------------------------------------
# StartingBan  (starting_bans.dat) -- 26 bytes
#   person_id    i32 [ 0]
#   ban_type     u8  [ 4]
#   unknown1     i32 [ 5]   (0xFFFFFFFF unset)
#   unknown2     i32 [ 9]   (0xFFFFFFFF or ban value, e.g. 145509/150783)
#   unknown3     i32 [13]   (0xFFFFFFFF unset)
#   start_date   i32 [17]   packed date
#   end_date     i32 [21]   packed date
#   unknown_tail u8  [25]
# ---------------------------------------------------------------------------
@dataclass
class StartingBanRec:
    person_id: int
    ban_type: int
    unknown1: int
    unknown2: int
    unknown3: int
    start_date: int
    end_date: int
    unknown_tail: int

    @classmethod
    def read(cls, r: ReaderEx) -> "StartingBanRec":
        return cls(
            r.read_i32(), r.read_u8(), r.read_i32(), r.read_i32(), r.read_i32(),
            r.read_i32(), r.read_i32(), r.read_u8(),
        )

    def write(self, w: WriterEx):
        w.write_i32(self.person_id)
        w.write_u8(self.ban_type)
        w.write_i32(self.unknown1)
        w.write_i32(self.unknown2)
        w.write_i32(self.unknown3)
        w.write_i32(self.start_date)
        w.write_i32(self.end_date)
        w.write_u8(self.unknown_tail)


# ---------------------------------------------------------------------------
# StartingInjury  (starting_injuries.dat) -- 23 bytes
#   person_id     i32 [ 0]
#   injury_class  i32 [ 4]   (small codes, e.g. 28)
#   injury_type   u16 [ 8]   (e.g. 0x0A22 = 2594)
#   start_date    i32 [10]   packed date (1900 sentinel = no start)
#   end_date      i32 [14]   packed date
#   side          u16 [18]
#   b20           u8  [20]
#   b21           u8  [21]
#   b22           u8  [22]
# ---------------------------------------------------------------------------
@dataclass
class StartingInjuryRec:
    person_id: int
    injury_class: int
    injury_type: int
    start_date: int
    end_date: int
    side: int
    b20: int
    b21: int
    b22: int

    @classmethod
    def read(cls, r: ReaderEx) -> "StartingInjuryRec":
        return cls(
            r.read_i32(), r.read_i32(), r.read_u16(), r.read_i32(), r.read_i32(),
            r.read_u16(), r.read_u8(), r.read_u8(), r.read_u8(),
        )

    def write(self, w: WriterEx):
        w.write_i32(self.person_id)
        w.write_i32(self.injury_class)
        w.write_u16(self.injury_type)
        w.write_i32(self.start_date)
        w.write_i32(self.end_date)
        w.write_u16(self.side)
        w.write_u8(self.b20)
        w.write_u8(self.b21)
        w.write_u8(self.b22)


# ---------------------------------------------------------------------------
# StartingContract  (starting_contracts.dat) -- 54 bytes
#   person_id      i32  [ 0]
#   club_id        i32  [ 4]
#   opaque8        bytes[ 8]  [8..15]  (0xFF unset - value/release clause)
#   start_date     i32  [16]   packed date
#   end_date       i32  [20]   packed date
#   contract_type  u16  [24]
#   wage           u32  [26]
#   opaque24       bytes[30]   [30..53]  (0xFF unset)
# ---------------------------------------------------------------------------
@dataclass
class StartingContractRec:
    person_id: int
    club_id: int
    opaque8: bytes
    start_date: int
    end_date: int
    contract_type: int
    wage: int
    opaque24: bytes

    @classmethod
    def read(cls, r: ReaderEx) -> "StartingContractRec":
        return cls(
            r.read_i32(), r.read_i32(), r.read_bytes(8),
            r.read_i32(), r.read_i32(), r.read_u16(), r.read_u32(),
            r.read_bytes(24),
        )

    def write(self, w: WriterEx):
        w.write_i32(self.person_id)
        w.write_i32(self.club_id)
        w.write_bytes(self.opaque8)
        w.write_i32(self.start_date)
        w.write_i32(self.end_date)
        w.write_u16(self.contract_type)
        w.write_u32(self.wage)
        w.write_bytes(self.opaque24)


# ---------------------------------------------------------------------------
# StartingLoan  (starting_loans.dat) -- 26 bytes
#   person_id        i32  [ 0]
#   club_id          i32  [ 4]   (loaning club)
#   start_date       i32  [ 8]   packed date
#   end_date         i32  [12]   packed date
#   wage_percentage  u16  [16]   (100, 356, 0)
#   opaque           bytes[ 8]   [18..25]  (0xFF unset)
# ---------------------------------------------------------------------------
@dataclass
class StartingLoanRec:
    person_id: int
    club_id: int
    start_date: int
    end_date: int
    wage_percentage: int
    opaque: bytes = field(default=b"\xff" * 8)

    @classmethod
    def read(cls, r: ReaderEx) -> "StartingLoanRec":
        return cls(
            r.read_i32(), r.read_i32(), r.read_i32(), r.read_i32(),
            r.read_u16(), r.read_bytes(8),
        )

    def write(self, w: WriterEx):
        w.write_i32(self.person_id)
        w.write_i32(self.club_id)
        w.write_i32(self.start_date)
        w.write_i32(self.end_date)
        w.write_u16(self.wage_percentage)
        w.write_bytes(self.opaque)


# ---------------------------------------------------------------------------
# Whole-file load / save (8-byte header + i32 count + records)
# ---------------------------------------------------------------------------
def load_file(path: str, rec_type):
    """Read a whole starting_*.dat file into a list of records."""
    with open(path, "rb") as f:
        r = ReaderEx(f)
        header = r.read_bytes(8)
        assert header == HEADER, f"unexpected header for {path}: {header.hex()}"
        count = r.read_i32()
        items = []
        for _ in range(count):
            items.append(rec_type.read(r))
        # verify we consumed exactly EOF
        assert r.eof(), f"trailing bytes after {count} records in {path}"
        return header, count, items


def save_file(path: str, header: bytes, items: List, rec_type):
    """Write a whole starting_*.dat file back out."""
    def _write(f):
        w = WriterEx(f)
        w.write_bytes(header)
        w.write_i32(len(items))
        for it in items:
            it.write(w)
    tmp = path + ".roundtrip_tmp"
    with open(tmp, "wb") as f:
        _write(f)
    import os
    os.replace(tmp, path)