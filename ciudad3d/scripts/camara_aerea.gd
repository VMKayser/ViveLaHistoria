class_name CamaraAerea
extends Camera3D
## Vista aérea (portada de web/src/ciudad/escena/CamaraMapa.tsx): un dedo mueve, dos dedos acercan y giran; vuelos animados
## a un punto; norte arriba; giro lento en la pantalla de inicio.

const ANIMACION := 0.45
const DIST_MIN := 6.0
const DIST_MAX := 1800.0
const PHI_MAX := PI / 2.1
const AUTOGIRO := 0.037    # rad/s

var objetivo := Vector3(-205.0, 58.0, 150.0)
var distancia := 235.0
var azimut := 0.74         # de dónde se mira: el desplazamiento horizontal de la cámara es (sen az, cos az)
var phi := 0.7             # inclinación desde la vertical (0 = desde arriba)
var autogiro := false
var activa := false
var _vuelo = null
var _toques := {}
var _ultimo_2 := {}

func _ready() -> void:
	fov = 40.0
	near = 0.3
	far = 16000.0
	_colocar()

func _desplazamiento() -> Vector3:
	var h := distancia * sin(phi)
	return Vector3(sin(azimut) * h, distancia * cos(phi), cos(azimut) * h)

func _colocar() -> void:
	global_position = objetivo + _desplazamiento()
	look_at(objetivo, Vector3.UP)

## Rumbo (rad, horario desde el norte) hacia el que mira la cámara.
func rumbo() -> float:
	var d := _desplazamiento()
	return atan2(-d.x, d.z)

func volar_a(obj: Vector3, dist := -1.0, az := NAN, ph := NAN) -> void:
	_vuelo = {"t": 0.0, "desde": [objetivo, distancia, azimut, phi],
		"hasta": [obj, distancia if dist < 0.0 else clampf(dist, DIST_MIN, DIST_MAX), azimut if is_nan(az) else az, phi if is_nan(ph) else ph]}

func ir_a(obj: Vector3, inmediato := false) -> void:
	if inmediato:
		_vuelo = null
		objetivo = obj
		_colocar()
	else:
		volar_a(obj)

func desplazar(dx: float, dz: float) -> void:
	_vuelo = null
	objetivo.x += dx
	objetivo.z += dz
	_colocar()

func norte_arriba() -> void:
	volar_a(objetivo, distancia, 0.0, phi)

func acercar(factor: float) -> void:
	volar_a(objetivo, distancia * factor)

## Las cuatro esquinas de lo que se ve en el suelo (para el minimapa).
func huella() -> PackedVector2Array:
	var r := PackedVector2Array()
	var vs := get_viewport().get_visible_rect().size
	var plano := Plane(Vector3.UP, objetivo.y)
	for c in [Vector2(0, vs.y), Vector2(vs.x, vs.y), Vector2(vs.x, 0), Vector2(0, 0)]:
		var o := project_ray_origin(c)
		var n := project_ray_normal(c)
		var p = plano.intersects_ray(o, n)
		if p == null or o.distance_to(p) > 2500.0:
			p = o + n * 2500.0
			p.y = objetivo.y
		r.append(Vector2(p.x, p.z))
	return r

func _process(dt: float) -> void:
	if not activa:
		return
	dt = minf(dt, 0.1)
	if _vuelo != null:
		_vuelo["t"] = minf(1.0, _vuelo["t"] + dt / ANIMACION)
		var s: float = _vuelo["t"]
		s = s * s * (3.0 - 2.0 * s)
		var d: Array = _vuelo["desde"]
		var h: Array = _vuelo["hasta"]
		objetivo = (d[0] as Vector3).lerp(h[0], s)
		distancia = lerpf(d[1], h[1], s)
		azimut = lerp_angle(d[2], h[2], s)
		phi = lerpf(d[3], h[3], s)
		if s >= 1.0:
			_vuelo = null
	elif autogiro:
		azimut += AUTOGIRO * dt
	_colocar()

func _input(ev: InputEvent) -> void:
	if not activa or autogiro:
		return
	if ev is InputEventScreenTouch:
		if ev.pressed:
			_toques[ev.index] = ev.position
		else:
			_toques.erase(ev.index)
		_ultimo_2 = {}
	elif ev is InputEventScreenDrag and _toques.has(ev.index):
		_toques[ev.index] = ev.position
		if _toques.size() == 1:
			_arrastrar(ev.position - ev.relative, ev.position)
		elif _toques.size() == 2:
			_dos_dedos()

func _punto_suelo(p: Vector2):
	var o := project_ray_origin(p)
	var n := project_ray_normal(p)
	return Plane(Vector3.UP, objetivo.y).intersects_ray(o, n)

func _arrastrar(antes: Vector2, ahora: Vector2) -> void:
	var a = _punto_suelo(antes)
	var b = _punto_suelo(ahora)
	if a == null or b == null:
		return
	_vuelo = null
	var d: Vector3 = a - b
	objetivo.x += d.x
	objetivo.z += d.z
	_colocar()

func _dos_dedos() -> void:
	var ks := _toques.keys()
	var p1: Vector2 = _toques[ks[0]]
	var p2: Vector2 = _toques[ks[1]]
	var dist := p1.distance_to(p2)
	var ang := (p2 - p1).angle()
	if _ultimo_2.has("dist") and dist > 1.0:
		_vuelo = null
		distancia = clampf(distancia * _ultimo_2["dist"] / dist, DIST_MIN, DIST_MAX)
		azimut -= angle_difference(_ultimo_2["ang"], ang)
		_colocar()
	_ultimo_2 = {"dist": dist, "ang": ang}
