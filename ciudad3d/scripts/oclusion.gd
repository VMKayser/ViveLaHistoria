class_name Oclusion
extends MeshInstance3D
## Oclusión ambiental en pantalla (shaders/oclusion.gdshader): un rectángulo que cubre la pantalla y oscurece rincones,
## aleros, juntas y la base de muros y árboles. La calidad la elige scripts/calidad.gd (muestras; 0 = apagada).

var _mat: ShaderMaterial

func _init() -> void:
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	_mat = ShaderMaterial.new()
	_mat.shader = load("res://shaders/oclusion.gdshader")
	_mat.render_priority = -100       # antes que los halos de los faroles y los vidrios transparentes
	q.material = _mat
	mesh = q
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	extra_cull_margin = 16384.0       # cubre la pantalla esté donde esté la cámara
	ignore_occlusion_culling = true
	if OS.get_environment("SUCRE_AO_DEPURAR") != "":        # pruebas: la oclusión sola, en grises (sobre blanco)
		_mat.set_shader_parameter("depurar", true)

## Muestras por píxel (0 apaga la oclusión).
func fijar_muestras(n: int) -> void:
	visible = n > 0
	_mat.set_shader_parameter("muestras", n)

## Radio en metros: 2,5 a pie, 8 desde el aire (como la web).
func fijar_radio(r: float) -> void:
	_mat.set_shader_parameter("radio", r)
	_mat.set_shader_parameter("alcance", 120.0 if r < 4.0 else 900.0)
