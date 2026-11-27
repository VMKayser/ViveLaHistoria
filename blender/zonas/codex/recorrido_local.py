"""Repite solo las vistas de una manzana con contexto cercano, sin cargar la ciudad.
Uso mediante ejecutar.py: recorrido_local.py --mid=M061
Conserva ojos, mirada y registro histórico de las demás manzanas.
"""
import os,sys,json,time,hashlib
from pathlib import Path
import bpy
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from kit import salida
from contexto_codex import instalar_contexto
mid=next(a.split('=',1)[1] for a in sys.argv if a.startswith('--mid='))
raiz=Path(datos.RAIZ);carpeta=raiz/'revisiones/codex/recorrido';registro=carpeta/'camaras.json'
meta=json.loads(registro.read_text());camaras=[c for c in meta['camaras'] if c['manzana']==mid]
assert camaras,'No hay cámaras registradas de '+mid
asignada=datos.manzana(mid)
es_interior=bool(asignada.get('edificios')) and not any(l['a_calle'] for e in asignada['edificios'] for l in lados(e['huella']))
es_generica='from generica import construir' in (raiz/'blender/zonas/codex'/(mid+'.py')).read_text()
if es_interior or es_generica:
    # Un lote interior no tiene una vereda propia. Las cámaras antiguas
    # junto a su huella acabaron dentro del relleno posterior de la BASE.
    puntos=[p for e in asignada['edificios'] for p in e['huella']]
    cx=sum(p[0] for p in puntos)/len(puntos);cy=sum(p[1] for p in puntos)/len(puntos)
    candidatos=[]
    for calle in datos.calles_reales():
        for a,b in zip(calle['eje'],calle['eje'][1:]):
            if __import__('math').dist(a,b)<1:continue
            dist,q=datos._dist_seg(cx,cy,a,b);candidatos.append((dist,calle,a,b,q))
    _,calle,a,b,q=min(candidatos,key=lambda c:c[0])
    L=__import__('math').dist(a,b);u=((b[0]-a[0])/L,(b[1]-a[1])/L)
    signo=1 if (cx-q[0])*(-u[1])+(cy-q[1])*u[0]>0 else -1
    n=(-u[1]*signo,u[0]*signo)
    ancho=calle['ancho']/2;vereda=calle.get('vereda',2.2)
    for c in camaras:
        despl=-4 if c['nombre']=='escorzo_pie' else 4
        t=max(.5,min(L-.5,(q[0]-a[0])*u[0]+(q[1]-a[1])*u[1]+despl))
        lado_vereda=-1 if c['nombre']=='frente_pie' else 1
        x=a[0]+t*u[0]+lado_vereda*n[0]*(ancho-vereda*.5);y=a[1]+t*u[1]+lado_vereda*n[1]*(ancho-vereda*.5)
        tx=q[0]+n[0]*(ancho+.1);ty=q[1]+n[1]*(ancho+.1)
        c.update(posicion=[x,y,altura_suelo(x,y)+1.6],mirar=[tx,ty,altura_suelo(tx,ty)+3.2],
                 altura_sobre_terreno_m=1.6,lote_interior=es_interior,
                 nota='Vista desde '+calle['nombre']+('; lote interior oculto por el frente vecino, sin acceso peatonal propio.' if es_interior else '; vereda actual tras ensanche #31.'))
if mid=='M075':
    from esquina_ortiz_dalence import huella_casona
    from frentes_codex import frente_real
    from detalles_plaza_codex import punto_encadenado
    f,g=frente_real({'huella':huella_casona()},None,0,normal=(-.76,.65))
    for c in camaras:
        ss,dist,qs=(f.largo*.50,10.4,f.largo*.50) if c['nombre']=='frente_pie' else (.6,.95,f.largo-.5)
        p=punto_encadenado(g,ss,0,dist);q=punto_encadenado(g,qs,0,0)
        c['posicion']=[p.x,p.y,altura_suelo(p.x,p.y)+1.6]
        c['mirar']=[q.x,q.y,altura_suelo(q.x,q.y)+(4.5 if c['nombre']=='frente_pie' else 3.5)]
        c['altura_sobre_terreno_m']=1.6
m,col=iniciar('codex',mid);ruta=Path(salida.dir_modelos('codex'))/(mid+'.glb')
bpy.ops.import_scene.gltf(filepath=str(ruta))
for ob in list(bpy.context.scene.objects):
    for co in list(ob.users_collection):co.objects.unlink(ob)
    col.objects.link(ob)
instalar_contexto([p for c in camaras for p in (c['posicion'],c['mirar'])],margen=25)
salida._luz_y_mundo();salida.contexto(mid)
from render_codex import configurar
sc=bpy.context.scene;configurar(sc,hilos=int(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--hilos=')),2)))
sc.render.resolution_x=800;sc.render.resolution_y=600;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='JPEG'
sha=hashlib.sha256(ruta.read_bytes()).hexdigest();inicio=time.time()
# Contexto preciso de esta tanda; no se atribuye este contexto a tomas históricas.
contexto={str(p.relative_to(raiz)):hashlib.sha256(p.read_bytes()).hexdigest()
          for p in (Path(p) for p in json.loads(bpy.data.collections['contexto_local'].get('archivos_glb_json','[]')))}
for c in camaras:
    assert abs(c['posicion'][2]-altura_suelo(*c['posicion'][:2])-1.6)<.02,(mid,c['nombre'],'Altura de ojos')
    cam=salida.camara(c['posicion'],c['mirar'],lente=20)
    dest=carpeta/mid/(c['nombre']+'.jpg');dest.parent.mkdir(exist_ok=True)
    sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam,do_unlink=True)
    c.update(modelo_sha256=sha,inicio_revision_unix=inicio,contexto_local_sha256=contexto)
    c.pop('contexto_codex_sha256',None)
    print('[recorrido local]',mid,c['nombre'],flush=True)
meta['modelos_sha256'][mid]=sha
meta['validacion']='Modelo principal por hash; contexto de cada toma registrado por separado'
temporal=registro.with_suffix('.tmp');temporal.write_text(json.dumps(meta,indent=2));temporal.replace(registro)
