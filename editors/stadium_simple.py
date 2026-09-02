"""Stadium editor - Termux friendly version."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.app import App

from ..ui.console import (
    print_header, print_success, print_error, print_warning, 
    print_info, get_input, clear_screen, show_numbered_list,
    show_help_text, wait_enter
)


def show_help_stadium():
    """Show help for stadium editor."""
    sections = [
        ("NAVIGASI", [
            "1-xx        : Pilih stadium dari list",
            "98          : Next page",
            "99          : Prev page",
            "0           : Back"
        ]),
        ("EDIT STADIUM", [
            "1           : Edit nama",
            "2           : Edit capacity",
            "3           : Edit expansion capacity",
            "0           : Back",
            "",
            "Data ditampilkan:",
            "- ID, UID, City ID",
            "- Capacity (kapasitas)",
            "- Expansion Capacity",
            "- Name, Name2"
        ])
    ]
    show_help_text("🏟️ STADIUM EDITOR", sections)


def mode_stadium_simple(app: "App"):
    """Stadium editor - termux friendly."""
    
    while True:
        items = [f"{s.name} (Cap: {s.capacity:,})" for s in app.stadiums.items]
        
        clear_screen()
        print_header("🏟️ STADIUM EDITOR")
        print_info("[?] Help | [0] Back\n")
        
        selected = show_numbered_list(items, "Pilih Stadium")
        
        if selected < 0:
            break
        
        stadium = app.stadiums.items[selected]
        edit_stadium(app, stadium)


def edit_stadium(app: "App", s):
    """Edit stadium fields."""
    while True:
        clear_screen()
        print_header(f"🏟️ {s.name}")
        
        print(f"  ID: {s.id}")
        print(f"  UID: {s.uid}")
        print(f"  City ID: {s.city_id}")
        print(f"  Capacity: {s.capacity:,}")
        print(f"  Expansion: {s.expansion_capacity:,}")
        print(f"  Name2: {s.name2}")
        
        print_info("\n[1] Edit name | [2] Edit capacity | [3] Edit expansion | [h] Help | [0] Back")
        
        cmd = get_input(">>", "bold green")
        
        if cmd == "0":
            break
        
        if cmd.lower() == "h":
            show_help_stadium()
            continue
        
        elif cmd == "1":
            val = get_input("Nama baru", "bold cyan")
            if val:
                s.name = val
                app.dirty_stadiums = True
                print_success("Updated")
        
        elif cmd == "2":
            val = get_input("Capacity", "bold cyan")
            if val.isdigit():
                s.capacity = int(val)
                app.dirty_stadiums = True
                print_success("Updated")
        
        elif cmd == "3":
            val = get_input("Expansion Capacity", "bold cyan")
            if val.isdigit():
                s.expansion_capacity = int(val)
                app.dirty_stadiums = True
                print_success("Updated")
