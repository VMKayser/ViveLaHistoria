class_name PuntoEntrega
extends Interactuable
## Lugar donde se deja un objeto que el jugador lleva en la mano (por ejemplo, el Acta).
## Necesita un hijo Marker3D llamado "Soporte" donde queda apoyado el objeto.

@export var objeto_requerido := "acta"

@onready var _soporte: Node3D = get_node_or_null("Soporte")


func _ready() -> void:
	super()
	verbo = "Dejar el objeto en"


func puede_interactuar(jugador: Jugador) -> bool:
	return super(jugador) and jugador.sostiene(objeto_requerido)


func texto_para(jugador: Jugador) -> String:
	return tr("[E] Dejar %s en %s") % [jugador.objeto_en_mano.nombre_visible, nombre_visible]


func interactuar(jugador: Jugador) -> void:
	var objeto := jugador.entregar_objeto()
	if objeto == null:
		return
	objeto.colocar_en(_soporte if _soporte != null else self)
	EstadoJuego.registrar("entregar", id_interaccion)
	EstadoJuego.aviso.emit(tr("Dejaste %s en %s.") % [objeto.nombre_visible, nombre_visible])
