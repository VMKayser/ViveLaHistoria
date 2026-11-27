// Cielo pintado (el de la web, web/src/ciudad/escena/Cielo.tsx): panorámica elegida por el usuario con ajuste de color y
// fundido al color del horizonte (continúa con la niebla). La imagen se gira para que el sol o la luna de la imagen caiga
// donde está la luz de la escena (desfase).
shader_type sky;
render_mode use_debanding;
uniform sampler2D mapa : source_color, filter_linear, repeat_enable;
uniform float desfase = 0.0;
uniform float exposicion = 1.0;
uniform float saturacion = 1.0;
uniform float contraste = 1.0;
uniform vec3 tinte : source_color = vec3(1.0);
uniform vec3 horizonte : source_color = vec3(0.6, 0.4, 0.35);

void sky() {
	vec3 d = normalize(EYEDIR);
	vec2 uv = vec2(atan(d.x, d.z) / (2.0 * PI) + 0.5 + desfase, 1.0 - (asin(clamp(d.y, -1.0, 1.0)) / PI + 0.5));
	vec3 c = texture(mapa, uv).rgb;
	c *= exposicion * tinte;
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(vec3(l), c, saturacion);
	c = (c - 0.5) * contraste + 0.5;
	c = mix(horizonte, c, smoothstep(-0.02, 0.16, d.y));
	COLOR = clamp(c, 0.0, 1.0);
}
