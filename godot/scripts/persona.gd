extends Node3D
## Una persona de 1809 (modelo de MakeHuman con ropa de época y esqueleto animado).
## Camina por una ruta, mira hacia algo, puede llevar antorcha y elige su animación
## según lo que hace: reposo, caminar, correr, o una acción fija (llamar, bendecir...).

const Efectos := preload("res://scripts/efectos.gd")

signal llego

static var _escenas := {}

var tipo := "hombre_a"
var velocidad := 1.3
var ruta: Array[Vector3] = []
var mirar_a := Vector3.INF
var mirar_nodo: Node3D
## Animación fija mientras está quieto (o al caminar, si es "prisionero").
var accion := ""
var luz: OmniLight3D

var _modelo: Node3D
var _ap: AnimationPlayer
var _mallas: Array = []
var _antorcha: Node3D
var _mano: BoneAttachment3D
var _actual := ""
var _visible := 0.0
var _meta_visible := 1.0
var _borrar := false


static func escena(nombre: String) -> PackedScene:
	if not _escenas.has(nombre):
		_escenas[nombre] = load("res://assets/personajes/%s.gltf" % nombre)
	return _escenas[nombre]


func _ready() -> void:
	_modelo = escena(tipo).instantiate()
	_modelo.rotation.y = PI  # los modelos miran a +Z; aquí el frente es -Z
	add_child(_modelo)
	_ap = _modelo.find_child("AnimationPlayer", true, false)
	if _ap:
		for n in _ap.get_animation_list():
			_ap.get_animation(n).loop_mode = Animation.LOOP_LINEAR
		_ap.seek(randf() * 2.0)
	for m in _modelo.find_children("*", "MeshInstance3D", true, false):
		_mallas.append(m)
	_fijar_visible()


func aparecer(de_golpe := false) -> void:
	_meta_visible = 1.0
	if de_golpe:
		_visible = 1.0
		_fijar_visible()


func desaparecer(y_borrar := true) -> void:
	_meta_visible = 0.0
	_borrar = y_borrar


func ir(puntos: Array, vel := -1.0) -> void:
	ruta.clear()
	for p in puntos:
		ruta.append(p)
	if vel > 0.0:
		velocidad = vel


func con_antorcha(con_luz := false) -> void:
	if _antorcha:
		return
	var sk: Skeleton3D = _modelo.find_child("*", true, false) as Skeleton3D
	for n in _modelo.find_children("*", "Skeleton3D", true, false):
		sk = n
	if sk == null:
		return
	_mano = BoneAttachment3D.new()
	_mano.bone_name = "hand_r"
	sk.add_child(_mano)
	_antorcha = load("res://assets/modelos/antorcha.glb").instantiate()
	add_child(_antorcha)
	var fuego := Efectos.fuego()
	fuego.position = Vector3(0, 1.12, 0)
	_antorcha.add_child(fuego)
	if con_luz:
		luz = Efectos.luz_fuego(1.9, 10.0)
		luz.position = Vector3(0, 1.25, 0)
		_antorcha.add_child(luz)


func _fijar_visible() -> void:
	var t: float = 1.0 - _visible
	for m in _mallas:
		(m as GeometryInstance3D).transparency = t
	if _antorcha:
		_antorcha.visible = _visible > 0.3


func _process(delta: float) -> void:
	if _visible != _meta_visible:
		_visible = move_toward(_visible, _meta_visible, delta * 1.25)
		_fijar_visible()
		if _visible <= 0.0 and _borrar:
			queue_free()
			return

	var moviendo := false
	if not ruta.is_empty():
		var meta := ruta[0]
		meta.y = position.y
		var d := meta - position
		var paso := velocidad * delta
		if d.length() <= max(paso, 0.15):
			position = meta
			ruta.remove_at(0)
			if ruta.is_empty():
				llego.emit()
		else:
			position += d.normalized() * paso
			_girar_hacia(position + d, delta)
			moviendo = true
	if mirar_nodo and is_instance_valid(mirar_nodo):
		mirar_a = mirar_nodo.global_position
	if not moviendo and mirar_a != Vector3.INF:
		_girar_hacia(mirar_a, delta)
	_animar(moviendo)
	if _antorcha and _mano:
		# La antorcha sigue a la mano pero se mantiene casi vertical.
		_antorcha.global_position = _mano.global_position + Vector3(0, -0.35, 0)
		_antorcha.global_basis = Basis(Vector3.UP, rotation.y) * Basis(Vector3.RIGHT, -0.25)


func _animar(moviendo: bool) -> void:
	if _ap == null:
		return
	var nombre := "reposo"
	var escala := 1.0
	if moviendo:
		if velocidad > 3.0 and _ap.has_animation("correr"):
			nombre = "correr"
			escala = velocidad / 4.2
		elif accion == "prisionero" and _ap.has_animation("prisionero"):
			nombre = "prisionero"
			escala = velocidad / 1.2
		elif _ap.has_animation("marcha_fusil"):
			nombre = "marcha_fusil"
			escala = velocidad / 1.35
		elif _antorcha and _ap.has_animation("antorcha_caminar"):
			nombre = "antorcha_caminar"
			escala = velocidad / 1.35
		else:
			nombre = "caminar"
			escala = velocidad / 1.35
	elif accion != "" and accion != "prisionero" and _ap.has_animation(accion):
		nombre = accion
	elif _antorcha and _ap.has_animation("antorcha"):
		nombre = "antorcha"
	if not _ap.has_animation(nombre):
		nombre = "reposo"
	_ap.speed_scale = clamp(escala, 0.6, 1.6)
	if nombre != _actual:
		_actual = nombre
		_ap.play(nombre, 0.3)


func _girar_hacia(p: Vector3, delta: float) -> void:
	var dir := p - global_position
	dir.y = 0.0
	if dir.length() < 0.01:
		return
	var objetivo := atan2(-dir.x, -dir.z)
	rotation.y = lerp_angle(rotation.y, objetivo, clamp(delta * 6.0, 0.0, 1.0))
