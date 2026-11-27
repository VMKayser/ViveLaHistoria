import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const raiz = path.resolve(__dirname, '../../../../..');
const requireWeb = createRequire(path.join(raiz, 'web/package.json'));
const validar = requireWeb('gltf-validator');

const datos = JSON.parse(fs.readFileSync(path.join(__dirname, 'mitsubishi_montero_sport_blanca.json'), 'utf8'));
const salida = path.join(raiz, 'web/public/models/ciudad/antigravity/vehiculos', datos.id);
const manifiesto = JSON.parse(fs.readFileSync(path.join(salida, `${datos.id}.variantes.json`), 'utf8'));

const sha256 = b => crypto.createHash('sha256').update(b).digest('hex');
const srgbALineal = h =>
  [0, 2, 4]
    .map(i => parseInt(h.slice(1 + i, 3 + i), 16) / 255)
    .map(v => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));

function leerGlb(nombre) {
  const bytes = fs.readFileSync(path.join(salida, nombre));
  assert.equal(bytes.readUInt32LE(0), 0x46546c67);
  assert.equal(bytes.readUInt32LE(4), 2);
  assert.equal(bytes.readUInt32LE(8), bytes.length);
  const largoJson = bytes.readUInt32LE(12);
  return {
    bytes,
    json: JSON.parse(bytes.toString('utf8', 20, 20 + largoJson)),
    binario: bytes.subarray(20 + largoJson),
  };
}

const maestro = leerGlb(`${datos.id}.glb`);
const pred = datos.variante_predeterminada;
const hexBase = datos.variantes[pred].principal.slice(1).toLowerCase();
const idxPintura = maestro.json.materials.findIndex(m => m.name.toLowerCase() === `muro__${hexBase}`);
assert(idxPintura >= 0, 'Falta pintura principal en el maestro');

function normalizarJson(doc) {
  const copia = structuredClone(doc);
  const nodoRaiz = copia.nodes.find(n => n.name === datos.id);
  if (nodoRaiz?.extras) delete nodoRaiz.extras.variante;
  const m = copia.materials[idxPintura];
  m.name = maestro.json.materials[idxPintura].name;
  m.pbrMetallicRoughness.baseColorFactor = maestro.json.materials[idxPintura].pbrMetallicRoughness.baseColorFactor;
  if (m.extras) {
    delete m.extras.pintura_vehiculo;
    if (!Object.keys(m.extras).length) delete m.extras;
  }
  return copia;
}

const resultados = [];
for (const v of manifiesto.variantes) {
  const actual = leerGlb(v.glb);
  assert.equal(sha256(actual.bytes), v.sha256_glb);
  assert.equal(actual.bytes.length, v.bytes_glb);
  assert(actual.binario.equals(maestro.binario), `${v.id}: cambió el binario`);
  assert.deepEqual(normalizarJson(actual.json), normalizarJson(maestro.json), `${v.id}: cambió estructura`);

  const esperado = srgbALineal(datos.variantes[v.id].principal);
  const mat = actual.json.materials[idxPintura];
  for (let i = 0; i < 3; i++) {
    assert(Math.abs(mat.pbrMetallicRoughness.baseColorFactor[i] - esperado[i]) < 1e-6);
  }
  assert(fs.statSync(path.join(salida, v.blend)).size > 200000);
  const informe = await validar.validateBytes(new Uint8Array(actual.bytes), { uri: v.glb });
  assert.equal(informe.issues.numErrors, 0, JSON.stringify(informe.issues.messages));
  assert.equal(informe.issues.numWarnings, 0, JSON.stringify(informe.issues.messages));
  resultados.push({ variante: v.id, bytes: actual.bytes.length, errores: 0, advertencias: 0, binario_identico: true });
}

fs.writeFileSync(path.join(raiz, 'revisiones/antigravity', datos.id, 'validacion_variantes.json'), JSON.stringify(resultados, null, 2) + '\n');
console.log(JSON.stringify(resultados));
