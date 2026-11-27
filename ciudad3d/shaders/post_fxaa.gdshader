// Antialias de pantalla (FXAA, versión liviana de Timothy Lottes): reemplaza al SMAA de la web. Va después del filtro
// pintado y del ajuste de color, sobre la imagen ya en sRGB.
shader_type canvas_item;
render_mode unshaded;
uniform sampler2D pantalla : hint_screen_texture, filter_linear, repeat_disable;

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 px = SCREEN_PIXEL_SIZE;
	vec3 rgbM = texture(pantalla, uv).rgb;
	vec3 rgbNW = texture(pantalla, uv + vec2(-1.0, -1.0) * px).rgb;
	vec3 rgbNE = texture(pantalla, uv + vec2(1.0, -1.0) * px).rgb;
	vec3 rgbSW = texture(pantalla, uv + vec2(-1.0, 1.0) * px).rgb;
	vec3 rgbSE = texture(pantalla, uv + vec2(1.0, 1.0) * px).rgb;
	float lM = luma(rgbM), lNW = luma(rgbNW), lNE = luma(rgbNE), lSW = luma(rgbSW), lSE = luma(rgbSE);
	float lMin = min(lM, min(min(lNW, lNE), min(lSW, lSE)));
	float lMax = max(lM, max(max(lNW, lNE), max(lSW, lSE)));
	if (lMax - lMin < max(0.0312, lMax * 0.125)) {
		COLOR = vec4(rgbM, 1.0);
	} else {
		vec2 dir = vec2(-((lNW + lNE) - (lSW + lSE)), ((lNW + lSW) - (lNE + lSE)));
		float reduce = max((lNW + lNE + lSW + lSE) * 0.25 * 0.125, 1.0 / 128.0);
		float rcp = 1.0 / (min(abs(dir.x), abs(dir.y)) + reduce);
		dir = clamp(dir * rcp, vec2(-8.0), vec2(8.0)) * px;
		vec3 a = 0.5 * (texture(pantalla, uv + dir * (1.0 / 3.0 - 0.5)).rgb + texture(pantalla, uv + dir * (2.0 / 3.0 - 0.5)).rgb);
		vec3 b = a * 0.5 + 0.25 * (texture(pantalla, uv - dir * 0.5).rgb + texture(pantalla, uv + dir * 0.5).rgb);
		float lb = luma(b);
		COLOR = vec4((lb < lMin || lb > lMax) ? a : b, 1.0);
	}
}
