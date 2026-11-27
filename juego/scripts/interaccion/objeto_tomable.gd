class_name ObjetoTomable
extends Interactuable
## Objeto que el jugador toma con [E].
## GUARDAR: va al inventario y desaparece del escenario (credencial, llaves).
## SOSTENER: queda visible en la mano y se puede llevar a otro lugar (el Acta).

enum Modo { GUARDAR, SOSTENER }

@export var modo: Modo = Modo.GUARDAR

var _padre_inicial: Node
var _transform_inicial: Transform3D


func _ready() -> void:
	super()
	verbo = "Tomar"
	add_to_group("restaurables")
	_padre_inicial = get_parent()
	_transform_inicial = transform


func puede_interactuar(jugador: Jugador) -> bool:
	return super(jugador) and jugador.objeto_en_mano != self


func interactuar(jugador: Jugador) -> void:
	activar_colision(false)
	if modo == Modo.SOSTENER:
		jugador.sostener(self)
	else:
		visible = false
	EstadoJuego.registrar("tomar", id_interaccion)
	if not ficha_id.is_empty():
		EstadoJuego.desbloquear_ficha(ficha_id)
	EstadoJuego.aviso.emit("Tomaste: %s" % nombre_visible)


func inspeccionar() -> void:
	if not ficha_id.is_empty():
		EstadoJuego.solicitud_ficha.emit(ficha_id)


## Vuelve a su lugar original (al fallar una misión o al reiniciar).
func restaurar() -> void:
	if get_parent() != _padre_inicial:
		reparent(_padre_inicial, false)
	transform = _transform_inicial
	visible = true
	activar_colision(true)


func restaurar_si_id(ids: Array) -> void:
	if id_interaccion in ids:
		restaurar()


## Deja el objeto apoyado en un punto del escenario y ya no se puede volver a tomar.
func colocar_en(soporte: Node3D) -> void:
	reparent(soporte, false)
	position = Vector3.ZERO
	rotation = Vector3.ZERO
	activar_colision(false)
