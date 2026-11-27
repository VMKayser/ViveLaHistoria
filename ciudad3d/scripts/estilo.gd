class_name Estilo
extends RefCounted
## Materiales del estilo pintado. La ciudad se dibuja con dos materiales (normal y fondo para los cerros, que solo cambia
## sin_niebla): cada vértice lleva el número de su rol (UV.x) y el shader toma de arreglos los parámetros de ese rol (pintura,
## relieve, detalle). Así una tesela es una o dos llamadas de dibujo en lugar de una por material (antes ≈20).
## Los valores están en texturas/estilo.json (la misma tabla que usa el empaquetador); los vehículos usan material_movil.
##
## Todo (ciudad, cerros, copas y vehículos) usa UN SOLO shader, shaders/estilo.gdshader: en WebGL Godot compila cuatro
## variantes de cada shader distinto al usarlo por primera vez (~4–5 s por shader en la primera visita, medido el
## 2026-11-26). Las copas ya no tienen material de doble cara: el empaquetador duplica sus caras ("doble" queda por si
## llegan datos viejos).
const SHADER := "res://shaders/estilo.gdshader"
## Racimos de hojas de las copas: el mismo código con HOJAS definido (recorte por alfa, sin descarte en el resto de la ciudad)
const SHADER_HOJAS := "res://shaders/hojas.gdshader"

static var _tabla := {}
static var _cache := {}
static var _texturas := {}

static func tabla() -> Dictionary:
	if _tabla.is_empty():
		_tabla = JSON.parse_string(FileAccess.get_file_as_string("res://texturas/estilo.json"))
		_tabla["capas"] = JSON.parse_string(FileAccess.get_file_as_string("res://texturas/capas.json"))
	return _tabla

static func textura(ruta: String) -> Texture:
	if not _texturas.has(ruta):
		_texturas[ruta] = load(ruta)
	return _texturas[ruta]

## Al salir: suelta materiales y texturas guardados en variables estáticas. Si no, Godot los libera después de apagar el
## servidor de render y el cierre aborta ("double free" / "corrupted size").
static func liberar() -> void:
	_cache.clear()
	_texturas.clear()

static func es_compatibilidad() -> bool:
	return RenderingServer.get_current_rendering_method() == "gl_compatibility"

## Material de la ciudad para la clase 'normal' | 'doble' | 'fondo' | 'hojas'; 'roles' es la lista de ciudad.json (el índice de cada
## rol es el número que llevan sus vértices).
static func material_ciudad(clase: String, roles: Array) -> ShaderMaterial:
	if _cache.has(clase):
		return _cache[clase]
	var t := tabla()
	var capas: Dictionary = t["capas"]
	var a := PackedVector4Array()
	var b := PackedVector4Array()
	var c := PackedVector4Array()
	for rol in roles:
		var p: Array = t["pintura"].get(rol, t["pintura_def"])
		var r = t["relieve"].get(rol)
		var d = t["detalle"].get(rol)
		a.append(Vector4(p[0], p[1], p[2], capas["relieve"][r[0]] if r != null else -1.0))
		b.append(Vector4(r[1] if r != null else 1.0, r[2] if r != null else 0.0,
			capas["detalle"][d[0]] if d != null else -1.0, d[1] if d != null else 1.0))
		c.append(Vector4(d[4] if d != null else 1.0, d[5] if d != null else 0.0, float(t["rugosidad"].get(rol, 0.0)),
			float(t["brillo"].get(rol, 0.0))))
	var m := ShaderMaterial.new()
	m.shader = load(SHADER_HOJAS if clase == "hojas" else SHADER)
	if es_compatibilidad():
		m.set_shader_parameter("comp_srgb", true)
	if clase == "hojas":
		m.set_shader_parameter("hojas", textura("res://texturas/hojas.png"))
	m.set_shader_parameter("rol_a", a)
	m.set_shader_parameter("rol_b", b)
	m.set_shader_parameter("rol_c", c)
	m.set_shader_parameter("capas_relieve", textura("res://texturas/capas_relieve.png"))
	m.set_shader_parameter("capas_detalle", textura("res://texturas/capas_detalle.png"))
	m.set_shader_parameter("reflejo", textura("res://texturas/reflejo_calle.jpg"))
	if clase == "fondo":
		m.set_shader_parameter("sin_niebla", true)
	_cache[clase] = m
	return m

## Material de un vehículo (patrón en coordenadas del objeto, faros y pilotos) con los colores de su unidad.
static func material_movil(rol: String, pintura: Color, detalle: Color) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SHADER)
	m.set_shader_parameter("movil", true)
	if es_compatibilidad():
		m.set_shader_parameter("comp_srgb", true)
	var p: Array = tabla()["pintura"].get(rol, tabla()["pintura_def"])
	m.set_shader_parameter("escala", p[0])
	m.set_shader_parameter("amplitud", p[1])
	m.set_shader_parameter("tipo", int(p[2]))
	m.set_shader_parameter("reflejo", textura("res://texturas/reflejo_calle.jpg"))
	m.set_shader_parameter("pintura", Vector3(pintura.r, pintura.g, pintura.b))
	m.set_shader_parameter("pintura_detalle", Vector3(detalle.r, detalle.g, detalle.b))
	return m
