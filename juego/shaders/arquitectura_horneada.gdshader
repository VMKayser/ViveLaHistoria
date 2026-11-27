shader_type spatial;
// Arquitectura con iluminación híbrida:
// - El sol es luz en tiempo real de Godot (sombras dinámicas, relieve y brillos).
// - La luz del cielo, sus rebotes y las velas vienen horneados desde Blender (Cycles)
//   en `luz_horneada`, sobre el UV de la malla. Por eso se apaga la luz ambiental de Godot,
//   que no sabe que el interior de la sala está techado.
// Texturas PBR con proyección triplanar en coordenadas de mundo (escala real en metros).
render_mode ambient_light_disabled;

uniform vec4 tinte : source_color = vec4(1.0);
uniform sampler2D albedo_tex : source_color, hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D arm_tex : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float escala = 0.5; // repeticiones de la textura por metro
uniform float fuerza_normal = 1.0;

uniform sampler2D luz_horneada : hint_default_white, filter_linear, repeat_disable;
uniform float rango = 4.0;      // el PNG guarda sqrt(luz / rango)
uniform float intensidad = 1.0; // ajuste artístico de la luz horneada
// Curva < 1 comprime el rango: realza interiores en sombra sin quemar el patio a pleno cielo
// (imita la adaptación del ojo, que el renderizador web no tiene).
uniform float curva : hint_range(0.3, 1.0) = 0.65;

varying vec3 v_posicion;
varying vec3 v_normal;

void vertex() {
	v_posicion = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

vec3 pesos_triplanares(vec3 n) {
	vec3 w = pow(abs(n), vec3(4.0));
	return w / (w.x + w.y + w.z);
}

vec3 normal_tangente(vec2 uv) {
	vec3 t = texture(normal_tex, uv).xyz * 2.0 - 1.0;
	t.xy *= fuerza_normal;
	return t;
}

void fragment() {
	vec3 n = normalize(v_normal);
	vec3 w = pesos_triplanares(n);
	vec3 p = v_posicion * escala;
	vec2 uv_x = p.zy;
	vec2 uv_y = p.xz;
	vec2 uv_z = p.xy;

	vec3 color = texture(albedo_tex, uv_x).rgb * w.x
		+ texture(albedo_tex, uv_y).rgb * w.y
		+ texture(albedo_tex, uv_z).rgb * w.z;
	vec3 arm = texture(arm_tex, uv_x).rgb * w.x
		+ texture(arm_tex, uv_y).rgb * w.y
		+ texture(arm_tex, uv_z).rgb * w.z;

	// Normales triplanares con mezcla "whiteout" (Ben Golus).
	vec3 tx = normal_tangente(uv_x);
	vec3 ty = normal_tangente(uv_y);
	vec3 tz = normal_tangente(uv_z);
	tx = vec3(tx.xy + n.zy, abs(tx.z) * n.x);
	ty = vec3(ty.xy + n.xz, abs(ty.z) * n.y);
	tz = vec3(tz.xy + n.xy, abs(tz.z) * n.z);
	vec3 normal_mundo = normalize(tx.zyx * w.x + ty.xzy * w.y + tz.xyz * w.z);
	NORMAL = normalize((VIEW_MATRIX * vec4(normal_mundo, 0.0)).xyz);

	ALBEDO = color * tinte.rgb;
	ROUGHNESS = arm.g;
	SPECULAR = 0.4;

	vec3 codificada = texture(luz_horneada, UV).rgb;
	vec3 luz = pow(codificada * codificada * rango, vec3(curva));
	EMISSION = ALBEDO * luz * mix(1.0, arm.r, 0.7) * intensidad;
}
