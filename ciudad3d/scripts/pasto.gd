class_name Pasto
extends Node3D
## Pasto y flores de verdad alrededor del caminante (pedido del usuario, 2026-11-26: "mejorar el pasto, flores, algo más
## realista"). El empaquetador deja en datos/pasto.json los triángulos de césped y de canteros; aquí se siembran en celdas
## de 16 m dentro de 'radio': matas de hojas de pasto y flores (tallo, cinco pétalos y centro) como MultiMesh, una llamada
## de dibujo por celda y tipo. Más lejos el shader las hunde en el suelo (sin saltos); la densidad baja con la distancia
## (las instancias van en orden al azar: mostrar las primeras N es ralear parejo). Una celda nueva por cuadro.

const CELDA := 16.0
const DENSIDAD_PASTO := 28.0        # matas por m² (de cerca)
const DENSIDAD_FLORES := 30.0       # flores por m² de cantero
const MAX_POR_CELDA := 9000

var radio := 40.0                   # m (según la calidad; 0 = sin pasto)
var ciudad: Ciudad
var _cesped := PackedFloat32Array()  # 12 floats por triángulo: 9 coordenadas + color
var _flores := PackedFloat32Array()
var _indice := {}                    # Vector2i -> [triángulos de césped, triángulos de flores]
var _vivas := {}                     # Vector2i -> [MultiMeshInstance3D o null, …]
var _mat_pasto: ShaderMaterial
var _mat_flores: ShaderMaterial
var _mata: ArrayMesh
var _flor: ArrayMesh
var _t := 0.0
var _listo := false

func _ready() -> void:
	if not ciudad.listo:
		await ciudad.indice_listo
	var d = await Datos.json("pasto.json", ciudad.version)
	if d == null:
		return
	_cesped = _aplanar(d["cesped"])
	_flores = _aplanar(d["flores"])
	_indexar(_cesped, 0)
	_indexar(_flores, 1)
	_mata = _malla_mata()
	_flor = _malla_flor()
	_mat_pasto = _material(false)
	_mat_flores = _material(true)
	_listo = true

static func _aplanar(lista: Array) -> PackedFloat32Array:
	var r := PackedFloat32Array()
	for t in lista:
		r.append_array(PackedFloat32Array(t))
	return r

func _indexar(tris: PackedFloat32Array, cual: int) -> void:
	for t in tris.size() / 12:
		var o := t * 12
		var x0 := minf(tris[o], minf(tris[o + 3], tris[o + 6]))
		var x1 := maxf(tris[o], maxf(tris[o + 3], tris[o + 6]))
		var z0 := minf(tris[o + 2], minf(tris[o + 5], tris[o + 8]))
		var z1 := maxf(tris[o + 2], maxf(tris[o + 5], tris[o + 8]))
		for i in range(floori(x0 / CELDA), floori(x1 / CELDA) + 1):
			for j in range(floori(z0 / CELDA), floori(z1 / CELDA) + 1):
				var k := Vector2i(i, j)
				if not _indice.has(k):
					_indice[k] = [[], []]
				_indice[k][cual].append(t)

func _material(fl: bool) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/pasto.gdshader")
	m.set_shader_parameter("flores", fl)
	m.set_shader_parameter("radio", radio)
	return m

func fijar_radio(r: float) -> void:
	radio = r
	if _mat_pasto:
		_mat_pasto.set_shader_parameter("radio", r)
		_mat_flores.set_shader_parameter("radio", r)

func _process(dt: float) -> void:
	if not _listo:
		return
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var p := cam.global_position
	_t -= dt
	if _t <= 0.0:
		_t = 0.25
		_raleo(p)
	if radio <= 0.0:
		return
	# la celda más cercana que falte (una por cuadro)
	var mejor = null
	var dmin := INF
	var c0 := Vector2i(floori(p.x / CELDA), floori(p.z / CELDA))
	var n := ceili(radio / CELDA)
	for i in range(c0.x - n, c0.x + n + 1):
		for j in range(c0.y - n, c0.y + n + 1):
			var k := Vector2i(i, j)
			if _vivas.has(k) or not _indice.has(k):
				continue
			var dd := _dist(k, p)
			if dd < radio and dd < dmin:
				dmin = dd
				mejor = k
	if mejor != null:
		_sembrar(mejor)

func _dist(k: Vector2i, p: Vector3) -> float:
	var cx := clampf(p.x, k.x * CELDA, (k.x + 1) * CELDA)
	var cz := clampf(p.z, k.y * CELDA, (k.y + 1) * CELDA)
	return Vector2(cx - p.x, cz - p.z).length()

## Densidad según la distancia y celdas que sobran.
func _raleo(p: Vector3) -> void:
	for k in _vivas.keys():
		var d := _dist(k, p)
		if d > radio + 8.0:
			for mmi in _vivas[k]:
				if mmi:
					mmi.queue_free()
			_vivas.erase(k)
			continue
		var f := clampf(1.0 - (d - 8.0) / maxf(radio - 8.0, 1.0) * 0.75, 0.25, 1.0)
		for mmi in _vivas[k]:
			if mmi:
				var mm: MultiMesh = mmi.multimesh
				mm.visible_instance_count = int(mm.instance_count * f)

func _sembrar(k: Vector2i) -> void:
	var listas: Array = _indice[k]
	_vivas[k] = [_multimesh(k, _cesped, listas[0], DENSIDAD_PASTO, _mata, _mat_pasto, 0.75, 1.35),
		_multimesh(k, _flores, listas[1], DENSIDAD_FLORES, _flor, _mat_flores, 0.7, 1.25)]

## Instancias al azar (repetible: la semilla es la celda) sobre los triángulos, solo las que caen dentro de la celda.
## Cada instancia elige su triángulo según el área (búsqueda binaria en las áreas acumuladas): salen ya en orden al azar,
## así que ralear es mostrar las primeras N.
func _multimesh(k: Vector2i, tris: PackedFloat32Array, lista: Array, densidad: float, malla: Mesh, mat: Material,
		esc0: float, esc1: float) -> MultiMeshInstance3D:
	if lista.is_empty():
		return null
	var x0 := k.x * CELDA
	var z0 := k.y * CELDA
	var acum := PackedFloat32Array()
	var total := 0.0
	for t in lista:
		var o: int = t * 12
		var a := Vector3(tris[o], tris[o + 1], tris[o + 2])
		total += (Vector3(tris[o + 3], tris[o + 4], tris[o + 5]) - a).cross(Vector3(tris[o + 6], tris[o + 7], tris[o + 8]) - a).length() * 0.5
		acum.append(total)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(k) + int(densidad)
	var intentos := mini(int(total * densidad), MAX_POR_CELDA * 3)
	var buf := PackedFloat32Array()
	buf.resize(mini(intentos, MAX_POR_CELDA) * 16)
	var n := 0
	for q in intentos:
		if n >= MAX_POR_CELDA:
			break
		var o: int = lista[mini(acum.bsearch(rng.randf() * total), lista.size() - 1)] * 12
		var u := rng.randf()
		var v := rng.randf()
		if u + v > 1.0:
			u = 1.0 - u
			v = 1.0 - v
		var w := 1.0 - u - v
		var px := tris[o] * w + tris[o + 3] * u + tris[o + 6] * v
		var pz := tris[o + 2] * w + tris[o + 5] * u + tris[o + 8] * v
		if px < x0 or px >= x0 + CELDA or pz < z0 or pz >= z0 + CELDA:
			continue
		var py := tris[o + 1] * w + tris[o + 4] * u + tris[o + 7] * v
		var ang := rng.randf() * TAU
		var s := rng.randf_range(esc0, esc1)
		var cs := cos(ang) * s
		var sn := sin(ang) * s
		var tono := rng.randf_range(0.85, 1.15)
		# transformación por filas (base girada en Y y escalada) + color
		var b := n * 16
		buf[b] = cs; buf[b + 1] = 0.0; buf[b + 2] = sn; buf[b + 3] = px - x0
		buf[b + 4] = 0.0; buf[b + 5] = s; buf[b + 6] = 0.0; buf[b + 7] = py
		buf[b + 8] = -sn; buf[b + 9] = 0.0; buf[b + 10] = cs; buf[b + 11] = pz - z0
		buf[b + 12] = tris[o + 9] * tono; buf[b + 13] = tris[o + 10] * tono
		buf[b + 14] = tris[o + 11] * rng.randf_range(0.8, 1.2); buf[b + 15] = 1.0
		n += 1
	if n == 0:
		return null
	buf.resize(n * 16)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = malla
	mm.instance_count = n
	mm.buffer = buf
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = mat
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mmi.position = Vector3(x0, 0.0, z0)
	add_child(mmi)
	return mmi

## Una mata: seis hojas de pasto finas, algo curvadas y abiertas, de 6 a 15 cm (césped cuidado de plaza). UV.y: altura relativa (para el color y
## el viento).
static func _malla_mata() -> ArrayMesh:
	var rng := RandomNumberGenerator.new()
	rng.seed = 2611
	var v := PackedVector3Array()
	var nrm := PackedVector3Array()
	var uv := PackedVector2Array()
	var idx := PackedInt32Array()
	for h in 6:
		var ang := rng.randf() * TAU
		var dir := Vector3(cos(ang), 0.0, sin(ang))
		var lado := Vector3(-dir.z, 0.0, dir.x)
		var pie := dir * rng.randf_range(0.0, 0.07)
		var alto := rng.randf_range(0.06, 0.15)
		var inclina := rng.randf_range(0.02, 0.07)
		var ancho := rng.randf_range(0.006, 0.01)
		var medio := pie + dir * inclina * 0.4 + Vector3.UP * alto * 0.55
		var punta := pie + dir * inclina + Vector3.UP * alto
		var b := v.size()
		v.append_array([pie - lado * ancho, pie + lado * ancho, medio - lado * ancho * 0.7, medio + lado * ancho * 0.7, punta])
		uv.append_array([Vector2(0, 0), Vector2(0, 0), Vector2(0, 0.55), Vector2(0, 0.55), Vector2(0, 1)])
		var n := dir
		for q in 5:
			nrm.append(n)
		idx.append_array([b, b + 2, b + 1, b + 1, b + 2, b + 3, b + 2, b + 4, b + 3])
	return _malla(v, nrm, uv, idx)

## Una flor: tallo con dos hojitas, cinco pétalos abiertos y el centro. UV.x: 0 tallo y hojas, 1 pétalos, 2 centro.
static func _malla_flor() -> ArrayMesh:
	var v := PackedVector3Array()
	var nrm := PackedVector3Array()
	var uv := PackedVector2Array()
	var idx := PackedInt32Array()
	var alto := 0.17
	var w := 0.006
	# tallo (dos caras cruzadas) y hojas
	for lado in [Vector3(w, 0, 0), Vector3(0, 0, w)]:
		var b := v.size()
		v.append_array([-lado, lado, Vector3(0, alto, 0) - lado, Vector3(0, alto, 0) + lado])
		uv.append_array([Vector2(0, 0), Vector2(0, 0), Vector2(0, 1), Vector2(0, 1)])
		for q in 4:
			nrm.append(Vector3(lado.z, 0, lado.x).normalized())
		idx.append_array([b, b + 2, b + 1, b + 1, b + 2, b + 3])
	for s in [1.0, -1.0]:
		var b := v.size()
		var y := 0.05 + (0.04 if s > 0 else 0.0)
		v.append_array([Vector3(0, y, 0), Vector3(0.07 * s, y + 0.04, 0.025), Vector3(0.06 * s, y + 0.035, -0.02)])
		uv.append_array([Vector2(0, 0.3), Vector2(0, 0.5), Vector2(0, 0.5)])
		for q in 3:
			nrm.append(Vector3(0, 1, 0))
		idx.append_array([b, b + 1, b + 2])
	# pétalos: abanico de cinco lóbulos algo levantados
	var c := Vector3(0, alto, 0)
	for p in 5:
		var a0 := p * TAU / 5.0
		var b := v.size()
		var d0 := Vector3(cos(a0 - 0.32), 0, sin(a0 - 0.32))
		var d1 := Vector3(cos(a0), 0, sin(a0))
		var d2 := Vector3(cos(a0 + 0.32), 0, sin(a0 + 0.32))
		v.append_array([c, c + d0 * 0.05 + Vector3(0, 0.014, 0), c + d1 * 0.066 + Vector3(0, 0.022, 0),
			c + d2 * 0.05 + Vector3(0, 0.014, 0)])
		uv.append_array([Vector2(1, 1), Vector2(1, 1), Vector2(1, 1), Vector2(1, 1)])
		for q in 4:
			nrm.append(Vector3(0, 1, 0))
		idx.append_array([b, b + 1, b + 2, b, b + 2, b + 3])
	# centro
	var b2 := v.size()
	for p in 4:
		var a := p * TAU / 4.0
		v.append(c + Vector3(cos(a) * 0.015, 0.02, sin(a) * 0.015))
		uv.append(Vector2(2, 1))
		nrm.append(Vector3(0, 1, 0))
	idx.append_array([b2, b2 + 1, b2 + 2, b2, b2 + 2, b2 + 3])
	return _malla(v, nrm, uv, idx)

static func _malla(v: PackedVector3Array, nrm: PackedVector3Array, uv: PackedVector2Array, idx: PackedInt32Array) -> ArrayMesh:
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_NORMAL] = nrm
	arr[Mesh.ARRAY_TEX_UV] = uv
	var blanco := PackedColorArray()
	blanco.resize(v.size())
	blanco.fill(Color.WHITE)
	arr[Mesh.ARRAY_COLOR] = blanco
	arr[Mesh.ARRAY_INDEX] = idx
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return m
