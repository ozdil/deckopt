"""Ayricalikli GPU saat uygulayici (amdgpu pp_od_clk_voltage). Varsayilan: kuru calisma.

TDP bilincli olarak desteklenmez: dogrulanmis, kararli bir sysfs yolu yoktur.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from .profile import LIMITS

DRM = Path("/sys/class/drm")
STATE = Path("/run/deckopt-gpu-state.json")
_CARD = re.compile(r"^card[0-9]+$")


def discover() -> Path:
    """pp_od_clk_voltage ve power_dpm_force_performance_level iceren cihaz dizini."""
    for card in sorted(DRM.iterdir()):
        if not _CARD.match(card.name):
            continue
        dev = card / "device"
        if dev.is_symlink() or not dev.is_dir():
            dev = dev.resolve()
        od, lvl = dev / "pp_od_clk_voltage", dev / "power_dpm_force_performance_level"
        if od.is_file() and lvl.is_file():
            return dev
    raise FileNotFoundError("pp_od_clk_voltage desteklenmiyor (Steam Deck degil veya OD kapali)")


def plan(mhz: int) -> list:
    lo, hi = LIMITS["gpu_clock_mhz"]
    mhz = max(lo, min(hi, int(mhz)))
    return [("power_dpm_force_performance_level", "manual"),
            ("pp_od_clk_voltage", f"s 1 {mhz}"), ("pp_od_clk_voltage", "c")]


def _write(dev: Path, name: str, val: str) -> None:
    with open(dev / name, "w") as f:
        f.write(val + "\n")


def helper_apply(mhz: int) -> None:
    """Root olarak calisir. Yazmadan once mevcut durumu yedekler."""
    if os.geteuid() != 0:
        raise PermissionError("root gerekli")
    dev = discover()
    prev = (dev / "power_dpm_force_performance_level").read_text().strip()
    if not STATE.exists():  # ilk yedegi ez(m)e
        fd = os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump({"dev": str(dev), "level": prev}, f)
    for name, val in plan(mhz):
        _write(dev, name, val)


def helper_restore() -> None:
    if os.geteuid() != 0:
        raise PermissionError("root gerekli")
    dev = discover()
    try:
        prev = json.loads(STATE.read_text()).get("level", "auto")
    except (OSError, ValueError):
        prev = "auto"
    if prev not in ("auto", "low", "high", "manual", "profile_standard"):
        prev = "auto"
    _write(dev, "pp_od_clk_voltage", "r")
    _write(dev, "pp_od_clk_voltage", "c")
    _write(dev, "power_dpm_force_performance_level", prev)
    STATE.unlink(missing_ok=True)


def run_privileged(action: str, mhz: int = 0) -> int:
    """Yerel makinede yetkili komut calistirilmaz. Steam Deck icin komut basar."""
    print("BILGI: Bu cihaz Steam Deck degildir. Yerel sistemde yetkili islem yapilmaz.")
    print("Steam Deck uzerinde calistirilmasi gereken komut:")
    if action == "apply":
        print(f"  sudo sh -c 'echo manual > /sys/class/drm/card0/device/power_dpm_force_performance_level && echo \"s 1 {int(mhz)}\" > /sys/class/drm/card0/device/pp_od_clk_voltage && echo c > /sys/class/drm/card0/device/pp_od_clk_voltage'")
    else:
        print("  sudo sh -c 'echo auto > /sys/class/drm/card0/device/power_dpm_force_performance_level && echo r > /sys/class/drm/card0/device/pp_od_clk_voltage && echo c > /sys/class/drm/card0/device/pp_od_clk_voltage'")
    return 0

