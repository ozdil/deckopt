## Ana arayuz: gamepad ile gezilir (D-pad, A = sec, B = geri). Yalnizca Steam Deck.
extends Control

const PROFILES := "user://profiles.json"
const KEYFILE := "user://gemini.key"

var hw: Dictionary
var games: Array = []
var store: Dictionary = {}
var gemini: Gemini
var root: VBoxContainer
var back_action: Callable = Callable()
var queue: Array = []
var busy := false


func _ready() -> void:
	_apply_theme()
	var bg := ColorRect.new()
	bg.color = Color(0.07, 0.08, 0.10)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 48)
	add_child(margin)
	root = VBoxContainer.new()
	root.add_theme_constant_override("separation", 16)
	margin.add_child(root)

	if not DeckScan.is_steam_deck():
		_lock_screen()
		return
	hw = DeckScan.hardware()
	gemini = Gemini.new()
	add_child(gemini)
	gemini.finished.connect(_on_profile)
	store = Store.load_json(PROFILES, {})
	games = DeckScan.scan_games()
	_home()


func _apply_theme() -> void:
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["JetBrainsMono Nerd Font", "JetBrains Mono", "monospace"])
	var t := Theme.new()
	t.default_font = font
	t.default_font_size = 26
	theme = t


func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("ui_cancel") and back_action.is_valid() and not busy:
		back_action.call()
		get_viewport().set_input_as_handled()


# ---------- yardimcilar ----------

func _clear() -> void:
	for c in root.get_children():
		c.queue_free()
	back_action = Callable()


func _title(text: String, sub: String = "") -> void:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", 40)
	root.add_child(l)
	if sub != "":
		var s := Label.new()
		s.text = sub
		s.modulate = Color(0.7, 0.75, 0.8)
		root.add_child(s)


func _button(text: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(0, 64)
	b.pressed.connect(cb)
	root.add_child(b)
	return b


func _hint(text: String) -> void:
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(spacer)
	var l := Label.new()
	l.text = text
	l.modulate = Color(0.55, 0.6, 0.65)
	l.add_theme_font_size_override("font_size", 20)
	root.add_child(l)


func _focus_first() -> void:
	for c in root.get_children():
		if c is Button or c is ItemList or c is LineEdit:
			c.call_deferred("grab_focus")
			return


func _key() -> String:
	return Store.read_limited(KEYFILE).strip_edges()


# ---------- ekranlar ----------

func _lock_screen() -> void:
	_title("Desteklenmeyen cihaz")
	var l := Label.new()
	l.text = "deckopt yalnizca Valve Steam Deck (LCD ve OLED) uzerinde calisir.\nTespit edilen cihaz: %s" % (DeckScan.product() if DeckScan.product() != "" else "bilinmiyor")
	l.autowrap_mode = TextServer.AUTOWRAP_WORD
	root.add_child(l)
	_button("Cikis", func(): get_tree().quit())
	_focus_first()


func _home() -> void:
	_clear()
	var done := 0
	for g in games:
		if store.has(g["appid"]):
			done += 1
	_title("deckopt", "%s  |  %d / %d oyun optimize edildi" % [hw["model"], done, games.size()])
	_button("Tum oyunlari optimize et", func(): _start(games, false))
	_button("Oyunlar ve profiller", _game_list)
	_button("Tumunu yeniden optimize et", func(): _start(games, true))
	_button("API anahtari" + ("" if _key() != "" else "  (gerekli)"), _key_screen)
	_button("Cikis", func(): get_tree().quit())
	_hint("D-pad: gezin    A: sec    B: geri")
	_focus_first()


func _key_screen() -> void:
	_clear()
	back_action = _home
	_title("Gemini API anahtari", "aistudio.google.com adresinden ucretsiz alinabilir. Anahtar yalnizca bu cihazda saklanir.")
	var le := LineEdit.new()
	le.secret = true
	le.placeholder_text = "Anahtari girin (ekran klavyesi: Steam + X)"
	le.custom_minimum_size = Vector2(0, 64)
	le.text = _key()
	root.add_child(le)
	var save := func():
		var k := le.text.strip_edges()
		if k != "":
			Store.atomic_write(KEYFILE, k)
		_home()
	le.text_submitted.connect(func(_t): save.call())
	_button("Kaydet", save)
	_button("Geri", _home)
	_hint("Anahtariniz deckopt sunucularina gonderilmez; yalnizca Google'a iletilir.")
	_focus_first()


func _game_list() -> void:
	_clear()
	back_action = _home
	_title("Oyunlar", "%d oyun bulundu" % games.size())
	if games.is_empty():
		var l := Label.new()
		l.text = "Kurulu oyun bulunamadi."
		root.add_child(l)
		_focus_first()
		return
	var list := ItemList.new()
	list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	for g in games:
		list.add_item(("[hazir]  " if store.has(g["appid"]) else "[  -  ]  ") + g["name"])
	list.item_activated.connect(func(i): _open_game(games[i]))
	root.add_child(list)
	list.call_deferred("grab_focus")
	if list.item_count > 0:
		list.select(0)


func _open_game(g: Dictionary) -> void:
	if store.has(g["appid"]):
		_detail(g)
	else:
		_start([g], false, func(): _detail(g))


func _detail(g: Dictionary) -> void:
	_clear()
	back_action = _game_list
	var entry: Dictionary = store.get(g["appid"], {})
	var p: Dictionary = entry.get("profile", {})
	if p.is_empty():
		p = Profile.sanitize({}, hw.get("max_hz", 60))
	_title(g["name"])
	var info := Label.new()
	info.autowrap_mode = TextServer.AUTOWRAP_WORD
	info.text = "\n".join([
		"Quick Access (...) > Performans menusunden uygulayin:",
		"  Kare siniri: %s     Yenileme hizi: %d Hz" % [str(p["fps_limit"]) if p["fps_limit"] > 0 else "kapali", p["refresh_hz"]],
		"  TDP siniri: %d W     GPU saati: %d MHz" % [p["tdp_w"], p["gpu_clock_mhz"]],
		"  Olcekleme filtresi: %s     Cozunurluk olcegi: %%%d" % [p["upscaler"].to_upper(), p["render_scale"]],
		"",
		"Oyun > Ozellikler > Baslatma Secenekleri:",
		"  " + Profile.launch_options(p),
		"",
		"Not: " + (p["notes"] if p["notes"] != "" else "-"),
	])
	root.add_child(info)
	_button("Baslatma seceneklerini panoya kopyala", func():
		DisplayServer.clipboard_set(Profile.launch_options(p))
		_toast("Kopyalandi"))
	_button("Yeniden optimize et", func(): _start([g], true, func(): _detail(g)))
	_button("Geri", _game_list)
	_focus_first()



func _toast(text: String) -> void:
	var l := Label.new()
	l.text = text
	l.modulate = Color(0.5, 0.9, 0.6)
	root.add_child(l)
	get_tree().create_timer(2.0).timeout.connect(func(): if is_instance_valid(l): l.queue_free())


# ---------- optimizasyon kuyrugu ----------

var _after: Callable = Callable()
var _total := 0
var _progress: Label


func _start(list: Array, force: bool, after: Callable = Callable()) -> void:
	if _key() == "":
		_key_screen()
		return
	queue = []
	for g in list:
		if force or not store.has(g["appid"]):
			queue.append(g)
	_after = after if after.is_valid() else _home
	if queue.is_empty():
		_after.call()
		return
	_total = queue.size()
	busy = true
	_clear()
	_title("Optimize ediliyor")
	_progress = Label.new()
	root.add_child(_progress)
	_button("Optimizasyonu durdur", func():
		queue.clear()
		busy = false
		Store.save_json(PROFILES, store)
		_home())
	_next()



func _next() -> void:
	if queue.is_empty():
		busy = false
		Store.save_json(PROFILES, store)
		_after.call()
		return
	var g: Dictionary = queue[0]
	_progress.text = "%d / %d   %s" % [_total - queue.size() + 1, _total, g["name"]]
	gemini.request_profile(_key(), g, hw)


func _on_profile(ok: bool, data: Dictionary, error: String) -> void:
	var g: Dictionary = queue.pop_front()
	if not ok and error == "API anahtari gecersiz":
		busy = false
		queue = []
		_key_screen()
		return
	var p := Profile.sanitize(data if ok else {}, hw["max_hz"])
	if not ok:
		p["notes"] = "YZ'ye ulasilamadi (%s); guvenli varsayilan profil." % error
	store[g["appid"]] = {"name": g["name"], "profile": p}
	Store.save_json(PROFILES, store)
	_next()
