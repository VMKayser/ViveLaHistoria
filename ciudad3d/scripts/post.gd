class_name Post
extends CanvasLayer
## Imagen final (antes el EffectComposer de la web): filtro pintado (Kuwahara) + saturación + contraste + viñeta en una
## pasada y, después, antialias FXAA. Va debajo de la interfaz (que tiene su propia capa, más alta).

var _pintado: ColorRect
var _fxaa: ColorRect
var _mat: ShaderMaterial

func _ready() -> void:
	layer = 0
	_mat = ShaderMaterial.new()
	_mat.shader = load("res://shaders/post_pintado.gdshader")
	_pintado = _rect(_mat)
	add_child(_pintado)
	var copia := BackBufferCopy.new()
	copia.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
	add_child(copia)
	var mf := ShaderMaterial.new()
	mf.shader = load("res://shaders/post_fxaa.gdshader")
	_fxaa = _rect(mf)
	add_child(_fxaa)

func _rect(m: ShaderMaterial) -> ColorRect:
	var r := ColorRect.new()
	r.set_anchors_preset(Control.PRESET_FULL_RECT)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.material = m
	return r

## Radio del filtro pintado (px; 0 = sin filtro) y si va el antialias.
func fijar_calidad(radio: float, antialias: bool) -> void:
	_mat.set_shader_parameter("pintado", radio > 0.0)
	_mat.set_shader_parameter("radio", maxf(radio, 1.0))
	_fxaa.visible = antialias

## [saturación, contraste, viñeta] de la hora del día.
func fijar_hora(p: Array) -> void:
	_mat.set_shader_parameter("saturacion", p[0])
	_mat.set_shader_parameter("contraste", p[1])
	_mat.set_shader_parameter("vineta", p[2])
