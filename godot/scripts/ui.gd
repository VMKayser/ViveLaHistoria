extends CanvasLayer
## Interfaz: fundidos, tarjetas de título, subtítulos, objetivo, avisos y el
## indicador del toque a rebato.

const FUENTE := preload("res://assets/fuentes/EBGaramond.ttf")

var fundido: ColorRect
var _tarjeta: VBoxContainer
var _titulo: Label
var _sub: Label
var _caja: PanelContainer
var _quien: Label
var _texto: Label
var _objetivo: Label
var _aviso: Label
var _ayuda: Label
var _mira: ColorRect
var _rebato: Control
var _turno := 0


class Rebato:
	extends Control
	var listo := 0.0
	var progreso := 0.0

	func _draw() -> void:
		var c := size / 2.0
		draw_arc(c, 46.0, 0.0, TAU, 64, Color(1, 1, 1, 0.15), 3.0, true)
		var col := Color(1.0, 0.85, 0.5, 0.95) if listo >= 0.85 else Color(1.0, 1.0, 1.0, 0.6)
		draw_arc(c, 46.0, -PI / 2.0, -PI / 2.0 + TAU * listo, 64, col, 5.0, true)
		if listo >= 0.85:
			draw_circle(c, 8.0, col)
		var ancho := 320.0
		var r := Rect2(c.x - ancho / 2.0, c.y + 78.0, ancho, 8.0)
		draw_rect(r, Color(1, 1, 1, 0.15))
		draw_rect(Rect2(r.position, Vector2(ancho * progreso, 8.0)), Color(1.0, 0.75, 0.4, 0.95))


func _ready() -> void:
	layer = 2
	var raiz := Control.new()
	raiz.set_anchors_preset(Control.PRESET_FULL_RECT)
	raiz.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(raiz)

	_mira = ColorRect.new()
	_mira.color = Color(1, 1, 1, 0.55)
	_mira.size = Vector2(4, 4)
	_mira.set_anchors_preset(Control.PRESET_CENTER)
	_mira.position = Vector2(-2, -2)
	raiz.add_child(_mira)

	_objetivo = _etiqueta(raiz, 26, Color(1.0, 0.92, 0.78))
	_objetivo.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_objetivo.position = Vector2(36, 28)
	_objetivo.modulate.a = 0.0

	_ayuda = _etiqueta(raiz, 20, Color(1, 1, 1, 0.75))
	_ayuda.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_ayuda.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_ayuda.position = Vector2(-640, 28)
	_ayuda.size = Vector2(600, 30)
	_ayuda.modulate.a = 0.0

	_aviso = _etiqueta(raiz, 26, Color(1.0, 0.9, 0.7))
	_aviso.set_anchors_preset(Control.PRESET_CENTER)
	_aviso.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_aviso.size = Vector2(600, 40)
	_aviso.position = Vector2(-300, 60)

	_caja = PanelContainer.new()
	var estilo := StyleBoxFlat.new()
	estilo.bg_color = Color(0.02, 0.015, 0.01, 0.55)
	estilo.set_content_margin_all(16)
	estilo.content_margin_left = 28
	estilo.content_margin_right = 28
	estilo.corner_radius_top_left = 4
	estilo.corner_radius_top_right = 4
	estilo.corner_radius_bottom_left = 4
	estilo.corner_radius_bottom_right = 4
	_caja.add_theme_stylebox_override("panel", estilo)
	_caja.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_caja.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_caja.modulate.a = 0.0
	raiz.add_child(_caja)
	var vb := VBoxContainer.new()
	_caja.add_child(vb)
	_quien = _etiqueta(vb, 22, Color(1.0, 0.78, 0.45))
	_texto = _etiqueta(vb, 30, Color(1, 0.97, 0.92))
	_texto.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART

	_rebato = Rebato.new()
	_rebato.set_anchors_preset(Control.PRESET_CENTER)
	_rebato.size = Vector2(400, 200)
	_rebato.position = Vector2(-200, -100)
	_rebato.visible = false
	raiz.add_child(_rebato)

	fundido = ColorRect.new()
	fundido.color = Color(0, 0, 0, 1)
	fundido.set_anchors_preset(Control.PRESET_FULL_RECT)
	fundido.mouse_filter = Control.MOUSE_FILTER_IGNORE
	raiz.add_child(fundido)

	_tarjeta = VBoxContainer.new()
	_tarjeta.set_anchors_preset(Control.PRESET_FULL_RECT)
	_tarjeta.alignment = BoxContainer.ALIGNMENT_CENTER
	_tarjeta.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tarjeta.modulate.a = 0.0
	raiz.add_child(_tarjeta)
	_titulo = _etiqueta(_tarjeta, 56, Color(1.0, 0.93, 0.8))
	_titulo.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub = _etiqueta(_tarjeta, 30, Color(0.9, 0.85, 0.78))
	_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_sub.size_flags_horizontal = Control.SIZE_FILL
	get_viewport().size_changed.connect(_ajustar)
	_ajustar()


## Subtítulos y tarjetas con un ancho cómodo de leer en cualquier pantalla (web incluida).
func _ajustar() -> void:
	var w := get_viewport().get_visible_rect().size.x
	var margen: float = max(40.0, (w - 1000.0) / 2.0)
	_caja.offset_left = margen
	_caja.offset_right = -margen
	_caja.offset_bottom = -70.0
	_sub.custom_minimum_size = Vector2(min(900.0, w - 80.0), 0)


func _etiqueta(padre: Node, tam: int, color: Color) -> Label:
	var l := Label.new()
	l.add_theme_font_override("font", FUENTE)
	l.add_theme_font_size_override("font_size", tam)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.8))
	l.add_theme_constant_override("shadow_offset_x", 2)
	l.add_theme_constant_override("shadow_offset_y", 2)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	padre.add_child(l)
	return l


func _fundir_nodo(n: CanvasItem, a: float, dur: float) -> Tween:
	var tw := create_tween()
	tw.tween_property(n, "modulate:a", a, dur)
	return tw


func fundir(a: float, dur := 1.0) -> void:
	var tw := create_tween()
	tw.tween_property(fundido, "color:a", a, dur)
	await tw.finished


func tarjeta(titulo: String, sub: String, segs := 4.0) -> void:
	_titulo.text = titulo
	_sub.text = sub
	await _fundir_nodo(_tarjeta, 1.0, 1.0).finished
	await get_tree().create_timer(segs).timeout
	await _fundir_nodo(_tarjeta, 0.0, 1.0).finished


func decir(quien: String, texto: String, segs := 0.0) -> void:
	if segs <= 0.0:
		segs = clamp(texto.length() * 0.065, 2.5, 9.0)
	_turno += 1
	var turno := _turno
	_quien.text = quien
	_quien.visible = quien != ""
	_texto.text = texto
	_fundir_nodo(_caja, 1.0, 0.3)
	await get_tree().create_timer(segs).timeout
	if turno == _turno:
		_fundir_nodo(_caja, 0.0, 0.5)


func objetivo(texto: String) -> void:
	_objetivo.text = "◆  " + texto if texto != "" else ""
	_objetivo.modulate.a = 0.0
	if texto != "":
		_fundir_nodo(_objetivo, 1.0, 0.8)


func aviso(texto: String) -> void:
	_aviso.text = ("E  ·  " + texto) if texto != "" else ""


func ayuda(texto: String, segs := 10.0) -> void:
	_ayuda.text = texto
	await _fundir_nodo(_ayuda, 1.0, 0.8).finished
	await get_tree().create_timer(segs).timeout
	_fundir_nodo(_ayuda, 0.0, 1.5)


func rebato(visible_: bool, listo := 0.0, progreso := 0.0) -> void:
	_rebato.visible = visible_
	_rebato.listo = listo
	_rebato.progreso = progreso
	_rebato.queue_redraw()


func ocultar_todo(si: bool) -> void:
	for n in [_objetivo, _aviso, _caja, _ayuda, _mira]:
		n.visible = not si
