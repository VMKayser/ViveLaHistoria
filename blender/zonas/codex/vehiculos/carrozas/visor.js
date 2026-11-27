import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CarruajeAnimado } from './cinematica_carruaje.mjs';
import { animarCaballoRome } from './caballo_rome.mjs';
import { aplicarVariante } from '../../../../../.agents/skills/vehiculo-3d-desde-diseno/scripts/colores_vehiculo.mjs';
import rome from './caballo_rome.json';

const $ = id => document.getElementById(id);
const lienzo = $('lienzo');
const status = $('estado');
const navegador = $('modelos');
const enganchar = $('enganchar');
const giro = $('giro');
const pelaje = $('pelaje');
const CABALLO = rome.id;
const velocidades = { reposo: 0, paso: 0.86, galope: 2.42, retroceso: -0.49 };
const pelajesPorVista = new Map([['carruaje_madera','castano']]);
for (const [id,color] of Object.entries(rome.variantes)) {
  pelaje.add(new Option(color.nombre,id));
}
const escena = new THREE.Scene();
escena.background = new THREE.Color('#e8d8c9');
escena.fog = new THREE.FogExp2('#e8d8c9', .034);

const camara = new THREE.PerspectiveCamera(41, 1, .03, 130);
const render = new THREE.WebGLRenderer({ antialias: true });
render.setPixelRatio(Math.min(window.devicePixelRatio, 1.7));
render.outputColorSpace = THREE.SRGBColorSpace;
render.toneMapping = THREE.ACESFilmicToneMapping;
render.toneMappingExposure = 1.14;
render.shadowMap.enabled = true;
render.shadowMap.type = THREE.PCFShadowMap;
render.domElement.setAttribute('aria-label', 'Modelo tridimensional. Arrastra para girar y pellizca o usa la rueda para acercar.');
lienzo.append(render.domElement);

const orbita = new OrbitControls(camara, render.domElement);
orbita.enableDamping = true;
orbita.minDistance = 1.0;
orbita.maxDistance = 25;
orbita.maxPolarAngle = Math.PI / 2.01;
orbita.enablePan = true;

escena.add(new THREE.HemisphereLight('#fff0e0', '#8e796f', 2.05));
const sol = new THREE.DirectionalLight('#fff2dc', 3.0);
sol.castShadow = true;
sol.shadow.mapSize.set(1536,1536);
Object.assign(sol.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8, near: .1, far: 28 });
sol.shadow.camera.updateProjectionMatrix();
sol.shadow.normalBias = .018;
escena.add(sol, sol.target);

const piso = new THREE.Mesh(new THREE.PlaneGeometry(185,185),
  new THREE.MeshStandardMaterial({ color: '#c4aa95', roughness: .93 }));
piso.rotation.x = -Math.PI/2;
piso.position.y = -.008;
piso.receiveShadow = true;
escena.add(piso);

const gltf = new GLTFLoader();
const pendientes = new Map();
const vector = () => new THREE.Vector3();
const reins = new THREE.MeshStandardMaterial({ color:'#432e2d', roughness:.88 });
const axisY = new THREE.Vector3(0, 1, 0);
const geometriaCorrea = new THREE.BoxGeometry(1, 1, 1);
let actual;
let seleccion = 'carroza_azul';
let modo = 'reposo';
let vista = 'tresCuartos';
let carga = 0;

function modelo(id) {
  if (!pendientes.has(id)) {
    pendientes.set(id, gltf.loadAsync(`./${id}.glb`).catch(error => {
      pendientes.delete(id);
      throw error;
    }));
  }
  return pendientes.get(id);
}

function sombras(raiz) {
  raiz.traverse(o => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
    }
  });
}

function actualizarPelaje() {
  if (!actual?.caballo) return;
  const id = pelajesPorVista.get(actual.id) ?? rome.variante_predeterminada;
  pelaje.value = id;
  aplicarVariante(actual.caballo,id,rome.variantes, {
    rolMaterial:'pelaje', ranuras:['pelaje','crin'], nombreRaiz:CABALLO,
  });
  if (actual.id===CABALLO) $('glb').href = `./${CABALLO}_${id}.glb`;
}

function liberarPelaje(caballo) {
  const materiales = new Set();
  caballo?.traverse(o => {
    if (!o.isMesh) return;
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
      if (m.userData.pintura_vehiculo) materiales.add(m);
    }
  });
  materiales.forEach(m => m.dispose());
}

function montarTiro(carruaje, escenaCaballo, contenedor) {
  const elementos = [];
  const varas = carruaje.raiz.getObjectByName('varas_caballo');
  varas.visible = true;
  for (const lado of ['derecha','izquierda']) {
    for (const [a, b, ancho] of [
      [`tirante_${lado}`,`tiro_caballo_${lado}`,.030],
      [`vara_punta_${lado}`,`cincha_caballo_${lado}`,.021],
    ]) {
      const correa = new THREE.Mesh(geometriaCorrea,reins);
      correa.castShadow = true;
      contenedor.add(correa);
      const apoyo = carruaje.raiz.getObjectByName(a);
      const hebilla = escenaCaballo.getObjectByName(b);
      if (!apoyo || !hebilla) throw new Error(`No se encontró el anclaje de ${lado}`);
      elementos.push({ apoyo, hebilla, correa, ancho });
    }
  }
  const a = vector(), b = vector(), rumbo = vector();
  return () => {
    contenedor.updateMatrixWorld(true);
    for (const { apoyo, hebilla, correa, ancho } of elementos) {
      apoyo.getWorldPosition(a);
      hebilla.getWorldPosition(b);
      contenedor.worldToLocal(a);
      contenedor.worldToLocal(b);
      rumbo.subVectors(b,a);
      correa.position.copy(a).lerp(b,.5);
      correa.scale.set(ancho,rumbo.length(),.009);
      correa.quaternion.setFromUnitVectors(axisY,rumbo.normalize());
    }
  };
}

function indicar(grupo, atributo, valor) {
  grupo.querySelectorAll(`button[data-${atributo}]`).forEach(b => {
    b.setAttribute('aria-pressed', String(b.dataset[atributo] === valor));
  });
}

function aplicarVista() {
  if (!actual) return;
  const sola = actual.id === CABALLO;
  const conTiro = Boolean(actual.carruaje && actual.caballo);
  const centro = actual.centro;
  const factor = Math.max(1, 1.47/camara.aspect);
  const lejos = sola ? 3.90 : conTiro ? 8.35 : 5.40;
  const extensiones = {
    tresCuartos: [lejos*.58, lejos*.36, lejos*.92],
    lateral: [0, lejos*.14, lejos*1.12],
    peaton: [lejos*.43, 1.60-centro.y, lejos*.96],
  };
  const [x,y,z] = extensiones[vista];
  orbita.target.copy(centro);
  camara.position.copy(centro).add(new THREE.Vector3(x*factor,y,z*factor));
  orbita.update();
}

async function cargar(id, mostrarCaballo) {
  const actualCarga = ++carga;
  status.textContent = 'Cargando modelo…';
  lienzo.dataset.ready = 'false';
  const esCaballo = id === CABALLO;
  try {
    const [asset, equino] = await Promise.all([
      modelo(id), esCaballo || !mostrarCaballo ? Promise.resolve(null) : modelo(CABALLO),
    ]);
    if (actualCarga !== carga) return;
    if (actual) {
      escena.remove(actual.grupo);
      actual.animar?.detener();
      liberarPelaje(actual.caballo);
      actual.caballo?.removeFromParent();
      actual.grupo.clear();
    }
    const grupo = new THREE.Group();
    const escenaModelo = esCaballo ? asset.scene.clone(true) : asset.scene;
    grupo.add(escenaModelo);
    const carruaje = esCaballo ? null : new CarruajeAnimado(escenaModelo,id);
    let animar = null, correas = null, caballo = esCaballo ? escenaModelo : null;
    if (carruaje) {
      const varas = asset.scene.getObjectByName('varas_caballo');
      varas.visible = Boolean(equino);
      if (equino) {
        caballo = equino.scene.clone(true);
        carruaje.tornamesa.add(caballo);
        const config = carruaje.cinematica;
        config.lanza += caballo.getObjectByName(CABALLO).userData.avance_desde_lanza_m;
        caballo.position.set(config.lanza, -config.radioDelantero, 0);
        correas = montarTiro(carruaje, caballo, grupo);
      }
    }
    if (caballo) {
      animar = animarCaballoRome(caballo,(equino || asset).animations,THREE.AnimationMixer);
      animar('reposo',0,0);
    }
    sombras(grupo);
    escena.add(grupo);
    const centro = new THREE.Vector3(esCaballo ? -.24 : equino ? 1.60 : 0,esCaballo ? .91 : 1.04,0);
    actual = { id, grupo, carruaje, caballo, animar, correas, centro, distancia:0 };
    $('opcion-caballo').hidden = esCaballo;
    $('opcion-giro').hidden = esCaballo;
    $('glb').href = `./${id}.glb`;
    $('blend').href = `./${id}.blend`;
    $('opcion-pelaje').hidden = !caballo;
    actualizarPelaje();
    modo = 'reposo';
    giro.value = '0';
    $('angulo').textContent = 'Recto';
    indicar($('marcha'), 'marcha', modo);
    aplicarVista();
    status.textContent = 'Arrastra para girar · Rueda o pellizco para acercar';
    lienzo.dataset.ready = 'true';
    lienzo.dataset.modelo = id;
  } catch (error) {
    if (actualCarga === carga) {
      status.textContent = 'No se pudo abrir el modelo 3D.';
      lienzo.dataset.ready = 'error';
      console.error(error);
    }
  }
}

navegador.addEventListener('click', ({ target }) => {
  const id = target.closest('[data-modelo]')?.dataset.modelo;
  if (!id || id === seleccion) return;
  seleccion = id;
  indicar(navegador, 'modelo', id);
  cargar(seleccion, enganchar.checked);
});
$('marcha').addEventListener('click', ({ target }) => {
  const elegida = target.closest('[data-marcha]')?.dataset.marcha;
  if (!elegida) return;
  modo = elegida;
  indicar($('marcha'), 'marcha', modo);
});
$('vistas').addEventListener('click', ({ target }) => {
  const elegida = target.closest('[data-vista]')?.dataset.vista;
  if (!elegida) return;
  vista = elegida;
  indicar($('vistas'), 'vista', vista);
  aplicarVista();
});
enganchar.addEventListener('change', () => cargar(seleccion, enganchar.checked));
pelaje.addEventListener('change', () => {
  if (!actual?.caballo) return;
  pelajesPorVista.set(actual.id,pelaje.value);
  actualizarPelaje();
});
giro.addEventListener('input', () => {
  const valor = Number(giro.value);
  const grados = Math.round(Math.abs(valor) * .29 * 180 / (100*Math.PI));
  $('angulo').textContent = valor === 0 ? 'Recto' : `${grados}° ${valor > 0 ? 'izquierda' : 'derecha'}`;
});

const desplazamiento = vector();
const encuadre = vector();
function actualizar(dt) {
  if (!actual) return;
  const { carruaje, caballo, animar, correas, centro } = actual;
  if (carruaje) {
    const estado = carruaje.actualizar(dt, {
      velocidad: velocidades[modo],
      direccion: Number(giro.value)/100*carruaje.cinematica.config.direccion_maxima,
    });
    if (caballo) {
      caballo.rotation.y = estado.rumboCaballoRelativo;
      const velocidad = estado.velocidad;
      const marcha = velocidad > 1.46 ? 'galope' : Math.abs(velocidad) > .035 ? 'paso' : 'reposo';
      animar(marcha, estado.distanciaCaballo-actual.distancia, dt);
      actual.distancia = estado.distanciaCaballo;
      correas();
    }
    const adelanto = caballo ? 1.60 : 0;
    encuadre.set(estado.x+adelanto*Math.cos(estado.rumbo), centro.y,
      estado.z-adelanto*Math.sin(estado.rumbo));
    desplazamiento.subVectors(encuadre,centro);
    centro.copy(encuadre);
    camara.position.add(desplazamiento);
    orbita.target.add(desplazamiento);
  } else {
    animar(modo==='retroceso' ? 'paso' : modo,velocidades[modo]*dt,dt);
  }
  piso.position.x = centro.x;
  piso.position.z = centro.z;
  sol.target.position.copy(centro);
  sol.position.copy(centro).add(new THREE.Vector3(5,8,4));
}
let previa = 0;
render.setAnimationLoop(ahora => {
  const dt = previa ? Math.min((ahora-previa)/1000,.075) : 0;
  previa = ahora;
  actualizar(dt);
  orbita.update();
  render.render(escena,camara);
});
new ResizeObserver(() => {
  const { clientWidth: w, clientHeight: h } = lienzo;
  if (!w || !h) return;
  camara.aspect = w/h;
  camara.updateProjectionMatrix();
  render.setSize(w,h,false);
  aplicarVista();
}).observe(lienzo);
if (new URLSearchParams(location.search).has('caballo')) {
  navegador.querySelector(`[data-modelo="${CABALLO}"]`).click();
} else cargar(seleccion,enganchar.checked);
