// Oclusión ambiental en pantalla (como el N8AO de la web three.js: radio 2,5 m a pie, intensidad 2,2, color lavanda
// #5b5f86). El SSAO propio de Godot es solo de Forward+; este pase funciona en Compatibility (web) y Mobile (APK).
// Un rectángulo que cubre la pantalla lee la profundidad de lo opaco, reconstruye la posición y la normal de cada
// píxel y mira 'muestras' puntos en el hemisferio: lo que queda tapado oscurece. Se dibuja multiplicando (blend_mul)
// antes que los halos y los vidrios transparentes; el ruido que queda lo alisa después el filtro pintado.
shader_type spatial;
render_mode unshaded, blend_mul, depth_test_disabled, depth_draw_never, cull_disabled, fog_disabled, shadows_disabled;

uniform sampler2D profundidad : hint_depth_texture, filter_nearest, repeat_disable;
uniform int muestras = 12;
uniform float radio = 2.5;
uniform float intensidad = 2.2;
uniform float alcance = 120.0;          // m: más lejos no hay oclusión (y se ahorra el cálculo)
uniform bool depurar = false;
uniform vec3 color_ao = vec3(0.075, 0.085, 0.13);    // sombra fresca, casi neutra (antes lavanda #5b5f86)

void vertex() {
	POSITION = vec4(VERTEX.xy * 2.0, 0.0, 1.0);
}

vec3 vista(vec2 uv, mat4 inv_proy) {
	float d = texture(profundidad, uv).r;
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	vec3 ndc = vec3(uv * 2.0 - 1.0, d * 2.0 - 1.0);
#else
	vec3 ndc = vec3(uv * 2.0 - 1.0, d);
#endif
	vec4 v = inv_proy * vec4(ndc, 1.0);
	return v.xyz / v.w;
}

// ruido de gradiente intercalado (Jimenez): rota el patrón de muestras en cada píxel
float ign(vec2 p) { return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715)))); }

void fragment() {
	vec3 p = vista(SCREEN_UV, INV_PROJECTION_MATRIX);
	float dist = -p.z;
	float vis = 1.0;
	if (dist < alcance) {
		vec3 n = normalize(cross(dFdx(p), dFdy(p)));
		if (dot(n, p) > 0.0) n = -n;
		// base ortonormal alrededor de la normal, girada al azar por píxel
		float ang = ign(FRAGCOORD.xy) * 6.2831853;
		vec3 t = normalize(cross(n, abs(n.y) < 0.99 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0)));
		vec3 b = cross(n, t);
		t = t * cos(ang) + b * sin(ang);
		b = cross(n, t);
		float occ = 0.0;
		float r = radio;
		// margen: la profundidad de 24 bits pierde precisión con la distancia (sin él, un muro plano se tapa a sí mismo)
		float margen = 0.04 + dist * 0.006;
		p += n * margen;
		for (int i = 0; i < muestras; i++) {
			// espiral de Fibonacci en el hemisferio, más densa cerca del centro
			float fi = (float(i) + 0.5) / float(muestras);
			float az = float(i) * 2.39996323;
			float h = sqrt(fi);
			vec3 dir = normalize(t * cos(az) * h + b * sin(az) * h + n * max(sqrt(1.0 - fi), 0.35));
			vec3 q = p + dir * r * mix(0.2, 1.0, fi * fi);
			vec4 c = PROJECTION_MATRIX * vec4(q, 1.0);
			vec2 uv = c.xy / c.w * 0.5 + 0.5;
			if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) continue;
			float z = vista(uv, INV_PROJECTION_MATRIX).z;
			// tapa si la superficie en ese punto está delante de la muestra; sin contar lo que está mucho más cerca
			float rango = smoothstep(0.0, 1.0, r / max(abs(p.z - z), 1e-3));
			occ += step(q.z + margen, z) * rango;
		}
		// lo poco que queda en superficies planas (precisión de la profundidad) no oscurece: solo los rincones de verdad
		occ = max(occ / float(muestras) - 0.12, 0.0) / 0.88;
		vis = pow(clamp(1.0 - occ, 0.0, 1.0), intensidad);
		vis = mix(vis, 1.0, smoothstep(alcance * 0.6, alcance, dist));
	}
	ALBEDO = depurar ? vec3(vis) : mix(color_ao, vec3(1.0), vis);
#if CURRENT_RENDERER == RENDERER_MOBILE
	// el renderizador Mobile guarda el color de la escena dividido por 2 (búfer de 10 bits con margen HDR): multiplicar
	// por 1 lo oscurecería a la mitad
	ALBEDO *= 2.0;
#endif
}
