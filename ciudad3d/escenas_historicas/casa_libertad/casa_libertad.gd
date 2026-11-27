class_name CasaLibertadMuseo
extends Node3D
## Escena oficial de la Casa de la Libertad (1809) para Ciudad Charcas / Godot 4.7 Compatibility Web.
## - Instancia `casa_libertad.glb` con sus colisiones `-colonly` (escala 1.0).
## - Coloca hasta 5 OmniLight3D cálidas en los marcadores `LUZ_*` (sombra suave opcional solo en la luz principal del Salón).
## - Configura `VisibilityRange` en mobiliario y salas interiores secundarias para mantener > 30 FPS desde la Plaza 25 de Mayo.
## - Registra todos los `POI_*` en el autoload `Interaccion` (`E` / `Enter` / clic) y muestra fichas históricas en un CanvasLayer limpio.

## Transformación exacta en mundo de Sucre alineada al milímetro con la vereda NO de la Plaza 25 de Mayo (M037 / S_PLAZA25).
const POSICION_PLAZA_25 := Vector3(-233.5396, 62.18, 167.4812)
const ROTACION_Y_PLAZA_25 := 0.89151   # rad (51.08°), fachada +Z local apuntando hacia la Plaza (0.7780, 0, 0.6282)

const MAX_LUCES := 5
const CAL := Color("#fbf9f4")
const TINTA := Color("#2b1d16")
const TINTA_SUAVE := Color("#6b5a4e")
const ROJO := Color("#a9432d")
const ORO := Color("#c9a45c")
const MARFIL := Color("#f4ead6")

## Base de datos histórica por marcador `POI_*` (compatible con alias como `POI_ACTA` -> `POI_ACTA_INDEPENDENCIA`).
const FICHAS_POI := {
	"POI_ENTRADA_PORTON": {
		"titulo": "Portada Barroca y Portón de Cedro",
		"subtitulo": "Fachada principal · Siglo XVIII–1809",
		"radio": 2.2,
		"texto": "Portada tallada en piedra arenisca rosada con columnas salomónicas, pináculos en jarrón y el escudo de la Universidad Real y Pontificia de San Francisco Xavier. Su portón de cedro nativo tachonado en bronce da acceso al zaguán empedrado."
	},
	"POI_PATIO_FUENTE": {
		"titulo": "Patio del Claustro Jesuítico",
		"subtitulo": "Arquitectura colonial · Claustro de 5 arcos",
		"radio": 2.0,
		"texto": "Corazón del antiguo Colegio Azul de los jesuitas y luego sede universitaria de Charcas. Sus galerías de arcos de medio punto sobre columnas de piedra rodean la fuente central ochavada y las bancas de estudio."
	},
	"POI_ESTATUA": {
		"titulo": "Monumento a Apiaguaiki Tumpa",
		"subtitulo": "Líder guaraní de Kuruyuki · Claustro Principal",
		"radio": 1.6,
		"texto": "Escultura en bronce oscuro dedicada a Apiaguaiki Tumpa, líder indígena guaraní de la resistencia chaqueña de 1892 (reconocible por su tocado ceremonial de jaguar), en homenaje a la lucha por la tierra y la dignidad de los pueblos originarios."
	},
	"POI_PORTADA_SALON": {
		"titulo": "Ingreso al Aula Magna Universitaria",
		"subtitulo": "Antigua Capilla Doméstica Jesuítica",
		"radio": 1.9,
		"texto": "Eje monumental del claustro hacia la antigua capilla doméstica de la Compañía de Jesús, convertida en Aula Magna de la Academia Carolina donde se formaron los doctores revolucionarios de mayo de 1809."
	},
	"POI_ACTA_INDEPENDENCIA": {
		"titulo": "Acta de la Independencia de Bolivia",
		"subtitulo": "Salón de la Independencia · 6 de agosto de 1825",
		"radio": 1.65,
		"texto": "En este salón, antigua Aula Magna de San Francisco Xavier, la Asamblea Deliberante de las provincias del Alto Perú firmó el Acta de la Independencia el 6 de agosto de 1825, declarando una república soberana bajo la presidencia de José Mariano Serrano."
	},
	"POI_PRESIDIO_BOLIVAR": {
		"titulo": "Testero Presidencial y Altar Cívico",
		"subtitulo": "Retratos de Bolívar, Sucre y Ballivián",
		"radio": 1.75,
		"texto": "Preside el testero el óleo de Simón Bolívar pintado en Lima por José Gil de Castro (1825), flanqueado por los mariscales Antonio José de Sucre (junto a la urna con su espada de Ayacucho) y José Ballivián bajo el artesonado barroco dorado."
	},
	"POI_SALA_MUSEO": {
		"titulo": "Sala de los Guerrilleros de la Independencia",
		"subtitulo": "Juana Azurduy, sables y Republiquetas (1809–1825)",
		"radio": 1.80,
		"texto": "Sala dedicada a los héroes de la guerra de guerrillas altoperuana con acceso directo desde el claustro y hacia el Salón de la Independencia. Preside el retrato y el cofre de madera tallada de la mariscal Juana Azurduy (cubierto con las banderas de Bolivia y Argentina), junto a sables de honor, cañón de montaña, Bandera de Macha y la memoria de Casimiro Olañeta."
	},
	"POI_CANON": {
		"titulo": "Cañón Histórico de Montaña",
		"subtitulo": "Artillería de campaña · Guerra de la Independencia",
		"radio": 1.55,
		"texto": "Pieza de artillería ligera empleada en los valles y quebradas del Alto Perú durante los quince años de combate por la emancipación americana frente a las tropas realistas."
	},
	"POI_BANDERA_BELGRANO": {
		"titulo": "Bandera de Macha y Casimiro Olañeta",
		"subtitulo": "Ejército del Norte · Rincón Conmemorativo",
		"radio": 1.65,
		"texto": "Exhibición del histórico estandarte celeste y blanco de Manuel Belgrano oculto en Titiri (Macha, Potosí) tras Vilcapugio y Ayohuma (1813), junto al pilar conmemorativo dedicado a Casimiro Olañeta y los combatientes altoperuanos."
	},
	"POI_PASILLO_AGUILA": {
		"titulo": "Antesala y Pedestal del Águila Tallada",
		"subtitulo": "Ingreso desde el Claustro · Ala Oeste",
		"radio": 1.65,
		"texto": "Acceso directo desde la galería oeste del claustro hacia el Antiguo Senado. Recibe al visitante el cofre histórico sostenido sobre un pedestal con un águila heráldica tallada en madera de cedro con las alas desplegadas."
	},
	"POI_SALA_BOLIVAR": {
		"titulo": "Salón del Antiguo Senado y Galería de los Presidentes",
		"subtitulo": "Retratos Presidenciales, Bastones de Mando y Busto de Bolívar",
		"radio": 2.10,
		"texto": "Largo salón histórico que albergó sesiones del Senado y hoy conserva la galería de retratos al óleo donados por las familias de los presidentes de Bolivia, vitrinas con bastones de mando presidenciales, un piano de época y, sobre la tarima norte, el busto monumental de Simón Bolívar bajo el Escudo Nacional."
	},
	"POI_SALA_VIRREINAL": {
		"titulo": "Sala Virreinal (Ala Oeste)",
		"subtitulo": "Real Audiencia de Charcas y Mapa de 1776",
		"radio": 1.70,
		"texto": "Acceso tradicional desde el claustro oeste a la sala dedicada a la Real Audiencia de Charcas, mapas de 1776, sillones virreinales de cuero y arte barroco chuquisaqueño (sala anexa cerrada en este recorrido)."
	},
	"POI_SALA_HONOR": {
		"titulo": "Salón de Honor y Archivo Historiográfico",
		"subtitulo": "Ala Este · Siglos XIX–XX",
		"radio": 1.70,
		"texto": "Salón institucional que conserva mobiliario republicano y condecoraciones de la historia constitucional boliviana en Sucre (acceso reservado durante esta visita)."
	},
	"POI_BIBLIOTECA": {
		"titulo": "Biblioteca y Archivo Histórico",
		"subtitulo": "Fondo Documental · Academia Carolina",
		"radio": 1.70,
		"texto": "Custodia volúmenes jurídicos y filosóficos de la Universidad Real y Pontificia de San Francisco Xavier que nutrieron el pensamiento ilustrado del 25 de Mayo de 1809 (sala reservada)."
	}
}

## Alias por si el marcador se consulta sin sufijo largo.
const ALIAS_POI := {
	"POI_ACTA": "POI_ACTA_INDEPENDENCIA",
}

@export var configurar_luces := true
@export var configurar_visibilidad := true
@export var registrar_pois := true
@export var sombra_salon_principal := false

@onready var glb_raiz: Node3D = get_node_or_null("CasaLibertad_GLB")

var luces_creadas: Array[OmniLight3D] = []
var areas_poi: Dictionary = {}              # id_registro -> {area, poi, radio}
var _ids_activos: Array[String] = []
var _id_mostrado := ""
var _panel_abierto := false
var _hud: CanvasLayer
var _banner: PanelContainer
var _banner_lbl: Label
var _ultimo_cercano := ""
var _ficha: PanelContainer
var _ficha_titulo: Label
var _ficha_sub: Label
var _ficha_texto: Label
var _ui_construida := false

func _ready() -> void:
	if glb_raiz == null:
		for c in get_children():
			if c is Node3D:
				glb_raiz = c
				break
	if glb_raiz == null:
		push_warning("CasaLibertadMuseo: no se encontró el nodo hijo CasaLibertad_GLB.")
		return

	_optimizar_materiales_y_visibilidad()
	if configurar_luces:
		_instanciar_luces()
	if registrar_pois:
		_crear_hud_poi()
		_registrar_zonas_poi()
		Interaccion.entro.connect(_on_interaccion_entro)
		Interaccion.salio.connect(_on_interaccion_salio)
		Interaccion.accion.connect(_on_interaccion_accion)

func _exit_tree() -> void:
	for id_reg in areas_poi.keys():
		Interaccion.quitar(id_reg)
	areas_poi.clear()

func _process(_dt: float) -> void:
	if _ids_activos.size() > 1 and not _panel_abierto:
		var c := _poi_mas_cercano()
		if c != _ultimo_cercano:
			_actualizar_banner()

func _unhandled_input(ev: InputEvent) -> void:
	if _panel_abierto and ev is InputEventKey and ev.pressed and not ev.echo:
		if ev.physical_keycode == KEY_ESCAPE:
			_cerrar_ficha()
			get_viewport().set_input_as_handled()

## Devuelve coordenadas de alineación exactas frente a la Plaza 25 de Mayo.
static func transform_en_plaza_25() -> Transform3D:
	return Transform3D(Basis(Vector3.UP, ROTACION_Y_PLAZA_25), POSICION_PLAZA_25)

static func _empieza_con(texto: String, prefijos: Array[String]) -> bool:
	for p in prefijos:
		if texto.begins_with(p):
			return true
	return false

## Recorre todas las MeshInstance3D: ajusta transparencia simple WebGL y configura VisibilityRange.
func _optimizar_materiales_y_visibilidad() -> void:
	var pilas: Array[Node] = [glb_raiz]
	while not pilas.is_empty():
		var n: Node = pilas.pop_back()
		for h in n.get_children():
			pilas.append(h)
		if not (n is MeshInstance3D):
			continue
		var mi := n as MeshInstance3D
		var nom := String(mi.name)

		# Materiales WebGL: asegurar vidrio simple y evitar sombras innecesarias en vidrio/suelo
		if mi.mesh != null:
			for s in range(mi.mesh.get_surface_count()):
				var mat := mi.get_active_material(s)
				if mat is StandardMaterial3D:
					var sm := mat as StandardMaterial3D
					if "vidrio" in sm.resource_name.to_lower() or sm.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA:
						sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
						sm.cull_mode = BaseMaterial3D.CULL_BACK
						if sm.roughness < 0.08:
							sm.roughness = 0.06
		if nom.begins_with("CL_Acera"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

		if not configurar_visibilidad:
			continue

		# VisibilityRange: oculta automáticamente mobiliario y salas secundarias cuando el jugador está en la Plaza
		var nom_malla := String(mi.mesh.resource_name) if mi.mesh != null else ""
		var rango := 0.0
		var margen := 4.0
		if _empieza_con(nom, ["CL_Sala_Guerrilleros", "CL_Sala_Bolivar"]):
			rango = 48.0
			margen = 5.0
		elif _empieza_con(nom, ["CL_Estatua_Flechero", "CL_Busto_Bolivar", "CL_Arana"]) or nom_malla.begins_with("M_Arana_Cristal"):
			rango = 46.0
			margen = 4.0
		elif _empieza_con(nom, ["CL_Silla", "CL_Escano", "CL_Sitial", "CL_Banca", "CL_Maceta"]) or _empieza_con(nom_malla, ["M_Silla_Presidio", "M_Escano_Inf", "M_Sitial_Sup", "M_Banca_Patio", "M_Maceta_Patio"]):
			rango = 40.0
			margen = 4.0
		elif nom.begins_with("CL_Salon_Arquitectura"):
			rango = 64.0
			margen = 6.0

		if rango > 0.0:
			mi.visibility_range_begin = 0.0
			mi.visibility_range_end = rango
			mi.visibility_range_end_margin = margen
			mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED

## Coloca hasta 5 OmniLight3D cálidas en los marcadores LUZ_* del .glb (máx. WebGL).
func _instanciar_luces() -> void:
	luces_creadas.clear()
	var pilas: Array[Node] = [glb_raiz]
	var marcadores: Array[Node3D] = []
	while not pilas.is_empty():
		var n: Node = pilas.pop_back()
		for h in n.get_children():
			pilas.append(h)
		if n is Node3D and n.name.begins_with("LUZ_"):
			marcadores.append(n as Node3D)

	marcadores.sort_custom(func(a, b): return a.name < b.name)
	for m in marcadores:
		if luces_creadas.size() >= MAX_LUCES:
			break
		var luz := OmniLight3D.new()
		luz.name = "Omni_" + m.name
		luz.light_color = Color(1.0, 0.87, 0.67)
		luz.omni_attenuation = 1.3
		luz.distance_fade_enabled = true
		luz.distance_fade_begin = 55.0
		luz.distance_fade_length = 12.0

		var es_salon_principal := (m.name == "LUZ_SALON_ARANA_02")
		if m.name == "LUZ_ZAGUAN_01":
			luz.light_energy = 1.8
			luz.omni_range = 11.5
		elif "SALON" in m.name:
			luz.light_energy = 2.7 if es_salon_principal else 2.3
			luz.omni_range = 18.0
		elif "GUERRILLEROS" in m.name:
			luz.light_energy = 2.4
			luz.omni_range = 16.0
		else:
			luz.light_energy = 2.6
			luz.omni_range = 16.5

		# En WebGL Compatibility las OmniLight3D van sin sombra, salvo opcionalmente la luz principal del Salón en PC.
		luz.shadow_enabled = sombra_salon_principal and es_salon_principal and not OS.has_feature("mobile") and not OS.has_feature("web")
		if luz.shadow_enabled:
			luz.shadow_bias = 0.08
			luz.shadow_blur = 2.0

		m.add_child(luz)
		luces_creadas.append(luz)

func fijar_modo_noche(es_noche: bool) -> void:
	var factor := 1.28 if es_noche else 1.0
	for luz in luces_creadas:
		var base := 1.8 if "ZAGUAN" in luz.name else (2.7 if "ARANA_02" in luz.name else 2.4)
		luz.light_energy = base * factor

## Registra todos los marcadores POI_* del .glb en el autoload Interaccion (máscara 8 = Jugador).
func _registrar_zonas_poi() -> void:
	var pilas: Array[Node] = [glb_raiz]
	while not pilas.is_empty():
		var n: Node = pilas.pop_back()
		for h in n.get_children():
			pilas.append(h)
		if not (n is Node3D and n.name.begins_with("POI_")):
			continue
		var poi_node := n as Node3D
		var clave := String(poi_node.name)
		if ALIAS_POI.has(clave):
			clave = ALIAS_POI[clave]
		var meta: Dictionary = FICHAS_POI.get(clave, {
			"titulo": clave.replace("POI_", "").replace("_", " ").capitalize(),
			"subtitulo": "Casa de la Libertad · Sucre",
			"radio": 2.2,
			"texto": "Espacio histórico del Museo Casa de la Libertad (antigua Universidad de San Francisco Xavier)."
		})
		var id_reg := "cl:" + poi_node.name
		var area := Area3D.new()
		area.name = "Zona_" + poi_node.name
		area.collision_layer = 0
		area.collision_mask = 8
		area.monitorable = false

		var cs := CollisionShape3D.new()
		var cyl := CylinderShape3D.new()
		cyl.radius = float(meta.get("radio", 2.2))
		cyl.height = 3.2
		cs.shape = cyl
		cs.position = Vector3(0.0, -0.5, 0.0)
		area.add_child(cs)
		poi_node.add_child(area)

		areas_poi[id_reg] = {"area": area, "poi": poi_node, "clave": clave, "meta": meta}
		Interaccion.registrar(id_reg, area)

func _poi_mas_cercano() -> String:
	if _ids_activos.is_empty():
		return ""
	if _ids_activos.size() == 1:
		return _ids_activos[0]
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return _ids_activos[-1]
	var mejor := _ids_activos[-1]
	var mejor_d := INF
	for id_reg in _ids_activos:
		var info: Dictionary = areas_poi.get(id_reg, {})
		if info.is_empty():
			continue
		var d: float = (info["poi"] as Node3D).global_position.distance_squared_to(cam.global_position)
		if d < mejor_d:
			mejor_d = d
			mejor = id_reg
	return mejor

func _on_interaccion_entro(id: String) -> void:
	if not areas_poi.has(id):
		return
	if not _ids_activos.has(id):
		_ids_activos.append(id)
	_actualizar_banner()

func _on_interaccion_salio(id: String) -> void:
	if _ids_activos.has(id):
		_ids_activos.erase(id)
	if id == _id_mostrado and _panel_abierto:
		_cerrar_ficha()
	_actualizar_banner()

func _on_interaccion_accion(id: String) -> void:
	if not areas_poi.has(id):
		return
	var elegido := _poi_mas_cercano()
	if elegido == "":
		elegido = id
	if _panel_abierto and _id_mostrado == elegido:
		_cerrar_ficha()
	else:
		_abrir_ficha(elegido)

func _actualizar_banner() -> void:
	if not _ui_construida:
		return
	var cercano := _poi_mas_cercano()
	_ultimo_cercano = cercano
	if cercano == "":
		_banner.visible = false
		return
	var info: Dictionary = areas_poi[cercano]
	var titulo: String = info["meta"]["titulo"]
	_banner_lbl.text = "%s  ·  Presiona [E] para leer" % titulo
	_banner.visible = not _panel_abierto
	_banner.reset_size()
	var vp := get_viewport().get_visible_rect().size
	_banner.position = Vector2((vp.x - _banner.size.x) * 0.5, vp.y - _banner.size.y - 26.0)

func _abrir_ficha(id_reg: String) -> void:
	var info: Dictionary = areas_poi[id_reg]
	var meta: Dictionary = info["meta"]
	_id_mostrado = id_reg
	_panel_abierto = true
	_ficha_titulo.text = meta["titulo"]
	_ficha_sub.text = meta["subtitulo"]
	_ficha_texto.text = meta["texto"]
	_ficha.visible = true
	_banner.visible = false
	_ficha.reset_size()
	var vp := get_viewport().get_visible_rect().size
	_ficha.position = Vector2((vp.x - _ficha.size.x) * 0.5, vp.y - _ficha.size.y - 28.0)

func _cerrar_ficha() -> void:
	_panel_abierto = false
	_id_mostrado = ""
	if _ficha != null:
		_ficha.visible = false
	_actualizar_banner()

# --------------------------------------------------------------------------- HUD COLONIAL DE FICHAS POI_*
func _estilo_tarjeta(borde_top := 3) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(CAL, 0.96)
	sb.set_corner_radius_all(12)
	sb.border_width_top = borde_top
	sb.border_width_bottom = 1
	sb.border_width_left = 1
	sb.border_width_right = 1
	sb.border_color = ROJO
	sb.shadow_color = Color(0.15, 0.10, 0.08, 0.30)
	sb.shadow_size = 12
	sb.content_margin_left = 20
	sb.content_margin_right = 20
	sb.content_margin_top = 14
	sb.content_margin_bottom = 14
	return sb

func _crear_hud_poi() -> void:
	_hud = CanvasLayer.new()
	_hud.name = "CasaLibertadHUD"
	_hud.layer = 15
	add_child(_hud)

	# Banner inferior de proximidad (clicable y con tecla E)
	_banner = PanelContainer.new()
	_banner.add_theme_stylebox_override("panel", _estilo_tarjeta(3))
	_banner.visible = false
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 12)
	_banner_lbl = Label.new()
	_banner_lbl.add_theme_font_size_override("font_size", 18)
	_banner_lbl.add_theme_color_override("font_color", TINTA)
	var btn_abrir := Button.new()
	btn_abrir.text = "E · Abrir"
	btn_abrir.add_theme_font_size_override("font_size", 16)
	var st_btn := _estilo_tarjeta(0)
	st_btn.bg_color = ROJO
	st_btn.border_width_bottom = 0
	st_btn.border_width_left = 0
	st_btn.border_width_right = 0
	st_btn.content_margin_left = 14
	st_btn.content_margin_right = 14
	st_btn.content_margin_top = 6
	st_btn.content_margin_bottom = 6
	for e in ["normal", "hover", "focus", "pressed"]:
		btn_abrir.add_theme_stylebox_override(e, st_btn)
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		btn_abrir.add_theme_color_override(c, Color.WHITE)
	btn_abrir.pressed.connect(func(): Interaccion.usar())
	hb.add_child(_banner_lbl)
	hb.add_child(btn_abrir)
	_banner.add_child(hb)
	_hud.add_child(_banner)

	# Tarjeta de ficha histórica
	_ficha = PanelContainer.new()
	_ficha.custom_minimum_size = Vector2(560, 0)
	_ficha.add_theme_stylebox_override("panel", _estilo_tarjeta(4))
	_ficha.visible = false

	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 8)

	var top_bar := HBoxContainer.new()
	_ficha_titulo = Label.new()
	_ficha_titulo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_ficha_titulo.add_theme_font_size_override("font_size", 24)
	_ficha_titulo.add_theme_color_override("font_color", ROJO)
	var serif := SystemFont.new()
	serif.font_names = PackedStringArray(["Georgia", "Noto Serif", "serif"])
	_ficha_titulo.add_theme_font_override("font", serif)

	var btn_cerrar := Button.new()
	btn_cerrar.text = "Cerrar [E]"
	btn_cerrar.add_theme_font_size_override("font_size", 15)
	for e in ["normal", "hover", "focus", "pressed"]:
		btn_cerrar.add_theme_stylebox_override(e, st_btn)
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		btn_cerrar.add_theme_color_override(c, Color.WHITE)
	btn_cerrar.pressed.connect(_cerrar_ficha)

	top_bar.add_child(_ficha_titulo)
	top_bar.add_child(btn_cerrar)

	_ficha_sub = Label.new()
	_ficha_sub.add_theme_font_size_override("font_size", 15)
	_ficha_sub.add_theme_color_override("font_color", TINTA_SUAVE)

	_ficha_texto = Label.new()
	_ficha_texto.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_ficha_texto.custom_minimum_size = Vector2(520, 0)
	_ficha_texto.add_theme_font_size_override("font_size", 18)
	_ficha_texto.add_theme_color_override("font_color", TINTA)

	vb.add_child(top_bar)
	vb.add_child(_ficha_sub)
	vb.add_child(_ficha_texto)
	_ficha.add_child(vb)
	_hud.add_child(_ficha)
	_ui_construida = true
