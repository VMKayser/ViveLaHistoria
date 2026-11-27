class_name RepositorioFuentes
extends Node
## Repositorio de fuentes y fichas históricas.
##
## Regla del proyecto: el juego solo muestra datos históricos que están en
## data/fichas.json, y cada ficha cita al menos una fuente de data/fuentes.json.
## Si una ficha o una fuente está incompleta, validar() lo reporta.

const RUTA_FUENTES := "res://data/fuentes.json"
const RUTA_FICHAS := "res://data/fichas.json"

const TIPOS_FUENTE := {
	"oficial": "Fuente oficial",
	"prensa": "Prensa",
	"academica": "Fuente académica",
	"enciclopedia": "Enciclopedia",
}

const ESTADOS_FICHA := {
	"verificada": "Verificada",
	"fuentes_difieren": "Las fuentes difieren",
	"por_verificar": "Por verificar",
}

const CAMPOS_FUENTE := ["titulo", "institucion", "tipo", "url", "consultado"]
const CAMPOS_FICHA := ["titulo", "texto", "estado", "fuentes", "escenas"]

var _fuentes: Dictionary = {}
var _fichas: Dictionary = {}


func _ready() -> void:
	cargar()
	for error in validar():
		push_error("[Fuentes] " + error)


func cargar() -> void:
	_fuentes.clear()
	_fichas.clear()
	for fuente: Dictionary in leer_json(RUTA_FUENTES).get("fuentes", []):
		_fuentes[str(fuente.get("id", ""))] = fuente
	for ficha: Dictionary in leer_json(RUTA_FICHAS).get("fichas", []):
		_fichas[str(ficha.get("id", ""))] = ficha


func tiene_ficha(id: String) -> bool:
	return _fichas.has(id)


func obtener_ficha(id: String) -> Dictionary:
	return _fichas.get(id, {})


func obtener_fuente(id: String) -> Dictionary:
	return _fuentes.get(id, {})


func todas_las_fuentes() -> Array:
	return _fuentes.values()


func todas_las_fichas() -> Array:
	return _fichas.values()


## Fuentes citadas por una ficha, con las oficiales primero.
func fuentes_de(ficha: Dictionary) -> Array:
	var lista: Array = []
	for id: String in ficha.get("fuentes", []):
		if _fuentes.has(id):
			lista.append(_fuentes[id])
	lista.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return _orden_tipo(a) < _orden_tipo(b))
	return lista


## Fuentes distintas citadas por un conjunto de fichas (para la bibliografía).
func fuentes_de_fichas(ids_fichas: Array) -> Array:
	var vistas := {}
	var lista: Array = []
	for id_ficha: String in ids_fichas:
		for fuente: Dictionary in fuentes_de(obtener_ficha(id_ficha)):
			var id_fuente := str(fuente.get("id", ""))
			if not vistas.has(id_fuente):
				vistas[id_fuente] = true
				lista.append(fuente)
	lista.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return _orden_tipo(a) < _orden_tipo(b))
	return lista


func etiqueta_tipo(fuente: Dictionary) -> String:
	return TIPOS_FUENTE.get(fuente.get("tipo", ""), "Fuente")


func etiqueta_estado(ficha: Dictionary) -> String:
	return ESTADOS_FICHA.get(ficha.get("estado", ""), "Sin estado")


func esta_aprobada(ficha: Dictionary) -> bool:
	var revision: Dictionary = ficha.get("revision", {})
	return bool(revision.get("aprobada", false))


## Devuelve la lista de errores de los datos. Vacía = datos consistentes.
func validar() -> PackedStringArray:
	var errores := PackedStringArray()
	for id: String in _fuentes:
		var fuente: Dictionary = _fuentes[id]
		for campo: String in CAMPOS_FUENTE:
			if str(fuente.get(campo, "")).strip_edges().is_empty():
				errores.append("La fuente '%s' no tiene '%s'." % [id, campo])
		if not TIPOS_FUENTE.has(fuente.get("tipo", "")):
			errores.append("La fuente '%s' tiene un tipo desconocido: '%s'." % [id, fuente.get("tipo", "")])
		if not str(fuente.get("url", "")).begins_with("https://"):
			errores.append("La URL de la fuente '%s' debe empezar con https://." % id)
	for id: String in _fichas:
		var ficha: Dictionary = _fichas[id]
		for campo: String in CAMPOS_FICHA:
			if not ficha.has(campo) or str(ficha[campo]).strip_edges().is_empty():
				errores.append("La ficha '%s' no tiene '%s'." % [id, campo])
		var citadas: Array = ficha.get("fuentes", [])
		if citadas.is_empty():
			errores.append("La ficha '%s' no cita ninguna fuente." % id)
		for id_fuente: String in citadas:
			if not _fuentes.has(id_fuente):
				errores.append("La ficha '%s' cita una fuente inexistente: '%s'." % [id, id_fuente])
		var estado := str(ficha.get("estado", ""))
		if not ESTADOS_FICHA.has(estado):
			errores.append("La ficha '%s' tiene un estado desconocido: '%s'." % [id, estado])
		if estado == "fuentes_difieren" and str(ficha.get("discrepancia", "")).is_empty():
			errores.append("La ficha '%s' dice que las fuentes difieren pero no explica la discrepancia." % id)
		if estado == "fuentes_difieren" and citadas.size() < 2:
			errores.append("La ficha '%s' dice que las fuentes difieren pero cita una sola fuente." % id)
	return errores


func leer_json(ruta: String) -> Dictionary:
	var archivo := FileAccess.open(ruta, FileAccess.READ)
	if archivo == null:
		push_error("[Fuentes] No se pudo abrir %s" % ruta)
		return {}
	var datos: Variant = JSON.parse_string(archivo.get_as_text())
	if typeof(datos) != TYPE_DICTIONARY:
		push_error("[Fuentes] JSON inválido en %s" % ruta)
		return {}
	return datos


func _orden_tipo(fuente: Dictionary) -> int:
	return TIPOS_FUENTE.keys().find(fuente.get("tipo", ""))
