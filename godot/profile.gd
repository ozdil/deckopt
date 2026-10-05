## Profil dogrulama: YZ ciktisina asla dogrudan guvenilmez.
class_name Profile
extends RefCounted

const LIMITS := {
	"tdp_w": [3, 15],
	"gpu_clock_mhz": [200, 1600],
	"fps_limit": [0, 90],
	"refresh_hz": [40, 90],
	"render_scale": [50, 100],
}
const UPSCALERS := ["none", "fsr", "nis", "integer"]
const ENV_ALLOW := [
	"PROTON_USE_WINED3D", "PROTON_NO_ESYNC", "PROTON_NO_FSYNC", "PROTON_ENABLE_NVAPI",
	"PROTON_FORCE_LARGE_ADDRESS_AWARE", "DXVK_ASYNC", "DXVK_FRAME_RATE", "RADV_PERFTEST",
	"MESA_SHADER_CACHE_MAX_SIZE", "WINE_FULLSCREEN_FSR", "WINE_FULLSCREEN_FSR_STRENGTH",
	"VKD3D_CONFIG", "mesa_glthread", "ENABLE_GAMESCOPE_WSI",
]
const DEFAULT := {
	"tdp_w": 10, "gpu_clock_mhz": 1200, "fps_limit": 40, "refresh_hz": 40,
	"upscaler": "none", "render_scale": 100, "proton": "", "gamemode": true,
	"env": {}, "notes": "",
}


static func _clamp_int(v: Variant, key: String) -> int:
	var lo: int = LIMITS[key][0]
	var hi: int = LIMITS[key][1]
	if typeof(v) != TYPE_INT and typeof(v) != TYPE_FLOAT:
		return DEFAULT[key]
	return clampi(int(v), lo, hi)


static func _fit_fps(fps: int, hz: int) -> int:
	if fps == 0 or hz % fps == 0:
		return fps
	for d in range(fps, 29, -1):
		if hz % d == 0:
			return d
	return hz


static func sanitize(raw: Variant, max_hz: int) -> Dictionary:
	var r: Dictionary = raw if raw is Dictionary else {}
	var p := DEFAULT.duplicate(true)
	for k in LIMITS:
		p[k] = _clamp_int(r.get(k), k)
	p["refresh_hz"] = mini(p["refresh_hz"], max_hz)
	var up := str(r.get("upscaler", "none")).to_lower()
	p["upscaler"] = up if up in UPSCALERS else "none"
	var pr := str(r.get("proton", ""))
	var re := RegEx.create_from_string("^[A-Za-z0-9_.\\- ]{1,64}$")
	p["proton"] = pr if re.search(pr) else ""
	p["gamemode"] = bool(r.get("gamemode", true))
	var val_re := RegEx.create_from_string("^[A-Za-z0-9_.,:=+\\-/]{0,128}$")
	var env := {}
	var raw_env: Variant = r.get("env", {})
	if raw_env is Dictionary:
		for k in raw_env:
			var v := str(raw_env[k])
			if str(k) in ENV_ALLOW and val_re.search(v):
				env[str(k)] = v
	p["env"] = env
	p["notes"] = str(r.get("notes", "")).left(300)
	p["fps_limit"] = _fit_fps(p["fps_limit"], p["refresh_hz"])
	return p


static func launch_options(p: Dictionary) -> String:
	var env: Dictionary = p["env"].duplicate()
	if p["fps_limit"] > 0 and not env.has("DXVK_FRAME_RATE"):
		env["DXVK_FRAME_RATE"] = str(p["fps_limit"])
	if p["upscaler"] == "fsr" and not env.has("WINE_FULLSCREEN_FSR"):
		env["WINE_FULLSCREEN_FSR"] = "1"
	var keys := env.keys()
	keys.sort()
	var parts := PackedStringArray()
	for k in keys:
		parts.append("%s=%s" % [k, env[k]])
	if p["gamemode"]:
		parts.append("gamemoderun")
	parts.append("%command%")
	return " ".join(parts)
