"""Club editor - Termux friendly version."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.app import App

from ..core.constants import CLUB_FIELDS
from ..core.models import AffiliateRec, ClubRec, KitRec
from ..ui.console import (
    RICH_AVAILABLE, console, print_header, print_success, 
    print_error, print_warning, print_info, get_input, clear_screen,
    show_numbered_list, show_help_text, wait_enter
)
from ..utils.helpers import lower_norm


def show_help_club():
    """Show help for club editor."""
    sections = [
        ("CARI CLUB", [
            "[nama]      : Cari nama club (flexible)",
            "Contoh: 'arsenal', 'madrid', 'inter'"
        ]),
        ("NAVIGASI LIST", [
            "1-50        : Pilih item nomor X",
            "98          : Next page",
            "99          : Prev page",
            "0           : Back / Batal"
        ]),
        ("MENU DETAIL CLUB", [
            "1           : Edit club",
            "2           : Cari club lain",
            "d           : Duplicate club (buat copy)",
            "b           : Batch edit all players",
            "0           : Back"
        ]),
        ("EDIT FIELD", [
            "[no] [val]  : Edit field nomor X dengan value Y",
            "p           : Edit daftar pemain (players)",
            "a           : Edit affiliates",
            "0           : Selesai edit",
            "",
            "Contoh:",
            "  1 Juventus FC    : Ubah FullName",
            "  5 123            : Ubah NationId",
            "  7 456            : Ubah Stadium",
            "  9 15             : Ubah Reputation"
        ]),
        ("KEY FIELDS", [
            "1=FullName    2=ShortName   3=SixLetter   4=ThreeLetter",
            "5=NationId    6=BasedId     7=Stadium     8=LeagueId",
            "9=Reputation  10=Status     11=Academy    12=Facilities",
            "13=AttAvg     14=AttMin     15=AttMax"
        ]),
        ("EDIT PLAYERS", [
            "Tampilkan daftar UID pemain di club",
            "1           : Add player by UID",
            "2           : Clear all players",
            "0           : Back"
        ]),
        ("EDIT AFFILIATES", [
            "List affiliate relationships",
            "1           : Add affiliate",
            "2           : Delete affiliate",
            "0           : Back",
            "",
            "Format add: u1 club1 club2 start_day start_year end_day end_year u2",
            "Contoh: '0 100 200 1 2020 30 2025 0'"
        ]),
        ("BATCH EDIT", [
            "Edit semua pemain di club sekaligus",
            "b           : Batch edit players",
            "",
            "Menu Batch:",
            "1=Add CA    2=Add PA     3=Set Stamina=20",
            "4=Set WorkRate=20       5=Change Nation",
            "6=Copy from player"
        ])
    ]
    show_help_text("🏟️ CLUB EDITOR", sections)


def search_clubs(app: "App", query: str) -> list:
    """Search clubs by name."""
    if not query:
        return []
    
    q = lower_norm(query)
    results = []
    
    for idx, c in enumerate(app.clubs.items):
        names = f"{c.full_name} {c.short_name} {c.six_letter} {c.three_letter}"
        if q in lower_norm(names):
            results.append((idx, c))
    
    return results


def get_next_club_uid(app: "App") -> int:
    """Get next available Club UID."""
    if not app.clubs.items:
        return 100000
    return max((c.uid for c in app.clubs.items), default=100000) + 1


def get_next_club_id(app: "App") -> int:
    """Get next available Club ID (same logic as C#)."""
    if not app.clubs.items:
        return 0
    return max((c.id for c in app.clubs.items), default=-1) + 1


def duplicate_club(app: "App", source_c: ClubRec) -> ClubRec:
    """Duplicate a club. Returns new club or None if failed."""
    clear_screen()
    print_header(f"📋 DUPLICATE: {source_c.full_name}")
    
    print_info(f"Source: {source_c.full_name} (ID: {source_c.id})")
    print_info("Data yang akan dicopy:")
    print(f"  - Nama, Stadium, Nation")
    print(f"  - Reputation, Status, Facilities")
    print(f"  - Colors, Kits (tanpa pemain & affiliates)")
    print("")
    
    print_info("\nOpsi:")
    print("  [y] Duplicate & Edit sekarang")
    print("  [n] Batal")
    confirm = get_input("Pilih", "bold yellow")
    if confirm.lower() != 'y':
        print_warning("Dibatalkan")
        wait_enter()
        return None
    
    try:
        new_uid = get_next_club_uid(app)
        new_id = get_next_club_id(app)
        
        # Create new club with copied data
        new_c = ClubRec(
            id=new_id,
            uid=new_uid,
            full_name=f"{source_c.full_name} (Copy)",
            full_term=source_c.full_term,
            short_name=source_c.short_name,
            short_term=source_c.short_term,
            six_letter=source_c.six_letter,
            three_letter=source_c.three_letter,
            based_id=source_c.based_id,
            nation_id=source_c.nation_id,
            colors6=list(source_c.colors6),
            kits6=[KitRec(k.unknown1, k.unknown2, list(k.colors)) for k in source_c.kits6],
            status=source_c.status,
            academy=source_c.academy,
            facilities=source_c.facilities,
            att_avg=source_c.att_avg,
            att_min=source_c.att_min,
            att_max=source_c.att_max,
            reserves=source_c.reserves,
            league_id=-1,  # Not in any league
            other_division=source_c.other_division,
            other_last_pos=source_c.other_last_pos,
            stadium=source_c.stadium,
            last_league=source_c.last_league,
            unknown4flag=source_c.unknown4flag,
            unknown4=source_c.unknown4,
            unknown5=source_c.unknown5,
            league_pos=source_c.league_pos,
            reputation=source_c.reputation,
            unknown6=source_c.unknown6,
            affiliates=[],  # No affiliates for new club
            players=[],     # No players for new club
            unknown7=list(source_c.unknown7),
            main_club=source_c.main_club,
            ctype=source_c.ctype,
            unknown8=source_c.unknown8,
            unknown9=source_c.unknown9,
            gender=source_c.gender
        )
        
        # Add to list
        app.clubs.items.append(new_c)
        app.club_by_eff_id[new_id] = new_c
        
        app.dirty_clubs = True
        
        print_success(f"✓ Club duplicated!")
        print_info(f"New UID: {new_uid}")
        print_info(f"New ID: {new_id}")
        print_info(f"Name: {new_c.full_name}")
        print_warning("Note: Club baru tidak punya pemain & affiliates")
        
        wait_enter()
        return new_c
        
    except Exception as e:
        print_error(f"Gagal duplicate: {e}")
        wait_enter()
        return None


def add_new_club(app: "App") -> bool:
    """Add a completely new club."""
    clear_screen()
    print_header("➕ ADD NEW CLUB")
    
    print_info("Buat club baru dengan data default.\n")
    
    full_name = get_input("Full Name", "bold cyan")
    if not full_name:
        print_warning("Nama harus diisi")
        wait_enter()
        return False
    
    short_name = get_input("Short Name", "bold cyan") or full_name[:20]
    nation = get_input("Nation ID", "bold cyan") or "0"
    stadium = get_input("Stadium ID", "bold cyan") or "0"
    
    try:
        new_uid = get_next_club_uid(app)
        new_id = get_next_club_id(app)
        
        new_c = ClubRec(
            id=new_id,
            uid=new_uid,
            full_name=full_name,
            full_term=0,
            short_name=short_name,
            short_term=0,
            six_letter=short_name[:6],
            three_letter=short_name[:3],
            based_id=int(nation),
            nation_id=int(nation),
            colors6=[0, 0, 0, 0, 0, 0],
            kits6=[KitRec(0, 0, [0]*10) for _ in range(6)],
            status=1,  # Professional
            academy=10,
            facilities=10,
            att_avg=5000,
            att_min=1000,
            att_max=10000,
            reserves=0,
            league_id=-1,
            other_division=-1,
            other_last_pos=0,
            stadium=int(stadium),
            last_league=-1,
            unknown4flag=False,
            unknown4=b"",
            unknown5=b"",
            league_pos=0,
            reputation=5000,
            unknown6=b"\x00" * 20,
            affiliates=[],
            players=[],
            unknown7=[0] * 11,
            main_club=-1,
            ctype=0,
            unknown8=b"\x00" * 34,
            unknown9=b"\x00" * 41,
            gender=0
        )
        
        app.clubs.items.append(new_c)
        app.club_by_eff_id[new_id] = new_c
        app.dirty_clubs = True
        
        print_success(f"✓ New club created!")
        print_info(f"UID: {new_uid}")
        print_info(f"ID: {new_id}")
        print_info(f"Name: {full_name}")
        
        wait_enter()
        return True
        
    except Exception as e:
        print_error(f"Gagal create club: {e}")
        wait_enter()
        return False


def show_club_detail(app: "App", c: ClubRec):
    """Show club details."""
    clear_screen()
    print_header(f"🏟️ {c.full_name}", f"Short: {c.short_name} | ID: {c.id}")
    
    nation = app.nation_name(c.nation_id)
    stadium = app.stadium_name(c.stadium)
    print_info(f"Nation: {nation} | Stadium: {stadium}")
    print_info(f"League ID: {c.league_id} | Reputation: {c.reputation}")
    
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich import box
        
        print("\n[bold cyan]📋 Club Data:[/bold cyan]")
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("No", style="bold green", width=4)
        table.add_column("Field", style="cyan", width=18)
        table.add_column("Value", style="white")
        
        key_fields = [
            (1, "FullName", c.full_name),
            (2, "ShortName", c.short_name),
            (3, "SixLetter", c.six_letter),
            (4, "ThreeLetter", c.three_letter),
            (5, "NationId", c.nation_id),
            (6, "Stadium", c.stadium),
            (7, "LeagueId", c.league_id),
            (8, "Reputation", c.reputation),
            (9, "Status", c.status),
            (10, "Academy", c.academy),
            (11, "Facilities", c.facilities),
            (12, "AttAvg", c.att_avg),
        ]
        for num, name, val in key_fields:
            table.add_row(str(num), name, str(val)[:30])
        console.print(table)
    else:
        print("\n📋 Club Data:")
        key_fields = [
            (1, "FullName", c.full_name),
            (2, "ShortName", c.short_name),
            (3, "SixLetter", c.six_letter),
            (4, "ThreeLetter", c.three_letter),
            (5, "NationId", c.nation_id),
        ]
        for num, name, val in key_fields:
            print(f"{num:2}. {name:18} {val}")


def edit_club_fields(app: "App", c: ClubRec):
    """Edit club fields."""
    while True:
        clear_screen()
        print_header(f"Edit Club: {c.full_name}")
        
        fields = [
            ("1", "FullName", c.full_name),
            ("2", "ShortName", c.short_name),
            ("3", "SixLetter", c.six_letter),
            ("4", "ThreeLetter", c.three_letter),
            ("5", "NationId", c.nation_id),
            ("6", "BasedId", c.based_id),
            ("7", "Stadium", c.stadium),
            ("8", "LeagueId", c.league_id),
            ("9", "Reputation", c.reputation),
            ("10", "Status", c.status),
            ("11", "Academy", c.academy),
            ("12", "Facilities", c.facilities),
            ("13", "AttAvg", c.att_avg),
            ("14", "AttMin", c.att_min),
            ("15", "AttMax", c.att_max),
        ]
        
        if RICH_AVAILABLE:
            from rich.table import Table
            from rich import box
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            table.add_column("No", style="bold green", width=4)
            table.add_column("Field", style="cyan", width=18)
            table.add_column("Value", style="white")
            for num, name, val in fields:
                table.add_row(num, name, str(val)[:30])
            console.print(table)
        else:
            for num, name, val in fields:
                print(f"{num:>3}. {name:18} {val}")
        
        print_info("\n[no] [value] = edit | [p] = players | [a] = affiliates | [b] = batch | [h] = help | [0] = back")
        
        cmd = get_input(">>", "bold green")
        if not cmd:
            continue
        
        if cmd == "0":
            break
        
        if cmd.lower() == "h":
            show_help_club()
            continue
        
        if cmd.lower() == "p":
            edit_club_players(app, c)
            continue
        
        if cmd.lower() == "a":
            edit_club_affiliates(app, c)
            continue
        
        if cmd.lower() == "b":
            batch_edit_players(app, c)
            continue
        
        parts = cmd.split(maxsplit=1)
        if len(parts) != 2:
            print_warning("Format: [no] [value]")
            continue
        
        field_no, value = parts
        
        try:
            field_map = {
                "1": ("full_name", str),
                "2": ("short_name", str),
                "3": ("six_letter", str),
                "4": ("three_letter", str),
                "5": ("nation_id", int),
                "6": ("based_id", int),
                "7": ("stadium", int),
                "8": ("league_id", int),
                "9": ("reputation", int),
                "10": ("status", int),
                "11": ("academy", int),
                "12": ("facilities", int),
                "13": ("att_avg", int),
                "14": ("att_min", int),
                "15": ("att_max", int),
            }
            
            if field_no in field_map:
                attr, typ = field_map[field_no]
                setattr(c, attr, typ(value))
                app.dirty_clubs = True
                print_success(f"{attr} = {value}")
        except Exception as e:
            print_error(str(e))


def edit_club_players(app: "App", c: ClubRec):
    """Edit club players list."""
    while True:
        clear_screen()
        print_header(f"👥 Players in {c.full_name}")
        
        if not c.players:
            print_info("Belum ada pemain")
        else:
            items = []
            for uid in c.players[:50]:  # Max 50
                name = app.people_name_by_uid(uid)
                items.append(f"UID:{uid} - {name}")
            
            for i, item in enumerate(items, 1):
                print(f"{i:2}. {item}")
            
            if len(c.players) > 50:
                print_info(f"... dan {len(c.players) - 50} lainnya")
        
        print_info("\n[1] Add player by UID | [2] Clear all | [0] Back")
        cmd = get_input(">>", "bold green")
        
        if cmd == "0":
            break
        elif cmd == "1":
            uid = get_input("UID pemain", "bold cyan")
            if uid.isdigit():
                c.players.append(int(uid))
                app.dirty_clubs = True
                print_success("Pemain ditambah ke club")
        elif cmd == "2":
            c.players = []
            app.dirty_clubs = True
            print_success("Daftar pemain dikosongkan")


def edit_club_affiliates(app: "App", c: ClubRec):
    """Edit club affiliates."""
    while True:
        clear_screen()
        print_header(f"🔗 Affiliates of {c.full_name}")
        
        if not c.affiliates:
            print_info("Belum ada affiliate")
        else:
            for i, aff in enumerate(c.affiliates, 1):
                print(f"{i:2}. Club1:{aff.club1_id} Club2:{aff.club2_id} ({aff.start_year}-{aff.end_year})")
        
        print_info("\n[1] Add | [2] Delete | [0] Back")
        cmd = get_input(">>", "bold green")
        
        if cmd == "0":
            break
        elif cmd == "1":
            print_info("Format: u1 club1 club2 start_day start_year end_day end_year u2")
            val = get_input("Values", "bold cyan")
            try:
                parts = [int(x) for x in val.split()]
                if len(parts) == 8:
                    c.affiliates.append(AffiliateRec(*parts))
                    app.dirty_clubs = True
                    print_success("Affiliate ditambah")
                else:
                    print_warning("Perlu 8 nilai")
            except Exception as e:
                print_error(str(e))
        elif cmd == "2":
            if not c.affiliates:
                print_warning("Tidak ada affiliate")
                continue
            num = get_input("Hapus no", "bold yellow")
            if num.isdigit():
                idx = int(num) - 1
                if 0 <= idx < len(c.affiliates):
                    c.affiliates.pop(idx)
                    app.dirty_clubs = True
                    print_success("Affiliate dihapus")


def batch_edit_players(app: "App", c: ClubRec):
    """Batch edit all players in a club."""
    # Find all players in this club
    players_in_club = []
    for player in app.players.items:
        if player.uid in c.players:
            # Find associated people
            person = None
            for p in app.people.items:
                if p.uid == player.uid:
                    person = p
                    break
            if person:
                players_in_club.append((person, player))
    
    if not players_in_club:
        print_warning("Tidak ada pemain di club ini")
        input("\nTekan ENTER...")
        return
    
    total = len(players_in_club)
    
    while True:
        clear_screen()
        print_header(f"🔥 BATCH EDIT: {c.full_name}")
        print_info(f"Total pemain: {total}")
        
        # Show sample of players
        print("\n📋 Sample pemain:")
        for i, (person, player) in enumerate(players_in_club[:10], 1):
            print(f"  {i}. {person.first_name} {person.last_name} (CA:{player.ca} PA:{player.pa})")
        if total > 10:
            print(f"  ... dan {total - 10} lainnya")
        
        print("\n" + "=" * 50)
        print("⚡ QUICK ACTIONS:")
        print("  1. Add CA +5           2. Add PA +5")
        print("  3. Stamina → 20        4. WorkRate → 20")
        print("  5. Change Nation       6. Copy from player")
        print("  0. Back")
        print("=" * 50)
        
        cmd = get_input(">>", "bold green")
        
        if cmd == "0":
            break
        
        changes_made = False
        
        if cmd == "1":
            # Add CA +5
            for _, player in players_in_club:
                player.ca = min(200, player.ca + 5)
                app.dirty_players = True
                changes_made = True
            print_success(f"CA +5 diterapkan ke {total} pemain")
            
        elif cmd == "2":
            # Add PA +5
            for _, player in players_in_club:
                player.pa = min(200, player.pa + 5)
                app.dirty_players = True
                changes_made = True
            print_success(f"PA +5 diterapkan ke {total} pemain")
            
        elif cmd == "3":
            # Stamina -> 20
            for _, player in players_in_club:
                player.stamina = 20
                app.dirty_players = True
                changes_made = True
            print_success(f"Stamina = 20 diterapkan ke {total} pemain")
            
        elif cmd == "4":
            # WorkRate -> 20
            for _, player in players_in_club:
                player.work_rate = 20
                app.dirty_players = True
                changes_made = True
            print_success(f"Work Rate = 20 diterapkan ke {total} pemain")
            
        elif cmd == "5":
            # Change nation
            new_nation = get_input("Nation ID baru", "bold cyan")
            if new_nation.isdigit():
                for _, player in players_in_club:
                    player.nation_id = int(new_nation)
                    player.second_nation_id = 0
                    app.dirty_players = True
                changes_made = True
                print_success(f"Nation ID {new_nation} diterapkan ke {total} pemain")
            
        elif cmd == "6":
            # Copy stats from a specific player
            ref_uid = get_input("UID pemain referensi", "bold cyan")
            if ref_uid.isdigit():
                ref_uid_int = int(ref_uid)
                ref_player = None
                for p in app.players.items:
                    if p.uid == ref_uid_int:
                        ref_player = p
                        break
                
                if ref_player:
                    stats_to_copy = [
                        "ca", "pa", "acceleration", "aerial_ability", "aggression", "agility",
                        "anticipation", "balance", "bravery", "command_of_area", "communication",
                        "composure", "concentration", "corners", "creativity", "crossing",
                        "decisions", "determination", "dribbling", "eccentricity", "finishing",
                        "first_touch", "flair", "free_kicks", "handling", "heading", "influence",
                        "jumping", "kicking", "long_shots", "long_throws", "marking",
                        "natural_fitness", "off_the_ball", "one_on_ones", "pace", "passing",
                        "penalties", "positioning", "reflexes", "rushing_out", "stamina",
                        "strength", "tackling", "teamwork", "technique", "throwing",
                        "throw_ins", "tendency_to_punch", "vision", "work_rate"
                    ]
                    
                    for _, player in players_in_club:
                        for stat in stats_to_copy:
                            if hasattr(ref_player, stat):
                                setattr(player, stat, getattr(ref_player, stat))
                        app.dirty_players = True
                        changes_made = True
                    
                    print_success(f"Stats dari UID {ref_uid} dicopy ke {total} pemain")
                else:
                    print_error(f"Player UID {ref_uid} tidak ditemukan")
        
        if changes_made:
            app.players.save_overwrite()
            print_success("Changes saved!")
        
        input("\nTekan ENTER untuk lanjut...")


def mode_club_simple(app: "App"):
    """Club editor - termux friendly."""
    current_c = None
    
    while True:
        clear_screen()
        print_header("🏟️ CLUB EDITOR")
        
        if current_c:
            show_club_detail(app, current_c)
            print_info("\n[1] Edit | [2] Cari lain | [d] Duplicate | [b] Batch | [0] Back")
            cmd = get_input(">>", "bold green")
            
            if cmd == "0":
                break
            elif cmd == "1":
                edit_club_fields(app, current_c)
            elif cmd == "2":
                current_c = None
            elif cmd.lower() == "d":
                new_c = duplicate_club(app, current_c)
                if new_c:
                    # Switch to new club for immediate editing
                    current_c = new_c
                    print_success("Switched to duplicated club!")
            elif cmd.lower() == "b":
                batch_edit_players(app, current_c)
            elif cmd.lower() == "h":
                show_help_club()
            else:
                print_warning("Pilihan tidak valid (h=help)")
        else:
            print_info("[+] Add new club | [?] Help | [nama] Cari | [kosong] Back")
            query = get_input(">>", "bold cyan")
            
            if not query:
                break
            
            if query == "+":
                add_new_club(app)
                continue
            
            if query == "?":
                show_help_club()
                continue
            
            results = search_clubs(app, query)
            if not results:
                print_warning("Tidak ditemukan")
                wait_enter()
            elif len(results) == 1:
                _, current_c = results[0]
            else:
                items = [f"{c.full_name} ({c.short_name})" for _, c in results]
                selected = show_numbered_list(items, f"Hasil: {query}")
                if selected >= 0:
                    _, current_c = results[selected]
