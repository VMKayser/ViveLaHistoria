// GENERADO por ciudad3d/herramientas/generar_post.py (no editar a mano).
// Imagen final: enfoque adaptativo (CAS) o filtro pintado (Kuwahara generalizado, 8 sectores), y el color: vibrancia,
// luces cálidas y sombras frescas, curva en S (en sRGB) y viñeta. Desde el 2026-11-26 (salto de calidad pedido por el
// usuario) el filtro pintado va suave y mezclado a medias: a pleno borroneaba las texturas.
shader_type canvas_item;
render_mode unshaded;
uniform sampler2D pantalla : hint_screen_texture, filter_linear, repeat_disable;
uniform bool pintado = true;
uniform float radio = 3.5;
uniform float mezcla = 0.45;
uniform float enfoque = 0.25;            // enfoque adaptativo al contraste (0 = nada)
uniform float vibrancia = 0.22;          // satura más lo poco saturado (no quema los colores fuertes)
uniform vec3 tinte_luces = vec3(1.025, 1.0, 0.965);
uniform vec3 tinte_sombras = vec3(0.95, 0.985, 1.05);
uniform float nitidez = 8.0;
uniform float saturacion = 0.12;
uniform float contraste = 0.07;
uniform float vineta = 0.35;
uniform float vineta_desfase = 0.3;

// la pantalla llega en sRGB: aproximación barata a lineal (γ = 2) para el filtro, exacta para el color final
vec3 lin(vec3 c) { return c * c; }
vec3 a_lineal(vec3 c) { return mix(pow((c + 0.055) / 1.055, vec3(2.4)), c / 12.92, step(c, vec3(0.04045))); }
vec3 a_srgb(vec3 c) { c = max(c, vec3(0.0)); return mix(1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, 12.92 * c, step(c, vec3(0.0031308))); }

void fragment() {
	vec2 uv = SCREEN_UV;
	vec3 color = a_lineal(texture(pantalla, uv).rgb);
	if (pintado) {
		vec2 paso = (radio / 4.0) * SCREEN_PIXEL_SIZE;
		vec3 c, c2;
		vec3 m0 = vec3(0.0), s0 = vec3(0.0); vec3 m1 = vec3(0.0), s1 = vec3(0.0); vec3 m2 = vec3(0.0), s2 = vec3(0.0); vec3 m3 = vec3(0.0), s3 = vec3(0.0); vec3 m4 = vec3(0.0), s4 = vec3(0.0); vec3 m5 = vec3(0.0), s5 = vec3(0.0); vec3 m6 = vec3(0.0), s6 = vec3(0.0); vec3 m7 = vec3(0.0), s7 = vec3(0.0);
		c = lin(texture(pantalla, uv + vec2(0.0, -4.0) * paso).rgb); c2 = c * c; m5 += c * 0.00622; s5 += c2 * 0.00622; m6 += c * 0.04979; s6 += c2 * 0.04979; m7 += c * 0.00622; s7 += c2 * 0.00622;
		c = lin(texture(pantalla, uv + vec2(-2.0, -3.0) * paso).rgb); c2 = c * c; m4 += c * 0.00255; s4 += c2 * 0.00255; m5 += c * 0.07768; s5 += c2 * 0.07768; m6 += c * 0.02899; s6 += c2 * 0.02899;
		c = lin(texture(pantalla, uv + vec2(-1.0, -3.0) * paso).rgb); c2 = c * c; m5 += c * 0.07852; s5 += c2 * 0.07852; m6 += c * 0.11180; s6 += c2 * 0.11180;
		c = lin(texture(pantalla, uv + vec2(0.0, -3.0) * paso).rgb); c2 = c * c; m5 += c * 0.02312; s5 += c2 * 0.02312; m6 += c * 0.18498; s6 += c2 * 0.18498; m7 += c * 0.02312; s7 += c2 * 0.02312;
		c = lin(texture(pantalla, uv + vec2(1.0, -3.0) * paso).rgb); c2 = c * c; m6 += c * 0.11180; s6 += c2 * 0.11180; m7 += c * 0.07852; s7 += c2 * 0.07852;
		c = lin(texture(pantalla, uv + vec2(2.0, -3.0) * paso).rgb); c2 = c * c; m0 += c * 0.00255; s0 += c2 * 0.00255; m6 += c * 0.02899; s6 += c2 * 0.02899; m7 += c * 0.07768; s7 += c2 * 0.07768;
		c = lin(texture(pantalla, uv + vec2(-3.0, -2.0) * paso).rgb); c2 = c * c; m4 += c * 0.02899; s4 += c2 * 0.02899; m5 += c * 0.07768; s5 += c2 * 0.07768; m6 += c * 0.00255; s6 += c2 * 0.00255;
		c = lin(texture(pantalla, uv + vec2(-2.0, -2.0) * paso).rgb); c2 = c * c; m4 += c * 0.02789; s4 += c2 * 0.02789; m5 += c * 0.22313; s5 += c2 * 0.22313; m6 += c * 0.02789; s6 += c2 * 0.02789;
		c = lin(texture(pantalla, uv + vec2(-1.0, -2.0) * paso).rgb); c2 = c * c; m4 += c * 0.00313; s4 += c2 * 0.00313; m5 += c * 0.28548; s5 += c2 * 0.28548; m6 += c * 0.20050; s6 += c2 * 0.20050;
		c = lin(texture(pantalla, uv + vec2(0.0, -2.0) * paso).rgb); c2 = c * c; m5 += c * 0.05905; s5 += c2 * 0.05905; m6 += c * 0.47237; s6 += c2 * 0.47237; m7 += c * 0.05905; s7 += c2 * 0.05905;
		c = lin(texture(pantalla, uv + vec2(1.0, -2.0) * paso).rgb); c2 = c * c; m0 += c * 0.00313; s0 += c2 * 0.00313; m6 += c * 0.20050; s6 += c2 * 0.20050; m7 += c * 0.28548; s7 += c2 * 0.28548;
		c = lin(texture(pantalla, uv + vec2(2.0, -2.0) * paso).rgb); c2 = c * c; m0 += c * 0.02789; s0 += c2 * 0.02789; m6 += c * 0.02789; s6 += c2 * 0.02789; m7 += c * 0.22313; s7 += c2 * 0.22313;
		c = lin(texture(pantalla, uv + vec2(3.0, -2.0) * paso).rgb); c2 = c * c; m0 += c * 0.02899; s0 += c2 * 0.02899; m6 += c * 0.00255; s6 += c2 * 0.00255; m7 += c * 0.07768; s7 += c2 * 0.07768;
		c = lin(texture(pantalla, uv + vec2(-3.0, -1.0) * paso).rgb); c2 = c * c; m4 += c * 0.11180; s4 += c2 * 0.11180; m5 += c * 0.07852; s5 += c2 * 0.07852;
		c = lin(texture(pantalla, uv + vec2(-2.0, -1.0) * paso).rgb); c2 = c * c; m4 += c * 0.20050; s4 += c2 * 0.20050; m5 += c * 0.28548; s5 += c2 * 0.28548; m6 += c * 0.00313; s6 += c2 * 0.00313;
		c = lin(texture(pantalla, uv + vec2(-1.0, -1.0) * paso).rgb); c2 = c * c; m4 += c * 0.08591; s4 += c2 * 0.08591; m5 += c * 0.68729; s5 += c2 * 0.68729; m6 += c * 0.08591; s6 += c2 * 0.08591;
		c = lin(texture(pantalla, uv + vec2(0.0, -1.0) * paso).rgb); c2 = c * c; m5 += c * 0.10363; s5 += c2 * 0.10363; m6 += c * 0.82903; s6 += c2 * 0.82903; m7 += c * 0.10363; s7 += c2 * 0.10363;
		c = lin(texture(pantalla, uv + vec2(1.0, -1.0) * paso).rgb); c2 = c * c; m0 += c * 0.08591; s0 += c2 * 0.08591; m6 += c * 0.08591; s6 += c2 * 0.08591; m7 += c * 0.68729; s7 += c2 * 0.68729;
		c = lin(texture(pantalla, uv + vec2(2.0, -1.0) * paso).rgb); c2 = c * c; m0 += c * 0.20050; s0 += c2 * 0.20050; m6 += c * 0.00313; s6 += c2 * 0.00313; m7 += c * 0.28548; s7 += c2 * 0.28548;
		c = lin(texture(pantalla, uv + vec2(3.0, -1.0) * paso).rgb); c2 = c * c; m0 += c * 0.11180; s0 += c2 * 0.11180; m7 += c * 0.07852; s7 += c2 * 0.07852;
		c = lin(texture(pantalla, uv + vec2(-4.0, 0.0) * paso).rgb); c2 = c * c; m3 += c * 0.00622; s3 += c2 * 0.00622; m4 += c * 0.04979; s4 += c2 * 0.04979; m5 += c * 0.00622; s5 += c2 * 0.00622;
		c = lin(texture(pantalla, uv + vec2(-3.0, 0.0) * paso).rgb); c2 = c * c; m3 += c * 0.02312; s3 += c2 * 0.02312; m4 += c * 0.18498; s4 += c2 * 0.18498; m5 += c * 0.02312; s5 += c2 * 0.02312;
		c = lin(texture(pantalla, uv + vec2(-2.0, 0.0) * paso).rgb); c2 = c * c; m3 += c * 0.05905; s3 += c2 * 0.05905; m4 += c * 0.47237; s4 += c2 * 0.47237; m5 += c * 0.05905; s5 += c2 * 0.05905;
		c = lin(texture(pantalla, uv + vec2(-1.0, 0.0) * paso).rgb); c2 = c * c; m3 += c * 0.10363; s3 += c2 * 0.10363; m4 += c * 0.82903; s4 += c2 * 0.82903; m5 += c * 0.10363; s5 += c2 * 0.10363;
		c = lin(texture(pantalla, uv + vec2(0.0, 0.0) * paso).rgb); c2 = c * c; m0 += c * 0.12500; s0 += c2 * 0.12500; m1 += c * 0.12500; s1 += c2 * 0.12500; m2 += c * 0.12500; s2 += c2 * 0.12500; m3 += c * 0.12500; s3 += c2 * 0.12500; m4 += c * 0.12500; s4 += c2 * 0.12500; m5 += c * 0.12500; s5 += c2 * 0.12500; m6 += c * 0.12500; s6 += c2 * 0.12500; m7 += c * 0.12500; s7 += c2 * 0.12500;
		c = lin(texture(pantalla, uv + vec2(1.0, 0.0) * paso).rgb); c2 = c * c; m0 += c * 0.82903; s0 += c2 * 0.82903; m1 += c * 0.10363; s1 += c2 * 0.10363; m7 += c * 0.10363; s7 += c2 * 0.10363;
		c = lin(texture(pantalla, uv + vec2(2.0, 0.0) * paso).rgb); c2 = c * c; m0 += c * 0.47237; s0 += c2 * 0.47237; m1 += c * 0.05905; s1 += c2 * 0.05905; m7 += c * 0.05905; s7 += c2 * 0.05905;
		c = lin(texture(pantalla, uv + vec2(3.0, 0.0) * paso).rgb); c2 = c * c; m0 += c * 0.18498; s0 += c2 * 0.18498; m1 += c * 0.02312; s1 += c2 * 0.02312; m7 += c * 0.02312; s7 += c2 * 0.02312;
		c = lin(texture(pantalla, uv + vec2(4.0, 0.0) * paso).rgb); c2 = c * c; m0 += c * 0.04979; s0 += c2 * 0.04979; m1 += c * 0.00622; s1 += c2 * 0.00622; m7 += c * 0.00622; s7 += c2 * 0.00622;
		c = lin(texture(pantalla, uv + vec2(-3.0, 1.0) * paso).rgb); c2 = c * c; m3 += c * 0.07852; s3 += c2 * 0.07852; m4 += c * 0.11180; s4 += c2 * 0.11180;
		c = lin(texture(pantalla, uv + vec2(-2.0, 1.0) * paso).rgb); c2 = c * c; m2 += c * 0.00313; s2 += c2 * 0.00313; m3 += c * 0.28548; s3 += c2 * 0.28548; m4 += c * 0.20050; s4 += c2 * 0.20050;
		c = lin(texture(pantalla, uv + vec2(-1.0, 1.0) * paso).rgb); c2 = c * c; m2 += c * 0.08591; s2 += c2 * 0.08591; m3 += c * 0.68729; s3 += c2 * 0.68729; m4 += c * 0.08591; s4 += c2 * 0.08591;
		c = lin(texture(pantalla, uv + vec2(0.0, 1.0) * paso).rgb); c2 = c * c; m1 += c * 0.10363; s1 += c2 * 0.10363; m2 += c * 0.82903; s2 += c2 * 0.82903; m3 += c * 0.10363; s3 += c2 * 0.10363;
		c = lin(texture(pantalla, uv + vec2(1.0, 1.0) * paso).rgb); c2 = c * c; m0 += c * 0.08591; s0 += c2 * 0.08591; m1 += c * 0.68729; s1 += c2 * 0.68729; m2 += c * 0.08591; s2 += c2 * 0.08591;
		c = lin(texture(pantalla, uv + vec2(2.0, 1.0) * paso).rgb); c2 = c * c; m0 += c * 0.20050; s0 += c2 * 0.20050; m1 += c * 0.28548; s1 += c2 * 0.28548; m2 += c * 0.00313; s2 += c2 * 0.00313;
		c = lin(texture(pantalla, uv + vec2(3.0, 1.0) * paso).rgb); c2 = c * c; m0 += c * 0.11180; s0 += c2 * 0.11180; m1 += c * 0.07852; s1 += c2 * 0.07852;
		c = lin(texture(pantalla, uv + vec2(-3.0, 2.0) * paso).rgb); c2 = c * c; m2 += c * 0.00255; s2 += c2 * 0.00255; m3 += c * 0.07768; s3 += c2 * 0.07768; m4 += c * 0.02899; s4 += c2 * 0.02899;
		c = lin(texture(pantalla, uv + vec2(-2.0, 2.0) * paso).rgb); c2 = c * c; m2 += c * 0.02789; s2 += c2 * 0.02789; m3 += c * 0.22313; s3 += c2 * 0.22313; m4 += c * 0.02789; s4 += c2 * 0.02789;
		c = lin(texture(pantalla, uv + vec2(-1.0, 2.0) * paso).rgb); c2 = c * c; m2 += c * 0.20050; s2 += c2 * 0.20050; m3 += c * 0.28548; s3 += c2 * 0.28548; m4 += c * 0.00313; s4 += c2 * 0.00313;
		c = lin(texture(pantalla, uv + vec2(0.0, 2.0) * paso).rgb); c2 = c * c; m1 += c * 0.05905; s1 += c2 * 0.05905; m2 += c * 0.47237; s2 += c2 * 0.47237; m3 += c * 0.05905; s3 += c2 * 0.05905;
		c = lin(texture(pantalla, uv + vec2(1.0, 2.0) * paso).rgb); c2 = c * c; m0 += c * 0.00313; s0 += c2 * 0.00313; m1 += c * 0.28548; s1 += c2 * 0.28548; m2 += c * 0.20050; s2 += c2 * 0.20050;
		c = lin(texture(pantalla, uv + vec2(2.0, 2.0) * paso).rgb); c2 = c * c; m0 += c * 0.02789; s0 += c2 * 0.02789; m1 += c * 0.22313; s1 += c2 * 0.22313; m2 += c * 0.02789; s2 += c2 * 0.02789;
		c = lin(texture(pantalla, uv + vec2(3.0, 2.0) * paso).rgb); c2 = c * c; m0 += c * 0.02899; s0 += c2 * 0.02899; m1 += c * 0.07768; s1 += c2 * 0.07768; m2 += c * 0.00255; s2 += c2 * 0.00255;
		c = lin(texture(pantalla, uv + vec2(-2.0, 3.0) * paso).rgb); c2 = c * c; m2 += c * 0.02899; s2 += c2 * 0.02899; m3 += c * 0.07768; s3 += c2 * 0.07768; m4 += c * 0.00255; s4 += c2 * 0.00255;
		c = lin(texture(pantalla, uv + vec2(-1.0, 3.0) * paso).rgb); c2 = c * c; m2 += c * 0.11180; s2 += c2 * 0.11180; m3 += c * 0.07852; s3 += c2 * 0.07852;
		c = lin(texture(pantalla, uv + vec2(0.0, 3.0) * paso).rgb); c2 = c * c; m1 += c * 0.02312; s1 += c2 * 0.02312; m2 += c * 0.18498; s2 += c2 * 0.18498; m3 += c * 0.02312; s3 += c2 * 0.02312;
		c = lin(texture(pantalla, uv + vec2(1.0, 3.0) * paso).rgb); c2 = c * c; m1 += c * 0.07852; s1 += c2 * 0.07852; m2 += c * 0.11180; s2 += c2 * 0.11180;
		c = lin(texture(pantalla, uv + vec2(2.0, 3.0) * paso).rgb); c2 = c * c; m0 += c * 0.00255; s0 += c2 * 0.00255; m1 += c * 0.07768; s1 += c2 * 0.07768; m2 += c * 0.02899; s2 += c2 * 0.02899;
		c = lin(texture(pantalla, uv + vec2(0.0, 4.0) * paso).rgb); c2 = c * c; m1 += c * 0.00622; s1 += c2 * 0.00622; m2 += c * 0.04979; s2 += c2 * 0.04979; m3 += c * 0.00622; s3 += c2 * 0.00622;
		vec3 acc = vec3(0.0);
		float wacc = 0.0;
		vec3 mk, vk;
		float alfa;
	mk = m0 / 2.58271; vk = abs(s0 / 2.58271 - mk * mk);
	alfa = 1.0 / (1.0 + pow((vk.r + vk.g + vk.b) * 1000.0, 0.5 * nitidez));
	acc += mk * alfa; wacc += alfa;
	mk = m1 / 2.30282; vk = abs(s1 / 2.30282 - mk * mk);
	alfa = 1.0 / (1.0 + pow((vk.r + vk.g + vk.b) * 1000.0, 0.5 * nitidez));
	acc += mk * alfa; wacc += alfa;
	mk = m2 / 2.58271; vk = abs(s2 / 2.58271 - mk * mk);
	alfa = 1.0 / (1.0 + pow((vk.r + vk.g + vk.b) * 1000.0, 0.5 * nitidez));
	acc += mk * alfa; wacc += alfa;
	mk = m3 / 2.30282; vk = abs(s3 / 2.30282 - mk * mk);
	alfa = 1.0 / (1.0 + pow((vk.r + vk.g + vk.b) * 1000.0, 0.5 * nitidez));
	acc += mk * alfa; wacc += alfa;
	mk = m4 / 2.58271; vk = abs(s4 / 2.58271 - mk * mk);
	alfa = 1.0 / (1.0 + pow((vk.r + vk.g + vk.b) * 1000.0, 0.5 * nitidez));
	acc += mk * alfa; wacc += alfa;
	mk = m5 / 2.30282; vk = abs(s5 / 2.30282 - mk * mk);
	alfa = 1.0 / (1.0 + pow((vk.r + vk.g + vk.b) * 1000.0, 0.5 * nitidez));
	acc += mk * alfa; wacc += alfa;
	mk = m6 / 2.58271; vk = abs(s6 / 2.58271 - mk * mk);
	alfa = 1.0 / (1.0 + pow((vk.r + vk.g + vk.b) * 1000.0, 0.5 * nitidez));
	acc += mk * alfa; wacc += alfa;
	mk = m7 / 2.30282; vk = abs(s7 / 2.30282 - mk * mk);
	alfa = 1.0 / (1.0 + pow((vk.r + vk.g + vk.b) * 1000.0, 0.5 * nitidez));
	acc += mk * alfa; wacc += alfa;
		vec3 pintura = acc / max(wacc, 1e-5);
		// la pintura se calculó con γ = 2: se vuelve a lineal exacto pasando por sRGB aproximado
		color = mix(color, a_lineal(sqrt(pintura)), mezcla);
	}
	if (enfoque > 0.0) {
		// enfoque adaptativo al contraste (AMD CAS, simplificado): devuelve la textura que pierden el escalado y la
		// mezcla del filtro, sin halos en los bordes fuertes
		vec2 px = SCREEN_PIXEL_SIZE;
		vec3 n = a_lineal(texture(pantalla, uv + vec2(0.0, -px.y)).rgb);
		vec3 s = a_lineal(texture(pantalla, uv + vec2(0.0, px.y)).rgb);
		vec3 e = a_lineal(texture(pantalla, uv + vec2(px.x, 0.0)).rgb);
		vec3 o = a_lineal(texture(pantalla, uv + vec2(-px.x, 0.0)).rgb);
		vec3 mn = min(color, min(min(n, s), min(e, o)));
		vec3 mx = max(color, max(max(n, s), max(e, o)));
		vec3 amp = sqrt(clamp(min(mn, 1.0 - mx) / max(mx, vec3(1e-4)), 0.0, 1.0));
		vec3 w = -amp * mix(0.125, 0.2, enfoque);
		color = clamp((color + (n + s + e + o) * w) / (1.0 + 4.0 * w), 0.0, 1.0);
	}
	// saturación de la hora + vibrancia
	float media = (color.r + color.g + color.b) / 3.0;
	if (saturacion > 0.0) {
		color += (media - color) * (1.0 - 1.0 / (1.001 - saturacion));
	} else {
		color += (media - color) * (-saturacion);
	}
	float sat = (max(color.r, max(color.g, color.b)) - min(color.r, min(color.g, color.b))) / max(max(color.r, max(color.g, color.b)), 1e-4);
	color = max(mix(vec3(dot(color, vec3(0.2126, 0.7152, 0.0722))), color, 1.0 + vibrancia * (1.0 - sat)), vec3(0.0));
	// luces cálidas, sombras frescas
	float l = clamp(dot(color, vec3(0.2126, 0.7152, 0.0722)) * 2.0, 0.0, 1.0);
	color *= mix(tinte_sombras, tinte_luces, smoothstep(0.08, 0.7, l));
	// contraste en sRGB con curva en S suave (sin cortar negros ni blancos)
	vec3 cs = clamp(a_srgb(color), 0.0, 1.0);
	vec3 curva = cs * cs * (3.0 - 2.0 * cs);
	cs = mix(cs, curva, contraste * 2.2);
	color = a_lineal(cs);
	// VignetteEffect (técnica por defecto)
	float d = distance(uv, vec2(0.5));
	color *= smoothstep(0.8, vineta_desfase * 0.799, d * (vineta + vineta_desfase));
	COLOR = vec4(a_srgb(color), 1.0);
}
