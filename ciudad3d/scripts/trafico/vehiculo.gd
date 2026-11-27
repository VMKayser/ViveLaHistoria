class_name Vehiculo
extends VehicleBody3D
## Un vehículo con física real (VehicleBody3D de Godot: cuatro ruedas con suspensión y agarre, motor en el eje trasero,
## frenos en las cuatro, dirección en el eje delantero) y un CONDUCTOR que lo maneja como una persona:
##  1. Ruta: una cola de tramos de la red con ~80 m por delante; en cada cruce elige (más a menudo de frente).
##  2. Volante: persecución pura (pure pursuit) de un punto del carril a 6–16 m según la velocidad, con el límite de giro
##     y la rapidez del volante del vehículo. El bus no va sobre rieles: si se abre en una curva, corrige.
##  3. Velocidad: IDM (Intelligent Driver Model) contra el obstáculo más cercano en su trazado (el vehículo de adelante,
##     el peatón, la línea de un cruce ocupado) y frenando ANTES de las curvas. La aceleración pedida se convierte en
##     fuerza de motor o de freno en las ruedas; la velocidad real sale de la física (pendientes, peso, agarre).
##  4. Cruces: uno a la vez por nodo (Trafico.pedir_cruce).
## Lejos del caminante (sin colisión de la ciudad cargada) pasa a modo LEJANO: el cuerpo se congela y avanza por
## distancia sobre el carril con el mismo conductor; al acercarse vuelve a la física con su velocidad.

const S0 := 3.0              # distancia mínima al de adelante, detenido (m)
const T_SEGURIDAD := 1.4     # tiempo de seguridad (s)
const FRENADA_COMODA := 2.2  # m/s² (2026-11-26: con más velocidad, frenada de ciudad normal)
const LARGO_RUTA := 80.0     # m de ruta planificados por delante
const MUESTRA := 2.0         # paso del trazado para buscar obstáculos (m)
const ALCANCE_OBSTACULOS := 56.0
## Las esquinas del casco viejo son más cerradas que el giro del kit (0,48 rad, radio ~7 m): el conductor usa hasta 0,62.
const DIRECCION_MINIMA := 0.62
const ATASCO := 2.5          # s queriendo avanzar sin moverse → maniobra
const MANIOBRA := 1.6        # s de marcha atrás con el volante al revés

var trafico: Node
var red: RedVial
var kit: KitVehiculo
var variante := 0
var temple := 1.0            # carácter del conductor (velocidad deseada × temple)
var de_plaza := false        # apareció para el tránsito de la plaza (trafico.gd lo devuelve allí si se aleja)
var activo := false
var ruta: Array[int] = []
var s := 0.0                 # distancia del eje trasero sobre ruta[0]
var v := 0.0                 # velocidad (m/s) hacia adelante
var lejano := true
var dt_pendiente := 0.0      # tiempo acumulado desde que pensó o rodó por última vez
var distancia_foco := 0.0
var quieto := 0.0
var sin_suelo := 0.0
# cruce
var cruce := -1
var conector := -1
var concedido := false
var espera_cruce := 0.0

var motivo := ""             # por qué frena (registro de pruebas)
var desvio := 0.0            # mayor distancia del eje trasero a su carril desde el último registro (pruebas)
var motivo_obst := ""
var _ruedas: Array[VehicleWheel3D] = []
var _tornamesa: Node3D                 # eje delantero que gira entero (carrozas)
var _ruedas_tornamesa: Array[Node3D] = []
var _caballo: Caballo
var _correas: Array = []               # [malla, apoyo (marco de la tornamesa), hebilla del caballo, ancho]
var _riendas: Array = []               # [malla, puño del cochero (marco del vehículo), lado de la boca]
var remolque: Remolque                 # lo que arrastra (o null)
var v_tope := INF                      # velocidad máxima con remolque
var _direccion := 0.0
var _atasco := 0.0
var _a_lejano := 0.0
var _maniobra := 0.0
var _giro_maniobra := 0.0
var _batalla := 3.5          # distancia entre ejes
var _frente := 5.0           # del eje trasero al paragolpes delantero
var _trazado := PackedVector3Array()   # puntos de la ruta cada MUESTRA m desde el eje trasero (se rehace cada paso)
var _vlim_trazado := PackedFloat32Array()
var _trazado_tramo := -1
var _trazado_s := 0.0

func armar(k: KitVehiculo, var_color: int, caballo_datos := {}) -> void:
	kit = k
	variante = var_color
	var m := kit.mov
	var r := float(m["radio_rueda"])
	var rd := kit.radio_delantera if kit.radio_delantera > 0.0 else r
	var et := float(m["eje_trasero"])
	var ed := float(m["eje_delantero"])
	var sv := float(m["semivia"])
	_batalla = ed - et
	_frente = kit.frente - et
	mass = kit.masa
	gravity_scale = 9.8 / float(ProjectSettings.get_setting("physics/3d/default_gravity", 9.8))
	center_of_mass_mode = RigidBody3D.CENTER_OF_MASS_MODE_CUSTOM
	center_of_mass = Vector3(0.0, minf(0.9, kit.alto * 0.42), (et + ed) * 0.5)
	angular_damp = 0.4
	collision_layer = 4                  # vehículos
	collision_mask = 1 | 2 | 4 | 8       # suelo, sólidos, vehículos, caminante
	can_sleep = false
	var forma := CollisionShape3D.new()
	var caja := BoxShape3D.new()
	var piso := kit.piso
	caja.size = Vector3(kit.medio_ancho * 2.0 - 0.25, kit.alto - piso, kit.frente - kit.cola)
	forma.shape = caja
	forma.position = Vector3(0.0, piso + caja.size.y * 0.5, (kit.frente + kit.cola) * 0.5)
	add_child(forma)
	for nombre in ["cuerpo0", "vidrio0"]:
		if kit.tiene(nombre):
			add_child(kit.pieza(nombre, variante, 0))
	add_child(kit.pieza("cuerpo1", variante, 1))
	add_child(kit.pieza("cuerpo2", variante, 2))
	# eje delantero que gira entero (carrozas): lleva las ruedas delanteras, las varas y el caballo
	if not kit.tornamesa.is_empty():
		_tornamesa = Node3D.new()
		_tornamesa.name = "Tornamesa"
		_tornamesa.position = Vector3(0.0, float(kit.tornamesa["y"]), float(kit.tornamesa["x"]))
		add_child(_tornamesa)
		for nivel in [0, 1]:
			if kit.tiene("tornamesa%d" % nivel):
				_tornamesa.add_child(kit.pieza("tornamesa%d" % nivel, variante, nivel))
		if not kit.caballo.is_empty() and not caballo_datos.is_empty():
			_caballo = Caballo.new(caballo_datos, randi())
			_caballo.position = Vector3(0.0, float(kit.caballo["y"]), float(kit.caballo["x"]))
			_tornamesa.add_child(_caballo)
			_armar_correas()
	# ruedas: suspensión rígida, recorrido corto. Fuerzas de los resortes ∝ masa (así las calcula Godot).
	const REPOSO := 0.3
	const RIGIDEZ := 45.0
	var hundimiento := 9.8 / (4.0 * RIGIDEZ)
	for eje in [et, ed]:
		var delantera: bool = eje == ed
		var radio := rd if delantera else r
		var pieza := "ruedad" if delantera and kit.tiene("ruedad0") else "rueda"
		for lado in [1.0, -1.0]:
			var w := VehicleWheel3D.new()
			w.position = Vector3(lado * sv, radio + REPOSO - hundimiento, eje)
			w.wheel_radius = radio
			w.wheel_rest_length = REPOSO
			w.suspension_travel = REPOSO
			w.suspension_stiffness = RIGIDEZ
			w.suspension_max_force = mass * 9.8
			w.damping_compression = 3.0
			w.damping_relaxation = 3.6
			w.wheel_friction_slip = 3.2
			w.wheel_roll_influence = 0.05
			w.use_as_traction = not delantera
			w.use_as_steering = delantera
			# con tornamesa, las ruedas delanteras van con el eje (giran alrededor de su centro, no de su pivote)
			var padre: Node3D = w
			if delantera and _tornamesa:
				padre = Node3D.new()
				padre.position = Vector3(lado * sv, radio - _tornamesa.position.y, 0.0)
				_tornamesa.add_child(padre)
				_ruedas_tornamesa.append(padre)
			for nivel in [0, 1]:
				var mi := kit.pieza("%s%d" % [pieza, nivel], variante, nivel)
				if lado > 0.0:
					mi.rotation.y = PI   # las del lado izquierdo, con el cubo hacia afuera
				padre.add_child(mi)
			add_child(w)
			_ruedas.append(w)

## Correas del tiro: de los tirantes y las puntas de las varas a la pechera y la cincha del caballo (anclajes animados).
func _armar_correas() -> void:
	# cuero con el material pintado de los vehículos (un StandardMaterial3D era otro shader que compilar en la web): una caja
	# unitaria con el color en los vértices (lineal, como el resto)
	var oscuro := Color(0.17, 0.11, 0.09).srgb_to_linear()
	var cuero := Estilo.material_movil("vehiculo", oscuro, oscuro)
	var arr := BoxMesh.new().get_mesh_arrays()
	var colores := PackedColorArray()
	colores.resize((arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size())
	colores.fill(oscuro)
	arr[Mesh.ARRAY_COLOR] = colores
	var caja := ArrayMesh.new()
	caja.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	for lado in ["derecha", "izquierda"]:
		for par in [["tirante_" + lado, "tiro_caballo_" + lado, 0.03], ["vara_punta_" + lado, "cincha_caballo_" + lado, 0.021]]:
			if not kit.anclas.has(par[0]):
				continue
			var hebilla := _caballo.anclaje(par[1])
			if hebilla == null:
				continue
			var mi := MeshInstance3D.new()
			mi.mesh = caja
			mi.material_override = cuero
			mi.visibility_range_end = KitVehiculo.LOD[0]
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_tornamesa.add_child(mi)
			var apoyo := KitVehiculo.a_godot(kit.anclas[par[0]])
			_correas.append([mi, apoyo, hebilla, par[2]])
	# riendas: de los puños del cochero al bocado, una por lado
	if kit.caballo.has("boca") and not kit.riendas.is_empty():
		for lado in ["izquierda", "derecha"]:
			var mi := MeshInstance3D.new()
			mi.mesh = caja
			mi.material_override = cuero
			mi.visibility_range_end = KitVehiculo.LOD[0]
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(mi)
			_riendas.append([mi, KitVehiculo.a_godot(kit.riendas[lado]), -0.07 if lado == "izquierda" else 0.07])

## Lo que no hace la física: eje delantero de las carrozas, ruedas que van con él, caballo y correas.
func _physics_process(dt: float) -> void:
	if not activo or _tornamesa == null:
		return
	_tornamesa.rotation.y = _direccion
	for w in _ruedas_tornamesa:
		w.rotation.x += v * dt / maxf(0.1, w.position.y + _tornamesa.position.y)
	if _caballo:
		var cerca := distancia_foco < 120.0
		_caballo.animar(cerca)
		if cerca:
			_caballo.avanzar(v)
	if distancia_foco < KitVehiculo.LOD[0]:
		for c in _correas:
			_tender(c[0], c[1], _tornamesa.to_local((c[2] as Node3D).global_position), c[3], 0.009)
		for c in _riendas:
			_tender(c[0], c[1], to_local(_caballo.boca_global(kit.caballo["boca"], c[2])), 0.014, 0.006)

## Correa recta de 'a' a 'b' (en el marco del padre de la malla): una caja unitaria estirada.
static func _tender(mi: MeshInstance3D, a: Vector3, b: Vector3, ancho: float, grosor: float) -> void:
	var dir := b - a
	var largo := dir.length()
	if largo < 0.01:
		return
	var y := dir / largo
	var x := y.cross(Vector3.UP)
	x = Vector3.RIGHT if x.length_squared() < 1e-6 else x.normalized()
	var z := x.cross(y)
	mi.transform = Transform3D(Basis(x * ancho, y * largo, z * grosor), (a + b) * 0.5)

## Ojo del enganche trasero (para un remolque): en la cola, a la altura del ojo de su lanza.
func enganche_global() -> Vector3:
	var alto := 0.5
	if remolque:
		alto = float(remolque.kit.tornamesa.get("y", 0.5)) + float(remolque.kit.anclas.get("enganche_frontal", [0, 0, 0])[1])
	return global_transform * Vector3(0.0, alto, kit.cola - 0.1)

## Engancha un remolque (lo arrastra detrás; va más despacio).
func enganchar(k: KitVehiculo, var_color: int) -> void:
	remolque = Remolque.new()
	remolque.armar(k, var_color, self)
	add_child(remolque)
	v_tope = float(k.mov["velocidad_maxima"]) * 1.25

# ------------------------------------------------------------------------------------------------------------ ruta
func colocar(tramo: int, d: float) -> void:
	ruta = [tramo]
	s = d
	v = 0.0
	_direccion = 0.0
	_atasco = 0.0
	_maniobra = 0.0
	_trazado_tramo = -1
	dt_pendiente = 0.0
	activo = true
	quieto = 0.0
	sin_suelo = 0.0
	visible = true
	_extender_ruta()
	_poner_lejano(true)
	_pose_en_ruta()
	reset_physics_interpolation()
	if remolque:
		remolque.colocar()

func _largo(k: int) -> float:
	return red.tramos[ruta[k]].largo

func _extender_ruta() -> void:
	var adelante := -s
	for k in ruta.size():
		adelante += _largo(k)
	var vueltas := 0
	while adelante < LARGO_RUTA:
		vueltas += 1
		if vueltas > 40:
			push_warning("%s: ruta sin avance (tramo %d)" % [name, ruta[-1]])
			return
		var ult: RedVial.Tramo = red.tramos[ruta[-1]]
		if ult.siguientes.is_empty():
			return
		var sig := ult.siguientes[0]
		if ult.siguientes.size() > 1:
			# de frente, más a menudo; cerca de la plaza, hacia ella (así hay mucho tránsito alrededor)
			var pesos := 0.0
			for o in ult.siguientes:
				pesos += _peso_giro(ult, o)
			var r := randf() * pesos
			for o in ult.siguientes:
				r -= _peso_giro(ult, o)
				if r <= 0.0:
					sig = o
					break
		ruta.append(sig)
		adelante += red.tramos[sig].largo

## Peso de seguir por el conector 'o' al final del tramo 'ult': de frente ×3; si se está cerca de la plaza y el camino
## (el carril al que lleva el conector) es del anillo de la plaza o termina más cerca de ella, × la atracción de la plaza.
func _peso_giro(ult: RedVial.Tramo, o: int) -> float:
	var con: RedVial.Tramo = red.tramos[o]
	var w := 3.0 if absf(con.giro) < 0.5 else 1.0
	var c: Vector2 = trafico.plaza_centro
	var atraccion: float = trafico.plaza_atraccion
	var radio: float = trafico.plaza_radio
	if atraccion > 1.0 and c.x != INF and not con.siguientes.is_empty():
		var aqui := ult.pts[ult.pts.size() - 1]
		var d0 := Vector2(aqui.x - c.x, aqui.z - c.y).length()
		if d0 < radio * 2.0:
			var destino: RedVial.Tramo = red.tramos[con.siguientes[0]]
			var fin := destino.pts[destino.pts.size() - 1]
			# sigue por el anillo de la plaza, o se acerca a ella
			if trafico.carriles_plaza.has(destino.id) or Vector2(fin.x - c.x, fin.z - c.y).length() < maxf(d0, radio * 0.6):
				w *= atraccion
	return w

## Punto de la ruta a 'd' metros por delante del eje trasero.
func punto_ruta(d: float) -> Vector3:
	var k := 0
	var x := s + d
	while k < ruta.size() - 1 and x > _largo(k):
		x -= _largo(k)
		k += 1
	return RedVial.punto(red.tramos[ruta[k]], x)

## Pasa al tramo siguiente al terminar uno. Devuelve false si llegó al final de la red (sale de la ciudad).
func _avanzar_ruta() -> bool:
	while s > _largo(0):
		if ruta.size() < 2:
			return false
		s -= _largo(0)
		ruta.pop_front()
	if ruta.size() < 2 and s >= _largo(0) - 0.5:
		return false
	_extender_ruta()
	return true

func eje_trasero_global() -> Vector3:
	return global_transform * Vector3(0.0, 0.0, float(kit.mov["eje_trasero"]))

## Ubica el cuerpo sobre el carril (modo lejano y al aparecer): eje trasero en el carril, mirando al punto de la batalla.
func _pose_en_ruta() -> void:
	var a := punto_ruta(0.0)
	var b := punto_ruta(_batalla)
	var z := (b - a)
	if z.length_squared() < 1e-6:
		return
	z = z.normalized()
	var x := Vector3.UP.cross(z).normalized()
	var y := z.cross(x)
	global_transform = Transform3D(Basis(x, y, z), a - z * float(kit.mov["eje_trasero"]))

func _poner_lejano(si: bool) -> void:
	lejano = si
	freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
	freeze = si
	# lejos no choca con nada (ni el cuerpo ni los rayos de las ruedas): solo se dibuja donde dice el conductor.
	# (Sacarlo del espacio físico con process_mode colgaba Jolt de vez en cuando.)
	collision_layer = 0 if si else 4
	collision_mask = 0 if si else (1 | 2 | 4 | 8)
	if not si:
		linear_velocity = global_basis.z * v
		angular_velocity = Vector3.ZERO
	for w in _ruedas:
		w.engine_force = 0.0
		w.brake = 0.0

## Frena del todo (fuera del carril, a la vista): queda quieto como cuerpo físico.
func detener() -> void:
	steering = 0.0
	for w in _ruedas:
		w.engine_force = 0.0
		w.brake = mass * 6.0 / float(Engine.physics_ticks_per_second) * 0.25

func fijar_lejano(si: bool) -> void:
	if si != lejano:
		_poner_lejano(si)

# ------------------------------------------------------------------------------------------------------------ manejo
## Paso de un vehículo lejano que no piensa en este paso: sigue con la última aceleración decidida (movimiento suave).
func rodar_lejano(dt: float) -> bool:
	if not activo:
		return true
	v = maxf(0.0, v + _a_lejano * dt)
	s += v * dt
	if not _avanzar_ruta():
		return false
	_pose_en_ruta()
	return true

## Un paso del conductor. Devuelve false si el vehículo salió de la red (Trafico lo hace reaparecer).
func conducir(dt: float) -> bool:
	if not activo:
		return true
	if not lejano:
		# dónde está de verdad: se proyecta el eje trasero sobre el carril
		v = linear_velocity.dot(global_basis.z)
		var eje := eje_trasero_global()
		var pr := RedVial.proyectar(red.tramos[ruta[0]], eje, s)
		s = pr[0]
		# al final del tramo: ¿ya está en el siguiente? (la proyección no sale de un tramo)
		if ruta.size() > 1 and s > _largo(0) - 6.0:
			var sig := RedVial.proyectar(red.tramos[ruta[1]], eje, maxf(0.0, s - _largo(0)))
			if sig[1] <= pr[1] and sig[0] > 0.01:
				s = _largo(0) + sig[0]
				pr = sig
		desvio = maxf(desvio, pr[1])
		if pr[1] > 7.0:
			return false   # se fue del carril (choque, vuelco): Trafico lo retira fuera de la vista
	if not _avanzar_ruta():
		return false
	_armar_trazado()
	var a := _aceleracion(dt)
	if lejano:
		if _tornamesa:
			_volante(dt)   # sin física no gira nada, pero el eje y el caballo siguen la curva
		_a_lejano = a
		v = maxf(0.0, v + a * dt)
		_maniobra = 0.0
		s += v * dt
		if not _avanzar_ruta():
			return false
		_pose_en_ruta()
	else:
		# atascado contra algo (un poste en una esquina cerrada, otro vehículo): marcha atrás un poco y otra vez
		if _maniobra > 0.0:
			_maniobra -= dt
			a = -0.8
		elif a > 0.3 and absf(v) < 0.15:
			_atasco += dt
			if _atasco > ATASCO:
				_atasco = 0.0
				_maniobra = MANIOBRA
				_giro_maniobra = _direccion
		else:
			_atasco = 0.0
		_volante(dt)
		_pedales(a)
		var en_suelo := false
		for w in _ruedas:
			en_suelo = en_suelo or w.is_in_contact()
		sin_suelo = 0.0 if en_suelo else sin_suelo + dt
	quieto = quieto + dt if absf(v) < 0.1 else 0.0
	return true

## El trazado se rehace solo cuando avanzó más de un metro o cambió de tramo; entre medio vale con su desfase.
func _armar_trazado() -> void:
	if not ruta.is_empty() and ruta[0] == _trazado_tramo and s >= _trazado_s and s - _trazado_s < 1.0:
		return
	var r := red.muestrear(ruta, s, MUESTRA, int(ALCANCE_OBSTACULOS / MUESTRA) + 1)
	_trazado = r[0]
	_vlim_trazado = r[1]
	_trazado_tramo = ruta[0]
	_trazado_s = s

## Cuánto avanzó desde que se muestreó el trazado (se resta a la distancia de cada punto).
func desfase_trazado() -> float:
	return s - _trazado_s

func trazado() -> PackedVector3Array:
	return _trazado

## Persecución pura desde el eje trasero (mirada corta a poca velocidad: no se come las esquinas).
func _volante(dt: float) -> void:
	if _maniobra > 0.0:
		_direccion = move_toward(_direccion, -_giro_maniobra, 1.2 * dt)
		steering = _direccion
		return
	var ld := clampf(3.8 + 0.8 * absf(v), 4.5, 16.0)
	var objetivo := punto_ruta(ld)
	var local := global_transform.affine_inverse() * objetivo
	local.z -= float(kit.mov["eje_trasero"])
	var alfa := atan2(local.x, local.z)
	var deseada := atan(2.0 * _batalla * sin(alfa) / ld)
	var maxima := maxf(float(kit.mov["direccion_maxima"]), DIRECCION_MINIMA)
	deseada = clampf(deseada, -maxima, maxima)
	var rapidez := float(kit.mov["rapidez_direccion"]) * 1.8
	_direccion = move_toward(_direccion, deseada, rapidez * dt)
	steering = _direccion

## Aceleración pedida → motor (eje trasero) o frenos (cuatro ruedas). Godot: el freno es el impulso máximo por paso.
func _pedales(a: float) -> void:
	var paso := 1.0 / float(Engine.physics_ticks_per_second)
	var motor := 0.0
	var freno := 0.0
	if _maniobra > 0.0:
		var atras := -mass * 0.9 * 0.5 if v > -1.0 else 0.0
		for w in _ruedas:
			w.engine_force = atras if w.use_as_traction else 0.0
			w.brake = 0.0
		return
	if a > 0.0:
		motor = mass * (a + 0.12) * 0.5          # + resistencia a la rodadura; dos ruedas de tracción
	else:
		freno = mass * (-a) * paso * 0.25
	if v < 0.25 and a < 0.05:
		freno = mass * 3.0 * paso * 0.25          # detenido: freno de mano (no se va en bajada)
		motor = 0.0
	for w in _ruedas:
		w.engine_force = motor if w.use_as_traction else 0.0
		w.brake = freno

## IDM contra el obstáculo más cercano en el trazado, con la velocidad de las curvas que vienen.
func _aceleracion(dt: float) -> float:
	var m := kit.mov
	var amax := float(m["aceleracion"])
	var bmax := float(m["frenada"])
	var v0 := minf(float(m["velocidad_maxima"]), v_tope) * temple
	# curvas por delante: llegar a cada una ya a su velocidad (frenando cómodo desde aquí)
	var desfase := desfase_trazado()
	for i in _vlim_trazado.size():
		var lim := _vlim_trazado[i] * temple
		v0 = minf(v0, sqrt(lim * lim + 2.0 * FRENADA_COMODA * maxf(0.0, i * MUESTRA - desfase - _frente)))
	var obs: Array = trafico.obstaculo(self)        # [hueco (m), velocidad del obstáculo]
	var hueco: float = obs[0]
	var v_otro: float = obs[1]
	motivo = ("%s %.1f" % [motivo_obst, hueco]) if hueco < 1e5 else ""
	var cr := _gestionar_cruce(dt)
	if cr < hueco:
		hueco = cr
		v_otro = 0.0
		motivo = "cruce %.1f esp=%.1f" % [cr, espera_cruce]
	var libre := 1.0 - pow(maxf(v, 0.0) / maxf(v0, 0.3), 4.0)
	var inter := 0.0
	if hueco < 1e5:
		var s_estrella := S0 + maxf(0.0, v * T_SEGURIDAD + v * (v - v_otro) / (2.0 * sqrt(amax * FRENADA_COMODA)))
		inter = pow(s_estrella / maxf(hueco, 0.2), 2.0)
	return clampf(amax * (libre - inter), -bmax * 2.5, amax)

## Cruces: pide el paso al acercarse al primer conector de la ruta; si no se lo dan, la línea de detención es un obstáculo.
func _gestionar_cruce(dt: float) -> float:
	# el cruce concedido se suelta cuando la cola del vehículo salió del conector
	if concedido and conector >= 0 and not ruta.has(conector):
		var atras := float(kit.mov["eje_trasero"]) - kit.cola + (remolque.largo if remolque else 0.0)
		if s > atras + 0.5 or red.tramos[ruta[0]].cruce >= 0:
			trafico.soltar_cruce(self)
	if concedido and ruta[0] == conector:
		return INF
	var acum := -s
	var idx := -1
	for k in ruta.size():
		var t: RedVial.Tramo = red.tramos[ruta[k]]
		if k > 0 and t.cruce >= 0:
			idx = k
			break
		acum += t.largo
		if acum > 60.0:
			break
	if idx < 0:
		return INF
	var con: RedVial.Tramo = red.tramos[ruta[idx]]
	var hasta := acum - _frente
	var alcance := maxf(14.0, v * v / (2.0 * FRENADA_COMODA) + 8.0)
	if hasta > alcance:
		return INF
	if concedido:
		return INF if conector == con.id else maxf(hasta - 0.8, 0.0)
	if trafico.pedir_cruce(self, con, dt):
		return INF
	return maxf(hasta - 0.8, 0.0)
