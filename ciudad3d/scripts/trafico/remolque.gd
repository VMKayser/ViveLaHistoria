class_name Remolque
extends Node3D
## Remolque de pasajeros (codex: remolque_madera) arrastrado por un vehículo. No tiene física propia: sigue al ojo de
## la lanza con la cinemática de un remolque de tornamesa (lanza fija al eje delantero, que gira entero; la caja sigue
## al eje delantero como un tractriz). Las ruedas se apoyan en la calle por rayos y giran según lo recorrido.
## Choca con el caminante y con los demás vehículos (no con su tractor) mediante un cuerpo animado.
##
## Marco del kit: x adelante, y arriba, z a la derecha → Godot: el remolque mira a +Z, +X a su izquierda.

var kit: KitVehiculo
var tractor: Vehiculo
var largo := 0.0                   # del ojo de la lanza a la cola (m): lo que el tractor lleva detrás
var _lanza := 0.0                  # del eje delantero al ojo de la lanza (horizontal)
var _alto_ojo := 0.5
var _batalla := 3.3
var _et := 0.0                     # eje trasero (x del kit)
var _f := Vector3.ZERO             # centro del eje delantero, en el suelo
var _r := Vector3.ZERO             # centro del eje trasero, en el suelo
var _tornamesa: Node3D
var _ruedas_t: Array[Node3D] = []
var _ruedas_d: Array[Node3D] = []
var _rt := 0.5
var _rd := 0.5
var _cuerpo: AnimatableBody3D
var _cola := Vector3.ZERO          # extremos globales (obstáculos del tráfico)
var _frente := Vector3.ZERO

func armar(k: KitVehiculo, variante: int, de: Vehiculo) -> void:
	kit = k
	tractor = de
	name = "Remolque"
	top_level = true
	var m := kit.mov
	_rt = float(m["radio_rueda"])
	_rd = kit.radio_delantera if kit.radio_delantera > 0.0 else _rt
	_et = float(m["eje_trasero"])
	var ed := float(m["eje_delantero"])
	var sv := float(m["semivia"])
	_batalla = ed - _et
	var ojo: Array = kit.anclas.get("enganche_frontal", [1.7, 0.0, 0.0])
	_lanza = float(ojo[0])
	_alto_ojo = float(kit.tornamesa.get("y", _rd)) + float(ojo[1])
	largo = _lanza + ed - kit.cola
	add_child(kit.pieza("cuerpo0", variante, 0))
	add_child(kit.pieza("cuerpo1", variante, 1))
	add_child(kit.pieza("cuerpo2", variante, 2))
	_tornamesa = Node3D.new()
	_tornamesa.position = Vector3(0.0, float(kit.tornamesa.get("y", _rd)), ed)
	add_child(_tornamesa)
	for nivel in [0, 1]:
		_tornamesa.add_child(kit.pieza("tornamesa%d" % nivel, variante, nivel))
	for lado in [1.0, -1.0]:
		_ruedas_t.append(_rueda("rueda", variante, lado, Vector3(lado * sv, _rt, _et), self))
		var pd := "ruedad" if kit.tiene("ruedad0") else "rueda"
		_ruedas_d.append(_rueda(pd, variante, lado, Vector3(lado * sv, _rd - _tornamesa.position.y, 0.0), _tornamesa))
	# cuerpo para chocar (caminante y otros vehículos), sin el tractor
	_cuerpo = AnimatableBody3D.new()
	_cuerpo.sync_to_physics = false
	_cuerpo.collision_layer = 4
	_cuerpo.collision_mask = 0
	var forma := CollisionShape3D.new()
	var caja := BoxShape3D.new()
	caja.size = Vector3(kit.medio_ancho * 2.0 - 0.2, kit.alto - kit.piso, kit.frente - kit.cola)
	forma.shape = caja
	forma.position = Vector3(0.0, kit.piso + caja.size.y * 0.5, (kit.frente + kit.cola) * 0.5)
	_cuerpo.add_child(forma)
	add_child(_cuerpo)
	_cuerpo.add_collision_exception_with(tractor)
	tractor.add_collision_exception_with(_cuerpo)

func _rueda(pieza: String, variante: int, lado: float, pos: Vector3, padre: Node3D) -> Node3D:
	var eje := Node3D.new()
	eje.position = pos
	for nivel in [0, 1]:
		var mi := kit.pieza("%s%d" % [pieza, nivel], variante, nivel)
		if lado > 0.0:
			mi.rotation.y = PI
		eje.add_child(mi)
	padre.add_child(eje)
	return eje

## Detrás del tractor, en línea (al aparecer).
func colocar() -> void:
	var z := tractor.global_basis.z
	z.y = 0.0
	z = z.normalized()
	var h := tractor.enganche_global()
	_f = h - z * _lanza
	_r = _f - z * _batalla
	_seguir(0.0, true)
	reset_physics_interpolation()

func _physics_process(dt: float) -> void:
	if tractor == null or not tractor.activo:
		return
	_seguir(dt, false)

func _seguir(dt: float, forzar_suelo: bool) -> void:
	var h := tractor.enganche_global()
	var antes := _r
	# eje delantero: a la distancia de la lanza del ojo; eje trasero: a la batalla del delantero (en planta)
	var d := Vector2(_f.x - h.x, _f.z - h.z)
	if d.length_squared() < 1e-6:
		d = Vector2(-tractor.global_basis.z.x, -tractor.global_basis.z.z)
	d = d.normalized() * _lanza
	_f = Vector3(h.x + d.x, _f.y, h.z + d.y)
	var b := Vector2(_r.x - _f.x, _r.z - _f.z)
	if b.length_squared() < 1e-6:
		b = d
	b = b.normalized() * _batalla
	_r = Vector3(_f.x + b.x, _r.y, _f.z + b.y)
	# alturas: la calle bajo cada eje (de cerca, con la ciudad armada); si no, la del ojo de la lanza
	var suelo_h := h.y - _alto_ojo
	if forzar_suelo or not tractor.lejano:
		_f.y = _suelo(_f, suelo_h)
		_r.y = _suelo(_r, suelo_h)
	else:
		_f.y = suelo_h
		_r.y = suelo_h
	var z := (_f - _r).normalized()
	var x := Vector3.UP.cross(z).normalized()
	var y := z.cross(x)
	global_transform = Transform3D(Basis(x, y, z), _r - z * _et)
	# la tornamesa apunta al ojo de la lanza
	var al_ojo := global_transform.basis.inverse() * (h - global_transform * _tornamesa.position)
	_tornamesa.rotation.y = atan2(al_ojo.x, al_ojo.z)
	# ruedas: giran lo recorrido
	var paso := Vector2(_r.x - antes.x, _r.z - antes.z).length() * signf(z.dot(_r - antes) + 1e-6)
	if dt > 0.0:
		for w in _ruedas_t:
			w.rotation.x += paso / _rt
		for w in _ruedas_d:
			w.rotation.x += paso / _rd
	_cola = global_transform * Vector3(0.0, 0.0, kit.cola)
	_frente = global_transform * Vector3(0.0, 0.0, kit.frente)

func _suelo(p: Vector3, si_no: float) -> float:
	var espacio := get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(p + Vector3(0, 2.5, 0), p - Vector3(0, 3.0, 0), 1)
	var r := espacio.intersect_ray(q)
	return r["position"].y if r else si_no

## Extremos globales (cola, frente) para que los demás vehículos lo vean como obstáculo.
func extremos() -> Array:
	return [_cola, _frente]
