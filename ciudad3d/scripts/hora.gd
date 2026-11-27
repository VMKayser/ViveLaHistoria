extends Node
## Hora del día (autoload "Hora"): todo lo que cambia entre día, atardecer, noche y amanecer en un solo lugar
## (antes web/src/ciudad/motor/atmosfera.ts). Cielo, luz del sol o la luna, luz de relleno, niebla, ajuste de color de la
## imagen final y faroles. Los materiales leen los valores como parámetros globales de shader (estilo.gdshaderinc).

signal cambio(hora: String)

const ATMOSFERAS := {
	"dia": {"cielo": "dia", "astro": Vector2(0.0931, 0.5583), "horizonte": "#c9d9ea", "niebla": "#c3d2e2",
		"sol": ["#ffe6c4", 2.8, Vector3(-0.55, 0.62, -0.56)], "relleno": ["#c9c6e6", "#c9a27e", 1.15],
		"post": [0.12, 0.07, 0.35], "luces": false,
		"luz": ["#fff0da", 1.0, "#9dbde6", 0.75, "#cfb9a0", 0.5, 0.62]},
	"atardecer": {"cielo": "atardecer", "astro": Vector2(0.0931, 0.5583), "horizonte": "#d86c45", "niebla": "#c98a6e",
		"sol": ["#ffb06a", 2.0, Vector3(-0.8, 0.22, -0.56)], "relleno": ["#8f86c8", "#b58a6c", 0.9],
		"post": [0.12, 0.08, 0.42], "luces": false,
		"luz": ["#ffb478", 1.05, "#a0a2dc", 0.62, "#c89070", 0.45, 0.6]},
	"amanecer": {"cielo": "amanecer", "astro": Vector2(0.0931, 0.5583), "horizonte": "#d88886", "niebla": "#c8a0a8",
		"sol": ["#ffc9b0", 1.9, Vector3(0.8, 0.22, 0.56)], "relleno": ["#a9a3d8", "#b39080", 0.9],
		"post": [0.1, 0.07, 0.4], "luces": false,
		"luz": ["#ffc9b0", 0.95, "#a2a6dc", 0.5, "#b39080", 0.35, 0.6]},
	"noche": {"cielo": "noche", "astro": Vector2(0.6123, 0.825), "horizonte": "#090e1f", "niebla": "#0d1528",
		"sol": ["#a9bcff", 0.9, Vector3(-0.36, 0.85, -0.38)], "relleno": ["#2a3a66", "#1a1620", 0.6],
		"post": [0.05, 0.1, 0.55], "luces": true,
		"luz": ["#a9bcff", 0.3, "#2a3a66", 0.25, "#1a1620", 0.2, 0.7]},
}
const MAX_FAROLES := 16
const NIEBLA_PIE := Vector2(120.0, 2600.0)
const NIEBLA_AIRE := Vector2(350.0, 2600.0)

var actual := "dia"
var entorno: Environment
var sol: DirectionalLight3D
var _cielo: ShaderMaterial
var _registrado := false

## Parámetros globales que leen todos los materiales: hay que registrarlos ANTES de crear ningún material.
func registrar_globales() -> void:
	if _registrado:
		return
	_registrado = true
	var rs := RenderingServer
	rs.global_shader_parameter_add("noche", RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 0.0)
	rs.global_shader_parameter_add("atm_luz", RenderingServer.GLOBAL_VAR_TYPE_VEC4, Vector4(0.6, 0.45, 2.3, 0.0))
	rs.global_shader_parameter_add("atm_niebla", RenderingServer.GLOBAL_VAR_TYPE_VEC3, Vector3(0.6, 0.5, 0.45))
	rs.global_shader_parameter_add("atm_niebla_d", RenderingServer.GLOBAL_VAR_TYPE_VEC2, NIEBLA_PIE)
	rs.global_shader_parameter_add("atm_sol_dir", RenderingServer.GLOBAL_VAR_TYPE_VEC3, Vector3(-0.55, 0.62, -0.56))
	rs.global_shader_parameter_add("atm_sol_col", RenderingServer.GLOBAL_VAR_TYPE_VEC3, Vector3(1.0, 0.9, 0.75))
	rs.global_shader_parameter_add("atm_cielo_col", RenderingServer.GLOBAL_VAR_TYPE_VEC3, Vector3(0.4, 0.47, 0.6))
	rs.global_shader_parameter_add("atm_suelo_col", RenderingServer.GLOBAL_VAR_TYPE_VEC3, Vector3(0.4, 0.33, 0.26))
	rs.global_shader_parameter_add("atm_hombro", RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 0.62)
	for i in MAX_FAROLES:
		rs.global_shader_parameter_add("farol_%d" % i, RenderingServer.GLOBAL_VAR_TYPE_VEC4, Vector4.ZERO)

## Crea el entorno (cielo) y la luz direccional, y los cuelga de 'padre'.
func montar(padre: Node) -> void:
	registrar_globales()
	entorno = Environment.new()
	entorno.background_mode = Environment.BG_SKY
	var cielo := Sky.new()
	_cielo = ShaderMaterial.new()
	_cielo.shader = load("res://shaders/cielo.gdshader")
	cielo.sky_material = _cielo
	cielo.radiance_size = Sky.RADIANCE_SIZE_32
	cielo.process_mode = Sky.PROCESS_MODE_INCREMENTAL
	entorno.sky = cielo
	entorno.ambient_light_source = Environment.AMBIENT_SOURCE_DISABLED
	entorno.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	entorno.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	entorno.fog_enabled = false
	var we := WorldEnvironment.new()
	we.name = "Entorno"
	we.environment = entorno
	padre.add_child(we)
	sol = DirectionalLight3D.new()
	sol.name = "Sol"
	sol.shadow_enabled = true
	# un solo mapa de sombras (como la web three.js): con dos cortes se dibujaba la ciudad dos veces más por cuadro
	sol.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
	sol.directional_shadow_max_distance = 110.0
	sol.shadow_bias = 0.05
	sol.shadow_normal_bias = 1.5
	sol.shadow_blur = 1.4
	sol.directional_shadow_fade_start = 0.85
	padre.add_child(sol)
	aplicar(actual)

static func lineal(hexa: String) -> Color:
	return Color(hexa).srgb_to_linear()

static func _vec(c: Color, k: float) -> Vector3:
	return Vector3(c.r, c.g, c.b) * k

static func _lum(c: Color) -> float:
	return 0.299 * c.r + 0.587 * c.g + 0.114 * c.b

func aplicar(hora: String) -> void:
	actual = hora
	var a: Dictionary = ATMOSFERAS[hora]
	var dir: Vector3 = (a["sol"][2] as Vector3).normalized()
	# cielo: imagen, giro para que el astro caiga sobre la luz, color del horizonte
	_cielo.set_shader_parameter("mapa", load("res://cielo/%s.jpg" % a["cielo"]))
	var astro: Vector2 = a["astro"]
	_cielo.set_shader_parameter("desfase", astro.x - (atan2(dir.x, dir.z) / TAU + 0.5))
	_cielo.set_shader_parameter("horizonte", Color(a["horizonte"]))
	# luz: solo importa su luminancia (el sombreado es en 3 franjas); el color se usa en la luz real por si algo la lee
	var c_sol := lineal(a["sol"][0])
	sol.light_color = Color(a["sol"][0])
	sol.light_energy = 1.0
	sol.look_at_from_position(Vector3.ZERO, -dir, Vector3.UP)
	var r: Array = a["relleno"]
	var rs := RenderingServer
	rs.global_shader_parameter_set("atm_luz", Vector4(_lum(lineal(r[0])) * r[2], _lum(lineal(r[1])) * r[2], _lum(c_sol) * a["sol"][1], 0.0))
	var n := lineal(a["niebla"])
	rs.global_shader_parameter_set("atm_niebla", Vector3(n.r, n.g, n.b))
	rs.global_shader_parameter_set("atm_sol_dir", dir)
	# luz de la escena (estilo.gdshaderinc): [sol, intensidad, cielo, intensidad, suelo, intensidad, hombro de la curva]
	var lz: Array = a["luz"]
	rs.global_shader_parameter_set("atm_sol_col", _vec(lineal(lz[0]), lz[1]))
	rs.global_shader_parameter_set("atm_cielo_col", _vec(lineal(lz[2]), lz[3]))
	rs.global_shader_parameter_set("atm_suelo_col", _vec(lineal(lz[4]), lz[5]))
	rs.global_shader_parameter_set("atm_hombro", lz[6])
	rs.global_shader_parameter_set("noche", 1.0 if a["luces"] else 0.0)
	cambio.emit(hora)

func niebla_a_pie(a_pie: bool) -> void:
	RenderingServer.global_shader_parameter_set("atm_niebla_d", NIEBLA_PIE if a_pie else NIEBLA_AIRE)

## Ajuste de color de la imagen final (saturación, contraste, viñeta) de la hora actual.
func post() -> Array:
	return ATMOSFERAS[actual]["post"]

func luces() -> bool:
	return ATMOSFERAS[actual]["luces"]
