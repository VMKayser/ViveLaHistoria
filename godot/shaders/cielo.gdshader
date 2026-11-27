// Cielo que mezcla dos panoramas HDR (atardecer y noche) según la hora.
shader_type sky;

uniform sampler2D cielo_tarde : filter_linear, repeat_enable;
uniform sampler2D cielo_noche : filter_linear, repeat_enable;
uniform float mezcla : hint_range(0.0, 1.0) = 0.0;
uniform float energia_tarde = 1.0;
uniform float energia_noche = 1.0;
uniform float giro = 0.0;
uniform vec3 suelo : source_color = vec3(0.12, 0.1, 0.08);

void sky() {
	vec3 d = normalize(EYEDIR);
	float u = atan(d.x, -d.z) / (2.0 * PI) + 0.5 + giro;
	float v = acos(clamp(d.y, -1.0, 1.0)) / PI;
	vec2 uv = vec2(fract(u), clamp(v, 0.0, 0.5));
	vec3 a = texture(cielo_tarde, uv).rgb * energia_tarde;
	vec3 b = texture(cielo_noche, uv).rgb * energia_noche;
	vec3 c = mix(a, b, mezcla);
	// Bajo el horizonte: el color del horizonte se apaga hacia la tierra.
	float bajo = smoothstep(0.0, -0.15, d.y);
	COLOR = mix(c, suelo * (energia_tarde * (1.0 - mezcla) + energia_noche * mezcla), bajo);
}
