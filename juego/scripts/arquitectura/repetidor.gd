@tool
class_name Repetidor
extends Node3D
## Repite su primer hijo en una grilla, como el modificador Array de Blender.
## Sirve para vigas, sillas, postes de baranda o faroles. Solo se guarda el original;
## las copias se generan al cargar la escena.

@export var cantidad := Vector3i(1, 1, 1):
	set(valor):
		cantidad = valor.max(Vector3i.ONE)
		_reconstruir()
@export var separacion := Vector3(1, 1, 1):
	set(valor):
		separacion = valor
		_reconstruir()

var _pendiente := false


func _ready() -> void:
	_construir()


func _reconstruir() -> void:
	if is_inside_tree() and not _pendiente:
		_pendiente = true
		_construir.call_deferred()


func _construir() -> void:
	_pendiente = false
	for hijo in get_children():
		if hijo.has_meta("copia"):
			remove_child(hijo)
			hijo.queue_free()
	if get_child_count() == 0:
		return
	var original := get_child(0) as Node3D
	if original == null:
		return
	for x in cantidad.x:
		for y in cantidad.y:
			for z in cantidad.z:
				if x == 0 and y == 0 and z == 0:
					continue
				var copia := original.duplicate() as Node3D
				copia.set_meta("copia", true)
				copia.position = original.position + Vector3(x * separacion.x, y * separacion.y, z * separacion.z)
				add_child(copia)
