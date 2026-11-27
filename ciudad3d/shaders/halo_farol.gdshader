// Halo aditivo de un farol (como web/src/ciudad/escena/Faroles.tsx): un cuadrado que mira siempre a la cámara, con brillo
// suave y núcleo; crece con la distancia para que los faroles lejanos se vean como puntos de luz.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, fog_disabled;
uniform vec3 color = vec3(1.0, 0.66, 0.3);
varying float v_dist;
varying vec2 v_uv;

void vertex() {
	vec3 c = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	v_dist = distance(CAMERA_POSITION_WORLD, c);
	float tam = clamp(1.1 + v_dist * 0.014, 1.1, 6.0);
	vec3 p = c + (INV_VIEW_MATRIX[0].xyz * VERTEX.x + INV_VIEW_MATRIX[1].xyz * VERTEX.y) * tam;
	v_uv = UV;
	POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(p, 1.0);
}

void fragment() {
	float d = length(v_uv - 0.5) * 2.0;
	float halo = pow(max(1.0 - d, 0.0), 2.4);
	float nucleo = smoothstep(0.22, 0.0, d);
	float lejos = 1.0 - smoothstep(500.0, 1400.0, v_dist);
	float cerca = smoothstep(1.0, 6.0, v_dist);
	float a = (halo * 0.75 + nucleo) * lejos * cerca;
	// three: AdditiveBlending (src·alfa + dst) sobre un búfer lineal = color·a². Aquí el mismo aporte con alfa 1: en el
	// renderizador de compatibilidad el búfer está en sRGB y multiplicar por alfa después de convertir lo dejaba tenue.
	ALBEDO = color * a * a;
	ALPHA = 1.0;
}
