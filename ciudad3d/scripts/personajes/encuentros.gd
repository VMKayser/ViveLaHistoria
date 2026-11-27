class_name Encuentros
extends Node
## Los personajes de la ciudad y los encuentros con ellos (plan: personas/encuentros/PLAN.md).
## - Coloca cada personaje cuando el caminante está cerca y el suelo de su lugar ya tiene colisión; lo quita al alejarse.
## - Cerca (< 8 m) el personaje lo mira; a menos de 3 m y de frente aparece "Presiona I para interactuar".
## - Con I (o tocando el aviso en el celular): la cámara pasa a una toma de tres cuartos, el personaje se vuelve y la
##   carta cuenta presentación → historia → por qué hace lo que hace → menú (edificio, despedirse).
## Lo que se contó queda en Guardado ("encuentros": {id: {historia, edificio}}): al volver, empieza en el menú.

signal _respuesta(valor: int)             # 0 = siguiente frase; ≥ 0 en el menú = opción; -1 = despedirse

const RADIO_APARECER := 55.0
const RADIO_QUITAR := 75.0
const RADIO_ATENTO := 8.0
const RADIO_AVISO := 3.0
const RADIO_AVISO_SALIR := 4.5
const ANGULO_AVISO := deg_to_rad(55.0)
const ESPERA_VOLVER := 20.0
const FOV_TOMA := 40.0
const CLAVE := "encuentros"

var jugador: Jugador
var ciudad: Ciudad
var interfaz: Interfaz
var puente: Puente
var trafico: Trafico                        # sus carriles: la ronda de los personajes no pisa la calzada
var _carriles := {}                         # celda de 8 m → PackedVector2Array de puntos de carril
var carta: Carta
var activo := false                         # hay un encuentro en curso
var _datos: Array = []
var _bytes := {}                            # id → PackedByteArray (descargado una vez)
var _bajando := {}
var _personajes := {}                       # id → Personaje
var _candidato: Personaje
var _espera := {}                           # id → segundos sin volver a ofrecer el aviso
var _camara: Camera3D
var _t := 0.0
var _retratos := {}

func _ready() -> void:
	carta = Carta.new()
	carta.name = "Carta"
	add_child(carta)
	carta.siguiente.connect(func(): _respuesta.emit(0))
	carta.elegido.connect(func(i): _respuesta.emit(i))
	carta.tocado_aviso.connect(_interactuar)
	var d = await Datos.json("personajes.json")
	if d is Dictionary:
		_datos = d.get("personajes", [])

# ------------------------------------------------------------------------------------------------- colocar
func _process(dt: float) -> void:
	_t += dt
	for k in _espera.keys():
		_espera[k] -= dt
		if _espera[k] <= 0.0:
			_espera.erase(k)
	if jugador == null or (not jugador.activo and not activo):
		return
	var yo := jugador.global_position
	if _t > 0.5:
		_t = 0.0
		_colocar_cercanos(yo)
	if not activo:
		_elegir_candidato(yo)
	_prueba()

## Solo pruebas (?encuentro=<id> en la web, SUCRE_ENCUENTRO=<id> en el escritorio): se planta frente a ese personaje y
## abre su encuentro; encuentro_dist=m lo mira desde m metros (2,3 por omisión); encuentro_aviso=1 se queda en el aviso.
var _prueba_hecha := false
var _prueba_movido := false
func _prueba() -> void:
	var id := str(Puente.parametro("encuentro")) if Puente.parametro("encuentro") != null else ""
	if id == "" or _prueba_hecha or activo or not jugador.activo:
		return
	if not _personajes.has(id):
		if not _prueba_movido:            # lejos: primero se acerca, para que el personaje aparezca
			for d in _datos:
				if d["id"] == id:
					_prueba_movido = true
					jugador.colocar(Vector3(d["lugar"]["x"] + 3.0, jugador.global_position.y + 6.0, d["lugar"]["z"]), 0.0)
		return
	_prueba_hecha = true
	var p: Personaje = _personajes[id]
	var frente := Vector3(sin(p.rotation.y), 0, cos(p.rotation.y))
	var dist := float(Puente.parametro("encuentro_dist")) if Puente.parametro("encuentro_dist") != null else 2.3
	jugador.colocar(p.global_position + frente * dist + Vector3.UP * 0.05, atan2(frente.x, frente.z))
	if Puente.parametro("encuentro_aviso") != null:
		return
	await get_tree().create_timer(1.0).timeout
	_candidato = p
	_interactuar()

func _colocar_cercanos(yo: Vector3) -> void:
	for d in _datos:
		var id: String = d["id"]
		var lugar := Vector2(d["lugar"]["x"], d["lugar"]["z"])
		var dist := lugar.distance_to(Vector2(yo.x, yo.z))
		if _personajes.has(id):
			if dist > RADIO_QUITAR and not activo:
				_personajes[id].queue_free()
				_personajes.erase(id)
			continue
		if dist > RADIO_APARECER or _bajando.has(id) or not ciudad.suelo_listo(lugar.x, lugar.y):
			continue
		_aparecer(d, lugar)

## Suelo (capa 1) en ese punto si está al aire libre: sin sólidos (capa 2) encima ni a menos de 0,45 m. {} si no.
## (Un rayo que también veía los sólidos dejaba al personaje sobre un tejado.)
func _suelo_libre(estado: PhysicsDirectSpaceState3D, p: Vector2) -> Dictionary:
	var h := estado.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(p.x, 420.0, p.y), Vector3(p.x, -100.0, p.y), 1))
	if h.is_empty():
		return {}
	var pie: Vector3 = h["position"]
	if not estado.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(p.x, 420.0, p.y), pie + Vector3.UP * 0.3, 2)).is_empty():
		return {}
	var forma := PhysicsShapeQueryParameters3D.new()
	var cil := CylinderShape3D.new()
	cil.radius = 0.45
	cil.height = 1.4
	forma.shape = cil
	forma.transform = Transform3D(Basis(), pie + Vector3.UP * 0.9)
	forma.collision_mask = 2
	return {} if not estado.intersect_shape(forma, 1).is_empty() else h

func _aparecer(d: Dictionary, lugar: Vector2) -> void:
	var id: String = d["id"]
	_bajando[id] = true
	if not _bytes.has(id):
		_bytes[id] = await Datos.bytes(d["archivo"], str(d.get("v", "")))
	var estado := jugador.get_world_3d().direct_space_state
	var h := _suelo_libre(estado, lugar)
	if h.is_empty():
		for r in range(1, 16):                # dentro de un edificio: el suelo libre más cercano, en espiral
			for k in 16:
				var a := TAU * k / 16.0
				h = _suelo_libre(estado, lugar + Vector2(cos(a), sin(a)) * r)
				if not h.is_empty():
					break
			if not h.is_empty():
				push_warning("personaje %s: su lugar (%.1f, %.1f) cae en un edificio; se usa (%.1f, %.1f)" % [id, lugar.x, lugar.y, h["position"].x, h["position"].z])
				break
	_bajando.erase(id)
	if h.is_empty() or _personajes.has(id):
		return
	var p := Personaje.new()
	add_child(p)
	if not p.armar(d, _bytes[id]):
		p.queue_free()
		_bytes.erase(id)
		return
	p.colocar(h["position"])
	_personajes[id] = p
	var guia_de := func(dd: Dictionary) -> String: return str(dd.get("acompana", dd.get("movimiento", {}).get("sigue_a", "")))
	if _personajes.has(guia_de.call(d)):
		p.guia = _personajes[guia_de.call(d)]
	for otro: Personaje in _personajes.values():       # el guía apareció después que su acompañante
		if guia_de.call(otro.datos) == id:
			otro.guia = p
	if d.has("movimiento") and p.guia == null:
		p.ronda = await _ronda(h["position"], float(d["movimiento"].get("radio", 8.0)))
	if not d.has("acompana"):
		carta.voz.precargar((d.get("guion", []) as Array).slice(0, 2))   # lo primero que dirá, ya en camino

## La ronda de un personaje: su lugar y hasta 5 puntos de suelo libre a menos de 'radio', a la vista desde su lugar
## (sin muros en el medio), fuera de la calzada (a más de 2,8 m de los carriles del tráfico) y sin cruzarla.
func _ronda(base: Vector3, radio: float) -> Array[Vector3]:
	var r: Array[Vector3] = [base]
	var espera := 0.0
	while trafico != null and trafico.red == null and espera < 15.0:      # los carriles aún bajan
		await get_tree().create_timer(0.5).timeout
		espera += 0.5
	if _carriles.is_empty() and trafico != null and trafico.red != null:
		for t in trafico.red.tramos:
			for q in t.pts:
				var k := Vector2i(floori(q.x / 8.0), floori(q.z / 8.0))
				if not _carriles.has(k):
					_carriles[k] = PackedVector2Array()
				_carriles[k].append(Vector2(q.x, q.z))
	if not is_inside_tree():
		return r
	var estado := jugador.get_world_3d().direct_space_state
	var semilla := RandomNumberGenerator.new()
	semilla.seed = hash(base.snapped(Vector3.ONE))
	for intento in 40:
		if r.size() >= 6:
			break
		var a := semilla.randf() * TAU
		var dist := semilla.randf_range(radio * 0.35, radio)
		var q2 := Vector2(base.x, base.z) + Vector2(sin(a), cos(a)) * dist
		var h := _suelo_libre(estado, q2)
		if h.is_empty():
			continue
		var pie: Vector3 = h["position"]
		if absf(pie.y - base.y) > 1.5:
			continue
		var visto := true
		for alto in [0.5, 1.3]:
			if not estado.intersect_ray(PhysicsRayQueryParameters3D.create(base + Vector3.UP * alto, pie + Vector3.UP * alto, 2)).is_empty():
				visto = false
		if not visto:
			continue
		var en_calle := false
		for k in range(1, int(dist) + 1):
			if _en_calzada(Vector2(base.x, base.z).lerp(q2, float(k) / maxf(1.0, dist))):
				en_calle = true
				break
		if not en_calle:
			r.append(pie)
	return r

func _en_calzada(p: Vector2) -> bool:
	var c := Vector2i(floori(p.x / 8.0), floori(p.y / 8.0))
	for i in range(-1, 2):
		for j in range(-1, 2):
			for q in _carriles.get(c + Vector2i(i, j), PackedVector2Array()):
				if q.distance_squared_to(p) < 2.8 * 2.8:
					return true
	return false

# ------------------------------------------------------------------------------------------------- aviso
func _elegir_candidato(yo: Vector3) -> void:
	var ojos := jugador.camara.global_position
	var mirada := -jugador.global_transform.basis.z
	var mejor: Personaje = null
	var mejor_d := INF
	for p: Personaje in _personajes.values():
		var hablante := not p.datos.has("acompana")
		var v := p.global_position - yo
		v.y = 0.0
		var d := v.length()
		p.caminante(yo)
		p.mirar(ojos if d < RADIO_ATENTO and hablante else null)
		if not hablante or _espera.has(p.id):
			continue
		var limite := RADIO_AVISO_SALIR if p == _candidato else RADIO_AVISO
		if d < limite and d < mejor_d and (d < 1.2 or mirada.angle_to(v.normalized()) < ANGULO_AVISO):
			mejor = p
			mejor_d = d
	if mejor != _candidato:
		_candidato = mejor
		if mejor != null:                    # el aviso aparece: se pide todo lo que contará al empezar
			carta.voz.precargar(_apertura(mejor))
		var visto := _libreta().has(mejor.id) if mejor != null else false
		carta.avisar(mejor.datos["nombre"] if visto else "", mejor != null)

func _unhandled_input(ev: InputEvent) -> void:
	if activo or not (ev is InputEventKey) or not ev.pressed or ev.echo:
		return
	if ev.physical_keycode == KEY_I and _candidato != null:
		get_viewport().set_input_as_handled()
		_interactuar()

func _interactuar() -> void:
	if not activo and _candidato != null and jugador.activo:
		_encuentro(_candidato)

# ------------------------------------------------------------------------------------------------- encuentro
func _libreta() -> Dictionary:
	var l = Guardado.leer(CLAVE, {})
	return l if l is Dictionary else {}

func _encuentro(p: Personaje) -> void:
	activo = true
	_candidato = null
	carta.avisar("", false)
	jugador.activo = false
	jugador.velocity = Vector3.ZERO
	jugador.entrada = Vector2.ZERO
	if interfaz != null:
		interfaz.hud_visible(false)
	if puente != null:
		puente.emitir({"tipo": "encuentro", "abierto": true, "personaje": p.id})
	p.empezar_encuentro(jugador.global_position)
	await _ir_a_toma(p)
	p.mirar(_camara.global_position)
	carta.abrir()
	var guion: Array = p.datos.get("guion", [])
	var de := func(seccion): return guion.filter(func(g): return g["seccion"] == seccion)
	var libreta := _libreta()
	var visto: Dictionary = libreta.get(p.id, {})
	var seguir := true
	if visto.get("historia", false) and not de.call("regreso").is_empty():
		seguir = await _contar(p, de.call("regreso"))
	else:
		seguir = await _contar(p, de.call("presentacion") + de.call("historia") + de.call("mecanica"))
		visto["historia"] = true
	while seguir:
		var opciones := []
		var acciones := []
		if not de.call("edificio").is_empty():
			opciones.append("Cuénteme de este edificio" if not visto.get("edificio", false) else "Otra vez lo del edificio")
			acciones.append("edificio")
		if visto.get("historia", false) and not de.call("historia").is_empty():
			opciones.append("Cuénteme su historia")
			acciones.append("historia")
		opciones.append("Despedirse")
		acciones.append("fin")
		carta.menu(opciones)
		for a in acciones:                   # el comienzo de cada opción, por si la elige
			carta.voz.precargar(de.call(a).slice(0, 2) if a != "fin" else [])
		var i: int = await _respuesta
		var accion: String = acciones[i] if i >= 0 and i < acciones.size() else "fin"
		match accion:
			"edificio":
				seguir = await _contar(p, de.call("edificio"))
				visto["edificio"] = true
			"historia":
				seguir = await _contar(p, de.call("historia") + de.call("mecanica"))
			_:
				seguir = false
	libreta[p.id] = visto
	Guardado.escribir(CLAVE, libreta)
	await carta.cerrar()
	p.terminar_encuentro()
	p.mirar(null)
	await _volver()
	_espera[p.id] = ESPERA_VOLVER
	if interfaz != null:
		interfaz.hud_visible(true)
	if puente != null:
		puente.emitir({"tipo": "encuentro", "abierto": false, "personaje": p.id})
	jugador.activo = true
	activo = false

## Las frases con las que empieza el encuentro (regreso si ya se contó la historia).
func _apertura(p: Personaje) -> Array:
	var guion: Array = p.datos.get("guion", [])
	var visto: Dictionary = _libreta().get(p.id, {})
	var regreso := guion.filter(func(g): return g["seccion"] == "regreso")
	if visto.get("historia", false) and not regreso.is_empty():
		return regreso
	return guion.filter(func(g): return g["seccion"] in ["presentacion", "historia", "mecanica"])

## Recorre frases; false si el jugador se despidió en el medio (Esc).
func _contar(p: Personaje, pasos: Array) -> bool:
	for i in pasos.size():
		var paso: Dictionary = pasos[i]
		carta.voz.precargar(pasos.slice(i + 1, i + 3))    # las dos siguientes se piden mientras suena esta
		var cronista: bool = paso.get("quien", "personaje") == "cronista"
		var quien := {"nombre": "El cronista", "retrato": null} if cronista else \
			{"nombre": p.datos["nombre"], "retrato": _retrato(p)}
		if not cronista:
			p.gesto(paso.get("gesto", ""))
		carta.decir(quien, paso["texto"], paso)
		var r: int = await _respuesta
		if r < 0:
			return false
	return true

func _retrato(p: Personaje) -> Texture2D:
	var archivo: String = p.datos.get("retrato", "")
	if archivo == "":
		return null
	if not _retratos.has(archivo):
		_retratos[archivo] = load("res://personajes/retratos/" + archivo)
	return _retratos[archivo]

# ------------------------------------------------------------------------------------------------- cámara
## Toma de tres cuartos: cámara a la altura de los ojos, a ~2,4 m, con el personaje en el tercio derecho y la mitad
## de arriba libre del papel. Si un muro tapa la toma, prueba del otro lado y más cerca.
func _toma(p: Personaje) -> Transform3D:
	var base := p.global_position
	var u := jugador.global_position - base
	u.y = 0.0
	u = u.normalized() if u.length() > 0.2 else Vector3(sin(p.rotation.y), 0, cos(p.rotation.y))
	var cfg: Dictionary = p.datos.get("camara", {})
	var lado: float = float(cfg.get("lado", 1))
	var dist: float = float(cfg.get("distancia", 2.4))
	var cara := base + Vector3.UP * 1.5
	var estado := jugador.get_world_3d().direct_space_state
	var pos := base + u * dist + Vector3.UP * 1.5
	for intento in [[lado, 1.0], [-lado, 1.0], [lado, 0.7], [-lado, 0.7], [0.0, 0.6]]:
		var dir: Vector3 = u.rotated(Vector3.UP, deg_to_rad(32.0) * float(intento[0]))
		var cand: Vector3 = base + dir * dist * float(intento[1]) + Vector3.UP * 1.5
		var q := PhysicsRayQueryParameters3D.create(cara, cand + dir * 0.4, 2)
		if estado.intersect_ray(q).is_empty():
			pos = cand
			break
	var f := (base + Vector3.UP * 1.15 - pos)
	f.y = 0.0
	var derecha := f.normalized().cross(Vector3.UP)
	var objetivo := base + Vector3.UP * 1.12 - derecha * 0.42      # el personaje queda a la derecha del cuadro
	return Transform3D(Basis.looking_at(objetivo - pos, Vector3.UP), pos)

func _ir_a_toma(p: Personaje) -> void:
	_camara = Camera3D.new()
	_camara.near = 0.05
	_camara.far = jugador.camara.far
	add_child(_camara)
	_camara.global_transform = jugador.camara.global_transform
	_camara.fov = jugador.camara.fov
	_camara.make_current()
	var tw := create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(_camara, "global_transform", _toma(p), 0.85)
	tw.tween_property(_camara, "fov", FOV_TOMA, 0.85)
	await tw.finished

func _volver() -> void:
	var tw := create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(_camara, "global_transform", jugador.camara.global_transform, 0.6)
	tw.tween_property(_camara, "fov", jugador.camara.fov, 0.6)
	await tw.finished
	jugador.camara.make_current()
	_camara.queue_free()
	_camara = null
