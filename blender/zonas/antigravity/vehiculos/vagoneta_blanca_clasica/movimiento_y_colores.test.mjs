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

const datos = JSON.parse(fs.readFileSync(new URL('./vagoneta_blanca_clasica.json', import.meta.url), 'utf8'));
const config = configurarMovimiento(datos);
const cerca = (a, b, tol = 1e-9) => assert(Math.abs(a - b) <= tol, `${a} != ${b}`);
const nuevo = () => new CinematicaVehiculo(config);

test('una circunferencia exacta avanza 2πr y gira una vuelta completa las cuatro ruedas', () => {
  const c = nuevo();
  const circunferencia = Math.PI * 2 * config.radio_rueda;
  c.avanzarDistancia(circunferencia);
  const s = c.estado();
  cerca(s.x, circunferencia);
  cerca(s.z, 0);
  for (const r of Object.values(s.ruedas)) {
    cerca(r.rodadura, -Math.PI * 2);
    cerca(r.distancia, circunferencia);
  }
});

test('retroceso invierte rodadura y regresar al origen la cancela', () => {
  const c = nuevo();
  c.avanzarDistancia(-3.5);
  assert(c.estado().ruedas.rueda_trasera_derecha.rodadura > 0);
  c.avanzarDistancia(3.5);
  cerca(c.estado().x, 0);
  for (const r of Object.values(c.estado().ruedas)) cerca(r.rodadura, 0);
});

test('en curvas cada rueda recorre su propio arco Ackermann sin deslizamiento lateral', () => {
  const c = nuevo();
  const radio = 8.5;
  const arco = (radio * Math.PI) / 2;
  const k = 1 / radio;
  c.avanzarDistancia(arco, k);
  const s = c.estado();
  cerca(s.rumbo, Math.PI / 2);
  for (const nombre of NOMBRES_RUEDAS) {
    const z = nombre.endsWith('_derecha') ? config.semivia : -config.semivia;
    const x = nombre.includes('_delantera_') ? c.batalla : 0;
    const r = s.ruedas[nombre];
    cerca(r.distancia, arco * Math.hypot(1 + k * z, k * x));
    cerca((1 + k * z) * Math.sin(r.direccion) - k * x * Math.cos(r.direccion), 0);
  }
  assert(s.ruedas.rueda_delantera_izquierda.direccion > s.ruedas.rueda_delantera_derecha.direccion);
  assert(s.ruedas.rueda_trasera_derecha.distancia > s.ruedas.rueda_trasera_izquierda.distancia);
});

test('frena antes de invertir marcha y al detenerse no giran las ruedas', () => {
  const c = nuevo();
  c.entrada({ velocidad: 6 });
  c.actualizar(2);
  const vAntes = c.velocidad;
  c.entrada({ velocidad: -2 });
  c.actualizar(0.1);
  assert(c.velocidad > 0);
  cerca(c.velocidad, vAntes - config.frenada * 0.1);
  c.entrada({ velocidad: 0, direccion: 0 });
  c.actualizar(3);
  cerca(c.velocidad, 0);
  const parado = c.estado();
  c.actualizar(5);
  for (const n of NOMBRES_RUEDAS) cerca(parado.ruedas[n].rodadura, c.estado().ruedas[n].rodadura);
});

test('invariancia de trayectoria y rodadura a 30, 60 y 120 FPS', () => {
  const estados = [30, 60, 120].map(fps => {
    const c = nuevo();
    c.entrada({ velocidad: 4.5, direccion: 0.28 });
    for (let i = 0; i < fps * 10; i++) c.actualizar(1 / fps);
    return c.estado();
  });
  for (const s of estados.slice(1)) {
    cerca(s.x, estados[0].x);
    cerca(s.z, estados[0].z);
    cerca(s.rumbo, estados[0].rumbo);
    for (const n of NOMBRES_RUEDAS) cerca(s.ruedas[n].rodadura, estados[0].ruedas[n].rodadura);
  }
});

test('adaptador Three VehiculoAnimado rota ruedas sin desplazar sus centros y teletransporta limpio', () => {
  const escena = new Group();
  const raiz = new Group();
  raiz.name = datos.id;
  raiz.userData.movimiento = config;
  escena.add(raiz);
  for (const n of NOMBRES_RUEDAS) {
    const rueda = new Group();
    rueda.name = n;
    const z = n.endsWith('_derecha') ? config.semivia : -config.semivia;
    if (n.includes('_delantera_')) {
      const dir = new Group();
      dir.name = n.replace('rueda_', 'direccion_');
      dir.position.set(config.eje_delantero, datos.centro_rueda_z, z);
      raiz.add(dir);
      dir.add(rueda);
    } else {
      rueda.position.set(config.eje_trasero, datos.centro_rueda_z, z);
      raiz.add(rueda);
    }
  }
  const auto = new VehiculoAnimado(escena, null, datos.id);
  const posOriginal = escena.getObjectByName('rueda_delantera_derecha').position.clone();
  auto.avanzarDistancia((config.radio_rueda * Math.PI) / 2);
  const rueda = escena.getObjectByName('rueda_delantera_derecha');
  const contacto = posOriginal.clone().set(0, -1, 0).applyQuaternion(rueda.quaternion);
  cerca(contacto.x, -1);
  cerca(contacto.y, 0);
  cerca(contacto.z, 0);
  assert(rueda.position.equals(posOriginal));
  auto.teletransportar({ x: 40, z: -15, rumbo: 0.5 });
  cerca(auto.estado().velocidad, 0);
});

test('recoloración por instancia aísla materiales compartidos y respeta parachoques/luces', () => {
  const matPintura = new MeshStandardMaterial({ name: 'muro__f2ece4', color: '#f2ece4' });
  const matBumper = new MeshStandardMaterial({ name: 'hierro__2b313f', color: '#2b313f' });
  const crearInstancia = () => {
    const g = new Group();
    const r = new Group();
    r.name = datos.id;
    r.userData.movimiento = config;
    r.add(new Mesh(new BoxGeometry(1, 1, 1), matPintura));
    r.add(new Mesh(new BoxGeometry(1, 1, 1), matBumper));
    g.add(r);
    return g;
  };
  const a = crearInstancia();
  const b = crearInstancia();
  aplicarVariante(a, 'guinda', datos.variantes);
  aplicarVariante(b, 'celeste', datos.variantes);
  const colorA = a.children[0].children[0].material.color.getHexString();
  const colorB = b.children[0].children[0].material.color.getHexString();
  assert.notEqual(colorA, colorB);
  assert.equal(a.children[0].children[1].material, matBumper);
});
