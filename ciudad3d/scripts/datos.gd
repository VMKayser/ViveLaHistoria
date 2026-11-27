extends Node
## Origen de los datos de la ciudad (autoload "Datos"). En el APK y en el escritorio van dentro del paquete (res://datos/);
## en la web NO (serían decenas de MB antes de ver nada): se descargan a demanda del mismo servidor
## (web/public/ciudad3d/datos/), con la versión de cada archivo en la dirección para que el navegador los guarde en caché.

const SIMULTANEAS := 6

var en_web := OS.has_feature("web")
var _base := ""
var _activas := 0

func _ready() -> void:
	if en_web:
		var origen = JavaScriptBridge.eval("window.location.origin", true)
		_base = str(origen) + "/ciudad3d/datos/"

## Bytes de un archivo de datos (con 'await'). Vacío si no existe o falla la descarga.
func bytes(nombre: String, version := "") -> PackedByteArray:
	if not en_web:
		return FileAccess.get_file_as_bytes("res://datos/" + nombre)
	while _activas >= SIMULTANEAS:
		await get_tree().process_frame
	_activas += 1
	var http := HTTPRequest.new()
	http.accept_gzip = false          # el navegador ya descomprime lo que manda el servidor
	add_child(http)
	var url := _base + nombre + ("?v=" + version if version != "" else "")
	var res := []
	if http.request(url) == OK:
		res = await http.request_completed
	http.queue_free()
	_activas -= 1
	if res.is_empty() or res[0] != HTTPRequest.RESULT_SUCCESS or res[1] != 200:
		push_warning("no se pudo descargar " + url)
		return PackedByteArray()
	return res[3]

func texto(nombre: String, version := "") -> String:
	var b: PackedByteArray = await bytes(nombre, version)
	return b.get_string_from_utf8()

func json(nombre: String, version := "") -> Variant:
	var t: String = await texto(nombre, version)
	return JSON.parse_string(t) if t != "" else null
