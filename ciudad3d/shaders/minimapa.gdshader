shader_type canvas_item;
// Minimapa circular: a pie el mapa gira para que el frente quede arriba; en vista aérea el norte va arriba.
uniform sampler2D mapa : filter_linear, source_color;
uniform vec4 limites;      // x0, z0, x1, z1 (mundo)
uniform vec2 centro;       // mundo
uniform float radio = 85.0;
uniform float rumbo = 0.0;
uniform bool peaton = true;

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	if (length(p) > 1.0) {
		COLOR = vec4(0.0);
	} else {
		vec2 s = p * radio;
		float a = peaton ? rumbo : 0.0;
		vec2 w = vec2(s.x * cos(a) - s.y * sin(a), s.x * sin(a) + s.y * cos(a)) + centro;
		vec2 uv = (w - limites.xy) / (limites.zw - limites.xy);
		vec4 c = vec4(0.914, 0.886, 0.824, 1.0);
		if (uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0) {
			c = texture(mapa, uv);
		}
		COLOR = c;
	}
}
