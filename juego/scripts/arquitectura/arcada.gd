@tool
class_name Arcada
extends CSGCombiner3D
## Muro con arcos de medio punto a lo largo del eje X local, como los claustros coloniales.
## La geometría se genera al cargar y al cambiar los parámetros en el inspector.
## Activa "use_collision" en el nodo para que el jugador no atraviese los pilares.

@export var largo := 20.0:
	set(valor):
		largo = valor
		_reconstruir()
@export var alto := 4.2:
	set(valor):
		alto = valor
		_reconstruir()
@export var grosor := 0.6:
	set(valor):
		grosor = valor
		_reconstruir()
@export var numero_arcos := 5:
	set(valor):
		numero_arcos = maxi(valor, 1)
		_reconstruir()
@export var ancho_vano := 2.8:
	set(valor):
		ancho_vano = valor
		_reconstruir()
## Altura a la que empieza la curva del arco.
@export var alto_arranque := 2.4:
	set(valor):
		alto_arranque = valor
		_reconstruir()
@export var material_muro: Material:
	set(valor):
		material_muro = valor
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
		if hijo.has_meta("generado"):
			remove_child(hijo)
			hijo.queue_free()

	var muro := CSGBox3D.new()
	muro.size = Vector3(largo, alto, grosor)
	muro.position = Vector3(0.0, alto / 2.0, 0.0)
	_agregar(muro)

	var paso := largo / numero_arcos
	for i in numero_arcos:
		var x := -largo / 2.0 + paso * (i + 0.5)
		var vano := CSGBox3D.new()
		vano.operation = CSGShape3D.OPERATION_SUBTRACTION
		vano.size = Vector3(ancho_vano, alto_arranque + 0.02, grosor + 0.2)
		vano.position = Vector3(x, alto_arranque / 2.0 - 0.01, 0.0)
		_agregar(vano)

		var arco := CSGCylinder3D.new()
		arco.operation = CSGShape3D.OPERATION_SUBTRACTION
		arco.radius = ancho_vano / 2.0
		arco.height = grosor + 0.2
		arco.sides = 28
		arco.rotation = Vector3(PI / 2.0, 0.0, 0.0)
		arco.position = Vector3(x, alto_arranque, 0.0)
		_agregar(arco)


func _agregar(forma: CSGShape3D) -> void:
	# Las caras que deja una resta usan el material de la forma que resta.
	forma.material = material_muro
	forma.set_meta("generado", true)
	add_child(forma)
