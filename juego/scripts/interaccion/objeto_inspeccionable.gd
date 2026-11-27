class_name ObjetoInspeccionable
extends Interactuable
## Algo que se observa pero no se toma (un retrato, una placa, un mapa).
## Al usarlo muestra su ficha histórica con la fuente.


func _ready() -> void:
	super()
	verbo = "Observar"


func interactuar(_jugador: Jugador) -> void:
	EstadoJuego.registrar("observar", id_interaccion)
	EstadoJuego.desbloquear_ficha(ficha_id)
	EstadoJuego.solicitud_ficha.emit(ficha_id)
