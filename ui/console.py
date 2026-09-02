"""Console UI utilities with Rich support."""

from __future__ import annotations

import os
from typing import List, Tuple, Optional

# Rich UI imports
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    from rich.box import ROUNDED, SIMPLE_HEAVY
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Console setup
if RICH_AVAILABLE:
    console = Console()
else:
    console = None


# ANSI Fallback colors
class C:
    R = "\x1b[31m"
    G = "\x1b[32m"
    Y = "\x1b[33m"
    B = "\x1b[34m"
    M = "\x1b[35m"
    CY = "\x1b[36m"
    W = "\x1b[37m"
    GR = "\x1b[90m"
    RS = "\x1b[0m"
    BD = "\x1b[1m"


def col(txt: str, cc: str) -> str:
    """Colorize text."""
    return f"{cc}{txt}{C.RS}"


def clear_screen():
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str, subtitle: str = ""):
    """Print header with style."""
    if RICH_AVAILABLE:
        header_text = Text()
        header_text.append(f"⚽ {title}", style="bold cyan")
        if subtitle:
            header_text.append(f"\n{subtitle}", style="dim white")
        console.print(Panel(header_text, box=ROUNDED, border_style="cyan", padding=(1, 2)))
    else:
        print(col(f"\n{'='*50}", C.CY))
        print(col(f"  {title}", C.BD + C.CY))
        if subtitle:
            print(col(f"  {subtitle}", C.GR))
        print(col(f"{'='*50}\n", C.CY))


def print_success(msg: str):
    """Print success message."""
    if RICH_AVAILABLE:
        console.print(f"[bold green]✓[/bold green] {msg}")
    else:
        print(col(f"✓ {msg}", C.G))


def print_error(msg: str):
    """Print error message."""
    if RICH_AVAILABLE:
        console.print(f"[bold red]✗[/bold red] {msg}")
    else:
        print(col(f"✗ {msg}", C.R))


def print_warning(msg: str):
    """Print warning message."""
    if RICH_AVAILABLE:
        console.print(f"[bold yellow]⚠[/bold yellow] {msg}")
    else:
        print(col(f"⚠ {msg}", C.Y))


def print_info(msg: str):
    """Print info message."""
    if RICH_AVAILABLE:
        console.print(f"[dim]ℹ[/dim] {msg}")
    else:
        print(col(f"ℹ {msg}", C.GR))


def print_panel(content: str, title: str = "", border_style: str = "cyan"):
    """Print panel with content."""
    if RICH_AVAILABLE:
        console.print(Panel(content, title=title, border_style=border_style, box=ROUNDED))
    else:
        if title:
            print(col(f"\n[{title}]", C.BD + C.CY))
        print(content)
        print("")


def get_input(prompt: str, style: str = "bold green") -> str:
    """Get user input with styled prompt."""
    if RICH_AVAILABLE:
        return console.input(f"[{style}]{prompt}[/{style}] ").strip()
    else:
        return input(col(prompt, C.G)).strip()


def create_menu_table(title: str, options: List[Tuple[str, str, str]]) -> Table:
    """Create menu table."""
    table = Table(
        title=title,
        box=ROUNDED,
        border_style="cyan",
        header_style="bold cyan",
        padding=(0, 2),
        show_header=False
    )
    table.add_column("No", style="bold green", justify="center", width=4)
    table.add_column("Menu", style="bold white", width=20)
    table.add_column("Description", style="dim", width=30)
    
    for no, name, desc in options:
        table.add_row(no, name, desc)
    
    return table


def create_data_table(title: str, columns: List[Tuple[str, str]]) -> Table:
    """Create data table."""
    table = Table(
        title=title,
        box=SIMPLE_HEAVY,
        border_style="blue",
        header_style="bold cyan",
        padding=(0, 1),
        show_lines=True
    )
    
    for col_name, style in columns:
        table.add_column(col_name, style=style)
    
    return table


def show_help_text(title: str, sections: List[Tuple[str, List[str]]]):
    """
    Display help text in a formatted way.
    sections: [(section_title, [lines...]), ...]
    """
    clear_screen()
    
    if RICH_AVAILABLE:
        from rich.panel import Panel
        from rich.text import Text
        
        console.print(Panel(f"[bold cyan]❓ {title} - HELP[/bold cyan]", border_style="cyan"))
        
        for section_title, lines in sections:
            console.print(f"\n[bold yellow]{section_title}[/bold yellow]")
            for line in lines:
                if line.startswith("  "):
                    console.print(f"[dim]{line}[/dim]")
                elif ":" in line and not line.startswith(" "):
                    parts = line.split(":", 1)
                    console.print(f"  [bold green]{parts[0]}[/bold green]:[white]{parts[1]}[/white]")
                else:
                    console.print(f"  [white]{line}[/white]")
        
        console.print("\n[dim]Tekan Enter untuk kembali...[/dim]")
    else:
        print(f"\n{'='*50}")
        print(f"? {title} - HELP")
        print('='*50)
        
        for section_title, lines in sections:
            print(f"\n{section_title}:")
            for line in lines:
                print(line)
        
        print("\nTekan Enter untuk kembali...")
    
    try:
        input("")
    except (EOFError, KeyboardInterrupt):
        pass


def wait_enter():
    """Wait for enter press."""
    try:
        input("" if RICH_AVAILABLE else "Tekan Enter...")
    except (EOFError, KeyboardInterrupt):
        pass


# ==================== TERMUX FRIENDLY HELPERS ====================

def show_numbered_list(items: List[str], title: str = "", per_page: int = 20) -> int:
    """
    Show numbered list and let user select by number.
    Returns selected index or -1 for back.
    """
    if not items:
        print_warning("List kosong.")
        return -1
    
    total = len(items)
    page = 0
    max_page = (total - 1) // per_page
    
    while True:
        clear_screen()
        if title:
            print_header(title, f"Page {page+1}/{max_page+1} | Total: {total}")
        
        start = page * per_page
        end = min(start + per_page, total)
        
        if RICH_AVAILABLE:
            from rich.table import Table
            from rich import box
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            table.add_column("No", style="bold green", width=4, justify="right")
            table.add_column("Item", style="white")
            for i in range(start, end):
                table.add_row(str(i - start + 1), items[i])
            console.print(table)
        else:
            for i in range(start, end):
                print(f"{i - start + 1:2d}. {items[i]}")
        
        # Navigation hints
        nav_options = []
        if page > 0:
            nav_options.append("[99] Prev")
        if page < max_page:
            nav_options.append("[98] Next")
        nav_options.append("[0] Back")
        
        print_info(f"Pilih 1-{end-start} | {' | '.join(nav_options)}")
        
        try:
            choice = get_input(">>", "bold green")
        except (EOFError, KeyboardInterrupt):
            return -1
        
        if not choice:
            continue
        
        if choice == "0":
            return -1
        elif choice == "99" and page > 0:
            page -= 1
        elif choice == "98" and page < max_page:
            page += 1
        elif choice.isdigit():
            num = int(choice)
            if 1 <= num <= (end - start):
                return start + num - 1
        
        print_warning("Pilihan tidak valid")


def edit_field_menu(fields: List[Tuple[str, str, str]], current_values: dict, title: str = "Edit") -> dict:
    """
    Simple field editor with numbered menu.
    fields: [(number, field_name, current_value), ...]
    Returns dict of changed fields.
    """
    changes = {}
    
    while True:
        clear_screen()
        print_header(title, "Pilih field untuk edit (0 untuk save & exit)")
        
        if RICH_AVAILABLE:
            from rich.table import Table
            from rich import box
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            table.add_column("No", style="bold green", width=4, justify="right")
            table.add_column("Field", style="cyan", width=20)
            table.add_column("Value", style="white")
            for num, name, val in fields:
                display_val = str(val)[:40] if val is not None else "-"
                if num in changes:
                    display_val += f" [green]→ {changes[num]}[/green]"
                table.add_row(num, name, display_val)
            console.print(table)
        else:
            for num, name, val in fields:
                display_val = str(val)[:40] if val is not None else "-"
                marker = " *" if num in changes else ""
                print(f"{num:>2}. {name:20} {display_val}{marker}")
        
        print_info("[0] Save & Exit | [field_no] [value] untuk edit")
        
        try:
            cmd = get_input(">>", "bold green")
        except (EOFError, KeyboardInterrupt):
            return changes
        
        if not cmd:
            continue
        
        parts = cmd.split(maxsplit=1)
        if not parts:
            continue
        
        if parts[0] == "0":
            return changes
        
        field_no = parts[0]
        matching = [(n, name, val) for n, name, val in fields if n == field_no]
        
        if not matching:
            print_warning(f"Field {field_no} tidak ditemukan")
            continue
        
        if len(parts) < 2:
            print_warning("Format: [no] [value]")
            continue
        
        changes[field_no] = parts[1]
        print_success(f"Field {field_no} = {parts[1]}")


def quick_search(prompt: str = "Cari") -> str:
    """Simple search input."""
    try:
        return get_input(f"{prompt} (kosong=batal)", "bold cyan")
    except (EOFError, KeyboardInterrupt):
        return ""
