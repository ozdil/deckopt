## Guvenli depolama: boyut siniri, atomik yazim, 0600 izin.
class_name Store
extends RefCounted

const MAX_READ := 1024 * 1024


static func read_limited(path: String, limit: int = MAX_READ) -> String:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return ""
	# sysfs dosyalari yanlis boyut bildirir; boyuta degil okunan veriye guvenilir
	var buf := f.get_buffer(limit + 1)
	if buf.size() > limit:
		push_warning("dosya cok buyuk: " + path)
		return ""
	return buf.get_string_from_utf8()


static func atomic_write(path: String, text: String) -> bool:
	var tmp := path.get_base_dir().path_join(".tmp_" + path.get_file())
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(text)
	f.close()
	FileAccess.set_unix_permissions(tmp, FileAccess.UNIX_READ_OWNER | FileAccess.UNIX_WRITE_OWNER)
	var err := DirAccess.rename_absolute(tmp, path)
	if err != OK:
		DirAccess.remove_absolute(tmp)
		return false
	return true



static func load_json(path: String, default_value: Variant) -> Variant:
	var t := read_limited(path)
	if t.is_empty():
		return default_value
	var v: Variant = JSON.parse_string(t)
	return default_value if v == null else v


static func save_json(path: String, v: Variant) -> bool:
	return atomic_write(path, JSON.stringify(v, "  "))
