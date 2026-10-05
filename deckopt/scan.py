"""Steam kutuphane taramasi (appmanifest_*.acf)."""
import os
import re
from pathlib import Path

from .platform import get_product_name
from .store import read_limited

_ROOTS = [
    Path("/home/deck/.local/share/Steam/steamapps"),
    Path.home() / ".local/share/Steam/steamapps",
    Path("/run/media/mmcblk0p1/steamapps"),
]
_KV = re.compile(r'"(appid|name|SizeOnDisk)"\s+"([^"]*)"')


def library_dirs() -> list:
    out = [r for r in _ROOTS if r.is_dir()]
    for r in list(out):
        vdf = r / "libraryfolders.vdf"
        if vdf.is_file():
            try:
                for m in re.finditer(r'"path"\s+"([^"]+)"', read_limited(vdf)):
                    d = Path(m.group(1)) / "steamapps"
                    if d.is_dir() and d not in out:
                        out.append(d)
            except (OSError, ValueError):
                pass
    return out


def scan_games() -> list:
    games, seen = [], set()
    for d in library_dirs():
        for acf in d.glob("appmanifest_*.acf"):
            try:
                kv = dict(_KV.findall(read_limited(acf)))
            except (OSError, ValueError):
                continue
            appid = kv.get("appid", "")
            if not appid.isdigit() or appid in seen:
                continue
            seen.add(appid)
            games.append({"appid": int(appid), "name": kv.get("name", appid)[:128]})
    return sorted(games, key=lambda g: g["name"].lower())


def read_hw() -> dict:
    """Steam Deck LCD/OLED donanimini tespit eder."""
    prod = get_product_name()
    if prod == "jupiter":
        return {
            "model": "Valve Steam Deck LCD",
            "screen": "LCD (800p, 60Hz)",
            "max_refresh": 60,
            "soc": "AMD Aerith (Zen 2 + RDNA 2)",
        }
    elif prod == "galileo":
        return {
            "model": "Valve Steam Deck OLED",
            "screen": "HDR OLED (800p, 90Hz)",
            "max_refresh": 90,
            "soc": "AMD Sephiroth (6nm Zen 2 + RDNA 2)",
        }
    return {
        "model": "Valve Steam Deck",
        "screen": "800p",
        "max_refresh": 60,
        "soc": "AMD Custom APU",
    }


