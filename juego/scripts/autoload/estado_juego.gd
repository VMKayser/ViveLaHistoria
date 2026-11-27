extends Node
## Estado de la partida y bus de eventos entre el mundo 3D y la interfaz.
##
## El mundo registra lo que hace el jugador (tomar, hablar, entrar a una zona,
## firmar, entregar, decidir) y el gestor de misiones lo lee para avanzar.

signal evento_registrado(tipo: String, id: String)
signal decision_tomada(decision_id: String, opcion_id: String)
signal ficha_desbloqueada(ficha_id: String)

# Pedidos a la interfaz. Cualquier nodo puede emitirlos sin conocer la interfaz.
signal solicitud_ficha(ficha_id: String)
signal solicitud_dialogo(personaje_id: String)
signal solicitud_decision(decision_id: String)
signal aviso(texto: String)

var mision_actual: String = ""
var decisiones: Dictionary = {}
var fichas_desbloqueadas: Array[String] = []
var _eventos: Dictionary = {}


func registrar(tipo: String, id: String) -> void:
	var clave := _clave(tipo, id)
	_eventos[clave] = int(_eventos.get(clave, 0)) + 1
	evento_registrado.emit(tipo, id)


## Cuántas veces ocurrió un evento. Con id "*" cuenta los ids distintos de ese tipo.
func cantidad(tipo: String, id: String) -> int:
	if id == "*":
		var distintos := 0
		var prefijo := tipo + ":"
		for clave: String in _eventos:
			if clave.begins_with(prefijo) and int(_eventos[clave]) > 0:
				distintos += 1
		return distintos
	return int(_eventos.get(_clave(tipo, id), 0))


## Borra eventos (por ejemplo, al fallar una misión con tiempo). Con id "*" borra todo el tipo.
func olvidar(tipo: String, id: String) -> void:
	if id == "*":
		var prefijo := tipo + ":"
		for clave: String in _eventos.keys():
			if clave.begins_with(prefijo):
				_eventos.erase(clave)
	else:
		_eventos.erase(_clave(tipo, id))


func tomar_decision(decision_id: String, opcion_id: String) -> void:
	decisiones[decision_id] = opcion_id
	decision_tomada.emit(decision_id, opcion_id)
	registrar("decision", decision_id)


func desbloquear_ficha(ficha_id: String) -> void:
	if ficha_id.is_empty() or ficha_id in fichas_desbloqueadas:
		return
	fichas_desbloqueadas.append(ficha_id)
	ficha_desbloqueada.emit(ficha_id)


func reiniciar() -> void:
	mision_actual = ""
	decisiones.clear()
	fichas_desbloqueadas.clear()
	_eventos.clear()


func _clave(tipo: String, id: String) -> String:
	return "%s:%s" % [tipo, id]
