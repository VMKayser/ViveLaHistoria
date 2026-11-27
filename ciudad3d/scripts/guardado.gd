extends Node
## Preferencias que se recuerdan entre visitas (autoload "Guardado"): la hora del día elegida, la calidad, etc.
## En la web, user:// vive en el almacenamiento del navegador; en el APK, en los datos de la app.

const RUTA := "user://sucre.cfg"
var _cfg := ConfigFile.new()

func _ready() -> void:
	_cfg.load(RUTA)

func leer(clave: String, defecto: Variant = null) -> Variant:
	return _cfg.get_value("sucre", clave, defecto)

func escribir(clave: String, valor: Variant) -> void:
	_cfg.set_value("sucre", clave, valor)
	_cfg.save(RUTA)
