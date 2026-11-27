/* Validación del formato y del contrato para reutilizar este vehículo. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const raiz = path.resolve(__dirname, '../../../..');
const requireWeb = createRequire(path.join(raiz, 'web/package.json'));
const validator = requireWeb('gltf-validator');
const archivo = path.join(raiz, 'web/public/models/ciudad/codex/vehiculos/autobus_bronco.glb');
const bytes = fs.readFileSync(archivo);
assert.equal(bytes.readUInt32LE(0), 0x46546c67);
assert.equal(bytes.readUInt32LE(4), 2);
assert.equal(bytes.readUInt32LE(8), bytes.length);
const gltf = JSON.parse(bytes.toString('utf8', 20, 20 + bytes.readUInt32LE(12)));
const inicioBinario = 28 + bytes.readUInt32LE(12);
function leerFlotantes(indice, componentes) {
  const a = gltf.accessors[indice], vista = gltf.bufferViews[a.bufferView];
  assert.equal(a.componentType, 5126);
  return Array.from({ length: a.count }, (_, i) => Array.from({ length: componentes }, (_, j) =>
    bytes.readFloatLE(inicioBinario+(vista.byteOffset||0)+(a.byteOffset||0)+i*(vista.byteStride||componentes*4)+j*4)));
}
const pivotes = ['rueda_trasera_derecha', 'rueda_trasera_izquierda',
  'rueda_delantera_derecha', 'rueda_delantera_izquierda', 'puerta_pivote'];
for (const nombre of pivotes) assert(gltf.nodes.some(n => n.name === nombre), `Falta pivote ${nombre}`);
for (const lado of ['derecha', 'izquierda']) {
  const direccion = gltf.nodes.find(n => n.name === `direccion_delantera_${lado}`);
  const rueda = gltf.nodes.findIndex(n => n.name === `rueda_delantera_${lado}`);
  assert(direccion?.children.includes(rueda), `La dirección debe ser padre de la rueda ${lado}`);
}
for (const nombre of ['rodar_adelante', 'rodar_atras']) {
  const clip = gltf.animations?.find(a => a.name === nombre);
  assert(clip, `Falta el clip ${nombre}`);
  for (const rueda of pivotes.filter(n => n.startsWith('rueda_')))
    assert(clip.channels.some(c => gltf.nodes[c.target.node].name === rueda && c.target.path === 'rotation'));
  for (const canal of clip.channels) {
    const sampler = clip.samplers[canal.sampler];
    const tiempos = leerFlotantes(sampler.input, 1);
    assert(Math.abs(tiempos.at(-1)[0]-tiempos[0][0]-1)<1e-6, 'Cada clip debe durar un segundo');
    const qs = leerFlotantes(sampler.output, 4);
    let giro = 0;
    for (let i=1;i<qs.length;i++) {
      const a=qs[i-1],b=qs[i];
      const z=b[2]*a[3]-b[3]*a[2]-b[0]*a[1]+b[1]*a[0];
      const w=b[0]*a[0]+b[1]*a[1]+b[2]*a[2]+b[3]*a[3];
      let d=2*Math.atan2(z,w);
      if(d>Math.PI)d-=2*Math.PI;if(d<-Math.PI)d+=2*Math.PI;
      giro+=d;
    }
    assert(Math.abs(giro-(nombre==='rodar_adelante'?-1:1)*2*Math.PI)<1e-5,
      `${nombre}: el clip debe dar una vuelta completa en el sentido correcto`);
  }
}
const vehiculo = gltf.nodes.find(n => n.name === 'autobus_bronco');
assert(vehiculo.extras.movimiento.radio_rueda > 0, 'Falta la configuración para el controlador');
assert.equal(gltf.cameras?.length || 0, 0, 'El estudio no debe exportarse');
assert(!gltf.nodes.some(n => /ESTUDIO|Principal|Recorte/.test(n.name)), 'Hay objetos del estudio en el GLB');
const triangulos = gltf.meshes.reduce((s, m) => s + m.primitives.reduce((t, p) =>
  t + gltf.accessors[p.indices].count / 3, 0), 0);
const datos = JSON.parse(fs.readFileSync(path.join(__dirname, 'bronco.json'), 'utf8'));
assert(triangulos > 15000 && triangulos < datos.acabados.presupuesto_triangulos);
const goma = gltf.materials.filter(m => m.normalTexture);
assert.equal(goma.length, 1, 'El normal debe pertenecer solo a la goma del neumático');
assert.equal(goma[0].normalTexture.scale, datos.acabados.normal_goma_intensidad);
assert(gltf.images?.some(i => i.bufferView !== undefined), 'El normal debe estar empaquetado en el GLB');
validator.validateBytes(new Uint8Array(bytes), { uri: 'autobus_bronco.glb' }).then(informe => {
  fs.writeFileSync(path.join(raiz, 'revisiones/codex/autobus_bronco/validacion_gltf.json'), JSON.stringify(informe, null, 2));
  assert.equal(informe.issues.numErrors, 0, JSON.stringify(informe.issues.messages));
  assert.equal(informe.issues.numWarnings, 0, JSON.stringify(informe.issues.messages));
  console.log(JSON.stringify({ bytes: bytes.length, triangulos, mallas: gltf.meshes.length,
    errores: informe.issues.numErrors, advertencias: informe.issues.numWarnings, pivotes: pivotes.length }));
}).catch(error => { console.error(error); process.exitCode = 1; });
