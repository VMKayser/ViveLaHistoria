// Viñeta, grano de película y un leve tono cálido: la noche como recuerdo.
shader_type canvas_item;

uniform sampler2D pantalla : hint_screen_texture, filter_linear;
uniform float vineta = 0.55;
uniform float grano = 0.045;
uniform float calidez = 0.06;

float azar(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	vec3 c = texture(pantalla, SCREEN_UV).rgb;
	vec2 q = SCREEN_UV - 0.5;
	float v = 1.0 - dot(q, q) * vineta * 2.2;
	c *= clamp(v, 0.0, 1.0);
	c = mix(c, c * vec3(1.06, 1.0, 0.9), calidez);
	float g = azar(SCREEN_UV * vec2(1280.0, 720.0) + fract(TIME * 13.7) * 91.0) - 0.5;
	c += g * grano;
	COLOR = vec4(c, 1.0);
}
