## Steam Deck donanim tespiti ve kutuphane taramasi (salt okuma).
class_name DeckScan
extends RefCounted

const DMI := "/sys/devices/virtual/dmi/id/product_name"


static func product() -> String:
	return Store.read_limited(DMI).strip_edges().to_lower()


static func is_steam_deck() -> bool:
	if OS.get_environment("DECKOPT_ALLOW_ANY_DEVICE") == "1":
		return true
	return product() in ["jupiter", "galileo"]


static func hardware() -> Dictionary:
	match product():
		"galileo":
			return {"model": "Steam Deck OLED", "max_hz": 90}
		"jupiter":
			return {"model": "Steam Deck LCD", "max_hz": 60}
	return {"model": "Steam Deck", "max_hz": 60}


static func _library_dirs() -> Array:
	var home := OS.get_environment("HOME")
	var out := []
	for d in [home.path_join(".local/share/Steam/steamapps"), "/run/media/mmcblk0p1/steamapps"]:
		if DirAccess.dir_exists_absolute(d) and d not in out:
			out.append(d)
	if out.size() > 0:
		var vdf := Store.read_limited(out[0].path_join("libraryfolders.vdf"))
		var re := RegEx.create_from_string("\"path\"\\s+\"([^\"]+)\"")
		for m in re.search_all(vdf):
			var d: String = m.get_string(1).path_join("steamapps")
			if DirAccess.dir_exists_absolute(d) and d not in out:
				out.append(d)
	return out


static func scan_games() -> Array:
	var games := []
	var seen := {}
	var re := RegEx.create_from_string("\"(appid|name)\"\\s+\"([^\"]*)\"")
	# Steam araclari (Proton, runtime) oyun degildir
	var skip := RegEx.create_from_string("(?i)^(proton|steam linux runtime|steamworks common)")
	for d in _library_dirs():
		var dir := DirAccess.open(d)
		if dir == null:
			continue
		for f in dir.get_files():
			if not (f.begins_with("appmanifest_") and f.ends_with(".acf")):
				continue
			var kv := {}
			for m in re.search_all(Store.read_limited(d.path_join(f))):
				if not kv.has(m.get_string(1)):
					kv[m.get_string(1)] = m.get_string(2)
			var appid := str(kv.get("appid", ""))
			var name := str(kv.get("name", appid)).left(128)
			if not appid.is_valid_int() or seen.has(appid) or skip.search(name):
				continue
			seen[appid] = true
			games.append({"appid": appid, "name": name})
	games.sort_custom(func(a, b): return a["name"].to_lower() < b["name"].to_lower())
	return games
