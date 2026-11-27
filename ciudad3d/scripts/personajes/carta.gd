class_name Carta
extends CanvasLayer
## La interfaz de los encuentros (propuesta "Carta de 1809", ui_ideas/encuentros_claude/, estilo [data-estilo="carta"]):
## el aviso "Presiona I para interactuar" y la carta: papel de época, camafeo ovalado con el rostro de quien habla,
## nombre, la frase que se escribe sola, menú y sello de lacre al final. Sin más adornos (pedido del usuario, 2026-11-26:
## nada de etiquetas de tipo ni fuentes en la carta; las fuentes quedan en los guiones).
## La maneja encuentros.gd: decir() una frase, menu() las opciones; emite 'siguiente', 'elegido' y 'cerrar'.

signal siguiente                      # terminó la frase (al acabar su audio o su tiempo de lectura) o el jugador la adelantó
signal elegido(indice: int)           # opción del menú (-1: despedirse)
signal tocado_aviso                   # tocó el aviso (celular)

const PAPEL := preload("res://personajes/ui/papel.png")
const SELLO := preload("res://personajes/ui/sello.png")
const CRONISTA := preload("res://personajes/ui/cronista.png")
const NORMAL := preload("res://personajes/ui/fuentes/CormorantGaramond_wght.ttf")
const CURSIVA := preload("res://personajes/ui/fuentes/CormorantGaramond-Italic_wght.ttf")
const TINTA := Color("#34230f")
const TINTA_NOMBRE := Color("#7a2a17")
const TINTA_SUAVE := Color("#7d6a4c")
const ORO := Color("#f2c14e")
const MS_LETRA := 0.026
const MS_PAUSA := 0.17
const LECTURA_BASE := 2.6           # s que queda la frase completa antes de pasar sola (+ 28 ms por letra), como la maqueta
const LECTURA_LETRA := 0.028
const PAUSA_TRAS_VOZ := 0.6         # s de silencio entre el fin de un audio y la frase siguiente
const ESCRITURA_VOZ := 0.85         # con voz, el texto termina de escribirse en este tramo del audio

var abierta := false
var _raiz: Control
var _aviso: Button
var _carta: Control
var _papel: TextureRect
var _camafeo: TextureRect
var _mat_camafeo: ShaderMaterial
var _nombre: Label
var _linea: Label
var _menu: HBoxContainer
var _sello: TextureRect
var _texto := ""
var _letras := 0.0
var _escribiendo := false
var _espera := 0.0
var _opciones := 0
var _leyendo := -1.0                  # cuenta atrás de lectura de la frase completa (−1: no corre)
var voz: Voz                          # las voces de las frases (ElevenLabs): la carta sigue su ritmo
var _con_voz := false                 # la frase actual suena: pasa a la siguiente cuando el audio termina
var _ms_letra := MS_LETRA
var _letra_base := 20                 # tamaño de letra de la frase según la pantalla (_acomodar); _encajar lo achica si no cabe
var _tope_voz := 0.0                  # respaldo: si el audio no avanza (navegador sin permiso de sonido), pasa igual
var _t := 0.0
var _tactil := DisplayServer.is_touchscreen_available()

func _ready() -> void:
	layer = 20
	_raiz = Control.new()
	_raiz.set_anchors_preset(Control.PRESET_FULL_RECT)
	_raiz.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_raiz)
	voz = Voz.new()
	voz.name = "Voz"
	voz.terminada.connect(_voz_terminada)
	add_child(voz)
	_crear_aviso()
	_crear_carta()
	get_viewport().size_changed.connect(_acomodar)
	_acomodar()

# ------------------------------------------------------------------------------------------------- fuentes
func _fuente(cursiva: bool, peso: int) -> FontVariation:
	var f := FontVariation.new()
	f.base_font = CURSIVA if cursiva else NORMAL
	f.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): peso}
	return f

# ------------------------------------------------------------------------------------------------- aviso
func _crear_aviso() -> void:
	_aviso = Button.new()
	_aviso.flat = true
	_aviso.focus_mode = Control.FOCUS_NONE
	_aviso.mouse_filter = Control.MOUSE_FILTER_STOP if _tactil else Control.MOUSE_FILTER_IGNORE
	var vacio := StyleBoxEmpty.new()
	for s in ["normal", "hover", "pressed", "focus", "disabled"]:
		_aviso.add_theme_stylebox_override(s, vacio)
	if _tactil:
		var caja := StyleBoxFlat.new()
		caja.bg_color = Color(0.08, 0.06, 0.04, 0.55)
		caja.set_corner_radius_all(28)
		caja.content_margin_left = 26
		caja.content_margin_right = 26
		caja.content_margin_top = 10
		caja.content_margin_bottom = 12
		caja.border_color = Color(ORO, 0.7)
		caja.set_border_width_all(2)
		_aviso.add_theme_stylebox_override("normal", caja)
		_aviso.add_theme_stylebox_override("pressed", caja)
	_aviso.add_theme_font_override("font", _fuente(false, 600))
	_aviso.add_theme_color_override("font_color", Color("#f6efe2"))
	_aviso.add_theme_color_override("font_hover_color", Color("#f6efe2"))
	_aviso.add_theme_color_override("font_pressed_color", ORO)
	_aviso.add_theme_constant_override("outline_size", 6)
	_aviso.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.55))
	_aviso.visible = false
	_aviso.modulate.a = 0.0
	_aviso.pressed.connect(func(): tocado_aviso.emit())
	_raiz.add_child(_aviso)

## Muestra el aviso ("" lo oculta). En la PC: "Presiona I para interactuar"; en el celular, un botón.
func avisar(nombre_conocido: String, mostrar: bool) -> void:
	if mostrar and not abierta:
		if _tactil:
			_aviso.text = "Hablar con " + nombre_conocido if nombre_conocido != "" else "Toca para interactuar"
		else:
			_aviso.text = ("Presiona I para hablar con " + nombre_conocido) if nombre_conocido != "" else "Presiona I para interactuar"
		_aviso.visible = true
	var objetivo := 1.0 if mostrar and not abierta else 0.0
	var tw := create_tween()
	tw.tween_property(_aviso, "modulate:a", objetivo, 0.2)
	if objetivo == 0.0:
		tw.tween_callback(func(): _aviso.visible = _aviso.modulate.a > 0.01)
	_acomodar()

# ------------------------------------------------------------------------------------------------- carta
func _crear_carta() -> void:
	_carta = Control.new()
	_carta.mouse_filter = Control.MOUSE_FILTER_STOP
	_carta.visible = false
	_carta.gui_input.connect(_toque)
	_carta.pivot_offset = Vector2.ZERO
	_raiz.add_child(_carta)

	_papel = TextureRect.new()
	_papel.texture = PAPEL
	_papel.stretch_mode = TextureRect.STRETCH_SCALE
	_papel.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_papel.set_anchors_preset(Control.PRESET_FULL_RECT)
	_papel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_carta.add_child(_papel)

	_nombre = Label.new()
	_nombre.add_theme_font_override("font", _fuente(true, 700))
	_nombre.add_theme_color_override("font_color", TINTA_NOMBRE)
	_carta.add_child(_nombre)


	_linea = Label.new()
	_linea.add_theme_font_override("font", _fuente(false, 500))
	_linea.add_theme_color_override("font_color", TINTA)
	_linea.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_linea.visible_characters_behavior = TextServer.VC_CHARS_AFTER_SHAPING  # lo que falta escribir ya ocupa su lugar
	_linea.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	_carta.add_child(_linea)



	_menu = HBoxContainer.new()
	_menu.visible = false
	_carta.add_child(_menu)

	_camafeo = TextureRect.new()
	_camafeo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_camafeo.stretch_mode = TextureRect.STRETCH_SCALE
	_camafeo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mat_camafeo = ShaderMaterial.new()
	_mat_camafeo.shader = preload("res://shaders/camafeo.gdshader")
	_camafeo.material = _mat_camafeo
	_camafeo.texture = CRONISTA
	_carta.add_child(_camafeo)

	_sello = TextureRect.new()
	_sello.texture = SELLO
	_sello.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_sello.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_sello.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_sello.visible = false
	_carta.add_child(_sello)

func _acomodar() -> void:
	var tam := get_viewport().get_visible_rect().size
	# como el CSS: ancho min(92 % del ancho, 1,52 × alto), alto 23 % (32 % en pantallas bajas de celular)
	var alto := maxf(tam.y * (0.32 if tam.y < 560.0 else 0.23), 150.0)
	var ancho := minf(tam.x * 0.92, maxf(tam.y * 1.52, alto * 4.2))
	_carta.size = Vector2(ancho, alto)
	_carta.position = Vector2((tam.x - ancho) * 0.5, tam.y - alto - tam.y * 0.045)
	_carta.pivot_offset = _carta.size * 0.5
	_carta.rotation = deg_to_rad(-0.35)
	var t_texto := clampf(tam.y * 0.0335, 15.0, 27.0) * 1.08
	var t_nombre := clampf(tam.y * 0.0255, 12.0, 20.0) * 1.45
	# camafeo: 0,91 × 1,17 del alto de la carta, asomado por arriba a la izquierda
	_camafeo.size = Vector2(alto * 0.91, alto * 1.17)
	_camafeo.position = Vector2(-alto * 0.04, -alto * 0.26)
	_camafeo.pivot_offset = _camafeo.size * 0.5
	_camafeo.rotation = deg_to_rad(-2.0)
	_mat_camafeo.set_shader_parameter("aspecto", _camafeo.size.x / _camafeo.size.y)
	var izq := alto * 1.09
	var der := alto * 0.32
	_nombre.position = Vector2(izq, alto * 0.13)
	_nombre.add_theme_font_size_override("font_size", int(t_nombre))
	var arriba := alto * 0.13 + t_nombre * 1.25
	_linea.position = Vector2(izq, arriba)
	_linea.size = Vector2(ancho - izq - der, alto * 0.9 - arriba)     # hasta el borde de abajo del papel, con margen
	_letra_base = int(t_texto)
	_encajar()
	_menu.add_theme_constant_override("separation", int(t_texto * 1.4))
	_menu.position = Vector2(izq, alto - alto * 0.12 - t_texto * 1.25)
	for b in _menu.get_children():
		(b as Control).add_theme_font_size_override("font_size", int(t_texto * 0.95))
	_sello.size = Vector2(alto * 0.36, alto * 0.36)
	_sello.position = Vector2(ancho - alto * 0.24, alto - alto * 0.26)
	_sello.pivot_offset = _sello.size * 0.5
	_aviso.add_theme_font_size_override("font_size", int(clampf(tam.y * 0.032, 18.0, 30.0)))
	_aviso.reset_size()
	_aviso.position = Vector2((tam.x - _aviso.size.x) * 0.5, tam.y * 0.74)

# ------------------------------------------------------------------------------------------------- uso
func abrir() -> void:
	abierta = true
	avisar("", false)
	_carta.visible = true
	_sello.visible = false
	_menu.visible = false
	_carta.modulate.a = 0.0
	var y := _carta.position.y
	_carta.position.y = y + 40.0
	var tw := create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tw.tween_property(_carta, "modulate:a", 1.0, 0.35)
	tw.tween_property(_carta, "position:y", y, 0.45)

## Sella y cierra (await).
func cerrar() -> void:
	_callar()
	_menu.visible = false
	await _poner_sello()
	var tw := create_tween().set_parallel()
	tw.tween_property(_carta, "modulate:a", 0.0, 0.3).set_delay(0.35)
	tw.tween_property(_carta, "position:y", _carta.position.y + 30.0, 0.3).set_delay(0.35)
	await tw.finished
	_carta.visible = false
	abierta = false
	_acomodar()

func _poner_sello() -> void:
	if _sello.visible:
		return
	_sello.visible = true
	_sello.scale = Vector2(1.8, 1.8)
	_sello.modulate.a = 0.0
	var tw := create_tween().set_parallel().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(_sello, "scale", Vector2.ONE, 0.3)
	tw.tween_property(_sello, "modulate:a", 1.0, 0.15)
	await tw.finished

## Una frase: quien = {nombre, retrato (Texture2D o null = cronista)}; paso = el del guion (voz, av, dur). Sin voz, la
## frase pasa sola tras su tiempo de lectura; con voz, se escribe al ritmo del audio y la carta pasa cuando termina.
func decir(quien: Dictionary, texto: String, paso: Dictionary = {}) -> void:
	_menu.visible = false
	_callar()
	_con_voz = voz.tocar(paso)
	_ms_letra = MS_LETRA
	if _con_voz:
		var dur := float(paso.get("dur", texto.length() * 0.065))
		_ms_letra = clampf(dur * ESCRITURA_VOZ / maxf(texto.length(), 1.0), 0.012, 0.09)
		_tope_voz = dur + 2.5             # margen para que el audio arranque (se va bajando mientras suena)
	var cronista: bool = quien.get("retrato") == null
	_nombre.text = quien.get("nombre", "")
	var tex: Texture2D = CRONISTA if cronista else quien["retrato"]
	if _camafeo.texture != tex:
		_camafeo.texture = tex
		_camafeo.scale = Vector2(0.94, 0.94)
		create_tween().tween_property(_camafeo, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_mat_camafeo.set_shader_parameter("cronista", cronista)
	_texto = texto
	_linea.text = texto
	_encajar()
	_linea.visible_characters = 0
	_letras = 0.0
	_espera = 0.0 if _con_voz else 0.38
	_escribiendo = true
	_leyendo = -1.0

func _voz_terminada() -> void:
	if _con_voz and not _escribiendo and not _menu.visible:
		_leyendo = PAUSA_TRAS_VOZ
	# si el texto aún se escribe, _completar() pondrá la pausa al terminar

func _callar() -> void:
	_con_voz = false
	voz.callar()

## Opciones escritas al pie de la carta (enlaces en tinta). El último es siempre "Despedirse".
func menu(opciones: Array) -> void:
	for b in _menu.get_children():
		b.queue_free()
	_opciones = opciones.size()
	for i in opciones.size():
		var b := LinkButton.new()
		b.text = ("%d · " % (i + 1) if not _tactil else "") + str(opciones[i])
		b.underline = LinkButton.UNDERLINE_MODE_ALWAYS
		b.focus_mode = Control.FOCUS_NONE
		b.add_theme_font_override("font", _fuente(true, 700))
		b.add_theme_color_override("font_color", TINTA_NOMBRE)
		b.add_theme_color_override("font_hover_color", Color("#b0412a"))
		b.add_theme_color_override("font_pressed_color", TINTA)
		b.pressed.connect(func(): elegido.emit(i))
		_menu.add_child(b)
	_menu.visible = true
	_leyendo = -1.0
	_poner_sello()
	_acomodar()

## La frase entera tiene que caber en la carta: se achica la letra (hasta un 62 %) hasta que su alto entra en el renglón.
func _encajar() -> void:
	var f := _linea.get_theme_font("font")
	var ancho := _linea.size.x
	var alto := _linea.size.y
	var t := _letra_base
	var minimo := int(_letra_base * 0.62)
	while t > minimo and f != null and ancho > 0.0:
		var h := f.get_multiline_string_size(_texto, HORIZONTAL_ALIGNMENT_LEFT, ancho, t, -1, TextServer.BREAK_MANDATORY | TextServer.BREAK_WORD_BOUND | TextServer.BREAK_ADAPTIVE).y
		if h * 1.08 <= alto:                # + el interlineado del Label
			break
		t -= 1
	_linea.add_theme_font_size_override("font_size", t)

func _completar() -> bool:
	if _escribiendo:
		_escribiendo = false
		_linea.visible_characters = -1
		if _con_voz:
			_leyendo = -1.0 if voz.sonando() else PAUSA_TRAS_VOZ   # la pasa el fin del audio
		else:
			_leyendo = LECTURA_BASE + _texto.length() * LECTURA_LETRA
		return true
	return false

## Un toque: si se está escribiendo, la completa (la voz sigue); si no, corta la voz y pasa a la siguiente.
func _adelantar() -> void:
	if _menu.visible:
		return
	if not _completar():
		_leyendo = -1.0
		_callar()
		siguiente.emit()

func _toque(ev: InputEvent) -> void:
	if (ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT) or (ev is InputEventScreenTouch and ev.pressed):
		_adelantar()
		_carta.accept_event()

func _unhandled_input(ev: InputEvent) -> void:
	if not abierta or not (ev is InputEventKey) or not ev.pressed or ev.echo:
		return
	var k: Key = ev.physical_keycode
	if k in [KEY_I, KEY_SPACE, KEY_ENTER, KEY_KP_ENTER]:
		_adelantar()
	elif k == KEY_ESCAPE:
		elegido.emit(-1)
	elif _menu.visible and k >= KEY_1 and k < KEY_1 + _opciones:
		elegido.emit(k - KEY_1)
	else:
		return
	get_viewport().set_input_as_handled()

func _process(dt: float) -> void:
	_t += dt
	if _con_voz and _leyendo < 0.0 and not _menu.visible:
		_tope_voz -= dt
		if _tope_voz < 0.0 and not _escribiendo:
			_callar()
			_leyendo = PAUSA_TRAS_VOZ
	if _leyendo >= 0.0 and not _menu.visible:
		_leyendo -= dt
		if _leyendo < 0.0:
			_leyendo = -1.0
			siguiente.emit()                  # la narración sigue sola, sin esperar al jugador
	if not _escribiendo:
		return
	if _espera > 0.0:
		_espera -= dt
		return
	_letras += dt / _ms_letra
	var n := int(_letras)
	if n >= _texto.length():
		_completar()
		return
	if n > _linea.visible_characters:
		_linea.visible_characters = n
		if not _con_voz and ",.;:?!…".contains(_texto[n - 1]):   # con voz manda el ritmo del audio
			_espera = MS_PAUSA
