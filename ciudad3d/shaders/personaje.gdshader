shader_type spatial;
render_mode cull_back, diffuse_lambert, specular_disabled, ambient_light_disabled, fog_disabled;
// Personajes de los encuentros (scripts/personajes/personaje.gd): su textura con la MISMA luz que la ciudad
// (luz.gdshaderinc: sol cálido, sombra iluminada por el cielo y el rebote del suelo, curva de tonos y niebla).
// Con el material estándar de Godot el lado en sombra quedaba casi negro: la escena no tiene luz ambiente (la ciudad
// se ilumina en su shader), y los modelos de Tripo además venían como metal. Un borde de luz de cielo los despega del
// fondo, como en las ilustraciones de los retratos.
#include "res://shaders/luz.gdshaderinc"

uniform sampler2D albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable, hint_default_white;
uniform vec4 tinte : source_color = vec4(1.0);
uniform sampler2D relieve : hint_normal, filter_linear_mipmap, repeat_enable;
uniform bool con_relieve = false;
uniform float fuerza_relieve = 0.5;

varying vec3 v_pos;
varying float v_prof;

void vertex() {
	v_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_prof = -(MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).z;
}

void fragment() {
	ALBEDO = texture(albedo, UV).rgb * tinte.rgb;
	if (con_relieve) {
		NORMAL_MAP = texture(relieve, UV).rgb;
		NORMAL_MAP_DEPTH = fuerza_relieve;
	}
}

void light() {
	vec3 base = ALBEDO;
	vec3 nw = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	vec3 rec = luz_recibida(nw, dot(NORMAL, LIGHT), ATTENUATION);
	// borde de luz de cielo (despega la figura del fondo, sobre todo a contraluz)
	float borde = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	rec += atm_cielo_col * borde * 0.6;
	vec3 col = tonos(base * rec);
	if (noche > 0.001) {
		col = mix(col, base * (vec3(0.045, 0.06, 0.12) + vec3(0.13, 0.17, 0.3) * 0.5 + vec3(0.25, 0.2, 0.14) * borde), noche);
	}
	col = con_niebla(col, v_prof);
	DIFFUSE_LIGHT = col / max(base, vec3(0.002));
}
