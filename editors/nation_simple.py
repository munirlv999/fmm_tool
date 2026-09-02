"""Nation editor - Termux friendly version."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.app import App

from ..ui.console import (
    RICH_AVAILABLE, console, print_header, print_success, 
    print_error, print_warning, print_info, get_input, clear_screen,
    show_numbered_list, show_help_text, wait_enter
)


def show_help_nation():
    """Show help for nation editor."""
    sections = [
        ("NAVIGASI", [
            "1-xx        : Pilih negara dari list",
            "98          : Next page",
            "99          : Prev page",
            "0           : Back"
        ]),
        ("EDIT FIELD", [
            "[no] [val]  : Edit field",
            "m           : Edit Male Team",
            "f           : Edit Female Team",
            "0           : Selesai / Back",
            "",
            "Contoh:",
            "  1 Italy           : Ubah Name",
            "  2 Italian         : Ubah Nationality",
            "  4 1               : Ubah ContinentId",
            "  6 15000           : Ubah StadiumId"
        ]),
        ("MALE/FEMALE TEAM", [
            "Edit data tim nasional:",
            "1=GameImportance  2=RivalId      3=IsRanked",
            "4=Ranking         5=Points       6=Color1",
            "7=Color2",
            "",
            "Contoh:",
            "  4 5    : Ranking = 5",
            "  5 1500 : Points = 1500"
        ])
    ]
    show_help_text("🌍 NATION EDITOR", sections)


def show_nation_detail(app: "App", n):
    """Show nation details."""
    clear_screen()
    print_header(f"🌍 {n.name}", f"Nationality: {n.nationality} | Code: {n.codename}")
    
    print_info(f"ID: {n.id} | UID: {n.uid} | Continent: {n.continent_id}")
    print_info(f"Capital: {n.capital_id} | Stadium: {n.stadium_id}")
    print_info(f"State Dev: {n.state_dev} | Region: {n.region}")
    
    if n.has_male_team and n.male_team:
        mt = n.male_team
        print_info(f"\n👨 Male Team: Rank {mt.ranking} | Points {mt.points} | Ranked: {mt.is_ranked}")
    
    if n.has_female_team and n.female_team:
        ft = n.female_team
        print_info(f"\n👩 Female Team: Rank {ft.ranking} | Points {ft.points}")


def edit_nation_fields(app: "App", n):
    """Edit nation fields."""
    while True:
        clear_screen()
        print_header(f"Edit Nation: {n.name}")
        
        fields = [
            ("1", "Name", n.name),
            ("2", "Nationality", n.nationality),
            ("3", "CodeName", n.codename),
            ("4", "ContinentId", n.continent_id),
            ("5", "CapitalId", n.capital_id),
            ("6", "StadiumId", n.stadium_id),
            ("7", "StateDev", n.state_dev),
            ("8", "Region", n.region),
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
        
        if n.has_male_team and n.male_team:
            mt = n.male_team
            print(f"\n  Male Team:")
            print(f"    Ranking: {mt.ranking}, Points: {mt.points}, Rival: {mt.rival_id}")
        
        print_info("\n[no] [value] = edit | [m] = male team | [f] = female team | [h] = help | [0] = back")
        
        cmd = get_input(">>", "bold green")
        if not cmd:
            continue
        
        if cmd == "0":
            break
        
        if cmd.lower() == "h":
            show_help_nation()
            continue
        
        if cmd.lower() == "m":
            edit_team(app, n, "male")
            continue
        
        if cmd.lower() == "f":
            edit_team(app, n, "female")
            continue
        
        parts = cmd.split(maxsplit=1)
        if len(parts) != 2:
            print_warning("Format: [no] [value]")
            continue
        
        field_no, value = parts
        
        try:
            field_map = {
                "1": ("name", str),
                "2": ("nationality", str),
                "3": ("codename", str),
                "4": ("continent_id", int),
                "5": ("capital_id", int),
                "6": ("stadium_id", int),
                "7": ("state_dev", int),
                "8": ("region", int),
            }
            
            if field_no in field_map:
                attr, typ = field_map[field_no]
                setattr(n, attr, typ(value))
                app.dirty_nations = True
                print_success(f"{attr} = {value}")
        except Exception as e:
            print_error(str(e))


def edit_team(app: "App", n, team_type: str):
    """Edit male/female team."""
    if team_type == "male":
        if not n.has_male_team:
            print_info("Creating male team...")
            from ..core.models import NationalTeamRec
            n.has_male_team = True
            n.male_team = NationalTeamRec(0, 0, 0, 0, 0, -1, 0, True, 0, 0, 0, [], b"\x00" * 11)
        team = n.male_team
        title = "Male Team"
    else:
        if not n.has_female_team:
            print_info("Creating female team...")
            from ..core.models import NationalTeamRec
            n.has_female_team = True
            n.female_team = NationalTeamRec(0, 0, 0, 0, 0, -1, 0, True, 0, 0, 0, [], b"\x00" * 11)
        team = n.female_team
        title = "Female Team"
    
    while True:
        clear_screen()
        print_header(f"🏆 {title} - {n.name}")
        
        fields = [
            ("1", "GameImportance", team.game_importance),
            ("2", "RivalId", team.rival_id),
            ("3", "IsRanked", team.is_ranked),
            ("4", "Ranking", team.ranking),
            ("5", "Points", team.points),
            ("6", "Color1", team.color1),
            ("7", "Color2", team.color2),
        ]
        
        for num, name, val in fields:
            print(f"{num:>3}. {name:18} {val}")
        
        print_info("\n[no] [value] = edit | [0] = back")
        
        cmd = get_input(">>", "bold green")
        if cmd == "0":
            break
        
        parts = cmd.split(maxsplit=1)
        if len(parts) != 2:
            continue
        
        field_no, value = parts
        
        try:
            if field_no == "1":
                team.game_importance = int(value)
            elif field_no == "2":
                team.rival_id = int(value)
            elif field_no == "3":
                team.is_ranked = value.lower() in ("1", "true", "yes")
            elif field_no == "4":
                team.ranking = int(value)
            elif field_no == "5":
                team.points = int(value)
            elif field_no == "6":
                team.color1 = int(value)
            elif field_no == "7":
                team.color2 = int(value)
            
            app.dirty_nations = True
            print_success(f"Updated")
        except Exception as e:
            print_error(str(e))


def mode_nation_simple(app: "App"):
    """Nation editor - termux friendly."""
    
    while True:
        items = [f"{n.name} ({n.nationality})" for n in app.nations.items]
        
        clear_screen()
        print_header("🌍 NATION EDITOR")
        print_info("[?] Help | [0] Back")
        print("")
        
        selected = show_numbered_list(items, "Pilih Nation")
        
        if selected < 0:
            break
        
        edit_nation_fields(app, app.nations.items[selected])
