"""Steam localconfig.vdf: gercek ayristirici + guvenli LaunchOptions yazici."""
import os
import shutil
import tempfile
from pathlib import Path

from .store import read_limited

VDF_MAX = 16 * 1024 * 1024  # buyuk kutuphanelerde localconfig 1 MiB'i asabilir
_ESC = {"n": "\n", "t": "\t", "\\": "\\", '"': '"'}


def parse(text: str) -> dict:
    pos, n = 0, len(text)

    def tok():
        nonlocal pos
        while pos < n:
            c = text[pos]
            if c in " \t\r\n":
                pos += 1
            elif text.startswith("//", pos):
                while pos < n and text[pos] != "\n":
                    pos += 1
            else:
                break
        if pos >= n:
            return None
        c = text[pos]
        if c in "{}":
            pos += 1
            return c
        if c != '"':
            raise ValueError(f"beklenmeyen karakter @{pos}")
        pos += 1
        buf = []
        while pos < n and text[pos] != '"':
            if text[pos] == "\\" and pos + 1 < n:
                buf.append(_ESC.get(text[pos + 1], text[pos + 1]))
                pos += 2
            else:
                buf.append(text[pos])
                pos += 1
        if pos >= n:
            raise ValueError("kapanmamis tirnak")
        pos += 1
        return ("s", "".join(buf))

    def block(depth):
        if depth > 64:
            raise ValueError("cok derin")
        d = {}
        while True:
            k = tok()
            if k is None:
                if depth:
                    raise ValueError("kapanmamis blok")
                return d
            if k == "}":
                if not depth:
                    raise ValueError("fazla }")
                return d
            if not isinstance(k, tuple):
                raise ValueError("anahtar bekleniyordu")
            v = tok()
            if v == "{":
                d[k[1]] = block(depth + 1)
            elif isinstance(v, tuple):
                d[k[1]] = v[1]
            else:
                raise ValueError("deger bekleniyordu")

    return block(0)


def _q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t") + '"'


def dump(d: dict, depth: int = 0) -> str:
    ind, out = "\t" * depth, []
    for k, v in d.items():
        if isinstance(v, dict):
            out.append(f"{ind}{_q(k)}\n{ind}{{\n{dump(v, depth + 1)}{ind}}}\n")
        else:
            out.append(f"{ind}{_q(k)}\t\t{_q(v)}\n")
    return "".join(out)


def steam_running() -> bool:
    for c in Path("/proc").glob("[0-9]*/comm"):
        try:
            if c.read_text().strip() == "steam":
                return True
        except OSError:
            continue
    return False


def find_localconfig() -> Path:
    base = Path.home() / ".local/share/Steam/userdata"
    cands = [p for p in base.glob("[0-9]*/config/localconfig.vdf") if p.is_file() and not p.is_symlink()]
    if not cands:
        raise FileNotFoundError("localconfig.vdf bulunamadi")
    return max(cands, key=lambda p: p.stat().st_mtime)


def _apps(root: dict) -> dict:
    node = root
    for k in ("UserLocalConfigStore", "Software", "Valve", "Steam", "apps"):
        node = node.setdefault(k, {})
    return node


def get_launch(path: Path, appid: int) -> str:
    return _apps(parse(read_limited(path, VDF_MAX))).get(str(appid), {}).get("LaunchOptions", "")


def set_launch(path: Path, appid: int, value: str) -> Path:
    """Steam kapaliyken yedek al, dogrula, atomik yaz. Yedek yolunu dondurur."""
    if steam_running():
        raise RuntimeError("Steam calisiyor; once kapatin (steam -shutdown)")
    if path.is_symlink():
        raise ValueError("symlink reddedildi")
    if "%command%" not in value or "\n" in value or len(value) > 1024:
        raise ValueError("gecersiz launch options")
    root = parse(read_limited(path, VDF_MAX))
    _apps(root).setdefault(str(appid), {})["LaunchOptions"] = value
    text = dump(root)
    if parse(text) != root:  # gidis-donus dogrulamasi
        raise RuntimeError("serilestirme dogrulamasi basarisiz")
    bak = path.with_name(path.name + ".deckopt.bak")
    shutil.copy2(path, bak)
    os.chmod(bak, 0o600)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return bak
