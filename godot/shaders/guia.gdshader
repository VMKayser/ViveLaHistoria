// Columna de luz tenue que marca hacia dónde ir.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.8, 0.45);
uniform float alto = 30.0;
uniform float fuerza = 0.6;

varying float h;

void vertex() {
	h = clamp(VERTEX.y / alto + 0.5, 0.0, 1.0);
}

void fragment() {
	float borde = pow(1.0 - abs(dot(NORMAL, VIEW)), 1.5);
	float pulso = 0.75 + 0.25 * sin(TIME * 2.2);
	ALBEDO = color * pow(1.0 - h, 2.2) * (0.25 + borde) * fuerza * pulso;
}
