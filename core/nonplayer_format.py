"""Non-player (staff/people) record format for FMM26.

Reverse-engineered from db_archive_2623/non_players.dat.

File layout:
  8 bytes header  (03 01 74 61 64 2e 01 00)
  4 bytes i32 LE  record count
  count x non_player records

Each record is exactly 39 bytes:
  uid            i32  person UID (references people.dat)
  unknown_a      u16
  unknown_b      u16
  home_rep       u16  Home reputation     (0..10000)
  world_rep      u16  World reputation    (0..10000)
  current_rep    u16  Current reputation  (0..10000)
  25 x u8 skill/role attributes (typical range 0..20)

All multi-byte integers are little-endian. Roundtrip is byte-exact: every
field is read and written back in order with no padding, so unknown/opaque
fields are preserved verbatim.
"""

from dataclasses import dataclass, field
from typing import List
from .binary import ReaderEx, WriterEx

# Names of the 25 single-byte skill/attribute fields (from the GUI editor
# NonPlayerModel property list). Order follows the editor's declaration order.
SKILL_NAMES = [
    "AttackFormation",
    "Attacking",
    "Business",
    "Coaching",
    "CoachingGoalkeepers",
    "DefendFormation",
    "Directness",
    "Discipline",
    "FreeRoles",
    "JudgingAbility",
    "JudgingPotential",
    "ManManagement",
    "Marking",
    "Motivating",
    "Offside",
    "Physiotherapy",
    "PlayingStyleDepth",
    "PlayingStyleFlex",
    "PlayingStyleFluid",
    "PlayingStyleTempo",
    "PlayingStyleWidth",
    "PreferredFormation",
    "Pressing",
    "Tactics",
    "Youngsters",
]

RECORD_SIZE = 39


@dataclass
class NonPlayerRec:
    """A single non-player record (39 bytes on disk)."""

    uid: int
    unknown_a: int
    unknown_b: int
    home_rep: int
    world_rep: int
    current_rep: int
    skills: List[int] = field(default_factory=lambda: [0] * 25)

    @staticmethod
    def read(r: ReaderEx) -> "NonPlayerRec":
        uid = r.read_i32()
        unknown_a = r.read_u16()
        unknown_b = r.read_u16()
        home_rep = r.read_u16()
        world_rep = r.read_u16()
        current_rep = r.read_u16()
        skills = [r.read_u8() for _ in range(25)]
        return NonPlayerRec(
            uid=uid,
            unknown_a=unknown_a,
            unknown_b=unknown_b,
            home_rep=home_rep,
            world_rep=world_rep,
            current_rep=current_rep,
            skills=skills,
        )

    def write(self, w: WriterEx):
        w.write_i32(self.uid)
        w.write_u16(self.unknown_a)
        w.write_u16(self.unknown_b)
        w.write_u16(self.home_rep)
        w.write_u16(self.world_rep)
        w.write_u16(self.current_rep)
        for v in self.skills:
            w.write_u8(v)

    def as_dict(self) -> dict:
        """Human-readable mapping with named skill fields."""
        d = {
            "uid": self.uid,
            "unknown_a": self.unknown_a,
            "unknown_b": self.unknown_b,
            "home_rep": self.home_rep,
            "world_rep": self.world_rep,
            "current_rep": self.current_rep,
        }
        for name, val in zip(SKILL_NAMES, self.skills):
            d[name] = val
        return d