"""Binary I/O utilities for FMM Tool."""

import os
import struct
from dataclasses import dataclass
from typing import Optional, Callable, Any, List


class ReaderEx:
    """Extended binary reader with little-endian support.

    A readahead buffer is kept so that the millions of tiny read_u8/read_i16/
    read_i32 calls issued by per-record parsers (people.dat does ~6.4M of them
    across 135k records) slice from an in-memory bytearray instead of hitting
    the underlying file object every time. tell/seek/peek stay correct because
    they are expressed in terms of the buffered logical position.
    """

    # 1 MiB readahead — comfortably larger than any single record, so the
    # small back-seeks inside People.read (tell/read-ahead/seek-back for the
    # optional fields) almost always stay within the live buffer.
    _CHUNK = 1 << 20

    def __init__(self, f):
        self.f = f
        self._buf = b""
        self._bpos = 0          # offset within _buf
        self._bbase = 0         # file offset where _buf starts
        # Cache file size up front (while buffer is empty) so eof() never has
        # to seek the file pointer to END and invalidate the read buffer.
        try:
            cur = f.tell()
            f.seek(0, os.SEEK_END)
            self._size = f.tell()
            f.seek(cur)
        except Exception:
            self._size = None

    def tell(self) -> int:
        return self._bbase + self._bpos

    def seek(self, pos: int, whence: int = 0):
        if whence != 0:
            # SEEK_CUR / SEEK_END — defer to the file and drop the buffer.
            self.f.seek(pos, whence)
            self._buf = b""
            self._bpos = 0
            self._bbase = self.f.tell()
            return
        # Absolute seek: if the target is inside the live buffer, just move
        # the cursor — no file I/O. Otherwise reposition the file and let the
        # next read_bytes refill.
        end = self._bbase + len(self._buf)
        if self._buf and self._bbase <= pos <= end:
            self._bpos = pos - self._bbase
        else:
            self.f.seek(pos, 0)
            self._buf = b""
            self._bpos = 0
            self._bbase = pos

    def read_bytes(self, n: int) -> bytes:
        if self._bpos + n <= len(self._buf):
            # hot path: serve entirely from the readahead buffer
            b = self._buf[self._bpos:self._bpos + n]
            self._bpos += n
            return b
        # cold path: not enough buffered. Read more, refilling as needed.
        out = self._buf[self._bpos:]
        self._buf = b""
        self._bpos = 0
        while len(out) < n:
            chunk = self.f.read(self._CHUNK)
            if not chunk:
                raise EOFError
            avail = len(out) + len(chunk)
            if avail >= n:
                # keep what we need, buffer the rest
                need = n - len(out)
                out += chunk[:need]
                self._buf = chunk[need:]
                self._bpos = 0
                self._bbase = self.f.tell() - len(self._buf)
            else:
                out += chunk
        return out[:n]

    
    def read_u8(self) -> int:
        return struct.unpack("<B", self.read_bytes(1))[0]
    
    def read_i16(self) -> int:
        return struct.unpack("<h", self.read_bytes(2))[0]
    
    def read_u16(self) -> int:
        return struct.unpack("<H", self.read_bytes(2))[0]
    
    def read_i32(self) -> int:
        return struct.unpack("<i", self.read_bytes(4))[0]
    
    def read_u32(self) -> int:
        return struct.unpack("<I", self.read_bytes(4))[0]
    
    def read_f32(self) -> float:
        return struct.unpack("<f", self.read_bytes(4))[0]
    
    def read_bool(self) -> bool:
        return self.read_u8() != 0
    
    def peek_i16(self) -> int:
        pos = self.tell()
        try:
            v = self.read_i16()
        finally:
            self.seek(pos)
        return v
    
    def read_string(self) -> str:
        ln = self.read_i32()
        if ln == 0:
            return ""
        return self.read_bytes(ln).decode("utf-8", errors="replace")
    
    def eof(self) -> bool:
        if self._size is None:
            cur = self.tell()
            self.f.seek(0, os.SEEK_END)
            self._size = self.f.tell()
            self.seek(cur)
        return self.tell() >= self._size


class WriterEx:
    """Extended binary writer with little-endian support."""
    
    def __init__(self, f):
        self.f = f
    
    def write_bytes(self, b: bytes):
        self.f.write(b)
    
    def write_u8(self, v: int):
        self.f.write(struct.pack("<B", v & 0xFF))
    
    def write_i16(self, v: int):
        self.f.write(struct.pack("<h", int(v)))
    
    def write_u16(self, v: int):
        self.f.write(struct.pack("<H", int(v) & 0xFFFF))
    
    def write_i32(self, v: int):
        self.f.write(struct.pack("<i", int(v)))
    
    def write_u32(self, v: int):
        self.f.write(struct.pack("<I", int(v) & 0xFFFFFFFF))
    
    def write_f32(self, v: float):
        self.f.write(struct.pack("<f", float(v)))
    
    def write_bool(self, v: bool):
        self.write_u8(1 if v else 0)
    
    def write_string(self, s: str):
        if not s:
            self.write_i32(0)
            return
        b = s.encode("utf-8")
        self.write_i32(len(b))
        self.write_bytes(b)


def atomic_overwrite(path: str, write_fn: Callable):
    """Atomic file overwrite using temp file."""
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        write_fn(f)
    os.replace(tmp, path)


@dataclass
class DatList:
    """Generic container for .dat file records."""

    path: str
    header: bytes
    count: int
    items: list
    count_size: str
    extra_pad_u8: Optional[int] = None
    pad_bytes: Optional[bytes] = None

    @staticmethod
    def load_i32(path: str, item_read_fn: Callable, pad_u8: bool = False,
                 pad: Optional[bytes] = None) -> "DatList":
        """Load file with i32 count."""
        with open(path, "rb") as f:
            r = ReaderEx(f)
            header = r.read_bytes(8)
            count = r.read_i32()
            padb = None
            if pad_u8:
                padb = bytes([r.read_u8()])
            elif pad is not None:
                padb = r.read_bytes(len(pad))
            items = []
            while not r.eof():
                try:
                    items.append(item_read_fn(r))
                except EOFError:
                    break
        return DatList(path, header, count, items, "i32",
                       (padb[0] if pad_u8 else None), padb)

    @staticmethod
    def load_i16(path: str, item_read_fn: Callable) -> "DatList":
        """Load file with i16 count."""
        with open(path, "rb") as f:
            r = ReaderEx(f)
            header = r.read_bytes(8)
            count = r.read_i16()
            items = []
            while not r.eof():
                try:
                    items.append(item_read_fn(r))
                except EOFError:
                    break
        return DatList(path, header, count, items, "i16", None)

    def save_overwrite(self, item_write_fn: Callable):
        """Save all items back to file."""
        def _write(f):
            w = WriterEx(f)
            w.write_bytes(self.header)
            if self.count_size == "i32":
                w.write_i32(len(self.items))
                if self.extra_pad_u8 is not None:
                    w.write_u8(self.extra_pad_u8)
                elif self.pad_bytes is not None:
                    w.write_bytes(self.pad_bytes)
            else:
                w.write_i16(len(self.items))
            for it in self.items:
                item_write_fn(it, w)
        atomic_overwrite(self.path, _write)


@dataclass
class AlwaysLoadList:
    """Container for clubs_to_always_load_male/female.dat files."""
    
    path: str
    header: bytes
    count: int
    items: List[int]
    
    @staticmethod
    def load(path: str) -> "AlwaysLoadList":
        """Load always_load file."""
        with open(path, "rb") as f:
            r = ReaderEx(f)
            header = r.read_bytes(8)
            count = r.read_i32()
            # Skip 4 bytes padding
            r.read_i32()
            items = []
            while not r.eof():
                try:
                    items.append(r.read_i32())
                except EOFError:
                    break
        return AlwaysLoadList(path, header, count, items)
    
    def save_overwrite(self):
        """Save all items back to file."""
        def _write(f):
            w = WriterEx(f)
            w.write_bytes(self.header)
            w.write_i32(len(self.items))
            w.write_i32(0)  # padding
            for it in self.items:
                w.write_i32(it)
        atomic_overwrite(self.path, _write)
