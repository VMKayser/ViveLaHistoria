shader_type spatial;
render_mode cull_disabled, diffuse_lambert, ambient_light_disabled, fog_disabled;
// Racimos de hojas de las copas (herramientas/empaquetar.py → tarjetas_hojas): el mismo estilo que la ciudad, con los
// cuadros abiertos hacia la cámara (o hacia el sol, en el pase de sombras) y recortados por la textura de hojas. Va en
// un shader aparte para que el descarte por alfa no afecte al resto de la ciudad.
#define HOJAS
#include "res://shaders/estilo.gdshaderinc"
