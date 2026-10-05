extends SceneTree
## Gelistirme araci: ana sahneyi yukleyip ekran goruntusu alir.

func _initialize() -> void:
	var out := OS.get_environment("SHOT_OUT")
	var scene: Node = load("res://main.tscn").instantiate()
	root.add_child(scene)
	for i in 20:
		await process_frame
	root.get_texture().get_image().save_png(out)
	quit()
