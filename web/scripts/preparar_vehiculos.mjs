#!/usr/bin/env node
// Prepara los vehículos de codex para circular por la ciudad: un "kit" por vehículo con tres niveles de detalle,
// listo para dibujarse con pocas llamadas de dibujo. La flota (qué vehículos, colores, luces, masa, caballos) está en
// scripts/vehiculos_trafico.json: una sola fuente.
//
// Origen (solo lectura, lo entrega codex): public/models/ciudad/codex/vehiculos/<archivo>.glb
// Destino: public/trafico/<vehiculo>.glb (+ resumen en public/trafico/vehiculos.json, caballo en caballo.json)
//          ../ciudad3d/vehiculos/caballo.glb (el caballo de las carrozas, animado: lo importa Godot)
//
// Qué hace y por qué:
// - Los originales traen decenas de mallas y materiales (85–92 mil triángulos los autos): aquí se funde todo por
//   FUNCIÓN, con el color en los vértices (como FusionadorLotes con la ciudad):
//     cuerpo    = carrocería, interior, puerta y decoración (opaco)
//     vidrio    = cristales (semitransparente, deja ver el interior de cerca)
//     rueda     = UNA rueda trasera (neumático, llanta, buje) centrada en su eje: se instancia ×4 (o ×2)
//     ruedad    = UNA rueda delantera, si es de otro tamaño (carrozas, remolque)
//     tornamesa = el eje delantero que gira entero (carrozas y remolque: varas, lanza, ballestas), en su marco
// - Tres niveles (simplificación de meshoptimizer con error absoluto en metros, sin tocar la silueta):
//     lod0 ( < ~36 m) cuerpo + vidrio + ruedas, casi sin pérdida
//     lod1 (36–140 m) cuerpo con los cristales fundidos (oscuros) + ruedas livianas
//     lod2 (lejos)    un solo bloque con las ruedas quietas
// - En el canal alfa del color va el TIPO de vértice (alfa = tipo / 8), que el sombreador usa para pintar cada
//   unidad de su color sin clonar materiales (1 pintura principal, 2 pintura de detalle) y para encender de noche
//   faros (3), pilotos (4) y ventanas (5).
// - Compresión meshopt (posiciones de 16 bits: 0,1 mm en un bus de 7 m), como el resto de los modelos.
//
// Uso: node scripts/preparar_vehiculos.mjs   (o npm run trafico)
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { Document, NodeIO } from "@gltf-transform/core";
import { ALL_EXTENSIONS } from "@gltf-transform/extensions";
import { MeshoptSimplifier } from "meshoptimizer";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..");
const ORIGEN = join(RAIZ, "public/models/ciudad/codex/vehiculos");
const DESTINO = join(RAIZ, "public/trafico");
const DESTINO_GODOT = join(RAIZ, "../ciudad3d/vehiculos");
const CONFIG = JSON.parse(readFileSync(join(RAIZ, "scripts/vehiculos_trafico.json"), "utf8"));
/** Cochero sentado (claude): se funde al cuerpo de las carrozas con "cochero": true, en el pescante. */
const COCHERO = join(RAIZ, "public/models/ciudad/claude/personajes/cochero/cochero_sentado.glb");
const ERROR_DEF = { cuerpo0: 0.003, rueda0: 0.006, cuerpo1: 0.04, rueda1: 0.035, cuerpo2: 0.16 };
const TIPO_VENTANA = 5;
const RUEDAS = ["rueda_trasera_derecha", "rueda_trasera_izquierda", "rueda_delantera_derecha", "rueda_delantera_izquierda"];

await MeshoptSimplifier.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
mkdirSync(DESTINO, { recursive: true });
const resumen = {};
const soloUno = process.argv[2];

for (const v of CONFIG.vehiculos) {
  if (soloUno && v.id !== soloUno) continue;
  const doc = await io.read(join(ORIGEN, v.archivo));
  const escena = doc.getRoot().getDefaultScene() ?? doc.getRoot().listScenes()[0];
  const nodos = doc.getRoot().listNodes();
  const nodo = (nombre) => nodos.find((n) => n.getName() === nombre);
  const raiz = nodos.find((n) => n.getExtras()?.movimiento);
  const nodoRueda = nodo(v.rueda);
  const nodoRuedaD = v.rueda_delantera ? nodo(v.rueda_delantera) : null;
  const torn = nodo("tornamesa_delantera");
  if (!raiz || !nodoRueda || (v.rueda_delantera && !nodoRuedaD)) throw new Error(`${v.id}: falta la raíz o una rueda de referencia`);
  const marco = {
    rueda: invertir(nodoRueda.getWorldMatrix()),
    ruedad: nodoRuedaD ? invertir(nodoRuedaD.getWorldMatrix()) : null,
    tornamesa: torn ? invertir(torn.getWorldMatrix()) : null,
  };

  // piezas por destino (cada una en su marco: la rueda en su eje, la tornamesa en su pivote)
  const piezas = { cuerpo: [], vidrio: [], rueda: [], ruedad: [], tornamesa: [] };
  const recorrer = (n, destino) => {
    const nombre = n.getName();
    const enRueda = destino === "rueda" || destino === "ruedad" || destino === "nada";
    if (nombre.startsWith("rueda_") && !enRueda) destino = nombre === v.rueda ? "rueda" : nombre === v.rueda_delantera ? "ruedad" : "nada";
    else if (nombre === "tornamesa_delantera") destino = "tornamesa";
    // (dentro de una rueda, las mallas hijas heredan su destino)
    const malla = n.getMesh();
    if (malla && destino !== "nada") {
      for (const prim of malla.listPrimitives()) {
        const mat = prim.getMaterial()?.getName() ?? "muro";
        const m = n.getWorldMatrix();
        if (destino === "cuerpo") (mat.startsWith("vidrio") && !v.tipos[mat] ? piezas.vidrio : piezas.cuerpo).push({ prim, matriz: m, mat });
        else piezas[destino].push({ prim, matriz: multiplicar(marco[destino], m), mat });
      }
    }
    for (const h of n.listChildren()) recorrer(h, destino);
  };
  for (const n of escena.listChildren()) recorrer(n, "cuerpo");

  const tipoDe = (mat) => v.tipos[mat] ?? (mat.startsWith("vidrio") ? TIPO_VENTANA : 0);
  let cuerpo = fundir(piezas.cuerpo, tipoDe);
  const mov = { ...raiz.getExtras().movimiento, ...(v.movimiento ?? {}) };
  const extras = {};

  // cochero sentado en el pescante (de frente, sobre el asiento más alto delante de la caja)
  if (v.cochero && existsSync(COCHERO)) {
    const dc = await io.read(COCHERO);
    const lista = [];
    for (const n of dc.getRoot().listNodes()) {
      for (const prim of n.getMesh()?.listPrimitives() ?? []) lista.push({ prim, matriz: n.getWorldMatrix(), mat: "cochero" });
    }
    const asiento = v.pescante ?? dc.getRoot().listNodes().find((n) => n.getExtras()?.pescante)?.getExtras().pescante?.[v.id];
    if (asiento) {
      cuerpo = concatenar(cuerpo, transformar(fundir(lista, () => 0), traslacion(asiento)));
      extras.cochero = asiento;
      // puños del cochero (marco del vehículo): de ahí salen las riendas hacia la boca del caballo
      const manos = dc.getRoot().listNodes().find((n) => n.getExtras()?.manos)?.getExtras().manos;
      if (manos) extras.riendas = Object.fromEntries(Object.entries(manos).map(([k, m]) => [k, m.map((x, i) => +(x + asiento[i]).toFixed(4))]));
    }
  }

  const vidrio = fundir(piezas.vidrio, tipoDe);
  const rueda = fundir(piezas.rueda, tipoDe);
  const ruedad = piezas.ruedad.length ? fundir(piezas.ruedad, tipoDe) : null;
  const tornamesa = piezas.tornamesa.length ? fundir(piezas.tornamesa, tipoDe) : null;
  const conVidrio = concatenar(cuerpo, vidrio);
  const error = { ...ERROR_DEF, ...(v.error ?? {}) };

  // ruedas de lod2: quietas, en su lugar (copias de la de referencia en cada pivote)
  const ruedaLiviana = simplificar(rueda, error.rueda1, 0.03, ["Permissive"], 0.3);
  const ruedadLiviana = ruedad ? simplificar(ruedad, error.rueda1, 0.03, ["Permissive"], 0.3) : null;
  let todo2 = tornamesa ? concatenar(conVidrio, transformar(tornamesa, torn.getWorldMatrix())) : conVidrio;
  for (const nombre of RUEDAS) {
    const n = nodo(nombre);
    if (!n) continue;
    const giro = nombre.endsWith("izquierda") ? rotY180() : identidad();
    const g = nombre.startsWith("rueda_delantera") && ruedadLiviana ? ruedadLiviana : ruedaLiviana;
    todo2 = concatenar(todo2, transformar(g, multiplicar(n.getWorldMatrix(), giro)));
  }

  const niveles = {
    cuerpo0: simplificar(cuerpo, error.cuerpo0, 1, []),
    vidrio0: vidrio,
    rueda0: simplificar(rueda, error.rueda0, 1, []),
    cuerpo1: simplificar(conVidrio, error.cuerpo1, 0.2, ["Permissive"]),
    rueda1: ruedaLiviana,
    cuerpo2: simplificar(todo2, error.cuerpo2, 0.02, ["Permissive", "Prune"], 0.3),
  };
  if (ruedad) {
    niveles.ruedad0 = simplificar(ruedad, error.rueda0, 1, []);
    niveles.ruedad1 = ruedadLiviana;
  }
  if (tornamesa) {
    niveles.tornamesa0 = simplificar(tornamesa, error.cuerpo0, 1, []);
    niveles.tornamesa1 = simplificar(tornamesa, error.cuerpo1, 0.2, ["Permissive"]);
    const p = posicion(torn.getWorldMatrix());
    extras.tornamesa = { x: p[0], y: p[1] };
    // anclajes de las correas del tiro (en el marco de la tornamesa) y enganche de la lanza
    const anclas = {};
    for (const nombre of ["tirante_derecha", "tirante_izquierda", "vara_punta_derecha", "vara_punta_izquierda", "enganche_frontal"]) {
      const n = nodo(nombre);
      if (n) anclas[nombre] = posicion(multiplicar(marco.tornamesa, n.getWorldMatrix())).map((x) => +x.toFixed(4));
    }
    extras.anclas = anclas;
  }
  if (ruedad) extras.radio_delantera = +(mov.radios_ruedas?.delantera ?? mov.radio_rueda).toFixed(4);
  if (mov.radios_ruedas?.trasera) mov.radio_rueda = mov.radios_ruedas.trasera;

  let caja = cajaDe(conVidrio);
  if (tornamesa) caja = unirCajas(caja, cajaDe(transformar(tornamesa, torn.getWorldMatrix())));
  // caballo enganchado: delante de la tornamesa, a la distancia de la lanza (contrato de codex, INTEGRACION.md)
  if (v.caballo) {
    const cab = await infoCaballo(v.caballo);
    const x = mov.enganche.distancia_al_eje_delantero_m + cab.avance;
    extras.caballo = { x: +x.toFixed(4), y: +(-extras.tornamesa.y).toFixed(4), boca: cab.boca };
    const enMundo = (q) => [q[0] + x + extras.tornamesa.x, q[1], q[2]];
    caja = unirCajas(caja, { min: enMundo(cab.caja.min), max: enMundo(cab.caja.max) });
  }

  // documento de salida: una malla por nivel/función, sin materiales propios (los pone Godot)
  const sal = new Document();
  const buf = sal.createBuffer();
  const esc = sal.createScene(v.id);
  const nodoRaiz = sal.createNode(v.id);
  const variantes = v.variantes ?? JSON.parse(readFileSync(join(ORIGEN, v.variantes_archivo), "utf8")).variantes;
  nodoRaiz.setExtras({
    movimiento: mov,
    variantes: variantes.map((x) => ({ id: x.id, principal: x.principal ?? x.colores?.principal, detalle: x.detalle ?? x.colores?.detalle })),
    caja,
    masa: v.masa,
    piso: v.piso,
    ...extras,
    triangulos: Object.fromEntries(Object.entries(niveles).map(([k, g]) => [k, g.indices.length / 3])),
    origen: `models/ciudad/codex/vehiculos/${v.archivo}`,
  });
  esc.addChild(nodoRaiz);
  for (const [nombre, g] of Object.entries(niveles)) {
    if (g.indices.length === 0) continue; // p. ej. sin cristales (remolque): la pieza no existe
    const prim = sal.createPrimitive()
      .setAttribute("POSITION", sal.createAccessor().setType("VEC3").setArray(g.pos).setBuffer(buf))
      .setAttribute("NORMAL", sal.createAccessor().setType("VEC3").setArray(g.nor).setBuffer(buf))
      .setAttribute("COLOR_0", sal.createAccessor().setType("VEC4").setArray(g.col).setBuffer(buf))
      .setIndices(sal.createAccessor().setType("SCALAR").setArray(g.indices).setBuffer(buf));
    const malla = sal.createMesh(nombre).addPrimitive(prim);
    nodoRaiz.addChild(sal.createNode(nombre).setMesh(malla));
  }
  const tmp = join(DESTINO, `${v.id}.crudo.glb`);
  const dst = join(DESTINO, `${v.id}.glb`);
  await io.write(tmp, sal);
  execFileSync("npx", ["gltf-transform", "meshopt", tmp, dst, "--level", "high",
    "--quantize-position", "16", "--quantize-normal", "12", "--quantize-color", "16"], { cwd: RAIZ, stdio: "pipe" });
  rmSync(tmp);
  const tri = Object.fromEntries(Object.entries(niveles).map(([k, g]) => [k, g.indices.length / 3]));
  resumen[v.id] = { archivo: `${v.id}.glb`, bytes: statSync(dst).size, bytesOrigen: statSync(join(ORIGEN, v.archivo)).size, triangulos: tri };
  console.log(v.id, JSON.stringify(resumen[v.id]));
}
if (!soloUno) {
  writeFileSync(join(DESTINO, "vehiculos.json"), JSON.stringify(resumen, null, 1) + "\n");
  await prepararCaballo(CONFIG.caballo);
}

// ---------------------------------------------------------------------------------------------------------- caballo

/** Avance desde la lanza y caja del caballo (marco del caballo: x adelante, y arriba, z a la derecha). */
async function infoCaballo(archivo) {
  const doc = await io.read(join(ORIGEN, archivo));
  const raiz = doc.getRoot().listNodes().find((n) => n.getExtras()?.clips);
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (const n of doc.getRoot().listNodes()) {
    for (const prim of n.getMesh()?.listPrimitives() ?? []) {
      const m = n.getWorldMatrix(), a = [0, 0, 0], b = [0, 0, 0], p = prim.getAttribute("POSITION");
      for (let i = 0; i < p.getCount(); i++) {
        aplicar(m, p.getElement(i, a), b);
        for (let k = 0; k < 3; k++) { min[k] = Math.min(min[k], b[k]); max[k] = Math.max(max[k], b[k]); }
      }
    }
  }
  // boca (el bocado, donde terminan las riendas): debajo del extremo delantero de la cabeza, en reposo
  let boca = null;
  for (const n of doc.getRoot().listNodes()) {
    if (!n.getName().startsWith("Cuerpo")) continue;
    for (const prim of n.getMesh()?.listPrimitives() ?? []) {
      const m = n.getWorldMatrix(), a = [0, 0, 0], b = [0, 0, 0], p = prim.getAttribute("POSITION");
      let suma = [0, 0, 0], k = 0, bajo = Infinity;
      for (let i = 0; i < p.getCount(); i++) {
        aplicar(m, p.getElement(i, a), b);
        if (b[0] > max[0] - 0.12) { suma = suma.map((x, j) => x + b[j]); k++; bajo = Math.min(bajo, b[1]); }
      }
      if (k) boca = [+(max[0] - 0.12).toFixed(3), +(bajo + 0.05).toFixed(3), 0];
    }
  }
  return { avance: raiz.getExtras().avance_desde_lanza_m ?? 0, clips: raiz.getExtras().clips, caja: { min, max }, boca };
}

/**
 * El caballo de las carrozas para Godot: misma malla, formas (morph targets) y clips que el de codex, pero con el color
 * de cada material en los vértices y el tipo (1 pelaje, 2 crin) en TEXCOORD_1, para que el sombreador de vehículos lo
 * pinte del pelaje de cada unidad con un solo material. Los pelajes y los clips van a public/trafico/caballo.json.
 */
async function prepararCaballo(cfg) {
  const doc = await io.read(join(ORIGEN, cfg.archivo));
  const raiz = doc.getRoot();
  const unico = doc.createMaterial("caballo");
  const buf = raiz.listBuffers()[0];
  for (const malla of raiz.listMeshes()) {
    for (const prim of malla.listPrimitives()) {
      const mat = prim.getMaterial();
      const c = colorDe(mat);
      const tipo = cfg.tipos[mat?.getExtras()?.pintura_vehiculo] ?? 0;
      const n = prim.getAttribute("POSITION").getCount();
      const col = new Float32Array(n * 4), uv = new Float32Array(n * 2);
      for (let i = 0; i < n; i++) {
        col.set([c[0], c[1], c[2], 1], i * 4);
        uv[i * 2] = tipo;
      }
      prim.setAttribute("COLOR_0", doc.createAccessor().setType("VEC4").setArray(col).setBuffer(buf));
      prim.setAttribute("TEXCOORD_1", doc.createAccessor().setType("VEC2").setArray(uv).setBuffer(buf));
      prim.setMaterial(unico);
      if (mat && mat !== unico) mat.dispose();
    }
  }
  for (const t of raiz.listTextures()) t.dispose();
  mkdirSync(DESTINO_GODOT, { recursive: true });
  await io.write(join(DESTINO_GODOT, "caballo.glb"), doc);
  const info = await infoCaballo(cfg.archivo);
  const pelajes = JSON.parse(readFileSync(join(ORIGEN, cfg.variantes_archivo), "utf8")).variantes
    .map((x) => ({ id: x.id, principal: x.pelaje, detalle: x.crin }));
  writeFileSync(join(DESTINO, "caballo.json"), JSON.stringify({ clips: info.clips, variantes: pelajes,
    origen: `models/ciudad/codex/vehiculos/${cfg.archivo}` }, null, 1) + "\n");
  console.log("caballo →", join(DESTINO_GODOT, "caballo.glb"));
}

// ---------------------------------------------------------------------------------------------------------- geometría

/** Color lineal del material: el factor; si tiene textura, el color que trae en el nombre (rol__rrggbb). */
function colorDe(mat) {
  const c = mat?.getBaseColorFactor() ?? [0.8, 0.8, 0.8, 1];
  const hex = mat?.getBaseColorTexture() && mat.getName().match(/__([0-9a-f]{6})$/i);
  if (!hex) return c;
  return [0, 2, 4].map((k) => Math.pow(parseInt(hex[1].slice(k, k + 2), 16) / 255, 2.2)).concat(1);
}
function posicion(m) { return [m[12], m[13], m[14]]; }
function traslacion(p) { return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, p[0], p[1], p[2], 1]; }
function unirCajas(a, b) {
  return { min: a.min.map((x, k) => +Math.min(x, b.min[k]).toFixed(3)), max: a.max.map((x, k) => +Math.max(x, b.max[k]).toFixed(3)) };
}

/** Une primitivas en una sola geometría (posición, normal, color lineal RGBA con el tipo en alfa) en el marco dado. */
function fundir(lista, tipoDe) {
  let nv = 0, ni = 0;
  for (const { prim } of lista) {
    nv += prim.getAttribute("POSITION").getCount();
    ni += prim.getIndices()?.getCount() ?? prim.getAttribute("POSITION").getCount();
  }
  const pos = new Float32Array(nv * 3), nor = new Float32Array(nv * 3), col = new Float32Array(nv * 4);
  const indices = new Uint32Array(ni);
  let ov = 0, oi = 0;
  for (const { prim, matriz, mat } of lista) {
    const p = prim.getAttribute("POSITION"), n = prim.getAttribute("NORMAL");
    const c = colorDe(prim.getMaterial());
    const cv = prim.getAttribute("COLOR_0");   // color por vértice (el cochero): manda sobre el del material
    const kc = [1, 1, 1, 1];
    const tipo = tipoDe(mat);
    const nm = matrizNormal(matriz);
    const espejo = determinante(matriz) < 0;
    const a = [0, 0, 0], b = [0, 0, 0];
    for (let i = 0; i < p.getCount(); i++) {
      p.getElement(i, a);
      aplicar(matriz, a, b);
      pos.set(b, (ov + i) * 3);
      if (n) {
        n.getElement(i, a);
        const x = nm[0] * a[0] + nm[3] * a[1] + nm[6] * a[2];
        const y = nm[1] * a[0] + nm[4] * a[1] + nm[7] * a[2];
        const z = nm[2] * a[0] + nm[5] * a[1] + nm[8] * a[2];
        const l = Math.hypot(x, y, z) || 1;
        nor.set([x / l, y / l, z / l], (ov + i) * 3);
      }
      if (cv) cv.getElement(i, kc);
      col.set([c[0] * kc[0], c[1] * kc[1], c[2] * kc[2], tipo / 8], (ov + i) * 4);
    }
    const idx = prim.getIndices();
    const cuenta = idx ? idx.getCount() : p.getCount();
    for (let k = 0; k < cuenta; k += 3) {
      const i0 = idx ? idx.getScalar(k) : k, i1 = idx ? idx.getScalar(k + 1) : k + 1, i2 = idx ? idx.getScalar(k + 2) : k + 2;
      indices[oi + k] = i0 + ov;
      indices[oi + k + 1] = (espejo ? i2 : i1) + ov;
      indices[oi + k + 2] = (espejo ? i1 : i2) + ov;
    }
    ov += p.getCount();
    oi += cuenta;
  }
  return { pos, nor, col, indices };
}

/**
 * Simplifica con meshoptimizer. error: metros (absoluto). La normal y el color pesan como atributos para que los
 * bordes duros y los límites entre colores sobrevivan; 'proporcion' es el piso de triángulos a conservar.
 */
function simplificar(g, error, proporcion, flags, pesoAtributos = 1) {
  const nv = g.pos.length / 3;
  const attr = new Float32Array(nv * 7);
  for (let i = 0; i < nv; i++) {
    attr.set([g.nor[3 * i], g.nor[3 * i + 1], g.nor[3 * i + 2], g.col[4 * i], g.col[4 * i + 1], g.col[4 * i + 2], g.col[4 * i + 3]], i * 7);
  }
  const objetivo = Math.max(3, Math.floor((g.indices.length * proporcion) / 3) * 3);
  const [idx] = MeshoptSimplifier.simplifyWithAttributes(
    g.indices, g.pos, 3, attr, 7, [0.25, 0.25, 0.25, 1, 1, 1, 4].map((w) => w * pesoAtributos), null,
    proporcion >= 1 ? 0 : objetivo, error, ["ErrorAbsolute", ...flags],
  );
  return compactar({ ...g, indices: idx });
}

/** Quita los vértices que ya no usa ningún triángulo. */
function compactar(g) {
  const nv = g.pos.length / 3;
  const mapa = new Int32Array(nv).fill(-1);
  let k = 0;
  for (const i of g.indices) if (mapa[i] < 0) mapa[i] = k++;
  const pos = new Float32Array(k * 3), nor = new Float32Array(k * 3), col = new Float32Array(k * 4);
  for (let i = 0; i < nv; i++) {
    const j = mapa[i];
    if (j < 0) continue;
    pos.set(g.pos.subarray(3 * i, 3 * i + 3), 3 * j);
    nor.set(g.nor.subarray(3 * i, 3 * i + 3), 3 * j);
    col.set(g.col.subarray(4 * i, 4 * i + 4), 4 * j);
  }
  const indices = new Uint32Array(g.indices.length);
  for (let i = 0; i < g.indices.length; i++) indices[i] = mapa[g.indices[i]];
  return { pos, nor, col, indices };
}

function concatenar(a, b) {
  const na = a.pos.length / 3;
  const indices = new Uint32Array(a.indices.length + b.indices.length);
  indices.set(a.indices);
  for (let i = 0; i < b.indices.length; i++) indices[a.indices.length + i] = b.indices[i] + na;
  const unir = (x, y) => { const r = new Float32Array(x.length + y.length); r.set(x); r.set(y, x.length); return r; };
  return { pos: unir(a.pos, b.pos), nor: unir(a.nor, b.nor), col: unir(a.col, b.col), indices };
}

function transformar(g, m) {
  const pos = new Float32Array(g.pos.length), nor = new Float32Array(g.nor.length);
  const nm = matrizNormal(m), b = [0, 0, 0];
  for (let i = 0; i < g.pos.length; i += 3) {
    aplicar(m, [g.pos[i], g.pos[i + 1], g.pos[i + 2]], b);
    pos.set(b, i);
    const a = [g.nor[i], g.nor[i + 1], g.nor[i + 2]];
    nor[i] = nm[0] * a[0] + nm[3] * a[1] + nm[6] * a[2];
    nor[i + 1] = nm[1] * a[0] + nm[4] * a[1] + nm[7] * a[2];
    nor[i + 2] = nm[2] * a[0] + nm[5] * a[1] + nm[8] * a[2];
  }
  return { pos, nor, col: g.col, indices: g.indices };
}

function cajaDe(g) {
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < g.pos.length; i += 3) {
    for (let k = 0; k < 3; k++) {
      min[k] = Math.min(min[k], g.pos[i + k]);
      max[k] = Math.max(max[k], g.pos[i + k]);
    }
  }
  return { min: min.map((x) => +x.toFixed(3)), max: max.map((x) => +x.toFixed(3)) };
}

// matrices 4×4 por columnas (como glTF)
function aplicar(m, a, o) {
  o[0] = m[0] * a[0] + m[4] * a[1] + m[8] * a[2] + m[12];
  o[1] = m[1] * a[0] + m[5] * a[1] + m[9] * a[2] + m[13];
  o[2] = m[2] * a[0] + m[6] * a[1] + m[10] * a[2] + m[14];
  return o;
}
function multiplicar(a, b) {
  const r = new Array(16).fill(0);
  for (let c = 0; c < 4; c++) for (let f = 0; f < 4; f++) for (let k = 0; k < 4; k++) r[c * 4 + f] += a[k * 4 + f] * b[c * 4 + k];
  return r;
}
function identidad() { return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]; }
function rotY180() { return [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1]; }
function determinante(m) {
  return m[0] * (m[5] * m[10] - m[9] * m[6]) - m[4] * (m[1] * m[10] - m[9] * m[2]) + m[8] * (m[1] * m[6] - m[5] * m[2]);
}
/** Inversa transpuesta del bloque 3×3 (por columnas). */
function matrizNormal(m) {
  const a = m[0], b = m[1], c = m[2], d = m[4], e = m[5], f = m[6], g = m[8], h = m[9], i = m[10];
  const det = determinante(m) || 1;
  // inversa (por columnas) y luego transpuesta
  const inv = [(e * i - f * h), -(b * i - c * h), (b * f - c * e), -(d * i - f * g), (a * i - c * g), -(a * f - c * d), (d * h - e * g), -(a * h - b * g), (a * e - b * d)].map((x) => x / det);
  return [inv[0], inv[3], inv[6], inv[1], inv[4], inv[7], inv[2], inv[5], inv[8]];
}
function invertir(m) {
  // transformaciones rígidas con escala: inversa general 4×4
  const inv = new Array(16);
  inv[0] = m[5] * m[10] * m[15] - m[5] * m[11] * m[14] - m[9] * m[6] * m[15] + m[9] * m[7] * m[14] + m[13] * m[6] * m[11] - m[13] * m[7] * m[10];
  inv[4] = -m[4] * m[10] * m[15] + m[4] * m[11] * m[14] + m[8] * m[6] * m[15] - m[8] * m[7] * m[14] - m[12] * m[6] * m[11] + m[12] * m[7] * m[10];
  inv[8] = m[4] * m[9] * m[15] - m[4] * m[11] * m[13] - m[8] * m[5] * m[15] + m[8] * m[7] * m[13] + m[12] * m[5] * m[11] - m[12] * m[7] * m[9];
  inv[12] = -m[4] * m[9] * m[14] + m[4] * m[10] * m[13] + m[8] * m[5] * m[14] - m[8] * m[6] * m[13] - m[12] * m[5] * m[10] + m[12] * m[6] * m[9];
  inv[1] = -m[1] * m[10] * m[15] + m[1] * m[11] * m[14] + m[9] * m[2] * m[15] - m[9] * m[3] * m[14] - m[13] * m[2] * m[11] + m[13] * m[3] * m[10];
  inv[5] = m[0] * m[10] * m[15] - m[0] * m[11] * m[14] - m[8] * m[2] * m[15] + m[8] * m[3] * m[14] + m[12] * m[2] * m[11] - m[12] * m[3] * m[10];
  inv[9] = -m[0] * m[9] * m[15] + m[0] * m[11] * m[13] + m[8] * m[1] * m[15] - m[8] * m[3] * m[13] - m[12] * m[1] * m[11] + m[12] * m[3] * m[9];
  inv[13] = m[0] * m[9] * m[14] - m[0] * m[10] * m[13] - m[8] * m[1] * m[14] + m[8] * m[2] * m[13] + m[12] * m[1] * m[10] - m[12] * m[2] * m[9];
  inv[2] = m[1] * m[6] * m[15] - m[1] * m[7] * m[14] - m[5] * m[2] * m[15] + m[5] * m[3] * m[14] + m[13] * m[2] * m[7] - m[13] * m[3] * m[6];
  inv[6] = -m[0] * m[6] * m[15] + m[0] * m[7] * m[14] + m[4] * m[2] * m[15] - m[4] * m[3] * m[14] - m[12] * m[2] * m[7] + m[12] * m[3] * m[6];
  inv[10] = m[0] * m[5] * m[15] - m[0] * m[7] * m[13] - m[4] * m[1] * m[15] + m[4] * m[3] * m[13] + m[12] * m[1] * m[7] - m[12] * m[3] * m[5];
  inv[14] = -m[0] * m[5] * m[14] + m[0] * m[6] * m[13] + m[4] * m[1] * m[14] - m[4] * m[2] * m[13] - m[12] * m[1] * m[6] + m[12] * m[2] * m[5];
  inv[3] = -m[1] * m[6] * m[11] + m[1] * m[7] * m[10] + m[5] * m[2] * m[11] - m[5] * m[3] * m[10] - m[9] * m[2] * m[7] + m[9] * m[3] * m[6];
  inv[7] = m[0] * m[6] * m[11] - m[0] * m[7] * m[10] - m[4] * m[2] * m[11] + m[4] * m[3] * m[10] + m[8] * m[2] * m[7] - m[8] * m[3] * m[6];
  inv[11] = -m[0] * m[5] * m[11] + m[0] * m[7] * m[9] + m[4] * m[1] * m[11] - m[4] * m[3] * m[9] - m[8] * m[1] * m[7] + m[8] * m[3] * m[5];
  inv[15] = m[0] * m[5] * m[10] - m[0] * m[6] * m[9] - m[4] * m[1] * m[10] + m[4] * m[2] * m[9] + m[8] * m[1] * m[6] - m[8] * m[2] * m[5];
  const det = m[0] * inv[0] + m[1] * inv[4] + m[2] * inv[8] + m[3] * inv[12];
  return inv.map((x) => x / det);
}
