"""Unified PersonDetailModel display for FMM Tool.

When a user opens a person, this renders that person's *entire* footprint in
one place: people + player + contract + loan(s) + injury(s) + ban(s) +
future transfer + retirement + career history + staff role (official/coach/
physio/scout) + non-player + relationships + languages.

It reuses the existing block helpers from ``ui/display.py`` for the people
and player stats sections, and adds lightweight section renderers for the
extended data. Every renderer follows the project's rich-vs-plain pattern:
``if RICH_AVAILABLE: Table/Panel else: print``.

Lookups use the UID (or array-index) indexes built once at load by
``App._build_person_indexes`` — O(1), no list scans.
"""

from typing import TYPE_CHECKING, Optional, List

from .console import RICH_AVAILABLE, console, print_info
from .display import show_people_block, show_player_block, rel_list
from ..utils.date import describe_date

if TYPE_CHECKING:
    from ..core.app import App
    from ..core.models import People, Player


# ---------------------------------------------------------------------------
# small formatting helpers
# ---------------------------------------------------------------------------
def _date(raw: int) -> str:
    """Packed FMM date -> human string via the shared describe_date helper."""
    return describe_date(raw) if raw is not None else "-"


def _club_name(app: "App", club_id: int) -> str:
    """Resolve a club id to a name, or '-' if unset."""
    if club_id is None or club_id < 0:
        return "-"
    c = app.club_by_eff_id.get(club_id)
    return c.full_name if c else f"#{club_id}"


def _wage(app: "App", wage: int) -> str:
    """Format a wage with thousands separators."""
    return f"{wage:,}" if wage is not None else "-"


def _section_title(title: str, style: str = "bold cyan"):
    """Print a section header (rich or plain)."""
    if RICH_AVAILABLE:
        console.print(f"\n[{style}]{title}[/{style}]")
    else:
        print(f"\n{title}")


# ---------------------------------------------------------------------------
# section renderers (each takes app + the resolved record(s))
# ---------------------------------------------------------------------------
def _show_contract(app: "App", p: "People"):
    rec = app.contracts_by_uid.get(p.uid)
    if rec is None:
        _section_title("📝 Contract")
        print_info("  (none)")
        return
    _section_title("📝 Contract")
    rows = [
        ("Club", f"{_club_name(app, rec.club_id)} ({rec.club_id})"),
        ("Wage", _wage(app, rec.wage)),
        ("Contract type", str(rec.contract_type)),
        ("Start", _date(rec.start_date)),
        ("End", _date(rec.end_date)),
    ]
    _print_kv(rows)


def _show_loans(app: "App", p: "People"):
    recs = app.loans_by_uid.get(p.uid, [])
    _section_title("🔁 Loan(s)")
    if not recs:
        print_info("  (none)")
        return
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.box import SIMPLE_HEAVY
        t = Table(box=SIMPLE_HEAVY, border_style="blue", padding=(0, 1))
        t.add_column("#", style="bold green", justify="center", width=3)
        t.add_column("Club", style="cyan")
        t.add_column("Wage%", style="white", justify="right")
        t.add_column("Start", style="white")
        t.add_column("End", style="white")
        for i, rec in enumerate(recs, 1):
            t.add_row(str(i), _club_name(app, rec.club_id),
                      str(rec.wage_percentage), _date(rec.start_date),
                      _date(rec.end_date))
        console.print(t)
    else:
        for i, rec in enumerate(recs, 1):
            print(f"  {i}. {_club_name(app, rec.club_id)} | wage%={rec.wage_percentage}"
                  f" | {_date(rec.start_date)}..{_date(rec.end_date)}")


def _show_injuries(app: "App", p: "People"):
    recs = app.injuries_by_uid.get(p.uid, [])
    _section_title("🤕 Injury(s)")
    if not recs:
        print_info("  (none)")
        return
    rows = []
    for i, rec in enumerate(recs, 1):
        rows.append((f"[{i}]", f"class={rec.injury_class} type={rec.injury_type}"
                     f" side={rec.side} | {_date(rec.start_date)}..{_date(rec.end_date)}"))
    _print_kv(rows)


def _show_bans(app: "App", p: "People"):
    recs = app.bans_by_uid.get(p.uid, [])
    _section_title("🚫 Ban(s)")
    if not recs:
        print_info("  (none)")
        return
    rows = []
    for i, rec in enumerate(recs, 1):
        rows.append((f"[{i}]", f"type={rec.ban_type} | {_date(rec.start_date)}..{_date(rec.end_date)}"))
    _print_kv(rows)


def _show_transfer(app: "App", p: "People"):
    recs = app.transfers_by_uid.get(p.uid, [])
    _section_title("🔄 Future Transfer(s)")
    if not recs:
        print_info("  (none)")
        return
    rows = []
    for i, rec in enumerate(recs, 1):
        rows.append((f"[{i}]", f"{_club_name(app, rec.from_club)} -> "
                     f"{_club_name(app, rec.to_club)} | fee={rec.transfer_fee:,}"
                     f" | {_date(rec.transfer_date)}"))
    _print_kv(rows)


def _show_retirement(app: "App", p: "People"):
    rec = app.retirements_by_uid.get(p.uid)
    _section_title("🏁 Retirement")
    if rec is None:
        print_info("  (none)")
        return
    _print_kv([("Date", _date(rec.retirement_date)), ("Reason", str(rec.reason))])


def _show_history(app: "App", p: "People"):
    phs = app.history_by_uid.get(p.uid, [])
    _section_title("📜 Career History")
    if not phs:
        print_info("  (none)")
        return
    total = 0
    for ph in phs:
        # seasons includes the terminator block (season_index == -1)
        played = [s for s in ph.seasons if s.season_index != -1]
        total += len(played)
    print_info(f"  {total} season(s) recorded.")
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.box import SIMPLE_HEAVY
        t = Table(box=SIMPLE_HEAVY, border_style="blue", padding=(0, 1))
        t.add_column("#", style="bold green", justify="center", width=3)
        t.add_column("Club", style="cyan")
        t.add_column("Flags", style="white")
        t.add_column("Date", style="white")
        t.add_column("Season", style="white", justify="right")
        i = 0
        for ph in phs:
            for s in ph.seasons:
                i += 1
                t.add_row(str(i), _club_name(app, s.club_uid),
                          f"0x{s.flags:08X}", _date(s.date_field),
                          str(s.season_index))
        console.print(t)
    else:
        i = 0
        for ph in phs:
            for s in ph.seasons:
                i += 1
                print(f"  {i}. {_club_name(app, s.club_uid)} | flags=0x{s.flags:08X}"
                      f" | {_date(s.date_field)} | season={s.season_index}")


def _show_staff(app: "App", p: "People", idx: int):
    """Staff roles. officials is keyed by UID; coaches/physios/scouts by the
    person's array index (their `id` field stores the array index, not UID)."""
    shown = False
    off = app.officials_by_uid.get(p.uid)
    if off:
        _section_title("👔 Official")
        _print_kv([
            ("Type", str(off.official_type)),
            ("Rep (cur/home/world)", f"{off.rep_current}/{off.rep_home}/{off.rep_world}"),
            ("Record UID", str(off.record_uid)),
        ])
        shown = True
    coach = app.coaches_by_idx.get(idx)
    if coach:
        _section_title("🧑‍🏫 Coach")
        _print_kv([("Attrs", f"{coach.attr1}/{coach.attr2}/{coach.attr3}")])
        shown = True
    physio = app.physios_by_idx.get(idx)
    if physio:
        _section_title("💉 Physio")
        _print_kv([("Attrs", f"{physio.attr1}/{physio.attr2}/{physio.attr3}")])
        shown = True
    scout = app.scouts_by_idx.get(idx)
    if scout:
        _section_title("🔍 Scout")
        _print_kv([("Attrs", f"{scout.attr1}/{scout.attr2}/{scout.attr3}")])
        shown = True
    if not shown:
        _section_title("👔 Staff Role")
        print_info("  (none)")


def _show_nonplayer(app: "App", p: "People"):
    rec = app.nonplayers_by_uid.get(p.uid)
    _section_title("🧠 Non-Player")
    if rec is None:
        print_info("  (none)")
        return
    _print_kv([
        ("Rep (home/world/current)",
         f"{rec.home_rep}/{rec.world_rep}/{rec.current_rep}"),
    ])
    # skills labeled via SKILL_NAMES
    try:
        from ..core.nonplayer_format import SKILL_NAMES
    except Exception:
        SKILL_NAMES = None
    rows = []
    for i, val in enumerate(rec.skills):
        label = SKILL_NAMES[i] if SKILL_NAMES and i < len(SKILL_NAMES) else f"skill[{i}]"
        rows.append((label, str(val)))
    _print_kv(rows)


def _show_languages(app: "App", p: "People"):
    _section_title("🗣️ Languages")
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.box import SIMPLE_HEAVY
        t = Table(box=SIMPLE_HEAVY, border_style="blue", padding=(0, 1))
        t.add_column("#", style="bold green", justify="center", width=3)
        t.add_column("Language", style="cyan")
        t.add_column("Proficiency", style="white", justify="right")
        t.add_column("Type", style="dim")
        i = 0
        for lid, prof in p.default_languages:
            i += 1
            t.add_row(str(i), app.lang_name(lid), str(prof), "default")
        for lid, prof in p.other_languages:
            i += 1
            t.add_row(str(i), app.lang_name(lid), str(prof), "other")
        console.print(t)
    else:
        i = 0
        for lid, prof in p.default_languages:
            i += 1
            print(f"  {i}. {app.lang_name(lid)} (prof={prof}) [default]")
        for lid, prof in p.other_languages:
            i += 1
            print(f"  {i}. {app.lang_name(lid)} (prof={prof}) [other]")


# ---------------------------------------------------------------------------
# shared key/value table printer
# ---------------------------------------------------------------------------
def _print_kv(rows: List[tuple]):
    """Render a list of (label, value) rows, rich or plain."""
    if not rows:
        return
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.box import SIMPLE
        t = Table(box=SIMPLE, show_header=False, padding=(0, 1))
        t.add_column("Field", style="cyan", width=26)
        t.add_column("Value", style="white")
        for label, val in rows:
            t.add_row(str(label), str(val))
        console.print(t)
    else:
        for label, val in rows:
            print(f"  {label}: {val}")


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------
def show_person_detail(app: "App", p: "People", pl: "Optional[Player]" = None,
                       idx: "Optional[int]" = None):
    """Render the full unified person footprint.

    Args:
        app: loaded App.
        p: the People record to display.
        pl: the matching Player record (may be None for non-players/officials).
        idx: the people array index (needed to resolve coaches/physios/scouts,
             whose ``id`` field stores the person array index, not a UID).
             If None, the staff-indexed sections are skipped.
    """
    # 1. People + player stats (reuse existing block helpers).
    if idx is None:
        # recover the index from the UID index when caller omitted it
        idx = app.people_uid_index.get(p.uid, 0)
    show_people_block(app, p, idx)
    if pl:
        show_player_block(app, pl)
    else:
        print_info("PLAYER (tidak ditemukan untuk PlayerId di People)")

    # 2. Extended-data sections (UID-keyed indexes built at load).
    _show_contract(app, p)
    _show_loans(app, p)
    _show_injuries(app, p)
    _show_bans(app, p)
    _show_transfer(app, p)
    _show_retirement(app, p)
    _show_history(app, p)
    _show_staff(app, p, idx)
    _show_nonplayer(app, p)

    # 3. Embedded-in-people sections.
    _show_languages(app, p)
    _section_title("🔗 Relationships")
    rel_list(app, p)
