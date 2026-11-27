extends RefCounted
## Fuego de antorchas y faroles (partículas por CPU: funcionan igual en la web).

static var _mat_fuego: StandardMaterial3D
static var _mat_humo: StandardMaterial3D


static func _textura_suave() -> GradientTexture2D:
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	var tx := GradientTexture2D.new()
	tx.gradient = g
	tx.fill = GradientTexture2D.FILL_RADIAL
	tx.fill_from = Vector2(0.5, 0.5)
	tx.fill_to = Vector2(0.5, 0.0)
	tx.width = 64
	tx.height = 64
	return tx


static func mat_fuego() -> StandardMaterial3D:
	if _mat_fuego == null:
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
		m.vertex_color_use_as_albedo = true
		m.albedo_color = Color(1.9, 1.35, 0.9, 1.0)
		m.albedo_texture = _textura_suave()
		m.disable_receive_shadows = true
		_mat_fuego = m
	return _mat_fuego


static func mat_humo() -> StandardMaterial3D:
	if _mat_humo == null:
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
		m.vertex_color_use_as_albedo = true
		m.albedo_texture = _textura_suave()
		m.disable_receive_shadows = true
		_mat_humo = m
	return _mat_humo


static func fuego(escala := 1.0) -> Node3D:
	var raiz := Node3D.new()
	var p := CPUParticles3D.new()
	p.amount = 26
	p.lifetime = 0.5
	p.local_coords = false
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 0.045 * escala
	p.direction = Vector3.UP
	p.spread = 10.0
	p.gravity = Vector3(0, 1.4, 0)
	p.initial_velocity_min = 0.35 * escala
	p.initial_velocity_max = 0.8 * escala
	p.scale_amount_min = 0.7
	p.scale_amount_max = 1.2
	var curva := Curve.new()
	curva.add_point(Vector2(0.0, 0.55))
	curva.add_point(Vector2(0.25, 1.0))
	curva.add_point(Vector2(1.0, 0.1))
	p.scale_amount_curve = curva
	var g := Gradient.new()
	g.set_color(0, Color(1.0, 0.9, 0.55, 1.0))
	g.set_color(1, Color(0.7, 0.12, 0.02, 0.0))
	g.add_point(0.35, Color(1.0, 0.55, 0.15, 0.9))
	p.color_ramp = g
	var q := QuadMesh.new()
	q.size = Vector2(0.2, 0.28) * escala
	q.material = mat_fuego()
	p.mesh = q
	raiz.add_child(p)

	var h := CPUParticles3D.new()
	h.amount = 10
	h.lifetime = 2.2
	h.local_coords = false
	h.position = Vector3(0, 0.2 * escala, 0)
	h.direction = Vector3.UP
	h.spread = 15.0
	h.gravity = Vector3(0.15, 0.6, 0)
	h.initial_velocity_min = 0.3
	h.initial_velocity_max = 0.6
	var curva_h := Curve.new()
	curva_h.add_point(Vector2(0.0, 0.3))
	curva_h.add_point(Vector2(1.0, 1.0))
	h.scale_amount_curve = curva_h
	var gh := Gradient.new()
	gh.set_color(0, Color(0.08, 0.07, 0.06, 0.35))
	gh.set_color(1, Color(0.08, 0.07, 0.06, 0.0))
	h.color_ramp = gh
	var qh := QuadMesh.new()
	qh.size = Vector2(0.5, 0.5) * escala
	qh.material = mat_humo()
	h.mesh = qh
	raiz.add_child(h)
	return raiz


static func luz_fuego(energia := 1.8, alcance := 9.0) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.light_color = Color(1.0, 0.62, 0.32)
	l.light_energy = energia
	l.omni_range = alcance
	l.omni_attenuation = 1.4
	l.shadow_enabled = false
	l.set_meta("base", energia)
	l.set_meta("fase", randf() * 100.0)
	return l
