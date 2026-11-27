class_name Voz
extends Node
## Las voces de los encuentros (una frase = un audio; datos de cada paso del guion: voz, av, dur; ver herramientas/personajes.py).
##
## - Web: las reproduce el navegador con <audio> (Ogg Opus 32 kbps, MP3 si no sabe Opus). El audio se va bajando mientras
##   suena (no hay que esperar el archivo entero), lo guarda la caché HTTP (la dirección lleva ?v=versión) y no pasa por
##   la cola de descargas de la ciudad (Datos), que al caminar va llena de teselas. precargar() lo pide con antelación.
## - APK y escritorio: MP3 48 kbps dentro del paquete, leído con FileAccess y reproducido por un AudioStreamPlayer.
## Si un audio no puede sonar (sin red, el navegador no dejó), la carta sigue igual por su tiempo (dur del paso).

signal terminada                            # el audio de la frase llegó a su fin

var en_web := OS.has_feature("web")
var _js: JavaScriptObject
var _al_terminar: JavaScriptObject          # callback JS (debe seguir vivo)
var _jugador: AudioStreamPlayer
var _cache := {}                            # escritorio/APK: ruta → AudioStreamMP3
var _sonando := false

const JS := """
window.sucreVoz = window.sucreVoz || (() => {
  const prueba = document.createElement('audio');
  const fmt = prueba.canPlayType('audio/ogg; codecs="opus"') ? 'opus' : 'mp3';
  const base = location.origin + '/ciudad3d/datos/';
  const cache = new Map();            // url → <audio> ya pedido (como mucho LIMITE, se sueltan los más viejos)
  const LIMITE = 40;
  let actual = null;
  const url = (ruta, v) => base + ruta + '.' + fmt + '.bin' + (v ? '?v=' + v : '');
  const elemento = (u) => {
    let a = cache.get(u);
    if (!a) {
      a = new Audio(); a.preload = 'auto'; a.src = u; cache.set(u, a);
      if (cache.size > LIMITE) { const k = cache.keys().next().value; if (cache.get(k) !== actual) { cache.get(k).src = ''; } cache.delete(k); }
    }
    return a;
  };
  const v = {
    alTerminar: null,
    precargar(ruta, ver) { elemento(url(ruta, ver)); },
    tocar(ruta, ver) {
      v.callar();
      const a = elemento(url(ruta, ver));
      actual = a;
      a.currentTime = 0;
      a.onended = () => { if (actual === a) { actual = null; v.alTerminar && v.alTerminar(); } };
      a.play().catch(() => {});      // bloqueado o sin red: la carta sigue por su tiempo
    },
    callar() { if (actual) { actual.onended = null; actual.pause(); actual = null; } },
  };
  return v;
})();
"""

func _ready() -> void:
	if en_web:
		JavaScriptBridge.eval(JS, true)
		_js = JavaScriptBridge.get_interface("sucreVoz")
		_al_terminar = JavaScriptBridge.create_callback(func(_a): _fin())
		_js.alTerminar = _al_terminar
	else:
		_jugador = AudioStreamPlayer.new()
		_jugador.finished.connect(_fin)
		add_child(_jugador)

## Pide con antelación el audio de estos pasos (los que no tienen voz se ignoran).
func precargar(pasos: Array) -> void:
	for paso in pasos:
		var ruta: String = paso.get("voz", "")
		if ruta == "":
			continue
		if en_web:
			_js.precargar(ruta, str(paso.get("av", "")))
		else:
			_stream(ruta)

## Hace sonar la frase. false si el paso no tiene voz (la carta va por tiempo de lectura).
func tocar(paso: Dictionary) -> bool:
	var ruta: String = paso.get("voz", "")
	if ruta == "":
		return false
	callar()
	if en_web:
		_js.tocar(ruta, str(paso.get("av", "")))
	else:
		var s := _stream(ruta)
		if s == null:
			return false
		_jugador.stream = s
		_jugador.play()
	_sonando = true
	return true

func callar() -> void:
	_sonando = false
	if en_web:
		_js.callar()
	elif _jugador.playing:
		_jugador.stop()

func sonando() -> bool:
	return _sonando

func _fin() -> void:
	if _sonando:
		_sonando = false
		terminada.emit()

func _stream(ruta: String) -> AudioStream:
	if not _cache.has(ruta):
		var b := FileAccess.get_file_as_bytes("res://datos/" + ruta + ".mp3.bin")
		var s: AudioStreamMP3 = null
		if not b.is_empty():
			s = AudioStreamMP3.new()
			s.data = b
		_cache[ruta] = s
	return _cache[ruta]
