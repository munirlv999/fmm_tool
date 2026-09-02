"""Region editor - Termux friendly version."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.app import App

from ..ui.console import (
    print_header, print_success, print_error, print_warning, 
    print_info, get_input, clear_screen, show_numbered_list,
    show_help_text, wait_enter
)


def show_help_region():
    """Show help for region editor."""
    sections = [
        ("NAVIGASI", [
            "1-xx        : Pilih region dari list",
            "98          : Next page",
            "99          : Prev page",
            "0           : Back"
        ]),
        ("EDIT REGION", [
            "1           : Edit nama",
            "2           : Edit nation ID",
            "3           : Edit weather ID",
            "0           : Back",
            "",
            "Data ditampilkan:",
            "- ID, UID",
            "- Name (nama region)",
            "- Nation (negara)",
            "- Weather ID"
        ])
    ]
    show_help_text("📍 REGION EDITOR", sections)


def mode_region_simple(app: "App"):
    """Region editor - termux friendly."""
    
    while True:
        items = [f"{r.name} ({app.nation_name(r.nation_id)})" for r in app.regions.items]
        
        clear_screen()
        print_header("📍 REGION EDITOR")
        print_info("[?] Help | [0] Back\n")
        
        selected = show_numbered_list(items, "Pilih Region")
        
        if selected < 0:
            break
        
        region = app.regions.items[selected]
        edit_region(app, region)


def edit_region(app: "App", r):
    """Edit region fields."""
    while True:
        clear_screen()
        print_header(f"📍 {r.name}")
        
        print(f"  ID: {r.id}")
        print(f"  UID: {r.uid}")
        print(f"  Nation: {app.nation_name(r.nation_id)} ({r.nation_id})")
        print(f"  Weather ID: {r.weather_id}")
        
        print_info("\n[1] Edit name | [2] Edit nation | [3] Edit weather | [h] Help | [0] Back")
        
        cmd = get_input(">>", "bold green")
        
        if cmd == "0":
            break
        
        if cmd.lower() == "h":
            show_help_region()
            continue
        
        elif cmd == "1":
            val = get_input("Nama baru", "bold cyan")
            if val:
                r.name = val
                app.dirty_regions = True
                print_success("Updated")
        
        elif cmd == "2":
            val = get_input("Nation ID", "bold cyan")
            if val.isdigit():
                r.nation_id = int(val)
                app.dirty_regions = True
                print_success("Updated")
        
        elif cmd == "3":
            val = get_input("Weather ID", "bold cyan")
            if val.isdigit():
                r.weather_id = int(val)
                app.dirty_regions = True
                print_success("Updated")
