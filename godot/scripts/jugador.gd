extends CharacterBody3D
## Estudiante de la Universidad en primera persona: camina, corre, mira e interactúa.

signal interaccion(id: String)

const VEL_CAMINAR := 3.0
const VEL_CORRER := 6.0
const SENSIBILIDAD := 0.0022
const GRAVEDAD := 9.8

var cabeza: Node3D
var camara: Camera3D
var controlable := true
var interactuar_bloqueado := false
var ui: Node

var _interacciones := {}  # id -> {pos, radio, texto}
var _foco := ""
var _bob := 0.0
var _hasta_paso := 0.0
var _pasos: AudioStreamPlayer
var _sonidos_paso: Array[AudioStream] = []


func _ready() -> void:
	var forma := CollisionShape3D.new()
	var capsula := CapsuleShape3D.new()
	capsula.radius = 0.32
	capsula.height = 1.75
	forma.shape = capsula
	forma.position.y = 0.875
	add_child(forma)
	cabeza = Node3D.new()
	cabeza.position.y = 1.62
	add_child(cabeza)
	camara = Camera3D.new()
	camara.fov = 72.0
	camara.near = 0.05
	camara.far = 1500.0
	cabeza.add_child(camara)
	camara.current = true
	floor_snap_length = 0.35
	floor_max_angle = deg_to_rad(50)
	_pasos = AudioStreamPlayer.new()
	_pasos.volume_db = -10.0
	add_child(_pasos)
	for i in 4:
		_sonidos_paso.append(load("res://assets/audio/paso_%d.ogg" % (i + 1)))


func registrar(id: String, pos: Vector3, radio: float, texto: String) -> void:
	_interacciones[id] = {"pos": pos, "radio": radio, "texto": texto}


func quitar(id: String) -> void:
	_interacciones.erase(id)


func ubicar(pos: Vector3, mirar: Vector3) -> void:
	global_position = pos
	velocity = Vector3.ZERO
	mirar_hacia(mirar)


func mirar_hacia(p: Vector3) -> void:
	var d := p - (global_position + Vector3(0, 1.62, 0))
	rotation.y = atan2(-d.x, -d.z)
	cabeza.rotation.x = clamp(atan2(d.y, Vector2(d.x, d.z).length()), -1.3, 1.3)


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.pressed and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif e is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED and controlable:
		rotate_y(-e.relative.x * SENSIBILIDAD)
		cabeza.rotation.x = clamp(cabeza.rotation.x - e.relative.y * SENSIBILIDAD, -1.4, 1.4)
	elif e.is_action_pressed("pausa"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	elif e.is_action_pressed("interactuar") and controlable and not interactuar_bloqueado and _foco != "":
		interaccion.emit(_foco)


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= GRAVEDAD * delta
	var entrada := Input.get_vector("izquierda", "derecha", "adelante", "atras") if controlable else Vector2.ZERO
	var corre := Input.is_action_pressed("correr")
	var vel := VEL_CORRER if corre else VEL_CAMINAR
	var dir := (transform.basis * Vector3(entrada.x, 0, entrada.y)).normalized()
	var acel := 10.0 if is_on_floor() else 2.0
	velocity.x = move_toward(velocity.x, dir.x * vel, acel * vel * delta)
	velocity.z = move_toward(velocity.z, dir.z * vel, acel * vel * delta)
	move_and_slide()

	var rapidez := Vector2(velocity.x, velocity.z).length()
	if is_on_floor() and rapidez > 0.5:
		_bob += delta * rapidez * 2.1
		_hasta_paso -= delta * rapidez
		if _hasta_paso <= 0.0:
			_hasta_paso = 1.45 if corre else 1.25
			_pasos.stream = _sonidos_paso.pick_random()
			_pasos.pitch_scale = randf_range(0.9, 1.1)
			_pasos.play()
	else:
		_bob = lerp(_bob, round(_bob / PI) * PI, delta * 5.0)
	camara.position.y = sin(_bob) * 0.035
	camara.position.x = cos(_bob * 0.5) * 0.02


func _process(_delta: float) -> void:
	var mejor := ""
	var mejor_d := INF
	if controlable and not interactuar_bloqueado:
		var ojo := camara.global_position
		var frente := -camara.global_transform.basis.z
		for id in _interacciones:
			var it: Dictionary = _interacciones[id]
			var hacia: Vector3 = it.pos - ojo
			var d := hacia.length()
			if d > it.radio:
				continue
			if d > 1.2 and frente.dot(hacia / d) < 0.55:
				continue
			if d < mejor_d:
				mejor_d = d
				mejor = id
	_foco = mejor
	if ui:
		ui.aviso(_interacciones[mejor].texto if mejor != "" else "")
