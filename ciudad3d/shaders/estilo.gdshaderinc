// Estilo de la ciudad: fondo de animación pintado a mano (el mismo de la web three.js, web/src/ciudad/motor/estilo.ts,
// hasta el 2026-11-25; desde entonces este es el original).
//  - variación "pintada" por rol (cal a brocha con desconchados, sillares, vetas, follaje en dos tonos, baldosas, asfalto
//    con parches), relieve de acuarela triplanar y atlas de DETALLE (una variante por zona de ~30 m);
//  - luz en 3 franjas suaves: sombra teñida de lavanda, medio tono rosado y luz cálida; la cantidad de luz se calcula
//    como en la web (luz de relleno hemisférica + sol) con los valores de la hora del día (scripts/hora.gd);
//  - vidrio: 8 tipos elegidos por el usuario, el mismo en todo un edificio (número de edificio en COLOR.a);
//  - niebla propia (smoothstep, como la web) y noche con los faroles más cercanos.
// Colores de entrada (COLOR de vértice): lineales.
//
// UN SOLO shader para la ciudad, los cerros, las copas y los vehículos (pedido del usuario, 2026-11-26: la carga tardaba
// demasiado). En WebGL, Godot compila cuatro variantes de cada shader distinto al usarlo por primera vez (~4–5 s por
// shader en la primera visita); antes había cuatro (ciudad, copas de doble cara, cerros y vehículos). Ahora:
//  - cerros: el mismo material con sin_niebla;
//  - copas: el empaquetador duplica sus caras con la normal invertida y UV.y = 1 (cara trasera), que aquí recupera la
//    normal de la cara delantera, igual que hacía el material de doble cara (cull_disabled);
//  - vehículos: 'movil' (uniforme) elige sus parámetros y su patrón en coordenadas del objeto.
varying vec3 v_pos;
varying vec3 v_nor;
varying vec3 v_cam;
varying float v_prof;
varying float v_edif;
varying flat int v_rol;           // ciudad: rol del material (UV.x): sus parámetros salen de los arreglos de abajo
varying vec3 v_patron;            // vehículos: posición en el objeto (el patrón no resbala al moverse)
varying float v_tipo_v;           // vehículos: pieza (UV2.x): pintura, detalle, faro, piloto, interior
#ifdef HOJAS
varying vec2 v_hoja_uv;           // racimos: coordenada en el atlas de hojas
varying float v_hoja_tono;        // racimos: variación de color de cada racimo
uniform sampler2D hojas : source_color, filter_linear_mipmap, repeat_disable, hint_default_white;
#endif

uniform bool comp_srgb = false;   // renderizador de compatibilidad: el color de vértice llega como sRGB → se reconvierte
#include "res://shaders/luz.gdshaderinc"
global uniform vec4 farol_0;
global uniform vec4 farol_1;
global uniform vec4 farol_2;
global uniform vec4 farol_3;
global uniform vec4 farol_4;
global uniform vec4 farol_5;
global uniform vec4 farol_6;
global uniform vec4 farol_7;
global uniform vec4 farol_8;
global uniform vec4 farol_9;
global uniform vec4 farol_10;
global uniform vec4 farol_11;
global uniform vec4 farol_12;
global uniform vec4 farol_13;
global uniform vec4 farol_14;
global uniform vec4 farol_15;
uniform vec3 color_farol = vec3(1.0, 0.62, 0.26);
uniform vec3 color_ventana = vec3(1.0, 0.7, 0.38);
uniform vec3 amb_noche = vec3(0.045, 0.06, 0.12);
uniform vec3 luna_noche = vec3(0.13, 0.17, 0.3);

// Toda una tesela con un solo material (scripts/estilo.gd): por rol, rol_a = (escala, amplitud, tipo, capa de relieve o −1),
// rol_b = (metros por repetición del relieve, fuerza, primera capa de detalle o −1, variantes), rol_c = (metros por
// repetición del detalle, fuerza, relieve en metros para la normal, brillo). Relieve y detalle son arreglos de texturas (herramientas/capas_textura.py).
const int MAX_ROLES = 32;
uniform vec4 rol_a[MAX_ROLES];
uniform vec4 rol_b[MAX_ROLES];
uniform vec4 rol_c[MAX_ROLES];
uniform sampler2DArray capas_relieve : filter_linear_mipmap, repeat_enable, hint_default_white;
uniform sampler2DArray capas_detalle : filter_linear_mipmap_anisotropic, repeat_enable, hint_default_white;
// vehículos: un material por pieza y color, con su pintura en uniformes (no usan los arreglos por rol)
uniform bool movil = false;
uniform float escala = 0.5;
uniform float amplitud = 0.05;
uniform int tipo = 0;
uniform sampler2D reflejo : source_color, filter_linear, repeat_enable, hint_default_black;
uniform vec3 sombra_tinte = vec3(0.64, 0.64, 0.82);
uniform vec3 calido = vec3(1.07, 0.99, 0.87);
uniform vec3 cielo_bajo = vec3(0.3324, 0.5457, 0.8228);   // #9cc3ea lineal
uniform bool sin_niebla = false;
// vehículos: color de la unidad (un material por variante de color)
uniform vec3 pintura = vec3(0.8);
uniform vec3 pintura_detalle = vec3(0.2);

float hash3(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
float ruido(vec3 p) {
	vec3 i = floor(p); vec3 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash3(i), hash3(i + vec3(1, 0, 0)), f.x), mix(hash3(i + vec3(0, 1, 0)), hash3(i + vec3(1, 1, 0)), f.x), f.y),
			mix(mix(hash3(i + vec3(0, 0, 1)), hash3(i + vec3(1, 0, 1)), f.x), mix(hash3(i + vec3(0, 1, 1)), hash3(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}
float fbm(vec3 p) { return 0.55 * ruido(p) + 0.3 * ruido(p * 2.1) + 0.15 * ruido(p * 4.3); }

float luz_farol(vec4 f, vec3 p, vec3 n) {
	if (f.w <= 0.0) {
		return 0.0;
	}
	vec3 d = f.xyz - p;
	float d2 = dot(d, d);
	float a = 1.0 - d2 / (f.w * f.w);
	if (a <= 0.0) {
		return 0.0;
	}
	float nl = clamp(dot(n, d * inversesqrt(d2 + 1e-4)) * 0.85 + 0.15, 0.0, 1.0);
	return a * a * nl;
}

void vertex() {
#ifdef HOJAS
	// racimo de hojas: los cuatro vértices traen el centro; aquí se abre el cuadro en el plano de la cámara (en el pase de
	// sombras, la "cámara" es el sol: la sombra también es de hojas), girado al azar y mecido por el viento
	float codigo = UV.y;
	float esquina = mod(codigo, 4.0);
	float variante = mod(floor(codigo / 4.0), 4.0);
	float tam = floor(codigo / 16.0) / 100.0;
	vec2 e = vec2(mod(esquina, 2.0), floor(esquina / 2.0));
	vec3 centro = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float az = hash3(floor(centro * 7.0)) * 6.2831853;
	vec2 q = (e - 0.5) * tam;
	q = vec2(q.x * cos(az) - q.y * sin(az), q.x * sin(az) + q.y * cos(az));
	vec3 viento = vec3(sin(TIME * 1.3 + centro.x * 0.35 + centro.z * 0.2), 0.0, cos(TIME * 1.1 + centro.z * 0.3)) * 0.05
		+ vec3(sin(TIME * 3.7 + centro.y * 2.0 + centro.x), sin(TIME * 4.1 + centro.z), 0.0) * 0.025 * tam;
	VERTEX += mat3(INV_VIEW_MATRIX) * vec3(q, 0.0) + viento;
	v_hoja_uv = (vec2(mod(variante, 2.0), floor(variante / 2.0)) + e) * 0.5;
	v_hoja_tono = hash3(floor(centro * 3.0) + 0.5);
#endif
	v_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_nor = normalize(mat3(MODEL_MATRIX) * NORMAL);
	v_cam = (INV_VIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	v_prof = -(MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).z;
	v_edif = COLOR.a;
	v_rol = int(UV.x + 0.5);
	v_patron = VERTEX;
	v_tipo_v = UV2.x;
	if (movil) {
		if (UV2.x > 0.5 && UV2.x < 1.5) {
			COLOR.rgb = pintura;
		} else if (UV2.x > 1.5 && UV2.x < 2.5) {
			COLOR.rgb = pintura_detalle;
		}
	} else if (UV.y > 0.5) {
#ifndef HOJAS
		v_nor = -v_nor;             // cara trasera de una copa: la normal de la delantera (ver arriba)
#endif
	}
}

vec3 color_base(vec3 c) {
	if (comp_srgb) {
		return mix(1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, 12.92 * c, step(c, vec3(0.0031308)));
	}
	return c;
}

void fragment() {
	vec3 base = color_base(COLOR.rgb);
#ifdef HOJAS
	vec4 h = texture(hojas, v_hoja_uv);
	ALPHA = h.a;
	// el recorte se afloja con la distancia: en los mipmaps el alfa se diluye y la copa se "pelaría"
	ALPHA_SCISSOR_THRESHOLD = mix(0.5, 0.28, smoothstep(15.0, 90.0, v_prof));
	// cada hoja con su tono (textura) y cada racimo con el suyo: de amarillo verdoso a verde azulado
	base *= 0.45 + 0.75 * h.r;
	float tr = v_hoja_tono - 0.5;
	base *= vec3(1.0 + tr * 0.45, 1.0 + tr * 0.18, 1.0 - tr * 0.3) * (0.92 + 0.16 * hash3(floor(v_pos * 1.7)));
#endif
	// vehículos: sus uniformes, sin relieve ni detalle (capa −1)
	vec4 pa = movil ? vec4(escala, amplitud, float(tipo), -1.0) : rol_a[v_rol];
	vec4 pb = movil ? vec4(1.0, 0.0, -1.0, 1.0) : rol_b[v_rol];
	vec4 pc = movil ? vec4(1.0, 0.0, 0.0, 0.0) : rol_c[v_rol];
	float escala_r = pa.x;
	// la pintura de los coches lleva barniz: casi lisa (el reflejo es lo que le da vida)
	float amplitud_r = (movil && v_tipo_v > 0.5 && v_tipo_v < 2.5) ? pa.y * 0.25 : pa.y;
	int tipo_r = int(pa.z + 0.5);
	vec3 q = (movil ? v_patron : v_pos) * escala_r;
	float v = 0.0;
#ifdef HOJAS
	tipo_r = -1;                 // racimos: el detalle lo da la textura de hojas (se ahorra el ruido: se superponen)
#endif
	if (tipo_r == 0) {
		v = fbm(q) - 0.5;
	} else if (tipo_r == 5) {
		// manchas grandes de cal (tono) + pinceladas alargadas en horizontal
		float manchas = fbm(q * 0.35) - 0.5;
		float brocha = ruido(vec3(q.x * 1.2, q.y * 9.0, q.z * 1.2)) - 0.5;
		v = manchas * 1.1 + brocha * 0.45;
	} else if (tipo_r == 8) {
		// asfalto viejo: grano fino + parches de reparación + franjas de desgaste
		vec2 pp = v_pos.xz / 3.5;
		float parche = step(0.80, hash3(vec3(floor(pp), 1.0)));
		float tono = hash3(vec3(floor(pp), 7.0)) - 0.5;
		float desgaste = smoothstep(0.55, 0.9, fbm(vec3(v_pos.x * 0.05, 0.0, v_pos.z * 0.05)));
		v = (fbm(q) - 0.5) * 0.5 + parche * tono * 1.4 + desgaste * 0.18;
	} else if (tipo_r == 1) {
		v = (hash3(floor(q * vec3(1.0, 2.2, 1.0))) - 0.5) + 0.4 * (ruido(q * 3.0) - 0.5);
	} else if (tipo_r == 2) {
		v = (ruido(vec3(q.x * 3.0, q.y * 0.4, q.z * 3.0)) - 0.5) + 0.3 * (hash3(floor(q * 2.0)) - 0.5);
	} else if (tipo_r == 3) {
		v = smoothstep(0.38, 0.62, fbm(q * 1.3)) - 0.5;
	} else if (tipo_r == 7) {
		// baldosas de 40 cm con junta oscura
		vec2 t = v_pos.xz / 0.4;
		vec2 f = fract(t);
		float borde = min(min(f.x, 1.0 - f.x), min(f.y, 1.0 - f.y));
		float junta = 1.0 - smoothstep(0.015, 0.045, borde);
		v = (hash3(vec3(floor(t), 0.0)) - 0.5) * 0.7 + 0.25 * (ruido(v_pos * 3.0) - 0.5) - junta * 0.9;
	}
	base *= 1.0 + v * amplitud_r * 2.0;
	if (tipo_r == 5) {
		// desconchados: la cal se cae en parches y deja ver la capa de abajo, más cálida y oscura
		float d = ruido(v_pos * 2.3) * 0.6 + ruido(v_pos * 7.0) * 0.4;
		float hueco = smoothstep(0.69, 0.74, d) * (0.4 + 0.6 * ruido(v_pos * 0.7));
		base = mix(base, base * vec3(0.90, 0.78, 0.64), hueco * 0.8);
	}
	float altura = 0.0;           // relieve de la superficie (texturas en grises), para la normal
	if (pa.w >= 0.0) {
		vec3 wn = pow(abs(normalize(v_nor)), vec3(4.0));
		wn /= (wn.x + wn.y + wn.z + 1e-5);
		vec3 pr = v_pos / pb.x;
		float r = texture(capas_relieve, vec3(pr.zy, pa.w)).r * wn.x + texture(capas_relieve, vec3(pr.xz, pa.w)).r * wn.y
			+ texture(capas_relieve, vec3(pr.xy, pa.w)).r * wn.z;
		base *= 1.0 + (r - 0.5) * 2.0 * pb.y;
		altura += (r - 0.5) * 0.5;
	}
	if (pb.z >= 0.0) {
		vec3 wd = pow(abs(normalize(v_nor)), vec3(4.0));
		wd /= (wd.x + wd.y + wd.z + 1e-5);
		// variante por zona: ruido lento (parches de ~30 m, de borde orgánico, como revoques de distinta época)
		float zona = clamp((fbm(v_pos * 0.03 + 11.0) - 0.3) * 2.5, 0.0, 0.999);
		float capa = pb.z + min(floor(zona * pb.w), pb.w - 1.0);
		vec3 pd = v_pos / pc.x;
		// (u, −v): la celda del atlas se leía con la v invertida
		float dd = texture(capas_detalle, vec3(pd.z, -pd.y, capa)).r * wd.x + texture(capas_detalle, vec3(pd.x, -pd.z, capa)).r * wd.y
			+ texture(capas_detalle, vec3(pd.x, -pd.y, capa)).r * wd.z;
		base *= 1.0 + (dd - 0.5) * 2.0 * pc.y;
		altura += dd - 0.5;
	}
	vec3 nw = normalize(v_nor);
	// relieve real (pedido del usuario, 2026-11-26: "aprovechar las texturas"): la textura en grises se usa como altura y
	// la normal se inclina según su pendiente en pantalla (bump por derivadas, sin tangentes ni UV); se apaga lejos, donde
	// las derivadas solo darían ruido
	float rugo = movil ? 0.0 : pc.z * (1.0 - smoothstep(25.0, 70.0, v_prof));
	if (rugo > 0.0) {
		float h = altura * rugo;
		vec3 dpx = dFdx(v_pos);
		vec3 dpy = dFdy(v_pos);
		vec3 r1 = cross(dpy, nw);
		vec3 r2 = cross(nw, dpx);
		float det = dot(dpx, r1);
		vec3 grad = sign(det) * (dFdx(h) * r1 + dFdy(h) * r2);
		vec3 nb = normalize(abs(det) * nw - grad);
		nw = dot(nb, nw) > 0.2 ? nb : nw;
	}
	if (!movil && abs(rol_a[v_rol].z - 3.0) < 0.5) {
		// follaje: hojas en racimos (ruido fino) sobre manchas grandes de luz y sombra, con el tono de cada árbol
		float tono = hash3(floor(v_pos * 0.25) + 0.37) - 0.5;
#ifndef HOJAS
		float racimo = ruido(v_pos * 5.5) * 0.6 + ruido(v_pos * 13.0) * 0.4;
		base *= 0.86 + racimo * 0.32;
#endif
		base *= vec3(1.0 + tono * 0.35, 1.0 + tono * 0.12, 1.0 - tono * 0.2);
		// por dentro y por debajo la copa es más oscura (las hojas de afuera tapan la luz)
		base *= mix(0.55, 1.0, smoothstep(-0.6, 0.5, nw.y));
	}
	NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
	ALBEDO = base;
	if (noche > 0.001 && tipo_r == 4 && movil) {
		// vehículos: interior iluminado detrás de los cristales; faros y pilotos encendidos
		EMISSION = vec3(0.95, 0.86, 0.68) * 0.6 * noche;
	} else if (noche > 0.001 && tipo_r == 4) {
		// ventanas encendidas al azar y globos de farol (vidrio cálido y claro)
		vec3 cel = floor(vec3(v_pos.x / 1.4, v_pos.y / 3.4, v_pos.z / 1.4));
		float enc = step(0.72, hash3(cel));
		vec3 em = color_ventana * (0.75 + 0.5 * hash3(cel + 3.7)) * enc * 0.92;
		float lum_b = dot(base, vec3(0.299, 0.587, 0.114));
		float es_globo = step(0.35, lum_b) * step(base.b * 1.25, base.r);
		em = mix(em, color_farol * 2.4, es_globo);
		EMISSION = em * noche;
	}
	if (movil && noche > 0.001) {
		float tv = floor(v_tipo_v + 0.5);
		if (tv == 3.0) EMISSION = vec3(1.0, 0.94, 0.8) * 2.2 * noche;
		if (tv == 4.0) EMISSION = vec3(1.0, 0.14, 0.08) * 1.5 * noche;
		if (tv == 5.0) EMISSION = vec3(0.95, 0.86, 0.68) * 0.6 * noche;
	}
	if (!sin_niebla) {
		EMISSION *= 1.0 - smoothstep(atm_niebla_d.x, atm_niebla_d.y, v_prof);
	}
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}

void light() {
	vec3 base = ALBEDO;
	int tipo_r = movil ? tipo : int(rol_a[v_rol].z + 0.5);
	vec3 nw = normalize(mat3(INV_VIEW_MATRIX) * NORMAL);
	float ndl = dot(NORMAL, LIGHT);
	float nl = max(ndl, 0.0);
	// irradiancia relativa de antes (relleno hemisférico + sol: sombra ≈ 0,5–1, pleno sol ≈ 3): la usan el bronce y la noche
	float amb = mix(atm_luz.y, atm_luz.x, 0.5 + 0.5 * v_nor.y);
	float luz = amb + atm_luz.z * nl * ATTENUATION;
	// luz de día (luz.gdshaderinc)
	vec3 rec = luz_recibida(nw, ndl, ATTENUATION);
	if (tipo_r == 3) {
		// follaje: la luz del sol atraviesa las hojas a contraluz
		float contra = pow(clamp(dot(VIEW, -LIGHT), 0.0, 1.0), 3.0);
		rec += atm_sol_col * vec3(0.55, 0.75, 0.25) * contra * (1.0 - nl) * ATTENUATION * 0.8;
	}
	vec3 col = base * rec;
	// brillo: un reflejo del sol en tejas esmaltadas, piedra pulida por el paso, hierro y pintura de los coches
	float brillo = movil ? ((v_tipo_v > 0.5 && v_tipo_v < 2.5) ? 0.55 : (tipo == 9 ? 0.6 : 0.0)) : rol_c[v_rol].w;
	if (brillo > 0.0) {
		vec3 hv = normalize(LIGHT + VIEW);
		float dur = movil ? 90.0 : 28.0;
		float esp = pow(max(dot(NORMAL, hv), 0.0), dur) * (dur + 8.0) / 25.0;
		col += atm_sol_col * esp * brillo * ATTENUATION * nl * 0.35;
	}
	if (movil && v_tipo_v > 0.5 && v_tipo_v < 2.5) {
		// pintura de coche con barniz: refleja la calle y el cielo, más al mirar de costado
		vec3 vd = normalize(v_pos - v_cam);
		vec3 rr = reflect(vd, nw);
		vec2 uvr = vec2(atan(rr.z, rr.x) / 6.2831853 + 0.5, asin(clamp(rr.y, -1.0, 1.0)) / 3.1415927 + 0.5);
		vec3 refl = texture(reflejo, vec2(uvr.x, 1.0 - uvr.y)).rgb;
		float fres = 0.05 + 0.95 * pow(1.0 - abs(dot(vd, nw)), 5.0);
		col = mix(col, refl * (0.45 + 0.55 * ATTENUATION), clamp(fres * 0.85 + 0.06, 0.0, 0.7));
	}
	col = tonos(col);
	if (tipo_r == 4) {
		// vidrio: el reflejo real de una calle soleada (más fuerte al mirar de costado); 8 tipos, uno por edificio
		vec3 nm = normalize(v_nor);
		vec3 vd = normalize(v_pos - v_cam);
		float fres = pow(1.0 - abs(dot(vd, nm)), 2.5);
		vec3 col0 = base * 0.75;
		vec3 rr = reflect(vd, nm);
		vec2 uvr = vec2(atan(rr.z, rr.x) / 6.2831853 + 0.5, asin(clamp(rr.y, -1.0, 1.0)) / 3.1415927 + 0.5);
		vec3 tg = normalize(cross(vec3(0.0, 1.0, 0.0), nm) + vec3(1e-4, 0.0, 0.0));
		float sx = dot(v_pos, tg);
		float edif = v_edif;
		float hv = movil ? 0.2 : (edif > 0.0 ? hash3(vec3(edif * 255.0, 3.7, 1.3)) : hash3(vec3(floor(dot(v_pos, nm) * 2.0), 5.1, 2.2)));
		float u = fract(sx / 1.3);
		float pliegue = 0.85 + 0.15 * sin(sx * 38.0);
		if (hv > 0.85) uvr.y += 0.008 * sin(v_pos.y * 45.0 + sx * 20.0);
		vec3 refl = texture(reflejo, vec2(uvr.x, 1.0 - uvr.y)).rgb;
		if (hv < 0.12) {                       // actual: azul-gris con reflejo
			col = mix(col0, refl * 0.9, 0.22 + 0.5 * fres);
		} else if (hv < 0.32) {                // oscuro con reflejo marcado
			col = mix(vec3(0.03, 0.035, 0.045), refl * 0.95, 0.3 + 0.55 * fres);
		} else if (hv < 0.52) {                // visillo blanco detrás
			col = mix(vec3(0.9, 0.88, 0.83) * pliegue * 0.82, refl, 0.15 + 0.45 * fres);
		} else if (hv < 0.62) {                // cortina roja recogida a los lados
			vec3 fondo = abs(u - 0.5) < 0.27 ? vec3(0.05, 0.045, 0.045) : vec3(0.52, 0.11, 0.08) * pliegue;
			col = mix(fondo, refl * 0.9, 0.15 + 0.5 * fres);
		} else if (hv < 0.70) {                // postigos de madera por dentro (una hoja cerrada)
			vec3 fondo = u < 0.5 ? vec3(0.4, 0.24, 0.13) * (0.85 + 0.15 * step(0.5, fract(v_pos.y * 7.0))) : vec3(0.05);
			col = mix(fondo, refl * 0.9, 0.15 + 0.45 * fres);
		} else if (hv < 0.76) {                // esmerilado
			col = mix(vec3(0.8, 0.82, 0.81), refl, 0.08 + 0.2 * fres);
		} else if (hv < 0.85) {                // interior con luz cálida
			float y = fract(v_pos.y / 3.6);
			col = mix(mix(vec3(0.5, 0.31, 0.15), vec3(0.08, 0.06, 0.05), y), refl * 0.9, 0.15 + 0.45 * fres);
		} else {                               // verde antiguo
			col = mix(vec3(0.15, 0.23, 0.19), refl * 0.9, 0.25 + 0.5 * fres);
		}
	} else if (tipo_r == 6) {
		vec3 nm = normalize(v_nor);
		vec3 vd = normalize(v_pos - v_cam);
		float fres_a = pow(1.0 - abs(dot(vd, nm)), 2.0);
		col = mix(base * 0.9, cielo_bajo * 0.8, 0.3 + 0.45 * fres_a);
	}
	if (tipo_r == 9) {
		// bronce pulido: cielo reflejado arriba y banda dorada donde la luz rebota hacia la cámara
		vec3 nm = normalize(v_nor);
		vec3 vd = normalize(v_pos - v_cam);
		vec3 sol = normalize(vec3(0.45, 0.8, 0.35));
		float espec = pow(max(dot(nm, normalize(sol - vd)), 0.0), 9.0);
		float fres_m = pow(1.0 - abs(dot(vd, nm)), 3.0);
		float cie = nm.y * 0.5 + 0.5;
		float lum_m = clamp(luz / 3.6, 0.3, 1.0);
		vec3 metal = base * (0.5 + 0.55 * cie) * lum_m;
		metal += vec3(1.0, 0.72, 0.38) * espec * 1.1 * lum_m + cielo_bajo * fres_m * 0.3 * lum_m;
		col = mix(col, metal, 0.92);
	}
	if (noche > 0.001) {
		// luna en dos franjas azuladas + luz cálida de los faroles cercanos
		float lit = smoothstep(0.16, 0.32, luz);
		vec3 nocturno = base * (amb_noche + luna_noche * lit);
		vec3 nrm = normalize(v_nor);
		float lf = luz_farol(farol_0, v_pos, nrm) + luz_farol(farol_1, v_pos, nrm) + luz_farol(farol_2, v_pos, nrm)
			+ luz_farol(farol_3, v_pos, nrm) + luz_farol(farol_4, v_pos, nrm) + luz_farol(farol_5, v_pos, nrm)
			+ luz_farol(farol_6, v_pos, nrm) + luz_farol(farol_7, v_pos, nrm) + luz_farol(farol_8, v_pos, nrm)
			+ luz_farol(farol_9, v_pos, nrm) + luz_farol(farol_10, v_pos, nrm) + luz_farol(farol_11, v_pos, nrm)
			+ luz_farol(farol_12, v_pos, nrm) + luz_farol(farol_13, v_pos, nrm) + luz_farol(farol_14, v_pos, nrm)
			+ luz_farol(farol_15, v_pos, nrm);
		lf = smoothstep(0.0, 0.95, lf);
		nocturno += base * color_farol * lf * 0.8;
		col = mix(col, nocturno, noche);
	}
	if (!sin_niebla) {
		// niebla como la de three (lineal con smoothstep), aquí para que sea igual en todos los renderizadores
		col = con_niebla(col, v_prof);
	}
	DIFFUSE_LIGHT = col / max(base, vec3(0.002));
}
