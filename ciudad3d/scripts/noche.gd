class_name Noche
extends Node3D
## Modo noche: elige los faroles más cercanos a la cámara para que iluminen paredes y suelo (16 en la PC, 8 en el
## celular; parámetros globales del shader) y dibuja los halos de todos los faroles en una sola llamada de dibujo.
## De dónde salen los faroles: el empaquetador los toma de la geometría (globos de vidrio cálido y claro), así que
## cualquier farol modelado de esa forma se enciende solo.

const RADIO_LUZ := 17.0
const ALCANCE := 60.0

var noche := false
var max_faroles := 8 if OS.has_feature("mobile") else Hora.MAX_FAROLES
var _faroles := PackedVector3Array()
var _halos: MultiMeshInstance3D
var _ultimo := Vector3(INF, 0.0, 0.0)

func cargar(lista) -> void:
	if lista == null:
		return
	for p in lista:
		_faroles.append(Vector3(p[0], p[1], p[2]))
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var quad := QuadMesh.new()
	quad.size = Vector2(1, 1)
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/halo_farol.gdshader")
	quad.material = mat
	mm.mesh = quad
	mm.instance_count = _faroles.size()
	for i in _faroles.size():
		mm.set_instance_transform(i, Transform3D(Basis(), _faroles[i]))
	_halos = MultiMeshInstance3D.new()
	_halos.multimesh = mm
	_halos.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_halos.extra_cull_margin = 4000.0
	_halos.visible = noche
	add_child(_halos)

## Lista de faroles (para el tráfico y otros): posiciones en el mundo.
func posiciones() -> PackedVector3Array:
	return _faroles

func fijar(es_noche: bool) -> void:
	noche = es_noche
	if _halos != null:
		_halos.visible = es_noche
	_ultimo = Vector3(INF, 0.0, 0.0)
	if not es_noche:
		for i in Hora.MAX_FAROLES:
			RenderingServer.global_shader_parameter_set("farol_%d" % i, Vector4.ZERO)

func _process(_dt: float) -> void:
	if not noche:
		return
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var p := cam.global_position
	if p.distance_squared_to(_ultimo) < 4.0:
		return
	_ultimo = p
	var cerca := []
	for f in _faroles:
		var d := p.distance_squared_to(f)
		if d < ALCANCE * ALCANCE:
			cerca.append([d, f])
	cerca.sort_custom(func(a, b): return a[0] < b[0])
	for i in Hora.MAX_FAROLES:
		var v := Vector4.ZERO
		if i < cerca.size() and i < max_faroles:
			var f: Vector3 = cerca[i][1]
			v = Vector4(f.x, f.y, f.z, RADIO_LUZ)
		RenderingServer.global_shader_parameter_set("farol_%d" % i, v)
