#!/usr/bin/env node
// Copias comprimidas (meshopt con cuantización de 16 bits en posiciones, sin simplificar nada) de los GLB de la ciudad.
//
// Origen:  public/models/ciudad/<agente>/<ID>.glb  (solo lectura: los exporta cada agente)
// Destino: public/models/opt/<agente>/<ID>.glb  +  public/models/opt/manifiesto.json
//
// El visor (datos/CatalogoModelos.ts) usa la copia comprimida solo si su marca 'actualizado' coincide con la del
// manifiesto del agente; si el agente re-exportó y aún no se corrió este script, se carga el original. Por eso nunca
// se ve un modelo viejo. Pesa ~5× menos (128 MB → ~26 MB), se descarga y se interpreta más rápido y no cambia la
// geometría: posiciones en 16 bits dentro de la caja de cada malla (≤ 5 mm en una malla de 300 m) y normales en 14 bits.
//
// Uso: npm run modelos:opt            (incremental)
//      npm run modelos:opt -- --todo  (rehace todo)
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..");
const ORIGEN = join(RAIZ, "public/models/ciudad");
const DESTINO = join(RAIZ, "public/models/opt");
const AGENTES = ["claude", "codex"];
const todo = process.argv.includes("--todo");

mkdirSync(DESTINO, { recursive: true });
const rutaMan = join(DESTINO, "manifiesto.json");
const previo = existsSync(rutaMan) ? JSON.parse(readFileSync(rutaMan, "utf8")) : {};
const nuevo = {};
let hechos = 0, omitidos = 0, antes = 0, despues = 0;
const t0 = Date.now();

for (const agente of AGENTES) {
  const rutaOrigen = join(ORIGEN, agente, "manifiesto.json");
  if (!existsSync(rutaOrigen)) continue;
  mkdirSync(join(DESTINO, agente), { recursive: true });
  const man = JSON.parse(readFileSync(rutaOrigen, "utf8"));
  for (const [id, v] of Object.entries(man)) {
    const clave = `${agente}/${id}`;
    const src = join(ORIGEN, agente, v.archivo);
    const dst = join(DESTINO, agente, v.archivo);
    if (!existsSync(src)) continue;
    const bytesOrigen = statSync(src).size;
    const p = previo[clave];
    if (!todo && p && p.actualizado === v.actualizado && p.bytesOrigen === bytesOrigen && existsSync(dst)) {
      nuevo[clave] = p;
      omitidos++;
      antes += bytesOrigen;
      despues += statSync(dst).size;
      continue;
    }
    // solo compresión meshopt, con la precisión máxima de la cuantización (posiciones 16 bits, normales 14): no se
    // sueldan, simplifican ni reordenan vértices con pérdida
    execFileSync("npx", [
      "gltf-transform", "meshopt", src, dst, "--level", "high",
      "--quantize-position", "16", "--quantize-normal", "14", "--quantize-color", "16",
    ], { cwd: RAIZ, stdio: "pipe" });
    const bytes = statSync(dst).size;
    nuevo[clave] = { archivo: v.archivo, actualizado: v.actualizado, bytesOrigen, bytes };
    hechos++;
    antes += bytesOrigen;
    despues += bytes;
    process.stdout.write(`  ${clave}: ${(bytesOrigen / 1e6).toFixed(2)} → ${(bytes / 1e6).toFixed(2)} MB\n`);
  }
}
writeFileSync(rutaMan, JSON.stringify(nuevo, null, 1));
console.log(`[modelos:opt] ${hechos} comprimidos, ${omitidos} al día · ${(antes / 1e6).toFixed(1)} MB → ${(despues / 1e6).toFixed(1)} MB (${(antes / Math.max(despues, 1)).toFixed(1)}×) en ${((Date.now() - t0) / 1000).toFixed(0)} s`);
