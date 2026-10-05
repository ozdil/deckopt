"""Gemini REST istemcisi (yalnizca stdlib). Anahtar: GEMINI_API_KEY ortam degiskeni."""
import json
import os
import urllib.request

from .store import MAX_READ

MODEL = os.environ.get("DECKOPT_MODEL", "gemini-2.5-flash")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"

PROMPT = """Sen Steam Deck icin oyun optimizasyon uzmanisin.
Oyun: "{name}" (appid {appid}). Donanim: {hw}.
Pil omru, 40-60 FPS stabilitesi ve gorsel kaliteyi dengeleyen bir profil uret.
SADECE JSON dondur, alanlar:
tdp_w(3-15), gpu_clock_mhz(200-1600), fps_limit(0-90), refresh_hz(40-90),
upscaler(none|fsr|nis|integer), render_scale(50-100), proton(string, bos olabilir),
gamemode(bool), env(sozluk: PROTON_*, DXVK_*, RADV_PERFTEST, mesa_glthread gibi),
ingame(sozluk: oyun ici ayar anahtar/deger), notes(kisa Turkce aciklama).
Emin degilsen guvenli varsayilanlar ver."""


def generate(game: dict, hw: dict) -> dict:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY tanimli degil")
    body = {
        "contents": [{"parts": [{"text": PROMPT.format(
            name=game["name"].replace('"', "'"), appid=int(game["appid"]), hw=hw.get("model", "Steam Deck"))}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
    }
    req = urllib.request.Request(
        URL.format(m=MODEL), data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (sabit https)
        raw = r.read(MAX_READ + 1)
    if len(raw) > MAX_READ:
        raise RuntimeError("yanit cok buyuk")
    data = json.loads(raw)
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)
