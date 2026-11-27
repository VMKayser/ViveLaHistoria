class_name Caballo
extends Node3D
## Caballo de tiro de las carrozas (ROME Galope adaptado por codex; vehiculos/caballo.glb sale de
## web/scripts/preparar_vehiculos.mjs con el color en los vértices). Va enganchado a la tornamesa de su carroza y mueve
## las patas según la velocidad del conjunto: reposo, paso o galope, con la cadencia ajustada a la zancada de cada clip
## (así los cascos no patinan sobre el empedrado).
##
## Marco: el GLB mira a +X (glTF); dentro de la carroza (que mira a +Z) se gira -90° en Y.

const ESCENA := "res://vehiculos/caballo.glb"
## Velocidades (m/s) de cambio de marcha
const HASTA_REPOSO := 0.12
const HASTA_PASO := 1.8
## Zancada del galope (m por ciclo del clip). La ficha de codex mide 2,55 m, pero con las carrozas a 7 m/s (2026-11-26:
## el usuario no debe alcanzarlas corriendo) eso daba 4 ciclos por segundo y "el caballo galopa y la carroza va lenta".
## Un galope corto real avanza ~3,4 m por tranco a ~2 trancos por segundo: así cadencia y avance se ven naturales.
const ZANCADA_GALOPE := 3.4
const CADENCIA_MINIMA := 1.6  # × la velocidad del clip: al arrancar no se ve en cámara lenta
const MEZCLA := 0.3          # s de fundido entre marchas

static var _escena: PackedScene
static var _materiales := {}  # pelaje (índice) -> material

var _ap: AnimationPlayer
var _clips: Dictionary       # nombre -> {duracion_s, zancada_m}
var _marcha := ""
var _modelo: Node3D

## datos: el "caballo" de datos/vehiculos.json (clips y pelajes). pelaje: índice de la variante de color.
func _init(datos: Dictionary, pelaje: int) -> void:
	name = "Caballo"
	if _escena == null:
		_escena = load(ESCENA)
	_modelo = _escena.instantiate()
	_modelo.rotation.y = -PI / 2.0
	add_child(_modelo)
	var variantes: Array = datos["variantes"]
	var k := pelaje % variantes.size()
	if not _materiales.has(k):
		var v: Dictionary = variantes[k]
		_materiales[k] = Estilo.material_movil("vehiculo", Color(str(v["principal"])).srgb_to_linear(),
			Color(str(v["detalle"])).srgb_to_linear())
	for mi in _modelo.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).material_override = _materiales[k]
	_clips = datos["clips"]
	_ap = _modelo.find_child("AnimationPlayer", true, false)
	if _ap:
		for nombre in _ap.get_animation_list():
			_ap.get_animation(nombre).loop_mode = Animation.LOOP_LINEAR
		_ap.playback_process_mode = AnimationPlayer.ANIMATION_PROCESS_PHYSICS
	avanzar(0.0)

## Anclaje animado del arnés (tiro_caballo_*, cincha_caballo_*): punto final de las correas.
func anclaje(nombre: String) -> Node3D:
	return _modelo.find_child(nombre, true, false)

## Punto global del bocado (boca: marco del GLB, x adelante, y arriba, z a la derecha), corrido 'lado' m a cada costado.
func boca_global(boca: Array, lado: float) -> Vector3:
	return _modelo.to_global(Vector3(float(boca[0]), float(boca[1]), float(boca[2]) + lado))

## Marcha y cadencia según la velocidad del conjunto (m/s; negativa: retrocede al paso).
func avanzar(v: float) -> void:
	if _ap == null:
		return
	var rapidez := absf(v)
	var marcha := "reposo" if rapidez < HASTA_REPOSO else ("paso" if rapidez < HASTA_PASO or v < 0.0 else "galope")
	if marcha != _marcha:
		_marcha = marcha
		_ap.play(marcha, MEZCLA)
	if marcha == "reposo":
		_ap.speed_scale = 1.0
	else:
		var c: Dictionary = _clips[marcha]
		# un ciclo del clip avanza 'zancada_m': la cadencia es la velocidad sobre la zancada
		if marcha == "galope":
			_ap.speed_scale = maxf(v * float(c["duracion_s"]) / ZANCADA_GALOPE, CADENCIA_MINIMA)
		else:
			_ap.speed_scale = v * float(c["duracion_s"]) / float(c["zancada_m"])

## Lejos no se anima (se ve quieto a más de ~120 m; ahorra el recálculo de formas).
func animar(si: bool) -> void:
	if _ap:
		_ap.active = si
