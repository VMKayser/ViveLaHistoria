#!/usr/bin/env node
/* Valida un GLB de vehículo: cabecera binaria, jerarquía de dirección y ruedas,
 * clips de 1 vuelta exacta, metadatos cinemáticos, ausencia de luces/cámaras de estudio,
 * presupuesto de triángulos, normal map empaquetado y gltf-validator en cero.
 */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    if (argv[i].startsWith('--') && i + 1 < argv.length) {
      out[argv[i].slice(2)] = argv[++i];
    }
  }
  return out;
}

function buscarPackageConValidador(inicio) {
  let actual = path.resolve(inicio);
  while (true) {
    for (const rel of ['package.json', 'web/package.json']) {
      const candidato = path.join(actual, rel);
      const valDir = path.join(path.dirname(candidato), 'node_modules/gltf-validator');
      if (fs.existsSync(candidato) && fs.existsSync(valDir)) return candidato;
    }
    const padre = path.dirname(actual);
    if (padre === actual) return null;
    actual = padre;
  }
}

const args = parseArgs(process.argv);
if (!args.glb || !args.datos) {
  console.error('Uso: node validar_glb_vehiculo.mjs --glb <modelo.glb> --datos <vehiculo.json> [--reporte <salida.json>]');
  process.exit(2);
}

const rutaGlb = path.resolve(args.glb);
const datos = JSON.parse(fs.readFileSync(path.resolve(args.datos), 'utf8'));
const idVehiculo = datos.id;
const bytes = fs.readFileSync(rutaGlb);

assert.equal(bytes.readUInt32LE(0), 0x46546c67, 'Cabecera magic GLB inválida');
assert.equal(bytes.readUInt32LE(4), 2, 'Versión GLB distinta de 2');
assert.equal(bytes.readUInt32LE(8), bytes.length, 'Longitud GLB inconsistente');

const largoJson = bytes.readUInt32LE(12);
const gltf = JSON.parse(bytes.toString('utf8', 20, 20 + largoJson));
const inicioBinario = 28 + largoJson;

function leerFlotantes(indice, componentes) {
  const a = gltf.accessors[indice];
  const vista = gltf.bufferViews[a.bufferView];
  assert.equal(a.componentType, 5126, 'El accessor debe ser FLOAT (5126)');
  const stride = vista.byteStride || componentes * 4;
  const base = inicioBinario + (vista.byteOffset || 0) + (a.byteOffset || 0);
  return Array.from({ length: a.count }, (_, i) =>
    Array.from({ length: componentes }, (_, j) => bytes.readFloatLE(base + i * stride + j * 4))
  );
}

const ruedas = [
  'rueda_trasera_derecha',
  'rueda_trasera_izquierda',
  'rueda_delantera_derecha',
  'rueda_delantera_izquierda',
];
for (const nombre of ruedas) {
  assert(gltf.nodes.some(n => n.name === nombre), `Falta pivote de rueda: ${nombre}`);
}
for (const lado of ['derecha', 'izquierda']) {
  const dir = gltf.nodes.find(n => n.name === `direccion_delantera_${lado}`);
  const idxRueda = gltf.nodes.findIndex(n => n.name === `rueda_delantera_${lado}`);
  assert(dir && dir.children?.includes(idxRueda), `direccion_delantera_${lado} debe ser padre de rueda_delantera_${lado}`);
  assert(dir.translation && Math.hypot(...dir.translation) > 0.2, `direccion_delantera_${lado} debe ubicarse en el eje delantero`);
  const nodoRueda = gltf.nodes[idxRueda];
  const desp = nodoRueda.translation ? Math.hypot(...nodoRueda.translation) : 0;
  assert(desp < 1e-5 && !nodoRueda.matrix, `rueda_delantera_${lado} no debe tener desplazamiento respecto a su pivote de dirección`);
}

for (const nombreClip of ['rodar_adelante', 'rodar_atras']) {
  const clip = gltf.animations?.find(a => a.name === nombreClip);
  assert(clip, `Falta el clip NLA ${nombreClip}`);
  for (const rueda of ruedas) {
    assert(
      clip.channels.some(c => gltf.nodes[c.target.node].name === rueda && c.target.path === 'rotation'),
      `El clip ${nombreClip} no anima la rotación de ${rueda}`
    );
  }
  for (const canal of clip.channels) {
    const sampler = clip.samplers[canal.sampler];
    const tiempos = leerFlotantes(sampler.input, 1);
    assert(tiempos.length >= 16, `${nombreClip}: insuficientes muestras (${tiempos.length})`);
    assert(Math.abs(tiempos.at(-1)[0] - tiempos[0][0] - 1.0) < 1e-5, `${nombreClip}: duración distinta de 1 s`);
    const qs = leerFlotantes(sampler.output, 4);
    let giroAcumulado = 0;
    for (let i = 1; i < qs.length; i++) {
      const a = qs[i - 1], b = qs[i];
      const z = b[2] * a[3] - b[3] * a[2] - b[0] * a[1] + b[1] * a[0];
      const w = b[0] * a[0] + b[1] * a[1] + b[2] * a[2] + b[3] * a[3];
      let d = 2 * Math.atan2(z, w);
      if (d > Math.PI) d -= 2 * Math.PI;
      if (d < -Math.PI) d += 2 * Math.PI;
      giroAcumulado += d;
    }
    const esperado = (nombreClip === 'rodar_adelante' ? -1 : 1) * 2 * Math.PI;
    assert(Math.abs(giroAcumulado - esperado) < 1e-4, `${nombreClip}: giro acumulado inválido (${giroAcumulado})`);
  }
}

const raiz = gltf.nodes.find(n => n.name === idVehiculo);
assert(raiz, `Falta el nodo raíz ${idVehiculo}`);
assert(raiz.extras?.movimiento?.radio_rueda > 0, 'Falta extras.movimiento en el nodo raíz');
assert.equal(gltf.cameras?.length || 0, 0, 'El GLB no debe exportar cámaras de estudio');
assert(!gltf.nodes.some(n => /^ESTUDIO_/.test(n.name || '')), 'Objetos de estudio filtrados al GLB');

const triangulos = gltf.meshes.reduce(
  (s, m) => s + m.primitives.reduce((t, p) => t + gltf.accessors[p.indices].count / 3, 0),
  0
);
const presupuesto = datos.acabados?.presupuesto_triangulos ?? 75000;
assert(triangulos > 4000 && triangulos < presupuesto, `Triángulos fuera de rango: ${triangulos}`);

if (datos.acabados?.textura_goma) {
  const conNormal = gltf.materials.filter(m => m.normalTexture);
  assert.equal(conNormal.length, 1, 'Exactamente el material del neumático debe llevar normalTexture');
  assert(gltf.images?.some(im => im.bufferView !== undefined), 'La textura normal debe ir empaquetada en el GLB');
}

const pkgValidador = args.package || buscarPackageConValidador(process.cwd());
let errores = 0;
let advertencias = 0;
if (pkgValidador) {
  const req = createRequire(pkgValidador);
  const validator = req('gltf-validator');
  const informe = await validator.validateBytes(new Uint8Array(bytes), { uri: path.basename(rutaGlb) });
  if (args.reporte) {
    fs.mkdirSync(path.dirname(path.resolve(args.reporte)), { recursive: true });
    fs.writeFileSync(path.resolve(args.reporte), JSON.stringify(informe, null, 2) + '\n');
  }
  errores = informe.issues.numErrors;
  advertencias = informe.issues.numWarnings;
  assert.equal(errores, 0, `Errores gltf-validator: ${JSON.stringify(informe.issues.messages)}`);
  assert.equal(advertencias, 0, `Advertencias gltf-validator: ${JSON.stringify(informe.issues.messages)}`);
}

console.log(
  JSON.stringify({
    archivo: path.basename(rutaGlb),
    bytes: bytes.length,
    triangulos,
    mallas: gltf.meshes.length,
    materiales: gltf.materials.length,
    errores_gltf: errores,
    advertencias_gltf: advertencias,
  })
);
