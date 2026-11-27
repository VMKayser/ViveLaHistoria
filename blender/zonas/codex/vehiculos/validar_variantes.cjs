/* Comprueba archivos finales: se permite cambiar pintura y etiqueta, nada más. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const { createRequire } = require('node:module');
const raiz = path.resolve(__dirname, '../../../..');
const requireWeb = createRequire(path.join(raiz, 'web/package.json'));
const validar = requireWeb('gltf-validator');
const salida = path.join(raiz, 'web/public/models/ciudad/codex/vehiculos');
const datos = JSON.parse(fs.readFileSync(path.join(__dirname, 'bronco.json')));
const manifiesto = JSON.parse(fs.readFileSync(path.join(salida, 'autobus_bronco.variantes.json')));
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
function leer(nombre) {
  const bytes = fs.readFileSync(path.join(salida, nombre));
  assert.equal(bytes.readUInt32LE(0), 0x46546c67);
  assert.equal(bytes.readUInt32LE(4), 2); assert.equal(bytes.readUInt32LE(8), bytes.length);
  const largo = bytes.readUInt32LE(12);
  return { bytes, json: JSON.parse(bytes.toString('utf8', 20, 20+largo)), binario: bytes.subarray(20+largo) };
}
const base = leer('autobus_bronco.glb');
const indices = [datos.colores.azul, datos.colores.azul_claro].map(h =>
  base.json.materials.findIndex(m => m.name === `pintura_acento__${h.slice(1)}`));
assert(indices.every(i => i >= 0));
function normalizar(doc) {
  const d = structuredClone(doc);
  delete d.nodes.find(n => n.name === 'autobus_bronco').extras.variante;
  for (const i of indices) {
    const m = d.materials[i];
    m.name = base.json.materials[i].name;
    m.pbrMetallicRoughness.baseColorFactor = base.json.materials[i].pbrMetallicRoughness.baseColorFactor;
    if (m.extras) { delete m.extras.pintura_bronco; if (!Object.keys(m.extras).length) delete m.extras; }
  }
  return d;
}
function lineal(h) {
  return [0,2,4].map(i => parseInt(h.slice(1+i,3+i),16)/255).map(v => v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
}
async function main() {
  assert.deepEqual(manifiesto.variantes.map(v => v.id), ['azul','rojo','amarillo','verde']);
  const resultados = [];
  for (const v of manifiesto.variantes) {
    const actual = leer(v.glb);
    assert.equal(hash(actual.bytes), v.sha256_glb);
    assert.equal(actual.bytes.length, v.bytes_glb);
    assert(actual.binario.equals(base.binario), `${v.id}: cambió el binario común`);
    assert.deepEqual(normalizar(actual.json), normalizar(base.json), `${v.id}: cambió algo además de la pintura`);
    for (const [j, k] of ['principal','detalle'].entries()) {
      const m = actual.json.materials[indices[j]], esperado = lineal(datos.variantes[v.id][k]);
      assert.equal(m.name, `pintura_acento__${datos.variantes[v.id][k].slice(1)}`);
      for (let i=0;i<3;i++) assert(Math.abs(m.pbrMetallicRoughness.baseColorFactor[i]-esperado[i])<1e-7);
      assert.equal(m.pbrMetallicRoughness.baseColorFactor[3],1);
    }
    assert(fs.statSync(path.join(salida,v.blend)).size>1000000);
    if (v.id==='azul') {
      assert(actual.bytes.equals(base.bytes));
      assert(fs.readFileSync(path.join(salida,v.blend)).equals(fs.readFileSync(path.join(salida,'autobus_bronco.blend'))));
    } else assert.equal(actual.json.nodes.find(n => n.name==='autobus_bronco').extras.variante,v.id);
    const informe = await validar.validateBytes(new Uint8Array(actual.bytes), {uri:v.glb});
    assert.equal(informe.issues.numErrors,0,JSON.stringify(informe.issues.messages));
    assert.equal(informe.issues.numWarnings,0,JSON.stringify(informe.issues.messages));
    resultados.push({color:v.id,bytes:actual.bytes.length,errores:0,advertencias:0,binario_identico:true});
  }
  fs.writeFileSync(path.join(raiz,'revisiones/codex/autobus_bronco/validacion_variantes.json'),JSON.stringify(resultados,null,2));
  console.log(JSON.stringify(resultados));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
