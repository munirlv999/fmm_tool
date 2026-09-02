"""Calculator mode for FMM Tool."""

import re
from ..ui.console import RICH_AVAILABLE, console, print_header, print_error, print_info, get_input, clear_screen, show_help_text, wait_enter


HEX = set("0123456789abcdefABCDEF")


def le_bytes_to_hex(b: bytes) -> str:
    """Convert little-endian bytes to hex string."""
    return "".join(f"{x:02X}" for x in b)


def int_to_le_bytes(n: int) -> bytes:
    """Convert int to little-endian bytes."""
    if n == 0:
        return b"\x00"
    size = (n.bit_length() + 7) // 8
    return n.to_bytes(size, "little", signed=False)


def parse_input(s: str):
    """Parse input string to determine format."""
    s = s.strip()
    
    if " " in s:
        parts = re.split(r"\s+", s)
        for p in parts:
            if not (1 <= len(p) <= 2 and all(c in HEX for c in p)):
                raise ValueError("HEX byte tidak valid")
        b = bytes(int(p, 16) for p in parts)
        val = int.from_bytes(b, "little")
        return "HEX BYTES (little-endian)", val, b
    
    if s.lower().startswith("0x") or any(c in "ABCDEFabcdef" for c in s):
        h = s.replace("0x", "")
        if not all(c in HEX for c in h):
            raise ValueError("HEX tidak valid")
        val = int(h, 16)
        b = int_to_le_bytes(val)
        return "HEX NUMBER", val, b
    
    if not s.isdigit():
        raise ValueError("Input tidak dikenali")
    
    val = int(s)
    b = int_to_le_bytes(val)
    return "DEC NUMBER", val, b


def show_help_calc():
    """Show calculator help."""
    sections = [
        ("FORMAT INPUT", [
            "[spasi]     : HEX BYTES little-endian",
            "            Contoh: '01 00 00 00' → 1",
            "            Contoh: '2C 01' → 300",
            "",
            "0x...       : HEX NUMBER",
            "            Contoh: '0x1234' → 4660",
            "            Contoh: '0xFF' → 255",
            "",
            "[angka]     : DECIMAL NUMBER",
            "            Contoh: '1234' → 0x04D2",
            "            Contoh: '99999' → 0x01869F"
        ]),
        ("OUTPUT", [
            "Mode        : Jenis input yang terdeteksi",
            "DEC         : Nilai desimal",
            "HEX (LE)    : Hex bytes little-endian",
            "",
            "Little Endian = byte terkecil di awal"
        ]),
        ("CONTOH PAKAI", [
            "Input: 'E7 03'",
            "Output: DEC = 999, HEX (LE) = E703",
            "",
            "Input: '999'",
            "Output: DEC = 999, HEX (LE) = E703",
            "",
            "Gunakan untuk convert UID, ID, dll"
        ]),
        ("NAVIGASI", [
            "[kosong]    : Input lagi",
            "?           : Tampilkan help",
            "0 / back    : Kembali ke menu"
        ])
    ]
    show_help_text("🧮 KALKULATOR HEX ⇄ DEC", sections)


def show_result(mode: str, dec: int, le_bytes: bytes):
    """Show calculation result."""
    if RICH_AVAILABLE:
        from rich.table import Table
        from rich.box import SIMPLE_HEAVY
        
        result = Table(box=SIMPLE_HEAVY, border_style="green", show_header=False)
        result.add_column("Property", style="cyan")
        result.add_column("Value", style="white")
        result.add_row("Mode", mode)
        result.add_row("DEC", str(dec))
        result.add_row("HEX (LE)", le_bytes_to_hex(le_bytes))
        console.print(result)
    else:
        print("\n" + "-" * 38)
        print(f"Mode : {mode}")
        print(f"DEC  : {dec}")
        print(f"HEX  : {le_bytes_to_hex(le_bytes)}")
        print("-" * 38 + "\n")


def mode_kalkulator():
    """Calculator mode main loop."""
    print_header("🧮 KALKULATOR", "HEX ⇄ DEC (LITTLE ENDIAN)")
    print_info("[?] Help | [0/back] Kembali | [input] Convert\n")
    
    while True:
        try:
            s = get_input("calc>", "bold green")
        except (EOFError, KeyboardInterrupt):
            print("")
            return
        
        if not s:
            continue
        
        if s == "?":
            show_help_calc()
            continue
        
        if s in ("0", "back", "exit", "quit"):
            return
        
        try:
            mode, dec, le_bytes = parse_input(s)
            show_result(mode, dec, le_bytes)
        except Exception as e:
            print_error(str(e))
