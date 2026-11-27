#!/usr/bin/env node
// Vehículos y red vial para la ciudad Godot.
//
// Entrada (solo lectura): web/public/trafico/<vehiculo>.glb (kits de web/scripts/preparar_vehiculos.mjs: piezas fundidas
// por función con tres niveles de detalle, comprimidas con meshopt) y web/public/trafico/red.json (carriles y cruces).
// Salida (como las teselas: u32 tamaño + zlib): ciudad3d/datos/vehiculos.json (tipos: movimiento, variantes de color, caja,
// archivo, masa, tornamesa, caballo…; flota: qué sale a la calle; caballo: clips y pelajes) + vehiculos/<id>.bin
// + red.json. El .bin es simple para leerlo sin decodificador meshopt en Godot:
//   u32 n piezas; por pieza: u8 largo + nombre, u32 v, u32 i, pos f32×3, nor f32×3, col f32×3 (lineal), tipo f32, idx u32.
// "tipo" es el tipo de vértice (1 pintura, 2 pintura de detalle, 3 faros, 4 pilotos, 5 ventanas) que el sombreador usa
// para pintar cada unidad de su color y encender las luces de noche. Las posiciones quedan en el marco del vehículo
// (x adelante, y arriba, z a la derecha), y la rueda centrada en su eje.
//
// Uso: node ciudad3d/herramientas/vehiculos.mjs
import { createRequire } from "node:module";
import { copyFileSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { deflateSync } from "node:zlib";
import { createHash } from "node:crypto";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "../..");
const ORIGEN = join(RAIZ, "web/public/trafico");
const DESTINO = join(RAIZ, "ciudad3d/datos");
const PIEZAS = ["cuerpo0", "vidrio0", "rueda0", "cuerpo1", "rueda1", "cuerpo2"];
/** Piezas que solo tienen algunos vehículos (rueda delantera de otro tamaño, eje delantero que gira entero). */
const OPCIONALES = ["ruedad0", "ruedad1", "tornamesa0", "tornamesa1"];
/** Lo que el kit lleva a Godot además de las mallas (de los extras de preparar_vehiculos.mjs). */
const CAMPOS = ["movimiento", "variantes", "caja", "masa", "piso", "tornamesa", "anclas", "caballo", "radio_delantera", "cochero", "riendas"];

// los módulos de gltf-transform y meshoptimizer viven en web/node_modules
const requerir = createRequire(join(RAIZ, "web/package.json"));
const importar = (m) => import(pathToFileURL(requerir.resolve(m)).href);
const { NodeIO } = await importar("@gltf-transform/core");
const { ALL_EXTENSIONS } = await importar("@gltf-transform/extensions");
const { MeshoptDecoder } = await importar("meshoptimizer");

await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ "meshopt.decoder": MeshoptDecoder });
mkdirSync(join(DESTINO, "vehiculos"), { recursive: true });

const tipos = {};
for (const archivo of readdirSync(ORIGEN).filter((f) => f.endsWith(".glb"))) {
  const doc = await io.read(join(ORIGEN, archivo));
  const nodos = doc.getRoot().listNodes();
  const raiz = nodos.find((n) => n.getExtras()?.movimiento);
  if (!raiz) continue;
  const id = raiz.getName();
  const trozos = [];
  const u32 = (n) => { const b = Buffer.alloc(4); b.writeUInt32LE(n); trozos.push(b); };
  const presentes = [...PIEZAS, ...OPCIONALES].filter((nombre) => nodos.some((n) => n.getName() === nombre && n.getMesh()));
  u32(presentes.length);
  for (const nombre of presentes) {
    const nodo = nodos.find((n) => n.getName() === nombre);
    const prim = nodo?.getMesh()?.listPrimitives()[0];
    if (!prim) throw new Error(`${archivo}: falta ${nombre}`);
    const m = nodo.getWorldMatrix();
    const p = prim.getAttribute("POSITION"), nr = prim.getAttribute("NORMAL"), c = prim.getAttribute("COLOR_0");
    const n = p.getCount();
    const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), col = new Float32Array(n * 3), tipo = new Float32Array(n);
    const e = [0, 0, 0], f = [0, 0, 0], k = [0, 0, 0, 0];
    for (let i = 0; i < n; i++) {
      p.getElement(i, e);
      for (let a = 0; a < 3; a++) pos[3 * i + a] = m[a] * e[0] + m[4 + a] * e[1] + m[8 + a] * e[2] + m[12 + a];
      nr.getElement(i, f);
      let x = m[0] * f[0] + m[4] * f[1] + m[8] * f[2], y = m[1] * f[0] + m[5] * f[1] + m[9] * f[2], z = m[2] * f[0] + m[6] * f[1] + m[10] * f[2];
      const l = Math.hypot(x, y, z) || 1;
      nor.set([x / l, y / l, z / l], 3 * i);
      c.getElement(i, k);
      col.set([k[0], k[1], k[2]], 3 * i);
      tipo[i] = Math.round(k[3] * 8);
    }
    const idx = Uint32Array.from(prim.getIndices().getArray());
    const nb = Buffer.from(nombre, "utf8");
    trozos.push(Buffer.from([nb.length]), nb);
    u32(n);
    u32(idx.length);
    for (const arr of [pos, nor, col, tipo, idx]) trozos.push(Buffer.from(arr.buffer, arr.byteOffset, arr.byteLength));
  }
  const crudo = Buffer.concat(trozos);
  const tam = Buffer.alloc(4);
  tam.writeUInt32LE(crudo.length);
  writeFileSync(join(DESTINO, "vehiculos", id + ".bin"), Buffer.concat([tam, deflateSync(crudo, { level: 9 })]));
  const x = raiz.getExtras();
  // v: huella del contenido (la web lo pide con ?v=… y lo guarda en caché para siempre)
  const v = createHash("sha1").update(crudo).digest("hex").slice(0, 10);
  tipos[id] = { archivo: `vehiculos/${id}.bin`, v };
  for (const k of CAMPOS) if (x[k] !== undefined) tipos[id][k] = x[k];
  console.log(`${id}: ${presentes.length} piezas`);
}
// la flota (qué sale a la calle y en qué proporción) y el caballo de las carrozas: de la configuración del tráfico
const config = JSON.parse(readFileSync(join(RAIZ, "web/scripts/vehiculos_trafico.json"), "utf8"));
const flota = config.flota.filter((f) => tipos[f.tipo] && (!f.remolque || tipos[f.remolque]));
const caballo = JSON.parse(readFileSync(join(ORIGEN, "caballo.json"), "utf8"));
writeFileSync(join(DESTINO, "vehiculos.json"), JSON.stringify({ tipos, flota, caballo, plaza: config.plaza ?? null }));
copyFileSync(join(ORIGEN, "red.json"), join(DESTINO, "red.json"));
console.log("vehiculos.json + red.json →", DESTINO);
