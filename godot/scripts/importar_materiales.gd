@tool
extends EditorScenePostImport
## Al importar un .glb, reemplaza sus materiales por los de res://materiales/
## que tengan el mismo nombre (así el editor ya muestra las texturas PBR).


func _post_import(escena: Node) -> Object:
	_recorrer(escena)
	return escena


func _recorrer(n: Node) -> void:
	if n is MeshInstance3D and n.mesh:
		for i in n.mesh.get_surface_count():
			var m: Material = n.mesh.surface_get_material(i)
			if m == null:
				continue
			var ruta := "res://materiales/%s.tres" % m.resource_name
			if ResourceLoader.exists(ruta):
				n.mesh.surface_set_material(i, load(ruta))
	for h in n.get_children():
		_recorrer(h)
