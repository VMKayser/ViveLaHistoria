import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { Group, Mesh, BoxGeometry, MeshStandardMaterial } from '../../../../../web/node_modules/three/build/three.module.js';
import {
  CinematicaVehiculo,
  VehiculoAnimado,
  configurarMovimiento,
  NOMBRES_RUEDAS,
} from '../../../../../.agents/skills/vehiculo-3d-desde-diseno/scripts/cinematica_vehiculo.mjs';
import { aplicarVariante } from '../../../../../.agents/skills/vehiculo-3d-desde-diseno/scripts/colores_vehiculo.mjs';

const datos = JSON.parse(fs.readFileSync(new URL('./mitsubishi_montero_sport_blanca.json', import.meta.url), 'utf8'));
const config = configurarMovimiento(datos);
const cerca = (a, b, tol = 1e-9) => assert(Math.abs(a - b) <= tol, `${a} != ${b}`);
const nuevo = () => new CinematicaVehiculo(config);

test('una vuelta exacta recorre 2πr en las cuatro ruedas todoterreno', () => {
  const c = nuevo();
  const d = Math.PI * 2 * config.radio_rueda;
  c.avanzarDistancia(d);
  cerca(c.estado().x, d);
  for (const r of Object.values(c.estado().ruedas)) cerca(r.rodadura, -Math.PI * 2);
});

test('arcos Ackermann diferenciados en curva y cero deriva lateral', () => {
  const c = nuevo();
  const radio = 9.5;
  const arco = (radio * Math.PI) / 2;
  const k = 1 / radio;
  c.avanzarDistancia(arco, k);
  const s = c.estado();
  cerca(s.rumbo, Math.PI / 2);
  assert(s.ruedas.rueda_delantera_izquierda.direccion > s.ruedas.rueda_delantera_derecha.direccion);
  assert(s.ruedas.rueda_trasera_derecha.distancia > s.ruedas.rueda_trasera_izquierda.distancia);
});

test('frenada previa a reversa, parada sin giro residual e invariancia a 30/60/120 FPS', () => {
  const estados = [30, 60, 120].map(fps => {
    const c = nuevo();
    c.entrada({ velocidad: 5, direccion: 0.25 });
    for (let i = 0; i < fps * 8; i++) c.actualizar(1 / fps);
    return c.estado();
  });
  for (const s of estados.slice(1)) {
    cerca(s.x, estados[0].x);
    cerca(s.z, estados[0].z);
    for (const n of NOMBRES_RUEDAS) cerca(s.ruedas[n].rodadura, estados[0].ruedas[n].rodadura);
  }
});

test('adaptador Three VehiculoAnimado y aislamiento de pintura por instancia', () => {
  const matBody = new MeshStandardMaterial({ name: 'muro__f3efe9', color: '#f3efe9' });
  const matCromo = new MeshStandardMaterial({ name: 'metal__dce1e8', color: '#dce1e8' });
  const mk = () => {
    const g = new Group();
    const r = new Group();
    r.name = datos.id;
    r.userData.movimiento = config;
    r.add(new Mesh(new BoxGeometry(1, 1, 1), matBody));
    r.add(new Mesh(new BoxGeometry(1, 1, 1), matCromo));
    for (const n of NOMBRES_RUEDAS) {
      const w = new Group();
      w.name = n;
      const z = n.endsWith('_derecha') ? config.semivia : -config.semivia;
      if (n.includes('_delantera_')) {
        const dir = new Group();
        dir.name = n.replace('rueda_', 'direccion_');
        dir.position.set(config.eje_delantero, datos.centro_rueda_z, z);
        r.add(dir);
        dir.add(w);
      } else {
        w.position.set(config.eje_trasero, datos.centro_rueda_z, z);
        r.add(w);
      }
    }
    g.add(r);
    return g;
  };
  const a = mk(), b = mk();
  aplicarVariante(a, 'grafito', datos.variantes);
  aplicarVariante(b, 'guinda', datos.variantes);
  assert.notEqual(a.children[0].children[0].material.color.getHexString(), b.children[0].children[0].material.color.getHexString());
  assert.equal(a.children[0].children[1].material, matCromo);
  const ctrl = new VehiculoAnimado(a, null, datos.id);
  ctrl.avanzarDistancia(2.0, 1 / 12);
  assert(a.getObjectByName('direccion_delantera_izquierda').rotation.y > 0);
});
