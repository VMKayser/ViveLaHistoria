class_name Trafico
extends Node3D
## Tráfico con física real: buses (VehicleBody3D, scripts/trafico/vehiculo.gd) manejados por conductores automáticos
## sobre la red de carriles (datos/red.json). Este nodo carga la red y los kits, reparte y hace reaparecer los vehículos,
## concede el paso en los cruces y decide qué vehículos usan la física completa:
##  - cerca del caminante (< RADIO_FISICA, con la colisión de la ciudad ya armada debajo): física completa;
##  - lejos: modo lejano, el mismo conductor avanzando por distancia sobre el carril (sin costo de física).
## Cantidad: la del nivel de calidad (Calidad.NIVELES) o ?trafico=N (0 = sin tráfico).

## Física completa hasta aquí (en la web, un solo hilo de WebAssembly, menos: más allá no se distingue a simple vista)
var radio_fisica := 90.0 if OS.has_feature("web") else 135.0
var radio_lejano := radio_fisica + 25.0   # histéresis: vuelve a modo lejano recién aquí
## Tope de vehículos con física completa a la vez (los más cercanos): con mucho tránsito en la plaza casi toda la flota
## queda dentro del radio de física, y en la web la física corre en un solo hilo. El resto avanza sobre el carril.
var max_fisicos := 12 if OS.has_feature("web") or OS.has_feature("mobile") else 20
const ESPERA_MAXIMA_CRUCE := 9.0      # s: si alguien espera más (atasco circular), pasa igual
const DIST_REAPARECER := 70.0         # nunca aparece a menos de esto del caminante ni a la vista
const PASO_LEJANO := 3                # los lejanos piensan uno de cada tantos pasos de física
## Burbuja de tráfico (como en los juegos de mundo abierto): el que se aleja más que esto del caminante reaparece cerca,
## fuera de la vista. Así toda la flota circula donde se la puede ver.
const RADIO_BURBUJA := 260.0
const DIST_RODAR := 200.0             # más lejos, los lejanos solo se mueven cuando piensan

var ciudad: Ciudad
var jugador: Jugador
var red: RedVial
var kits: Array[KitVehiculo] = []
var _kit_por_id := {}
var _flota: Array = []                 # [{tipo, peso, remolque?}] de datos/vehiculos.json
var _caballo := {}                     # clips y pelajes del caballo de las carrozas
## Plaza 25 de Mayo: donde se concentra el tránsito (datos/vehiculos.json → plaza, de web/scripts/vehiculos_trafico.json)
var plaza_centro := Vector2(INF, INF)
var plaza_radio := 0.0
var plaza_atraccion := 1.0
var _plaza_alcance := 0.0
var _plaza_parte := 0.0
var _carriles_plaza: Array[int] = []
var carriles_plaza := {}            # el mismo conjunto, para consultar rápido (vehiculo.gd: seguir dando vueltas)
var vehiculos: Array[Vehiculo] = []
var listo := false
var _cantidad := 12
var _forzada := -1
var _colas := []                       # por cruce: {titulares: [Vehiculo], espera: [Vehiculo]}
var _rng := RandomNumberGenerator.new()
var _tic := 0
var _cuerpos: Array = []               # por paso: [cola, frente, vehículo] de cada vehículo activo

func _ready() -> void:
	_rng.seed = 20261125
	var p = Puente.parametro("trafico")
	if p != null and str(p).is_valid_int():
		_forzada = int(p)
	if not Datos.en_web:
		arrancar()

var _arrancado := false
## En la web los vehículos (~5 MB) se descargan recién al aparecer a pie (principal.gd): antes competían con las teselas
## y la pantalla de carga duraba más. En el escritorio y el APK vienen en el paquete y se cargan enseguida.
func arrancar() -> void:
	if _arrancado:
		return
	_arrancado = true
	_cargar()

func _bajar(id: String, t: Dictionary, bins: Dictionary, pendientes: Array) -> void:
	bins[id] = await Datos.bytes(t["archivo"], str(t.get("v", "")))
	pendientes[0] -= 1

func _cargar() -> void:
	var datos_red = await Datos.json("red.json")
	var datos_veh = await Datos.json("vehiculos.json")
	if not (datos_red is Dictionary and datos_veh is Dictionary):
		push_warning("tráfico: faltan red.json o vehiculos.json")
		return
	red = RedVial.new(datos_red)
	for i in red.cruces:
		_colas.append({"titulares": [], "espera": []})
	var tipos: Dictionary = datos_veh["tipos"]
	# todas las descargas a la vez (Datos limita las simultáneas); se arman en orden
	var bins := {}
	var pendientes := [tipos.size()]
	for id in tipos:
		_bajar(id, tipos[id], bins, pendientes)
	while pendientes[0] > 0:
		await get_tree().process_frame
	for id in tipos:
		var t: Dictionary = tipos[id]
		var bin: PackedByteArray = bins[id]
		if bin.size() > 8:
			var k := KitVehiculo.new(id, t, bin)
			kits.append(k)
			_kit_por_id[id] = k
	if kits.is_empty():
		return
	_caballo = datos_veh.get("caballo", {})
	_preparar_plaza(datos_veh.get("plaza"))
	for f in datos_veh.get("flota", []):
		if _kit_por_id.has(f["tipo"]) and (not f.has("remolque") or _kit_por_id.has(f["remolque"])):
			_flota.append(f)
	# pruebas: SUCRE_TRAFICO_TIPO="carroza_azul,turismo_abierto" deja solo esos tipos en la calle
	if OS.has_environment("SUCRE_TRAFICO_TIPO"):
		var solo := OS.get_environment("SUCRE_TRAFICO_TIPO").split(",")
		_flota = _flota.filter(func(f): return f["tipo"] in solo)
	if _flota.is_empty():
		for k in kits:
			_flota.append({"tipo": k.id, "peso": 1.0})
	listo = true
	_ajustar_flota()

func _exit_tree() -> void:
	# las mallas de los kits se liberan antes que el servidor de dibujo (si no, Godot se queja al cerrar)
	for v in vehiculos:
		v.free()
	vehiculos.clear()
	kits.clear()

func fijar_cantidad(n: int) -> void:
	_cantidad = n
	if listo:
		_ajustar_flota()

func _ajustar_flota() -> void:
	var n := _forzada if _forzada >= 0 else _cantidad
	while vehiculos.size() > n:
		var v: Vehiculo = vehiculos.pop_back()
		soltar_cruce(v)
		v.queue_free()
	while vehiculos.size() < n:
		var v := Vehiculo.new()
		v.name = "Vehiculo%d" % vehiculos.size()
		v.trafico = self
		v.red = red
		var f: Dictionary = _flota[_elegir(vehiculos.size())]
		var kit: KitVehiculo = _kit_por_id[f["tipo"]]
		v.armar(kit, _rng.randi() % kit.materiales.size(), _caballo)
		if f.has("remolque"):
			var kr: KitVehiculo = _kit_por_id[f["remolque"]]
			v.enganchar(kr, _rng.randi() % kr.materiales.size())
		v.temple = _rng.randf_range(0.85, 1.1)
		add_child(v)
		vehiculos.append(v)
		_repartir(v)

## Qué tipo sale en el puesto n de la flota: reparto proporcional al peso e intercalado (round robin ponderado suave),
## así con pocos vehículos (celular) también salen carrozas y clásicos, y nunca dos iguales seguidos si hay variedad.
func _elegir(n: int) -> int:
	var total := 0.0
	for f in _flota:
		total += float(f["peso"])
	var actual := PackedFloat64Array()
	actual.resize(_flota.size())
	var elegido := 0
	for _paso in n + 1:
		elegido = 0
		for i in _flota.size():
			actual[i] += float(_flota[i]["peso"])
			if actual[i] > actual[elegido]:
				elegido = i
		actual[elegido] -= total
	return elegido

func _preparar_plaza(p) -> void:
	if not (p is Dictionary) or not p.has("centro"):
		return
	plaza_centro = Vector2(p["centro"][0], p["centro"][1])
	plaza_radio = float(p.get("radio", 170.0))
	plaza_atraccion = float(p.get("atraccion", 1.0))
	_plaza_alcance = float(p.get("alcance", 500.0))
	_plaza_parte = float(p.get("parte", 0.0))
	for i in red.carriles_zona:
		for q in red.tramos[i].pts:
			if Vector2(q.x - plaza_centro.x, q.z - plaza_centro.y).length() < plaza_radio:
				_carriles_plaza.append(i)
				carriles_plaza[i] = true
				break

func _lejos_de_plaza(v: Vehiculo, foco: Vector3) -> bool:
	if Vector2(foco.x - plaza_centro.x, foco.z - plaza_centro.y).length() > _plaza_alcance:
		return false
	var p := v.global_position
	return Vector2(p.x - plaza_centro.x, p.z - plaza_centro.y).length() > plaza_radio * 2.0 and not _a_la_vista(p, DIST_REAPARECER)

## Carriles donde (re)aparecer: cerca de la plaza una parte de las veces si el caminante anda por ahí; si no, toda la zona.
func _carriles_para(foco: Vector3) -> Array[int]:
	if not _carriles_plaza.is_empty() and Vector2(foco.x - plaza_centro.x, foco.z - plaza_centro.y).length() < _plaza_alcance \
			and _rng.randf() < _plaza_parte:
		return _carriles_plaza
	return red.carriles_zona

## Al empezar: en cualquier carril (con preferencia por la plaza, como al reaparecer), separado de los demás.
func _repartir(v: Vehiculo) -> void:
	var foco := jugador.global_position if jugador.is_inside_tree() else Vector3(plaza_centro.x, 0.0, plaza_centro.y)
	var carriles := _carriles_para(foco)
	var total := 0.0
	for i in carriles:
		total += red.tramos[i].largo
	for _intento in 40:
		var r := _rng.randf() * total
		var k := 0
		while k < carriles.size() - 1 and r > red.tramos[carriles[k]].largo:
			r -= red.tramos[carriles[k]].largo
			k += 1
		var t := red.tramos[carriles[k]]
		var d := clampf(r, 2.0, t.largo - 1.0)
		if _libre(RedVial.punto(t, d), 18.0, v):
			v.de_plaza = carriles == _carriles_plaza
			v.colocar(t.id, d)
			return
	v.activo = false
	v.visible = false

func _libre(p: Vector3, radio: float, yo: Vehiculo) -> bool:
	for o in vehiculos:
		if o != yo and o.activo and o.global_position.distance_squared_to(p) < radio * radio:
			return false
	return true

func _camara() -> Camera3D:
	return get_viewport().get_camera_3d()

func _a_la_vista(p: Vector3, margen: float) -> bool:
	var c := _camara()
	if c == null:
		return false
	if c.global_position.distance_to(p) < margen:
		return true
	return c.is_position_in_frustum(p) and c.global_position.distance_to(p) < 900.0

## Vuelve a entrar en un carril dentro de la burbuja (entre DIST_REAPARECER y RADIO_BURBUJA del caminante), fuera de la
## vista y lejos de los demás.
func _reaparecer(v: Vehiculo, foco: Vector3) -> void:
	soltar_cruce(v)
	v.activo = false
	v.visible = false
	v.fijar_lejano(true)
	var carriles := _carriles_para(foco)
	for _intento in 16:
		var t := red.tramos[carriles[_rng.randi() % carriles.size()]]
		var d := _rng.randf_range(2.0, maxf(2.5, t.largo - 2.0))
		var p := RedVial.punto(t, d)
		var dist := Vector2(p.x - foco.x, p.z - foco.z).length()
		if dist > RADIO_BURBUJA * 0.95 or _a_la_vista(p, DIST_REAPARECER) or not _libre(p, 18.0, v):
			continue
		v.de_plaza = carriles == _carriles_plaza
		v.colocar(t.id, d)
		return

var costo_ms := 0.0          # tiempo del conductor de toda la flota en el último paso (medición)

func _physics_process(dt: float) -> void:
	if not listo:
		return
	var t0 := Time.get_ticks_usec()
	var foco := jugador.global_position if jugador.is_inside_tree() else Vector3.ZERO
	var c := _camara()
	if c:
		foco = c.global_position
	_tic += 1
	_preparar_obstaculos()
	# cuántos van con física y cuál es el más lejano (para cederle el lugar a uno más cercano)
	var fisicos := 0
	var mas_lejano: Vehiculo = null
	for o in vehiculos:
		if o.activo and not o.lejano:
			fisicos += 1
			if mas_lejano == null or o.distancia_foco > mas_lejano.distancia_foco:
				mas_lejano = o
	var reaparecio := false
	for i in vehiculos.size():
		var v := vehiculos[i]
		if not v.activo:
			if not reaparecio:          # uno por paso: buscar dónde aparecer cuesta
				_reaparecer(v, foco)
				reaparecio = true
			continue
		# los lejanos piensan cada PASO_LEJANO pasos (repartidos); entre medio solo ruedan por el carril (los muy lejanos,
		# ni eso: se mueven cuando piensan)
		v.dt_pendiente += dt
		# el tránsito de la plaza vuelve a ella: si se aleja más del doble del radio, fuera de la vista, reaparece en el anillo
		if v.de_plaza and (i + _tic) % PASO_LEJANO == 0 and _lejos_de_plaza(v, foco):
			_retirar(v)
			continue
		if v.lejano and (i + _tic) % PASO_LEJANO != 0:
			if v.distancia_foco < DIST_RODAR:
				if not v.rodar_lejano(v.dt_pendiente):
					_retirar(v)
				v.dt_pendiente = 0.0
			continue
		var dtv := v.dt_pendiente
		v.dt_pendiente = 0.0
		# física completa cerca, con el suelo armado; lejano si se aleja o si la ciudad aún no tiene colisión ahí
		var d := v.global_position.distance_to(foco)
		v.distancia_foco = d
		if d > RADIO_BURBUJA and not _a_la_vista(v.global_position, 0.0):
			_retirar(v)
			continue
		var con_suelo := ciudad.suelo_listo(v.global_position.x, v.global_position.z)
		if v.lejano and d < radio_fisica and con_suelo:
			if fisicos >= max_fisicos and mas_lejano != null and mas_lejano.distancia_foco > d + 15.0:
				mas_lejano.fijar_lejano(true)     # el más lejano le cede la física
				fisicos -= 1
				mas_lejano = null
			if fisicos < max_fisicos:
				v.fijar_lejano(false)
				fisicos += 1
		elif not v.lejano and (d > radio_lejano or not con_suelo or v.sin_suelo > 0.6):
			v.fijar_lejano(true)
			fisicos -= 1
		if not v.conducir(dtv):
			_retirar(v)
		elif v.quieto > 25.0 and not _a_la_vista(v.global_position, 60.0):
			_retirar(v)   # atascado mucho tiempo: se lo reubica (nunca queda trabado para siempre)
	costo_ms = (Time.get_ticks_usec() - t0) / 1000.0
	if OS.has_environment("SUCRE_TRAFICO_REGISTRO"):
		_registrar(dt, foco)
	if OS.has_environment("SUCRE_TRAFICO_MIRAR"):
		_mirar_vehiculo()

## Pruebas (SUCRE_TRAFICO_MIRAR="lado,alto"): la cámara sigue al vehículo con física más cercano, de costado y a la altura
## de los ojos, para revisar ruedas, suspensión y apoyo en la calle.
var _camara_prueba: Camera3D
func _mirar_vehiculo() -> void:
	if _camara_prueba == null:
		_camara_prueba = Camera3D.new()
		_camara_prueba.fov = jugador.camara.fov
		add_child(_camara_prueba)
	var c := _camara_prueba
	var mejor: Vehiculo = null
	for v in vehiculos:
		if v.activo and not v.lejano and (mejor == null or v.global_position.distance_to(jugador.global_position) < mejor.global_position.distance_to(jugador.global_position)):
			mejor = v
	if mejor == null:
		return
	var k := OS.get_environment("SUCRE_TRAFICO_MIRAR").split(",")
	var lado := float(k[0]) if k.size() > 0 else 9.0
	var alto := float(k[1]) if k.size() > 1 else 1.6
	c.make_current()
	var objetivo := mejor.global_position + Vector3(0, 1.2, 0)
	var desde := mejor.global_position + mejor.global_basis.x * lado + mejor.global_basis.z * (lado * 0.6) + Vector3(0, alto, 0)
	c.global_transform = Transform3D(Basis.looking_at(objetivo - desde, Vector3.UP), desde)

var _t_registro := 0.0

## Registro para pruebas (variable SUCRE_TRAFICO_REGISTRO): estado de la flota cada 2 s.
func _registrar(dt: float, foco: Vector3) -> void:
	_t_registro += dt
	if _t_registro < 2.0:
		return
	_t_registro = 0.0
	var fisicos := 0
	var linea := ""
	for v in vehiculos:
		if not v.activo:
			continue
		if not v.lejano:
			fisicos += 1
			var p := v.global_position
			v.contact_monitor = true
			v.max_contacts_reported = 4
			var toques := v.get_colliding_bodies().map(func(b): return "%s(capa %d)" % [b.name, b.collision_layer])
			linea += " [%s d=%.0f v=%.1f s=%.1f t=%d %s p=%.1f,%.1f,%.1f dir=%.2f desvio=%.2f toca=%s]" % [v.name, p.distance_to(foco), v.v, v.s, v.ruta[0], v.motivo,
				p.x, p.y, p.z, v.steering, v.desvio, toques]
			v.desvio = 0.0
	# resumen por tipo: activos, cuántos andan a menos de 95 m de la plaza y su velocidad (media y máxima, m/s, de los que
	# no están detenidos)
	var tipos := {}
	for v in vehiculos:
		if v.activo:
			var k: String = v.kit.id
			var e: Array = tipos.get(k, [0, 0, 0.0, 0, 0.0])
			e[0] += 1
			if Vector2(v.global_position.x - plaza_centro.x, v.global_position.z - plaza_centro.y).length() < 95.0:
				e[1] += 1
			if v.v > 0.5:
				e[2] += v.v
				e[3] += 1
				e[4] = maxf(e[4], v.v)
			tipos[k] = e
	var resumen := []
	for k in tipos:
		var e: Array = tipos[k]
		resumen.append("%s %d/%d v=%.1f máx %.1f" % [k, e[0], e[1], e[2] / maxf(e[3], 1), e[4]])
	print("trafico: %d activos, %d con física, %.2f ms | por tipo (activos/en la plaza, velocidad media y máxima en marcha): %s" % [vehiculos.filter(func(x): return x.activo).size(), fisicos, costo_ms, ", ".join(resumen)])
	if OS.get_environment("SUCRE_TRAFICO_REGISTRO") == "2":
		print("  ", linea)

func _retirar(v: Vehiculo) -> void:
	soltar_cruce(v)
	if _a_la_vista(v.global_position, 40.0) and v.activo and v.ruta.size() > 0 and not v.lejano:
		# salió del carril a la vista (choque): queda frenado como cuerpo físico hasta que se lo pierda de vista
		v.detener()
		return
	v.activo = false

# ------------------------------------------------------------------------------------------------------------ obstáculos
## Lo más cercano en el trazado del vehículo: otro vehículo (con su velocidad) o el caminante. [hueco, velocidad].
func _preparar_obstaculos() -> void:
	_cuerpos.clear()
	for o in vehiculos:
		if o.activo:
			var z := o.global_basis.z
			_cuerpos.append([o.global_position + z * o.kit.cola, o.global_position + z * o.kit.frente, o])
			if o.remolque:
				var ext: Array = o.remolque.extremos()
				_cuerpos.append([ext[0], ext[1], o])

func obstaculo(v: Vehiculo) -> Array:
	var tr := v.trazado()
	if tr.size() < 2:
		return [INF, 0.0]
	var yo := v.global_position
	var adelante := v.global_basis.z
	var alcance := Vehiculo.ALCANCE_OBSTACULOS + 8.0
	# solo lo que está por delante y a su alcance
	var cercanos: Array = []
	for c in _cuerpos:
		var o: Vehiculo = c[2]
		if o == v:
			continue
		var rel: Vector3 = (c[0] + c[1]) * 0.5 - yo   # centro del cuerpo (o del remolque)
		if rel.length_squared() > alcance * alcance or rel.dot(adelante) < -8.0:
			continue
		# ancho de los dos cuerpos; uno que viene de frente por el otro carril (paralelo, a ~3 m) no cuenta
		var umbral := 2.5 if o.global_basis.z.dot(adelante) > -0.5 else 1.4
		cercanos.append([c[0], c[1], o, umbral * umbral])
	var peaton := jugador.global_position
	var hay_peaton := peaton.distance_squared_to(yo) < alcance * alcance
	if cercanos.is_empty() and not hay_peaton:
		return [INF, 0.0]
	var frente := v.kit.frente - float(v.kit.mov["eje_trasero"])
	var desfase := v.desfase_trazado()
	for i in range(1, tr.size()):
		var d := i * Vehiculo.MUESTRA - desfase
		if d < frente - 0.5:
			continue
		var p := tr[i]
		if hay_peaton and Vector2(p.x - peaton.x, p.z - peaton.z).length_squared() < 1.9 * 1.9 and absf(p.y - peaton.y) < 3.0:
			v.motivo_obst = "peaton"
			return [maxf(d - frente - 1.0, 0.0), 0.0]
		for c in cercanos:
			var q: Vector3 = Geometry3D.get_closest_point_to_segment(p, c[0], c[1])
			if Vector2(p.x - q.x, p.z - q.z).length_squared() < c[3] and absf(p.y - q.y) < 3.0:
				var o: Vehiculo = c[2]
				v.motivo_obst = o.name
				return [maxf(d - frente, 0.0), maxf(o.v, 0.0) * maxf(0.0, o.global_basis.z.dot(adelante))]
	return [INF, 0.0]

# ------------------------------------------------------------------------------------------------------------ cruces
## Uno a la vez por cruce (cola por orden de llegada); pueden pasar juntos los que vienen del mismo carril.
func pedir_cruce(v: Vehiculo, con: RedVial.Tramo, dt: float) -> bool:
	var cola: Dictionary = _colas[con.cruce]
	if v.cruce != con.cruce:
		soltar_cruce(v)
		v.cruce = con.cruce
		v.conector = con.id
		v.espera_cruce = 0.0
		cola["espera"].append(v)
	v.espera_cruce += dt
	var entrada := con.anteriores[0]
	var compatible := func(o: Vehiculo) -> bool:
		return o.conector >= 0 and red.tramos[o.conector].anteriores[0] == entrada
	var esperando: Array = cola["espera"]
	var pos := esperando.find(v)
	var puede := v.espera_cruce > ESPERA_MAXIMA_CRUCE
	if not puede:
		puede = true
		for o in cola["titulares"]:
			if not compatible.call(o):
				puede = false
				break
		if puede:
			for k in pos:
				if not compatible.call(esperando[k]):
					puede = false
					break
	if puede:
		esperando.erase(v)
		cola["titulares"].append(v)
		v.concedido = true
	return puede

func soltar_cruce(v: Vehiculo) -> void:
	if v.cruce >= 0 and v.cruce < _colas.size():
		_colas[v.cruce]["titulares"].erase(v)
		_colas[v.cruce]["espera"].erase(v)
	v.cruce = -1
	v.conector = -1
	v.concedido = false
	v.espera_cruce = 0.0
