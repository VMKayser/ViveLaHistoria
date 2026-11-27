#!/usr/bin/env python3
"""Genera shaders/post_pintado.gdshader: el filtro "pintado a mano" de pantalla completa (Kuwahara generalizado de
Papari et al., 8 sectores con pesos suaves) + el ajuste de color de la imagen final (saturación, contraste, viñeta).

Igual que el de la web (web/src/ciudad/motor/FiltroPintado.ts, medido en una Intel UHD: 56 → 9,6 ms): los pesos (radial
gaussiano × lóbulo cos⁶ de cada sector) dependen solo de la posición de la muestra, así que el shader se GENERA
desenrollado con los pesos como constantes y cada muestra suma solo a los sectores donde pesa (umbral 0,002); R = 4.
    python3 ciudad3d/herramientas/generar_post.py
"""
import math
import os

R = 4
UMBRAL = 0.002
total = [0.0] * 8
lineas = []
for j in range(-R, R + 1):
    for i in range(-R, R + 1):
        vx, vy = i / R, j / R
        d2 = vx * vx + vy * vy
        if d2 > 1:
            continue
        g = math.exp(-3.0 * d2)
        ang = math.atan2(vy, vx)
        terminos = []
        for k in range(8):
            cw = 0.125 if d2 < 1e-4 else max(0.0, math.cos(ang - k * 0.7853982)) ** 6
            pw = g * cw
            if pw < UMBRAL:
                continue
            total[k] += pw
            terminos.append(f"m{k} += c * {pw:.5f}; s{k} += c2 * {pw:.5f};")
        if terminos:
            # el +y de la web (uv hacia arriba) es −y en la pantalla de Godot: da igual, el filtro es simétrico
            lineas.append(f"c = lin(texture(pantalla, uv + vec2({i}.0, {j}.0) * paso).rgb); c2 = c * c; " + " ".join(terminos))

sectores = "\n".join(
    f"\tmk = m{k} / {total[k]:.5f}; vk = abs(s{k} / {total[k]:.5f} - mk * mk);\n"
    f"\talfa = 1.0 / (1.0 + pow((vk.r + vk.g + vk.b) * 1000.0, 0.5 * nitidez));\n"
    f"\tacc += mk * alfa; wacc += alfa;" for k in range(8))

codigo = f"""// GENERADO por ciudad3d/herramientas/generar_post.py (no editar a mano).
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
vec3 lin(vec3 c) {{ return c * c; }}
vec3 a_lineal(vec3 c) {{ return mix(pow((c + 0.055) / 1.055, vec3(2.4)), c / 12.92, step(c, vec3(0.04045))); }}
vec3 a_srgb(vec3 c) {{ c = max(c, vec3(0.0)); return mix(1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, 12.92 * c, step(c, vec3(0.0031308))); }}

void fragment() {{
	vec2 uv = SCREEN_UV;
	vec3 color = a_lineal(texture(pantalla, uv).rgb);
	if (pintado) {{
		vec2 paso = (radio / {R}.0) * SCREEN_PIXEL_SIZE;
		vec3 c, c2;
		{" ".join(f"vec3 m{k} = vec3(0.0), s{k} = vec3(0.0);" for k in range(8))}
		{chr(10).join(chr(9) * 2 + l for l in lineas).lstrip()}
		vec3 acc = vec3(0.0);
		float wacc = 0.0;
		vec3 mk, vk;
		float alfa;
{sectores}
		vec3 pintura = acc / max(wacc, 1e-5);
		// la pintura se calculó con γ = 2: se vuelve a lineal exacto pasando por sRGB aproximado
		color = mix(color, a_lineal(sqrt(pintura)), mezcla);
	}}
	if (enfoque > 0.0) {{
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
	}}
	// saturación de la hora + vibrancia
	float media = (color.r + color.g + color.b) / 3.0;
	if (saturacion > 0.0) {{
		color += (media - color) * (1.0 - 1.0 / (1.001 - saturacion));
	}} else {{
		color += (media - color) * (-saturacion);
	}}
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
}}
"""
destino = os.path.join(os.path.dirname(__file__), "..", "shaders", "post_pintado.gdshader")
open(destino, "w").write(codigo)
print(f"{len(lineas)} muestras → {os.path.normpath(destino)}")
