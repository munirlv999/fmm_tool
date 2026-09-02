"""Binary format for FMM26 player_history.dat.

Reverse-engineered from FMM player_history.dat (~21 MB).

File layout (all multi-byte values little-endian):

    Offset  Size  Field
    0       8     file header (magic) = 03 01 74 61 64 2e 01 00
    8       4     i32 ``count``  (this file: 360)
    12      ...   "uid index" section

The uid index section is a list of ``i32 + u8`` entries (5 bytes each).  For
every entry the trailing u8 is 0; the u32 is a person UID.  The section ends
when a 5-byte-aligned position is reached whose u8 is non-zero (that byte
belongs to the next section).  In this database there are 105772 entries,
spanning bytes 12..528872.

Then the "history" section:

    bytes 528872..528877   region header (5 bytes) = 03 ff ff ff ff
    ...                    a run of 20-byte season blocks
    last 4 bytes           trailing terminator = ff ff ff ff

Each season block is 20 bytes = 5 x i32:

    i32  person_uid   (constant for all blocks of one player)
    i32  club_uid     (club / competition UID; preserved verbatim)
    i32  flags        (observed values: 0 or 0xffff0000; preserved verbatim)
    i32  date_field   (packed date / undecoded; preserved verbatim)
    i32  season_index (running season counter; value -1 marks the last block
                       of a player's history)

A single player's history is the maximal run of consecutive blocks sharing the
same ``person_uid`` and ending with a block whose ``season_index == -1``.
Across the whole database the blocks total 1033919, forming 105773 players.

The dataclasses below preserve every opaque/packed field as raw integers so a
read -> write cycle reproduces the file byte-for-byte.
"""

from dataclasses import dataclass, field
from typing import List
import struct

from .binary import ReaderEx, WriterEx

_HISTORY_HEADER = b"\x03\x01\x74\x61\x64\x2e\x01\x00"


@dataclass
class PlayerHistorySeason:
    """One 20-byte season block within a player's history.

    ``person_uid`` and ``season_index`` are structural; the three middle
    fields hold packed club / stats data whose exact meaning is not fully
    decoded, so they are preserved as raw unsigned 32-bit values.
    """

    person_uid: int
    club_uid: int
    flags: int
    date_field: int
    season_index: int

    @staticmethod
    def read(r: ReaderEx) -> "PlayerHistorySeason":
        # Bulk unpack: one 20-byte read + one struct.unpack instead of 5
        # separate read_i32() calls. At 1.03M blocks this cuts ~5M read+unpack
        # calls down to ~2M (one read_bytes + one unpack per block).
        person_uid, club_uid, flags, date_field, season_index = \
            struct.unpack("<iiiii", r.read_bytes(20))
        return PlayerHistorySeason(person_uid, club_uid, flags,
                                   date_field, season_index)

    def write(self, w: WriterEx):
        # Bulk pack to match the bulk read path (one pack + one write_bytes).
        w.write_bytes(struct.pack("<iiiii", self.person_uid, self.club_uid,
                                  self.flags, self.date_field,
                                  self.season_index))


@dataclass
class PlayerHistory:
    """One player's full career history.

    ``seasons`` is the list of 20-byte blocks for this player, *including* the
    final terminator block whose ``season_index == -1``.
    """

    person_uid: int
    seasons: List[PlayerHistorySeason] = field(default_factory=list)


@dataclass
class PlayerHistoryFile:
    """The whole player_history.dat file."""

    header: bytes
    count: int
    uid_index: List[int]
    region_b_header: bytes
    players: List[PlayerHistory]
    trailing: bytes

    @staticmethod
    def read(r: ReaderEx) -> "PlayerHistoryFile":
        header = r.read_bytes(8)
        count = r.read_i32()

        # --- uid index section -------------------------------------------
        # Each entry is u32 + u8; the u8 is always 0.  Stop when the 5-byte
        # aligned position runs into a non-zero u8 (start of history section).
        uid_index = []
        while not r.eof():
            pos = r.tell()
            uid = r.read_i32()
            b = r.read_u8()
            if b == 0:
                uid_index.append(uid)
            else:
                r.seek(pos)  # rewind; history section begins at pos
                break

        # --- history section ---------------------------------------------
        region_b_header = r.read_bytes(5)

        # Reserve the trailing 4 terminator bytes so the block loop stops.
        end = r.tell()
        r.seek(0, 2)
        file_end = r.tell()
        r.seek(end)
        data_end = file_end - 4

        players = []
        while r.tell() < data_end:
            seasons = []
            while True:
                s = PlayerHistorySeason.read(r)
                seasons.append(s)
                if s.season_index == -1:
                    break
            players.append(PlayerHistory(
                person_uid=seasons[0].person_uid, seasons=seasons))

        trailing = r.read_bytes(4)
        return PlayerHistoryFile(
            header=header,
            count=count,
            uid_index=uid_index,
            region_b_header=region_b_header,
            players=players,
            trailing=trailing,
        )

    def write(self, w: WriterEx):
        w.write_bytes(self.header if self.header else _HISTORY_HEADER)
        w.write_i32(self.count)
        for uid in self.uid_index:
            w.write_i32(uid)
            w.write_u8(0)
        w.write_bytes(self.region_b_header)
        for p in self.players:
            for s in p.seasons:
                s.write(w)
        w.write_bytes(self.trailing)