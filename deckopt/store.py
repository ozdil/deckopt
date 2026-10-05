"""Guvenli okuma/yazma yardimcilari: boyut siniri, atomik yazim, symlink reddi."""
import json
import os
import tempfile
from pathlib import Path

MAX_READ = 1024 * 1024  # 1 MiB


def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
    return Path(base) / "deckopt"


def read_limited(path: Path, limit: int = MAX_READ) -> str:
    if path.is_symlink():
        raise ValueError(f"symlink reddedildi: {path}")
    with open(path, "rb") as f:
        raw = f.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f"dosya cok buyuk: {path}")
    return raw.decode("utf-8", errors="replace")


def ensure_dir(d: Path) -> None:
    if d.is_symlink():
        raise ValueError(f"symlink reddedildi: {d}")
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(d, 0o700)


def atomic_write_json(path: Path, obj) -> None:
    ensure_dir(path.parent)
    if path.is_symlink():
        raise ValueError(f"symlink reddedildi: {path}")
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(read_limited(path))
