extends SceneTree
## Valida fuentes, fichas y escenas sin abrir el juego.
## Uso: godot --headless --path juego --script res://tests/validar_datos.gd
## Sale con código 1 si hay errores (sirve para CI o antes de cada commit).

const ESCENAS := ["res://data/escenas/asamblea_1825.json"]
## Traducciones: misma estructura e ids que el original; solo cambian los textos de estos campos.
const TRADUCCIONES := {
	"res://data/escenas/asamblea_1825.json": "res://data/en/asamblea_1825.json",
	"res://data/fichas.json": "res://data/en/fichas.json",
}
const CAMPOS_TEXTO := ["titulo", "subtitulo", "aviso_recreacion", "descripcion", "nombre", "rol", "texto", "pregunta",
	"contexto", "reaccion", "cita", "discrepancia", "nota"]


func _init() -> void:
	var repositorio: RepositorioFuentes = load("res://scripts/autoload/fuentes.gd").new()
	repositorio.cargar()
	var errores := PackedStringArray(repositorio.validar())
	for ruta: String in ESCENAS:
		for error in ValidadorEscena.validar(repositorio.leer_json(ruta), repositorio):
			errores.append("%s: %s" % [ruta.get_file(), error])

	for original: String in TRADUCCIONES:
		var traducida: String = TRADUCCIONES[original]
		var a: Variant = JSON.parse_string(FileAccess.get_file_as_string(original))
		var b: Variant = JSON.parse_string(FileAccess.get_file_as_string(traducida))
		if b == null:
			errores.append("%s: no existe o no es JSON válido." % traducida)
		else:
			_comparar_traduccion(a, b, traducida.get_file(), "", errores)

	var fuentes := repositorio.todas_las_fuentes()
	var fichas := repositorio.todas_las_fichas()
	var por_tipo := {}
	for fuente: Dictionary in fuentes:
		por_tipo[fuente["tipo"]] = int(por_tipo.get(fuente["tipo"], 0)) + 1
	var por_estado := {}
	var pendientes := 0
	var con_oficial := 0
	for ficha: Dictionary in fichas:
		por_estado[ficha["estado"]] = int(por_estado.get(ficha["estado"], 0)) + 1
		if not repositorio.esta_aprobada(ficha):
			pendientes += 1
		for fuente: Dictionary in repositorio.fuentes_de(ficha):
			if fuente["tipo"] == "oficial":
				con_oficial += 1
				break

	print("Fuentes: %d %s" % [fuentes.size(), por_tipo])
	print("Fichas: %d %s" % [fichas.size(), por_estado])
	print("Fichas respaldadas por al menos una fuente oficial: %d de %d" % [con_oficial, fichas.size()])
	print("Fichas pendientes de revisión docente: %d" % pendientes)
	if errores.is_empty():
		print("OK: datos consistentes.")
	else:
		for error in errores:
			printerr("ERROR: " + error)
	repositorio.free()
	quit(1 if not errores.is_empty() else 0)


## La traducción debe tener la misma forma que el original: mismas claves, mismas listas y los mismos valores en todo
## lo que no es texto para leer (ids, estados, fuentes, misiones…).
func _comparar_traduccion(a: Variant, b: Variant, archivo: String, ruta: String, errores: PackedStringArray) -> void:
	if typeof(a) != typeof(b):
		errores.append("%s: '%s' cambia de tipo en la traducción." % [archivo, ruta])
	elif a is Dictionary:
		for clave in a:
			if not b.has(clave):
				errores.append("%s: falta '%s/%s' en la traducción." % [archivo, ruta, clave])
			else:
				_comparar_traduccion(a[clave], b[clave], archivo, "%s/%s" % [ruta, clave], errores)
		for clave in b:
			if not a.has(clave):
				errores.append("%s: '%s/%s' sobra en la traducción." % [archivo, ruta, clave])
	elif a is Array:
		if a.size() != b.size():
			errores.append("%s: '%s' tiene %d elementos en el original y %d en la traducción." % [archivo, ruta, a.size(), b.size()])
		else:
			for i in a.size():
				_comparar_traduccion(a[i], b[i], archivo, "%s/%d" % [ruta, i], errores)
	elif a is String:
		var campo := ruta.get_slice("/", ruta.get_slice_count("/") - 1)
		if campo.is_valid_int():
			campo = ruta.get_slice("/", ruta.get_slice_count("/") - 2)
		if not CAMPOS_TEXTO.has(campo) and a != b:
			errores.append("%s: '%s' no es un texto traducible y cambió ('%s' → '%s')." % [archivo, ruta, a, b])
	elif a != b:
		errores.append("%s: '%s' cambió en la traducción." % [archivo, ruta])

