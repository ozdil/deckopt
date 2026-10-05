"""Gamepad dostu tam ekran arayuz (curses, ek bagimlilik yok).

Tuslar: Yon tuslari / D-pad = gezin, Enter / A = sec, Esc / B = geri, q = cikis.
Steam Input'ta bu kisayol icin "Klavye (WASD) ve Fare" yerine
"Oyun kumandasi -> yon tuslari + Enter/Esc" duzeni onerilir.
"""
import curses
import os
from pathlib import Path

from . import ai, profile, scan
from .store import atomic_write_json, data_dir, ensure_dir, load_json, read_limited

PROFILES = lambda: data_dir() / "profiles.json"  # noqa: E731
KEYFILE = lambda: Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "deckopt" / "gemini.key"  # noqa: E731


def load_key() -> str:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    p = KEYFILE()
    if p.is_file() and not p.is_symlink():
        return read_limited(p).strip()
    return ""


def save_key(key: str) -> None:
    p = KEYFILE()
    ensure_dir(p.parent)
    import tempfile
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=p.parent)
    with os.fdopen(fd, "w") as f:
        f.write(key.strip())
    os.chmod(tmp, 0o600)
    os.replace(tmp, p)


def _menu(scr, title, items, footer=""):
    """Basit secim listesi. Secilen indeksi ya da None (geri) dondurur."""
    idx, top = 0, 0
    while True:
        scr.erase()
        h, w = scr.getmaxyx()
        scr.addnstr(0, 2, title, w - 4, curses.A_BOLD)
        view = h - 4
        top = min(max(top, idx - view + 1), idx)
        for i, it in enumerate(items[top:top + view]):
            attr = curses.A_REVERSE if top + i == idx else 0
            scr.addnstr(2 + i, 2, it, w - 4, attr)
        scr.addnstr(h - 1, 2, footer or "Yon: gezin  Enter/A: sec  Esc/B: geri", w - 4, curses.A_DIM)
        k = scr.getch()
        if k in (curses.KEY_UP, ord("w")):
            idx = (idx - 1) % len(items)
        elif k in (curses.KEY_DOWN, ord("s")):
            idx = (idx + 1) % len(items)
        elif k in (curses.KEY_NPAGE,):
            idx = min(len(items) - 1, idx + view)
        elif k in (curses.KEY_PPAGE,):
            idx = max(0, idx - view)
        elif k in (10, 13, curses.KEY_ENTER, ord(" ")):
            return idx
        elif k in (27, ord("q"), curses.KEY_BACKSPACE):
            return None


def _msg(scr, lines):
    scr.erase()
    h, w = scr.getmaxyx()
    for i, ln in enumerate(lines[: h - 2]):
        scr.addnstr(i, 2, ln, w - 4)
    scr.addnstr(h - 1, 2, "Devam icin herhangi bir tus", w - 4, curses.A_DIM)
    scr.getch()


def _ask_key(scr):
    curses.echo()
    curses.curs_set(1)
    scr.erase()
    scr.addstr(1, 2, "Gemini API anahtari (Steam + X ile ekran klavyesi):")
    scr.addstr(3, 2, "> ")
    raw = scr.getstr(3, 4, 200).decode(errors="ignore").strip()
    curses.noecho()
    curses.curs_set(0)
    if raw:
        save_key(raw)
    return raw


def _optimize(scr, games, store, force=False):
    key = load_key() or _ask_key(scr)
    if key:
        os.environ["GEMINI_API_KEY"] = key
    hw = scan.read_hw()
    h, w = scr.getmaxyx()
    for n, g in enumerate(games, 1):
        k = str(g["appid"])
        if k in store and not force:
            continue
        scr.erase()
        scr.addnstr(1, 2, f"Optimize ediliyor {n}/{len(games)}", w - 4, curses.A_BOLD)
        scr.addnstr(3, 2, g["name"], w - 4)
        scr.refresh()
        try:
            p = profile.sanitize(ai.generate(g, hw))
        except Exception:  # ag/anahtar hatasi: guvenli varsayilan
            p = profile.sanitize({})
            p["notes"] = "YZ'ye ulasilamadi; guvenli varsayilan profil."
        store[k] = {"name": g["name"], "profile": p}
        atomic_write_json(PROFILES(), store)


def _show(scr, entry):
    p = entry["profile"]
    _msg(scr, [
        entry["name"], "",
        f"TDP: {p['tdp_w']} W     GPU: {p['gpu_clock_mhz']} MHz",
        f"FPS siniri: {p['fps_limit'] or 'yok'}     Yenileme: {p['refresh_hz']} Hz",
        f"Olcekleme: {p['upscaler']}  ({p['render_scale']}%)",
        "", "Not: " + (p.get("notes") or "-"), "",
        "Uygulama (Quick Access / ... menusu):",
        "  Performans > Kare siniri, Yenileme hizi, TDP siniri, GPU saati",
        "", "Baslatma Secenekleri (oyun > Ozellikler):",
        "  " + profile.launch_options(p),
    ])


def _run(scr):
    curses.curs_set(0)
    scr.keypad(True)
    while True:
        games = scan.scan_games()
        store = load_json(PROFILES(), {}) or {}
        done = sum(1 for g in games if str(g["appid"]) in store)
        hw = scan.read_hw()
        c = _menu(scr, f"deckopt  |  {hw['model']}  |  {done}/{len(games)} oyun optimize", [
            "Tum oyunlari optimize et",
            "Oyun listesi ve profiller",
            "Tumunu yeniden optimize et",
            "API anahtarini degistir",
            "Cikis",
        ])
        if c in (None, 4):
            return
        if c == 0:
            _optimize(scr, games, store)
        elif c == 2:
            _optimize(scr, games, store, force=True)
        elif c == 3:
            _ask_key(scr)
        elif c == 1 and games:
            while True:
                rows = [("[OK] " if str(g["appid"]) in store else "[ -] ") + g["name"] for g in games]
                i = _menu(scr, "Oyunlar", rows)
                if i is None:
                    break
                g = games[i]
                if str(g["appid"]) not in store:
                    _optimize(scr, [g], store)
                _show(scr, store[str(g["appid"])])


def run():
    curses.wrapper(_run)
