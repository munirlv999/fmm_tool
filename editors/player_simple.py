"""Player editor - Termux friendly version."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.app import App

from ..core.constants import PEOPLE_FIELDS, PLAYER_FIELDS
from ..core.models import People, Player, Relationship
from ..ui.console import (
    RICH_AVAILABLE, console, print_header, print_success, 
    print_error, print_warning, print_info, get_input, clear_screen,
    show_numbered_list, show_help_text, wait_enter
)
from ..utils.date import parse_date_or_int32, date_to_int32
from ..utils.ethnicity import eth_parse
from ..utils.helpers import lower_norm


def show_help_player():
    """Show help for player editor."""
    sections = [
        ("CARI PLAYER", [
            "[nama]      : Cari nama (flexible, partial match)",
            "[UID]       : Cari by UID langsung (angka)",
            "[c]         : Cari semua pemain di Club",
            "Contoh: 'messi', '37076007', atau 'c' lalu 'manchester'"
        ]),
        ("NAVIGASI LIST HASIL", [
            "1-50        : Pilih item nomor X",
            "98          : Next page (halaman berikutnya)",
            "99          : Prev page (halaman sebelumnya)",
            "0           : Back / Batal"
        ]),
        ("MENU DETAIL PLAYER", [
            "1           : Edit player",
            "2           : Cari player lain",
            "d           : Duplicate player (buat copy)",
            "t           : Transfer ke klub lain (sync kontrak)",
            "u           : Ganti UID global (sync semua referensi)",
            "0           : Back ke menu utama"
        ]),
        ("EDIT FIELD", [
            "[no] [val]  : Edit field nomor X dengan value Y",
            "g           : Apply GACOR preset (auto 200 CA/PA, dll)",
            "r           : Edit favourites/relationships",
            "l           : Edit languages (default & other)",
            "0           : Selesai edit / back",
            "",
            "Contoh edit:",
            "  25 200    : Ubah CA jadi 200",
            "  26 190    : Ubah PA jadi 190",
            "  6 12345   : Ubah NationId jadi 12345",
            "  g         : Apply preset gacor"
        ]),
        ("KEY STATS (nomor field)", [
            "People Fields (1-20):",
            "  2=FirstName  3=LastName  6=NationId",
            "  7=OtherNats  10=Type     19=ClubId",
            "",
            "Player Fields (21+):",
            "  21=CA  22=PA",
            "  23=Finishing  24=Dribbling  25=Pace  26=Technique",
            "  27=Crossing  28=Passing  29=Tackling  30=Heading",
            "  31=Strength  32=Stamina  33=Jumping  34=Decision  35=Aggression"
        ]),
        ("RELATIONSHIP EDIT", [
            "1           : Add relationship",
            "2           : Delete relationship",
            "0           : Back",
            "",
            "Format add: strength type unknown target_uid reason",
            "Contoh: '50 1 3 12345 2'",
            "type: 1=Favourite 2=Disliked 3=Rival 4=Friendly (best-effort)"
        ]),
        ("LANGUAGE EDIT", [
            "1           : Add default language",
            "2           : Add other language",
            "3           : Edit strength",
            "4           : Delete",
            "0           : Back",
            "",
            "Pemilihan bahasa: masukkan ID atau cari via nama"
        ])
    ]
    show_help_text("👤 PLAYER EDITOR", sections)


def get_display_name(app: "App", p: People) -> str:
    """Get display name for people."""
    return app.people_display_name(p)


def search_people(app: "App", query: str) -> list:
    """Search people by name."""
    if not query:
        return []
    
    q = lower_norm(query)
    results = []
    
    for idx, p in enumerate(app.people.items):
        name = lower_norm(get_display_name(app, p))
        if q in name or all(word in name for word in q.split()):
            results.append((idx, p))
    
    return results


def search_players_by_club(app: "App", club_id: int) -> list:
    """Search all players in a specific club.
    
    Returns list of (people_idx, people, player) tuples.
    """
    results = []
    
    for idx, p in enumerate(app.people.items):
        # Check if person belongs to this club
        if p.club_id == club_id:
            # Find associated player record
            pl = app.player_by_id.get(p.player_id)
            if pl:
                results.append((idx, p, pl))
    
    return results


def get_next_uid(app: "App") -> int:
    """Get next available UID."""
    max_uid = max((p.uid for p in app.people.items), default=2000000000)
    return max_uid + 1


def get_next_people_id(app: "App") -> int:
    """Get next available People ID (same logic as C#)."""
    if not app.people.items:
        return 0
    return max((p.id for p in app.people.items), default=-1) + 1


def get_next_player_id(app: "App") -> int:
    """Get next available Player ID (same logic as C#)."""
    if not app.players.items:
        return 0
    return max((p.id for p in app.players.items), default=-1) + 1


def duplicate_player(app: "App", source_p: People) -> tuple:
    """
    Duplicate a player (people + player record).
    Returns (new_people, new_player) if successful, (None, None) if failed.
    """
    clear_screen()
    print_header(f"📋 DUPLICATE: {get_display_name(app, source_p)}")
    
    # Check if source has player record
    source_pl = app.player_by_id.get(source_p.player_id)
    if not source_pl:
        print_warning("Orang ini bukan player (tidak ada player record)!")
        wait_enter()
        return False
    
    print_info(f"Source: UID={source_p.uid}, PlayerID={source_p.player_id}")
    print_info("Data yang akan dicopy:")
    print(f"  - People data (nama, nation, club, dll)")
    print(f"  - Player stats (CA={source_pl.ca}, PA={source_pl.pa}, dll)")
    print("")
    
    print_info("\nOpsi:")
    print("  [y] Duplicate & Edit sekarang")
    print("  [n] Batal")
    confirm = get_input("Pilih", "bold yellow")
    if confirm.lower() != 'y':
        print_warning("Dibatalkan")
        wait_enter()
        return None, None
    
    try:
        # Create new People record
        new_uid = get_next_uid(app)
        new_people_id = get_next_people_id(app)
        new_player_id = get_next_player_id(app)
        
        # Copy people data
        new_p = People(
            id=new_people_id,
            uid=new_uid,
            first_name_id=source_p.first_name_id,
            last_name_id=source_p.last_name_id,
            common_name_id=source_p.common_name_id,
            dob_raw=source_p.dob_raw,
            nation_id=source_p.nation_id,
            other_nationalities=list(source_p.other_nationalities),
            ethnicity=source_p.ethnicity,
            ptype=source_p.ptype,
            national_caps=0,  # Reset stats for new player
            national_goals=0,
            national_u21_caps=0,
            national_u21_goals=0,
            club_id=-1,  # Free agent
            joined_raw=0,
            adaptability=source_p.adaptability,
            ambition=source_p.ambition,
            controversy=source_p.controversy,
            loyality=source_p.loyality,
            pressure=source_p.pressure,
            professionalism=source_p.professionalism,
            sportmanship=source_p.sportmanship,
            temperament=source_p.temperament,
            player_id=-1,  # Will be set after creating player
            default_languages=list(source_p.default_languages),
            other_languages=list(source_p.other_languages),
            relationships=[],  # New player has no relationships
            unknown1=source_p.unknown1,
            unknown_date=source_p.unknown_date,
            unknown3=source_p.unknown3,
            unknown6b=source_p.unknown6b,
            unknown6c=source_p.unknown6c,
            unknown6d=source_p.unknown6d,
            unknown6e=source_p.unknown6e,
            unknown6f=source_p.unknown6f,
            unknown7=source_p.unknown7,
            unknown8=source_p.unknown8,
            unknown9=source_p.unknown9,
            unknown10=source_p.unknown10,
            unknown21=source_p.unknown21
        )
        
        # Create new Player record
        new_pl = Player(
            id=new_player_id,
            uid=new_uid,
            crossing=source_pl.crossing,
            dribbling=source_pl.dribbling,
            tackling=source_pl.tackling,
            finishing=source_pl.finishing,
            longshot=source_pl.longshot,
            heading=source_pl.heading,
            jumping=source_pl.jumping,
            passing=source_pl.passing,
            decision=source_pl.decision,
            unselfishness=source_pl.unselfishness,
            pace=source_pl.pace,
            strength=source_pl.strength,
            stamina=source_pl.stamina,
            technique=source_pl.technique,
            consistency=source_pl.consistency,
            aggression=source_pl.aggression,
            bigmatch=source_pl.bigmatch,
            injuryprone=source_pl.injuryprone,
            leadership=source_pl.leadership,
            versatility=source_pl.versatility,
            setpieces=source_pl.setpieces,
            penalty=source_pl.penalty,
            creativity=source_pl.creativity,
            movement=source_pl.movement,
            positioning=source_pl.positioning,
            workrate=source_pl.workrate,
            flair=source_pl.flair,
            handling=source_pl.handling,
            kicking=source_pl.kicking,
            agility=source_pl.agility,
            aerial=source_pl.aerial,
            reflexes=source_pl.reflexes,
            communication=source_pl.communication,
            throwing=source_pl.throwing,
            gk=source_pl.gk,
            lib=source_pl.lib,
            lb=source_pl.lb,
            cb=source_pl.cb,
            rb=source_pl.rb,
            dm=source_pl.dm,
            lm=source_pl.lm,
            cm=source_pl.cm,
            rm=source_pl.rm,
            lw=source_pl.lw,
            am=source_pl.am,
            rw=source_pl.rw,
            cf=source_pl.cf,
            lwb=source_pl.lwb,
            rwb=source_pl.rwb,
            leftfoot=source_pl.leftfoot,
            rightfoot=source_pl.rightfoot,
            ca=source_pl.ca,
            pa=source_pl.pa,
            home_rep=source_pl.home_rep,
            current_rep=source_pl.current_rep,
            world_rep=source_pl.world_rep,
            international_retirement=source_pl.international_retirement,
            squad_number=0,  # Reset
            preferred_squad_number=0,
            height=source_pl.height,
            weight=source_pl.weight,
            unknown1=source_pl.unknown1,
            unknown2=source_pl.unknown2
        )
        
        # Link people to player
        new_p.player_id = new_player_id
        
        # Add to lists
        app.people.items.append(new_p)
        app.people_uid_index[new_uid] = len(app.people.items) - 1
        app.player_by_id[new_player_id] = new_pl
        app.players.items.append(new_pl)
        
        # Mark dirty
        app.dirty_people = True
        app.dirty_players = True
        
        print_success(f"✓ Player duplicated!")
        print_info(f"New UID: {new_uid}")
        print_info(f"Name: {get_display_name(app, new_p)}")
        print_info(f"CA: {new_pl.ca} | PA: {new_pl.pa}")
        print_warning("Note: Player baru sebagai Free Agent (ClubId=-1)")
        
        wait_enter()
        return new_p, new_pl
        
    except Exception as e:
        print_error(f"Gagal duplicate: {e}")
        wait_enter()
        return None, None


def add_new_player(app: "App") -> bool:
    """
    Add a completely new player.
    Returns True if successful.
    """
    clear_screen()
    print_header("➕ ADD NEW PLAYER")
    
    print_info("Buat player baru dari nol dengan stats default.")
    print("")
    
    # Get basic info
    first_name = get_input("First Name ID (atau 0)", "bold cyan")
    if not first_name.isdigit():
        print_warning("First Name ID harus angka")
        wait_enter()
        return False
    
    last_name = get_input("Last Name ID (atau 0)", "bold cyan")
    if not last_name.isdigit():
        print_warning("Last Name ID harus angka")
        wait_enter()
        return False
    
    nation = get_input("Nation ID", "bold cyan")
    if not nation.isdigit():
        print_warning("Nation ID harus angka")
        wait_enter()
        return False
    
    dob = get_input("Date of Birth (YYYY-MM-DD, default 2000-01-01)", "bold cyan") or "2000-01-01"
    
    ca = get_input("CA (default 100)", "bold cyan") or "100"
    pa = get_input("PA (default 120)", "bold cyan") or "120"
    
    try:
        new_uid = get_next_uid(app)
        new_people_id = get_next_people_id(app)
        new_player_id = get_next_player_id(app)
        
        # Create People
        new_p = People(
            id=new_people_id,
            uid=new_uid,
            first_name_id=int(first_name),
            last_name_id=int(last_name),
            common_name_id=-1,
            dob_raw=date_to_int32(dob) if '-' in dob else int(dob),
            nation_id=int(nation),
            other_nationalities=[],
            ethnicity=0,
            ptype=1,  # Player type
            national_caps=0,
            national_goals=0,
            national_u21_caps=0,
            national_u21_goals=0,
            club_id=-1,
            joined_raw=0,
            adaptability=10,
            ambition=10,
            controversy=10,
            loyality=10,
            pressure=10,
            professionalism=10,
            sportmanship=10,
            temperament=10,
            player_id=new_player_id,
            default_languages=[],
            other_languages=[],
            relationships=[],
            unknown1=0,
            unknown_date=0,
            unknown3=0,
            unknown6b=0,
            unknown6c=0,
            unknown6d=0,
            unknown6e=0,
            unknown6f=None,
            unknown7=0,
            unknown8=0,
            unknown9=None,
            unknown10=None,
            unknown21=0
        )
        
        # Create Player with default stats
        new_pl = Player(
            id=new_player_id,
            uid=new_uid,
            crossing=10, dribbling=10, tackling=10, finishing=10,
            longshot=10, heading=10, jumping=10, passing=10,
            decision=10, unselfishness=10, pace=10, strength=10,
            stamina=10, technique=10, consistency=10, aggression=10,
            bigmatch=10, injuryprone=10, leadership=10, versatility=10,
            setpieces=10, penalty=10, creativity=10, movement=10,
            positioning=10, workrate=10, flair=10,
            handling=1, kicking=1, agility=1, aerial=1, reflexes=1,
            communication=1, throwing=1,
            gk=1, lib=1, lb=1, cb=1, rb=1, dm=1, lm=1, cm=1, rm=1,
            lw=1, am=1, rw=1, cf=1, lwb=1, rwb=1,
            leftfoot=10, rightfoot=10,
            ca=int(ca), pa=int(pa),
            home_rep=50, current_rep=50, world_rep=50,
            international_retirement=0,
            unknown1=0, squad_number=0, preferred_squad_number=0,
            height=180, weight=75,
            unknown2=0
        )
        
        # Add to lists
        app.people.items.append(new_p)
        app.people_uid_index[new_uid] = len(app.people.items) - 1
        app.player_by_id[new_player_id] = new_pl
        app.players.items.append(new_pl)
        
        # Mark dirty
        app.dirty_people = True
        app.dirty_players = True
        
        print_success(f"✓ New player created!")
        print_info(f"UID: {new_uid}")
        print_info(f"People ID: {new_people_id}")
        print_info(f"Player ID: {new_player_id}")
        print_warning("Note: Edit stats dengan 'Edit Player' setelah ini")
        
        wait_enter()
        return True
        
    except Exception as e:
        print_error(f"Gagal create player: {e}")
        wait_enter()
        return False


def show_player_detail(app: "App", p: People, pl: Player = None):
    """Show the unified person footprint (PersonDetailModel).

    Replaces the old two-table view with one screen covering everything
    attached to this person: people + player + contract + loan(s) + injury(s)
    + ban(s) + future transfer + retirement + career history + staff role +
    non-player + relationships + languages. Lookups are O(1) via the indexes
    built at load (App._build_person_indexes).
    """
    clear_screen()
    name = get_display_name(app, p)
    print_header(f"👤 {name}", f"UID: {p.uid} | ID: {p.id}")

    # Club / nation header line (mirrors the old behaviour).
    club = app.club_by_eff_id.get(p.club_id)
    club_name = club.full_name if club else "Free Agent"
    nation_name = app.nation_name(p.nation_id)
    print_info(f"Club: {club_name} | Nation: {nation_name}")

    idx = app.people_uid_index.get(p.uid)
    from ..ui.person_detail import show_person_detail
    show_person_detail(app, p, pl, idx)


def edit_person_detail(app: "App", p: People, pl: Player = None):
    """Unified edit menu for one person — dispatches to the existing
    per-section editors so every part of a person's footprint is editable from
    one place without jumping between the Player editor and 8 "More Data"
    editors.

    Each option opens the relevant existing editor (which runs its own loop
    and returns here on Back). Staff/non-player get small inline editors.
    """
    idx = app.people_uid_index.get(p.uid)
    while True:
        clear_screen()
        show_player_detail(app, p, pl)
        print_info(
            "\n[1] People+Stats | [2] Contract | [3] Loan(s) | [4] Injury(s) "
            "| [5] Ban(s) | [6] Future Transfer | [7] Retirement | [8] History "
            "| [9] Staff/Non-Player | [r] Relationships | [l] Languages | [0] Back"
        )
        cmd = (get_input(">>", "bold green") or "").strip().lower()

        if cmd == "0":
            break
        elif cmd == "1":
            edit_player_fields(app, p, pl)
        elif cmd == "2":
            _edit_contract(app, p)
        elif cmd == "3":
            _edit_loans(app, p)
        elif cmd == "4":
            _edit_injuries(app, p)
        elif cmd == "5":
            _edit_bans(app, p)
        elif cmd == "6":
            _edit_transfer(app, p)
        elif cmd == "7":
            _edit_retirement(app, p)
        elif cmd == "8":
            _edit_history(app, p)
        elif cmd == "9":
            _edit_staff_nonplayer(app, p, idx)
        elif cmd == "r":
            edit_relationships(app, p)
        elif cmd == "l":
            edit_languages(app, p)
        else:
            print_warning("Pilihan tidak valid")


def _set_dirty(app: "App", attr: str):
    """Mark an extended list dirty by its app attribute name."""
    flag = getattr(app, f"dirty_{attr}", None)
    if flag is not None:
        setattr(app, f"dirty_{attr}", True)


def _edit_int(prompt_label: str, current, cast=int):
    """Prompt for an int value, showing the current one. Returns None on empty."""
    raw = get_input(f"{prompt_label} [{current}]", "bold cyan")
    if not raw or not raw.strip():
        return None
    try:
        return cast(raw.strip())
    except (ValueError, TypeError):
        print_warning("Input bukan angka, skip.")
        return None


def _add_record(app: "App", attr: str, index_attr: str, rec, single=False):
    """Append a new record to an extended list, sync the UID index, set dirty.

    Args:
        attr: app attribute holding the DatList (e.g. 'starting_loans').
        index_attr: app attribute holding the UID->list/rec index (e.g.
            'loans_by_uid').
        rec: the record instance to add (its person_id/uid must already be set).
        single: True for single-record-per-person indexes (dict[uid]->rec),
            False for multi (dict[uid]->list[rec]).
    """
    dat = getattr(app, attr, None)
    if dat is None:
        print_warning(f"List {attr} tidak tersedia (file tidak ada).")
        return False
    dat.items.append(rec)
    idx = getattr(app, index_attr)
    # resolve the uid field on this record type
    uid = getattr(rec, "person_id", None)
    if uid is None:
        uid = getattr(rec, "uid", None)
    if uid is None:
        uid = getattr(rec, "person_uid", None)
    if uid is not None:
        if single:
            idx[uid] = rec
        else:
            idx.setdefault(uid, []).append(rec)
    _set_dirty(app, attr)
    return True


def _delete_record(app: "App", attr: str, index_attr: str, rec, single=False):
    """Remove a record from an extended list, sync the UID index, set dirty."""
    dat = getattr(app, attr, None)
    if dat is None:
        return False
    try:
        dat.items.remove(rec)
    except ValueError:
        print_warning("Record tidak ditemukan di list.")
        return False
    uid = getattr(rec, "person_id", None)
    if uid is None:
        uid = getattr(rec, "uid", None)
    if uid is None:
        uid = getattr(rec, "person_uid", None)
    if uid is not None:
        idx = getattr(app, index_attr)
        if single:
            idx.pop(uid, None)
        else:
            lst = idx.get(uid)
            if lst:
                try:
                    lst.remove(rec)
                except ValueError:
                    pass
                if not lst:
                    idx.pop(uid, None)
    _set_dirty(app, attr)
    return True


def _edit_contract(app: "App", p: People):
    """Edit the (single) contract record for this person."""
    rec = app.contracts_by_uid.get(p.uid)
    if rec is None:
        print_warning("Person ini tidak punya contract record.")
        wait_enter()
        return
    clear_screen()
    print_header(f"📝 Contract: {get_display_name(app, p)}")
    print_info(f"Club: {rec.club_id}  Wage: {rec.wage:,}  Type: {rec.contract_type}")
    print_info(f"Start: {rec.start_date}  End: {rec.end_date}")
    wage = _edit_int("Wage", rec.wage)
    if wage is not None:
        rec.wage = wage
    ctype = _edit_int("Contract type", rec.contract_type)
    if ctype is not None:
        rec.contract_type = ctype
    club = _edit_int("Club id", rec.club_id)
    if club is not None:
        rec.club_id = club
    _set_dirty(app, "starting_contracts")
    print_success("Contract diupdate.")
    wait_enter()


def _edit_loans(app: "App", p: People):
    while True:
        recs = app.loans_by_uid.get(p.uid, [])
        clear_screen()
        print_header(f"🔁 Loan(s): {get_display_name(app, p)}")
        if not recs:
            print_info("Belum ada loan.")
        else:
            for i, r in enumerate(recs, 1):
                print(f"  {i}. club={r.club_id} wage%={r.wage_percentage} "
                      f"({r.start_date}..{r.end_date})")
        print_info("\n[1] Edit | [2] Tambah loan | [3] Hapus loan | [0] Back")
        cmd = (get_input(">>", "bold green") or "").strip()
        if cmd == "0" or not cmd:
            break
        elif cmd == "1":
            if not recs:
                print_warning("Belum ada loan."); wait_enter(); continue
            sel = show_numbered_list(
                [f"#{i+1} club={r.club_id} wage%={r.wage_percentage}" for i, r in enumerate(recs)],
                "LOAN(s)")
            if sel < 0:
                continue
            rec = recs[sel]
            wp = _edit_int("Wage %", rec.wage_percentage)
            if wp is not None:
                rec.wage_percentage = wp
            club = _edit_int("Club id", rec.club_id)
            if club is not None:
                rec.club_id = club
            _set_dirty(app, "starting_loans")
            print_success("Loan diupdate."); wait_enter()
        elif cmd == "2":
            from ..core.transfer_format import StartingLoanRec
            club = _edit_int("Club id", -1)
            if club is None:
                print_warning("Club id wajib."); wait_enter(); continue
            rec = StartingLoanRec(
                person_id=p.uid, club_id=club, start_date=0x076C0001,
                end_date=0x07770001, wage_percentage=100, opaque=b"\xff" * 8)
            if _add_record(app, "starting_loans", "loans_by_uid", rec, single=False):
                print_success("Loan ditambah."); wait_enter()
        elif cmd == "3":
            if not recs:
                print_warning("Belum ada loan."); wait_enter(); continue
            sel = show_numbered_list(
                [f"#{i+1} club={r.club_id} wage%={r.wage_percentage}" for i, r in enumerate(recs)],
                "HAPUS LOAN")
            if sel < 0:
                continue
            if _delete_record(app, "starting_loans", "loans_by_uid", recs[sel], single=False):
                print_success("Loan dihapus."); wait_enter()



def _edit_injuries(app: "App", p: People):
    while True:
        recs = app.injuries_by_uid.get(p.uid, [])
        clear_screen()
        print_header(f"🤕 Injury(s): {get_display_name(app, p)}")
        if not recs:
            print_info("Belum ada injury.")
        else:
            for i, r in enumerate(recs, 1):
                print(f"  {i}. class={r.injury_class} type={r.injury_type} side={r.side}")
        print_info("\n[1] Edit | [2] Tambah injury | [3] Hapus injury | [0] Back")
        cmd = (get_input(">>", "bold green") or "").strip()
        if cmd == "0" or not cmd:
            break
        elif cmd == "1":
            if not recs:
                print_warning("Belum ada injury."); wait_enter(); continue
            sel = show_numbered_list(
                [f"#{i+1} class={r.injury_class} type={r.injury_type}" for i, r in enumerate(recs)],
                "INJURY(s)")
            if sel < 0:
                continue
            rec = recs[sel]
            cls = _edit_int("Injury class", rec.injury_class)
            if cls is not None:
                rec.injury_class = cls
            itype = _edit_int("Injury type", rec.injury_type)
            if itype is not None:
                rec.injury_type = itype
            _set_dirty(app, "starting_injuries")
            print_success("Injury diupdate."); wait_enter()
        elif cmd == "2":
            from ..core.transfer_format import StartingInjuryRec
            cls = _edit_int("Injury class", 28)
            itype = _edit_int("Injury type", 0x0A22)
            rec = StartingInjuryRec(
                person_id=p.uid, injury_class=cls if cls is not None else 28,
                injury_type=itype if itype is not None else 0x0A22,
                start_date=0x076C0001, end_date=0x07770001, side=1, b20=0, b21=0, b22=0)
            if _add_record(app, "starting_injuries", "injuries_by_uid", rec, single=False):
                print_success("Injury ditambah."); wait_enter()
        elif cmd == "3":
            if not recs:
                print_warning("Belum ada injury."); wait_enter(); continue
            sel = show_numbered_list(
                [f"#{i+1} class={r.injury_class} type={r.injury_type}" for i, r in enumerate(recs)],
                "HAPUS INJURY")
            if sel < 0:
                continue
            if _delete_record(app, "starting_injuries", "injuries_by_uid", recs[sel], single=False):
                print_success("Injury dihapus."); wait_enter()



def _edit_bans(app: "App", p: People):
    while True:
        recs = app.bans_by_uid.get(p.uid, [])
        clear_screen()
        print_header(f"🚫 Ban(s): {get_display_name(app, p)}")
        if not recs:
            print_info("Belum ada ban.")
        else:
            for i, r in enumerate(recs, 1):
                print(f"  {i}. type={r.ban_type} ({r.start_date}..{r.end_date})")
        print_info("\n[1] Edit | [2] Tambah ban | [3] Hapus ban | [0] Back")
        cmd = (get_input(">>", "bold green") or "").strip()
        if cmd == "0" or not cmd:
            break
        elif cmd == "1":
            if not recs:
                print_warning("Belum ada ban."); wait_enter(); continue
            sel = show_numbered_list(
                [f"#{i+1} type={r.ban_type}" for i, r in enumerate(recs)], "BAN(s)")
            if sel < 0:
                continue
            rec = recs[sel]
            bt = _edit_int("Ban type", rec.ban_type)
            if bt is not None:
                rec.ban_type = bt
            _set_dirty(app, "starting_bans")
            print_success("Ban diupdate."); wait_enter()
        elif cmd == "2":
            from ..core.transfer_format import StartingBanRec
            bt = _edit_int("Ban type", 1)
            rec = StartingBanRec(
                person_id=p.uid, ban_type=bt if bt is not None else 1,
                unknown1=-1, unknown2=-1, unknown3=-1,
                start_date=0x076C0001, end_date=0x07770001, unknown_tail=0)
            if _add_record(app, "starting_bans", "bans_by_uid", rec, single=False):
                print_success("Ban ditambah."); wait_enter()
        elif cmd == "3":
            if not recs:
                print_warning("Belum ada ban."); wait_enter(); continue
            sel = show_numbered_list(
                [f"#{i+1} type={r.ban_type}" for i, r in enumerate(recs)], "HAPUS BAN")
            if sel < 0:
                continue
            if _delete_record(app, "starting_bans", "bans_by_uid", recs[sel], single=False):
                print_success("Ban dihapus."); wait_enter()



def _edit_transfer(app: "App", p: People):
    while True:
        recs = app.transfers_by_uid.get(p.uid, [])
        rec = recs[0] if recs else None
        clear_screen()
        print_header(f"🔄 Future Transfer: {get_display_name(app, p)}")
        if rec is None:
            print_info("Belum ada future transfer.")
        else:
            print_info(f"From: {rec.from_club}  To: {rec.to_club}  Fee: {rec.transfer_fee:,}")
        print_info("\n[1] Edit | [2] Tambah | [3] Hapus | [0] Back")
        cmd = (get_input(">>", "bold green") or "").strip()
        if cmd == "0" or not cmd:
            break
        elif cmd == "1":
            if rec is None:
                print_warning("Belum ada record. Pakai [2] Tambah."); wait_enter(); continue
            fee = _edit_int("Transfer fee", rec.transfer_fee)
            if fee is not None:
                rec.transfer_fee = fee
            to = _edit_int("To club id", rec.to_club)
            if to is not None:
                rec.to_club = to
            frm = _edit_int("From club id", rec.from_club)
            if frm is not None:
                rec.from_club = frm
            _set_dirty(app, "starting_transfers")
            print_success("Future transfer diupdate."); wait_enter()
        elif cmd == "2":
            if rec is not None:
                print_warning("Sudah ada future transfer (single record). Hapus dulu."); wait_enter(); continue
            from ..core.transfer_format import FutureTransferRec
            to = _edit_int("To club id", -1)
            frm = _edit_int("From club id", -1)
            fee = _edit_int("Transfer fee", 0)
            nrec = FutureTransferRec(
                person_id=p.uid, from_club=frm if frm is not None else -1,
                to_club=to if to is not None else -1, reserved=0,
                transfer_date=0x07770001, future_date=0, fee_kind=1,
                transfer_fee=fee if fee is not None else 0, opaque=b"\xff" * 24)
            if _add_record(app, "starting_transfers", "transfers_by_uid", nrec, single=True):
                print_success("Future transfer ditambah."); wait_enter()
        elif cmd == "3":
            if rec is None:
                print_warning("Belum ada record."); wait_enter(); continue
            if _delete_record(app, "starting_transfers", "transfers_by_uid", rec, single=True):
                print_success("Future transfer dihapus."); wait_enter()


def _edit_retirement(app: "App", p: People):
    while True:
        rec = app.retirements_by_uid.get(p.uid)
        clear_screen()
        print_header(f"🏁 Retirement: {get_display_name(app, p)}")
        if rec is None:
            print_info("Belum ada retirement.")
        else:
            print_info(f"Date: {rec.retirement_date}  Reason: {rec.reason}")
        print_info("\n[1] Edit | [2] Tambah | [3] Hapus | [0] Back")
        cmd = (get_input(">>", "bold green") or "").strip()
        if cmd == "0" or not cmd:
            break
        elif cmd == "1":
            if rec is None:
                print_warning("Belum ada record. Pakai [2] Tambah."); wait_enter(); continue
            reason = _edit_int("Reason", rec.reason)
            if reason is not None:
                rec.reason = reason
            rdate = _edit_int("Retirement date (packed)", rec.retirement_date)
            if rdate is not None:
                rec.retirement_date = rdate
            _set_dirty(app, "starting_retirements")
            print_success("Retirement diupdate."); wait_enter()
        elif cmd == "2":
            if rec is not None:
                print_warning("Sudah ada retirement (single record). Hapus dulu."); wait_enter(); continue
            from ..core.transfer_format import RetirementRec
            rdate = _edit_int("Retirement date (packed)", 0x07770001)
            reason = _edit_int("Reason", 0)
            nrec = RetirementRec(
                person_id=p.uid,
                retirement_date=rdate if rdate is not None else 0x07770001,
                reason=reason if reason is not None else 0)
            if _add_record(app, "starting_retirements", "retirements_by_uid", nrec, single=True):
                print_success("Retirement ditambah."); wait_enter()
        elif cmd == "3":
            if rec is None:
                print_warning("Belum ada record."); wait_enter(); continue
            if _delete_record(app, "starting_retirements", "retirements_by_uid", rec, single=True):
                print_success("Retirement dihapus."); wait_enter()



def _edit_history(app: "App", p: People):
    """Edit career history via the existing history_simple._edit_player."""
    phs = app.history_by_uid.get(p.uid, [])
    if not phs:
        print_warning("Person ini tidak punya career history record.")
        wait_enter()
        return
    from .history_simple import _edit_player
    _edit_player(app, phs[0])


def _edit_staff_nonplayer(app: "App", p: People, idx):
    """Edit official/coach/physio/scout (by UID or array-index) + non-player."""
    clear_screen()
    print_header(f"👔 Staff / Non-Player: {get_display_name(app, p)}")
    parts = []
    off = app.officials_by_uid.get(p.uid)
    if off:
        parts.append(f"Official: type={off.official_type} rep={off.rep_current}/{off.rep_home}/{off.rep_world}")
    if idx is not None:
        for label, store, attr in (("Coach", app.coaches_by_idx, None),
                                   ("Physio", app.physios_by_idx, None),
                                   ("Scout", app.scouts_by_idx, None)):
            rec = store.get(idx) if store else None
            if rec:
                parts.append(f"{label}: attrs {rec.attr1}/{rec.attr2}/{rec.attr3}")
    np = app.nonplayers_by_uid.get(p.uid)
    if np:
        parts.append(f"NonPlayer: rep {np.home_rep}/{np.world_rep}/{np.current_rep}")
    if not parts:
        print_warning("Person ini tidak punya staff/non-player record.")
        wait_enter()
        return
    for line in parts:
        print_info(line)

    # official reputation edit
    if off is not None:
        rc = _edit_int("Official rep_current", off.rep_current)
        if rc is not None:
            off.rep_current = rc
        _set_dirty(app, "officials")
    # staff attr edits (idx-keyed)
    if idx is not None:
        for label, store, attr, dirty_name in (
            ("Coach", app.coaches_by_idx, "attr1", "coaches"),
            ("Physio", app.physios_by_idx, "attr1", "physios"),
            ("Scout", app.scouts_by_idx, "attr1", "scouts"),
        ):
            rec = store.get(idx) if store else None
            if rec is not None:
                a = _edit_int(f"{label} attr1", rec.attr1)
                if a is not None:
                    rec.attr1 = a
                _set_dirty(app, dirty_name)
    # non-player reputation edit
    if np is not None:
        hr = _edit_int("NonPlayer home_rep", np.home_rep)
        if hr is not None:
            np.home_rep = hr
        wr = _edit_int("NonPlayer world_rep", np.world_rep)
        if wr is not None:
            np.world_rep = wr
        cr = _edit_int("NonPlayer current_rep", np.current_rep)
        if cr is not None:
            np.current_rep = cr
        _set_dirty(app, "non_players")
    print_success("Staff/Non-Player diupdate.")
    wait_enter()


def _player_edit_fields():
    """Ordered (number, label, attr) map shared by the display and the handler
    so the number the user sees is always the field that actually gets edited.
    (People fields 1..20, then player stats 21+.)"""
    out = []
    for i, (label, attr) in enumerate(PEOPLE_FIELDS[:20], 1):
        out.append((i, label, attr))
    player_stats = [
        ("CA", "ca"), ("PA", "pa"), ("Finishing", "finishing"),
        ("Dribbling", "dribbling"), ("Pace", "pace"), ("Technique", "technique"),
        ("Crossing", "crossing"), ("Passing", "passing"), ("Tackling", "tackling"),
        ("Heading", "heading"), ("Strength", "strength"), ("Stamina", "stamina"),
        ("Jumping", "jumping"), ("Decision", "decision"), ("Aggression", "aggression"),
    ]
    for i, (label, attr) in enumerate(player_stats, len(PEOPLE_FIELDS[:20]) + 1):
        out.append((i, label, attr))
    return out


def edit_player_fields(app: "App", p: People, pl: Player):
    """Edit player fields with simple numeric menu."""
    field_map = _player_edit_fields()  # (num, label, attr)
    while True:
        clear_screen()
        print_header(f"Edit: {get_display_name(app, p)}")

        # Browse fields, showing the real current value for each number.
        fields = []
        for num, label, attr in field_map:
            if num <= 20:
                val = str(getattr(p, attr))[:25]
            else:
                if not pl:
                    continue
                val = str(getattr(pl, attr))
            fields.append((str(num), label, val))

        # Show fields
        if RICH_AVAILABLE:
            from rich.table import Table
            from rich import box
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            table.add_column("No", style="bold green", width=4)
            table.add_column("Field", style="cyan", width=18)
            table.add_column("Value", style="white")
            for num, name, val in fields:
                table.add_row(num, name, val)
            console.print(table)
        else:
            for num, name, val in fields:
                print(f"{num:>3}. {name:18} {val}")

        print_info("\n[no] [value] = edit | [g] = gacor | [r] = fav | [l] = lang | [h] = help | [0] = back")

        cmd = get_input(">>", "bold green")
        if not cmd:
            continue

        if cmd == "0":
            break

        if cmd.lower() == "h":
            show_help_player()
            continue

        if cmd.lower() == "g":
            apply_gacor(app, p, pl)
            continue

        if cmd.lower() == "r":
            edit_relationships(app, p)
            continue

        if cmd.lower() == "l":
            edit_languages(app, p)
            continue

        parts = cmd.split(maxsplit=1)
        if len(parts) != 2:
            print_warning("Format: [no] [value]")
            continue

        field_no, value = parts
        matched = [m for m in field_map if str(m[0]) == field_no]
        if not matched:
            print_warning(f"Field {field_no} tidak ada")
            continue
        _, label, attr = matched[0]

        try:
            if field_no.isdigit() and int(field_no) >= 21:
                if not pl:
                    print_warning("Bukan player, tidak punya stats!")
                    continue
                setattr(pl, attr, int(value))
                app.dirty_players = True
                print_success(f"{label} = {value}")
            elif attr == "other_nationalities":
                p.other_nationalities = [int(x.strip()) for x in value.split(",") if x.strip()]
                app.dirty_people = True
                print_success(f"{label} = {value}")
            elif attr == "ethnicity":
                p.ethnicity = eth_parse(value)
                app.dirty_people = True
                print_success(f"{label} = {value}")
            elif attr == "uid":
                old = p.uid
                p.uid = int(value)
                # keep the uid index consistent so search by the new uid works
                idx = app.people_uid_index.pop(old, None)
                if idx is not None:
                    app.people_uid_index[p.uid] = idx
                if pl is not None:
                    pl.uid = p.uid  # keep player record's uid in step
                app.dirty_people = True
                print_success(f"{label} = {value}")
            elif attr in ("dob_raw", "joined_raw"):
                setattr(p, attr, parse_date_or_int32(value))
                app.dirty_people = True
                print_success(f"{label} = {value}")
            else:
                setattr(p, attr, int(value))
                app.dirty_people = True
                print_success(f"{label} = {value}")
        except Exception as e:
            print_error(str(e))


def apply_gacor(app: "App", p: People, pl: Player):
    """Apply gacor preset (boost well-known player stats)."""
    if not pl:
        print_warning("Bukan player!")
        return

    clear_screen()
    print_header("⚡ GACOR PRESET")

    # Personality / mental attributes (people fields).
    mental = {
        "adaptability": 20, "ambition": 20, "controversy": 20, "loyality": 20,
        "pressure": 20, "professionalism": 20, "sportmanship": 20, "temperament": 20,
    }
    for attr, v in mental.items():
        setattr(p, attr, v)

    # Star player stats (the headline promise: 200 CA / 200 PA + key stats to 20).
    pl.ca = 200
    pl.pa = 200
    for attr in ("finishing", "dribbling", "tackling", "pace", "passing",
                 "technique", "crossing", "heading", "strength", "stamina",
                 "jumping", "decision", "aggression", "longshot", "creativity",
                 "movement", "positioning", "workrate", "flair", "setpieces",
                 "penalty", "consistency", "bigmatch", "leadership", "versatility"):
        setattr(pl, attr, 20)

    app.dirty_people = True
    app.dirty_players = True
    print_success("Gacor preset diterapkan! (CA/PA=200, stats=20, mental=20)")
    wait_enter()


# RelationshipType labels (best-effort; the GUI enum isn't authoritative in
# the AOT binary, so these are the common FMM meanings for the observed
# values 1-4).
_REL_TYPE_LABELS = {
    1: "Favourite",
    2: "Disliked",
    3: "Rival",
    4: "Friendly",
}


def _rel_type_label(t: int) -> str:
    return _REL_TYPE_LABELS.get(t, "?")


def edit_relationships(app: "App", p: People):
    """PersonFavouriteModel editor (People.relationships).

    Each relationship targets a person (by uid); the raw numbers are shown
    alongside the best-effort labels so nothing is silently interpreted.
    """
    while True:
        clear_screen()
        print_header(f"🔗 Favourites: {get_display_name(app, p)}")
        print_info("(PersonFavouriteModel = People.relationships)")

        if not p.relationships:
            print_info("Belum ada relationship")
        else:
            items = []
            for i, rel in enumerate(p.relationships, 1):
                name = app.people_name_by_uid(rel.uid)
                items.append(
                    f"{i}. [strength {rel.level}] {_rel_type_label(rel.type)}"
                    f"(type {rel.type}) reason {rel.reason} → {name} (UID:{rel.uid})"
                )
            if RICH_AVAILABLE:
                for item in items:
                    console.print(f"  {item}")
            else:
                for item in items:
                    print(f"  {item}")

        print_info("\n[1] Add | [2] Delete | [0] Back")
        cmd = get_input(">>", "bold green")

        if cmd == "0":
            break
        elif cmd == "1":
            print_info("Format: strength type unknown target_uid reason")
            print_info(f"  type: {', '.join(f'{k}={v}' for k, v in sorted(_REL_TYPE_LABELS.items()))}")
            val = get_input("Values", "bold cyan")
            try:
                parts = [int(x) for x in val.split()]
                if len(parts) == 5:
                    p.relationships.append(Relationship(*parts))
                    app.dirty_people = True
                    print_success("Relationship ditambah")
                else:
                    print_warning("Perlu 5 nilai")
            except Exception as e:
                print_error(str(e))
        elif cmd == "2":
            if not p.relationships:
                print_warning("Tidak ada relationship")
                continue
            num = get_input("Hapus no", "bold yellow")
            if num.isdigit():
                idx = int(num) - 1
                if 0 <= idx < len(p.relationships):
                    p.relationships.pop(idx)
                    app.dirty_people = True
                    print_success("Relationship dihapus")


def _pick_language(app: "App") -> int:
    """Prompt for a language ID (raw number or name search). Returns id or None."""
    q = get_input("Language ID (atau nama)", "bold cyan")
    if not q:
        return None
    if q.isdigit():
        return int(q)
    # name search over languages
    from ..utils.helpers import lower_norm
    ql = lower_norm(q)
    hits = [(l.id, l.name) for l in app.languages.items
            if ql in lower_norm(l.name)]
    if not hits:
        print_warning("Bahasa tidak ditemukan")
        wait_enter()
        return None
    if len(hits) == 1:
        return hits[0][0]
    items = [f"{name} (ID {lid})" for lid, name in hits]
    sel = show_numbered_list(items, f"Pilih bahasa: {q}")
    if sel < 0:
        return None
    return hits[sel][0]


def edit_languages(app: "App", p: People):
    """PersonLanguageModel editor (People.default_languages + other_languages).

    Each language is (lang_id, strength); strength is the 0-10 proficiency.
    """
    while True:
        clear_screen()
        print_header(f"📖 Languages: {get_display_name(app, p)}")
        print_info("(PersonLanguageModel = default_languages + other_languages)")

        def _fmt(lang_list):
            out = []
            for i, (lid, s) in enumerate(lang_list, 1):
                out.append(f"  {i:2}. {app.lang_name(lid)} (ID {lid}, strength {s})")
            return out

        print("\n[bold cyan]Default:[/bold cyan]")
        dlines = _fmt(p.default_languages)
        if dlines:
            for l_ in dlines:
                print(l_)
        else:
            print("  (kosong)")
        print("\n[bold cyan]Other:[/bold cyan]")
        olines = _fmt(p.other_languages)
        if olines:
            for l_ in olines:
                print(l_)
        else:
            print("  (kosong)")

        print_info("\n[1] Add default | [2] Add other | [3] Edit strength | [4] Delete | [0] Back")
        cmd = get_input(">>", "bold green")
        if cmd == "0":
            break
        elif cmd == "1" or cmd == "2":
            lang_id = _pick_language(app)
            if lang_id is None:
                continue
            strength = get_input("Strength (1-10)", "bold cyan")
            if not strength.isdigit():
                print_warning("Strength harus angka")
                continue
            target = p.default_languages if cmd == "1" else p.other_languages
            target.append((lang_id, int(strength)))
            app.dirty_people = True
            print_success("Bahasa ditambah")
        elif cmd == "3":
            which = get_input("D[d]efault / O[o]ther / [b]ack", "bold cyan").lower()
            target = p.default_languages if which == "d" else (p.other_languages if which == "o" else None)
            if target is None:
                continue
            num = get_input("Nomor bahasa", "bold yellow")
            if not num.isdigit():
                continue
            idx = int(num) - 1
            if not (0 <= idx < len(target)):
                print_warning("Nomor tidak valid")
                continue
            strength = get_input("Strength baru (1-10)", "bold cyan")
            if not strength.isdigit():
                print_warning("Strength harus angka")
                continue
            lid, _ = target[idx]
            target[idx] = (lid, int(strength))
            app.dirty_people = True
            print_success("Strength diubah")
        elif cmd == "4":
            which = get_input("D[d]efault / O[o]ther / [b]ack", "bold cyan").lower()
            target = p.default_languages if which == "d" else (p.other_languages if which == "o" else None)
            if target is None:
                continue
            if not target:
                print_warning("Kosong")
                continue
            num = get_input("Hapus nomor", "bold yellow")
            if num.isdigit():
                idx = int(num) - 1
                if 0 <= idx < len(target):
                    target.pop(idx)
                    app.dirty_people = True
                    print_success("Bahasa dihapus")


def change_player_uid(app: "App", p: People):
    """Change a player UID globally, syncing every reference to it."""
    print_info(f"Ganti UID: {get_display_name(app, p)} (UID saat ini: {p.uid})")
    new_uid_str = get_input("UID baru (angka, kosong=batal)", "bold cyan")
    if not new_uid_str:
        return
    if not new_uid_str.isdigit():
        print_error("UID harus angka")
        wait_enter()
        return
    new_uid = int(new_uid_str)
    if new_uid in app.people_uid_index:
        print_error(f"UID {new_uid} sudah dipakai ({app.people_name_by_uid(new_uid)})")
        wait_enter()
        return
    confirm = get_input(f"Yakin ubah UID {p.uid} -> {new_uid}? (y/n)", "bold yellow")
    if confirm.lower() != 'y':
        return
    try:
        from ..core.squad_ops import rename_uid
        report = rename_uid(app, p.uid, new_uid)
        print_success(f"✓ UID berubah: {p.uid} -> {new_uid}")
        for k, v in report.items():
            print_info(f"  {k}: {v} ref diubah")
        wait_enter()
    except Exception as e:
        print_error(f"Gagal ganti UID: {e}")
        wait_enter()


def transfer_player(app: "App", p: People):
    """Transfer a player to another club, syncing contract data."""
    print_info(f"Transfer: {get_display_name(app, p)}")
    print_info(f"Klub saat ini: {app.club_name_from_people(p)} (ID: {p.club_id})")

    club_input = get_input("Klub tujuan (nama atau ID, kosong=batal)", "bold cyan")
    if not club_input:
        return
    club_id = None
    if club_input.isdigit():
        club_id = int(club_input)
    else:
        from .club_simple import search_clubs
        clubs = search_clubs(app, club_input)
        if clubs:
            if len(clubs) == 1:
                club_id = clubs[0][1].id if clubs[0][1].id != -1 else clubs[0][0]
            else:
                items = [f"{c.full_name} ({c.short_name})" for _, c in clubs]
                sel = show_numbered_list(items, f"Pilih klub: {club_input}")
                if sel >= 0:
                    club_id = clubs[sel][1].id if clubs[sel][1].id != -1 else clubs[sel][0]
    if club_id is None or club_id not in app.club_by_eff_id:
        print_error("Klub tujuan tidak ditemukan")
        wait_enter()
        return

    target = app.club_by_eff_id[club_id]
    if getattr(target, "ctype", 0) == 1:
        print_error(f"{target.full_name} adalah tim nasional, bukan club. Transfer klub hanya ke club sungguhan.")
        wait_enter()
        return
    print_info(f"Target: {target.full_name} (ID: {club_id})")

    wage = get_input("Gaji mingguan (0)", "bold cyan") or "0"
    years = get_input("Durasi kontrak tahun (default 3)", "bold cyan") or "3"
    squad = get_input("Nomor punggung (0)", "bold cyan") or "0"
    confirm = get_input(f"Transfer ke {target.full_name}? (y/n)", "bold yellow")
    if confirm.lower() != 'y':
        return
    try:
        from ..core.squad_ops import transfer_player as do_transfer
        do_transfer(
            app, p, club_id,
            wage=int(wage), years=int(years), squad_number=int(squad),
        )
        app.save_all_dirty()
        print_success(f"✓ Transfer ke {target.full_name} berhasil!")
        wait_enter()
    except Exception as e:
        print_error(f"Gagal transfer: {e}")
        wait_enter()


def mode_player_simple(app: "App"):
    """Player editor - termux friendly."""
    current_p = None
    current_pl = None
    
    while True:
        clear_screen()
        print_header("👤 PLAYER EDITOR")
        
        if current_p:
            show_player_detail(app, current_p, current_pl)
            print_info("\n[1] Edit (unified) | [2] Cari lain | [d] Duplicate | [t] Transfer | [u] Ganti UID | [0] Back")
            cmd = get_input(">>", "bold green")

            if cmd == "0":
                break
            elif cmd == "1":
                edit_person_detail(app, current_p, current_pl)
            elif cmd == "2":
                current_p = None
                current_pl = None
            elif cmd.lower() == "d":
                new_p, new_pl = duplicate_player(app, current_p)
                if new_p and new_pl:
                    # Switch to new player for immediate editing
                    current_p = new_p
                    current_pl = new_pl
                    print_success("Switched to duplicated player!")
            elif cmd.lower() == "t":
                transfer_player(app, current_p)
            elif cmd.lower() == "u":
                change_player_uid(app, current_p)
            elif cmd.lower() == "h":
                show_help_player()
            else:
                print_warning("Pilihan tidak valid (tekan h untuk help)")
        else:
            # Search mode
            print_info("[+] Add | [c] ByClub | [?] Help | [nama/UID] Cari | [kosong] Back")
            query = get_input(">>", "bold cyan")
            
            if not query:
                break
            
            if query == "+":
                add_new_player(app)
                continue
            
            if query == "?":
                show_help_player()
                continue
            
            # Search by Club
            if query.lower() == "c":
                club_input = get_input("Club ID (atau nama club)", "bold cyan")
                if not club_input:
                    continue
                
                club_id = None
                if club_input.isdigit():
                    club_id = int(club_input)
                else:
                    # Search club by name
                    from .club_simple import search_clubs
                    clubs = search_clubs(app, club_input)
                    if clubs:
                        if len(clubs) == 1:
                            club_id = clubs[0][1].id if clubs[0][1].id != -1 else clubs[0][0]
                        else:
                            # Show list
                            from ..ui.console import show_numbered_list
                            items = [f"{c.full_name} ({c.short_name})" for _, c in clubs]
                            selected = show_numbered_list(items, f"Pilih club: {club_input}")
                            if selected >= 0:
                                club_id = clubs[selected][1].id if clubs[selected][1].id != -1 else clubs[selected][0]
                    
                if club_id is None:
                    print_warning("Club tidak ditemukan")
                    wait_enter()
                    continue
                
                # Find all players in this club
                results = search_players_by_club(app, club_id)
                if not results:
                    print_warning(f"Tidak ada pemain di club ID {club_id}")
                    wait_enter()
                    continue
                
                # Show list of players
                items = [f"{get_display_name(app, p)} (UID:{p.uid}, CA:{pl.ca})" for _, p, pl in results]
                from ..ui.console import show_numbered_list
                selected = show_numbered_list(items, f"Pemain di Club ID {club_id}")
                if selected >= 0:
                    idx, current_p, current_pl = results[selected]
                continue
            
            # If numeric, search by UID
            if query.isdigit():
                uid = int(query)
                idx = app.people_uid_index.get(uid)
                if idx is not None:
                    current_p = app.people.items[idx]
                    current_pl = app.player_by_id.get(current_p.player_id)
                else:
                    print_warning(f"UID {uid} tidak ditemukan")
                    wait_enter()
            else:
                # Search by name
                results = search_people(app, query)
                if not results:
                    print_warning("Tidak ditemukan")
                    wait_enter()
                elif len(results) == 1:
                    idx, current_p = results[0]
                    current_pl = app.player_by_id.get(current_p.player_id)
                else:
                    # Show list for selection
                    items = [f"{get_display_name(app, p)} (UID:{p.uid})" for _, p in results]
                    selected = show_numbered_list(items, f"Hasil: {query}")
                    if selected >= 0:
                        idx, current_p = results[selected]
                        current_pl = app.player_by_id.get(current_p.player_id)
