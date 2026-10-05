"""MangoHud CSV tabanli kural tabanli geri besleme (AI'siz, deterministik)."""
import csv
import io
from pathlib import Path

from .profile import sanitize
from .store import read_limited

MIN_SAMPLES = 120  # ~100 ms aralikla en az 12 sn; gercek kullanimda log_interval'e gore
SKIP_SECONDS = 30.0
MAX_ITER = 5


def parse_log(path: Path) -> dict:
    """MangoHud CSV'sinden avg fps, 1% low ve ortalama guc cikarir."""
    rows = list(csv.reader(io.StringIO(read_limited(path))))
    hi = next((i for i, r in enumerate(rows) if "fps" in [c.strip().lower() for c in r]), None)
    if hi is None:
        raise ValueError("fps basligi bulunamadi")
    head = [c.strip().lower() for c in rows[hi]]
    ix = {n: head.index(n) for n in ("fps", "frametime", "elapsed", "gpu_power") if n in head}
    fps, ft, pw = [], [], []
    for r in rows[hi + 1:]:
        try:
            t = float(r[ix["elapsed"]]) / 1e9 if "elapsed" in ix else 1e9
            if "elapsed" in ix and t < SKIP_SECONDS:
                continue
            fps.append(float(r[ix["fps"]]))
            if "frametime" in ix:
                ft.append(float(r[ix["frametime"]]))
            if "gpu_power" in ix:
                pw.append(float(r[ix["gpu_power"]]))
        except (ValueError, IndexError):
            continue
    if len(fps) < MIN_SAMPLES:
        raise ValueError(f"yetersiz ornek: {len(fps)} < {MIN_SAMPLES}")
    avg = sum(fps) / len(fps)
    if ft:
        worst = sorted(ft, reverse=True)[:max(1, len(ft) // 100)]
        low1 = 1000.0 / (sum(worst) / len(worst))
    else:
        low1 = sorted(fps)[max(0, len(fps) // 100)]
    return {"avg": avg, "low1": low1, "power": (sum(pw) / len(pw)) if pw else None}


def suggest(p: dict, m: dict, history: list) -> tuple:
    """(yeni_profil, aciklama). Her turda en fazla bir degisiklik."""
    if p.get("locked") or len(history) >= MAX_ITER:
        return p, "kilitli/iterasyon siniri"
    target = p["fps_limit"] or p["refresh_hz"]
    q = dict(p)
    why = "kararli"
    if m["low1"] < 0.85 * target or m["avg"] < 0.95 * target:
        if q["render_scale"] > 50:
            q["render_scale"] -= 10
            why = "render_scale -10"
        elif q["upscaler"] == "none":
            q["upscaler"] = "fsr"
            why = "upscaler fsr"
        elif q["tdp_w"] < 15:
            q["tdp_w"] += 1
            why = "tdp +1"
        else:
            q["fps_limit"] = max(30, target - 10)
            why = "fps_limit dusur"
    elif m["avg"] >= 1.05 * target and m["low1"] >= 0.95 * target:
        if q["tdp_w"] > 3:
            q["tdp_w"] -= 1
            why = "tdp -1"
        elif q["render_scale"] < 100:
            q["render_scale"] = min(100, q["render_scale"] + 5)
            why = "render_scale +5"
    if why == "kararli":
        q["locked"] = True
    # ayni alan ters yone donerse kilitle (salinim onleme)
    changed = [k for k in ("render_scale", "tdp_w", "upscaler", "fps_limit") if q[k] != p[k]]
    for h in history[-2:]:
        if h.get("field") in changed and h.get("dir") != _dir(p, q, h.get("field")):
            q["locked"] = True
    out = sanitize(q)
    out["locked"] = bool(q.get("locked"))
    return out, why


def _dir(p, q, f):
    try:
        return 1 if q[f] > p[f] else -1
    except TypeError:
        return 0
