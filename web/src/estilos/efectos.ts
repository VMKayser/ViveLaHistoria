import { Effect, EffectAttribute } from "postprocessing";
import { Color, Uniform } from "three";

/** Contorno de tinta a partir de la profundidad y del color. */
const tintaFrag = /* glsl */ `
uniform vec3 uColor;
uniform float uGrosor;
uniform float uUmbral;

float invZ(vec2 p) { return 1.0 / max(-getViewZ(readDepth(p)), 0.001); }

void mainImage(const in vec4 inputColor, const in vec2 uv, const in float depth, out vec4 outputColor) {
  vec2 t = texelSize * uGrosor;
  float w = invZ(uv);
  float lap = abs(invZ(uv - vec2(t.x, 0.0)) + invZ(uv + vec2(t.x, 0.0)) - 2.0 * w)
            + abs(invZ(uv - vec2(0.0, t.y)) + invZ(uv + vec2(0.0, t.y)) - 2.0 * w);
  float e = smoothstep(uUmbral, uUmbral * 2.5, lap / w);
  vec3 cl = texture2D(inputBuffer, uv - vec2(t.x, 0.0)).rgb;
  vec3 cr = texture2D(inputBuffer, uv + vec2(t.x, 0.0)).rgb;
  vec3 cu = texture2D(inputBuffer, uv + vec2(0.0, t.y)).rgb;
  vec3 cd = texture2D(inputBuffer, uv - vec2(0.0, t.y)).rgb;
  float ce = length(cr - cl) + length(cu - cd);
  e = max(e, smoothstep(0.45, 0.8, ce) * 0.7);
  outputColor = vec4(mix(inputColor.rgb, uColor, e), inputColor.a);
}
`;

export class TintaEffect extends Effect {
  constructor({ color = "#2a1f1a", grosor = 1.2, umbral = 0.04 } = {}) {
    super("TintaEffect", tintaFrag, {
      attributes: EffectAttribute.DEPTH,
      uniforms: new Map<string, Uniform>([
        ["uColor", new Uniform(new Color(color))],
        ["uGrosor", new Uniform(grosor)],
        ["uUmbral", new Uniform(umbral)],
      ]),
    });
  }
}

/** Acuarela: papel, granulado de pigmento, lavado de color y borde de tinta tembloroso. */
const acuarelaFrag = /* glsl */ `
uniform vec3 uPapel;
uniform vec3 uTinta;

float h(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) {
  float s = 0.0, a = 0.5;
  for (int i = 0; i < 4; i++) { s += a * vn(p); p *= 2.03; a *= 0.5; }
  return s;
}
float invZ(vec2 p) { return 1.0 / max(-getViewZ(readDepth(p)), 0.001); }

void mainImage(const in vec4 inputColor, const in vec2 uv, const in float depth, out vec4 outputColor) {
  vec2 px = uv / texelSize;
  vec2 wob = (vec2(fbm(uv * 9.0), fbm(uv * 9.0 + 7.3)) - 0.5) * 0.007;
  vec2 q = uv + wob;
  vec3 c = texture2D(inputBuffer, q).rgb;

  // borde tembloroso (profundidad + color)
  vec2 t = texelSize * 1.6;
  float w = invZ(q);
  float lap = abs(invZ(q - vec2(t.x, 0.0)) + invZ(q + vec2(t.x, 0.0)) - 2.0 * w)
            + abs(invZ(q - vec2(0.0, t.y)) + invZ(q + vec2(0.0, t.y)) - 2.0 * w);
  float e = smoothstep(0.03, 0.12, lap / w);
  vec3 a = texture2D(inputBuffer, q - vec2(t.x, 0.0)).rgb, b = texture2D(inputBuffer, q + vec2(t.x, 0.0)).rgb;
  vec3 u = texture2D(inputBuffer, q + vec2(0.0, t.y)).rgb, d = texture2D(inputBuffer, q - vec2(0.0, t.y)).rgb;
  e = max(e, smoothstep(0.25, 0.7, length(b - a) + length(u - d)));
  e *= 0.55 + 0.45 * fbm(px / 18.0);

  // lavado hacia el papel y granulado del pigmento
  float lav = 0.08 + 0.2 * fbm(uv * 3.5 + 2.0);
  c = mix(c, uPapel, lav);
  c = floor(c * 7.0 + 0.5) / 7.0 * 0.35 + c * 0.65;
  c *= 0.9 + 0.18 * fbm(px / 5.0);
  // acumulación de pigmento en los bordes
  c = mix(c, c * 0.6 + uTinta * 0.25, e * 0.75);

  // textura del papel
  c *= 0.94 + 0.08 * fbm(px / 2.2);
  // bordes de la hoja sin pintar
  float m = min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y));
  float v = smoothstep(0.0, 0.09, m + (fbm(uv * 7.0) - 0.5) * 0.07);
  c = mix(uPapel, c, v);
  outputColor = vec4(c, inputColor.a);
}
`;

export class AcuarelaEffect extends Effect {
  constructor({ papel = "#f3ecdc", tinta = "#4a3426" } = {}) {
    super("AcuarelaEffect", acuarelaFrag, {
      attributes: EffectAttribute.DEPTH,
      uniforms: new Map<string, Uniform>([
        ["uPapel", new Uniform(new Color(papel))],
        ["uTinta", new Uniform(new Color(tinta))],
      ]),
    });
  }
}
