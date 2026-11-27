import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createRequire } from 'node:module';
import { test } from 'node:test';
import { CinematicaCarruaje } from './cinematica_carruaje.mjs';
import { animarCaballoRome } from './caballo_rome.mjs';
import { aplicarVariante } from '../../../../../.agents/skills/vehiculo-3d-desde-diseno/scripts/colores_vehiculo.mjs';

const publico = new URL('../../../../../web/public/models/ciudad/codex/vehiculos/carrozas/',import.meta.url);
const requireWeb = createRequire(new URL('../../../../../web/package.json',import.meta.url));
const { validateBytes } = requireWeb('gltf-validator');
const ids = ['carroza_azul','carruaje_madera','caballo_rome'];

function glb(id) {
  const bytes = fs.readFileSync(new URL(id+'.glb',publico));
  const largo = bytes.readUInt32LE(12);
  const doc = JSON.parse(bytes.toString('utf8',20,20+largo));
  return { bytes,doc,inicio:28+largo };
}

function leer(archivo,id,n) {
  const a = archivo.doc.accessors[id], v = archivo.doc.bufferViews[a.bufferView];
  const formatos = {5126:[4,'readFloatLE'],5125:[4,'readUInt32LE'],
    5123:[2,'readUInt16LE'],5121:[1,'readUInt8']};
  const [size,funcion] = formatos[a.componentType];
  const inicio = archivo.inicio+(v.byteOffset ?? 0)+(a.byteOffset ?? 0);
  const stride = v.byteStride ?? size*n;
  return (i,j=0) => archivo.bytes[funcion](inicio+i*stride+j*size);
}

function triangulos(archivo) {
  for (const m of archivo.doc.meshes) {
    for (const p of m.primitives) {
      const pos = leer(archivo,p.attributes.POSITION,3);
      const ix = leer(archivo,p.indices,1);
      const cuenta = archivo.doc.accessors[p.indices].count;
      for (let i=0; i<cuenta; i+=3) {
        const b = [0,1,2].map(j => pos(ix(i+1),j)-pos(ix(i),j));
        const c = [0,1,2].map(j => pos(ix(i+2),j)-pos(ix(i),j));
        const area2 = Math.hypot(b[1]*c[2]-b[2]*c[1], b[2]*c[0]-b[0]*c[2], b[0]*c[1]-b[1]*c[0]);
        assert(area2>2e-11,`${m.name}: triángulo degenerado ${i/3}`);
      }
    }
  }
}

for (const id of ids) {
  test(`${id}: glTF, triángulos y clips`,async () => {
    const archivo = glb(id);
    const { doc,bytes } = archivo;
    const informe = await validateBytes(bytes);
    assert.equal(informe.issues.numErrors,0);
    assert.equal(informe.issues.numWarnings,0);
    assert(!doc.cameras?.length);
    triangulos(archivo);
    const ficha = JSON.parse(fs.readFileSync(new URL(id+'.ficha.json',publico)));
    const clips = id==='caballo_rome' ? ficha.clips : Object.fromEntries(ficha.clips.map(c=>[c,{duracion_s:1}]));
    assert.equal(doc.animations.length,Object.keys(clips).length);
    for (const clip of doc.animations) {
      for (const sampler of clip.samplers) {
        const tiempo = doc.accessors[sampler.input];
        assert.equal(tiempo.min[0],0);
        assert(Math.abs(tiempo.max[0]-clips[clip.name].duracion_s)<1e-6);
      }
    }
    if (id==='caballo_rome') {
      const cuerpo = doc.meshes.find(m=>m.name==='Cuerpo ROME');
      assert.equal(cuerpo.primitives.reduce((s,p)=>s+doc.accessors[p.indices].count/3,0),984);
      assert.equal(cuerpo.extras.targetNames.filter(n=>n.startsWith('rome_')).length,15);
      assert.equal(ficha.anclajes.length,4);
      assert(ficha.anclajes.every(n=>doc.nodes.some(o=>o.name===n)));
    }
  });
}

const { doc } = glb('carroza_azul');
const config = doc.nodes.find(n=>n.name==='carroza_azul').extras.movimiento;
const cerca = (a,b) => assert(Math.abs(a-b) < 1e-8,`${a} ≈ ${b}`);

test('Ruedas asimétricas y eje delantero sobre una tornamesa real',() => {
  const motor = new CinematicaCarruaje(config);
  motor.avanzarDistancia(4, .09);
  const { ruedas,direccion,distanciaCaballo } = motor.estado();
  const ri = ruedas.rueda_delantera_izquierda, rd = ruedas.rueda_delantera_derecha;
  cerca(ri.direccion,direccion);
  cerca(rd.direccion,direccion);
  cerca(rd.distancia-ri.distancia,2*.09*4*config.semivia);
  cerca(rd.rodadura,-rd.distancia/config.radios_ruedas.delantera);
  const rt = ruedas.rueda_trasera_derecha;
  cerca(rt.rodadura,-rt.distancia/config.radios_ruedas.trasera);
  assert(distanciaCaballo > 4);
});

test('Avance, parada, inversión y reinicio se conservan a 30, 60 y 120 FPS',() => {
  function prueba(fps) {
    const motor = new CinematicaCarruaje(config);
    for (const [velocidad,direccion,tiempo] of [[1.6,.22,2],[-.5,-.14,3],[0,0,2]]) {
      motor.entrada({velocidad,direccion});
      for (let i=0; i<fps*tiempo; i++) motor.actualizar(1/fps);
      cerca(motor.velocidad,velocidad);
    }
    const fin = motor.estado();
    const detenido = motor.actualizar(.2);
    cerca(fin.distanciaCaballo,detenido.distanciaCaballo);
    for (const nombre of Object.keys(fin.ruedas)) cerca(fin.ruedas[nombre].rodadura,detenido.ruedas[nombre].rodadura);
    motor.teletransportar({x:3,z:7,rumbo:0},true);
    cerca(motor.estado().distanciaCaballo,0);
    cerca(motor.estado().x,3);
    cerca(motor.estado().z,7);
    return fin;
  }
  const base = prueba(120);
  for (const fps of [30,60]) {
    const fin = prueba(fps);
    for (const clave of ['x','z','rumbo','distanciaCaballo']) cerca(base[clave],fin[clave]);
    for (const nombre of Object.keys(base.ruedas)) cerca(base.ruedas[nombre].rodadura,fin.ruedas[nombre].rodadura);
  }
});

const paletaRome = JSON.parse(fs.readFileSync(new URL('./caballo_rome.json',import.meta.url))).variantes;

test('Las cuatro descargas conservan toda la geometría y los clips del maestro',async () => {
  const maestro = glb('caballo_rome');
  for (const [id,paleta] of Object.entries(paletaRome)) {
    const variante = glb(`caballo_rome_${id}`);
    const informe = await validateBytes(variante.bytes);
    assert.equal(informe.issues.numErrors+informe.issues.numWarnings,0);
    assert.deepEqual(variante.bytes.subarray(variante.inicio),maestro.bytes.subarray(maestro.inicio));
    assert.deepEqual(variante.doc.animations,maestro.doc.animations);
    for (const rol of ['pelaje','crin']) {
      assert(variante.doc.materials.some(m => m.name===`${rol}__${paleta[rol].slice(1)}`));
    }
  }
});

test('El pelaje se aísla por instancia y el enganche sigue el galope',async () => {
  const THREE = await import('../../../../../web/node_modules/three/build/three.module.js');
  const { GLTFLoader } = await import('../../../../../web/node_modules/three/examples/jsm/loaders/GLTFLoader.js');
  const bin = glb('caballo_rome').bytes;
  const asset = await new GLTFLoader().parseAsync(Uint8Array.from(bin).buffer,'');
  const uno = asset.scene.clone(true), dos = asset.scene.clone(true);
  const color = (r,id) => aplicarVariante(r,id,paletaRome,{nombreRaiz:'caballo_rome',ranuras:['pelaje','crin']});
  const buscar = (obj,rol) => {
    let mat;
    obj.traverse(o => { if(o.isMesh && o.material.userData.pintura_vehiculo===rol) mat=o.material; });
    return mat;
  };
  color(uno,'tordo');
  color(dos,'negro');
  assert.notEqual(buscar(uno,'pelaje'),buscar(dos,'pelaje'));
  assert.equal(buscar(uno,'pelaje').color.getHexString(),paletaRome.tordo.pelaje.slice(1));
  assert.equal(buscar(dos,'pelaje').color.getHexString(),paletaRome.negro.pelaje.slice(1));
  assert.equal(buscar(asset.scene,'pelaje').color.getHexString(),paletaRome.alazan.pelaje.slice(1));
  const ancla = uno.getObjectByName('tiro_caballo_derecha');
  const quieta = ancla.position.clone();
  const animar = animarCaballoRome(uno,asset.animations,THREE.AnimationMixer);
  for (let i=0;i<22;i++) animar('galope',.035,1/60);
  assert(ancla.position.distanceTo(quieta)>.012);
  assert.equal(dos.getObjectByName(ancla.name).position.distanceTo(quieta),0);
  for (let i=0;i<100;i++) animar('reposo',0,1/60);
  assert(ancla.position.distanceTo(quieta)<.0001);
  animar.detener();
});
