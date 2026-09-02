"""Language editor - Termux friendly version."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.app import App

from ..core.models import LanguageRec
from ..ui.console import (
    RICH_AVAILABLE, console, print_header, print_success,
    print_error, print_warning, print_info, get_input, clear_screen,
    show_numbered_list, show_help_text, wait_enter
)


def show_help_language():
    """Show help for language editor."""
    sections = [
        ("CARI BAHASA", [
            "[nama]      : Cari bahasa (flexible)",
            "[ID]        : Cari by ID (angka)",
            "Contoh: 'english', 'indonesian', '5'"
        ]),
        ("MENU DETAIL", [
            "1           : Edit nama",
            "2           : Edit nama lain",
            "3           : Edit nation ID",
            "4           : Edit difficulty",
            "0           : Back"
        ]),
        ("LIST SEMUA", [
            "1-xx        : Pilih bahasa",
            "98          : Next page",
            "99          : Prev page",
            "0           : Back"
        ])
    ]
    show_help_text("🌐 LANGUAGE EDITOR", sections)


def mode_language_simple(app: "App"):
    """Language editor - termux friendly."""

    while True:
        clear_screen()
        print_header("🌐 LANGUAGE EDITOR")
        print_info(f"Total: {len(app.languages.items)} bahasa")
        print("")
        print("  [1] Cari bahasa")
        print("  [2] List semua")
        print("  [?] Help | [0] Back")
        print("")

        cmd = get_input(">>", "bold green")

        if cmd == "?":
            show_help_language()
            continue
        if cmd == "0":
            break
        elif cmd == "1":
            query = get_input("Cari bahasa", "bold cyan")
            if not query:
                continue
            results = [
                (i, n) for i, n in enumerate(app.languages.items)
                if query.lower() in (n.name + " " + n.other_name).lower()
            ]
            if not results:
                print_warning("Tidak ditemukan")
                input("Enter...")
                continue
            items = [f"ID:{n.id} - {n.name}" for _, n in results]
            selected = show_numbered_list(items, f"Hasil: {query}")
            if selected >= 0:
                edit_language(app, results[selected][1])
        elif cmd == "2":
            items = [f"ID:{n.id} - {n.name}" for n in app.languages.items]
            selected = show_numbered_list(items, "LANGUAGES")
            if selected >= 0:
                edit_language(app, app.languages.items[selected])


def edit_language(app: "App", lang: LanguageRec):
    """Edit single language record."""
    while True:
        clear_screen()
        print_header(f"🌐 {lang.name}")
        print(f"  ID: {lang.id} | UID: {lang.uid}")
        print(f"  Name: {lang.name}")
        print(f"  Other Name: {lang.other_name}")
        print(f"  Nation ID: {lang.nation_id}")
        print(f"  Difficulty: {lang.difficulty}")

        print_info("\n[1] Edit name | [2] Edit other name | [3] Edit nation | [4] Edit difficulty | [0] Back")
        cmd = get_input(">>", "bold green")

        if cmd == "0":
            break
        elif cmd == "1":
            val = get_input("Nama bahasa", "bold cyan")
            if val:
                lang.name = val
                app.dirty_languages = True
                print_success("Updated")
        elif cmd == "2":
            val = get_input("Nama lain", "bold cyan")
            if val:
                lang.other_name = val
                app.dirty_languages = True
                print_success("Updated")
        elif cmd == "3":
            val = get_input("Nation ID", "bold cyan")
            if val.isdigit():
                lang.nation_id = int(val)
                app.dirty_languages = True
                print_success("Updated")
        elif cmd == "4":
            val = get_input("Difficulty (angka)", "bold cyan")
            if val.isdigit():
                lang.difficulty = int(val)
                app.dirty_languages = True
                print_success("Updated")