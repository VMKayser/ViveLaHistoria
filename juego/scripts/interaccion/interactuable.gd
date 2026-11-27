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


## Caja de colisión que envuelve todas las mallas del modelo (sirve para .glb de varias piezas).
func _asegurar_colision() -> void:
	for hijo in get_children():
		if hijo is CollisionShape3D:
			return
	var inversa := global_transform.affine_inverse()
	var caja := AABB()
	var hay_malla := false
	for visual in _visuales(self):
		var local: AABB = (inversa * visual.global_transform) * visual.get_aabb()
		caja = local if not hay_malla else caja.merge(local)
		hay_malla = true
	if not hay_malla:
		push_warning("[Interactuable] '%s' no tiene modelo ni colisión." % name)
		return
	var forma := BoxShape3D.new()
	forma.size = caja.size.max(Vector3.ONE * 0.05)
	var colision := CollisionShape3D.new()
	colision.shape = forma
	colision.position = caja.get_center()
	add_child(colision)


func _visuales(nodo: Node) -> Array[VisualInstance3D]:
	var lista: Array[VisualInstance3D] = []
	for hijo in nodo.get_children():
		if hijo is VisualInstance3D and not (hijo is Label3D):
			lista.append(hijo)
		lista.append_array(_visuales(hijo))
	return lista
