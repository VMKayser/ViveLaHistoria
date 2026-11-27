class_name Calles
extends RefCounted
## Nombre de la calle más cercana a un punto (portado de web/src/mapa/busqueda.ts): rejilla de celdas de 40 m con los tramos.
## Las coordenadas del archivo son del mapa (x este, y norte); el mundo 3D usa z = −norte.

const CELDA := 40.0
const TIPOS_MENORES := ["footway", "steps", "path", "service"]
var _celdas := {}
var _puntos := PackedVector2Array()   # vértices de calles con nombre (x, z del mundo) para elegir dónde aparecer

func cargar(texto: String) -> void:
	var datos = JSON.parse_string(texto)
	if datos == null:
		return
	for c in datos:
		var p: Array = c["p"]
		var nombre: String = c["n"]
		if nombre != "" and not (c["t"] in TIPOS_MENORES):
			for q in p:
				_puntos.append(Vector2(q[0], -q[1]))
		for i in range(1, p.size()):
			var t := [p[i - 1][0], p[i - 1][1], p[i][0], p[i][1], nombre]
			for k in [_clave(p[i - 1][0], p[i - 1][1]), _clave(p[i][0], p[i][1])]:
				if not _celdas.has(k):
					_celdas[k] = []
				if not (t in _celdas[k]):
					_celdas[k].append(t)

func _clave(x: float, y: float) -> String:
	return "%d,%d" % [floori(x / CELDA), floori(y / CELDA)]

func _dist_tramo(px: float, py: float, t: Array) -> float:
	var dx: float = t[2] - t[0]
	var dy: float = t[3] - t[1]
	var l2: float = dx * dx + dy * dy
	if l2 == 0.0:
		l2 = 1.0
	var u: float = clampf(((px - t[0]) * dx + (py - t[1]) * dy) / l2, 0.0, 1.0)
	return Vector2(px - (t[0] + u * dx), py - (t[1] + u * dy)).length()

## Nombre de la calle a menos de 'max' m del punto web (x, z); "" si no hay.
func calle(x_web: float, z_web: float, maximo: float) -> String:
	var x := x_web
	var y := -z_web
	var cx := floori(x / CELDA)
	var cy := floori(y / CELDA)
	var mejor := ""
	var mejor_d := INF
	for i in range(-1, 2):
		for j in range(-1, 2):
			var lista: Array = _celdas.get("%d,%d" % [cx + i, cy + j], [])
			for t in lista:
				if t[4] == "":
					continue
				var d := _dist_tramo(x, y, t)
				if d < mejor_d:
					mejor_d = d
					mejor = t[4]
	return mejor if mejor_d <= maximo else ""

## Vértices de calles con nombre cercanos a (x, z), de los más cercanos a los más lejanos (a menos de 250 m).
func puntos_cercanos(x: float, z: float, maximo := 200) -> Array:
	var lista := []
	for p in _puntos:
		var d := (p.x - x) * (p.x - x) + (p.y - z) * (p.y - z)
		if d < 250.0 * 250.0:
			lista.append([d, p])
	lista.sort_custom(func(a, b): return a[0] < b[0])
	return lista.slice(0, maximo).map(func(a): return a[1])
