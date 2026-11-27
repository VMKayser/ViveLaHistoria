class_name Jugador
extends CharacterBody3D
## Recorrido a pie en primera persona (portado de web/src/ciudad/motor/ControlPeaton.ts): gravedad, escalones bajos,
## choques que dejan deslizar, velocidad con inercia, balanceo de la cabeza ligado a la distancia recorrida.

const ALTURA_OJOS := 1.65
const VEL_CAMINAR := 2.6
const VEL_CORRER := 5.5
const ACELERACION := 9.0
const FRENADO := 11.0
const LARGO_PASO := 0.75
const BOB_ALTO := 0.032
const BOB_LADO := 0.018
const BOB_ROLL := 0.0045
const FOV_BASE := 68.0
const PITCH_MAX := 1.2
const ESCALON_MAX := 0.6
const RADIO := 0.35
const VEL_GIRO := 1.7              # rad/s (teclado, Q/E y flechas)
const SENS_ARRASTRE := 0.0042      # rad/px (ratón, arrastrar para mirar sin capturar el puntero)

var camara: Camera3D
var yaw := 0.0
var pitch := 0.0
var entrada := Vector2.ZERO        # x: lado (+ derecha), y: adelante (+)
var correr := false
var activo := false
var ciudad: Ciudad
var _fase := 0.0
var _bob := 0.0
var _fov := FOV_BASE
var _ojos_y := 0.0
var _giro_vel := 0.0
var _arrastrando := false

func _ready() -> void:
	collision_layer = 8                     # caminante (los vehículos lo ven y no lo atraviesan)
	collision_mask = 7                      # suelo (1), sólidos (2) y vehículos (4)
	floor_snap_length = 0.7
	floor_max_angle = deg_to_rad(55.0)
	var forma := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = RADIO
	cap.height = 1.75
	forma.shape = cap
	forma.position.y = 0.875 + 0.02
	add_child(forma)
	camara = Camera3D.new()
	camara.fov = FOV_BASE
	camara.near = 0.1
	camara.far = 6000.0
	camara.position.y = ALTURA_OJOS
	add_child(camara)
	_ojos_y = ALTURA_OJOS

## Coloca los pies en p mirando con rumbo 'rumbo' (0 = norte, −z).
func colocar(p: Vector3, rumbo: float) -> void:
	global_position = p
	velocity = Vector3.ZERO
	yaw = rumbo
	pitch = 0.0
	_aplicar_rotacion()
	reset_physics_interpolation()   # un salto, no un movimiento: sin interpolar desde donde estaba

func mirar(dx: float, dy: float) -> void:
	yaw -= dx
	pitch = clampf(pitch - dy, -PITCH_MAX, PITCH_MAX)
	_aplicar_rotacion()

func _aplicar_rotacion() -> void:
	rotation.y = yaw
	camara.rotation.x = pitch

## Ratón: arrastrar con el botón izquierdo para mirar (como la web). El teclado se lee en _teclado().
func _unhandled_input(ev: InputEvent) -> void:
	if not activo:
		return
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		_arrastrando = ev.pressed
	elif ev is InputEventMouseMotion and _arrastrando and not DisplayServer.is_touchscreen_available():
		mirar(ev.relative.x * SENS_ARRASTRE, ev.relative.y * SENS_ARRASTRE)

## WASD / flechas para caminar, Q E (y flechas a los lados) para girar, R F para mirar arriba y abajo, Shift para correr.
func _teclado(dt: float) -> void:
	var adelante := float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)) - float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN))
	var lado := float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A))
	var e_para_interaccion := Interaccion != null and Interaccion.actual() != ""
	var giro := float(Input.is_physical_key_pressed(KEY_Q) or Input.is_physical_key_pressed(KEY_LEFT)) - float((not e_para_interaccion and Input.is_physical_key_pressed(KEY_E)) or Input.is_physical_key_pressed(KEY_RIGHT))
	var cabeceo := float(Input.is_physical_key_pressed(KEY_R)) - float(Input.is_physical_key_pressed(KEY_F))
	if adelante != 0.0 or lado != 0.0:
		entrada = Vector2(lado, adelante)
		correr = Input.is_physical_key_pressed(KEY_SHIFT)
	elif not _tactil_activo:
		entrada = Vector2.ZERO
	# giro con inercia (≈ 0,15 s)
	_giro_vel = lerpf(_giro_vel, giro * VEL_GIRO, 1.0 - exp(-10.0 * dt))
	if absf(_giro_vel) > 0.0005 or cabeceo != 0.0:
		mirar(-_giro_vel * dt, -cabeceo * 1.2 * dt)

var _tactil_activo := false
## La interfaz táctil (joystick) fija la entrada; mientras el dedo esté puesto, el teclado no la pisa.
func entrada_tactil(v: Vector2, c: bool) -> void:
	entrada = v
	correr = c
	_tactil_activo = v.length() > 0.0

func _physics_process(dt: float) -> void:
	if not activo:
		return
	_teclado(dt)
	# sin el suelo cargado debajo no se cae: se espera
	if ciudad != null and not ciudad.suelo_listo(global_position.x, global_position.z):
		velocity = Vector3.ZERO
		return
	dt = minf(dt, 0.12)
	var adelante := Vector3(-sin(yaw), 0.0, -cos(yaw))
	var derecha := Vector3(cos(yaw), 0.0, -sin(yaw))
	var mov := adelante * entrada.y + derecha * entrada.x
	var largo := mov.length()
	if largo > 1.0:
		mov /= largo
		largo = 1.0
	var vmax := VEL_CORRER if correr else VEL_CAMINAR
	var deseada := mov * vmax
	var k := 1.0 - exp(-(ACELERACION if largo > 0.01 else FRENADO) * dt)
	var h := Vector3(velocity.x, 0.0, velocity.z).lerp(deseada, k)
	velocity.x = h.x
	velocity.z = h.z
	if is_on_floor():
		velocity.y = -0.5
	else:
		velocity.y -= 24.0 * dt
	_subir_escalon(Vector3(velocity.x, 0.0, velocity.z) * dt)
	var antes := global_position
	move_and_slide()
	# balanceo de la cabeza (por distancia recorrida)
	var recorrido := Vector2(global_position.x - antes.x, global_position.z - antes.z).length()
	var intensidad := clampf(h.length() / VEL_CAMINAR, 0.0, 1.6)
	_fase += recorrido / LARGO_PASO * PI
	var a := (1.7 if correr else 1.0)
	_bob = lerpf(_bob, intensidad, 1.0 - exp(-8.0 * dt))
	var objetivo_y := ALTURA_OJOS + (-absf(sin(_fase)) * BOB_ALTO * a) * _bob
	_ojos_y = lerpf(_ojos_y, objetivo_y, 1.0 - exp(-14.0 * dt))
	camara.position = Vector3(sin(_fase) * BOB_LADO * _bob, _ojos_y, 0.0)
	camara.rotation.z = sin(_fase) * BOB_ROLL * _bob
	_fov = lerpf(_fov, FOV_BASE + (6.0 if correr and largo > 0.5 else 0.0), 1.0 - exp(-5.0 * dt))
	camara.fov = _fov

## Si algo bajo (bordillo, grada) frena el avance, se sube hasta ESCALON_MAX.
func _subir_escalon(movimiento: Vector3) -> void:
	if not is_on_floor() or movimiento.length() < 0.001:
		return
	if test_move(global_transform, movimiento):
		var arriba := global_transform.translated(Vector3.UP * ESCALON_MAX)
		if not test_move(arriba, movimiento):
			global_position.y += ESCALON_MAX * 0.9
