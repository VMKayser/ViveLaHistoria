class_name Revision
extends Node3D
## Revisiones (herramienta de desarrollo, solo web): captura del encuadre que marca el usuario con los datos de la
## escena, y marcas 3D de las correcciones guardadas. El formulario y la lista son de la página (React); esto solo
## calcula lo que sabe la escena (antes escena/Capturador.tsx y MarcasRevision.tsx). Coordenadas "lienzo": x este,
## y norte, z altura (las de Blender y reparto/).

var principal: Node
var _marcas: Node3D

static func a_lienzo(v: Vector3) -> Dictionary:
	return {"x": snappedf(v.x, 0.01), "y": snappedf(-v.z, 0.01), "z": snappedf(v.y, 0.01)}

func _rayo(cam: Camera3D, p: Vector2) -> Variant:
	var origen := cam.project_ray_origin(p)
	var dir := cam.project_ray_normal(p)
	var q := PhysicsRayQueryParameters3D.create(origen, origen + dir * 4000.0, 3)
	var h := get_world_3d().direct_space_state.intersect_ray(q)
	return null if h.is_empty() else h["position"]

## marco: rectángulo 0–1 de la pantalla (desde arriba a la izquierda).
func capturar(marco: Rect2) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var cam := get_viewport().get_camera_3d()
	var vp := get_viewport().get_visible_rect().size
	var centro = _rayo(cam, (marco.position + marco.size * 0.5) * vp)
	var aproximado := false
	if centro == null:
		# el centro no toca nada: el punto más cercano dentro del marco, o uno a 25 m en el rayo
		var mejor = null
		var mejor_d := INF
		for i in 5:
			for j in 5:
				var p = _rayo(cam, (marco.position + marco.size * Vector2((i + 0.5) / 5.0, (j + 0.5) / 5.0)) * vp)
				if p != null and (p as Vector3).distance_to(cam.global_position) < mejor_d:
					mejor = p
					mejor_d = (p as Vector3).distance_to(cam.global_position)
		centro = mejor if mejor != null else cam.project_position((marco.position + marco.size * 0.5) * vp, 25.0)
		aproximado = true
	var esquinas := []
	for e in [marco.position, marco.position + Vector2(marco.size.x, 0), marco.end, marco.position + Vector2(0, marco.size.y)]:
		var p = _rayo(cam, e * vp)
		esquinas.append(null if p == null else a_lienzo(p))
	var j: Jugador = principal.jugador
	var datos := {
		"camara": {"modo": "peaton", "lienzo": a_lienzo(cam.global_position), "rumbo_grados": snappedf(fposmod(rad_to_deg(-j.yaw), 360.0), 0.1),
			"inclinacion_grados": snappedf(rad_to_deg(j.pitch), 0.1), "fov_vertical_grados": snappedf(cam.fov, 0.1), "aspecto": vp.x / vp.y},
		"marco": {"x0": marco.position.x, "y0": marco.position.y, "x1": marco.end.x, "y1": marco.end.y},
		"centro": a_lienzo(centro), "centro_aproximado": aproximado, "esquinas": esquinas,
		"distancia_m": snappedf((centro as Vector3).distance_to(cam.global_position), 0.1),
	}
	principal.puente.emitir({"tipo": "captura", "datos": datos,
		"captura": Marshalls.raw_to_base64(img.save_jpg_to_buffer(0.92))})

## Marcas 3D de las revisiones: un poste con una bola de color según el estado (la elegida, más grande).
func marcar(lista) -> void:
	if _marcas != null:
		_marcas.queue_free()
		_marcas = null
	if lista == null or (lista as Array).is_empty():
		return
	_marcas = Node3D.new()
	add_child(_marcas)
	for r in lista:
		var color := Color("#d9171a") if r.get("estado", "pendiente") == "pendiente" else (Color("#eac102") if r.get("estado") == "en_curso" else Color("#1f7a45"))
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.albedo_color = color
		m.no_depth_test = true
		m.render_priority = 10
		var bola := MeshInstance3D.new()
		var s := SphereMesh.new()
		var radio := 0.35 if r.get("elegida", false) else 0.22
		s.radius = radio
		s.height = radio * 2.0
		bola.mesh = s
		bola.material_override = m
		bola.position = Vector3(float(r["x"]), float(r["z"]), -float(r["y"]))
		bola.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		bola.set_meta("id", r.get("id", ""))
		_marcas.add_child(bola)

func _unhandled_input(ev: InputEvent) -> void:
	# clic sobre una marca: la página la elige
	if _marcas == null or not (ev is InputEventMouseButton) or not ev.pressed or ev.button_index != MOUSE_BUTTON_LEFT:
		return
	var cam := get_viewport().get_camera_3d()
	for b in _marcas.get_children():
		if cam.is_position_behind(b.global_position):
			continue
		if cam.unproject_position(b.global_position).distance_to(ev.position) < 18.0:
			principal.puente.emitir({"tipo": "elegida", "id": b.get_meta("id")})
			return
