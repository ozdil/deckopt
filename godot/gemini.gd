## Gemini REST istemcisi. Anahtar kullanicinindir, yalnizca user:// altinda 0600 saklanir.
class_name Gemini
extends Node

signal finished(ok: bool, data: Dictionary, error: String)

const MODEL := "gemini-2.5-flash"
const URL := "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
const PROMPT := """Sen Steam Deck icin oyun optimizasyon uzmanisin.
Oyun: "%s" (Steam appid %s). Donanim: %s, ekran en fazla %d Hz.
Pil omru, kare hizi kararliligi ve goruntu kalitesini dengeleyen bir profil uret.
SADECE JSON dondur. Alanlar: tdp_w(3-15), gpu_clock_mhz(200-1600), fps_limit(0-90),
refresh_hz(40-%d), upscaler(none|fsr|nis|integer), render_scale(50-100), proton(metin),
gamemode(bool), env(sozluk: PROTON_*, DXVK_*, RADV_PERFTEST gibi), notes(kisa Turkce aciklama).
Emin degilsen guvenli varsayilanlar ver."""

var _http: HTTPRequest


func _ready() -> void:
	_http = HTTPRequest.new()
	_http.timeout = 30.0
	_http.body_size_limit = Store.MAX_READ
	add_child(_http)
	_http.request_completed.connect(_on_done)


func request_profile(key: String, game: Dictionary, hw: Dictionary) -> void:
	var text := PROMPT % [game["name"].replace("\"", "'"), game["appid"], hw["model"], hw["max_hz"], hw["max_hz"]]
	var body := {
		"contents": [{"parts": [{"text": text}]}],
		"generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
	}
	var headers := ["Content-Type: application/json", "x-goog-api-key: " + key]
	var err := _http.request(URL % MODEL, headers, HTTPClient.METHOD_POST, JSON.stringify(body))
	if err != OK:
		finished.emit(false, {}, "istek baslatilamadi (%d)" % err)


func _on_done(result: int, code: int, _h: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		finished.emit(false, {}, "baglanti hatasi (%d)" % result)
		return
	if code == 400 or code == 401 or code == 403:
		finished.emit(false, {}, "API anahtari gecersiz")
		return
	if code != 200:
		finished.emit(false, {}, "sunucu hatasi (HTTP %d)" % code)
		return
	var data: Variant = JSON.parse_string(body.get_string_from_utf8())
	if not (data is Dictionary):
		finished.emit(false, {}, "yanit cozulemedi")
		return
	var candidates: Variant = data.get("candidates", [])
	if not (candidates is Array) or candidates.is_empty():
		finished.emit(false, {}, "YZ aday cikti uretemedi")
		return
	var parts: Variant = candidates[0].get("content", {}).get("parts", [])
	if not (parts is Array) or parts.is_empty():
		finished.emit(false, {}, "YZ icerik metni bulunamadi")
		return
	var text: String = str(parts[0].get("text", "")).strip_edges()
	if text.begins_with("```"):
		var first_nl := text.find("\n")
		if first_nl != -1:
			text = text.substr(first_nl + 1)
		if text.ends_with("```"):
			text = text.left(text.length() - 3).strip_edges()
	var prof: Variant = JSON.parse_string(text)
	if not (prof is Dictionary):
		finished.emit(false, {}, "profil cozulemedi")
		return
	finished.emit(true, prof, "")

