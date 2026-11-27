import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { Group } from '../../../../web/node_modules/three/build/three.module.js';
import { CinematicaVehiculo, configurarMovimiento, NOMBRES_RUEDAS } from './cinematica_vehiculo.mjs';
import { AutobusAnimado } from './autobus_animado.mjs';

const datos = JSON.parse(fs.readFileSync(new URL('./bronco.json', import.meta.url)));
const config = configurarMovimiento(datos);
const cerca = (a, b, tolerancia = 1e-9) => assert(Math.abs(a-b) <= tolerancia, `${a} != ${b}`);
const nuevo = () => new CinematicaVehiculo(config);

test('una circunferencia desplaza el autobús y da una vuelta exacta en las cuatro ruedas', () => {
  const c = nuevo(), distancia = Math.PI*2*config.radio_rueda;
  c.avanzarDistancia(distancia);
  const s = c.estado();
  cerca(s.x, distancia); cerca(s.z, 0);
  for (const r of Object.values(s.ruedas)) { cerca(r.rodadura, -Math.PI*2); cerca(r.distancia, distancia); }
});

test('retroceder invierte el giro; volver al origen deshace la rodadura', () => {
  const c = nuevo(); c.avanzarDistancia(-4);
  assert(c.estado().ruedas.rueda_trasera_derecha.rodadura > 0);
  c.avanzarDistancia(4);
  cerca(c.estado().x, 0);
  for (const r of Object.values(c.estado().ruedas)) cerca(r.rodadura, 0);
});

test('en una curva cada rueda recorre su propio arco, sin velocidad lateral', () => {
  const c = nuevo(), radio = 12, distancia = radio*Math.PI/2, k = 1/radio;
  c.avanzarDistancia(distancia, k);
  const s = c.estado(), batalla = c.batalla;
  cerca(s.rumbo, Math.PI/2);
  cerca(c.traseroX, config.eje_trasero+radio); cerca(c.traseroZ, -radio);
  for (const nombre of NOMBRES_RUEDAS) {
    const z = nombre.endsWith('_derecha') ? config.semivia : -config.semivia;
    const x = nombre.includes('_delantera_') ? batalla : 0;
    const r = s.ruedas[nombre];
    cerca(r.distancia, distancia*Math.hypot(1+k*z,k*x));
    // Producto con la dirección lateral de la rueda: debe ser cero.
    cerca((1+k*z)*Math.sin(r.direccion)-k*x*Math.cos(r.direccion),0);
  }
  assert(s.ruedas.rueda_delantera_izquierda.direccion > s.ruedas.rueda_delantera_derecha.direccion);
  assert(s.ruedas.rueda_trasera_derecha.distancia > s.ruedas.rueda_trasera_izquierda.distancia);
});

test('al girar a la derecha cambia la rueda interior; retroceder conserva Ackermann', () => {
  const c = nuevo(); c.avanzarDistancia(-3, -1/12);
  const r = c.estado().ruedas;
  assert(Math.abs(r.rueda_delantera_derecha.direccion) > Math.abs(r.rueda_delantera_izquierda.direccion));
  assert(r.rueda_delantera_derecha.rodadura > 0);
  assert(c.estado().rumbo > 0);
});

test('aceleración, frenada y volante tienen límites; parar impide que sigan girando', () => {
  const c = nuevo(); c.entrada({ velocidad: 5, direccion: .4 });
  c.actualizar(.25); cerca(c.velocidad, config.aceleracion*.25);
  cerca(c.direccion, config.rapidez_direccion*.25);
  c.entrada({ velocidad: 0, direccion: 0 }); c.actualizar(2);
  cerca(c.velocidad, 0);
  const antes = c.estado(); c.actualizar(10); const despues = c.estado();
  cerca(antes.x, despues.x); cerca(antes.z, despues.z);
  for (const n of NOMBRES_RUEDAS) cerca(antes.ruedas[n].rodadura, despues.ruedas[n].rodadura);
});

test('cambiar de marcha frena primero, sin invertir instantáneamente la velocidad', () => {
  const c = nuevo(); c.entrada({ velocidad: 4 }); c.actualizar(3);
  const antes = c.velocidad;
  c.entrada({ velocidad: -1.5 }); c.actualizar(.1);
  assert(c.velocidad > 0); cerca(c.velocidad, antes-config.frenada*.1);
  c.actualizar(3); assert(c.velocidad < 0);
});

test('misma trayectoria y rodadura a 30, 60 y 120 FPS', () => {
  const resultados = [30,60,120].map(fps => {
    const c = nuevo(); c.entrada({ velocidad: 3, direccion: .25 });
    for(let i=0;i<fps*12;i++) c.actualizar(1/fps);
    return c.estado();
  });
  for(const s of resultados.slice(1)) {
    cerca(s.x,resultados[0].x); cerca(s.z,resultados[0].z); cerca(s.rumbo,resultados[0].rumbo);
    for(const n of NOMBRES_RUEDAS) cerca(s.ruedas[n].rodadura,resultados[0].ruedas[n].rodadura);
  }
});

test('teletransportar y reiniciar no producen giros ficticios', () => {
  const c = nuevo(); c.avanzarDistancia(4); const fase = c.estado().ruedas.rueda_delantera_derecha.rodadura;
  c.teletransportar({x:300,z:-200,rumbo:.8});
  cerca(c.estado().ruedas.rueda_delantera_derecha.rodadura,fase); cerca(c.velocidad,0);
  c.teletransportar({x:0,z:0,rumbo:0},true);
  cerca(c.estado().ruedas.rueda_delantera_derecha.rodadura,0);
});

test('girar parado no hace rodar las ruedas y dt=0 no modifica el estado', () => {
  const c=nuevo(); c.entrada({direccion:.3}); c.actualizar(1);
  assert(c.direccion>0);
  for(const r of Object.values(c.estado().ruedas)) cerca(r.rodadura,0);
  const antes=c.estado();assert.deepEqual(c.actualizar(0),antes);
});

test('rechaza geometría y entradas no finitas o físicamente imposibles', () => {
  assert.throws(()=>new CinematicaVehiculo({...config,radio_rueda:0}));
  const c=nuevo();assert.throws(()=>c.actualizar(-1));assert.throws(()=>c.entrada({velocidad:NaN}));
  assert.throws(()=>c.avanzarDistancia(2,10));
});

test('el adaptador transforma la jerarquía real de Three sin mover los centros de rueda', () => {
  const modelo=new Group(),raiz=new Group();raiz.name='autobus_bronco';modelo.add(raiz);
  raiz.userData.movimiento=config;
  for(const n of NOMBRES_RUEDAS){
    const rueda=new Group();rueda.name=n;
    const z=n.endsWith('_derecha')?config.semivia:-config.semivia;
    if(n.includes('_delantera_')){
      const direccion=new Group();direccion.name=n.replace('rueda_','direccion_');
      direccion.position.set(config.eje_delantero,datos.centro_rueda_z,z);raiz.add(direccion);direccion.add(rueda);
    }else{rueda.position.set(config.eje_trasero,datos.centro_rueda_z,z);raiz.add(rueda);}
  }
  const bus=new AutobusAnimado(modelo),antes=modelo.getObjectByName('rueda_delantera_derecha').position.clone();
  bus.avanzarDistancia(.49*Math.PI/2);
  const rueda=modelo.getObjectByName('rueda_delantera_derecha');
  // q y -q describen la misma orientación: comprobar el punto de contacto.
  const contacto=antes.clone().set(0,-1,0).applyQuaternion(rueda.quaternion);
  cerca(contacto.x,-1);cerca(contacto.y,0);cerca(contacto.z,0);
  assert(rueda.position.equals(antes));
  bus.avanzarDistancia(2,1/12);
  cerca(modelo.getObjectByName('direccion_delantera_derecha').rotation.y,bus.estado().ruedas.rueda_delantera_derecha.direccion);
});
