extends Node
## Registra las acciones de entrada por código, para no depender de la
## configuración del editor y que todo el equipo tenga los mismos controles.

const ACCIONES := {
	"mover_adelante": [KEY_W, KEY_UP],
	"mover_atras": [KEY_S, KEY_DOWN],
	"mover_izquierda": [KEY_A, KEY_LEFT],
	"mover_derecha": [KEY_D, KEY_RIGHT],
	"correr": [KEY_SHIFT],
	"saltar": [KEY_SPACE],
	"interactuar": [KEY_E],
	"inspeccionar": [KEY_R],
	"diario": [KEY_TAB],
}


func _ready() -> void:
	for accion: String in ACCIONES:
		if not InputMap.has_action(accion):
			InputMap.add_action(accion)
		for tecla: int in ACCIONES[accion]:
			var evento := InputEventKey.new()
			evento.physical_keycode = tecla
			InputMap.action_add_event(accion, evento)
