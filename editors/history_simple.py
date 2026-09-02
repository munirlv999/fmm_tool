"""Player history editor - Termux friendly.

player_history.dat is a whole-file structure (uid index + season blocks), so
it needs its own editor rather than the generic record editor.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.app import App

from ..ui.console import (
    RICH_AVAILABLE, console, print_header, print_success,
    print_error, print_warning, print_info, get_input, clear_screen,
    show_numbered_list, wait_enter
)


def _person_label(app: "App", uid: int) -> str:
    return app.people_name_by_uid(uid)


def mode_history_simple(app: "App"):
    """Player history editor."""
    ph = app.player_history
    if ph is None:
        print_warning("player_history.dat tidak tersedia.")
        return

    while True:
        clear_screen()
        print_header("📈 PLAYER HISTORY")
        print_info(f"Players: {len(ph.players)} | Season blocks: {sum(len(p.seasons) for p in ph.players)}")
        print("")
        print("  [1] Cari pemain (UID / nama)")
        print("  [2] List semua")
        print("  [0] Back")
        print("")

        cmd = get_input(">>", "bold green")
        if cmd == "0":
            break
        elif cmd == "1":
            query = get_input("UID / nama pemain", "bold cyan")
            if not query:
                continue
            if query.isdigit():
                results = [p for p in ph.players if p.person_uid == int(query)]
            else:
                results = [
                    p for p in ph.players
                    if query.lower() in _person_label(app, p.person_uid).lower()
                ]
            if not results:
                print_warning("Tidak ditemukan")
                input("Enter...")
                continue
            items = [f"UID {p.person_uid} - {_person_label(app, p.person_uid)} ({len(p.seasons)} season)" for p in results]
            sel = show_numbered_list(items, f"Hasil: {query}")
            if sel >= 0:
                _edit_player(app, results[sel])
        elif cmd == "2":
            items = [f"UID {p.person_uid} - {_person_label(app, p.person_uid)} ({len(p.seasons)} season)" for p in ph.players]
            sel = show_numbered_list(items, "PLAYER HISTORY")
            if sel >= 0:
                _edit_player(app, ph.players[sel])


def _edit_player(app: "App", player):
    while True:
        clear_screen()
        print_header(f"📈 {_person_label(app, player.person_uid)} (UID {player.person_uid})")
        print_info("Seasons:")
        for i, s in enumerate(player.seasons, 1):
            club = app.club_by_eff_id.get(s.club_uid)
            cname = club.full_name if club else f"#{s.club_uid}"
            print(f"  {i:3}. {cname} | flags={s.flags:#x} date={s.date_field} idx={s.season_index}")

        print_info("\n[1] Tambah season | [2] Hapus season (terakhir) | [0] Back")
        cmd = get_input(">>", "bold green")
        if cmd == "0":
            break
        elif cmd == "1":
            club = get_input("Club UID", "bold cyan")
            if not club.isdigit():
                print_warning("Club UID harus angka")
                continue
            from ..core.history_format import PlayerHistorySeason
            last_idx = player.seasons[-1].season_index if player.seasons else -1
            # mark previous last block as non-terminal
            if player.seasons and player.seasons[-1].season_index == -1:
                player.seasons[-1].season_index = last_idx if last_idx > 0 else 0
            player.seasons.append(PlayerHistorySeason(
                person_uid=player.person_uid,
                club_uid=int(club),
                flags=0,
                date_field=0,
                season_index=-1,  # new terminal block
            ))
            app.dirty_player_history = True
            print_success("Season ditambah")
        elif cmd == "2":
            if len(player.seasons) <= 1:
                print_warning("Minimal 1 season")
                continue
            player.seasons.pop()
            if player.seasons:
                player.seasons[-1].season_index = -1
            app.dirty_player_history = True
            print_success("Season terakhir dihapus")