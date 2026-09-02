"""Competition editor - Termux friendly with move/switch club."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.app import App

from ..ui.console import (
    RICH_AVAILABLE, console, print_header, print_success, 
    print_error, print_warning, print_info, get_input, clear_screen,
    show_numbered_list, show_help_text, wait_enter
)
from ..utils.helpers import lower_norm


def show_help_competition():
    """Show help for competition editor."""
    sections = [
        ("CARI KOMPETISI", [
            "[nama]      : Cari nama kompetisi",
            "[ID]        : Cari by ID (angka)",
            "Contoh: 'premier', 'serie a', '100'"
        ]),
        ("NAVIGASI LIST", [
            "1-50        : Pilih kompetisi",
            "98          : Next page",
            "99          : Prev page",
            "0           : Back"
        ]),
        ("MENU DETAIL", [
            "1           : Edit data kompetisi",
            "2           : Manage klub (move/switch/remove)",
            "3           : Cari kompetisi lain",
            "0           : Back"
        ]),
        ("EDIT FIELD", [
            "[no] [val]  : Edit field",
            "0           : Selesai / Back",
            "",
            "Key Fields:",
            "1=FullName  2=ShortName   3=CodeName",
            "4=NationId  5=Reputation  6=Level",
            "7=Type      8=IsWomen     9=FgColor",
            "10=BgColor"
        ]),
        ("MANAGE KLUB", [
            "Pilih klub dari list, lalu:",
            "1=Move      : Pindah klub ke liga lain",
            "2=Switch    : Tukar posisi dengan klub lain",
            "3=Remove    : Hapus klub dari liga",
            "",
            "Move: Input ID atau nama liga tujuan",
            "Switch: Cari klub untuk ditukar posisi",
            "Remove: Hapus dari liga (jadi free agent)"
        ])
    ]
    show_help_text("🏆 COMPETITION EDITOR", sections)


def search_competitions(app: "App", query: str) -> list:
    """Search competitions."""
    if not query:
        return []
    
    q = lower_norm(query)
    results = []
    
    for idx, c in enumerate(app.competitions.items):
        text = f"{c.full_name} {c.short_name} {c.code_name}"
        if q in lower_norm(text):
            results.append((idx, c))
    
    return results


def get_clubs_in_competition(app: "App", comp_id: int) -> list:
    """Get clubs in this competition."""
    return [(idx, c) for idx, c in enumerate(app.clubs.items) if c.league_id == comp_id]


def show_competition_detail(app: "App", c):
    """Show competition details."""
    clear_screen()
    print_header(f"🏆 {c.full_name}", f"Short: {c.short_name} | Code: {c.code_name}")
    
    nation = app.nation_name(c.nation_id)
    print_info(f"ID: {c.id} | UID: {c.uid} | Nation: {nation}")
    print_info(f"Type: {c.ctype} | Level: {c.level} | Reputation: {c.reputation}")
    print_info(f"IsWomen: {c.is_women}")
    
    # Show clubs in this competition
    clubs = get_clubs_in_competition(app, c.id)
    print(f"\n  Klub di kompetisi ini: {len(clubs)}")
    for i, (idx, club) in enumerate(clubs[:10]):
        print(f"    {i+1}. {club.full_name}")
    if len(clubs) > 10:
        print(f"    ... dan {len(clubs) - 10} lainnya")


def edit_competition_fields(app: "App", c):
    """Edit competition fields."""
    while True:
        clear_screen()
        print_header(f"Edit: {c.full_name}")
        
        fields = [
            ("1", "FullName", c.full_name),
            ("2", "ShortName", c.short_name),
            ("3", "CodeName", c.code_name),
            ("4", "NationId", c.nation_id),
            ("5", "Reputation", c.reputation),
            ("6", "Level", c.level),
            ("7", "Type", c.ctype),
            ("8", "IsWomen", c.is_women),
            ("9", "FgColor", c.fg_color),
            ("10", "BgColor", c.bg_color),
        ]
        
        for num, name, val in fields:
            print(f"{num:>3}. {name:18} {val}")
        
        print_info("\n[no] [value] = edit | [0] = back")
        
        cmd = get_input(">>", "bold green")
        if not cmd:
            continue
        
        if cmd == "0":
            break
        
        parts = cmd.split(maxsplit=1)
        if len(parts) != 2:
            print_warning("Format: [no] [value]")
            continue
        
        field_no, value = parts
        
        try:
            field_map = {
                "1": ("full_name", str),
                "2": ("short_name", str),
                "3": ("code_name", str),
                "4": ("nation_id", int),
                "5": ("reputation", int),
                "6": ("level", int),
                "7": ("ctype", int),
                "8": ("is_women", lambda x: x.lower() in ("1", "true", "yes")),
                "9": ("fg_color", int),
                "10": ("bg_color", int),
            }
            
            if field_no in field_map:
                attr, typ = field_map[field_no]
                setattr(c, attr, typ(value))
                app.dirty_competitions = True
                print_success(f"{attr} = {value}")
        except Exception as e:
            print_error(str(e))


def manage_competition_clubs(app: "App", c):
    """Manage clubs in competition (move/switch/remove)."""
    while True:
        clear_screen()
        print_header(f"🏆 Klub di: {c.full_name}")
        
        clubs = get_clubs_in_competition(app, c.id)
        
        if not clubs:
            print_info("Belum ada klub di kompetisi ini")
        else:
            items = []
            for idx, club in clubs:
                nation = app.nation_name(club.nation_id)
                items.append(f"{club.full_name} ({nation})")
            
            selected = show_numbered_list(items, "Pilih klub untuk manage")
            
            if selected < 0:
                break
            
            club_idx, selected_club = clubs[selected]
            manage_single_club(app, c, selected_club, clubs)


def manage_single_club(app: "App", comp, club, current_clubs):
    """Manage single club (move/switch/remove)."""
    while True:
        clear_screen()
        print_header(f"🔧 Manage: {club.full_name}")
        
        print_info(f"Current League: {comp.full_name} (ID: {club.league_id})")
        print_info(f"Based: {club.based_id} | Nation: {app.nation_name(club.nation_id)}")
        
        print("\n  1. Move to other competition")
        print("  2. Switch with other club")
        print("  3. Remove from this competition")
        print("  0. Back")
        
        cmd = get_input(">>", "bold green")
        
        if cmd == "0":
            break
        
        elif cmd == "1":
            # Move club to other competition
            print_info("Cari kompetisi tujuan:")
            query = get_input("Nama/ID kompetisi", "bold cyan")
            
            if query.isdigit():
                target_id = int(query)
                target_comp = next((c for c in app.competitions.items if c.id == target_id), None)
            else:
                results = search_competitions(app, query)
                if not results:
                    print_warning("Tidak ditemukan")
                    continue
                items = [f"{c.full_name} ({app.nation_name(c.nation_id)})" for _, c in results]
                selected = show_numbered_list(items, "Pilih kompetisi")
                if selected < 0:
                    continue
                target_comp = results[selected][1]
            
            if target_comp:
                # Move club
                old_league = club.league_id
                club.league_id = target_comp.id
                club.based_id = target_comp.nation_id
                app.dirty_clubs = True
                print_success(f"Pindah ke {target_comp.full_name}")
                input("Enter...")
                break
        
        elif cmd == "2":
            # Switch with other club
            print_info("Cari klub untuk ditukar:")
            query = get_input("Nama klub", "bold cyan")
            
            results = []
            for idx, c in enumerate(app.clubs.items):
                if c.id != club.id and query.lower() in c.full_name.lower():
                    results.append((idx, c))
            
            if not results:
                print_warning("Tidak ditemukan")
                continue
            
            items = [f"{c.full_name} (League: {c.league_id})" for _, c in results]
            selected = show_numbered_list(items, "Pilih klub untuk ditukar")
            
            if selected < 0:
                continue
            
            other_idx, other_club = results[selected]
            
            # Swap league_id and based_id
            club.league_id, other_club.league_id = other_club.league_id, club.league_id
            club.based_id, other_club.based_id = other_club.based_id, club.based_id
            app.dirty_clubs = True
            
            print_success(f"Tukar posisi dengan {other_club.full_name}")
            input("Enter...")
            break
        
        elif cmd == "3":
            # Remove from competition
            confirm = get_input(f"Yakin hapus {club.full_name} dari liga? (y/n)", "bold yellow")
            if confirm.lower() == "y":
                club.league_id = -1
                club.based_id = club.nation_id
                app.dirty_clubs = True
                print_success("Klub dihapus dari kompetisi")
                input("Enter...")
                break


def mode_competition_simple(app: "App"):
    """Competition editor - termux friendly."""
    current_c = None
    
    while True:
        clear_screen()
        print_header("🏆 COMPETITION EDITOR")
        
        if current_c:
            show_competition_detail(app, current_c)
            print_info("\n[1] Edit | [2] Manage klub | [3] Cari lain | [h] Help | [0] Back")
            cmd = get_input(">>", "bold green")
            
            if cmd == "0":
                break
            elif cmd == "1":
                edit_competition_fields(app, current_c)
            elif cmd == "2":
                manage_competition_clubs(app, current_c)
            elif cmd == "3":
                current_c = None
            elif cmd.lower() == "h":
                show_help_competition()
            else:
                print_warning("Pilihan tidak valid")
        else:
            print_info("[?] Help | [nama/ID] Cari | [kosong] Back")
            query = get_input("Cari", "bold cyan")
            
            if query == "?":
                show_help_competition()
                continue
            
            if not query:
                break
            
            if query.isdigit():
                comp_id = int(query)
                found = next((c for c in app.competitions.items if c.id == comp_id), None)
                if found:
                    current_c = found
                else:
                    print_warning(f"ID {comp_id} tidak ditemukan")
                    input("Enter...")
            else:
                results = search_competitions(app, query)
                if not results:
                    print_warning("Tidak ditemukan")
                    input("Enter...")
                elif len(results) == 1:
                    current_c = results[0][1]
                else:
                    items = [f"{c.full_name} ({app.nation_name(c.nation_id)})" for _, c in results]
                    selected = show_numbered_list(items, f"Hasil: {query}")
                    if selected >= 0:
                        current_c = results[selected][1]
