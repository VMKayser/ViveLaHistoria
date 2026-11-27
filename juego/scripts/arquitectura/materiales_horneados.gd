class_name MaterialesHorneados
extends Node3D
## Aplica a la arquitectura exportada desde Blender (blender/construir_casa_libertad.py)
## los materiales PBR del juego más la luz horneada con Cycles.
##
## Cada superficie del .glb trae el nombre de su material ("cal", "piedra", ...); aquí se
## reemplaza por el shader de arquitectura con las texturas de juego/materiales/<nombre>.tres.
## La arquitectura queda en la capa visual 2 para que las luces de velas de Godot no la
## iluminen dos veces (esa luz ya está horneada).

const SHADER := preload("res://shaders/arquitectura_horneada.gdshader")
const CAPA_ARQUITECTURA := 2

@export var luz_horneada: Texture2D
@export var intensidad := 1.0
@export var rango := 4.0
## Menor que 1 comprime el rango de la luz horneada (interiores más visibles).
@export_range(0.3, 1.0) var curva := 0.65

var _cache: Dictionary = {}


func _ready() -> void:
	for malla: MeshInstance3D in find_children("*", "MeshInstance3D", true, false):
		malla.layers = CAPA_ARQUITECTURA
		for i in malla.mesh.get_surface_count():
			var original := malla.mesh.surface_get_material(i)
			var nombre := original.resource_name if original != null else ""
			malla.set_surface_override_material(i, _material(nombre))


func _material(nombre: String) -> Material:
	if _cache.has(nombre):
		return _cache[nombre]
	var ruta := "res://materiales/%s.tres" % nombre
	var resultado: Material
	if nombre.is_empty() or not ResourceLoader.exists(ruta):
		push_warning("[Arquitectura] Sin material de juego para '%s'." % nombre)
		resultado = StandardMaterial3D.new()
	else:
		var base := load(ruta) as StandardMaterial3D
		if base.albedo_texture == null:
			# Materiales sin textura (terciopelo): color plano más la luz horneada.
			var plano := ShaderMaterial.new()
			plano.shader = SHADER
			plano.set_shader_parameter("tinte", base.albedo_color)
			plano.set_shader_parameter("escala", 1.0)
			_asignar_luz(plano)
			resultado = plano
		else:
			var material := ShaderMaterial.new()
			material.shader = SHADER
			material.set_shader_parameter("tinte", base.albedo_color)
			material.set_shader_parameter("albedo_tex", base.albedo_texture)
			material.set_shader_parameter("normal_tex", base.normal_texture)
			material.set_shader_parameter("arm_tex", base.roughness_texture)
			material.set_shader_parameter("escala", base.uv1_scale.x)
			_asignar_luz(material)
			resultado = material
	_cache[nombre] = resultado
	return resultado


func _asignar_luz(material: ShaderMaterial) -> void:
	material.set_shader_parameter("luz_horneada", luz_horneada)
	material.set_shader_parameter("rango", rango)
	material.set_shader_parameter("intensidad", intensidad)
	material.set_shader_parameter("curva", curva)
