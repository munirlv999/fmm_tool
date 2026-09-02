"""Name tool - Termux friendly version."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.app import App

from ..core.models import NameRec
from ..ui.console import (
    RICH_AVAILABLE, console, print_header, print_success, 
    print_error, print_warning, print_info, get_input, clear_screen,
    show_numbered_list, show_help_text, wait_enter
)


def show_help_name():
    """Show help for name tool."""
    sections = [
        ("MENU UTAMA", [
            "1           : First Names (nama depan)",
            "2           : Second Names (nama belakang)",
            "3           : Common Names (nama panggilan)",
            "0           : Back"
        ]),
        ("SUB-MENU TIAP TIPE", [
            "1           : Cari nama",
            "2           : List semua (dengan next/prev)",
            "3           : Tambah nama baru",
            "0           : Back"
        ]),
        ("EDIT NAMA", [
            "1           : Edit value (nama)",
            "2           : Edit gender (0=male, 1=female)",
            "3           : Edit nation UID",
            "0           : Back"
        ]),
        ("TAMBAH NAMA BARU", [
            "Input: Nama, Nation UID (default 0), Gender (default 0)",
            "ID otomatis di-generate (max existing + 1)"
        ])
    ]
    show_help_text("📝 NAME TOOL", sections)


def mode_name_simple(app: "App"):
    """Name tool - termux friendly."""
    
    name_types = [
        ("1", "First Names", app.first_names, app.first_by_id, "first"),
        ("2", "Second Names", app.second_names, app.second_by_id, "second"),
        ("3", "Common Names", app.common_names, app.common_by_id, "common"),
    ]
    
    while True:
        clear_screen()
        print_header("📝 NAME TOOL")
        
        print_info("[?] Help | [0] Back\n")
        
        for num, label, dat, _, _ in name_types:
            print(f"  {num}. {label} ({len(dat.items)} items)")
        
        print("")
        
        choice = get_input(">>", "bold green")
        
        if choice == "?":
            show_help_name()
            continue
        
        if choice == "0":
            break
        
        selected = None
        for num, label, dat, by_id, key in name_types:
            if choice == num:
                selected = (label, dat, by_id, key)
                break
        
        if not selected:
            continue
        
        label, dat, by_id, key = selected
        edit_name_list(app, label, dat, by_id, key)


def edit_name_list(app: "App", label, dat, by_id, key):
    """Edit specific name list."""
    
    while True:
        clear_screen()
        print_header(f"📝 {label}")
        
        print_info("[1] Cari | [2] List semua | [3] Tambah baru | [0] Back")
        cmd = get_input(">>", "bold green")
        
        if cmd == "0":
            break
        
        elif cmd == "1":
            query = get_input("Cari nama", "bold cyan")
            if not query:
                continue
            
            results = [(i, n) for i, n in enumerate(dat.items) if query.lower() in n.value.lower()]
            
            if not results:
                print_warning("Tidak ditemukan")
                input("Enter...")
                continue
            
            items = [f"ID:{n.id} - {n.value}" for _, n in results]
            selected_idx = show_numbered_list(items, f"Hasil: {query}")
            
            if selected_idx >= 0:
                edit_name_record(app, dat, by_id, results[selected_idx][1], key)
        
        elif cmd == "2":
            items = [f"ID:{n.id} - {n.value}" for n in dat.items]
            selected_idx = show_numbered_list(items, label)
            
            if selected_idx >= 0:
                edit_name_record(app, dat, by_id, dat.items[selected_idx], key)
        
        elif cmd == "3":
            add_new_name(app, dat, by_id, key)


def edit_name_record(app: "App", dat, by_id, rec: NameRec, key):
    """Edit single name record."""
    while True:
        clear_screen()
        print_header(f"Edit: {rec.value}")
        
        print(f"  ID: {rec.id}")
        print(f"  Value: {rec.value}")
        print(f"  Gender: {rec.gender}")
        print(f"  NationUID: {rec.nation_uid}")
        
        print_info("\n[1] Edit value | [2] Edit gender | [3] Edit nation | [0] Back")
        cmd = get_input(">>", "bold green")
        
        if cmd == "0":
            break
        
        elif cmd == "1":
            new_val = get_input("Nama baru", "bold cyan")
            if new_val:
                rec.value = new_val
                _mark_dirty(app, key)
                print_success("Updated")
        
        elif cmd == "2":
            new_val = get_input("Gender (0=male, 1=female)", "bold cyan")
            if new_val.isdigit():
                rec.gender = int(new_val)
                _mark_dirty(app, key)
                print_success("Updated")
        
        elif cmd == "3":
            new_val = get_input("Nation UID", "bold cyan")
            if new_val.isdigit():
                rec.nation_uid = int(new_val)
                _mark_dirty(app, key)
                print_success("Updated")


def add_new_name(app: "App", dat, by_id, key):
    """Add new name."""
    clear_screen()
    print_header("➕ Tambah Nama Baru")
    
    name = get_input("Nama", "bold cyan")
    if not name:
        return
    
    nation = get_input("Nation UID (default: 0)", "bold cyan") or "0"
    gender = get_input("Gender (0=male, 1=female, default: 0)", "bold cyan") or "0"
    
    next_id = max((x.id for x in dat.items), default=-1) + 1
    
    rec = NameRec(
        unknown1=0,
        id=next_id,
        gender=int(gender),
        nation_uid=int(nation),
        unknown2=1,
        unknown3=255,
        value=name
    )
    
    dat.items.append(rec)
    by_id[next_id] = rec
    _mark_dirty(app, key)
    
    print_success(f"Ditambah: {name} (ID: {next_id})")
    input("Enter...")


def _mark_dirty(app: "App", key: str):
    """Mark name file as dirty."""
    if key == "first":
        app.dirty_names_first = True
    elif key == "second":
        app.dirty_names_second = True
    elif key == "common":
        app.dirty_names_common = True
