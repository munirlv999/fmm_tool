"""
FMM Tool v3 - Termux-Friendly Edition
=====================================
Football Manager Mobile - Data Editor Tool
Optimized for mobile/Termux use with numeric navigation.

Usage:
    python -m fmm_tool
    or
    python fmm_tool/main.py
"""

import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fmm_tool.ui.console import (
    RICH_AVAILABLE, console, clear_screen, print_warning,
    print_success, print_error, print_info, get_input, print_header, wait_enter
)
from fmm_tool.core.app import App


MENU_ITEMS = [
    ("1", "👤 Player Editor", "Cari & edit pemain"),
    ("2", "🌍 Nation Editor", "Edit data negara"),
    ("3", "🏟️ Club Editor", "Cari & edit klub"),
    ("4", "📝 Name Tool", "Edit nama (first/second/common)"),
    ("5", "🏆 Competition", "Edit kompetisi & pindah klub"),
    ("6", "🏟️ Stadium Editor", "Edit data stadion"),
    ("7", "📍 Region Editor", "Edit data region"),
    ("a", "🌐 Language", "Edit data bahasa"),
    ("m", "🗂️ More Data", "City, Awards, Rivals, Staff, dll"),
    ("8", "🧮 Kalkulator", "Konversi HEX ⇄ DEC"),
    ("9", "💾 Save As", "Backup ke folder baru"),
    ("s", "💾 Save", "Simpan perubahan (dirty only)"),
    ("0", "❌ Exit", "Simpan & keluar"),
]


def show_main_menu():
    """Display main menu - termux friendly."""
    clear_screen()
    
    if RICH_AVAILABLE:
        from rich.align import Align
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        
        console.print("\n[bold cyan]⚽ FMM TOOL v3[/bold cyan] [dim]- Mobile Edition[/dim]\n")
        
        table = Table(
            box=box.ROUNDED,
            border_style="cyan",
            show_header=False,
            padding=(0, 2),
        )
        table.add_column("Key", style="bold green", justify="center", width=4)
        table.add_column("Menu", style="bold white", width=20)
        table.add_column("Keterangan", style="dim", width=30)
        
        for key, name, desc in MENU_ITEMS:
            table.add_row(key, name, desc)
        
        console.print(table)
        console.print("")
    else:
        print("\n⚽ FMM TOOL v3 - Mobile Edition")
        print("=" * 50)
        for key, name, desc in MENU_ITEMS:
            print(f"{key}) {name:<20} {desc}")
        print("=" * 50)


def show_storage_locations():
    """Show common storage locations checked."""
    paths = App.get_android_storage_paths()
    
    print_info("Lokasi yang dicek:")
    for p in paths[:5]:  # Show first 5
        print(f"  - {p}")
    print("")


def check_storage_permission():
    """Check if we have storage permission by trying to access Downloads."""
    test_paths = [
        "/sdcard/Download",
        "/storage/emulated/0/Download",
        os.path.join(os.path.expanduser("~"), "storage", "downloads"),
    ]
    for path in test_paths:
        if os.path.exists(path):
            try:
                # Try to create a test file
                test_file = os.path.join(path, ".fmm_test")
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                return path
            except PermissionError:
                continue
    return None


def prompt_create_folder():
    """Prompt user to create/select data folder."""
    clear_screen()
    print_header("📁 SETUP DATABASE FOLDER")
    
    print_info("Selamat datang di FMM Tool!")
    print("")
    print_info("Database belum ditemukan.")
    print("")
    
    # Check storage permission first
    downloads_path = check_storage_permission()
    
    if downloads_path is None:
        print_error("❌ Tidak bisa akses storage!")
        print("")
        print_info("Anda perlu setup permission dulu:")
        print("")
        print("  1. Jalankan command ini di terminal:")
        print("     termux-setup-storage")
        print("")
        print("  2. Izinkan permission jika ada popup")
        print("")
        print("  3. Jalankan ulang FMM Tool")
        print("")
        input("Tekan Enter untuk exit...")
        sys.exit(1)
    
    # Permission OK, create folder automatically
    folder_name = "MUNIR EDITOR DATA"
    new_path = os.path.join(downloads_path, folder_name)
    
    try:
        os.makedirs(new_path, exist_ok=True)
        print_success(f"✓ Folder otomatis dibuat:")
        print(f"     {new_path}")
        print("")
        print_header("📝 LANGKAH BERIKUTNYA")
        print("")
        print_info("1. Copy semua file .dat ke folder tersebut")
        print("")
        print_info("2. File yang dibutuhkan (11 file):")
        print("     • people.dat")
        print("     • players.dat")
        print("     • first_names.dat")
        print("     • second_names.dat")
        print("     • common_names.dat")
        print("     • languages.dat")
        print("     • nation.dat")
        print("     • club.dat")
        print("     • competition.dat")
        print("     • stadium.dat")
        print("     • regions.dat")
        print("")
        print_info("3. Command copy contoh:")
        print(f"     cp ~/downloads/*.dat \"{new_path}/\"")
        print("")
        print_info("4. Setelah copy selesai, jalankan ulang:")
        print("     python -m fmm_tool")
        print("")
        input("Tekan Enter untuk exit...")
        sys.exit(0)
        
    except Exception as e:
        print_error(f"Gagal buat folder: {e}")
        print("")
        print_info("Coba pilih opsi manual:")
        print("  [1] Input path custom")
        print("  [0] Exit")
        print("")
        
        choice = get_input(">>", "bold green")
        
        if choice == "1":
            custom_path = get_input("Path folder lengkap", "bold cyan")
            if custom_path:
                custom_path = os.path.expanduser(custom_path)
                try:
                    os.makedirs(custom_path, exist_ok=True)
                    print_success(f"Folder dibuat: {custom_path}")
                    print_info("Copy file .dat ke folder tersebut")
                    input("Tekan Enter untuk exit...")
                    sys.exit(0)
                except Exception as e2:
                    print_error(f"Gagal: {e2}")
                    input("Tekan Enter...")
        
        return None


def find_database():
    """Try to find database in various locations."""
    # Check current directory first
    if all(os.path.exists(fn) for fn in App.REQUIRED_FILES):
        return os.getcwd()
    
    # Check Android storage paths
    for path in App.get_android_storage_paths():
        if all(os.path.exists(os.path.join(path, fn)) for fn in App.REQUIRED_FILES):
            return path
    
    # Check "MUNIR EDITOR DATA" folder specifically
    home = os.path.expanduser("~")
    munir_paths = [
        "/sdcard/Download/MUNIR EDITOR DATA",
        "/storage/emulated/0/Download/MUNIR EDITOR DATA",
        os.path.join(home, "storage", "downloads", "MUNIR EDITOR DATA"),
        os.path.join(home, "downloads", "MUNIR EDITOR DATA"),
    ]
    for path in munir_paths:
        if os.path.exists(path):
            if all(os.path.exists(os.path.join(path, fn)) for fn in App.REQUIRED_FILES):
                return path
    
    return None


def load_data():
    """Load data with auto-detect and prompt."""
    clear_screen()
    print_header("⚽ FMM TOOL v3 - Mobile Edition")
    print_info("Mencari database...")
    
    data_dir = find_database()
    
    if data_dir is None:
        # Permission check and folder creation
        # This will exit after creating folder or showing instructions
        prompt_create_folder()
        # If we reach here, user chose custom path with files
        return None
    
    print_info(f"Database ditemukan di: {data_dir}")
    
    try:
        app = App(data_dir)
        print_success(f"✓ Loaded: {len(app.people.items)} people, {len(app.clubs.items)} clubs")
        input("\nTekan Enter untuk mulai...")
        return app
    except Exception as e:
        print_error(f"Gagal load: {e}")
        return None


def save_as(app):
    """Save database to new folder."""
    clear_screen()
    print_header("💾 SAVE AS")
    
    print_info("Simpan database ke folder baru (backup)")
    print("")
    
    # Show options
    print("Pilih lokasi:")
    print("  [1] /sdcard/Download")
    print("  [2] /sdcard/Documents")
    print("  [3] /sdcard/")
    print("  [4] Path custom")
    print("  [0] Batal")
    print("")
    
    choice = get_input(">>", "bold green")
    
    base_paths = {
        "1": "/sdcard/Download",
        "2": "/sdcard/Documents",
        "3": "/sdcard",
    }
    
    dest_dir = None
    
    if choice in base_paths:
        base = base_paths[choice]
        if not os.path.exists(base):
            print_error(f"Folder {base} tidak ada")
            return
        
        folder_name = get_input("Nama folder baru", "bold cyan")
        if not folder_name:
            print_warning("Nama folder harus diisi")
            return
        
        dest_dir = os.path.join(base, folder_name)
    
    elif choice == "4":
        custom_path = get_input("Path lengkap folder tujuan", "bold cyan")
        if custom_path:
            dest_dir = custom_path
        else:
            print_warning("Path harus diisi")
            return
    
    elif choice == "0":
        return
    
    else:
        print_warning("Pilihan tidak valid")
        return
    
    # Check if exists
    if os.path.exists(dest_dir):
        confirm = get_input(f"Folder {dest_dir} sudah ada. Timpa? (y/n)", "bold yellow")
        if confirm.lower() != 'y':
            print_warning("Dibatalkan")
            return
    else:
        try:
            os.makedirs(dest_dir)
        except Exception as e:
            print_error(f"Gagal buat folder: {e}")
            return
    
    # Copy ALL database files (.dat, .lng, config.xml) — not just the
    # required ones, otherwise extended data (coaches, contracts, history,
    # city, rivalries, etc.) is silently lost from the backup.
    try:
        files_copied = 0
        for fn in os.listdir(app.data_dir):
            src = os.path.join(app.data_dir, fn)
            if not os.path.isfile(src):
                continue
            # Only copy recognized data file types; skip temp/hidden files.
            if fn.endswith(".dat") or fn.endswith(".lng") or fn == "config.xml":
                dst = os.path.join(dest_dir, fn)
                shutil.copy2(src, dst)
                files_copied += 1

        print_success(f"✓ {files_copied} file tersimpan di {dest_dir}")

    except Exception as e:
        print_error(f"Gagal copy: {e}")


def main():
    """Main entry point."""
    # Try to load data
    app = load_data()
    
    if app is None:
        return 1
    
    while True:
        show_main_menu()
        choice = get_input(">>", "bold green")
        
        if choice == "0":
            print_info("Menyimpan perubahan...")
            try:
                app.save_all_dirty()
                print_success("Tersimpan!")
            except Exception as e:
                print_error(f"Gagal save: {e}")
            print("\n👋 Terima kasih!\n")
            break
        
        elif choice == "1":
            from fmm_tool.editors.player_simple import mode_player_simple
            mode_player_simple(app)
        elif choice == "2":
            from fmm_tool.editors.nation_simple import mode_nation_simple
            mode_nation_simple(app)
        elif choice == "3":
            from fmm_tool.editors.club_simple import mode_club_simple
            mode_club_simple(app)
        elif choice == "4":
            from fmm_tool.editors.name_simple import mode_name_simple
            mode_name_simple(app)
        elif choice == "5":
            from fmm_tool.editors.competition_simple import mode_competition_simple
            mode_competition_simple(app)
        elif choice == "6":
            from fmm_tool.editors.stadium_simple import mode_stadium_simple
            mode_stadium_simple(app)
        elif choice == "7":
            from fmm_tool.editors.region_simple import mode_region_simple
            mode_region_simple(app)
        elif choice.lower() == "a":
            from fmm_tool.editors.language_simple import mode_language_simple
            mode_language_simple(app)
        elif choice.lower() == "m":
            from fmm_tool.editors.extended import mode_extended
            mode_extended(app)
        elif choice == "8":
            from fmm_tool.editors.calculator import mode_kalkulator
            mode_kalkulator()
        elif choice == "9":
            save_as(app)
        elif choice.lower() == "s":
            # Quick save (dirty only)
            clear_screen()
            print_header("💾 SAVE")
            saved_files = []
            try:
                if app.dirty_people:
                    saved_files.append("people.dat")
                if app.dirty_players:
                    saved_files.append("players.dat")
                if app.dirty_names_first:
                    saved_files.append("first_names.dat")
                if app.dirty_names_second:
                    saved_files.append("second_names.dat")
                if app.dirty_names_common:
                    saved_files.append("common_names.dat")
                if app.dirty_languages:
                    saved_files.append("languages.dat")
                if app.dirty_nations:
                    saved_files.append("nation.dat")
                if app.dirty_clubs:
                    saved_files.append("club.dat")
                if app.dirty_competitions:
                    saved_files.append("competition.dat")
                if app.dirty_stadiums:
                    saved_files.append("stadium.dat")
                if app.dirty_regions:
                    saved_files.append("regions.dat")
                if app.dirty_always_load_male:
                    saved_files.append("clubs_to_always_load_male.dat")
                if app.dirty_always_load_female:
                    saved_files.append("clubs_to_always_load_female.dat")
                
                app.save_all_dirty()
                
                if saved_files:
                    print_success(f"✓ {len(saved_files)} file disimpan:")
                    for fn in saved_files:
                        print(f"  • {fn}")
                else:
                    print_info("Tidak ada perubahan untuk disimpan")
                wait_enter()
            except Exception as e:
                print_error(f"Gagal save: {e}")
                wait_enter()
        else:
            print_warning("Pilihan tidak valid")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
