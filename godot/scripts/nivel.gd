extends Node3D
## La Plata, 25 de mayo de 1809. Arma la ciudad, la luz del atardecer a la noche,
## los faroles, el sonido, el jugador y la historia (director.gd).
##
## Para pruebas, acepta argumentos después de "--":
##   --paso=rebato         empieza en ese paso del guion
##   --hora=0.8            fija la hora (0 = cinco de la tarde, 1 = noche cerrada)
##   --vista=x,y,z,tx,ty,tz  cámara fija mirando a un punto
##   --captura=ruta.png --espera=5   guarda la imagen y sale
##   --sin_ui

const Materiales := preload("res://scripts/materiales.gd")
const Efectos := preload("res://scripts/efectos.gd")
const Jugador := preload("res://scripts/jugador.gd")
const UI := preload("res://scripts/ui.gd")
const Director := preload("res://scripts/director.gd")

# hora, elevación y azimut de la luz (grados), color, energía, energía del cielo de tarde,
# mezcla con el cielo nocturno, luz ambiente, color y densidad de niebla, exposición,
# brillo de ventanas, faroles encendidos (0..1)
const CLAVES := [
	[0.0, 9.0, 292.0, Color(1.0, 0.76, 0.52), 1.6, 1.0, 0.0, 0.9, Color(0.78, 0.63, 0.5), 0.0035, 1.0, 0.06, 0.0],
	[0.3, 2.5, 294.0, Color(1.0, 0.52, 0.3), 0.8, 0.55, 0.0, 0.65, Color(0.6, 0.45, 0.38), 0.005, 1.1, 0.6, 0.5],
	[0.45, -2.0, 294.0, Color(0.7, 0.45, 0.4), 0.0, 0.25, 0.3, 0.42, Color(0.3, 0.27, 0.3), 0.007, 1.25, 1.5, 1.0],
	[0.6, 30.0, 70.0, Color(0.55, 0.62, 0.9), 0.12, 0.15, 0.6, 0.32, Color(0.14, 0.15, 0.2), 0.009, 1.4, 1.9, 1.0],
	[1.0, 40.0, 70.0, Color(0.58, 0.66, 1.0), 0.2, 0.08, 1.0, 0.24, Color(0.05, 0.06, 0.09), 0.011, 1.6, 2.2, 1.0],
]

var ciudad: Node3D
var marcas := {}
var entorno: Environment
var sol: DirectionalLight3D
var cielo: ShaderMaterial
var jugador
var ui
var director
var sonido := {}
var guia: MeshInstance3D
var luces_fuego: Array = []
var hora_fija := false
var args := {}

var calidad := 2
var auto_calidad := true
var _fps_t := 0.0
var _fps_frames := 0
var _t_juego := 0.0

var _faroles: Array = []
var _faroles_on := 0.0
var _tw_hora: Tween

var hora := 0.0:
	set(v):
		hora = v
		_aplicar_hora()


func _ready() -> void:
	args = _leer_args()
	_entradas()
	_ciudad()
	_entorno()
	_faroles_y_props()
	_jugador_ui()
	_sonidos()
	_guia()
	fijar_calidad(int(args.get("calidad", "2")))
	auto_calidad = not args.has("captura")
	hora = 0.0
	director = Director.new()
	director.nivel = self
	add_child(director)
	if args.has("hora"):
		hora = float(args.hora)
		hora_fija = true
	if args.has("fila"):
		# Prueba: personajes en fila (--fila=soldado,zudanez,... --fila_anim=reposo)
		var nombres := String(args.fila).split(",")
		for i in nombres.size():
			var mod: Node3D = load("res://assets/personajes/%s.gltf" % nombres[i]).instantiate()
			add_child(mod)
			mod.position = Vector3(20.0, 0.0, (i - (nombres.size() - 1) / 2.0) * 0.95)
			mod.rotation_degrees.y = -90.0
			var ap: AnimationPlayer = mod.find_child("AnimationPlayer", true, false)
			var anim := String(args.get("fila_anim", "reposo"))
			if ap and ap.has_animation(anim):
				ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR
				ap.play(anim)
				ap.seek(randf() * 2.0)
	if args.has("modelo"):
		# Prueba: coloca un modelo en un punto (--modelo=res://... --modelo_pos=x,y,z,rot_y)
		var mod: Node3D = load(String(args.modelo)).instantiate()
		add_child(mod)
		var v := String(args.get("modelo_pos", "0,0,0,0")).split(",")
		mod.position = Vector3(float(v[0]), float(v[1]), float(v[2]))
		mod.rotation_degrees.y = float(v[3]) if v.size() > 3 else 0.0
		Materiales.aplicar(mod)
		var ap: AnimationPlayer = mod.find_child("AnimationPlayer", true, false)
		if ap and args.has("modelo_anim"):
			var anim := String(args.modelo_anim)
			ap.get_animation(anim).loop_mode = Animation.LOOP_LINEAR
			ap.play(anim)
		if ap:
			print("[animaciones] ", ap.get_animation_list())
	director.iniciar(args.get("paso", "intro"))
	if args.has("captura"):
		_capturar()


func _leer_args() -> Dictionary:
	var r := {}
	for a in OS.get_cmdline_user_args():
		var s := String(a).trim_prefix("--")
		var i := s.find("=")
		if i >= 0:
			r[s.substr(0, i)] = s.substr(i + 1)
		else:
			r[s] = "1"
	return r


func _entradas() -> void:
	var mapa := {
		"adelante": [KEY_W, KEY_UP], "atras": [KEY_S, KEY_DOWN],
		"izquierda": [KEY_A, KEY_LEFT], "derecha": [KEY_D, KEY_RIGHT],
		"correr": [KEY_SHIFT], "interactuar": [KEY_E, KEY_ENTER],
		"pausa": [KEY_ESCAPE], "reiniciar": [KEY_R], "calidad": [KEY_Q],
	}
	for accion in mapa:
		if not InputMap.has_action(accion):
			InputMap.add_action(accion)
		for k in mapa[accion]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k
			InputMap.action_add_event(accion, ev)


# ------------------------------------------------------------------ mundo

func _ciudad() -> void:
	ciudad = load("res://assets/modelos/ciudad_1809.glb").instantiate()
	add_child(ciudad)
	Materiales.aplicar(ciudad)
	for n in ciudad.find_children("*", "Node3D", true, false):
		var nom := String(n.name)
		if nom.begins_with("M_") or nom.begins_with("R_") or nom.begins_with("P_"):
			marcas[nom] = n
		if n is MeshInstance3D and (nom.begins_with("terreno") or nom.begins_with("borde")):
			(n as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func marca(nombre: String) -> Node3D:
	return marcas.get(nombre)


func pos(nombre: String) -> Vector3:
	var m: Node3D = marcas.get(nombre)
	if m == null:
		push_warning("Falta el marcador " + nombre)
		return Vector3.ZERO
	return m.global_position


func _entorno() -> void:
	entorno = Environment.new()
	entorno.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	cielo = ShaderMaterial.new()
	cielo.shader = load("res://shaders/cielo.gdshader")
	cielo.set_shader_parameter("cielo_tarde", load("res://assets/cielos/atardecer.hdr"))
	cielo.set_shader_parameter("cielo_noche", load("res://assets/cielos/noche.hdr"))
	sky.sky_material = cielo
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	entorno.sky = sky
	entorno.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	entorno.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	entorno.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	entorno.tonemap_white = 6.0
	entorno.glow_enabled = true
	entorno.glow_intensity = 0.7
	entorno.glow_bloom = 0.05
	entorno.glow_hdr_threshold = 0.9
	entorno.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	entorno.fog_enabled = true
	entorno.fog_sky_affect = 0.2
	entorno.adjustment_enabled = true
	var we := WorldEnvironment.new()
	we.environment = entorno
	add_child(we)
	sol = DirectionalLight3D.new()
	sol.shadow_enabled = true
	sol.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	sol.directional_shadow_max_distance = 90.0
	sol.shadow_blur = 1.5
	add_child(sol)


func _interpolar(h: float) -> Array:
	h = clamp(h, 0.0, 1.0)
	for i in CLAVES.size() - 1:
		var a: Array = CLAVES[i]
		var b: Array = CLAVES[i + 1]
		if h <= b[0]:
			var t := smoothstep(a[0], b[0], h)
			var r := []
			for k in a.size():
				r.append(lerp(a[k], b[k], t))
			return r
	return CLAVES[-1]


func _aplicar_hora() -> void:
	if entorno == null:
		return
	var v := _interpolar(hora)
	var el := deg_to_rad(v[1])
	var az := deg_to_rad(v[2])
	var hacia := Vector3(sin(az) * cos(el), sin(el), -cos(az) * cos(el))
	sol.look_at_from_position(Vector3.ZERO, -hacia, Vector3.UP)
	sol.light_color = v[3]
	sol.light_energy = v[4]
	sol.visible = v[4] > 0.01
	_sombras()
	cielo.set_shader_parameter("energia_tarde", v[5])
	cielo.set_shader_parameter("mezcla", v[6])
	entorno.ambient_light_energy = v[7]
	entorno.fog_light_color = v[8]
	entorno.fog_density = v[9]
	entorno.tonemap_exposure = v[10]
	entorno.adjustment_saturation = lerp(1.05, 0.82, hora)
	var ventanas: StandardMaterial3D = Materiales.material("ventana_luz")
	if ventanas:
		ventanas.emission_energy_multiplier = v[11]
	_faroles_on = v[12]
	var vidrio: StandardMaterial3D = Materiales.material("vidrio_farol")
	if vidrio:
		vidrio.emission_energy_multiplier = 0.05 + 3.0 * _faroles_on
	for l in _faroles:
		l.set_meta("base", 1.5 * _faroles_on)
		l.visible = _faroles_on > 0.02


## 0 = baja, 1 = media, 2 = alta. En la web, la calidad baja sola si faltan cuadros.
func fijar_calidad(c: int) -> void:
	calidad = clampi(c, 0, 2)
	var vp := get_viewport()
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = [0.6, 0.8, 1.0][calidad]
	vp.msaa_3d = Viewport.MSAA_2X if calidad == 2 else Viewport.MSAA_DISABLED
	if entorno:
		entorno.glow_enabled = calidad > 0
	_sombras()


func _sombras() -> void:
	if sol == null:
		return
	sol.shadow_enabled = calidad > 0 and sol.light_energy > 0.3
	if calidad == 2:
		sol.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
		sol.directional_shadow_max_distance = 90.0
	else:
		sol.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
		sol.directional_shadow_max_distance = 60.0


func _vigilar_fps(delta: float) -> void:
	_t_juego += delta
	if not auto_calidad or calidad == 0 or _t_juego < 8.0 or ui.fundido.color.a > 0.5:
		return
	_fps_t += delta
	_fps_frames += 1
	if _fps_t >= 4.0:
		var fps := _fps_frames / _fps_t
		_fps_t = 0.0
		_fps_frames = 0
		if fps < 27.0:
			fijar_calidad(calidad - 1)
			ui.ayuda("Calidad gráfica: %s (Q para cambiarla)" % ["baja", "media", "alta"][calidad], 4.0)


func fijar_hora(h: float, dur := 0.0) -> void:
	if hora_fija:
		return
	if _tw_hora and _tw_hora.is_valid():
		_tw_hora.kill()
	if dur <= 0.0:
		hora = h
	else:
		_tw_hora = create_tween()
		_tw_hora.tween_property(self, "hora", h, dur)


func _faroles_y_props() -> void:
	var farol_escena: PackedScene = load("res://assets/modelos/farol.glb")
	var candidatos := []
	for nom in marcas:
		if nom.begins_with("P_farol"):
			candidatos.append(marcas[nom])
	# Solo los faroles cerca del recorrido llevan luz real (las demás brillan sin iluminar).
	var recorrido := [Vector3(0, 0, 0), Vector3(27.5, 0, -30), Vector3(27.5, 0, -70), Vector3(27.5, 0, -100)]
	candidatos.sort_custom(func(a, b): return _dist_recorrido(a.global_position, recorrido) < _dist_recorrido(b.global_position, recorrido))
	for i in candidatos.size():
		var m: Node3D = candidatos[i]
		var f: Node3D = farol_escena.instantiate()
		add_child(f)
		f.global_transform = m.global_transform
		Materiales.aplicar(f)
		if i < 14:
			var punto: Node3D = f.find_child("luz", true, false)
			var l := Efectos.luz_fuego(0.0, 8.0)
			l.light_color = Color(1.0, 0.72, 0.4)
			(punto if punto else f).add_child(l)
			_faroles.append(l)
			luces_fuego.append(l)

	var escenas := {
		"barril": ["res://assets/modelos/barril.glb"],
		"cantaro": ["res://assets/props/jug_01/jug_01.gltf", "res://assets/props/ceramic_pot/ceramic_pot.gltf"],
		"banca": ["res://assets/props/painted_wooden_bench/painted_wooden_bench.gltf"],
	}
	for nom in marcas:
		if not nom.begins_with("P_") or nom.begins_with("P_farol"):
			continue
		var tipo := String(nom).split("_")[1]
		if not escenas.has(tipo):
			continue
		var p: Node3D = load(escenas[tipo].pick_random()).instantiate()
		add_child(p)
		p.global_transform = marcas[nom].global_transform
		p.rotate_y(randf_range(-0.4, 0.4))
		Materiales.aplicar(p)


func _dist_recorrido(p: Vector3, puntos: Array) -> float:
	var d := INF
	for q in puntos:
		d = min(d, p.distance_to(q))
	return d


func _jugador_ui() -> void:
	ui = UI.new()
	add_child(ui)
	var capa := CanvasLayer.new()
	capa.layer = 1
	add_child(capa)
	var post := ColorRect.new()
	post.set_anchors_preset(Control.PRESET_FULL_RECT)
	post.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var pm := ShaderMaterial.new()
	pm.shader = load("res://shaders/postproceso.gdshader")
	post.material = pm
	capa.add_child(post)
	jugador = Jugador.new()
	jugador.ui = ui
	add_child(jugador)


func _guia() -> void:
	guia = MeshInstance3D.new()
	var c := CylinderMesh.new()
	c.top_radius = 0.6
	c.bottom_radius = 0.6
	c.height = 30.0
	c.cap_top = false
	c.cap_bottom = false
	c.radial_segments = 16
	guia.mesh = c
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/guia.gdshader")
	guia.material_override = m
	guia.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	guia.visible = false
	add_child(guia)


func mostrar_guia(p: Vector3) -> void:
	guia.global_position = p + Vector3(0, 15.0, 0)
	guia.visible = true


func ocultar_guia() -> void:
	guia.visible = false


# ------------------------------------------------------------------ sonido

func _sonidos() -> void:
	sonido.viento = _bucle("viento", -18.0)
	sonido.tension = _bucle("tension", -60.0)


func _bucle(nombre: String, db: float) -> AudioStreamPlayer:
	var s := AudioStreamPlayer.new()
	var st: AudioStream = load("res://assets/audio/%s.ogg" % nombre)
	if st is AudioStreamOggVorbis:
		st.loop = true
	s.stream = st
	s.volume_db = db
	s.autoplay = true
	add_child(s)
	return s


func bucle_3d(nombre: String, padre: Node3D, db: float, unidad := 10.0) -> AudioStreamPlayer3D:
	var s := AudioStreamPlayer3D.new()
	var st: AudioStream = load("res://assets/audio/%s.ogg" % nombre).duplicate()
	if st is AudioStreamOggVorbis:
		st.loop = true
	s.stream = st
	s.volume_db = db
	s.unit_size = unidad
	s.max_distance = 300.0
	padre.add_child(s)
	s.play()
	return s


func sonar_3d(nombre: String, p: Vector3, db := 0.0, tono := 1.0, unidad := 15.0) -> void:
	var s := AudioStreamPlayer3D.new()
	s.stream = load("res://assets/audio/%s.ogg" % nombre)
	s.volume_db = db
	s.pitch_scale = tono
	s.unit_size = unidad
	s.max_distance = 600.0
	add_child(s)
	s.global_position = p
	s.finished.connect(s.queue_free)
	s.play()


func fundir_sonido(s: Node, db: float, dur: float) -> void:
	if s == null:
		return
	create_tween().tween_property(s, "volume_db", db, dur)


# ------------------------------------------------------------------ ciclo

func _process(delta: float) -> void:
	_vigilar_fps(delta)
	if Input.is_action_just_pressed("calidad"):
		auto_calidad = false
		fijar_calidad((calidad + 2) % 3)
		ui.ayuda("Calidad gráfica: %s" % ["baja", "media", "alta"][calidad], 3.0)
	var t := Time.get_ticks_msec() / 1000.0
	for i in range(luces_fuego.size() - 1, -1, -1):
		var l: OmniLight3D = luces_fuego[i]
		if not is_instance_valid(l):
			luces_fuego.remove_at(i)
			continue
		var f: float = l.get_meta("fase")
		var parpadeo := 0.82 + 0.1 * sin(t * 9.0 + f) + 0.08 * sin(t * 23.0 + f * 1.7)
		l.light_energy = float(l.get_meta("base")) * parpadeo
	if director and director.terminado and Input.is_action_just_pressed("reiniciar"):
		get_tree().reload_current_scene()


func _capturar() -> void:
	if args.has("ventana"):
		# Ventana completa, con interfaz y posproceso.
		await get_tree().create_timer(float(args.get("espera", "5"))).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(String(args.captura))
		print("[captura] ", args.captura)
		get_tree().quit()
		return
	# Imagen de 1280x720 en un SubViewport (el gestor de ventanas no cambia su tamaño).
	var sv := SubViewport.new()
	var res := String(args.get("res", "1280x720")).split("x")
	sv.size = Vector2i(int(res[0]), int(res[1]))
	sv.world_3d = get_viewport().world_3d
	sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	sv.msaa_3d = Viewport.MSAA_2X
	add_child(sv)
	get_viewport().disable_3d = true
	if args.has("sin_sombras"):
		sol.shadow_enabled = false
	if args.has("sin_glow"):
		entorno.glow_enabled = false
	if args.has("sin_msaa"):
		sv.msaa_3d = Viewport.MSAA_DISABLED
	if args.has("sin_niebla"):
		entorno.fog_enabled = false
	var cam := Camera3D.new()
	cam.fov = 72.0
	cam.far = 1500.0
	sv.add_child(cam)
	var t := 0.0
	var espera := float(args.get("espera", "5"))
	while t < espera:
		await get_tree().process_frame
		t += get_process_delta_time()
		if args.has("vista"):
			var v := String(args.vista).split(",")
			cam.look_at_from_position(Vector3(float(v[0]), float(v[1]), float(v[2])), Vector3(float(v[3]), float(v[4]), float(v[5])))
		else:
			cam.global_transform = jugador.camara.global_transform
	await RenderingServer.frame_post_draw
	sv.get_texture().get_image().save_png(String(args.captura))
	print("[captura] %s  fps=%d  llamadas=%d  primitivas=%d  objetos=%d" % [args.captura, Engine.get_frames_per_second(),
		RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
		RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)])
	get_tree().quit()
