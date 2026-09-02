"""Generic extended-data editors (city, continent, awards, rivals, officials,
staff, non-players, futures/transfers/bans/injuries/contracts/loans, history).

Each editor introspects its record dataclass and exposes the scalar fields
(int/str/bool/float) for editing; complex fields (bytes/lists) are preserved
untouched on save so round-trips stay byte-identical.
"""

from typing import TYPE_CHECKING, List, Tuple, Callable

if TYPE_CHECKING:
    from ..core.app import App

from ..ui.console import print_header, get_input, clear_screen, print_info, print_warning
from .generic_editor import edit_collection

_TYPE_MAP = {
    "int": "int", "float": "float", "bool": "bool", "str": "str",
}


def _scalar_fields(cls) -> List[Tuple[str, str, str]]:
    """Return (attr, label, kind) for scalar dataclass fields of cls."""
    out = []
    for f in getattr(cls, "__dataclass_fields__", {}).values():
        t = f.type
        base = t.__name__ if hasattr(t, "__name__") else str(t)
        base = base.replace("Optional[", "").replace("]", "").rstrip(".")
        if base in _TYPE_MAP:
            out.append((f.name, f.name, _TYPE_MAP[base]))
    return out


def _person_label(app: "App", attr: str, rec):
    """Try to render a person/uid/club id as a readable label. Falls back to the raw value."""
    try:
        uid = getattr(rec, attr)
        if isinstance(uid, int):
            nm = app.people_name_by_uid(uid)
            if nm != "-":
                return f"{nm} (UID {uid})"
            return f"UID {uid}"
    except Exception:
        pass
    return str(getattr(rec, attr))


def _make_editor(app: "App", attr: str, title: str, cls, dirty_key: str):
    """Return a closure that opens the generic editor for one data list."""
    dat = getattr(app, attr)
    if dat is None:
        return lambda: print_warning(f"{title} tidak tersedia (file/modul belum ada).")

    def dirty_fn(a: "App"):
        setattr(a, f"dirty_{dirty_key}", True)

    fields = _scalar_fields(cls)

    def search_text(rec):
        # prefer a name-like string field, else a uid/int field
        strs = [a for a, _, k in fields if k == "str"]
        for a in strs:
            v = getattr(rec, a)
            if v:
                return str(v)
        ints = [a for a, _, k in fields if k == "int"]
        for a in ints:
            if a in ("uid", "id", "person", "person_uid", "club_id"):
                return _person_label(app, a, rec)
        return str(getattr(rec, fields[0][0]) if fields else rec)

    def run():
        edit_collection(app, title, dat, fields, dirty_fn, search_text)

    return run


def mode_extended(app: "App"):
    """Top-level dispatcher for all extended-data editors."""
    from . import extended_map

    entries = extended_map.build(app)

    while True:
        clear_screen()
        print_header("🗂️ MORE DATA EDITORS")
        print_info("[0] Back\n")
        items = []
        for i, (title, _run) in enumerate(entries, 1):
            items.append(title)
            print(f"  {i:2}. {title}")
        print("")
        cmd = get_input(">>", "bold green")
        if cmd == "0":
            break
        if cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(entries):
                entries[idx][1]()