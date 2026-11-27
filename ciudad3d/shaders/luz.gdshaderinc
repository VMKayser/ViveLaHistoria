// Luz de la escena, común a la ciudad (estilo.gdshaderinc) y al pasto y las flores (pasto.gdshader): parámetros globales
// que cambia scripts/hora.gd para todos los materiales a la vez, la luz de día y la curva de tonos.
global uniform float noche;
global uniform vec4 atm_luz;        // x: relleno cielo, y: relleno suelo (luminancias × intensidad), z: sol (luminancia × intensidad)
global uniform vec3 atm_niebla;     // color de la niebla (lineal)
global uniform vec2 atm_niebla_d;   // comienzo y fin de la niebla (m)
global uniform vec3 atm_sol_dir;    // dirección hacia el sol (para el bronce)
global uniform vec3 atm_sol_col;    // luz del sol o la luna (lineal × intensidad)
global uniform vec3 atm_cielo_col;  // luz de relleno que baja del cielo (lineal)
global uniform vec3 atm_suelo_col;  // luz que rebota del suelo (lineal)
global uniform float atm_hombro;    // desde qué valor la curva de tonos empieza a comprimir las luces altas

// Luz que recibe una superficie (2026-11-26, salto de calidad): sol cálido con un terminador algo pintado (ni duro ni
// plástico) y la sombra iluminada por el cielo azul arriba y el rebote cálido del suelo abajo: sombras frescas y luces
// cálidas, con el contraste de la referencia (≈3:1 entre sol y sombra; las tres franjas de antes daban 1,8:1 y todo se
// veía lavado). nw: normal en el mundo; ndl: normal·luz (en vista); sombra: ATTENUATION.
vec3 luz_recibida(vec3 nw, float ndl, float sombra) {
	float dif = smoothstep(-0.08, 0.5, ndl) * 0.45 + max(ndl, 0.0) * 0.55;
	vec3 cielo = mix(atm_suelo_col, atm_cielo_col, smoothstep(-0.7, 0.9, nw.y));
	return cielo + atm_sol_col * dif * sombra;
}

// Curva de tonos: deja igual los medios tonos y comprime solo las luces altas (el muro blanco al sol no se quema)
vec3 tonos(vec3 c) {
	vec3 k = vec3(atm_hombro);
	vec3 sobre = max(c - k, vec3(0.0));
	return min(c, k) + (1.0 - k) * (1.0 - exp(-sobre / (1.0 - k)));
}

// Niebla lineal con smoothstep (como la de three), igual en todos los renderizadores
vec3 con_niebla(vec3 col, float prof) {
	return mix(col, atm_niebla, smoothstep(atm_niebla_d.x, atm_niebla_d.y, prof));
}
