import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { Group, Mesh, BoxGeometry, MeshStandardMaterial } from '../../../../web/node_modules/three/build/three.module.js';
import { aplicarVariante } from './colores_bronco.mjs';

const datos = JSON.parse(fs.readFileSync(new URL('./bronco.json',import.meta.url)));
function objetos(materiales) {
  const modelo = new Group(), raiz = new Group(); raiz.name='autobus_bronco'; modelo.add(raiz);
  raiz.position.set(12,3,-4); raiz.rotation.y=.7;
  for(const m of materiales)raiz.add(new Mesh(new BoxGeometry(),m));
  return {modelo,raiz};
}
function materiales() {
  return [datos.colores.azul,datos.colores.azul_claro,'#cf3028'].map(h=>{
    const m = new MeshStandardMaterial({color:h});m.name=`pintura_acento__${h.slice(1)}`;return m;
  });
}

test('cada instancia conserva su pintura; pilotos y transformaciones no se alteran',()=>{
  const compartidos=materiales(), a=objetos(compartidos),b=objetos(compartidos);
  const pose=a.raiz.position.clone(),giro=a.raiz.quaternion.clone();
  aplicarVariante(a.modelo,'rojo',datos.variantes);
  assert.equal(a.raiz.children[0].material.color.getHexString(),'bd292e');
  assert.equal(b.raiz.children[0].material.color.getHexString(),'0343b8');
  assert.equal(a.raiz.children[2].material,compartidos[2]);
  assert(a.raiz.position.equals(pose));assert(a.raiz.quaternion.equals(giro));
  assert.equal(a.raiz.userData.variante,'rojo');
});

test('recorrer los cuatro colores reutiliza las pinturas privadas y conserva la geometría',()=>{
  const a=objetos(materiales()),geometria=a.raiz.children[0].geometry;
  aplicarVariante(a.modelo,'azul',datos.variantes);
  const pintura=a.raiz.children[0].material;
  for(const id of Object.keys(datos.variantes)) {
    aplicarVariante(a.modelo,id,datos.variantes);
    assert.equal(a.raiz.children[0].material,pintura);
    assert.equal(pintura.color.getHexString(),datos.variantes[id].principal.slice(1));
    assert.equal(a.raiz.children[0].geometry,geometria);
  }
});
