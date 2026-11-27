extends Node
## Autoload Interaccion: punto de encuentro de lo que viene (personajes, escenas históricas, escape rooms) con el núcleo
## de la ciudad, por señales, sin tocar principal.gd ni ciudad.gd.
##
## Un contenido nuevo registra sus zonas (Area3D) con un id; el caminante entra o sale de ellas y, con la tecla Intro (o el
## botón de acción del APK), "usa" la zona más cercana en la que está. Quien la registró escucha las señales y hace lo
## suyo (abrir un diálogo, empezar una escena, mostrar una pista).

signal entro(id: String)
signal salio(id: String)
signal accion(id: String)

var _zonas := {}            # id -> Area3D
var _dentro: Array[String] = []

## Registra un Area3D como zona interactiva. La capa 8 es la del caminante (jugador.gd).
func registrar(id: String, zona: Area3D) -> void:
	_zonas[id] = zona
	zona.collision_mask = 8
	zona.monitoring = true
	zona.body_entered.connect(func(_b): _entrar(id))
	zona.body_exited.connect(func(_b): _salir(id))

func quitar(id: String) -> void:
	_zonas.erase(id)
	_salir(id)

## Zona activa (la última en la que entró el caminante), o "".
func actual() -> String:
	return _dentro[-1] if not _dentro.is_empty() else ""

func usar() -> void:
	var id := actual()
	if id != "":
		accion.emit(id)

func _entrar(id: String) -> void:
	if not _dentro.has(id):
		_dentro.append(id)
		entro.emit(id)

func _salir(id: String) -> void:
	if _dentro.has(id):
		_dentro.erase(id)
		salio.emit(id)

func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo:
		if e.physical_keycode in [KEY_ENTER, KEY_KP_ENTER]:
			usar()
		elif e.physical_keycode == KEY_E and actual() != "":
			usar()
