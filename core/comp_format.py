"""Reverse-engineered binary record formats for FMM26 competition data files.

Decodes rivalries.dat and awards.dat.

rivalries.dat (count = 1683):
    header: 8 bytes magic (03 01 74 61 64 2e 01 00)
    count:  i32
    pad:    6 bytes (0x00 0x00 0xb9 0x79 0x02 0x00)
    records: each is
        name:          string (i32 length + utf8 bytes)
        terminator:    u8 (0xff)
        team_one:      i32  (club id)
        team_two:      i32  (club id)
        reputation:    u8
        team_one_wins: i16
        team_one_losses: i16
        team_one_draws: i16
        team_one_unbeaten_streak: i16
        team_two_unbeaten_streak: i16
        winning_streak: i16
        losing_streak: i16
        index:         i32  (1-based record ordinal)
        known:         i32  (opaque / date / extra)
    The last record in the archive is truncated: it ends after the
    stat fields (missing the trailing index/known i32).  It is read
    leniently (the two trailing i32 are optional and default to None).

awards.dat (count = 1116):
    header: 8 bytes magic (03 01 74 61 64 2e 01 00)
    count:  i32
    records: each is
        id:          i32
        uid:         i32
        name:        string (i32 length + utf8 bytes)
        ff:          u8 (0xff)
        name_short:  string (i32 length + utf8 bytes)
        ff:          u8 (0xff)
        body:        102 bytes, structured as:
            header (23 bytes):
                comp_type:   i16  (competition grouping code)
                run_by:      i16  (competition id; -1 for world awards)
                based_rule:  i16  (competition level / rule)
                type:        u8   (award category)
                recipient_type: u8  (1=player, 7=team, 2=manager)
                date_rule:   u8
                unknown:     u8
                unknown:     5 bytes
                number_of_placings: u8
                position:    u8
                unknown:     u8
                specific_date: i16 (year, e.g. 1900 default / 2025)
                min_age:     u8
                max_age:     u8
                unknown:     u8
            placings: 3 x 26 bytes:
                uid:   i32 (person/place reference)
                club:  i32
                year:  i16
                place: i16
                points:i16
                pad:   12 bytes (0xff)
            trailing: u8 (flags)
"""

import struct
from dataclasses import dataclass, field
from typing import List, Optional

from .binary import ReaderEx, WriterEx


@dataclass
class RivalryRec:
    """Rivalry between two clubs."""
    name: str
    team_one: int
    team_two: int
    reputation: int
    team_one_wins: int
    team_one_losses: int
    team_one_draws: int
    team_one_unbeaten_streak: int
    team_two_unbeaten_streak: int
    winning_streak: int
    losing_streak: int
    index: Optional[int] = None
    known: Optional[int] = None

    @staticmethod
    def read(r: ReaderEx) -> "RivalryRec":
        name = r.read_string()
        r.read_u8()  # 0xff terminator
        team_one = r.read_i32()
        team_two = r.read_i32()
        reputation = r.read_u8()
        t1w = r.read_i16()
        t1l = r.read_i16()
        t1d = r.read_i16()
        t1u = r.read_i16()
        t2u = r.read_i16()
        wst = r.read_i16()
        lst = r.read_i16()
        index = None
        known = None
        try:
            index = r.read_i32()
            known = r.read_i32()
        except EOFError:
            pass
        return RivalryRec(
            name=name, team_one=team_one, team_two=team_two,
            reputation=reputation,
            team_one_wins=t1w, team_one_losses=t1l, team_one_draws=t1d,
            team_one_unbeaten_streak=t1u, team_two_unbeaten_streak=t2u,
            winning_streak=wst, losing_streak=lst,
            index=index, known=known,
        )

    def write(self, w: WriterEx):
        w.write_string(self.name)
        w.write_u8(0xFF)
        w.write_i32(self.team_one)
        w.write_i32(self.team_two)
        w.write_u8(self.reputation)
        w.write_i16(self.team_one_wins)
        w.write_i16(self.team_one_losses)
        w.write_i16(self.team_one_draws)
        w.write_i16(self.team_one_unbeaten_streak)
        w.write_i16(self.team_two_unbeaten_streak)
        w.write_i16(self.winning_streak)
        w.write_i16(self.losing_streak)
        if self.index is not None:
            w.write_i32(self.index)
        if self.known is not None:
            w.write_i32(self.known)


@dataclass
class AwardPlacing:
    """A single award placing (winner) entry (26 bytes)."""
    uid: int
    club: int
    year: int
    place: int
    points: int
    pad: bytes = b"\xff" * 12

    @staticmethod
    def read(r: ReaderEx) -> "AwardPlacing":
        uid = r.read_i32()
        club = r.read_i32()
        year = r.read_i16()
        place = r.read_i16()
        points = r.read_i16()
        pad = r.read_bytes(12)
        return AwardPlacing(uid, club, year, place, points, pad)

    def write(self, w: WriterEx):
        w.write_i32(self.uid)
        w.write_i32(self.club)
        w.write_i16(self.year)
        w.write_i16(self.place)
        w.write_i16(self.points)
        w.write_bytes((self.pad or b"\xff" * 12))


@dataclass
class AwardRec:
    """Award record."""
    id: int
    uid: int
    name: str
    name_short: str
    comp_type: int
    run_by: int
    based_rule: int
    type: int
    recipient_type: int
    date_rule: int
    unknown: int
    unknown5: bytes
    number_of_placings: int
    position: int
    unknown_b: int
    specific_date: int
    min_age: int
    max_age: int
    unknown_c: int
    placings: List[AwardPlacing]
    trailing: int

    @staticmethod
    def read(r: ReaderEx) -> "AwardRec":
        ident = r.read_i32()
        uid = r.read_i32()
        name = r.read_string()
        r.read_u8()  # 0xff
        name_short = r.read_string()
        r.read_u8()  # 0xff

        comp_type = r.read_i16()
        run_by = r.read_i16()
        based_rule = r.read_i16()
        type_ = r.read_u8()
        recipient = r.read_u8()
        date_rule = r.read_u8()
        unknown = r.read_u8()
        unknown5 = r.read_bytes(5)
        nplac = r.read_u8()
        position = r.read_u8()
        unknown_b = r.read_u8()
        specific_date = r.read_i16()
        min_age = r.read_u8()
        max_age = r.read_u8()
        unknown_c = r.read_u8()

        placings = [AwardPlacing.read(r) for _ in range(3)]
        trailing = r.read_u8()
        return AwardRec(
            id=ident, uid=uid, name=name, name_short=name_short,
            comp_type=comp_type, run_by=run_by, based_rule=based_rule,
            type=type_, recipient_type=recipient, date_rule=date_rule,
            unknown=unknown, unknown5=unknown5,
            number_of_placings=nplac, position=position, unknown_b=unknown_b,
            specific_date=specific_date, min_age=min_age, max_age=max_age,
            unknown_c=unknown_c,
            placings=placings, trailing=trailing,
        )

    def write(self, w: WriterEx):
        w.write_i32(self.id)
        w.write_i32(self.uid)
        w.write_string(self.name)
        w.write_u8(0xFF)
        w.write_string(self.name_short)
        w.write_u8(0xFF)

        w.write_i16(self.comp_type)
        w.write_i16(self.run_by)
        w.write_i16(self.based_rule)
        w.write_u8(self.type)
        w.write_u8(self.recipient_type)
        w.write_u8(self.date_rule)
        w.write_u8(self.unknown)
        w.write_bytes(self.unknown5 if self.unknown5 else b"\x00" * 5)
        w.write_u8(self.number_of_placings)
        w.write_u8(self.position)
        w.write_u8(self.unknown_b)
        w.write_i16(self.specific_date)
        w.write_u8(self.min_age)
        w.write_u8(self.max_age)
        w.write_u8(self.unknown_c)

        for p in self.placings:
            p.write(w)
        w.write_u8(self.trailing)