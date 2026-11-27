class_name Calidad
extends Node
## Niveles de calidad (antes web/src/ciudad/motor/calidad.ts). Arranca en "alta" y baja sola si el equipo no sostiene
## los cuadros por segundo; ?calidad=alta|media|baja lo fija (para capturas y comparaciones).

const NIVELES := {
	"alta": {"escala": 1.0, "sombra": 4096, "detalle": 420.0, "hojas": 130.0, "pasto": 32.0, "pintado": 0.0, "aa": true, "vehiculos": 30, "ao": 12},
	"media": {"escala": 0.85, "sombra": 2048, "detalle": 280.0, "hojas": 90.0, "pasto": 22.0, "pintado": 0.0, "aa": true, "vehiculos": 22, "ao": 8},
	"baja": {"escala": 0.7, "sombra": 1024, "detalle": 160.0, "hojas": 0.0, "pasto": 0.0, "pintado": 0.0, "aa": false, "vehiculos": 12, "ao": 0},
}
## "pintado": radio del filtro Kuwahara (0 = apagado). Desde el 2026-11-26 apagado en todos los niveles: borroneaba las
## texturas y costaba ~3–4 fps en la web (49 lecturas por píxel); lo reemplaza el enfoque adaptativo (CAS, 5 lecturas).
const MS_LIMITE := 40.0        # media de ms por cuadro por encima de la cual se baja (≈ 25 fps)

var nivel := "alta"
var fijo := false
## Mientras carga (antes de aparecer a pie) no se mide ni se baja la calidad: los cuadros lentos de la carga (compilación de
## shaders, teselas) no dicen nada del equipo, y antes la bajaban a "media" sin motivo y obligaban a recompilar. En la web,
## además, la pantalla de inicio tapa el lienzo: se dibuja a resolución mínima (mismos shaders, que así se compilan durante
## la carga y no al entrar) para que la carga no espere cuadros que nadie ve.
var cargando := true
const ESCALA_CARGA := 0.25
var ciudad: Ciudad
var post: Post
var oclusion: Oclusion
var trafico: Node
var pasto: Pasto
var _t := 0.0
var _n := 0
var _suma := 0.0
var _esperar := 6.0           # la compilación de shaders y la primera subida de geometría dan tirones que no cuentan

## Diagnóstico de rendimiento: ?sin=sombra,post,trafico,ao,pasto,hojas,ciudad apaga cada parte para medir lo que cuesta.
var sin: PackedStringArray = []

func _ready() -> void:
	var p = Puente.parametro("sin")
	if p != null:
		sin = str(p).split(",")
		fijo = true
	if OS.has_feature("mobile"):
		nivel = "media"
	var q = Puente.parametro("calidad")
	if q != null and NIVELES.has(str(q)):
		nivel = str(q)
		fijo = true
	aplicar(nivel)

func aplicar(n: String) -> void:
	nivel = n
	var c: Dictionary = NIVELES[n]
	get_viewport().scaling_3d_scale = ESCALA_CARGA if cargando and OS.has_feature("web") else c["escala"]
	RenderingServer.directional_shadow_atlas_set_size(c["sombra"], true)
	ciudad.radio_detalle = c["detalle"]
	ciudad.radio_hojas = 0.0 if "hojas" in sin else c["hojas"]
	if pasto != null:
		pasto.fijar_radio(0.0 if "pasto" in sin else c["pasto"])
	post.fijar_calidad(0.0 if OS.has_feature("mobile") else c["pintado"], c["aa"])
	if oclusion != null:
		oclusion.fijar_muestras(0 if "ao" in sin else c["ao"])
	if trafico != null and trafico.has_method("fijar_cantidad"):
		trafico.fijar_cantidad(0 if "trafico" in sin else c["vehiculos"])
	if "post" in sin:
		post.visible = false
	if "sombra" in sin:
		var sol := get_tree().root.find_child("Sol", true, false) as DirectionalLight3D
		if sol:
			sol.shadow_enabled = false

## Ya se está a pie: resolución normal y, desde ahora, la medición para bajar de nivel si hace falta.
func fin_carga() -> void:
	if not cargando:
		return
	cargando = false
	_esperar = 6.0
	_t = 0.0
	_n = 0
	_suma = 0.0
	aplicar(nivel)

func fijar(n: String) -> void:
	fijo = true
	aplicar(n)

func _process(dt: float) -> void:
	if fijo or cargando or nivel == "baja":
		return
	if _esperar > 0.0:
		_esperar -= dt
		return
	_t += dt
	_n += 1
	_suma += dt
	if _t < 4.0:
		return
	var ms := _suma / float(_n) * 1000.0
	_t = 0.0
	_n = 0
	_suma = 0.0
	if ms > MS_LIMITE:
		aplicar("media" if nivel == "alta" else "baja")
		_esperar = 3.0
