class_name GestorMisiones
extends Node
## Lee el JSON de la escena y avanza las misiones según los eventos de EstadoJuego.

signal mision_actualizada(mision: Dictionary, objetivos: Array)
signal tiempo_actualizado(segundos: float)
signal mision_fallida(mision: Dictionary)
signal escena_completada(escena: Dictionary)

@export_file("*.json") var ruta_escena := "res://data/escenas/asamblea_1825.json"

var datos: Dictionary = {}
var _indice := -1
var _tiempo_restante := 0.0
var _completada := false


func _ready() -> void:
	datos = Fuentes.leer_json(ruta_escena)
	for error in ValidadorEscena.validar(datos, Fuentes):
		push_error("[Escena %s] %s" % [ruta_escena.get_file(), error])
	EstadoJuego.evento_registrado.connect(_al_evento)
	# Diferido para que la interfaz alcance a conectarse antes de la primera misión.
	_activar.call_deferred(0)


func _process(delta: float) -> void:
	if _tiempo_restante <= 0.0:
		return
	_tiempo_restante = maxf(_tiempo_restante - delta, 0.0)
	tiempo_actualizado.emit(_tiempo_restante)
	if is_zero_approx(_tiempo_restante):
		_fallar()


func mision_actual() -> Dictionary:
	var misiones: Array = datos.get("misiones", [])
	if _indice >= 0 and _indice < misiones.size():
		return misiones[_indice]
	return {}


func personaje(id: String) -> Dictionary:
	return datos.get("personajes", {}).get(id, {})


func objeto(id: String) -> Dictionary:
	return datos.get("objetos", {}).get(id, {})


func decision(id: String) -> Dictionary:
	return datos.get("decisiones", {}).get(id, {})


## Elige la variante de diálogo de un personaje según la misión actual.
## Gana la primera variante cuya "si_mision" coincide; si ninguna, la que no tiene condición.
func dialogo_para(id_personaje: String) -> Dictionary:
	var variantes: Array = datos.get("dialogos", {}).get(id_personaje, [])
	for variante: Dictionary in variantes:
		if str(variante.get("si_mision", "")) == EstadoJuego.mision_actual:
			return variante
	for variante: Dictionary in variantes:
		if not variante.has("si_mision"):
			return variante
	return {}


func estado_objetivos(mision: Dictionary) -> Array:
	var estados: Array = []
	for objetivo: Dictionary in mision.get("objetivos", []):
		var requerido := int(objetivo.get("cantidad", 1))
		var actual := EstadoJuego.cantidad(str(objetivo.get("tipo", "")), str(objetivo.get("objetivo", "")))
		var texto := str(objetivo.get("texto", ""))
		if requerido > 1:
			texto += " (%d/%d)" % [mini(actual, requerido), requerido]
		estados.append({"texto": texto, "cumplido": actual >= requerido})
	return estados


func _activar(indice: int) -> void:
	_indice = indice
	var misiones: Array = datos.get("misiones", [])
	if _indice >= misiones.size():
		_completar_escena()
		return
	var mision := mision_actual()
	EstadoJuego.mision_actual = str(mision.get("id", ""))
	_tiempo_restante = float(mision.get("tiempo_limite", 0))
	_revisar()


func _al_evento(_tipo: String, _id: String) -> void:
	_revisar()


func _revisar() -> void:
	if _completada:
		return
	var mision := mision_actual()
	if mision.is_empty():
		return
	var estados := estado_objetivos(mision)
	mision_actualizada.emit(mision, estados)
	for estado: Dictionary in estados:
		if not estado["cumplido"]:
			return
	EstadoJuego.aviso.emit("Misión cumplida: %s" % mision.get("titulo", ""))
	_activar(_indice + 1)


func _fallar() -> void:
	var mision := mision_actual()
	var ids_tomados := []
	for objetivo: Dictionary in mision.get("objetivos", []):
		var tipo := str(objetivo.get("tipo", ""))
		var id := str(objetivo.get("objetivo", ""))
		EstadoJuego.olvidar(tipo, id)
		if tipo == "tomar":
			ids_tomados.append(id)
	get_tree().call_group("jugador", "soltar_objeto_en_mano")
	get_tree().call_group("restaurables", "restaurar_si_id", ids_tomados)
	mision_fallida.emit(mision)
	EstadoJuego.aviso.emit("Se acabó el tiempo. La misión vuelve a empezar.")
	_tiempo_restante = float(mision.get("tiempo_limite", 0))
	_revisar()


func _completar_escena() -> void:
	_completada = true
	_tiempo_restante = 0.0
	EstadoJuego.mision_actual = ""
	for id_ficha: String in datos.get("cierre", {}).get("fichas", []):
		EstadoJuego.desbloquear_ficha(id_ficha)
	escena_completada.emit(datos)
