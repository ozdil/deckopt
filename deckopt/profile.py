"""Profil semasi, dogrulama ve donanim guvenlik sinirlari (LLM ciktisina asla guvenilmez)."""
import re

# Steam Deck LCD/OLED guvenli sinirlar
LIMITS = {
    "tdp_w": (3, 15),
    "gpu_clock_mhz": (200, 1600),
    "fps_limit": (0, 90),
    "refresh_hz": (40, 90),
}
UPSCALERS = {"none", "fsr", "nis", "integer"}
_ENV_KEY = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
_ENV_VAL = re.compile(r"^[A-Za-z0-9_.,:=+\-/ ]{0,128}$")
_PROTON = re.compile(r"^[A-Za-z0-9_.\- ]{1,64}$")
# Izinli env anahtarlari (beyaz liste)
ENV_ALLOW = {
    "PROTON_USE_WINED3D", "PROTON_NO_ESYNC", "PROTON_NO_FSYNC", "PROTON_ENABLE_NVAPI",
    "PROTON_FORCE_LARGE_ADDRESS_AWARE", "DXVK_ASYNC", "DXVK_FRAME_RATE",
    "RADV_PERFTEST", "MESA_SHADER_CACHE_MAX_SIZE", "WINE_FULLSCREEN_FSR",
    "WINE_FULLSCREEN_FSR_STRENGTH", "VKD3D_CONFIG", "mesa_glthread", "ENABLE_GAMESCOPE_WSI",
}

DEFAULT = {
    "tdp_w": 10, "gpu_clock_mhz": 1200, "fps_limit": 40, "refresh_hz": 40,
    "upscaler": "none", "render_scale": 100, "proton": "", "gamemode": True,
    "env": {}, "ingame": {}, "notes": "",
}


def _clamp(v, lo, hi, fallback):
    try:
        v = int(v)
    except (TypeError, ValueError):
        return fallback
    return max(lo, min(hi, v))


def sanitize(raw: dict) -> dict:
    """Bilinmeyen/zararli degerleri ayiklar, sinirlara kirpar."""
    if not isinstance(raw, dict):
        raw = {}
    p = dict(DEFAULT)
    for k, (lo, hi) in LIMITS.items():
        p[k] = _clamp(raw.get(k), lo, hi, DEFAULT[k]) if not (k == "fps_limit" and raw.get(k) == 0) else 0
    up = str(raw.get("upscaler", "none")).lower()
    p["upscaler"] = up if up in UPSCALERS else "none"
    p["render_scale"] = _clamp(raw.get("render_scale"), 50, 100, 100)
    pr = str(raw.get("proton", ""))
    p["proton"] = pr if _PROTON.match(pr) else ""
    p["gamemode"] = bool(raw.get("gamemode", True))
    env = {}
    for k, v in (raw.get("env") or {}).items():
        v = str(v)
        if k in ENV_ALLOW and _ENV_KEY.match(k) or k == "mesa_glthread":
            if _ENV_VAL.match(v):
                env[k] = v
    p["env"] = env
    ig = {}
    for k, v in (raw.get("ingame") or {}).items():
        if re.match(r"^[A-Za-z0-9_.]{1,64}$", str(k)) and re.match(r"^[A-Za-z0-9_.\-]{0,64}$", str(v)):
            ig[str(k)] = str(v)
    p["ingame"] = ig
    p["notes"] = str(raw.get("notes", ""))[:300]
    p["fps_limit"] = _fit_fps(p["fps_limit"], p["refresh_hz"])
    return p


def _fit_fps(fps: int, hz: int) -> int:
    """FPS siniri yenileme hizinin tam boleni olmali (kare suresi tutarliligi)."""
    if fps == 0 or hz % fps == 0:
        return fps
    for d in range(fps, 0, -1):
        if hz % d == 0 and d >= 30:
            return d
    return hz


def launch_options(p: dict) -> str:
    """Steam 'Baslatma Secenekleri' satiri uretir (root gerektirmez)."""
    env = dict(p["env"])
    if p["fps_limit"]:
        env.setdefault("DXVK_FRAME_RATE", str(p["fps_limit"]))
    if p["upscaler"] == "fsr":
        env.setdefault("WINE_FULLSCREEN_FSR", "1")
    parts = [f"{k}={v}" for k, v in sorted(env.items()) if " " not in v]
    if p["gamemode"]:
        parts.append("gamemoderun")
    parts.append("%command%")
    return " ".join(parts)
