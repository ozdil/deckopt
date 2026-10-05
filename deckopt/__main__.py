"""CLI: python -m deckopt {scan|optimize|show|apply}"""
import argparse
import sys

from datetime import date
from pathlib import Path

from . import ai, platform, power, profile, scan, tune, vdf
from .store import atomic_write_json, data_dir, load_json

PROFILES = lambda: data_dir() / "profiles.json"  # noqa: E731


def cmd_scan(_a):
    for g in scan.scan_games():
        print(f"{g['appid']:>10}  {g['name']}")


def cmd_optimize(a):
    games = scan.scan_games()
    if a.appid:
        games = [g for g in games if g["appid"] == a.appid]
    store = load_json(PROFILES(), {})
    hw = scan.read_hw()
    for g in games:
        key = str(g["appid"])
        if key in store and not a.force:
            print(f"atlandi (onbellek): {g['name']}")
            continue
        try:
            p = profile.sanitize(ai.generate(g, hw))
        except Exception as e:  # ag/anahtar hatasi: varsayilanla devam
            print(f"AI basarisiz ({g['name']}): {e}; varsayilan profil", file=sys.stderr)
            p = profile.sanitize({})
        store[key] = {"name": g["name"], "profile": p}
        atomic_write_json(PROFILES(), store)
        print(f"optimize edildi: {g['name']}")


def cmd_show(a):
    e = (load_json(PROFILES(), {}) or {}).get(str(a.appid))
    if not e:
        sys.exit("profil yok")
    p = e["profile"]
    print(e["name"])
    for k, v in p.items():
        print(f"  {k}: {v}")
    print("\nSteam Baslatma Secenekleri:\n  " + profile.launch_options(p))


def cmd_apply(a):
    cmd_show(a)
    print("\nNot: TDP/GPU saat ayarlari icin Decky PowerTools gibi bir arac kullanin; "
          "bu CLI yalnizca dogrulanmis degerleri uretir.")


def cmd_tune(a):
    store = load_json(PROFILES(), {})
    e = store.get(str(a.appid))
    if not e:
        sys.exit("profil yok; once optimize")
    m = tune.parse_log(Path(a.log))
    hist = e.setdefault("history", [])
    new, why = tune.suggest(e["profile"], m, hist)
    print(f"olcum: avg={m['avg']:.1f} low1={m['low1']:.1f} guc={m['power']}  -> {why}")
    if a.dry_run:
        return
    field = why.split()[0] if why != "kararli" else None
    hist.append({"date": date.today().isoformat(), "avg": round(m["avg"], 1),
                 "low1": round(m["low1"], 1), "change": why, "field": ({"render_scale":"render_scale","tdp":"tdp_w","upscaler":"upscaler","fps_limit":"fps_limit"}.get(field)),
                 "dir": -1 if ("-" in why or "dusur" in why) else 1})
    e["profile"] = new
    atomic_write_json(PROFILES(), store)
    print("Yeni satir:  " + profile.launch_options(new))


def cmd_write_launch(a):
    e = (load_json(PROFILES(), {}) or {}).get(str(a.appid))
    if not e:
        sys.exit("profil yok; once optimize")
    new = profile.launch_options(e["profile"])
    path = Path(a.config) if a.config else vdf.find_localconfig()
    print(f"dosya : {path}\neski  : {vdf.get_launch(path, a.appid) or '(bos)'}\nyeni  : {new}")
    if not a.apply:
        print("(kuru calisma; yazmak icin --apply, Steam kapali olmali)")
        return
    try:
        bak = vdf.set_launch(path, a.appid, new)
    except (RuntimeError, ValueError) as ex:
        sys.exit(f"hata: {ex}")
    print(f"yazildi; yedek: {bak}")


def cmd_power(a):
    e = (load_json(PROFILES(), {}) or {}).get(str(a.appid))
    if not e:
        sys.exit("profil yok; once optimize")
    mhz = e["profile"]["gpu_clock_mhz"]
    print(f"Oyun: {e['name']} (AppID: {a.appid})")
    print(f"Hedef Steam Deck GPU Saati: {mhz} MHz")
    print("Planlanan donanim ayarlari:")
    for name, val in power.plan(mhz):
        print(f"  {name} <- {val!r}")
    print()
    power.run_privileged("apply", mhz)



def cmd_power_restore(_a):
    sys.exit(power.run_privileged("restore"))


def cmd_power_helper(a):
    try:
        if a.action == "apply":
            power.helper_apply(int(a.mhz))
        else:
            power.helper_restore()
    except (OSError, ValueError) as ex:
        sys.exit(f"hata: {ex}")


def main():
    platform.enforce_steam_deck()
    ap = argparse.ArgumentParser(prog="deckopt")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan").set_defaults(f=cmd_scan)
    o = sub.add_parser("optimize")
    o.add_argument("--appid", type=int)
    o.add_argument("--force", action="store_true")
    o.set_defaults(f=cmd_optimize)
    t = sub.add_parser("tune")
    t.add_argument("appid", type=int)
    t.add_argument("--log", required=True)
    t.add_argument("--dry-run", action="store_true")
    t.set_defaults(f=cmd_tune)
    w = sub.add_parser("write-launch")
    w.add_argument("appid", type=int)
    w.add_argument("--apply", action="store_true")
    w.add_argument("--config", help="test icin alternatif localconfig.vdf")
    w.set_defaults(f=cmd_write_launch)
    pw = sub.add_parser("power")
    pw.add_argument("appid", type=int)
    pw.add_argument("--apply", action="store_true")
    pw.set_defaults(f=cmd_power)
    sub.add_parser("power-restore").set_defaults(f=cmd_power_restore)
    ph = sub.add_parser("power-helper")
    ph.add_argument("action", choices=["apply", "restore"])
    ph.add_argument("mhz", nargs="?", type=int, default=0)
    ph.set_defaults(f=cmd_power_helper)
    for n, f in (("show", cmd_show), ("apply", cmd_apply)):
        s = sub.add_parser(n)
        s.add_argument("appid", type=int)
        s.set_defaults(f=f)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
