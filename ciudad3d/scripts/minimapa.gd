class_name Minimapa
extends Control
## Minimapa (abajo a la izquierda en la web; aquí arriba a la izquierda para dejar el pulgar libre). Toque sin arrastrar:
## ir a ese punto (a pie, aparece ahí; en vista aérea, vuela). Arrastrar (vista aérea) mueve el mapa.

signal ir_a(x: float, z: float)
signal desplazar(dx: float, dz: float)

const TAM := 170.0
const RADIO_PIE := 85.0
const LIMITES := Vector4(-650.0, -460.0, 250.0, 760.0)

var peaton := true
var centro := Vector2.ZERO
var rumbo_ := 0.0
var distancia := 235.0
var huella := PackedVector2Array()
var _rect: ColorRect
var _mat: ShaderMaterial
var _toque := -1
var _movido := 0.0

func _ready() -> void:
	custom_minimum_size = Vector2(TAM, TAM)
	size = Vector2(TAM, TAM)
	_rect = ColorRect.new()
	_rect.position = Vector2(4, 4)
	_rect.size = Vector2(TAM - 8, TAM - 8)
	_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mat = ShaderMaterial.new()
	_mat.shader = load("res://shaders/minimapa.gdshader")
	# en la web el minimapa es el de la página (React): no se sube esta imagen (≈23 MB de memoria de vídeo)
	if not Datos.en_web:
		_mat.set_shader_parameter("mapa", load("res://texturas/minimapa.webp"))
	_mat.set_shader_parameter("limites", LIMITES)
	_rect.material = _mat
	add_child(_rect)

func radio() -> float:
	return RADIO_PIE if peaton else maxf(120.0, minf(900.0, distancia * 0.9))

func refrescar() -> void:
	_mat.set_shader_parameter("centro", centro)
	_mat.set_shader_parameter("radio", radio())
	_mat.set_shader_parameter("rumbo", rumbo_)
	_mat.set_shader_parameter("peaton", peaton)
	queue_redraw()

func _draw() -> void:
	var c := Vector2(TAM, TAM) / 2.0
	var r := radio()
	var s := (TAM - 8.0) / 2.0 / r        # px por metro
	var giro := rumbo_ if peaton else 0.0
	# trapecio de lo que se ve (vista aérea)
	if not peaton and huella.size() == 4:
		var pts := PackedVector2Array()
		for p in huella:
			var d := (p - centro) * s
			pts.append(c + d.rotated(-giro))
		draw_colored_polygon(pts, Color(1, 1, 1, 0.28))
		pts.append(pts[0])
		draw_polyline(pts, Color(1, 1, 1, 0.95), 2.0)
	# aro bandera: rojo y blanco en cuartos
	for k in 4:
		draw_arc(c, TAM / 2.0 - 3.0, k * PI / 2.0 + PI / 4.0, (k + 1) * PI / 2.0 + PI / 4.0, 24,
			Color("#d9171a") if k % 2 == 0 else Color.WHITE, 5.0, true)
	# flecha del observador: a pie siempre hacia arriba; en vista aérea gira con el rumbo
	var k2 := 1.0 if peaton else 0.8
	var rot := 0.0 if peaton else rumbo_
	var flecha := PackedVector2Array([Vector2(0, -11), Vector2(8, 8), Vector2(0, 4), Vector2(-8, 8)])
	var f := PackedVector2Array()
	for p in flecha:
		f.append(c + (p * k2).rotated(rot))
	draw_colored_polygon(f, Color("#eac102"))
	f.append(f[0])
	draw_polyline(f, Color("#2b1d16"), 1.6)
	# la N roja sobre el borde
	var ang_n := (-rumbo_ if peaton else 0.0) - PI / 2.0
	var pn := c + Vector2(cos(ang_n), sin(ang_n)) * (TAM / 2.0 - 13.0)
	draw_circle(pn, 9.0, Color("#d9171a"))
	var fuente := ThemeDB.fallback_font
	draw_string(fuente, pn + Vector2(-5, 5), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)

func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		if ev.pressed:
			_toque = 1
			_movido = 0.0
		elif _toque == 1:
			_toque = -1
			if _movido < 6.0:
				var c := Vector2(TAM, TAM) / 2.0
				var s := (TAM - 8.0) / 2.0 / radio()
				var v: Vector2 = (ev.position - c) / s
				var a := rumbo_ if peaton else 0.0
				var m := Vector2(v.x * cos(a) - v.y * sin(a), v.x * sin(a) + v.y * cos(a))
				ir_a.emit(centro.x + m.x, centro.y + m.y)
	elif ev is InputEventMouseMotion and _toque == 1:
		_movido += ev.relative.length()
		if not peaton and _movido >= 6.0:
			var s := (TAM - 8.0) / 2.0 / radio()
			desplazar.emit(-ev.relative.x / s, -ev.relative.y / s)
