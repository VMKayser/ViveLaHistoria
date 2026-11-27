class_name RedVial
extends RefCounted
## Red de carriles del tráfico (datos/red.json, la genera web/scripts/red_vial.py desde OSM y las calles reales).
##
## Un TRAMO es un carril de calle o una curva de cruce (conector): una polilínea densa (~1 punto por metro) con su
## longitud acumulada, tangente, curvatura y velocidad máxima por punto (límite de la calle y aceleración lateral cómoda
## en las curvas). Los conductores (Vehiculo) la usan como trazado a seguir: no van "sobre rieles", la siguen con el
## volante (persecución pura) y el motor; solo los vehículos lejanos avanzan por distancia sobre ella.

## Aceleración lateral cómoda (m/s²): limita la velocidad en las curvas.
const ACEL_LATERAL := 2.4        # 2026-11-26: antes 1,5 (doblaban las esquinas a paso de hombre)

class Tramo:
	var id: int
	var pts: PackedVector3Array
	var s: PackedFloat32Array           # distancia acumulada hasta cada punto
	var vlim: PackedFloat32Array        # velocidad máxima en cada punto
	var largo: float
	var calle: String
	var fuera: bool                     # fuera de la zona modelada (entrada y salida de vehículos)
	var cruce := -1                     # conector: id del cruce (todos los de un mismo nodo de OSM lo comparten)
	var giro := 0.0                     # conector: giro total (rad, + izquierda)
	var siguientes: Array[int] = []
	var anteriores: Array[int] = []

var tramos: Array[Tramo] = []
var entradas: Array[int] = []           # carriles sin anterior: borde de la red, por donde entran vehículos
var carriles_zona: Array[int] = []      # carriles dentro de la zona modelada (reparto inicial)
var cruces := 0

func _init(datos: Dictionary) -> void:
	var carriles: Array = datos["carriles"]
	var nc := carriles.size()
	for i in nc:
		var c: Dictionary = carriles[i]
		tramos.append(_tramo(i, c["puntos"], float(c["vmax"]), str(c.get("calle", "")), bool(c.get("fuera", false)), -1, 0.0))
	var ids_cruce := {}
	var conectores: Array = datos["conectores"]
	for i in conectores.size():
		var k: Dictionary = conectores[i]
		var nodo := str(k["nodo"])
		if not ids_cruce.has(nodo):
			ids_cruce[nodo] = ids_cruce.size()
		var de: Tramo = tramos[int(k["de"])]
		var a: Tramo = tramos[int(k["a"])]
		var t := _tramo(nc + i, k["puntos"], minf(de.vlim[de.vlim.size() - 1], a.vlim[0]), de.calle, de.fuera and a.fuera,
			ids_cruce[nodo], float(k.get("giro", 0.0)))
		tramos.append(t)
		de.siguientes.append(t.id)
		t.anteriores.append(de.id)
		t.siguientes.append(a.id)
		a.anteriores.append(t.id)
	cruces = ids_cruce.size()
	for i in nc:
		var t := tramos[i]
		if t.anteriores.is_empty():
			entradas.append(i)
		if not t.fuera and t.largo > 12.0:
			carriles_zona.append(i)

func _tramo(id: int, puntos: Array, vmax: float, calle: String, fuera: bool, cruce: int, giro: float) -> Tramo:
	var t := Tramo.new()
	t.id = id
	t.calle = calle
	t.fuera = fuera
	t.cruce = cruce
	t.giro = giro
	var n := puntos.size() / 3
	t.pts.resize(n)
	t.s.resize(n)
	t.vlim.resize(n)
	for i in n:
		t.pts[i] = Vector3(puntos[3 * i], puntos[3 * i + 1], puntos[3 * i + 2])
		if i > 0:
			t.s[i] = t.s[i - 1] + t.pts[i].distance_to(t.pts[i - 1])
	t.largo = t.s[n - 1] if n > 0 else 0.0
	# curvatura: cambio de rumbo por metro entre puntos a ±2 → velocidad cómoda en la curva
	for i in n:
		var a := maxi(0, i - 2)
		var b := mini(n - 1, i + 2)
		var ds := t.s[b] - t.s[a]
		var curv := 0.0
		if ds > 1e-3 and b - a >= 2:
			var t0 := Vector2(t.pts[a + 1].x - t.pts[a].x, t.pts[a + 1].z - t.pts[a].z).normalized()
			var t1 := Vector2(t.pts[b].x - t.pts[b - 1].x, t.pts[b].z - t.pts[b - 1].z).normalized()
			curv = absf(t0.angle_to(t1)) / ds
		t.vlim[i] = minf(vmax, sqrt(ACEL_LATERAL / maxf(curv, 1e-4)))
	return t

## Índice del segmento [i, i+1] que contiene la distancia d (búsqueda binaria).
static func segmento(t: Tramo, d: float) -> int:
	var hi := t.s.size() - 1
	if d <= 0.0 or hi <= 0:
		return 0
	if d >= t.s[hi]:
		return hi - 1
	return clampi(t.s.bsearch(d, true) - 1, 0, hi - 1)

## Punto del tramo a la distancia d.
static func punto(t: Tramo, d: float) -> Vector3:
	var i := segmento(t, d)
	var j := mini(i + 1, t.pts.size() - 1)
	var l := t.s[j] - t.s[i]
	var u := clampf((d - t.s[i]) / l, 0.0, 1.0) if l > 1e-6 else 0.0
	return t.pts[i].lerp(t.pts[j], u)

## Muestrea una ruta (lista de tramos) desde 'd0' sobre el primero, cada 'paso' metros, 'n' puntos. Devuelve
## [posiciones, velocidades máximas]. Recorre la polilínea una sola vez (sin búsquedas por punto).
func muestrear(ruta: Array[int], d0: float, paso: float, n: int) -> Array:
	var pts := PackedVector3Array()
	var vlim := PackedFloat32Array()
	pts.resize(n)
	vlim.resize(n)
	var k := 0
	var t: Tramo = tramos[ruta[0]]
	var ts := t.s
	var tp := t.pts
	var tv := t.vlim
	var largo := t.largo
	var i := segmento(t, d0)
	var d := d0
	for j in n:
		while true:
			if i < ts.size() - 2 and d > ts[i + 1]:
				i += 1
			elif d > largo and k < ruta.size() - 1:
				d -= largo
				k += 1
				t = tramos[ruta[k]]
				ts = t.s
				tp = t.pts
				tv = t.vlim
				largo = t.largo
				i = 0
			else:
				break
		var i1 := mini(i + 1, ts.size() - 1)
		var l := ts[i1] - ts[i]
		var u := clampf((d - ts[i]) / l, 0.0, 1.0) if l > 1e-6 else 0.0
		pts[j] = tp[i].lerp(tp[i1], u)
		vlim[j] = tv[i]
		d += paso
	return [pts, vlim]

static func velocidad(t: Tramo, d: float) -> float:
	return t.vlim[segmento(t, d)]

## Distancia sobre el tramo del punto más cercano a p, buscando cerca de 'cerca' (−4 a +12 m): rápida y estable.
static func proyectar(t: Tramo, p: Vector3, cerca: float) -> Array:
	var i0 := maxi(0, segmento(t, cerca - 4.0))
	var i1 := mini(t.pts.size() - 1, segmento(t, cerca + 12.0) + 1)
	var mejor := INF
	var mejor_s := cerca
	for i in range(i0, i1):
		var a := t.pts[i]
		var b := t.pts[i + 1]
		var ab := Vector2(b.x - a.x, b.z - a.z)
		var l2 := ab.length_squared()
		var u := 0.0 if l2 < 1e-8 else clampf(Vector2(p.x - a.x, p.z - a.z).dot(ab) / l2, 0.0, 1.0)
		var q := Vector2(a.x + ab.x * u - p.x, a.z + ab.y * u - p.z)
		var d2 := q.length_squared()
		if d2 < mejor:
			mejor = d2
			mejor_s = t.s[i] + (t.s[i + 1] - t.s[i]) * u
	return [mejor_s, sqrt(mejor)]
