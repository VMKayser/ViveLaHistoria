import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VehiculoAnimado, configurarMovimiento } from './cinematica_vehiculo.mjs';
import { aplicarVariante } from './colores_vehiculo.mjs';
import datos from './vagoneta_blanca_clasica.json';

const lienzo = document.querySelector('canvas');
const estado = document.querySelector('#estado');
const escena = new THREE.Scene();
escena.background = new THREE.Color('#c8c1c8');

const render = new THREE.WebGLRenderer({ canvas: lienzo, antialias: true });
render.setPixelRatio(Math.min(devicePixelRatio, 2));
render.shadowMap.enabled = true;
render.shadowMap.type = THREE.PCFSoftShadowMap;
render.toneMapping = THREE.ACESFilmicToneMapping;
render.toneMappingExposure = 1.22;

const camara = new THREE.PerspectiveCamera(35, 1, 0.05, 140);
camara.position.set(5.6, 2.3, 6.4);

const controles = new OrbitControls(camara, lienzo);
controles.target.set(0, 0.78, 0);
controles.enableDamping = true;
controles.minDistance = 1.4;
controles.maxDistance = 18;
controles.maxPolarAngle = Math.PI * 0.492;

escena.add(new THREE.HemisphereLight('#f6ece6', '#8d839b', 2.35));
const sol = new THREE.DirectionalLight('#fff0df', 3.4);
sol.position.set(5, 8.5, 5.5);
sol.castShadow = true;
sol.shadow.mapSize.set(2048, 2048);
Object.assign(sol.shadow.camera, { left: -5, right: 5, top: 5, bottom: -5, near: 0.1, far: 26 });
sol.shadow.bias = -0.0002;
sol.shadow.normalBias = 0.02;
escena.add(sol);
escena.add(sol.target);

const relleno = new THREE.DirectionalLight('#d0defc', 1.15);
relleno.position.set(-4, 3.5, -4.5);
escena.add(relleno);

const suelo = new THREE.Mesh(
  new THREE.PlaneGeometry(200, 200),
  new THREE.MeshStandardMaterial({ color: '#b7aeb7', roughness: 1 })
);
suelo.rotation.x = -Math.PI / 2;
suelo.position.y = -0.008;
suelo.receiveShadow = true;
escena.add(suelo);

const rejilla = new THREE.GridHelper(200, 100, '#9b929e', '#b3a9b5');
rejilla.position.y = -0.005;
rejilla.visible = false;
escena.add(rejilla);

let modelo;
let conductor;
let prueba = false;
let giro = false;
let alambre = false;
let tiempoAnterior;

const config = configurarMovimiento(datos);
const teclas = new Set();
const pulsadores = new Map();
const botonPrueba = document.querySelector('#probar');
const indicador = document.querySelector('#velocidad');
const luzInicial = sol.position.clone();

const ajustes = {
  perspectiva: [[5.6, 2.25, 6.4], [0, 0.78, 0]],
  lateral: [[0, 0.85, 8.2], [0, 0.82, 0]],
  frente: [[7.4, 0.88, 0], [0, 0.82, 0]],
  trasera: [[-7.4, 0.88, 0], [0, 0.82, 0]],
  peaton: [[5.4, 1.60, 6.0], [0, 0.85, 0]],
  rueda: [[2.05, 0.65, 2.05], [datos.ejes[1], datos.centro_rueda_z, datos.semivia_ruedas]],
};

document.querySelectorAll('[data-vista]').forEach(b =>
  b.addEventListener('click', () => {
    const [pos, mira] = ajustes[b.dataset.vista];
    camara.position.fromArray(pos);
    controles.target.fromArray(mira);
    if (conductor) {
      const s = conductor.estado();
      camara.position.x += s.x;
      camara.position.z += s.z;
      controles.target.x += s.x;
      controles.target.z += s.z;
    }
    controles.update();
    document.body.dataset.vista = b.dataset.vista;
  })
);

document.querySelector('#giro').addEventListener('click', e => {
  giro = !giro;
  e.currentTarget.setAttribute('aria-pressed', String(giro));
});

document.querySelector('#malla').addEventListener('click', e => {
  alambre = !alambre;
  modelo?.traverse(o => {
    if (o.isMesh) {
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) m.wireframe = alambre;
    }
  });
  e.currentTarget.setAttribute('aria-pressed', String(alambre));
});

function cambiarColor(id) {
  if (!modelo) return;
  aplicarVariante(modelo, id, datos.variantes, { nombreRaiz: datos.id });
  window.vehiculo.color = id;
  document.querySelector('#descargar-glb').href = `${datos.id}_${id}.glb`;
  document.querySelector('#descargar-blend').href = `${datos.id}_${id}.blend`;
  lienzo.setAttribute('aria-label', `Vista 3D de ${datos.nombre} (${datos.variantes[id].nombre})`);
}

document.querySelector('#color').addEventListener('change', e => cambiarColor(e.target.value));

new GLTFLoader().load(
  `./${datos.id}.glb`,
  gltf => {
    modelo = gltf.scene;
    modelo.traverse(o => {
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
      }
    });
    escena.add(modelo);
    conductor = new VehiculoAnimado(modelo, config, datos.id);
    window.vehiculo = { conductor, modelo, clips: gltf.animations.map(a => a.name) };
    cambiarColor(document.querySelector('#color').value);
    document.querySelectorAll('[data-conduccion]').forEach(b => {
      b.disabled = false;
    });
    estado.textContent = 'Arrastra para inspeccionar · usa flechas o W/A/S/D para conducir';
    document.body.dataset.modelo = 'cargado';
  },
  undefined,
  err => {
    estado.textContent = 'No se pudo cargar el GLB del vehículo.';
    console.error(err);
  }
);

function terminarPrueba() {
  prueba = false;
  botonPrueba.setAttribute('aria-pressed', 'false');
  botonPrueba.textContent = 'Probar marcha';
}
function limpiarMandos() {
  teclas.clear();
  pulsadores.clear();
}

botonPrueba.addEventListener('click', () => {
  if (!conductor) return;
  const siguiente = !prueba;
  limpiarMandos();
  terminarPrueba();
  prueba = siguiente;
  botonPrueba.setAttribute('aria-pressed', String(prueba));
  botonPrueba.textContent = prueba ? 'Terminar prueba' : 'Probar marcha';
});

document.querySelector('#frenar').addEventListener('click', () => {
  terminarPrueba();
  limpiarMandos();
  conductor?.entrada({ velocidad: 0, direccion: 0 });
});

document.querySelector('#reiniciar').addEventListener('click', () => {
  terminarPrueba();
  limpiarMandos();
  conductor?.teletransportar({ x: 0, z: 0, rumbo: 0 }, true);
  sol.position.copy(luzInicial);
  sol.target.position.set(0, 0, 0);
  document.querySelector('[data-vista="perspectiva"]').click();
});

const mapaTeclas = {
  ArrowUp: 'adelante',
  KeyW: 'adelante',
  ArrowDown: 'atras',
  KeyS: 'atras',
  ArrowLeft: 'izquierda',
  KeyA: 'izquierda',
  ArrowRight: 'derecha',
  KeyD: 'derecha',
};

addEventListener('keydown', e => {
  if (!conductor || e.ctrlKey || e.metaKey || e.altKey || /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
  if (mapaTeclas[e.code]) {
    e.preventDefault();
    terminarPrueba();
    teclas.add(e.code);
  } else if (e.code === 'Space') {
    e.preventDefault();
    document.querySelector('#frenar').click();
  }
});
addEventListener('keyup', e => {
  if (mapaTeclas[e.code]) {
    e.preventDefault();
    teclas.delete(e.code);
  }
});

document.querySelectorAll('[data-mando]').forEach(b => {
  b.addEventListener('pointerdown', e => {
    e.preventDefault();
    terminarPrueba();
    pulsadores.set(e.pointerId, b.dataset.mando);
    b.setPointerCapture(e.pointerId);
  });
  for (const ev of ['pointerup', 'pointercancel', 'lostpointercapture']) {
    b.addEventListener(ev, e => {
      pulsadores.delete(e.pointerId);
    });
  }
});

addEventListener('blur', limpiarMandos);
document.addEventListener('visibilitychange', () => {
  tiempoAnterior = undefined;
  if (document.hidden) {
    terminarPrueba();
    limpiarMandos();
    conductor?.entrada({ velocidad: 0, direccion: 0 });
  }
});

function actualizarMarcha(dt) {
  if (!conductor) return;
  const mandos = new Set([...Array.from(teclas, c => mapaTeclas[c]), ...pulsadores.values()]);
  const velocidad = prueba
    ? config.velocidad_demo
    : (mandos.has('adelante') ? 5.5 : 0) - (mandos.has('atras') ? 2.2 : 0);
  const direccion = prueba
    ? Math.atan((config.eje_delantero - config.eje_trasero) / config.radio_demo)
    : ((mandos.has('izquierda') ? 1 : 0) - (mandos.has('derecha') ? 1 : 0)) * config.direccion_maxima;
  const antes = conductor.estado();
  conductor.entrada({ velocidad, direccion });
  const despues = conductor.actualizar(dt);
  const dx = despues.x - antes.x;
  const dz = despues.z - antes.z;
  camara.position.x += dx;
  camara.position.z += dz;
  controles.target.x += dx;
  controles.target.z += dz;
  sol.position.x += dx;
  sol.position.z += dz;
  sol.target.position.x += dx;
  sol.target.position.z += dz;
  rejilla.visible =
    prueba || mandos.size > 0 || Math.abs(despues.velocidad) > 0.01 || Math.hypot(despues.x, despues.z) > 0.1;
  indicador.textContent = `${Math.abs(despues.velocidad * 3.6).toFixed(1)} km/h${
    despues.velocidad < -0.01 ? ' · R' : ''
  }`;
  document.body.dataset.movimiento = Math.abs(despues.velocidad) > 0.01 ? 'marcha' : 'detenido';
  for (const b of document.querySelectorAll('[data-mando]')) {
    b.dataset.activo = String(mandos.has(b.dataset.mando));
  }
}

function redimensionar() {
  render.setSize(lienzo.clientWidth, lienzo.clientHeight, false);
  camara.aspect = lienzo.clientWidth / lienzo.clientHeight;
  camara.fov = Math.max(
    35,
    THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(17.5)) / camara.aspect))
  );
  camara.updateProjectionMatrix();
}
new ResizeObserver(redimensionar).observe(lienzo);

render.setAnimationLoop(tiempo => {
  const dt = tiempoAnterior === undefined ? 0 : Math.min((tiempo - tiempoAnterior) / 1000, 0.1);
  tiempoAnterior = tiempo;
  actualizarMarcha(dt);
  controles.autoRotate = giro;
  controles.autoRotateSpeed = 1.0;
  controles.update(dt);
  render.render(escena, camara);
});
