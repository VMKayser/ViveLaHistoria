extends SceneTree
## Valida fuentes, fichas y escenas sin abrir el juego.
## Uso: godot --headless --path juego --script res://tests/validar_datos.gd
## Sale con código 1 si hay errores (sirve para CI o antes de cada commit).

const ESCENAS := ["res://data/escenas/asamblea_1825.json"]


func _init() -> void:
	var repositorio: RepositorioFuentes = load("res://scripts/autoload/fuentes.gd").new()
	repositorio.cargar()
	var errores := PackedStringArray(repositorio.validar())
	for ruta: String in ESCENAS:
		for error in ValidadorEscena.validar(repositorio.leer_json(ruta), repositorio):
			errores.append("%s: %s" % [ruta.get_file(), error])

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
