import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { AutobusAnimado } from './autobus_animado.mjs';
import { configurarMovimiento } from './cinematica_vehiculo.mjs';
import datos from './bronco.json';
import { aplicarVariante } from './colores_bronco.mjs';

const lienzo = document.querySelector('canvas');
const estado = document.querySelector('#estado');
const escena = new THREE.Scene();
escena.background = new THREE.Color('#c8c1c8');
const render = new THREE.WebGLRenderer({ canvas: lienzo, antialias: true });
render.setPixelRatio(Math.min(devicePixelRatio, 2));
render.shadowMap.enabled = true;
render.shadowMap.type = THREE.PCFSoftShadowMap;
render.toneMapping = THREE.ACESFilmicToneMapping;
render.toneMappingExposure = 1.25;
const camara = new THREE.PerspectiveCamera(36, 1, .05, 150);
camara.position.set(7.5, 4.2, 10.5);
const controles = new OrbitControls(camara, lienzo);
controles.target.set(0, 1.5, 0);
controles.enableDamping = true;
controles.minDistance = 2;
controles.maxDistance = 22;
controles.maxPolarAngle = Math.PI * .49;
escena.add(new THREE.HemisphereLight('#f4e9e4', '#8d8299', 2.4));
const sol = new THREE.DirectionalLight('#fff0df', 3.5);
sol.position.set(5, 9, 6);
sol.castShadow = true;
sol.shadow.mapSize.set(2048, 2048);
Object.assign(sol.shadow.camera, { left: -7, right: 7, top: 7, bottom: -7, near: .1, far: 30 });
sol.shadow.bias = -.00025;
sol.shadow.normalBias = .025;
escena.add(sol);
escena.add(sol.target);
const relleno = new THREE.DirectionalLight('#d0defc', 1.2);
relleno.position.set(-4, 4, -5);
escena.add(relleno);
const suelo = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({ color: '#b7aeb7', roughness: 1 }));
suelo.rotation.x = -Math.PI / 2;
suelo.position.y = -.012;
suelo.receiveShadow = true;
escena.add(suelo);
const rejilla = new THREE.GridHelper(200, 100, '#9b929e', '#b3a9b5');
rejilla.position.y = -.008;
rejilla.visible = false;
escena.add(rejilla);
let autobus;
let conductor;
let prueba = false;
let tiempoAnterior;
const config = configurarMovimiento(datos);
const teclas = new Set();
const pulsadores = new Map();
const botonPrueba = document.querySelector('#probar');
const indicador = document.querySelector('#velocidad');
const luzInicial = sol.position.clone();
let giro = false;
let alambre = false;
const ajustes = {
  perspectiva: [[7.5, 4.2, 10.5], [0, 1.5, 0]],
  lateral: [[0, 1.6, 12], [0, 1.6, 0]],
  frente: [[11, 1.6, 0], [0, 1.6, 0]],
  trasera: [[-11, 1.6, 0], [0, 1.6, 0]],
  peaton: [[8, 1.6, 10], [0, 1.5, 0]],
  rueda: [[3.3, 1.3, 3.1], [1.92, .55, .965]],
};
document.querySelectorAll('[data-vista]').forEach(b => b.addEventListener('click', () => {
  const [pos, mira] = ajustes[b.dataset.vista];
  camara.position.fromArray(pos);
  controles.target.fromArray(mira);
  if (conductor) {
    const s = conductor.estado();
    camara.position.x += s.x; camara.position.z += s.z;
    controles.target.x += s.x; controles.target.z += s.z;
  }
  controles.update();
  document.body.dataset.vista = b.dataset.vista;
}));
document.querySelector('#giro').addEventListener('click', e => {
  giro = !giro;
  e.currentTarget.setAttribute('aria-pressed', String(giro));
});
document.querySelector('#malla').addEventListener('click', e => {
  alambre = !alambre;
  autobus?.traverse(o => {
    if (o.isMesh) for (const m of (Array.isArray(o.material) ? o.material : [o.material])) m.wireframe = alambre;
  });
  e.currentTarget.setAttribute('aria-pressed', String(alambre));
});
new GLTFLoader().load('./autobus_bronco.glb', gltf => {
  autobus = gltf.scene;
  autobus.traverse(o => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
    }
  });
  escena.add(autobus);
  conductor = new AutobusAnimado(autobus, config);
  window.bronco = { conductor, modelo: autobus, clips: gltf.animations.map(a => a.name) };
  cambiarColor(document.querySelector('#color').value);
  document.querySelectorAll('[data-conduccion]').forEach(b => { b.disabled = false; });
  estado.textContent = 'Arrastra para mirar · usa las flechas para conducir';
  document.body.dataset.modelo = 'cargado';
}, undefined, error => {
  estado.textContent = 'No se pudo cargar el modelo. Recarga la página.';
  console.error(error);
});

function cambiarColor(id) {
  if (!autobus) return;
  aplicarVariante(autobus, id, datos.variantes);
  window.bronco.color = id;
  document.querySelector('#descargar-glb').href = `autobus_bronco_${id}.glb`;
  document.querySelector('#descargar-blend').href = `autobus_bronco_${id}.blend`;
  lienzo.setAttribute('aria-label', `Vista 3D del autobús blanco y ${datos.variantes[id].nombre.toLowerCase()}`);
}
document.querySelector('#color').addEventListener('change', e => cambiarColor(e.target.value));

function terminarPrueba() {
  prueba = false;
  botonPrueba.setAttribute('aria-pressed', 'false');
  botonPrueba.textContent = 'Probar marcha';
}
function limpiarMandos() { teclas.clear(); pulsadores.clear(); }
botonPrueba.addEventListener('click', () => {
  if (!conductor) return;
  const nueva = !prueba;
  limpiarMandos();
  terminarPrueba();
  prueba = nueva;
  botonPrueba.setAttribute('aria-pressed', String(prueba));
  botonPrueba.textContent = prueba ? 'Terminar prueba' : 'Probar marcha';
});
document.querySelector('#frenar').addEventListener('click', () => {
  terminarPrueba(); limpiarMandos();
  conductor?.entrada({ velocidad: 0, direccion: 0 });
});
document.querySelector('#reiniciar').addEventListener('click', () => {
  terminarPrueba(); limpiarMandos();
  conductor?.teletransportar({ x: 0, z: 0, rumbo: 0 }, true);
  sol.position.copy(luzInicial); sol.target.position.set(0, 0, 0);
  document.querySelector('[data-vista="perspectiva"]').click();
});
const mapaTeclas = { ArrowUp: 'adelante', KeyW: 'adelante', ArrowDown: 'atras', KeyS: 'atras',
  ArrowLeft: 'izquierda', KeyA: 'izquierda', ArrowRight: 'derecha', KeyD: 'derecha' };
addEventListener('keydown', e => {
  if (!conductor || e.ctrlKey || e.metaKey || e.altKey || /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
  if (mapaTeclas[e.code]) {
    e.preventDefault(); terminarPrueba(); teclas.add(e.code);
  } else if (e.code === 'Space') { e.preventDefault(); document.querySelector('#frenar').click(); }
});
addEventListener('keyup', e => { if (mapaTeclas[e.code]) { e.preventDefault(); teclas.delete(e.code); } });
document.querySelectorAll('[data-mando]').forEach(b => {
  b.addEventListener('pointerdown', e => {
    e.preventDefault(); terminarPrueba();
    pulsadores.set(e.pointerId, b.dataset.mando); b.setPointerCapture(e.pointerId);
  });
  for (const evento of ['pointerup', 'pointercancel', 'lostpointercapture'])
    b.addEventListener(evento, e => { pulsadores.delete(e.pointerId); });
});
addEventListener('blur', limpiarMandos);
document.addEventListener('visibilitychange', () => {
  tiempoAnterior = undefined;
  if (document.hidden) { terminarPrueba(); limpiarMandos(); conductor?.entrada({ velocidad: 0, direccion: 0 }); }
});
function actualizarMarcha(dt) {
  if (!conductor) return;
  const mandos = new Set([...Array.from(teclas, c => mapaTeclas[c]), ...pulsadores.values()]);
  const velocidad = prueba ? config.velocidad_demo :
    (mandos.has('adelante') ? 4 : 0) - (mandos.has('atras') ? 1.5 : 0);
  const direccion = prueba ? Math.atan((config.eje_delantero-config.eje_trasero)/config.radio_demo) :
    ((mandos.has('izquierda') ? 1 : 0) - (mandos.has('derecha') ? 1 : 0)) * config.direccion_maxima;
  const antes = conductor.estado();
  conductor.entrada({ velocidad, direccion });
  const despues = conductor.actualizar(dt);
  const dx = despues.x - antes.x, dz = despues.z - antes.z;
  camara.position.x += dx; camara.position.z += dz;
  controles.target.x += dx; controles.target.z += dz;
  sol.position.x += dx; sol.position.z += dz;
  sol.target.position.x += dx; sol.target.position.z += dz;
  rejilla.visible = prueba || mandos.size > 0 || Math.abs(despues.velocidad) > .01 || Math.hypot(despues.x, despues.z) > .1;
  indicador.textContent = `${Math.abs(despues.velocidad*3.6).toFixed(1)} km/h${despues.velocidad < -.01 ? ' · R' : ''}`;
  document.body.dataset.movimiento = Math.abs(despues.velocidad) > .01 ? 'marcha' : 'detenido';
  for (const b of document.querySelectorAll('[data-mando]')) b.dataset.activo = String(mandos.has(b.dataset.mando));
}
function redimensionar() {
  render.setSize(lienzo.clientWidth, lienzo.clientHeight, false);
  camara.aspect = lienzo.clientWidth / lienzo.clientHeight;
  camara.fov = Math.max(36, THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(17)) / camara.aspect)));
  camara.updateProjectionMatrix();
}
new ResizeObserver(redimensionar).observe(lienzo);
render.setAnimationLoop(tiempo => {
  const dt = tiempoAnterior === undefined ? 0 : Math.min((tiempo-tiempoAnterior)/1000, .1);
  tiempoAnterior = tiempo;
  actualizarMarcha(dt);
  controles.autoRotate = giro;
  controles.autoRotateSpeed = 1;
  controles.update(dt);
  render.render(escena, camara);
});
