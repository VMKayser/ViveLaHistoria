class_name Jugador
extends CharacterBody3D
## Controlador en primera persona: caminar, correr, saltar, mirar,
## interactuar con lo que está al frente y sostener objetos en la mano.

signal enfoque_cambiado(texto: String)

@export var velocidad_caminar := 3.2
@export var velocidad_correr := 6.0
@export var impulso_salto := 4.6
@export var aceleracion := 12.0
@export var sensibilidad_raton := 0.0025
@export var balanceo_mano := 0.012

var objeto_en_mano: ObjetoTomable = null
var controles_activos := true

var _gravedad: float = float(ProjectSettings.get_setting("physics/3d/default_gravity", 9.8))
var _texto_enfoque := ""
var _tiempo_balanceo := 0.0

@onready var cabeza: Node3D = $Cabeza
@onready var camara: Camera3D = $Cabeza/Camara
@onready var rayo: RayCast3D = $Cabeza/Camara/RayoInteraccion
@onready var mano: Node3D = $Cabeza/Camara/Mano
@onready var punto_agarre: Marker3D = $Cabeza/Camara/Mano/PuntoAgarre
@onready var _posicion_mano: Vector3 = mano.position


func _ready() -> void:
	add_to_group("jugador")
	rayo.add_exception(self)


func _unhandled_input(event: InputEvent) -> void:
	if not controles_activos:
		return
	if event is InputEventMouseButton and event.is_pressed():
		if Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		var movimiento := event as InputEventMouseMotion
		rotate_y(-movimiento.relative.x * sensibilidad_raton)
		cabeza.rotate_x(-movimiento.relative.y * sensibilidad_raton)
		cabeza.rotation.x = clampf(cabeza.rotation.x, deg_to_rad(-85.0), deg_to_rad(85.0))
	elif event.is_action_pressed("interactuar"):
		_interactuar()
	elif event.is_action_pressed("inspeccionar") and objeto_en_mano != null:
		objeto_en_mano.inspeccionar()


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= _gravedad * delta

	var direccion := Vector3.ZERO
	var velocidad_objetivo := velocidad_caminar
	if controles_activos:
		if Input.is_action_just_pressed("saltar") and is_on_floor():
			velocity.y = impulso_salto
		var entrada := Input.get_vector("mover_izquierda", "mover_derecha", "mover_adelante", "mover_atras")
		direccion = (transform.basis * Vector3(entrada.x, 0.0, entrada.y)).normalized()
		if Input.is_action_pressed("correr"):
			velocidad_objetivo = velocidad_correr

	var horizontal := Vector3(velocity.x, 0.0, velocity.z)
	horizontal = horizontal.lerp(direccion * velocidad_objetivo, clampf(aceleracion * delta, 0.0, 1.0))
	velocity.x = horizontal.x
	velocity.z = horizontal.z
	move_and_slide()

	_balancear_mano(delta, horizontal.length())
	_actualizar_enfoque()


## Verdadero si el jugador tiene en la mano el objeto con ese id.
func sostiene(id_objeto: String) -> bool:
	return objeto_en_mano != null and objeto_en_mano.id_interaccion == id_objeto


func sostener(objeto: ObjetoTomable) -> void:
	if objeto_en_mano != null:
		objeto_en_mano.restaurar()
	objeto_en_mano = objeto
	objeto.reparent(punto_agarre, false)
	objeto.position = Vector3.ZERO
	objeto.rotation = Vector3.ZERO


## Saca el objeto de la mano para dejarlo en otro lugar (por ejemplo, una mesa).
func entregar_objeto() -> ObjetoTomable:
	var objeto := objeto_en_mano
	objeto_en_mano = null
	return objeto


## Devuelve a su lugar original lo que el jugador tenga en la mano.
func soltar_objeto_en_mano() -> void:
	if objeto_en_mano != null:
		var objeto := objeto_en_mano
		objeto_en_mano = null
		objeto.restaurar()


func _interactuar() -> void:
	var objetivo := _interactuable_enfocado()
	if objetivo != null and objetivo.puede_interactuar(self):
		objetivo.interactuar(self)


func _interactuable_enfocado() -> Interactuable:
	if not rayo.is_colliding():
		return null
	var nodo := rayo.get_collider() as Node
	while nodo != null and not (nodo is Interactuable):
		nodo = nodo.get_parent()
	return nodo as Interactuable


func _actualizar_enfoque() -> void:
	var texto := ""
	if controles_activos:
		var objetivo := _interactuable_enfocado()
		if objetivo != null and objetivo.puede_interactuar(self):
			texto = objetivo.texto_para(self)
		elif objeto_en_mano != null:
			texto = tr("[R] Inspeccionar %s") % objeto_en_mano.nombre_visible
	if texto != _texto_enfoque:
		_texto_enfoque = texto
		enfoque_cambiado.emit(texto)


func _balancear_mano(delta: float, rapidez: float) -> void:
	if is_on_floor() and rapidez > 0.3:
		_tiempo_balanceo += delta * rapidez * 2.2
	var desplazamiento := Vector3(
		sin(_tiempo_balanceo) * balanceo_mano,
		absf(cos(_tiempo_balanceo)) * balanceo_mano,
		0.0)
	mano.position = mano.position.lerp(_posicion_mano + desplazamiento, clampf(10.0 * delta, 0.0, 1.0))
