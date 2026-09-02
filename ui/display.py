"""Display functions for FMM Tool."""

from typing import TYPE_CHECKING

from .console import RICH_AVAILABLE, console, print_warning, print_info
from ..utils.date import describe_date
from ..utils.ethnicity import eth_show
from ..utils.helpers import club_status_show, bytes_to_hex


if TYPE_CHECKING:
    from ..core.app import App
    from ..core.models import People, Player, NationRec, ClubRec, CompetitionRec, StadiumRec, RegionRec, NationalTeamRec


def rel_list(app: "App", p: "People"):
    """Display relationships list."""
    if not p.relationships:
        print_info("Relationships kosong.")
        return
    
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.box import SIMPLE_HEAVY
        
        table = Table(title="[bold cyan]🔗 Relationships[/bold cyan]", box=SIMPLE_HEAVY, border_style="cyan")
        table.add_column("No", style="bold green", justify="center")
        table.add_column("Level", style="white")
        table.add_column("Type", style="white")
        table.add_column("UID", style="yellow")
        table.add_column("Name", style="cyan")
        table.add_column("Reason", style="white")
        
        for i, rel in enumerate(p.relationships, 1):
            nm = app.people_name_by_uid(rel.uid)
            table.add_row(str(i), str(rel.level), str(rel.type), str(rel.uid), nm, str(rel.reason))
        console.print(table)
    else:
        for i, rel in enumerate(p.relationships, 1):
            nm = app.people_name_by_uid(rel.uid)
            print(f"{i:02d}. level={rel.level} type={rel.type} unk={rel.unknown} uid={rel.uid} ({nm}) reason={rel.reason}")


def get_stat_bar(value: int, max_val: int = 20) -> str:
    """Create visual stat bar."""
    if RICH_AVAILABLE:
        filled = int((value / max_val) * 10)
        empty = 10 - filled
        color = "green" if value >= 15 else "yellow" if value >= 10 else "red"
        return f"[bold {color}]{'█' * filled}[/bold {color}][dim]{'░' * empty}[/dim]"
    return str(value)


def show_people_block(app: "App", p: "People", idx: int):
    """Display people block."""
    from ..core.constants import PEOPLE_FIELDS
    
    disp = app.people_display_name(p)
    eff_id = idx if p.id == -1 else p.id
    club_nm = app.club_name_from_people(p)
    nation_nm = app.nation_name(p.nation_id)
    
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich.box import SIMPLE_HEAVY
        
        # Header panel
        header = Text()
        header.append(f"Name: ", style="dim")
        header.append(f"{disp}\n", style="bold cyan")
        header.append(f"Index: ", style="dim")
        header.append(f"{idx}  ", style="white")
        header.append(f"UID: ", style="dim")
        header.append(f"{p.uid}\n", style="white")
        header.append(f"Club: ", style="dim")
        header.append(f"{club_nm}  ", style="green")
        header.append(f"Nation: ", style="dim")
        header.append(f"{nation_nm}", style="yellow")
        console.print(Panel(header, title="[bold cyan]👤 PLAYER INFO[/bold cyan]", border_style="cyan"))
        
        # Fields table
        table = Table(box=SIMPLE_HEAVY, border_style="blue", show_lines=False, padding=(0, 1))
        table.add_column("No", style="bold green", justify="center", width=3)
        table.add_column("Field", style="cyan", width=18)
        table.add_column("Value", style="white")
        
        for i, (label, attr) in enumerate(PEOPLE_FIELDS, 1):
            v = getattr(p, attr)
            if label == "FirstName":
                val = f"{app.name_first(v)} ({v})"
            elif label == "LastName":
                val = f"{app.name_second(v)} ({v})"
            elif label == "CommonName":
                val = "-" if v == -1 else f"{app.name_common(v)} ({v})"
            elif label in ("DateOfBirth", "JoinedDate"):
                val = describe_date(v)
            elif label == "Ethnicity":
                val = eth_show(v)
            elif label in ("DefaultLanguages", "OtherLanguages"):
                out = [f"{lid}:{prof}({app.lang_name(lid)})" for lid, prof in v]
                val = ", ".join(out) if out else "-"
            elif label == "Relationships":
                val = f"{len(v)} relationships"
            else:
                val = str(v)
            table.add_row(str(i), label, val)
        console.print(table)
    else:
        from ..utils.helpers import C, col
        print(col("\nPEOPLE", C.BD + C.CY))
        print(f"Index: {idx}  ID: {eff_id}  UID: {p.uid}")
        print(f"Name: {disp}")
        print(f"Club: {club_nm}  Nation: {nation_nm}")
        for i, (label, attr) in enumerate(PEOPLE_FIELDS, 1):
            v = getattr(p, attr)
            print(f"{i:02d}. {label}: {v}")


def show_player_block(app: "App", pl: "Player"):
    """Display player stats block."""
    from ..core.constants import PEOPLE_FIELDS, PLAYER_FIELDS
    
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.text import Text
        from rich.box import SIMPLE_HEAVY
        
        table = Table(title="[bold magenta]⚽ PLAYER STATS[/bold magenta]",
                     box=SIMPLE_HEAVY, border_style="magenta", show_lines=False, padding=(0, 1))
        table.add_column("No", style="bold green", justify="center", width=3)
        table.add_column("Attribute", style="cyan", width=18)
        table.add_column("Value", style="white", justify="right")
        
        base = len(PEOPLE_FIELDS)
        for j, (label, attr) in enumerate(PLAYER_FIELDS, 1):
            v = getattr(pl, attr)
            style = "white"
            if label in ("CA", "PA"):
                style = "bold yellow" if v >= 150 else "green" if v >= 130 else "white"
            elif label in ("Finishing", "Dribbling", "Pace", "Technique"):
                style = "bold green" if v >= 15 else "white"
            table.add_row(str(base + j), label, Text(str(v), style=style))
        console.print(table)
    else:
        from ..utils.helpers import C, col
        print(col("\nPLAYER STATS", C.BD + C.M))
        base = len(PEOPLE_FIELDS)
        for j, (label, attr) in enumerate(PLAYER_FIELDS, 1):
            v = getattr(pl, attr)
            print(f"{base + j:02d}. {label}: {v}")


def show_selected_player_editor(app: "App"):
    """Show selected player in editor."""
    if app.cur_people_idx is None:
        print_warning("Belum pilih orang. Ketik UID atau nama.")
        return
    
    p = app.people.items[app.cur_people_idx]
    show_people_block(app, p, app.cur_people_idx)
    
    pl = app.player_by_id.get(p.player_id)
    if pl:
        show_player_block(app, pl)
    else:
        print_warning("PLAYER (tidak ditemukan untuk PlayerId di People)")


def show_team_block(prefix_no: int, team: "NationalTeamRec"):
    """Display team sub-block."""
    from ..core.constants import TEAM_SUBFIELDS
    
    letter_map = {k: (label, attr) for k, label, attr in TEAM_SUBFIELDS}
    
    def line(letter: str, value_str: str):
        if RICH_AVAILABLE:
            console.print(f"   [dim]{prefix_no}{letter}.[/dim] [cyan]{letter_map[letter][1]}:[/cyan] {value_str}")
        else:
            print(f"   {prefix_no}{letter}. {letter_map[letter][1]}: {value_str}")
    
    line("a", str(team.game_importance))
    line("b", str(team.rival_id))
    line("c", str(team.is_ranked))
    line("d", str(team.ranking))
    line("e", str(team.points))
    line("f", ";".join([str(x) for x in team.coefficients]) if team.coefficients else "")
    line("g", str(team.color1))
    line("h", str(team.color2))
    line("i", str(team.color3))
    line("j", str(team.color4))
    line("k", str(team.unknown4))
    line("l", str(team.unknown5))
    
    from ..utils.helpers import bytes_to_hex
    line("m", bytes_to_hex(team.unknown6 if team.unknown6 else b"\x00" * 11))


def show_nation_block(app: "App", n: "NationRec"):
    """Display nation block."""
    from ..core.constants import NATION_FIELDS
    
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich.box import SIMPLE_HEAVY
        
        header = Text()
        header.append(f"{n.name}\n", style="bold cyan")
        header.append(f"ID: {n.id}  |  UID: {n.uid}  |  Code: {n.codename}", style="dim")
        console.print(Panel(header, title="[bold cyan]🌍 NATION[/bold cyan]", border_style="cyan"))
        
        table = Table(box=SIMPLE_HEAVY, border_style="blue", show_lines=False, padding=(0, 1))
        table.add_column("No", style="bold green", justify="center", width=4)
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        for i, (label, attr) in enumerate(NATION_FIELDS, 1):
            v = getattr(n, attr)
            if label == "Languages":
                out = [f"{lid}:{prof}({app.lang_name(lid)})" for lid, prof in v]
                val = ", ".join(out) if out else "-"
            elif label == "StadiumId":
                val = f"{v} ({app.stadium_name(v)})"
            elif label == "MaleTeam":
                val = "Present" if v else "None"
            elif label == "FemaleTeam":
                val = "Present" if v else "None"
            else:
                val = str(v)
            table.add_row(str(i), label, val)
        console.print(table)
        
        if n.male_team:
            console.print("\n[bold cyan]Male Team Details:[/bold cyan]")
            show_team_block(18, n.male_team)
        if n.female_team:
            console.print("\n[bold cyan]Female Team Details:[/bold cyan]")
            show_team_block(20, n.female_team)
    else:
        from ..utils.helpers import C, col
        print(col("\nNATION", C.BD + C.CY))
        print(f"Name: {n.name}  ID: {n.id}")
        for i, (label, attr) in enumerate(NATION_FIELDS, 1):
            v = getattr(n, attr)
            if label == "StadiumId":
                print(f"{i:02d}. StadiumId: {v} ({app.stadium_name(v)})")
            elif label == "MaleTeam":
                print(f"{i:02d}. MaleTeam:")
                if v:
                    show_team_block(i, v)
            elif label == "FemaleTeam":
                print(f"{i:02d}. FemaleTeam:")
                if v:
                    show_team_block(i, v)
            else:
                print(f"{i:02d}. {label}: {v}")


def show_club_block(app: "App", c: "ClubRec", idx: int):
    """Display club block."""
    from ..core.constants import CLUB_FIELDS
    
    eff_id = idx if c.id == -1 else c.id
    
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich.box import SIMPLE_HEAVY
        
        header = Text()
        header.append(f"{c.full_name}\n", style="bold cyan")
        header.append(f"Index: {idx}  |  EffId: {eff_id}  |  Stadium: {app.stadium_name(c.stadium)}", style="dim")
        console.print(Panel(header, title="[bold cyan]🏟️ CLUB[/bold cyan]", border_style="cyan"))
        
        table = Table(box=SIMPLE_HEAVY, border_style="blue", show_lines=False, padding=(0, 1))
        table.add_column("No", style="bold green", justify="center", width=4)
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        for i, (label, attr) in enumerate(CLUB_FIELDS, 1):
            v = getattr(c, attr)
            if label == "NationId":
                val = f"{v} ({app.nation_name(v)})"
            elif label == "Stadium":
                val = f"{v} ({app.stadium_name(v)})"
            elif label == "Status":
                val = club_status_show(v)
            elif label == "Players":
                val = f"{len(v)} players"
            elif label == "Affiliates":
                val = f"{len(v)} affiliates"
            else:
                val = str(v)
            table.add_row(str(i), label, val)
        console.print(table)
    else:
        from ..utils.helpers import C, col
        print(col("\nCLUB", C.BD + C.CY))
        print(f"Index: {idx}  EffId: {eff_id}")
        print(f"Name: {c.full_name}")
        for i, (label, attr) in enumerate(CLUB_FIELDS, 1):
            v = getattr(c, attr)
            print(f"{i:02d}. {label}: {v}")


def show_competition_block(app: "App", c: "CompetitionRec", idx: int):
    """Display competition block."""
    from ..core.constants import COMPETITION_FIELDS

    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich.box import SIMPLE_HEAVY

        header = Text()
        header.append(f"{c.full_name}\n", style="bold cyan")
        header.append(f"Index: {idx}  |  ID: {c.id}  |  Nation: {app.nation_name(c.nation_id)}", style="dim")
        console.print(Panel(header, title="[bold cyan]🏆 COMPETITION[/bold cyan]", border_style="cyan"))

        table = Table(box=SIMPLE_HEAVY, border_style="blue", show_lines=False, padding=(0, 1))
        table.add_column("No", style="bold green", justify="center", width=4)
        table.add_column("Field", style="cyan", width=22)
        table.add_column("Value", style="white")

        for i, (label, attr) in enumerate(COMPETITION_FIELDS, 1):
            v = getattr(c, attr)
            if label == "NationId":
                val = f"{v} ({app.nation_name(v)})"
            elif label in ("ForegroundColor", "BackgroundColor"):
                val = f"{v} (0x{v:04X})"
            elif label == "Qualifiers":
                val = f"{len(v)} entries"
            else:
                val = str(v)
            table.add_row(str(i), label, val)
        console.print(table)
    else:
        from ..utils.helpers import C, col
        print(col("\nCOMPETITION", C.BD + C.CY))
        print(f"Index: {idx}  ID: {c.id}  Name: {c.full_name}")
        for i, (label, attr) in enumerate(COMPETITION_FIELDS, 1):
            v = getattr(c, attr)
            print(f"{i:02d}. {label}: {v}")


def show_stadium_block(app: "App", s: "StadiumRec", idx: int):
    """Display stadium block."""
    from ..core.constants import STADIUM_FIELDS
    
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich.box import SIMPLE_HEAVY
        
        header = Text()
        header.append(f"{s.name}\n", style="bold cyan")
        header.append(f"Index: {idx}  |  ID: {s.id}  |  Capacity: {s.capacity:,}", style="dim")
        console.print(Panel(header, title="[bold cyan]🏟️ STADIUM[/bold cyan]", border_style="cyan"))
        
        table = Table(box=SIMPLE_HEAVY, border_style="blue", show_lines=False, padding=(0, 1))
        table.add_column("No", style="bold green", justify="center", width=4)
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        for i, (label, attr) in enumerate(STADIUM_FIELDS, 1):
            v = getattr(s, attr)
            table.add_row(str(i), label, str(v))
        console.print(table)
    else:
        from ..utils.helpers import C, col
        print(col("\nSTADIUM", C.BD + C.CY))
        print(f"Index: {idx}")
        for i, (label, attr) in enumerate(STADIUM_FIELDS, 1):
            v = getattr(s, attr)
            print(f"{i:02d}. {label}: {v}")


def show_region_block(app: "App", r: "RegionRec", idx: int):
    """Display region block."""
    from ..core.constants import REGION_FIELDS
    
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich.box import SIMPLE_HEAVY
        
        header = Text()
        header.append(f"{r.name}\n", style="bold cyan")
        header.append(f"Index: {idx}  |  ID: {r.id}  |  Nation: {app.nation_name(r.nation_id)}", style="dim")
        console.print(Panel(header, title="[bold cyan]📍 REGION[/bold cyan]", border_style="cyan"))
        
        table = Table(box=SIMPLE_HEAVY, border_style="blue", show_lines=False, padding=(0, 1))
        table.add_column("No", style="bold green", justify="center", width=4)
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        for i, (label, attr) in enumerate(REGION_FIELDS, 1):
            v = getattr(r, attr)
            if label == "NationId":
                val = f"{v} ({app.nation_name(v)})"
            else:
                val = str(v)
            table.add_row(str(i), label, val)
        console.print(table)
    else:
        from ..utils.helpers import C, col
        print(col("\nREGION", C.BD + C.CY))
        print(f"Index: {idx}")
        for i, (label, attr) in enumerate(REGION_FIELDS, 1):
            v = getattr(r, attr)
            if label == "NationId":
                print(f"{i:02d}. NationId: {v} ({app.nation_name(v)})")
            else:
                print(f"{i:02d}. {label}: {v}")
