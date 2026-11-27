shader_type spatial;
render_mode cull_disabled, diffuse_lambert, ambient_light_disabled, fog_disabled;
// Pasto y flores sembrados de cerca (scripts/pasto.gd): matas de hojas de pasto y flores con tallo, pétalos y centro, en
// MultiMesh (una llamada de dibujo por celda). Viento que mueve más la punta, se hunden en el suelo al alejarse (sin
// saltos al aparecer) y la misma luz de la ciudad (luz.gdshaderinc). El color de cada mata o flor es el de la instancia.
#include "res://shaders/luz.gdshaderinc"

uniform float radio = 40.0;          // m: a esta distancia ya no hay pasto (se hunde desde el 60 %)
uniform bool flores = false;

varying vec3 v_nw;
varying vec3 v_pos;
varying float v_prof;
varying float v_alto;
varying float v_parte;               // flores: 0 tallo y hojas, 1 pétalos, 2 centro
varying float v_tono;

float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void vertex() {
	vec3 raiz = MODEL_MATRIX[3].xyz;
	vec3 cam = INV_VIEW_MATRIX[3].xyz;
	float d = distance(raiz.xz, cam.xz);
	float k = 1.0 - smoothstep(radio * 0.6, radio, d);
	VERTEX.y *= k;
	v_alto = UV.y;
	v_parte = UV.x;
	// viento: ráfagas lentas que recorren el césped + temblor de cada hoja, más en la punta
	vec2 r = vec2(sin(TIME * 1.6 + raiz.x * 0.45 + raiz.z * 0.25), cos(TIME * 1.3 + raiz.z * 0.4)) * 0.5 + 0.5;
	vec2 w = (vec2(0.6, 0.25) * r.x + vec2(sin(TIME * 5.0 + raiz.x * 7.0 + raiz.z * 3.0), cos(TIME * 4.3 + raiz.z * 6.0)) * 0.18)
		* (flores ? 0.05 : 0.07) * UV.y * UV.y * k;
	mat3 m = mat3(MODEL_MATRIX);
	float s2 = dot(m[0], m[0]);
	VERTEX += transpose(m) * vec3(w.x, 0.0, w.y) / s2;
	v_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	// la luz del pasto es casi la del suelo (si no, cada hoja de canto se vería oscura)
	v_nw = normalize(mix(normalize(m * NORMAL), vec3(0.0, 1.0, 0.0), flores && UV.x > 0.5 ? 0.3 : 0.7));
	v_prof = -(MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).z;
	v_tono = hash2(raiz.xz * 3.1);
}

void fragment() {
	vec3 c = COLOR.rgb;
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	// en Compatibility el color llega pasado de sRGB a lineal: los datos ya eran lineales (como en estilo.gdshaderinc)
	c = mix(1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, 12.92 * c, step(c, vec3(0.0031308)));
#endif
	vec3 base;
	if (flores && v_parte > 1.5) {
		base = vec3(0.85, 0.62, 0.08);                                 // centro amarillo
	} else if (flores && v_parte > 0.5) {
		base = c * (0.85 + 0.3 * v_tono);                              // pétalos
	} else if (flores) {
		base = vec3(0.1, 0.24, 0.05) * mix(0.7, 1.15, v_alto);        // tallo y hojas
	} else {
		// del pie (en la sombra de las demás hojas) a la punta, más clara y amarillenta
		base = c * mix(vec3(0.62, 0.66, 0.6), vec3(1.3, 1.25, 0.9), v_alto) * (0.85 + 0.3 * v_tono);
	}
	ALBEDO = base;
	NORMAL = normalize((VIEW_MATRIX * vec4(v_nw, 0.0)).xyz);
}

void light() {
	vec3 base = ALBEDO;
	vec3 rec = luz_recibida(v_nw, dot(NORMAL, LIGHT), ATTENUATION);
	// a contraluz el sol atraviesa las hojas
	float contra = pow(clamp(dot(VIEW, -LIGHT), 0.0, 1.0), 3.0);
	rec += atm_sol_col * vec3(0.5, 0.7, 0.2) * contra * v_alto * ATTENUATION * 0.6;
	vec3 col = tonos(base * rec);
	if (noche > 0.001) {
		col = mix(col, base * (vec3(0.045, 0.06, 0.12) + vec3(0.13, 0.17, 0.3) * 0.5), noche);
	}
	col = con_niebla(col, v_prof);
	DIFFUSE_LIGHT = col / max(base, vec3(0.002));
}
