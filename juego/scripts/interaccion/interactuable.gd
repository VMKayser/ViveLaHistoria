class_name Interactuable
extends StaticBody3D
## Base de todo lo que el jugador puede usar con [E].
##
## Para usar un modelo de Blender: arrastra el .glb como hijo de este nodo.
## Si no tiene CollisionShape3D, se crea una caja de colisión a partir del modelo.

## Id que usan las misiones y los diálogos (por ejemplo "acta" o "serrano").
@export var id_interaccion := ""
@export var nombre_visible := ""
@export var verbo := "Usar"
## Ficha histórica asociada (id de data/fichas.json).
@export var ficha_id := ""
## Si no está vacío, solo se puede usar durante esa misión.
@export var solo_en_mision := ""


func _ready() -> void:
	_asegurar_colision()


func puede_interactuar(_jugador: Jugador) -> bool:
	return solo_en_mision.is_empty() or solo_en_mision == EstadoJuego.mision_actual


func texto_para(_jugador: Jugador) -> String:
	return "[E] %s %s" % [verbo, nombre_visible]


func interactuar(_jugador: Jugador) -> void:
	pass


func activar_colision(activa: bool) -> void:
	collision_layer = 1 if activa else 0


func _asegurar_colision() -> void:
	for hijo in get_children():
		if hijo is CollisionShape3D:
			return
	var visual := _buscar_visual(self)
	if visual == null:
		push_warning("[Interactuable] '%s' no tiene modelo ni colisión." % name)
		return
	var caja := visual.get_aabb()
	var relativa: Transform3D = global_transform.affine_inverse() * visual.global_transform
	var forma := BoxShape3D.new()
	forma.size = (caja.size * relativa.basis.get_scale()).max(Vector3.ONE * 0.05)
	var colision := CollisionShape3D.new()
	colision.shape = forma
	colision.position = relativa * caja.get_center()
	add_child(colision)


func _buscar_visual(nodo: Node) -> VisualInstance3D:
	for hijo in nodo.get_children():
		if hijo is VisualInstance3D and not (hijo is Label3D):
			return hijo
		var encontrado := _buscar_visual(hijo)
		if encontrado != null:
			return encontrado
	return null
