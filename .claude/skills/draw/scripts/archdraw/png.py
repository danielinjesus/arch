"""PNG through a headless Chromium-family browser (Edge on Windows, Chrome, Chromium)."""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import struct
import tempfile
import zlib
from pathlib import Path

# Headless Chrome's page area is shorter than --window-size (by about 90 px), so the window is
# made taller and the PNG is cropped back to the diagram's height.
_EXTRA_H = 240

_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]
_NAMES = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome", "msedge",
          "microsoft-edge"]
_PLAYWRIGHT = ["/opt/pw-browsers/chromium-*/chrome-linux/chrome",
               os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"),
               os.path.expandvars(r"%LOCALAPPDATA%\ms-playwright\chromium-*\chrome-win\chrome.exe")]


def find_browser() -> str | None:
    env = os.environ.get("ARCH_BROWSER")
    if env:
        return env
    for name in _NAMES:
        if (p := shutil.which(name)):
            return p
    for p in _CANDIDATES:
        if os.path.exists(p):
            return p
    for pattern in _PLAYWRIGHT:
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    return None


def svg_to_png(svg_text: str, width: float, height: float, out: Path, scale: float = 2.0,
               browser: str | None = None) -> None:
    """Raises RuntimeError with a hint when no browser is found or the screenshot fails."""
    browser = browser or find_browser()
    if not browser:
        raise RuntimeError("no Chrome/Edge/Chromium found for the PNG; set ARCH_BROWSER to its path")
    out = Path(out).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "diagram.svg"
        src.write_text(svg_text, encoding="utf-8")
        args = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
                "--no-first-run", "--no-default-browser-check", f"--user-data-dir={Path(tmp) / 'profile'}",
                f"--window-size={int(round(width))},{int(round(height)) + _EXTRA_H}",
                f"--force-device-scale-factor={scale}", f"--screenshot={out}", src.as_uri()]
        if sys.platform.startswith("linux") and hasattr(os, "geteuid") and os.geteuid() == 0:
            args.insert(1, "--no-sandbox")
        if out.exists():
            out.unlink()
        try:
            subprocess.run(args, capture_output=True, timeout=90, check=False)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"PNG failed: {e}") from e
    if not out.exists():
        raise RuntimeError(f"PNG failed: {browser} wrote no screenshot")
    crop_height(out, int(round(height * scale)))


def crop_height(path: Path, rows: int) -> None:
    """Keep the top `rows` rows of a non-interlaced 8-bit PNG (filters only look upward)."""
    data = Path(path).read_bytes()
    pos, ihdr, idat = 8, b"", []
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            ihdr = body
        elif kind == b"IDAT":
            idat.append(body)
        pos += 12 + n
    w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", ihdr)
    if rows >= h or depth != 8 or interlace:
        return
    bpp = {0: 1, 2: 3, 4: 2, 6: 4}.get(ctype)
    if bpp is None:
        return
    raw = zlib.decompress(b"".join(idat))[: rows * (1 + w * bpp)]

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    new_ihdr = struct.pack(">IIBBBBB", w, rows, depth, ctype, 0, 0, 0)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", new_ihdr)
                           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
