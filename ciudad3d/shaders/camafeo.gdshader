shader_type canvas_item;
// Camafeo ovalado de la carta: marco de oro, fondo de pizarra y el retrato recortado en óvalo
// (como [data-estilo="carta"] .retrato-a de ui_ideas/encuentros_claude/estilos.css).

uniform float aspecto = 0.78;        // ancho / alto del rectángulo
uniform bool cronista = false;       // el emblema del narrador se ve más chico y centrado
uniform float marco = 0.055;         // grosor del marco (fracción del radio)

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float aa = fwidth(r) * 1.5;
	float fuera = 1.0 - smoothstep(1.0 - aa, 1.0, r);
	float dentro = 1.0 - smoothstep(1.0 - marco - aa, 1.0 - marco, r);
	// oro: degradado diagonal con brillos (linear-gradient(140deg, #f7df9c, #a87b32 45%, #f3d58e 60%, #8a6125))
	float t = clamp(dot(UV, normalize(vec2(0.64, 0.77))), 0.0, 1.0);
	vec3 oro = mix(vec3(0.97, 0.87, 0.61), vec3(0.66, 0.48, 0.20), smoothstep(0.0, 0.45, t));
	oro = mix(oro, vec3(0.95, 0.84, 0.56), smoothstep(0.45, 0.6, t));
	oro = mix(oro, vec3(0.54, 0.38, 0.15), smoothstep(0.6, 1.0, t));
	// fondo: radial-gradient(circle at 40% 35%, #4c6670, #1f2c33 75%)
	vec3 fondo = mix(vec3(0.30, 0.40, 0.44), vec3(0.12, 0.17, 0.20), smoothstep(0.0, 0.75, distance(UV, vec2(0.4, 0.35))));
	// retrato cuadrado que cubre el óvalo (se recorta a los lados)
	vec2 uv = vec2(0.5 + (UV.x - 0.5) * aspecto, UV.y);
	if (cronista) {
		uv = (UV - 0.5) * vec2(aspecto, 1.0) * 1.35 + 0.5;
	}
	vec4 cara = texture(TEXTURE, uv);
	if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) cara.a = 0.0;
	vec3 interior = mix(fondo, cara.rgb, cara.a);
	// orla: sombra interior abajo (inset 0 -1.5cqh 2.5cqh #0005)
	interior *= 1.0 - 0.35 * smoothstep(0.55, 1.0, r) * smoothstep(-0.2, 1.0, p.y);
	vec3 c = mix(oro, interior, dentro);
	COLOR = vec4(c, fuera);
}
