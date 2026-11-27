extends Node
## Recorre la Escena 1 de principio a fin simulando las acciones del jugador
## y verifica cada paso: misiones, decisiones, firmas, falla por tiempo y cierre.
## Uso: godot --headless --path juego res://tests/prueba_flujo.tscn

const NIVEL := preload("res://escenas/niveles/asamblea_1825.tscn")

var _pasos := 0
var _fallos: Array[String] = []
var _escena_completada := false


func _ready() -> void:
	EstadoJuego.reiniciar()
	var nivel := NIVEL.instantiate()
	add_child(nivel)
	await get_tree().process_frame
	await get_tree().process_frame

	var gestor: GestorMisiones = nivel.get_node("GestorMisiones")
	var interfaz: Interfaz = nivel.get_node("Interfaz")
	var jugador: Jugador = nivel.get_node("Jugador")
	var acta: ObjetoTomable = nivel.get_node("Objetos/Acta")
	var credencial: ObjetoTomable = nivel.get_node("Objetos/Credencial")
	var mesa: PuntoEntrega = nivel.get_node("Objetos/MesaSecretaria")
	var serrano: Personaje = nivel.get_node("Personajes/Serrano")
	gestor.escena_completada.connect(func(_datos: Dictionary) -> void: _escena_completada = true)

	# Física: el jugador debe quedar parado sobre el piso (colisión de la arquitectura)
	for i in 90:
		await get_tree().physics_frame
	_comprobar(jugador.is_on_floor() and jugador.global_position.y > -0.2, "El jugador queda parado sobre el piso del patio")

	# Misión 1: llegar a la Sala Mayor
	_comprobar(_mision(gestor) == "m1_llegada", "La escena empieza en la misión 1")
	_comprobar(not acta.puede_interactuar(jugador), "El Acta no se puede tomar antes de la misión de firmas")
	_comprobar(serrano.nombre_visible == "Mariano Serrano", "Los personajes toman su nombre del JSON")
	interfaz._terminar_dialogo("mendizabal", gestor.dialogo_para("mendizabal"))
	EstadoJuego.tomar_decision("d_sede", "chuquisaca")
	credencial.interactuar(jugador)
	_comprobar(not credencial.visible, "La credencial desaparece al tomarla")
	EstadoJuego.registrar("zona", "sala_mayor")

	# Misión 2: las tres posturas
	_comprobar(_mision(gestor) == "m2_posturas", "Pasa a la misión 2")
	for id in ["diputado_peru", "diputado_rioplata", "olaneta"]:
		var variante := gestor.dialogo_para(id)
		_comprobar(variante.get("si_mision", "") == "m2_posturas", "%s usa el diálogo de la misión 2" % id)
		interfaz._terminar_dialogo(id, variante)

	# Misión 3: votación
	_comprobar(_mision(gestor) == "m3_votacion", "Pasa a la misión 3")
	interfaz._terminar_dialogo("serrano", gestor.dialogo_para("serrano"))
	EstadoJuego.tomar_decision("d_destino", "independencia")
	EstadoJuego.tomar_decision("d_nombre", "republica_bolivar")

	# Misión 4: firmas, primero fallando por tiempo
	_comprobar(_mision(gestor) == "m4_firmas", "Pasa a la misión 4")
	_comprobar(acta.puede_interactuar(jugador), "En la misión 4 el Acta se puede tomar")
	acta.interactuar(jugador)
	_comprobar(jugador.sostiene("acta"), "El jugador sostiene el Acta")
	nivel.get_node("Personajes/Mendizabal").interactuar(jugador)
	_comprobar(EstadoJuego.cantidad("firma", "*") == 1, "Mendizábal firma")
	gestor._fallar()
	_comprobar(EstadoJuego.cantidad("firma", "*") == 0, "Al acabarse el tiempo se borran las firmas")
	_comprobar(not jugador.sostiene("acta") and acta.get_parent().name == "Objetos", "Al acabarse el tiempo el Acta vuelve a la mesa")

	acta.interactuar(jugador)
	serrano.interactuar(jugador)
	_comprobar(EstadoJuego.cantidad("firma_presidente", "serrano") == 0, "Serrano no firma sin tres firmas previas")
	for ruta in ["Personajes/Mendizabal", "Personajes/DiputadoPeru", "Personajes/Olaneta"]:
		nivel.get_node(ruta).interactuar(jugador)
	_comprobar(EstadoJuego.cantidad("firma", "*") == 3, "Tres diputados firman")
	serrano.interactuar(jugador)

	# Misión 5: entrega
	_comprobar(_mision(gestor) == "m5_entrega", "Pasa a la misión 5")
	_comprobar(mesa.puede_interactuar(jugador), "Se puede dejar el Acta en la mesa")
	mesa.interactuar(jugador)
	_comprobar(acta.get_parent().name == "Soporte", "El Acta queda sobre la mesa")
	_comprobar(_escena_completada, "La escena se completa")

	# Fuentes
	_comprobar("f_congreso" in EstadoJuego.fichas_desbloqueadas, "El cierre desbloquea la ficha del Congreso")
	var fuentes := Fuentes.fuentes_de_fichas(EstadoJuego.fichas_desbloqueadas)
	_comprobar(not fuentes.is_empty() and fuentes[0]["tipo"] == "oficial", "La bibliografía lista primero las fuentes oficiales")
	for id_ficha in EstadoJuego.fichas_desbloqueadas:
		_comprobar(not Fuentes.fuentes_de(Fuentes.obtener_ficha(id_ficha)).is_empty(), "La ficha %s cita fuentes" % id_ficha)

	print("Fichas desbloqueadas: %d · Fuentes citadas: %d" % [EstadoJuego.fichas_desbloqueadas.size(), fuentes.size()])
	print("Pasos comprobados: %d · Fallos: %d" % [_pasos, _fallos.size()])
	for fallo in _fallos:
		printerr("FALLO: " + fallo)
	get_tree().quit(1 if not _fallos.is_empty() else 0)


func _mision(gestor: GestorMisiones) -> String:
	return str(gestor.mision_actual().get("id", ""))


func _comprobar(condicion: bool, descripcion: String) -> void:
	_pasos += 1
	if condicion:
		print("  ok  " + descripcion)
	else:
		_fallos.append(descripcion)
		print("  XX  " + descripcion)
