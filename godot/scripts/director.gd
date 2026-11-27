extends Node
## Guion interactivo de la noche del 25 de mayo de 1809 en La Plata.
##
## Hechos en que se basa (ver "Fuentes históricas" en el README): el arresto del abogado Jaime de
## Zudáñez, «el defensor de los pobres»; el repique a rebato de las campanas de
## San Francisco por los Lemoine; la multitud que acude al arzobispo; la
## liberación de Zudáñez; el asedio a la casa del presidente García Pizarro, que
## entregó el mando y fue apresado. Los diálogos son dramatizaciones.

const Persona := preload("res://scripts/persona.gd")
const Materiales := preload("res://scripts/materiales.gd")

const PASOS := ["intro", "arresto", "llamado", "torre", "rebato", "pueblo", "audiencia", "final"]

const PUEBLO := Color(1.0, 0.72, 0.42)
const SOLDADOS := Color(1.0, 0.3, 0.2)
const ZUDANEZ := Color(1.0, 0.95, 0.72)
const LEMOINE := Color(0.6, 0.85, 1.0)
const ARZOBISPO := Color(0.8, 0.62, 1.0)
const TIPOS_PUEBLO := ["hombre_a", "hombre_b", "hombre_c", "mujer_a", "mujer_b", "mujer_c", "hombre_a", "mujer_a", "criollo", "fraile"]
const MAX_LUCES := 8

# Por dónde llega la gente a la plaza mientras suenan las campanas.
const ENTRADAS := [
	[Vector3(27.5, 0, -110), [Vector3(27.5, 0, -28)]],
	[Vector3(-55, 0, -27.5), []],
	[Vector3(55, 0, -27.5), []],
	[Vector3(27.5, 0, 55), [Vector3(27.5, 0, -27.5)]],
	[Vector3(-27.5, 0, 55), [Vector3(-27.5, 0, -27.5)]],
	[Vector3(-27.5, 0, -55), [Vector3(-27.5, 0, -27.5)]],
]

var nivel
var ui
var jugador
var terminado := false
var multitud: Array = []
var lemoine
var zudanez
var campana: Node3D

var _base_campana: Transform3D
var _ang := 0.0
var _vel := 0.0
var _badajo: Node3D
var _son_campana: AudioStreamPlayer3D
var _centro := Node3D.new()
var _son_multitud: AudioStreamPlayer3D
var _son_fuego: AudioStreamPlayer3D
var _luces := 0
var _campanas_catedral := false
var _entrada := 0
var piloto := false


func _ready() -> void:
	piloto = nivel.args.has("piloto")
	if piloto:
		Engine.time_scale = 4.0
	ui = nivel.ui
	jugador = nivel.jugador
	add_child(_centro)
	_son_multitud = nivel.bucle_3d("multitud", _centro, -60.0, 14.0)
	_son_fuego = nivel.bucle_3d("fuego", _centro, -60.0, 6.0)


func iniciar(desde: String) -> void:
	var i := PASOS.find(desde)
	if i < 0:
		i = 0
	if i > 0:
		ui.fundido.color.a = 0.0
	for k in range(i, PASOS.size()):
		var saltar := k == i and i > 0
		print("[paso] ", PASOS[k])
		match PASOS[k]:
			"intro": await _intro()
			"arresto": await _arresto(saltar)
			"llamado": await _llamado(saltar)
			"torre": await _torre(saltar)
			"rebato": await _rebato(saltar)
			"pueblo": await _pueblo(saltar)
			"audiencia": await _audiencia(saltar)
			"final": await _final()


# ------------------------------------------------------------------ utilidades

func g(nombre: String) -> Vector3:
	return nivel.pos(nombre)


func esperar(s: float) -> void:
	await get_tree().create_timer(s).timeout


func hasta(cond: Callable, max_s := INF) -> void:
	if piloto:
		max_s = min(max_s, 1.5)
	var t := 0.0
	while not cond.call() and t < max_s:
		await get_tree().process_frame
		t += get_process_delta_time()


func cerca(p: Vector3, r: float) -> bool:
	var a: Vector3 = jugador.global_position
	return Vector2(a.x - p.x, a.z - p.z).length() < r and abs(a.y - p.y) < 4.0


func esperar_interaccion(id: String) -> void:
	if piloto:
		await esperar(0.5)
		return
	while true:
		var r: String = await jugador.interaccion
		if r == id:
			return


func nueva(tipo: String, _tinte: Color, p: Vector3, _inten := 1.0, de_golpe := false):
	var f = Persona.new()
	f.tipo = tipo
	f.position = p
	nivel.add_child(f)
	f.aparecer(de_golpe)
	return f


func _dispersar(c: Vector3, ancho: float, z0: float, z1: float) -> Vector3:
	return c + Vector3(randf_range(-ancho, ancho), 0, randf_range(z0, z1))


func _antorcha(p) -> void:
	var con_luz := _luces < MAX_LUCES
	p.con_antorcha(con_luz)
	if con_luz:
		_luces += 1
		nivel.luces_fuego.append(p.luz)


func _process(delta: float) -> void:
	if campana:
		var acel := -9.0 * sin(_ang) - 0.55 * _vel
		_vel += acel * delta
		_ang += _vel * delta
		campana.transform = _base_campana * Transform3D(Basis(Vector3.RIGHT, _ang), Vector3.ZERO)
		if _badajo:
			_badajo.rotation.x = lerp(_badajo.rotation.x, -_ang * 0.6, clamp(delta * 4.0, 0.0, 1.0))
	if not multitud.is_empty() and Engine.get_process_frames() % 20 == 0:
		var suma := Vector3.ZERO
		var n := 0
		for p in multitud:
			if is_instance_valid(p):
				suma += p.global_position
				n += 1
		if n > 0:
			_centro.global_position = suma / n


# ------------------------------------------------------------------ pasos

func _intro() -> void:
	nivel.fijar_hora(0.0)
	jugador.controlable = false
	jugador.ubicar(g("M_universidad"), Vector3(20, 1.6, -26))
	ui.fundido.color.a = 1.0
	_gente_de_plaza()
	await esperar(0.8)
	await ui.tarjeta("La Plata, 25 de mayo de 1809", "Cinco de la tarde", 3.5)
	await ui.decir("", "Corre un rumor por la ciudad: el presidente García Pizarro y el arzobispo quieren entregar Charcas a la princesa Carlota del Brasil.", 7.0)
	nivel.fijar_hora(0.12, 70.0)
	await ui.fundir(0.0, 2.5)
	jugador.controlable = true
	ui.ayuda("Clic para mirar  ·  W A S D caminar  ·  Shift correr  ·  E interactuar", 12.0)
	ui.objetivo("Observa la plaza")
	await ui.decir("", "Eres estudiante de la Universidad de San Francisco Xavier. En sus aulas, los doctores de Charcas discuten en voz baja.", 6.5)
	await esperar(2.0)


func _gente_de_plaza() -> void:
	var puntos := [Vector3(10, 0, 8), Vector3(-6, 0, 12), Vector3(-12, 0, -6), Vector3(4, 0, -10),
		Vector3(16, 0, -14), Vector3(-16, 0, 14), Vector3(8, 0, 16), Vector3(-3, 0, -16), Vector3(18, 0, 4)]
	var tipos := ["mujer_a", "hombre_a", "fraile", "criollo", "mujer_b", "hombre_b", "mujer_c", "hombre_c", "criollo"]
	for i in puntos.size():
		var p = nueva(tipos[i], PUEBLO, puntos[i])
		p.velocidad = randf_range(0.7, 1.1)
		p.rotation.y = randf() * TAU
		p.set_meta("deambula", true)
		multitud.append(p)
		if i % 2 == 0:
			_deambular(p)
	nivel.fundir_sonido(_son_multitud, -24.0, 4.0)


func _deambular(p) -> void:
	while is_instance_valid(p) and p.get_meta("deambula", false):
		var a := randf() * TAU
		var r := randf_range(5.0, 20.0)
		p.ir([Vector3(cos(a) * r, 0, sin(a) * r)])
		await p.llego
		if not (is_instance_valid(p) and p.get_meta("deambula", false)):
			return
		await esperar(randf_range(2.0, 6.0))


func _arresto(saltar: bool) -> void:
	if saltar:
		nivel.fijar_hora(0.08)
		jugador.ubicar(g("M_universidad"), Vector3(20, 1.6, -26))
		_gente_de_plaza()
	ui.objetivo("Mira hacia la calle de San Francisco, al norte")
	var ruta := []
	for i in range(1, 7):
		ruta.append(g("R_escolta_%d" % i))
	var dir: Vector3 = (ruta[1] - ruta[0]).normalized()
	var escolta := []
	for i in 5:
		var es_zudanez := i == 2
		var p = nueva("zudanez" if es_zudanez else "soldado", ZUDANEZ if es_zudanez else SOLDADOS,
			ruta[0] - dir * (i * 1.9), 1.5 if es_zudanez else 1.1)
		if es_zudanez:
			p.accion = "prisionero"
		p.ir(ruta, 1.35)
		escolta.append(p)
	zudanez = escolta[2]
	nivel.fundir_sonido(nivel.sonido.tension, -16.0, 8.0)
	await esperar(1.0)
	ui.decir("", "Por la calle de San Francisco bajan soldados del rey. Llevan a alguien preso.", 5.0)
	await hasta(func(): return zudanez.global_position.distance_to(jugador.global_position) < 17.0, 70.0)
	for p in multitud:
		p.set_meta("deambula", false)
		p.ruta.clear()
		p.mirar_nodo = zudanez
	await ui.decir("Jaime de Zudáñez", "¡Me llevan a matar! ¡Pueblo, me llevan a matar!", 4.0)
	nivel.fundir_sonido(_son_multitud, -14.0, 5.0)
	ui.objetivo("Sigue a la escolta")
	# Algunos curiosos van detrás.
	for i in 4:
		var p = multitud[i]
		p.ir([_dispersar(g("M_audiencia"), 7.0, -9.0, -3.0)], randf_range(1.2, 1.6))
	await ui.decir("", "Es Jaime de Zudáñez, abogado de la Audiencia. En la ciudad lo llaman «el defensor de los pobres».", 6.0)
	await hasta(func(): return zudanez.ruta.is_empty(), 90.0)
	for p in escolta:
		p.desaparecer()
	for p in multitud:
		p.mirar_nodo = null
		p.mirar_a = g("M_audiencia")
	await ui.decir("", "Las puertas de la Real Audiencia se cierran tras él.", 4.0)


func _llamado(saltar: bool) -> void:
	if saltar:
		nivel.fijar_hora(0.15)
		jugador.ubicar(Vector3(6, 0, 4), g("M_lemoine"))
		_gente_de_plaza()
	lemoine = nueva("lemoine", LEMOINE, g("M_lemoine"), 1.3)
	lemoine.mirar_nodo = jugador
	lemoine.accion = "llamar"
	ui.objetivo("Acércate al hombre que llama a la gente")
	ui.decir("Una voz", "¡Paisanos! ¡Aquí, paisanos!", 3.0)
	await hasta(func(): return cerca(lemoine.global_position, 4.0))
	await ui.decir("Juan Manuel Lemoine", "¡Se lo llevan preso! Si no despertamos a la ciudad, mañana vienen por todos.", 5.0)
	await ui.decir("Juan Manuel Lemoine", "¡A San Francisco! ¡Hay que tocar las campanas a rebato! ¡Sígueme!", 4.0)
	lemoine.accion = ""
	ui.objetivo("Corre con Lemoine a la iglesia de San Francisco, calle arriba")
	var torre := g("M_sanfrancisco_puerta_torre")
	nivel.mostrar_guia(torre)
	nivel.fijar_hora(0.3, 35.0)
	_guiar(lemoine, [Vector3(16, 0, -6), Vector3(27.5, 0, -30), Vector3(27.5, 0, -60), torre + Vector3(-1.6, 0, 1.0)])
	await hasta(func(): return cerca(torre, 5.0))


func _guiar(p, puntos: Array) -> void:
	for q in puntos:
		p.mirar_nodo = null
		p.ir([q], 4.2)
		await p.llego
		while is_instance_valid(p) and p.global_position.distance_to(jugador.global_position) > 13.0:
			p.mirar_nodo = jugador
			await get_tree().process_frame
	if is_instance_valid(p):
		p.mirar_nodo = jugador


func _crear_campana() -> void:
	if campana:
		return
	campana = load("res://assets/modelos/campana.glb").instantiate()
	nivel.add_child(campana)
	campana.global_transform = nivel.marca("M_sanfrancisco_campana").global_transform
	_base_campana = campana.transform
	Materiales.aplicar(campana)
	_badajo = campana.find_child("badajo", true, false)
	_son_campana = AudioStreamPlayer3D.new()
	_son_campana.stream = load("res://assets/audio/campana.ogg")
	_son_campana.unit_size = 30.0
	_son_campana.max_distance = 800.0
	campana.add_child(_son_campana)


func _al_campanario() -> void:
	_crear_campana()
	var m: Node3D = nivel.marca("M_sanfrancisco_campanario")
	jugador.ubicar(m.global_position, g("M_sanfrancisco_campana") - Vector3(0, 0.5, 0))
	if lemoine == null or not is_instance_valid(lemoine):
		lemoine = nueva("lemoine", LEMOINE, Vector3.ZERO, 1.3, true)
	lemoine.ruta.clear()
	lemoine.global_position = m.global_position + m.global_transform.basis.x * 1.4 + m.global_transform.basis.z * 0.3
	lemoine.mirar_nodo = campana


func _torre(saltar: bool) -> void:
	var torre := g("M_sanfrancisco_puerta_torre")
	if saltar:
		nivel.fijar_hora(0.3)
		jugador.ubicar(torre + Vector3(-3, 0, 4), torre)
		lemoine = nueva("lemoine", LEMOINE, torre + Vector3(-1.6, 0, 1.0), 1.3, true)
		lemoine.mirar_nodo = jugador
	ui.objetivo("Sube al campanario")
	ui.decir("Juan Manuel Lemoine", "¡Arriba, rápido! La puerta de la torre está abierta.", 3.5)
	var m: Node3D = nivel.marca("M_sanfrancisco_puerta_torre")
	var puerta: Vector3 = torre - m.global_transform.basis.z * 1.6 + Vector3(0, 1.3, 0)
	jugador.registrar("torre", puerta, 3.5, "Subir al campanario")
	await esperar_interaccion("torre")
	jugador.quitar("torre")
	nivel.ocultar_guia()
	jugador.controlable = false
	await ui.fundir(1.0, 0.8)
	ui.decir("", "Los escalones de piedra del campanario, a oscuras, con el corazón en la garganta…", 3.5)
	_al_campanario()
	nivel.fijar_hora(0.4)
	await esperar(3.0)
	jugador.controlable = true
	await ui.fundir(0.0, 1.2)


func _golpe_campana() -> void:
	_vel += 2.3 if _vel >= 0.0 else -2.3
	await esperar(0.18)
	_son_campana.pitch_scale = randf_range(0.98, 1.02)
	_son_campana.play()


func _rebato(saltar: bool) -> void:
	if saltar:
		nivel.fijar_hora(0.4)
		_al_campanario()
	ui.objetivo("Toca la campana a rebato")
	jugador.registrar("campana", g("M_sanfrancisco_campana") - Vector3(0, 0.7, 0), 3.5, "Tomar la cuerda de la campana")
	await esperar_interaccion("campana")
	jugador.quitar("campana")
	jugador.interactuar_bloqueado = true
	ui.decir("Juan Manuel Lemoine", "¡Tira con fuerza! Espera a que la campana vuelva y tira otra vez.", 5.0)
	nivel.fundir_sonido(nivel.sonido.tension, -10.0, 4.0)
	const META := 12
	var golpes := 0
	var listo := 1.0
	while golpes < META:
		await get_tree().process_frame
		listo = min(1.0, listo + get_process_delta_time() / 0.8)
		ui.rebato(true, listo, float(golpes) / META)
		if Input.is_action_just_pressed("interactuar") or (piloto and listo >= 0.9):
			if listo >= 0.85:
				golpes += 1
				listo = 0.0
				_golpe_campana()
				_al_golpe(golpes, META)
			else:
				listo = 0.0
	ui.rebato(true, 0.0, 1.0)
	await esperar(1.0)
	ui.rebato(false)
	jugador.interactuar_bloqueado = false
	await ui.decir("", "Las campanas de San Francisco fueron las primeras en sonar. Después sonaron las demás, y la ciudad entera salió a la calle.", 7.0)


func _al_golpe(n: int, meta: int) -> void:
	nivel.fijar_hora(0.4 + 0.45 * n / meta, 1.5)
	nivel.fundir_sonido(_son_multitud, lerp(-30.0, -10.0, float(n) / meta), 2.0)
	if n % 2 == 1:
		_grupo(6)
	match n:
		2:
			ui.decir("", "El tañido rebota en los muros. Abajo se abren puertas y ventanas.", 4.0)
		6:
			_campanas_catedral = true
			_repicar_catedral()
			ui.decir("", "Desde la Catedral responden otras campanas.", 4.0)
		9:
			ui.decir("Voces en la calle", "¡A la plaza! ¡Que suelten a Zudáñez!", 3.5)


func _repicar_catedral() -> void:
	var p := g("M_catedral_campana")
	while _campanas_catedral:
		nivel.sonar_3d("campana_grave", p, 2.0, randf_range(0.97, 1.03), 30.0)
		await esperar(randf_range(1.4, 1.9))


func _grupo(n: int, de_golpe := false) -> void:
	var e: Array = ENTRADAS[_entrada % ENTRADAS.size()]
	_entrada += 1
	var destino := g("M_arzobispo")
	for i in n:
		var origen: Vector3 = e[0] + Vector3(randf_range(-2, 2), 0, randf_range(-2, 2))
		var p = nueva(TIPOS_PUEBLO.pick_random(), PUEBLO, origen if not de_golpe else _dispersar(destino, 9.0, -1.0, 7.0), 1.0, de_golpe)
		if i == 0 or randf() < 0.45:
			_antorcha(p)
		if not de_golpe:
			var via: Array = []
			for q in e[1]:
				via.append(q + Vector3(randf_range(-1.5, 1.5), 0, randf_range(-1.5, 1.5)))
			via.append(_dispersar(destino, 9.0, -1.0, 7.0))
			p.ir(via, randf_range(1.6, 2.2))
		p.mirar_a = g("M_balcon_arzobispo")
		multitud.append(p)


func _pueblo(saltar: bool) -> void:
	if saltar:
		nivel.fijar_hora(0.85)
		_al_campanario()
		for i in 5:
			_grupo(6, true)
		nivel.fundir_sonido(_son_multitud, -10.0, 1.0)
	nivel.fijar_hora(0.88, 8.0)
	nivel.fundir_sonido(_son_fuego, -12.0, 4.0)
	ui.objetivo("Baja y únete al pueblo frente al Palacio Arzobispal")
	var m: Node3D = nivel.marca("M_sanfrancisco_campanario")
	jugador.registrar("bajar", m.global_position - m.global_transform.basis.z * 1.3 + Vector3(0, 1.0, 0), 3.0, "Bajar del campanario")
	await esperar_interaccion("bajar")
	jugador.quitar("bajar")
	jugador.controlable = false
	await ui.fundir(1.0, 0.8)
	jugador.ubicar(g("M_sanfrancisco_puerta_torre"), Vector3(27.5, 1.6, 0))
	if is_instance_valid(lemoine):
		lemoine.desaparecer()
	var faltan := 34 - multitud.size()
	while faltan > 0:
		_grupo(min(6, faltan), true)
		faltan -= 6
	await esperar(0.5)
	jugador.controlable = true
	await ui.fundir(0.0, 1.0)
	await esperar(6.0)
	_campanas_catedral = false
	var arz := g("M_arzobispo")
	nivel.mostrar_guia(arz)
	await hasta(func(): return cerca(arz, 15.0))
	nivel.ocultar_guia()
	await ui.decir("", "Sin otra autoridad a quien acudir, la multitud fue a la casa del arzobispo a pedirle que intercediera por Zudáñez.", 7.0)
	var arzobispo = nueva("arzobispo", ARZOBISPO, g("M_balcon_arzobispo"), 1.4)
	arzobispo.mirar_a = Vector3(0, 0, 0)
	arzobispo.accion = "bendecir"
	for p in multitud:
		if is_instance_valid(p):
			p.mirar_nodo = arzobispo
			if randf() < 0.4:
				p.accion = "vitorear"
	ui.decir("Voces en la multitud", "¡Que lo suelten! ¡Que suelten a Zudáñez!", 4.0)
	await esperar(4.5)
	for p in multitud:
		if is_instance_valid(p):
			p.accion = ""
	await ui.decir("", "Presionado por el pueblo, el presidente García Pizarro tuvo que liberarlo.", 5.5)
	zudanez = nueva("zudanez", ZUDANEZ, arz + Vector3(-9, 0, 3), 1.6)
	zudanez.ir([arz + Vector3(0, 0, 4)], 1.2)
	for p in multitud:
		if is_instance_valid(p):
			p.mirar_nodo = zudanez
			if randf() < 0.7:
				p.accion = "vitorear"
	nivel.sonar_3d("ovacion", arz + Vector3(0, 1.5, 4), 4.0, 1.0, 25.0)
	await ui.decir("", "Zudáñez volvió libre entre la gente. Pero la noche no había terminado.", 5.5)
	zudanez.accion = "vitorear"
	for p in multitud:
		if is_instance_valid(p):
			p.accion = ""
	arzobispo.desaparecer()


func _audiencia(saltar: bool) -> void:
	var aud := g("M_audiencia")
	if saltar:
		nivel.fijar_hora(0.9)
		for i in 6:
			_grupo(6, true)
		jugador.ubicar(g("M_arzobispo") + Vector3(4, 0, 10), aud)
		nivel.fundir_sonido(_son_multitud, -10.0, 1.0)
		nivel.fundir_sonido(_son_fuego, -12.0, 1.0)
	ui.objetivo("Sigue a la multitud hasta la Real Audiencia")
	var balcon := g("M_balcon_audiencia")
	for p in multitud:
		if is_instance_valid(p):
			p.mirar_nodo = null
			p.mirar_a = balcon
			p.ir([_dispersar(aud, 11.0, -10.0, -1.0)], randf_range(1.3, 1.9))
	if is_instance_valid(zudanez):
		zudanez.desaparecer()
	nivel.mostrar_guia(aud)
	var m: Node3D = nivel.marca("M_balcon_audiencia")
	for k in [-2.5, 0.0, 2.5]:
		var s = nueva("soldado", SOLDADOS, balcon + m.global_transform.basis.x * k, 1.1)
		s.mirar_a = Vector3(0, 0, 0)
	await hasta(func(): return cerca(aud, 18.0), 120.0)
	nivel.ocultar_guia()
	await ui.decir("", "Esa noche el pueblo rodeó la casa del presidente García Pizarro.", 5.0)
	ui.decir("Voces en la multitud", "¡Que entregue el mando!", 3.5)
	await esperar(3.0)
	for i in 3:
		nivel.sonar_3d("disparo", balcon + Vector3(0, 1.0, 0), 8.0, randf_range(0.9, 1.1), 30.0)
		await esperar(randf_range(0.5, 1.3))
	await ui.decir("", "Hubo piedras, disparos y muertos en la plaza. Pero el pueblo no se retiró.", 6.0)
	await esperar(2.0)


func _final() -> void:
	jugador.controlable = false
	nivel.fundir_sonido(_son_multitud, -40.0, 6.0)
	nivel.fundir_sonido(_son_fuego, -50.0, 6.0)
	await ui.fundir(1.0, 3.0)
	await ui.tarjeta("Madrugada del 26 de mayo", "García Pizarro entregó el mando y fue apresado. La Real Audiencia asumió el gobierno de la ciudad.", 6.0)
	await ui.tarjeta("El Primer Grito Libertario de América", "Dieciséis años después, en la Universidad que viste esta noche, se firmó la independencia de Bolivia.", 7.0)
	ui._titulo.text = "Ciudad Charcas"
	ui._sub.text = "Casa de la Libertad · Sucre\n\nPulsa R para volver a empezar"
	create_tween().tween_property(ui._tarjeta, "modulate:a", 1.0, 1.5)
	terminado = true
	print("[fin] la historia terminó")
	if piloto:
		await esperar(1.0)
		get_tree().quit()
