"""High-level database operations: global UID rename + player transfer.

This replaces the missing ``fmm_ops.py`` :class:`Squad` used by the older
patched editor. The two operations here touch the real database files and sync
every reference that points at a person UID, verified against the live DB:

  UID references (renamed on rename_uid):
    people.dat                     p.uid (the record itself)
    players.dat                    pl.uid
    starting_contracts.dat         person_id
    starting_loans.dat             person_id
    starting_bans.dat              person_id
    starting_transfers.dat         person_id
    starting_injuries.dat          person_id
    starting_retirements.dat       person_id
    officials/coaches/physios/scouts.dat  person_uid   (NOT record_uid)
    people.dat relationships       rel.uid  (other people pointing at this person)
    people_to_always_load_*.dat    the uid list

  NOT touched (they index people by array position, not UID):
    non_players.dat uid, player_history.dat person_uid/uid_index,
    officials.record_uid, clubs_to_always_load_*.dat
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app import App

from .binary import AlwaysLoadList, DatList
from .transfer_format import StartingContractRec
from .models import People

# (app_attr, person-id field) for every list that stores a *person UID*.
_UID_LISTS = [
    ("starting_transfers", "person_id"),
    ("starting_retirements", "person_id"),
    ("starting_bans", "person_id"),
    ("starting_injuries", "person_id"),
    ("starting_contracts", "person_id"),
    ("starting_loans", "person_id"),
]

# staff files keep the person ref in ``person_uid`` (record_uid is an index).
# Only officials uses a real person UID; coaches/physios/scouts encode the
# person array index in ``id``, so they must NOT be rewritten on a UID change.
_STAFF_LISTS = ["officials"]


def _attr_file(app: "App", attr: str) -> str:
    return os.path.join(app.data_dir, f"{attr}.dat")


def _rename_in_person_id_list(app: "App", attr: str, old: int, new: int) -> int:
    """Rewrite ``person_id`` in one extended list. Returns count rewritten."""
    dat = getattr(app, attr, None)
    if dat is None:
        return 0
    n = 0
    for rec in dat.items:
        if getattr(rec, "person_id") == old:
            rec.person_id = new
            n += 1
    if n:
        setattr(app, f"dirty_{attr}", True)
    return n


def _rename_in_staff_list(app: "App", attr: str, old: int, new: int) -> int:
    dat = getattr(app, attr, None)
    if dat is None:
        return 0
    n = 0
    for rec in dat.items:
        if getattr(rec, "person_uid") == old:
            rec.person_uid = new
            n += 1
    if n:
        setattr(app, f"dirty_{attr}", True)
    return n


def _rename_in_always_load(app: "App", filename: str, old: int, new: int) -> int:
    path = os.path.join(app.data_dir, filename)
    if not os.path.exists(path):
        return 0
    al = AlwaysLoadList.load(path)
    n = 0
    for i, v in enumerate(al.items):
        if v == old:
            al.items[i] = new
            n += 1
    if n:
        al.save_overwrite()
    return n


def rename_uid(app: "App", old_uid: int, new_uid: int) -> "dict":
    """Rename a person UID across every file that references it.

    Returns a dict of {file -> count rewritten} for reporting.
    """
    report = {}

    # 1. people.dat — the record itself
    pidx = app.people_uid_index.get(old_uid)
    if pidx is None:
        raise ValueError(f"UID {old_uid} tidak ditemukan di people.dat")
    p = app.people.items[pidx]
    p.uid = new_uid
    del app.people_uid_index[old_uid]
    app.people_uid_index[new_uid] = pidx
    app.dirty_people = True
    report["people.dat"] = 1

    # 2. players.dat — player record uid (same person)
    pl = app.player_by_id.get(p.player_id)
    if pl is not None:
        pl.uid = new_uid
        app.dirty_players = True
        report["players.dat"] = 1

    # 3. person_id in the six starting_* lists, and staff person_uid
    rp = {}
    for attr, _ in _UID_LISTS:
        c = _rename_in_person_id_list(app, attr, old_uid, new_uid)
        if c:
            rp[f"{attr}.dat"] = c
    for attr in _STAFF_LISTS:
        c = _rename_in_staff_list(app, attr, old_uid, new_uid)
        if c:
            rp[f"{attr}.dat"] = c
    report.update(rp)

    # 4. relationships in people.dat that point at this person
    rel_c = 0
    for pers in app.people.items:
        for rel in pers.relationships:
            if rel.uid == old_uid:
                rel.uid = new_uid
                rel_c += 1
    if rel_c:
        app.dirty_people = True
    report["relationships"] = rel_c

    # 5. people_to_always_load_*.dat
    for fn in ("people_to_always_load_male.dat", "people_to_always_load_female.dat"):
        c = _rename_in_always_load(app, fn, old_uid, new_uid)
        if c:
            report[fn] = c

    return {k: v for k, v in report.items() if v}


def transfer_player(app: "App", p: People, target_club_id: int, wage: int,
                    years: int, squad_number: int = 0) -> None:
    """Move a player to another club, syncing contract data.

    - Sets ``p.club_id`` (roster membership is derived from club_id).
    - Updates the player's ``starting_contracts.dat`` record (or appends one).
    - ``years`` = contract length; the contract ends 30 June of that year.
    """
    from .transfer_format import pack_fmm_date

    old_club_id = p.club_id
    p.club_id = target_club_id
    app.dirty_people = True

    # player squad number lives on the Player record
    pl = app.player_by_id.get(p.player_id)
    if pl is not None and squad_number:
        pl.squad_number = squad_number
        app.dirty_players = True

    # Sync the club roster: club.players stores PEOPLE.ID (array index), not
    # the person UID and not the Player.id. This is what drives the Club
    # column in the official FMM26.Editor, so keep old/new clubs consistent.
    if target_club_id != old_club_id:
        old = app.club_by_eff_id.get(old_club_id)
        new = app.club_by_eff_id.get(target_club_id)
        if old is not None and p.id in old.players:
            old.players.remove(p.id)
            app.dirty_clubs = True
        if new is not None and p.id not in new.players:
            new.players.append(p.id)
            app.dirty_clubs = True

    # contract: end 30 June `years` from now (FMM contract convention)
    from datetime import date
    end_year = date.today().year + years
    end_date = pack_fmm_date(end_year, 180)  # dayOfYear 180 ~ 30 June (approx)

    contracts = getattr(app, "starting_contracts", None)
    if contracts is None:
        return

    found = None
    for rec in contracts.items:
        if rec.person_id == p.uid:
            found = rec
            break

    if found is not None:
        found.club_id = target_club_id
        found.wage = wage
        found.end_date = end_date
    else:
        contracts.items.append(StartingContractRec(
            person_id=p.uid, club_id=target_club_id, opaque8=b"\xff" * 8,
            start_date=0, end_date=end_date, contract_type=0, wage=wage,
            opaque24=b"\xff" * 24,
        ))
    app.dirty_starting_contracts = True