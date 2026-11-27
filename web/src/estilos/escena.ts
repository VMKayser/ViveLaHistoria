/**
 * Escena compartida por los cinco estilos: fachada lateral de la Catedral de Sucre,
 * su atrio y la franja de la Plaza 25 de Mayo que queda enfrente.
 *
 * Unidades en metros. Ejes: x a lo largo de la calle (torre a la izquierda),
 * y hacia arriba, z hacia la plaza. La fachada de la catedral está en z = 0.
 *
 * Medidas: largos y distancias desde OSM (Sucre.osm.gz); alturas estimadas
 * a partir de las fotos de guia_plaza/ (persona = 1,65 m). Son aproximadas
 * hasta tener planos.
 */

export type Mat =
  | "suelo" | "cal" | "piedra" | "piedraAtrio" | "pisoAtrio" | "teja" | "balaustre"
  | "hierro" | "vano" | "madera" | "asfalto" | "linea" | "acera" | "baldosa" | "baldosa2"
  | "cesped" | "copa" | "copa2" | "copaRedonda" | "tronco" | "troncoBlanco" | "palmera"
  | "flor1" | "flor2" | "flor3" | "bronce" | "monumento" | "estatua" | "reloj"
  | "gob" | "pizarra" | "cupula";

export type Tipo = "caja" | "cil" | "cono" | "esfera";

export interface Prim {
  t: Tipo;
  /** centro */
  p: [number, number, number];
  /** tamaño total: caja [ancho, alto, fondo]; cil/cono/esfera [diámetro x, alto, diámetro z] */
  s: [number, number, number];
  /** rotación euler (radianes) */
  r?: [number, number, number];
  m: Mat;
  /** segmentos radiales (4 = base cuadrada) */
  seg?: number;
}

const P: Prim[] = [];
const R = (n: number) => Math.round(n * 1000) / 1000;

/** caja por extremos */
function bloque(x0: number, x1: number, y0: number, y1: number, z0: number, z1: number, m: Mat, r?: Prim["r"]) {
  P.push({ t: "caja", p: [R((x0 + x1) / 2), R((y0 + y1) / 2), R((z0 + z1) / 2)], s: [R(x1 - x0), R(y1 - y0), R(z1 - z0)], m, r });
}
function cil(x: number, y0: number, y1: number, z: number, d: number, m: Mat, seg?: number, dz = d) {
  P.push({ t: "cil", p: [x, R((y0 + y1) / 2), z], s: [d, R(y1 - y0), dz], m, seg });
}
function cono(x: number, y0: number, y1: number, z: number, d: number, m: Mat, seg?: number, r?: Prim["r"]) {
  P.push({ t: "cono", p: [x, R((y0 + y1) / 2), z], s: [d, R(y1 - y0), d], m, seg, r });
}
function esfera(x: number, y: number, z: number, d: number, m: Mat, dy = d, dz = d) {
  P.push({ t: "esfera", p: [x, y, z], s: [d, dy, dz], m });
}
/** vano con arco de medio punto en un muro paralelo a x (cara en zCara, mirando a +z) */
function vanoArco(x: number, y0: number, alto: number, ancho: number, zCara: number, m: Mat = "vano", marco?: Mat) {
  if (marco) {
    bloque(x - ancho / 2 - 0.35, x + ancho / 2 + 0.35, y0 - 0.35, y0 + alto, zCara, zCara + 0.12, marco);
    P.push({ t: "cil", p: [x, y0 + alto, zCara + 0.06], s: [ancho + 0.7, 0.12, ancho + 0.7], r: [Math.PI / 2, 0, 0], m: marco, seg: 24 });
  }
  const z = zCara + (marco ? 0.13 : 0.02);
  bloque(x - ancho / 2, x + ancho / 2, y0, y0 + alto, z, z + 0.06, m);
  P.push({ t: "cil", p: [x, y0 + alto, z + 0.03], s: [ancho, 0.06, ancho], r: [Math.PI / 2, 0, 0], m, seg: 24 });
}
/** balaustrada a lo largo de x */
function balaustrada(x0: number, x1: number, y: number, z: number, alto: number, m: Mat, base: Mat, paso = 0.45, pilares: number[] = []) {
  bloque(x0, x1, y, y + 0.18, z - 0.3, z + 0.3, base);
  for (let x = x0 + paso / 2; x < x1; x += paso) {
    if (pilares.some((px) => Math.abs(px - x) < 0.5)) continue;
    cil(R(x), y + 0.18, y + alto - 0.14, z, 0.2, m, 8);
  }
  bloque(x0, x1, y + alto - 0.14, y + alto, z - 0.28, z + 0.28, base);
  for (const px of pilares) {
    bloque(px - 0.32, px + 0.32, y, y + alto + 0.25, z - 0.32, z + 0.32, base);
    cono(px, y + alto + 0.25, y + alto + 1.15, z, 0.45, base, 12);
    esfera(px, y + alto + 1.2, z, 0.26, base);
  }
}
function figura(x: number, y: number, z: number, h: number, m: Mat) {
  cil(x, y, y + h * 0.78, z, h * 0.26, m, 10);
  esfera(x, y + h * 0.86, z, h * 0.2, m);
}
function arbolGrande(x: number, z: number, h: number, var_: number) {
  cil(x, 0, 1.3, z, 0.7, "troncoBlanco", 10);
  cil(x, 1.3, h * 0.62, z, 0.55, "tronco", 10);
  const d = h * 0.62;
  esfera(x, h * 0.72, z, d, var_ % 2 ? "copa" : "copa2", d * 0.62);
  esfera(x + d * 0.32, h * 0.66, z - d * 0.2, d * 0.7, "copa", d * 0.48);
  esfera(x - d * 0.3, h * 0.64, z + d * 0.18, d * 0.66, "copa2", d * 0.46);
}
function arbolRedondo(x: number, z: number) {
  cil(x, 0.15, 1.0, z, 0.32, "troncoBlanco", 8);
  cil(x, 1.0, 3.0, z, 0.26, "tronco", 8);
  esfera(x, 3.9, z, 3.3, "copaRedonda", 2.4);
}
function palmera(x: number, z: number, h: number) {
  cil(x, 0, 1.4, z, 0.95, "troncoBlanco", 12);
  cil(x, 1.4, h, z, 0.85, "palmera", 12);
  for (let i = 0; i < 7; i++) {
    const a = (i / 7) * Math.PI * 2;
    P.push({ t: "caja", p: [R(x + Math.cos(a) * 1.7), R(h + 0.2), R(z + Math.sin(a) * 1.7)], s: [3.6, 0.15, 0.9], r: [0, R(-a), -0.35], m: "copa" });
  }
  esfera(x, h + 0.4, z, 1.2, "copa2");
}
function farol(x: number, z: number, h = 5.5) {
  cil(x, 0.15, 0.7, z, 0.45, "hierro", 10);
  cil(x, 0.7, h, z, 0.18, "hierro", 8);
  bloque(x - 0.3, x + 0.3, h, h + 0.7, z - 0.3, z + 0.3, "reloj");
  cono(x, h + 0.7, h + 1.1, z, 0.75, "hierro", 4, [0, Math.PI / 4, 0]);
}
function banco(x: number, z: number, mirando: 1 | -1) {
  bloque(x - 0.9, x + 0.9, 0.45, 0.53, z - 0.25, z + 0.25, "madera");
  const zr = z - mirando * 0.28;
  bloque(x - 0.9, x + 0.9, 0.6, 1.0, zr - 0.04, zr + 0.04, "madera");
  for (const dx of [-0.75, 0.75]) bloque(x + dx - 0.04, x + dx + 0.04, 0.15, 1.0, z - 0.3, z + 0.3, "hierro");
}
function cercaJardin(x: number, z: number, lado: number) {
  bloque(x - lado / 2, x + lado / 2, 0.15, 0.3, z - lado / 2, z + lado / 2, "acera");
  for (const [a, b, c, d] of [
    [-1, 1, -1, -1], [-1, 1, 1, 1], [-1, -1, -1, 1], [1, 1, -1, 1],
  ]) bloque(x + (a * lado) / 2 - 0.03, x + (b * lado) / 2 + 0.03, 0.3, 0.75, z + (c * lado) / 2 - 0.03, z + (d * lado) / 2 + 0.03, "hierro");
}

// ---------------------------------------------------------------- terreno
bloque(-82, 55, -0.6, 0, -26, 74, "suelo");
bloque(-82, 55, 0, 0.02, 9.5, 20, "asfalto");
for (let x = -80; x < 54; x += 6) {
  bloque(x, x + 3, 0.02, 0.04, 13.0, 13.15, "linea");
  bloque(x, x + 3, 0.02, 0.04, 16.4, 16.55, "linea");
}
bloque(-82, 55, 0, 0.16, 6.4, 9.5, "acera"); // acera de la catedral

// ---------------------------------------------------------------- atrio
bloque(-42, 19.5, 0, 0.9, -1, 5.6, "pisoAtrio");
const pilaresAtrio = [-39, -33, -27, -21, -15, -9, -3, 3, 15, 19];
bloque(-42.4, 7.3, 0, 2.1, 5.6, 6.4, "piedraAtrio");
bloque(11.7, 19.9, 0, 2.1, 5.6, 6.4, "piedraAtrio");
balaustrada(-42.4, 7.3, 2.1, 6.0, 0.95, "cal", "piedraAtrio", 0.42, pilaresAtrio.filter((x) => x < 7));
balaustrada(11.7, 19.9, 2.1, 6.0, 0.95, "cal", "piedraAtrio", 0.42, pilaresAtrio.filter((x) => x > 11));
// portón de hierro frente al portal
for (const x of [7.0, 12.0]) {
  bloque(x - 0.45, x + 0.45, 0, 4.4, 5.5, 6.5, "piedraAtrio");
  cono(x, 4.4, 5.4, 6.0, 0.6, "piedraAtrio", 12);
}
for (let x = 7.6; x < 11.5; x += 0.22) bloque(R(x), R(x + 0.05), 0.2, 3.3, 5.97, 6.03, "hierro");
bloque(7.45, 11.55, 3.3, 3.42, 5.95, 6.05, "hierro");
bloque(7.45, 11.55, 1.6, 1.7, 5.95, 6.05, "hierro");

// ---------------------------------------------------------------- torre
// cuerpo 1
bloque(-42, -32, 0, 17, -10, 0.6, "cal");
for (const x of [-41.4, -32.6]) bloque(x - 0.6, x + 0.6, 0, 17, 0.6, 0.9, "piedra");
bloque(-42, -32, 0, 1.2, 0.6, 0.85, "piedra");
bloque(-42.4, -31.6, 17, 17.8, -10.4, 1.1, "piedra");
balaustrada(-42.2, -31.8, 17.8, 0.8, 0.9, "balaustre", "cal", 0.4, [-41.8, -37, -32.2]);
// cuerpo 2: campanario
bloque(-41, -33, 17.8, 25.5, -9, -0.2, "cal");
for (const x of [-40.5, -33.5]) bloque(x - 0.55, x + 0.55, 17.8, 25.5, -0.2, 0.1, "piedra");
for (const x of [-38.9, -35.1]) {
  vanoArco(x, 19.6, 3.0, 1.8, -0.2);
  P.push({ t: "cono", p: [x, 21.1, -0.05], s: [1.0, 1.1, 1.0], m: "bronce", seg: 14 });
}
bloque(-41.4, -32.6, 25.5, 26.2, -9.4, 0.4, "piedra");
balaustrada(-41.2, -32.8, 26.2, 0.1, 0.8, "balaustre", "cal", 0.4, [-40.8, -33.2]);
for (const x of [-40.8, -33.2]) figura(x, 27.0, 0.1, 1.6, "estatua");
for (const x of [-41.8, -32.2]) figura(x, 18.7, 0.8, 1.7, "estatua");
// cuerpo 3: reloj
bloque(-40, -34, 26.2, 31, -8, -1.2, "cal");
for (const x of [-39.6, -34.4]) bloque(x - 0.4, x + 0.4, 26.2, 31, -1.2, -0.95, "piedra");
P.push({ t: "cil", p: [-37, 28.7, -1.1], s: [2.4, 0.2, 2.4], r: [Math.PI / 2, 0, 0], m: "piedra", seg: 32 });
P.push({ t: "cil", p: [-37, 28.7, -0.98], s: [2.0, 0.08, 2.0], r: [Math.PI / 2, 0, 0], m: "reloj", seg: 32 });
bloque(-37.05, -36.95, 28.7, 29.5, -0.93, -0.9, "hierro");
bloque(-37, -36.4, 28.65, 28.75, -0.92, -0.89, "hierro");
bloque(-40.3, -33.7, 31, 31.6, -8.3, -0.9, "piedra");
// remate piramidal
P.push({ t: "cono", p: [-37, 33.8, -4.6], s: [8.6, 4.4, 8.6], r: [0, Math.PI / 4, 0], m: "teja", seg: 4 });
figura(-37, 36.0, -4.6, 1.5, "estatua");
for (const x of [-39.9, -34.1]) figura(x, 31.6, -1.2, 1.3, "estatua");

// ---------------------------------------------------------------- nave
bloque(-32, 6, 0, 15, -20, 0, "cal");
bloque(-32, 6, 0, 1.2, 0, 0.25, "piedra");
const pilastras = [-31.2, -22.4, -13.6, -4.8, 4.6];
for (const x of pilastras) bloque(x - 0.7, x + 0.7, 0, 15, 0, 0.35, "piedra");
bloque(-32.2, 6.2, 15, 15.6, -20.4, 0.6, "cal");
balaustrada(-32, 6, 15.6, 0.15, 1.1, "balaustre", "cal", 0.45, pilastras);
for (const x of [-26.8, -18, -9.2]) vanoArco(x, 7.4, 2.8, 1.9, 0, "vano", "cal");
for (const x of [-18]) vanoArco(x, 2.5, 1.6, 1.3, 0, "vano", "cal");
// cubierta de teja con cúpulas sobre las bóvedas (ver plano_plaza_catedral_vista_superior.png)
bloque(-31.8, 5.8, 15.6, 15.9, -19.6, -0.7, "teja");
for (const x of [-26.5, -17.5, -8.5, 0.5]) esfera(x, 15.9, -10, 6.2, "teja", 3.2);
for (const x of [-26.5, -17.5, -8.5, 0.5]) cil(x, 17.3, 18.1, -10, 1.1, "cal", 12);

// ---------------------------------------------------------------- portal barroco
bloque(6, 15, 0, 13, -0.5, 1.2, "piedra");
vanoArco(10.5, 0.9, 3.9, 3.0, 1.2, "madera");
for (const x of [7.3, 8.4, 12.6, 13.7]) {
  cil(x, 0.9, 6.8, 1.55, 0.6, "piedra", 14);
  cil(x, 7.6, 12.6, 1.5, 0.5, "piedra", 14);
}
bloque(6.2, 14.8, 6.8, 7.6, 0, 2.0, "piedra");
bloque(6.2, 14.8, 12.6, 13.4, 0, 1.9, "piedra");
vanoArco(10.5, 8.2, 2.2, 1.7, 1.2);
figura(10.5, 8.2, 1.55, 2.3, "estatua");
bloque(8.1, 12.9, 13.4, 18, -0.4, 1.2, "piedra");
for (const x of [8.5, 12.5]) cil(x, 13.4, 17.6, 1.4, 0.45, "piedra", 12);
vanoArco(10.5, 14.2, 1.9, 1.5, 1.2);
figura(10.5, 14.2, 1.55, 2.0, "estatua");
bloque(8.6, 12.4, 18, 18.6, -0.3, 1.5, "piedra");
cono(10.5, 18.6, 20.0, 0.7, 2.6, "piedra", 4, [0, Math.PI / 4, 0]);
bloque(10.38, 10.62, 20.0, 22.2, 0.58, 0.82, "piedra");
bloque(9.7, 11.3, 21.2, 21.45, 0.58, 0.82, "piedra");
for (const x of [6.6, 14.4]) {
  cono(x, 13.4, 15.6, 1.2, 0.7, "piedra", 10);
  esfera(x, 15.7, 1.2, 0.45, "piedra");
}
for (const x of [8.1, 12.9]) esfera(x, 13.9, 1.3, 1.0, "piedra", 1.0, 0.7);

// ---------------------------------------------------------------- volumen tras el portal y edificio adjunto
bloque(15, 20, 0, 18, -8, 0, "cal");
balaustrada(15, 20, 18, 0.0, 0.9, "balaustre", "cal", 0.45, [15.3, 19.7]);
vanoArco(17.5, 10, 2.2, 1.5, 0, "vano", "cal");
bloque(20, 48, 0, 12, -18, 0, "cal");
bloque(20, 48, 0, 0.8, 0, 0.2, "piedra");
bloque(19.8, 48.2, 12, 12.5, -18.2, 0.35, "cal");
bloque(20.2, 47.8, 12.5, 12.8, -17.8, -0.2, "teja");
for (const x of [24, 29.5, 35, 40.5]) {
  vanoArco(x, 5.5, 1.9, 1.5, 0);
  for (let i = -0.55; i <= 0.56; i += 0.275) bloque(R(x + i - 0.03), R(x + i + 0.03), 5.4, 8.2, 0.08, 0.16, "hierro");
}
vanoArco(45, 0.2, 2.6, 1.6, 0, "madera");

// ---------------------------------------------------------------- Gobernación (contexto, a la izquierda)
bloque(-80, -43, 0, 13, -18, -1.5, "gob");
bloque(-80.3, -42.7, 13, 13.5, -18.3, -1.2, "cal");
bloque(-80, -43, 13.5, 15.5, -16.5, -3.5, "pizarra");
for (let x = -77; x < -45; x += 4) {
  bloque(x - 0.7, x + 0.7, 1.2, 4.0, -1.5, -1.42, "vano");
  bloque(x - 0.7, x + 0.7, 6.0, 9.2, -1.5, -1.42, "vano");
  bloque(x - 1.0, x + 1.0, 6.0, 6.15, -1.5, -0.8, "hierro");
  bloque(x - 1.0, x + 1.0, 6.9, 6.97, -0.85, -0.8, "hierro");
}
cil(-46, 13, 15.5, -4.5, 5.0, "cal", 24);
esfera(-46, 15.5, -4.5, 5.0, "cupula", 4.4);
cil(-46, 17.4, 18.4, -4.5, 0.5, "hierro", 8);

// ---------------------------------------------------------------- vereda de la catedral
for (const x of [-37, -25, -13, -1, 16.5, 24, 32, 40]) arbolRedondo(x, 7.9);
for (const x of [-31, 4.2, 28]) farol(x, 9.0, 6.2);

// ---------------------------------------------------------------- plaza: pasillo frente a la catedral
bloque(-82, 55, 0, 0.18, 20, 28.5, "baldosa");
bloque(-82, 55, 0.18, 0.19, 23.6, 25.2, "baldosa2");
bloque(-82, 55, 0, 0.24, 20, 20.3, "acera"); // bordillo
let k = 0;
for (let x = -74; x <= 50; x += 8, k++) {
  cercaJardin(x, 21.6, 1.8);
  arbolGrande(x, 21.6, 10 + ((k * 37) % 5), k);
  if (x < 46) banco(x + 4, 22.0, -1);
}
for (const x of [-58, -30, -2, 26]) farol(x, 27.9, 5.0);

// ---------------------------------------------------------------- plaza: jardines
bloque(-82, 55, 0, 0.12, 28.5, 74, "cesped");
// reja baja del jardín, con aberturas para los caminos
for (const [x0, x1] of [[-82, -14], [-8, 22], [28, 55]] as const) {
  bloque(x0, x1, 0.12, 0.3, 28.6, 28.9, "acera");
  bloque(x0, x1, 0.75, 0.82, 28.72, 28.78, "hierro");
  for (let x = x0 + 0.5; x < x1; x += 1.0) bloque(R(x - 0.03), R(x + 0.03), 0.3, 0.85, 28.72, 28.78, "hierro");
}
// caminos interiores
bloque(-14, -8, 0.12, 0.2, 28.5, 74, "baldosa");
bloque(22, 28, 0.12, 0.2, 28.5, 74, "baldosa");
bloque(-82, 55, 0.12, 0.2, 44, 48, "baldosa");
// canteros de flores
const canteros: [number, number, number, number, Mat][] = [
  [-60, 36, 14, 8, "flor1"], [-35, 36, 16, 8, "flor2"], [8, 36, 18, 9, "flor3"],
  [40, 37, 16, 8, "flor1"], [-48, 58, 20, 10, "flor3"], [-28, 60, 10, 6, "flor1"],
  [40, 58, 18, 9, "flor2"], [8, 56, 9, 6, "flor1"],
];
for (const [x, z, dx, dz, m] of canteros) {
  cil(x, 0.12, 0.35, z, dx, "cesped", 32, dz);
  cil(x, 0.35, 0.55, z, dx * 0.82, m, 32, dz * 0.78);
  cil(x, 0.55, 0.7, z, dx * 0.45, "cesped", 32, dz * 0.4);
}
for (const [x, z, h] of [[-46, 40, 14], [-4, 52, 15], [33, 41, 13], [16, 64, 14], [-62, 66, 13]] as const) palmera(x, z, h);
for (const [x, z, h] of [[-70, 40, 11], [-22, 41, 12], [20, 45, 11], [48, 46, 12], [-38, 68, 12], [32, 68, 11], [-6, 68, 12]] as const)
  arbolGrande(x, z, h, Math.round(x));
for (const [x, z] of [[-20, 50], [40, 50], [-60, 50]] as const) farol(x, z, 5);
// monumento al centro de la plaza (a ~44 m del borde)
bloque(-3.5, 3.5, 0.12, 0.9, 60.5, 67.5, "monumento");
bloque(-2.3, 2.3, 0.9, 5.2, 61.7, 66.3, "monumento");
bloque(-2.7, 2.7, 5.2, 5.8, 61.3, 66.7, "monumento");
bloque(-1.6, 1.6, 5.8, 8.6, 62.4, 65.6, "monumento");
cil(0, 8.6, 9.0, 64, 2.6, "monumento", 20);
figura(0, 9.0, 64, 3.4, "bronce");

export const PRIMITIVAS: readonly Prim[] = P;

/** límites de la escena (para sombras y vóxeles) */
export const LIMITES = { x: [-82, 55], y: [-0.6, 38], z: [-26, 74] } as const;
