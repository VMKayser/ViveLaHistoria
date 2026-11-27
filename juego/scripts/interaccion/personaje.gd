class_name Personaje
extends Interactuable
## Personaje con el que se habla. Los diálogos están en el JSON de la escena.
## Si el jugador lleva el Acta y este personaje puede firmar, en vez de hablar firma.

## Tipo de evento que registra su firma: "firma" (diputado) o "firma_presidente".
@export var tipo_firma := ""
## Firmas de diputados que deben existir antes de que este personaje firme.
@export var firmas_requeridas := 0
@export var objeto_para_firmar := "acta"

var es_ficticio := false
var _etiqueta: Label3D


func _ready() -> void:
	super()
	verbo = "Hablar con"
	add_to_group("personajes")


## Recibe nombre, rol y si es ficticio desde los datos de la escena.
func configurar(datos: Dictionary) -> void:
	if datos.is_empty():
		push_warning("[Personaje] '%s' no está en el JSON de la escena." % id_interaccion)
		return
	nombre_visible = str(datos.get("nombre", nombre_visible))
	es_ficticio = bool(datos.get("ficticio", false))
	if ficha_id.is_empty():
		ficha_id = str(datos.get("ficha", ""))
	_crear_etiqueta(str(datos.get("rol", "")))


func texto_para(jugador: Jugador) -> String:
	if _puede_firmar(jugador):
		return "[E] Pedir la firma de %s" % nombre_visible
	return "[E] Hablar con %s" % nombre_visible


func interactuar(jugador: Jugador) -> void:
	if _puede_firmar(jugador):
		var firmadas := EstadoJuego.cantidad("firma", "*")
		if firmadas < firmas_requeridas:
			EstadoJuego.aviso.emit("%s: primero consiga %d firmas de diputados (lleva %d)." % [nombre_visible, firmas_requeridas, firmadas])
			return
		EstadoJuego.registrar(tipo_firma, id_interaccion)
		EstadoJuego.aviso.emit("%s firmó el Acta." % nombre_visible)
		return
	EstadoJuego.solicitud_dialogo.emit(id_interaccion)


func _puede_firmar(jugador: Jugador) -> bool:
	return not tipo_firma.is_empty() \
		and jugador.sostiene(objeto_para_firmar) \
		and EstadoJuego.cantidad(tipo_firma, id_interaccion) == 0


func _crear_etiqueta(rol: String) -> void:
	if _etiqueta == null:
		_etiqueta = Label3D.new()
		_etiqueta.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_etiqueta.font_size = 36
		_etiqueta.pixel_size = 0.004
		_etiqueta.outline_size = 10
		_etiqueta.position = Vector3(0.0, 2.15, 0.0)
		add_child(_etiqueta)
	var texto := nombre_visible
	if not rol.is_empty():
		texto += "\n" + rol
	if es_ficticio:
		texto += "\n(personaje ficticio)"
	_etiqueta.text = texto
