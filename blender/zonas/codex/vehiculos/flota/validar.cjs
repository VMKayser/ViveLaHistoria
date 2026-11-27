/* Valida los archivos finales, los pivotes a escala y el adaptador con cada rig. */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {createRequire}=require('node:module');
const {pathToFileURL}=require('node:url');
const raiz=path.resolve(__dirname,'../../../../..');
const requireWeb=createRequire(path.join(raiz,'web/package.json'));
const validator=requireWeb('gltf-validator');
const THREE=requireWeb('three');
const salida=path.join(raiz,'web/public/models/ciudad/codex/vehiculos/flota');
const disenos=JSON.parse(fs.readFileSync(path.join(__dirname,'disenos.json')));
const config=JSON.parse(fs.readFileSync(path.join(__dirname,'configuracion.json')));
const revision=path.join(raiz,'revisiones/codex/flota');

async function main(){
 const {crearConductor}=await import(pathToFileURL(path.join(__dirname,'controlador.mjs')));
 const reportes=[];
 const elegidos=process.argv.slice(2);
 for(const [id,entrada] of Object.entries(disenos).filter(([id])=>!elegidos.length||elegidos.includes(id))){
  const d=entrada.datos ? require(path.join(__dirname,entrada.datos)) : entrada;
  const bytes=fs.readFileSync(path.join(salida,id+'.glb'));
  assert.equal(bytes.readUInt32LE(0),0x46546c67);assert.equal(bytes.readUInt32LE(8),bytes.length);
  const gltf=JSON.parse(bytes.toString('utf8',20,20+bytes.readUInt32LE(12)));
  const binario=28+bytes.readUInt32LE(12);
  function valores(indice,n){
   const a=gltf.accessors[indice],v=gltf.bufferViews[a.bufferView];
   assert.equal(a.componentType,5126);
   return Array.from({length:a.count},(_,i)=>Array.from({length:n},(_,j)=>bytes.readFloatLE(binario+(v.byteOffset||0)+(a.byteOffset||0)+i*(v.byteStride||n*4)+j*4)));
  }
  const ni=gltf.nodes.findIndex(n=>n.name===id);assert(ni>=0,id+': raíz');
  const c=gltf.nodes[ni].extras.movimiento;
  assert(Math.abs(c.radio_rueda-d.radio_rueda)<1e-8);assert.equal(c.eje_delantero,d.ejes[1]);
  assert.equal(gltf.cameras?.length||0,0);assert(!gltf.nodes.some(n=>/ESTUDIO|Principal|Recorte/.test(n.name)));
  assert(gltf.images?.some(i=>i.bufferView!==undefined),'Textura empaquetada');
  assert.equal(gltf.materials.filter(m=>m.normalTexture).length,1,'Solo la goma tiene normal');
  const ruedas=['trasera_derecha','trasera_izquierda','delantera_derecha','delantera_izquierda'].map(n=>'rueda_'+n);
  for(const lado of ['derecha','izquierda']){
   const direccion=gltf.nodes.find(n=>n.name==='direccion_delantera_'+lado);
   assert(direccion?.children.includes(gltf.nodes.findIndex(n=>n.name==='rueda_delantera_'+lado)));
  }
  for(const nombre of ['rodar_adelante','rodar_atras']){
   const clip=gltf.animations?.find(a=>a.name===nombre);assert(clip,id+': '+nombre);
   assert.equal(clip.channels.length,4);
   for(const rueda of ruedas){
    const canal=clip.channels.find(c=>gltf.nodes[c.target.node].name===rueda&&c.target.path==='rotation');assert(canal);
    const sampler=clip.samplers[canal.sampler],qs=valores(sampler.output,4),tiempos=valores(sampler.input,1);
    assert(Math.abs(tiempos.at(-1)[0]-tiempos[0][0]-1)<1e-6);
    let giro=0;
    for(let i=1;i<qs.length;i++){
     const a=qs[i-1],b=qs[i];const z=b[2]*a[3]-b[3]*a[2]-b[0]*a[1]+b[1]*a[0];
     const w=b[0]*a[0]+b[1]*a[1]+b[2]*a[2]+b[3]*a[3];
     let delta=2*Math.atan2(z,w);if(delta>Math.PI)delta-=2*Math.PI;if(delta<-Math.PI)delta+=2*Math.PI;giro+=delta;
    }
    assert(Math.abs(giro-(nombre==='rodar_adelante'?-1:1)*2*Math.PI)<1e-5,id+': giro completo');
   }
  }
  // Reconstruir la jerarquía que consume Three, con las transformaciones del GLB.
  const nodos=gltf.nodes.map(n=>{
   const o=new THREE.Object3D();o.name=n.name;o.userData=n.extras||{};
   if(n.matrix){o.matrix.fromArray(n.matrix);o.matrix.decompose(o.position,o.quaternion,o.scale);}
   else {if(n.translation)o.position.fromArray(n.translation);if(n.rotation)o.quaternion.fromArray(n.rotation);if(n.scale)o.scale.fromArray(n.scale);}
   return o;
  });
  gltf.nodes.forEach((n,i)=>(n.children||[]).forEach(j=>nodos[i].add(nodos[j])));
  const modelo=new THREE.Group();gltf.scenes[gltf.scene||0].nodes.forEach(i=>modelo.add(nodos[i]));modelo.updateMatrixWorld(true);
  const conductor=crearConductor(modelo,id);
  for(const nombre of ruedas){
   const p=modelo.getObjectByName(nombre).getWorldPosition(new THREE.Vector3());
   const x=nombre.includes('delantera')?d.ejes[1]:d.ejes[0];const z=nombre.endsWith('derecha')?d.semivia_ruedas:-d.semivia_ruedas;
   assert(p.distanceTo(new THREE.Vector3(x,d.radio_rueda,z))<1e-6,id+': pivote '+nombre);
  }
  conductor.avanzarDistancia(2*Math.PI*d.radio_rueda);
  for(const rueda of ruedas){const q=modelo.getObjectByName(rueda).quaternion;assert(Math.abs(q.w)>1-1e-8);}
  const curvatura=Math.min(.1,.90*Math.tan(c.direccion_maxima)/(c.eje_delantero-c.eje_trasero));
  const s=conductor.avanzarDistancia(2,curvatura);
  if(c.tipo_direccion==='tornamesa'){
   const eje=modelo.getObjectByName('tornamesa_delantera');
   assert(eje && modelo.getObjectByName('enganche_frontal')?.parent===eje);
   assert.equal(s.ruedas.rueda_delantera_derecha.direccion,s.ruedas.rueda_delantera_izquierda.direccion);
   assert(Math.abs(eje.rotation.y-s.direccion)<1e-7);
   const a=modelo.getObjectByName('rueda_delantera_derecha').getWorldPosition(new THREE.Vector3());
   const b=modelo.getObjectByName('rueda_delantera_izquierda').getWorldPosition(new THREE.Vector3());
   assert(Math.abs(a.distanceTo(b)-2*d.semivia_ruedas)<1e-6,id+': vía al girar con la tornamesa');
  } else assert.notEqual(s.ruedas.rueda_delantera_derecha.direccion,s.ruedas.rueda_delantera_izquierda.direccion);
  conductor.teletransportar({x:0,z:0,rumbo:0},true);
  conductor.entrada({velocidad:-1,direccion:0});for(let i=0;i<120;i++)conductor.actualizar(1/60);
  assert(conductor.estado().x<0);assert(conductor.estado().ruedas.rueda_trasera_derecha.rodadura>0);
  const informe=await validator.validateBytes(new Uint8Array(bytes),{uri:id+'.glb'});
  fs.mkdirSync(path.join(revision,id),{recursive:true});
  fs.writeFileSync(path.join(revision,id,'validacion_gltf.json'),JSON.stringify(informe,null,2));
  assert.equal(informe.issues.numErrors,0,JSON.stringify(informe.issues.messages));
  assert.equal(informe.issues.numWarnings,0,JSON.stringify(informe.issues.messages));
  const triangulos=gltf.meshes.reduce((s,m)=>s+m.primitives.reduce((n,p)=>n+gltf.accessors[p.indices].count/3,0),0);
  assert(triangulos<config.presupuesto_triangulos);
  const reporte={id,bytes:bytes.length,triangulos,mallas:gltf.meshes.length,errores:informe.issues.numErrors,advertencias:informe.issues.numWarnings,pivotes:4,clips:2,recta_curva_reversa:true};
  reportes.push(reporte);console.log(JSON.stringify(reporte));
 }
 fs.writeFileSync(path.join(revision,elegidos.length?'validacion_parcial.json':'validacion_flota.json'),JSON.stringify(reportes,null,2)+'\n');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
