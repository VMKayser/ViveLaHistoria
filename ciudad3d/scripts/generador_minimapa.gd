class_name GeneradorMinimapa
extends Node
## Imagen cenital de la ciudad para el minimapa (antes la hacía el visor three.js). Se usa desde el escritorio:
##   SUCRE_MINIMAPA=1 godot --path ciudad3d   (o npm run ciudad:minimapa)
## Recorre el área LIMITES en mosaicos: en cada uno carga la ciudad alrededor, la fotografía desde arriba con una cámara
## ortográfica (norte arriba, de día, sin niebla ni sombras) y la pega en la imagen final. Escribe texturas/minimapa.webp
## (la usa el minimapa del APK, scripts/minimapa.gd) y datos/minimapa.json con los límites (la web lo copia de ahí).

const LIMITES := Minimapa.LIMITES       # x0, z0, x1, z1 (m)
const PX_POR_METRO := 2048.0 / 900.0    # 2048 px de ancho para los 900 m de este a oeste
const LADO_PX := 512                    # mosaico

var ciudad: Ciudad
var ocultar: Array[Node3D] = []

func _ready() -> void:
	_generar()

func _generar() -> void:
	while not ciudad.listo:
		await get_tree().process_frame
	for n in ocultar:
		n.visible = false
	Hora.aplicar("dia")
	RenderingServer.global_shader_parameter_set("atm_niebla_d", Vector2(1e6, 2e6))
	var ancho_m := LIMITES.z - LIMITES.x
	var alto_m := LIMITES.w - LIMITES.y
	var ancho := int(round(ancho_m * PX_POR_METRO))
	var alto := int(round(alto_m * PX_POR_METRO))
	var lado_m := LADO_PX / PX_POR_METRO
	var final := Image.create(ancho, alto, false, Image.FORMAT_RGB8)

	var vista := SubViewport.new()
	vista.size = Vector2i(LADO_PX, LADO_PX)
	vista.world_3d = get_viewport().find_world_3d()
	vista.msaa_3d = Viewport.MSAA_4X
	vista.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vista)
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = lado_m
	cam.near = 1.0
	cam.far = 1500.0
	vista.add_child(cam)
	cam.make_current()

	var cols := int(ceil(ancho / float(LADO_PX)))
	var filas := int(ceil(alto / float(LADO_PX)))
	for f in filas:
		for c in cols:
			var cx := LIMITES.x + (c + 0.5) * lado_m
			var cz := LIMITES.y + (f + 0.5) * lado_m
			var centro := Vector3(cx, 0.0, cz)
			ciudad.fijar_foco(centro)
			var t := 0.0
			while ciudad.progreso_alrededor(centro, lado_m) < 0.999 and t < 60.0:
				await get_tree().process_frame
				t += get_process_delta_time()
			for _k in 8:
				await RenderingServer.frame_post_draw
			# desde arriba, mirando abajo, con el norte (−z) hacia arriba de la imagen
			cam.global_transform = Transform3D(Basis.looking_at(Vector3.DOWN, Vector3(0, 0, -1)), Vector3(cx, 700.0, cz))
			for _k in 3:
				await RenderingServer.frame_post_draw
			var img := vista.get_texture().get_image()
			img.convert(Image.FORMAT_RGB8)
			final.blit_rect(img, Rect2i(0, 0, LADO_PX, LADO_PX), Vector2i(c * LADO_PX, f * LADO_PX))
			print("minimapa: mosaico %d/%d" % [f * cols + c + 1, filas * cols])
	final.save_webp("res://texturas/minimapa.webp", true, 0.9)
	var info := {"limites": {"x0": LIMITES.x, "z0": LIMITES.y, "x1": LIMITES.z, "z1": LIMITES.w}, "ancho": ancho, "alto": alto}
	var f := FileAccess.open("res://datos/minimapa.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(info))
	f.close()
	print("minimapa: texturas/minimapa.webp (%d×%d) y datos/minimapa.json" % [ancho, alto])
	get_tree().quit()
