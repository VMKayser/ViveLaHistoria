class_name ZonaEvento
extends Area3D
## Registra un evento "zona" cuando el jugador entra (por ejemplo, a la Sala Mayor).

@export var id_zona := ""
@export var mensaje_al_entrar := ""

var _visitada := false


func _ready() -> void:
	body_entered.connect(_al_entrar)


func _al_entrar(cuerpo: Node3D) -> void:
	if not (cuerpo is Jugador):
		return
	EstadoJuego.registrar("zona", id_zona)
	if not _visitada and not mensaje_al_entrar.is_empty():
		EstadoJuego.aviso.emit(mensaje_al_entrar)
	_visitada = true
