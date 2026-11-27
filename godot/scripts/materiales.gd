extends RefCounted
## Reemplazo de materiales por nombre en tiempo de ejecución (respaldo de la importación).

static var _cache := {}


static func aplicar(raiz: Node) -> void:
	for n in raiz.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(i)
			if m == null:
				continue
			var nuevo := material(m.resource_name)
			if nuevo and nuevo != m:
				mi.set_surface_override_material(i, nuevo)


static func material(nombre: String) -> Material:
	if _cache.has(nombre):
		return _cache[nombre]
	var ruta := "res://materiales/%s.tres" % nombre
	var m: Material = load(ruta) if ResourceLoader.exists(ruta) else null
	_cache[nombre] = m
	return m
