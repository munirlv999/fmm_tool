"""Generic field editor reused by the newly-added editors.

Given a DatList and a list of (attr, label, kind) field definitions, it
provides a search/list/edit UI that reads and writes the underlying records
while marking the file dirty when something changes.
"""

from typing import TYPE_CHECKING, List, Tuple, Callable

if TYPE_CHECKING:
    from ..core.app import App

from ..ui.console import (
    RICH_AVAILABLE, console, print_header, print_success,
    print_error, print_warning, print_info, get_input, clear_screen,
    show_numbered_list, wait_enter
)

# kind -> converter / formatter
def _conv(kind: str, raw: str):
    if kind == "int":
        return int(raw)
    if kind == "str":
        return raw
    if kind == "bool":
        return raw.strip().lower() in ("1", "true", "yes", "y")
    if kind == "float":
        return float(raw)
    raise ValueError(f"Unknown kind: {kind}")


def _fmt(kind: str, val) -> str:
    if kind == "bool":
        return "Yes" if val else "No"
    return str(val)


def edit_collection(app: "App", title: str, dat, fields: List[Tuple[str, str, str]],
                    dirty_fn: Callable[[], None], search_text=None):
    """Main loop: search / list / edit a collection of records.

    fields: list of (attr, label, kind); kind in int/str/bool/float.
    dirty_fn: called after a successful edit to mark the file dirty.
    search_text: optional callable(record) -> str to search by (default uses
        the first string field).
    """
    if search_text is None:
        str_attrs = [a for a, _, k in fields if k == "str"]
        def search_text(rec):
            for a in str_attrs:
                v = getattr(rec, a)
                if v:
                    return str(v)
            return ""
        # use a closure-safe default
        search_text = _default_search(search_text if not str_attrs else None, str_attrs)

    while True:
        clear_screen()
        print_header(title)
        print_info(f"[1] Cari | [2] List semua | [0] Back\n")
        cmd = get_input(">>", "bold green")

        if cmd == "0":
            break
        elif cmd == "1":
            query = get_input("Cari", "bold cyan")
            if not query:
                continue
            results = [(i, r) for i, r in enumerate(dat.items)
                       if query.lower() in search_text(r).lower()]
            if not results:
                print_warning("Tidak ditemukan")
                input("Enter...")
                continue
            items = [search_text(r) for _, r in results]
            sel = show_numbered_list(items, f"Hasil: {query}")
            if sel >= 0:
                _edit_record(app, dat.items[results[sel][0]], fields, dirty_fn, search_text)
        elif cmd == "2":
            items = [search_text(r) for r in dat.items]
            sel = show_numbered_list(items, title)
            if sel >= 0:
                _edit_record(app, dat.items[sel], fields, dirty_fn, search_text)


def _default_search(_unused, str_attrs):
    def fn(rec):
        for a in str_attrs:
            v = getattr(rec, a)
            if v:
                return str(v)
        return ""
    return fn


def _edit_record(app: "App", rec, fields: List[Tuple[str, str, str]], dirty_fn, search_text):
    while True:
        clear_screen()
        print_header(search_text(rec))
        for i, (attr, label, kind) in enumerate(fields, 1):
            print(f"  {i:2}. {label:24} {_fmt(kind, getattr(rec, attr))}")

        print_info("\n[no] [value] = edit | [0] = back")
        cmd = get_input(">>", "bold green")
        if cmd == "0":
            break

        parts = cmd.split(maxsplit=1)
        if len(parts) != 2:
            print_warning("Format: [no] [value]")
            continue

        num, value = parts
        if not num.isdigit():
            continue
        idx = int(num) - 1
        if not (0 <= idx < len(fields)):
            print_warning("Field tidak ada")
            continue

        attr, label, kind = fields[idx]
        try:
            setattr(rec, attr, _conv(kind, value))
            dirty_fn(app)
            print_success(f"{label} = {value}")
        except Exception as e:
            print_error(str(e))