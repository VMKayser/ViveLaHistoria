import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { crearConductor } from './controlador.mjs';

const $ = s => document.querySelector(s);
const escena = new THREE.Scene();
escena.background = new THREE.Color('#c8c0c8');
const render = new THREE.WebGLRenderer({ canvas: $('canvas'), antialias: true });
render.setPixelRatio(Math.min(devicePixelRatio, 2));
render.shadowMap.enabled = true;
render.shadowMap.type = THREE.PCFShadowMap;
render.toneMapping = THREE.ACESFilmicToneMapping;
render.toneMappingExposure = 1.15;
const camara = new THREE.PerspectiveCamera(36, 1, .04, 180);
const controles = new OrbitControls(camara, $('canvas'));
controles.enableDamping = true;
controles.maxPolarAngle = Math.PI * .49;
controles.minDistance = .5;
controles.maxDistance = 25;
escena.add(new THREE.HemisphereLight('#f8ece1', '#8b8098', 2.5));
const sol = new THREE.DirectionalLight('#fff0df', 3.3);
sol.position.set(5, 8, 6);
sol.castShadow = true;
sol.shadow.mapSize.set(2048, 2048);
Object.assign(sol.shadow.camera, { left: -7, right: 7, top: 7, bottom: -7, near: .1, far: 35 });
sol.shadow.bias = -.0002;
sol.shadow.normalBias = .015;
escena.add(sol, sol.target);
const relleno = new THREE.DirectionalLight('#cedcff', 1.1);
relleno.position.set(-4, 3, -5);
escena.add(relleno);
const suelo = new THREE.Mesh(new THREE.PlaneGeometry(300, 300), new THREE.MeshStandardMaterial({ color: '#b7aeb7', roughness: 1 }));
suelo.rotation.x = -Math.PI / 2;
suelo.position.y = -.012;
suelo.receiveShadow = true;
escena.add(suelo);
const cargador = new GLTFLoader();
let catalogo, actual, modelo, conductor, solicitud = 0, prueba = false, alambre = false, anterior;
const teclas = new Set(), pulsadores = new Map();
const mapa = { KeyW: 'adelante', ArrowUp: 'adelante', KeyS: 'atras', ArrowDown: 'atras', KeyA: 'izquierda', ArrowLeft: 'izquierda', KeyD: 'derecha', ArrowRight: 'derecha' };
window.flota = { escena, render, camara, controles };

function liberar(objeto) {
  const materiales = new Set(), texturas = new Set(), geometrias = new Set();
  objeto.traverse(o => { if (o.isMesh) { geometrias.add(o.geometry); for (const m of [o.material].flat()) materiales.add(m); } });
  for (const m of materiales) for (const valor of Object.values(m)) if (valor?.isTexture) texturas.add(valor);
  for (const g of geometrias) g.dispose();
  for (const t of texturas) t.dispose();
  for (const m of materiales) m.dispose();
}

function rotuloPrueba() {
  return actual?.tipo === 'remolque' ? 'Probar rodadura' : 'Probar marcha';
}

function parar() {
  prueba = false; teclas.clear(); pulsadores.clear();
  $('#probar').setAttribute('aria-pressed', 'false');
  $('#probar').textContent = rotuloPrueba();
  conductor?.entrada({ velocidad: 0, direccion: 0 });
}

function vista(nombre = 'perspectiva') {
  if (!actual) return;
  const d = actual, h = d.alto / 2, largo = d.largo;
  const s = conductor?.estado() || { x: 0, z: 0 };
  const ajustes = {
    perspectiva: [[largo * 1.15, 3.1, largo * 1.65], [0, h, 0]],
    frente: [[7.5, h, 0], [0, h, 0]], lateral: [[0, h, largo * 1.8], [0, h, 0]],
    trasera: [[-7.5, h, 0], [0, h, 0]], peaton: [[largo * 1.2, 1.6, largo * 1.6], [0, h, 0]],
    rueda: [[d.ejes[1] + .62, .9, 2.3], [d.ejes[1], d.radio_rueda, d.semivia_ruedas]],
  };
  const [pos, mira] = ajustes[nombre];
  camara.position.fromArray(pos).add(new THREE.Vector3(s.x, 0, s.z));
  controles.target.fromArray(mira).add(new THREE.Vector3(s.x, 0, s.z));
  controles.update(); document.body.dataset.vista = nombre; ajustarZoom();
}

function ajustarZoom() {
  const perspectivaAncha = document.body.dataset.vista === 'perspectiva' && camara.aspect > 1.12;
  camara.zoom = perspectivaAncha ? (catalogo?.titulo ? 1.30 : 1.24) : 1;
  camara.updateProjectionMatrix();
}

async function elegir(id) {
  const turno = ++solicitud;
  parar(); conductor = null;
  document.body.dataset.modelo = 'cargando';
  $('#estado').hidden = false;
  $('[aria-label="Elegir vehículo"]').value = id;
  document.querySelectorAll('[data-conduccion]').forEach(b => { b.disabled = true; });
  $('#estado').textContent = 'Cargando vehículo…';
  try {
    const ficha = catalogo.vehiculos.find(v => v.id === id);
    const gltf = await cargador.loadAsync(ficha.glb ?? `${id}.glb`);
    if (turno !== solicitud) { liberar(gltf.scene); return; }
    if (modelo) { escena.remove(modelo); liberar(modelo); }
    actual = ficha;
    modelo = gltf.scene;
    modelo.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; for (const m of [o.material].flat()) m.wireframe = alambre; } });
    escena.add(modelo);
    conductor = crearConductor(modelo,id);
    $('#probar').textContent = rotuloPrueba();
    $('#rapidez').max = String(Math.max(3, Math.floor(conductor.cinematica.config.velocidad_maxima * 3.6 + 1e-6)));
    $('#rapidez-texto').textContent = `${$('#rapidez').value} km/h`;
    Object.assign(window.flota, { modelo, conductor, actual, clips: gltf.animations.map(a => a.name), elegir, vista });
    $('#descargar-glb').href = ficha.glb ?? `${id}.glb`;
    $('#descargar-blend').href = ficha.blend ?? `${id}.blend`;
    $('#imagen-diseno').src = ficha.lamina ?? `referencias/${id}.png`;
    $('canvas').setAttribute('aria-label', `Modelo 3D de ${actual.nombre}`);
    $('#estado').textContent = actual.nombre;
    $('#estado').hidden = Boolean(catalogo.titulo);
    document.body.dataset.modelo = 'cargado'; document.body.dataset.vehiculo = id;
    document.querySelectorAll('[data-conduccion]').forEach(b => { b.disabled = false; });
    sol.position.set(5, 8, 6); sol.target.position.set(0, 0, 0);
    vista();
    history.replaceState(null, '', `#${id}`);
  } catch (error) { if (turno === solicitud) { $('#estado').textContent = 'No se pudo cargar. Vuelve a elegir el vehículo.'; console.error(error); } }
}

document.querySelectorAll('[data-vista]').forEach(b => b.addEventListener('click', () => vista(b.dataset.vista)));
$('#vehiculo').addEventListener('change', e => elegir(e.target.value));
$('#probar').addEventListener('click', () => {
  const nuevo = !prueba; parar(); prueba = nuevo;
  $('#probar').setAttribute('aria-pressed', String(prueba));
  $('#probar').textContent = prueba ? 'Terminar prueba' : rotuloPrueba();
});
$('#frenar').addEventListener('click', parar);
$('#reiniciar').addEventListener('click', () => {
  parar(); conductor?.teletransportar({ x: 0, z: 0, rumbo: 0 }, true);
  sol.position.set(5, 8, 6); sol.target.position.set(0, 0, 0); vista();
});
$('#malla').addEventListener('click', e => {
  alambre = !alambre; e.currentTarget.setAttribute('aria-pressed', String(alambre));
  modelo?.traverse(o => { if (o.isMesh) for (const m of [o.material].flat()) m.wireframe = alambre; });
});
$('#referencia').addEventListener('click', () => $('#diseno').showModal());
$('#cerrar-diseno').addEventListener('click', () => $('#diseno').close());
$('#rapidez').addEventListener('input', e => { $('#rapidez-texto').textContent = `${e.target.value} km/h`; });
addEventListener('keydown', e => {
  if (e.ctrlKey || e.metaKey || e.altKey || /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
  if (mapa[e.code]) { e.preventDefault(); prueba = false; $('#probar').setAttribute('aria-pressed','false'); $('#probar').textContent=rotuloPrueba(); teclas.add(e.code); }
  if (e.code === 'Space') { e.preventDefault(); parar(); }
});
addEventListener('keyup', e => { teclas.delete(e.code); });
document.querySelectorAll('[data-mando]').forEach(b => {
  b.addEventListener('pointerdown', e => {
    e.preventDefault(); prueba = false; $('#probar').setAttribute('aria-pressed','false'); $('#probar').textContent=rotuloPrueba();
    pulsadores.set(e.pointerId,b.dataset.mando); b.setPointerCapture(e.pointerId);
  });
  for (const evento of ['pointerup','pointercancel','lostpointercapture']) b.addEventListener(evento,e=>pulsadores.delete(e.pointerId));
});
addEventListener('blur',parar);
document.addEventListener('visibilitychange',()=>{anterior=undefined;if(document.hidden)parar();});
new ResizeObserver(()=>{
  const c=$('canvas');render.setSize(c.clientWidth,c.clientHeight,false);
  camara.aspect=c.clientWidth/c.clientHeight;
  camara.fov=Math.max(36,THREE.MathUtils.radToDeg(2*Math.atan(Math.tan(THREE.MathUtils.degToRad(18))/camara.aspect)));
  ajustarZoom();
}).observe($('canvas'));
render.setAnimationLoop(t=>{
  const dt=anterior===undefined?0:Math.min((t-anterior)/1000,.1);anterior=t;
  if(conductor){
    const mandos=new Set([...Array.from(teclas,c=>mapa[c]),...pulsadores.values()]);
    const c=conductor.cinematica.config;
    const velocidad=prueba?Number($('#rapidez').value)/3.6:(mandos.has('adelante')?Number($('#rapidez').value)/3.6:0)-(mandos.has('atras')?1.5:0);
    const direccion=prueba?Math.atan(conductor.cinematica.batalla/c.radio_demo):((mandos.has('izquierda')?1:0)-(mandos.has('derecha')?1:0))*c.direccion_maxima;
    const antes=conductor.estado();conductor.entrada({velocidad,direccion});const despues=conductor.actualizar(dt);
    const delta=new THREE.Vector3(despues.x-antes.x,0,despues.z-antes.z);
    camara.position.add(delta);controles.target.add(delta);sol.position.add(delta);sol.target.position.add(delta);
    $('#velocidad').textContent=`${Math.abs(despues.velocidad*3.6).toFixed(1)} km/h${despues.velocidad<-.01?' · R':''}`;
    document.body.dataset.movimiento=Math.abs(despues.velocidad)>.01?'marcha':'detenido';
    document.querySelectorAll('[data-mando]').forEach(b=>{b.dataset.activo=String(mandos.has(b.dataset.mando));});
  }
  controles.update(dt);render.render(escena,camara);
});
fetch('catalogo.json').then(r=>{if(!r.ok)throw Error('Catálogo no disponible');return r.json();}).then(datos=>{
  catalogo=datos;
  if (catalogo.vehiculos.length === 1) $('#vehiculo').hidden = true;
  if (catalogo.titulo) {
    $('header strong').textContent = catalogo.titulo;
    $('header a').hidden = true;
    document.title = catalogo.titulo + ' · Mi Ciudad';
  }
  for(const v of catalogo.vehiculos){const o=document.createElement('option');o.value=v.id;o.textContent=v.nombre;$('#vehiculo').append(o);}
  const id=location.hash.slice(1);elegir(catalogo.vehiculos.some(v=>v.id===id)?id:catalogo.vehiculos[0].id);
}).catch(error=>{$('#estado').textContent='No se pudo cargar el catálogo';console.error(error);});
