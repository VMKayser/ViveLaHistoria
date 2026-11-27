class_name Ciudad
extends Node3D
## La ciudad en teselas de 100 m que se cargan y descartan según dónde esté el observador. Cada tesela tiene un archivo
## de "base" (muros, techos, suelo, vegetación) y otro de "detalle" (rejas, carpinterías, flores) que solo se carga de
## cerca. La colisión se arma aparte y solo cerca del caminante (y de los vehículos con física).
##
## Escritorio y APK: los archivos se leen del paquete y se arman en hilos. Web (sin hilos): se descargan a demanda
## (autoload Datos) y se arman en el hilo principal con un presupuesto de tiempo por cuadro, para que no haya tirones.

signal indice_listo
signal tesela_lista(clave: String)

const RADIO_CARGA := 420.0          # m: teselas de base alrededor del observador
const RADIO_COLISION := 170.0       # m: colisión (caminante y vehículos)
const MARGEN_DESCARGA := 90.0
const ARCHIVOS := {"b": "base", "d": "detalle", "h": "hojas"}

var radio_detalle := 420.0          # m: rejas, carpinterías y flores (según la calidad)
var radio_hojas := 170.0            # m: racimos de hojas de las copas (según la calidad; 0 = solo la copa maciza)
## web: tiempo máximo por cuadro para armar teselas. Mientras carga detrás de la pantalla de inicio (nadie ve el lienzo)
## se usa más: así la carga no espera cuadros que no se miran.
const PRESUPUESTO_MS := 7.0
const PRESUPUESTO_CARGA_MS := 30.0
var presupuesto_ms := PRESUPUESTO_CARGA_MS
var roles: Array = []
var grupos: Array = []
var clases: Array = []
var origenes: Array = []
var lado := 100.0
var version := ""                   # versión de los datos (ciudad.json): para la caché de los archivos sin versión propia
var modelos := {}                   # "agente/id" -> centro [x, y, z] (para el taller)
var listo := false
var cargadas_en_total := 0
var _teselas := {}                  # "tx,tz" -> entrada del índice
var _estado := {}                   # "tx,tz|b" / "|d" -> "pidiendo" | Node3D
var _colision := {}                 # "tx,tz" -> "armando" | StaticBody3D[]
var _mallas_choque := {}            # "tx,tz" -> {suelo, solido: [[pos, idx], …], origen} para armar la colisión de cerca
var _cola_armar := []               # web: [clave, tipo, bytes, origen]
var _foco := Vector3.ZERO
var _t_ultimo := 0.0
var _en_vuelo := 0
var _hilos := not OS.has_feature("web")
var _ocultos := {}                  # origen -> true (taller)
var _tareas := {}                   # escritorio/APK: id de tarea en curso del WorkerThreadPool -> true

func _ready() -> void:
	var d = await Datos.json("ciudad.json", str(Time.get_unix_time_from_system()) if Datos.en_web else "")
	if d == null:
		push_error("no hay datos de la ciudad (ciudad.json)")
		return
	if int(d.get("formato", 1)) != 2:
		push_error("datos de la ciudad con formato viejo: correr ciudad3d/herramientas/empaquetar.py")
		return
	roles = d["roles"]
	grupos = d["grupos"]
	clases = d["clases"]
	origenes = d["origenes"]
	# materiales creados en el hilo principal antes de que las teselas se armen en hilos
	for clase in clases:
		Estilo.material_ciudad(clase, roles)
	lado = d["lado"]
	version = str(d.get("version", ""))
	modelos = d.get("modelos", {})
	for e in d["teselas"]:
		_teselas["%d,%d" % [e["tx"], e["tz"]]] = e
	_cargar_fondo(d["fondo"])
	listo = true
	indice_listo.emit()

func _cargar_fondo(info: Dictionary) -> void:
	var b: PackedByteArray = await Datos.bytes(info["archivo"], info.get("v", ""))
	var sup := Tesela.leer(b, grupos, clases, origenes)
	if sup.is_empty():
		return
	var arm := Tesela.armar(sup, roles)
	var mi := MeshInstance3D.new()
	mi.name = "fondo_cerros"
	mi.mesh = arm["mallas"][0]["malla"]
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.extra_cull_margin = 16000.0
	var o: Array = info["origen"]
	mi.position = Vector3(o[0], o[1], o[2])
	add_child(mi)

func _tarea(id: int) -> void:
	_tareas[id] = true
	# las terminadas se olvidan (no hace falta esperarlas)
	for t in _tareas.keys():
		if WorkerThreadPool.is_task_completed(t):
			WorkerThreadPool.wait_for_task_completion(t)
			_tareas.erase(t)

## Al salir, las tareas en curso terminan antes de que se libere la ciudad (si no, arman mallas sobre un nodo ya liberado).
func _exit_tree() -> void:
	for t in _tareas:
		WorkerThreadPool.wait_for_task_completion(t)
	_tareas.clear()

func fijar_foco(p: Vector3) -> void:
	_foco = p

func _process(_dt: float) -> void:
	if not listo:
		return
	if not _hilos:
		_armar_pendientes()
	var t := Time.get_ticks_msec() / 1000.0
	if t - _t_ultimo < 0.2:
		return
	_t_ultimo = t
	_actualizar()

func _distancia(e: Dictionary) -> float:
	var c: Array = e["centro"]
	return Vector2(c[0] - _foco.x, c[2] - _foco.z).length() - float(e["radio"]) * 0.6

func _actualizar() -> void:
	var pedir := []
	for k in _teselas:
		var e: Dictionary = _teselas[k]
		var d := _distancia(e)
		if e.has("base"):
			_decidir(k, "b", d < RADIO_CARGA, d > RADIO_CARGA + MARGEN_DESCARGA, d, pedir)
		if e.has("detalle"):
			_decidir(k, "d", d < radio_detalle, d > radio_detalle + MARGEN_DESCARGA, d, pedir)
		if e.has("hojas"):
			_decidir(k, "h", d < radio_hojas, d > radio_hojas + 40.0, d + 60.0, pedir)
		# colisión: solo cerca y con la base ya armada
		if _mallas_choque.has(k) and not _colision.has(k) and d < RADIO_COLISION:
			_armar_colision(k)
		elif _colision.has(k) and _colision[k] is Array and d > RADIO_COLISION + MARGEN_DESCARGA:
			_quitar_colision(k)
	pedir.sort_custom(func(a, b): return a[0] < b[0])
	for p in pedir:
		if _en_vuelo >= 8:
			break
		_pedir(p[1], p[2])

func _decidir(k: String, tipo: String, quiere: bool, sobra: bool, dist: float, pedir: Array) -> void:
	var clave := k + "|" + tipo
	var est = _estado.get(clave)
	if est == null:
		if quiere:
			pedir.append([dist, k, tipo])
	elif sobra and est is Node3D:
		est.queue_free()
		_estado.erase(clave)
		if tipo == "b":
			_quitar_colision(k)
			_mallas_choque.erase(k)

func _pedir(k: String, tipo: String) -> void:
	var clave := k + "|" + tipo
	_estado[clave] = "pidiendo"
	_en_vuelo += 1
	var info: Dictionary = _teselas[k][ARCHIVOS[tipo]]
	var b: PackedByteArray = await Datos.bytes(info["archivo"], info.get("v", ""))
	if _hilos:
		_tarea(WorkerThreadPool.add_task(_trabajo.bind(k, tipo, b, info["origen"]), false, "tesela " + clave))
	else:
		_cola_armar.append([k, tipo, b, info["origen"]])

## Escritorio/APK, en un hilo: decodifica y arma las mallas.
func _trabajo(k: String, tipo: String, b: PackedByteArray, origen: Array) -> void:
	var arm := Tesela.armar(Tesela.leer(b, grupos, clases, origenes), roles)
	_terminar.call_deferred(k, tipo, origen, arm)

## Web: arma lo descargado sin pasarse del presupuesto del cuadro.
func _armar_pendientes() -> void:
	var t0 := Time.get_ticks_usec()
	while not _cola_armar.is_empty() and (Time.get_ticks_usec() - t0) < presupuesto_ms * 1000.0:
		var p: Array = _cola_armar.pop_front()
		_terminar(p[0], p[1], p[3], Tesela.armar(Tesela.leer(p[2], grupos, clases, origenes), roles))

func _terminar(k: String, tipo: String, origen: Array, arm: Dictionary) -> void:
	_en_vuelo -= 1
	var clave := k + "|" + tipo
	if not _estado.has(clave):
		return
	var nodo := Node3D.new()
	nodo.name = "t_" + clave.replace(",", "_").replace("|", "_")
	nodo.position = Vector3(origen[0], origen[1], origen[2])
	for m in arm["mallas"]:
		var mi := MeshInstance3D.new()
		mi.mesh = m["malla"]
		mi.set_meta("origen", m["origen"])
		mi.visible = not _ocultos.has(m["origen"])
		if m["grupo"] == "suelo":
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if tipo == "h":
			mi.extra_cull_margin = 1.5      # los racimos se abren en el shader hasta ~0,8 m alrededor de su centro
		nodo.add_child(mi)
	add_child(nodo)
	_estado[clave] = nodo
	cargadas_en_total += 1
	if tipo == "b":
		_mallas_choque[k] = {"suelo": arm["suelo"], "solido": arm["solido"], "origen": origen}
		if _distancia(_teselas[k]) < RADIO_COLISION:
			_armar_colision(k)
	tesela_lista.emit(k)

func _armar_colision(k: String) -> void:
	_colision[k] = "armando"
	var mc: Dictionary = _mallas_choque[k]
	if _hilos:
		_tarea(WorkerThreadPool.add_task(func():
			var formas := _formas(mc)
			_colocar_colision.call_deferred(k, formas, mc["origen"]), false, "colision " + k))
	else:
		_colocar_colision(k, _formas(mc), mc["origen"])

static func _formas(mc: Dictionary) -> Dictionary:
	var f := {}
	for g in ["suelo", "solido"]:
		var forma := Tesela.forma(mc[g])
		if forma != null:
			f[g] = forma
	return f

func _colocar_colision(k: String, formas: Dictionary, origen: Array) -> void:
	if not _colision.has(k) or not _mallas_choque.has(k):
		return
	var cuerpos := []
	for g in formas:
		var cuerpo := StaticBody3D.new()
		cuerpo.collision_layer = 1 if g == "suelo" else 2
		cuerpo.collision_mask = 0
		cuerpo.position = Vector3(origen[0], origen[1], origen[2])
		var cs := CollisionShape3D.new()
		cs.shape = formas[g]
		cuerpo.add_child(cs)
		add_child(cuerpo)
		cuerpos.append(cuerpo)
	_colision[k] = cuerpos

func _quitar_colision(k: String) -> void:
	if _colision.get(k) is Array:
		for c in _colision[k]:
			c.queue_free()
	_colision.erase(k)

## ¿Ya tiene colisión la tesela bajo (x, z)? Mientras no, el caminante espera para no caer al vacío.
func suelo_listo(x: float, z: float) -> bool:
	var k := "%d,%d" % [floori(x / lado), floori(z / lado)]
	return not _teselas.has(k) or _colision.get(k) is Array

## Fracción de teselas de base listas en torno a 'p' (para la barra de carga).
func progreso_alrededor(p: Vector3, radio: float) -> float:
	if not listo:
		return 0.0
	var total := 0
	var listas := 0
	for k in _teselas:
		var e: Dictionary = _teselas[k]
		if not e.has("base"):
			continue
		var c: Array = e["centro"]
		if Vector2(c[0] - p.x, c[2] - p.z).length() < radio:
			total += 1
			if _estado.get(k + "|b") is Node3D:
				listas += 1
	return 1.0 if total == 0 else float(listas) / float(total)

## Taller: muestra u oculta lo de un origen (claude, codex, lienzo, lienzo_volumen).
func mostrar_origen(origen: String, ver: bool) -> void:
	if ver:
		_ocultos.erase(origen)
	else:
		_ocultos[origen] = true
	for clave in _estado:
		var n = _estado[clave]
		if n is Node3D:
			for mi in n.get_children():
				if mi.has_meta("origen") and mi.get_meta("origen") == origen:
					mi.visible = ver
