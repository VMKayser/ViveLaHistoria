"""Recorrido de verificación: dos vistas a 1,6 m por manzana exportada.
Una desde la vereda opuesta para el conjunto y otra en escorzo desde la
propia. Carga los GLB de ambos agentes como contexto, sin escribirlos.
"""
import os,sys,math,json,glob,hashlib,time
import bpy
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from kit import salida
from piezas_codex import recorte_estricto
args=sys.argv
seleccion=next((a.split('=',1)[1].split(',') for a in args if a.startswith('--manzanas=')),None)
escena=os.path.join(datos.RAIZ,'revisiones/codex/recorrido/escena.blend')
if '--cargar-escena' in args:
 esperado=json.load(open(escena+'.json'))
 for mid,h in esperado.items():
  ruta=os.path.join(datos.RAIZ,'web/public/models/ciudad/codex',mid+'.glb')
  assert hashlib.sha256(open(ruta,'rb').read()).hexdigest()==h,('Caché de escena desactualizada',mid)
 bpy.ops.wm.open_mainfile(filepath=escena)
else:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 for agente in ('claude','codex'):
  for ruta in sorted(glob.glob(os.path.join(datos.RAIZ,'web/public/models/ciudad',agente,'*.glb'))):
   bpy.ops.import_scene.gltf(filepath=ruta)
 # El visor carga el terreno del lienzo además de BASE. Sin él los
 # patios interiores se ven azules aunque en la app sí tienen suelo.
 anteriores=set(bpy.data.objects)
 bpy.ops.import_scene.gltf(filepath=os.path.join(datos.RAIZ,'web/public/mapa/lienzo.glb'))
 for ob in set(bpy.data.objects)-anteriores:
  if ob.type=='MESH' and ob.name=='TERRAIN':
   ob.location.z-=.35
   ob.data.materials.clear();ob.data.materials.append(material('calzada','#cbb48e'))
  else:bpy.data.objects.remove(ob,do_unlink=True)
 salida._luz_y_mundo()
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=4
sc.cycles.use_denoising=True;sc.render.use_persistent_data=True
sc.render.threads_mode='FIXED';sc.render.threads=8
sc.render.resolution_x=800;sc.render.resolution_y=600;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='JPEG'
bpy.data.objects['sol'].rotation_euler=(math.radians(40),0,math.radians(145))
def calle_real_cercana(x,y):
    mejor=None
    for c in datos.calles_reales():
        for a,b in zip(c['eje'],c['eje'][1:]):
            distancia,q=datos._dist_seg(x,y,a,b)
            if mejor is None or distancia<mejor[0]:mejor=(distancia,q,c)
    return mejor
def vereda_real(x,y,opuesta=False):
    distancia,q,calle=calle_real_cercana(x,y)
    dx,dy=q[0]-x,q[1]-y;L=math.hypot(dx,dy) or 1
    signo=1 if opuesta else -1
    d=calle['ancho']/2-calle['vereda']*.5
    return q[0]+signo*dx/L*d,q[1]+signo*dy/L*d

camaras=[]
man=json.load(open(os.path.join(datos.RAIZ,'web/public/models/ciudad/codex/manifiesto.json')))
for mid in man:
 if seleccion and mid not in seleccion:continue
 m=manzana(mid);datos.verificar_dueno('codex',mid)
 if mid=='M063':
  # Cuerpo posterior sin frente público propio: el acceso del conjunto está
  # en E02ae75/M061. Se revisa desde su calle y se añade el tejado en oblicuo.
  em=edificio('M061','E02ae75');l=lados(em['huella'])[5];f=Fachada(None,l,0)
  for j,t in enumerate((.25,.7)):
   q=f.punto(f.largo*t,0);px,py=vereda_real(q.x,q.y,opuesta=True)
   camaras.append((mid,f'entorno_museo_{j}',(px,py,altura_suelo(px,py)+1.6),
                   (q.x,q.y,altura_suelo(q.x,q.y)+3)))
  cx,cy=m['centro'];z=altura_suelo(cx,cy)
  camaras.append((mid,'cubierta_posterior',(cx-18,cy-15,z+28),(cx,cy,z+8.6)))
  continue
 if mid=='P01':
  h=recorte_estricto(m['poligono']);ls=lados(h)
  mejores=sorted((l for l in ls if l['largo']>10),key=lambda l:l['largo'],reverse=True)[:2]
  for j,l in enumerate(mejores):
   f=Fachada(None,l,0);p=f.punto(f.largo*.2,0,-.8);q=f.punto(f.largo*.5,0,-3)
   camaras.append((mid,f'borde_{j}',(p.x,p.y,altura_suelo(p.x,p.y)+1.6),(q.x,q.y,altura_suelo(q.x,q.y)+.2)))
  # #23: revisar expresamente la cuña SE que el recorte anterior quitaba.
  for j,(p,q) in enumerate((((-131.2,-234.0),(-115,-212)),
                            ((-113,-204),(-138,-241)))):
   camaras.append((mid,f'borde_SE_{j}',(*p,altura_suelo(*p)+1.6),
                    (*q,altura_suelo(*q)+.2)))
  continue
 ls=[dict(l,area=e['area_m2']) for e in m.get('edificios',[]) for l in lados(e['huella']) if l['a_calle'] and l['largo']>1.25]
 if not ls:
  ls=[dict(l,area=e['area_m2']) for e in m.get('edificios',[]) for l in lados(e['huella']) if l['largo']>1.25]
  l=min(ls,key=lambda l:datos.calle_cercana((l['a'][0]+l['b'][0])/2,(l['a'][1]+l['b'][1])/2)[0])
 else:l=max(ls,key=lambda l:l['largo'])
 f=Fachada(None,l,0)
 centro=f.punto(f.largo/2,0)
 distancia,_,calle=calle_real_cercana(centro.x,centro.y)
 interior=distancia>calle['ancho']/2+3.5
 if interior:
  # Las huellas interiores no se ven desde un eje de calle lejano.
  p=f.punto(f.largo/2,0,min(7,max(3,f.largo*.6)));px,py=p.x,p.y
 else:px,py=vereda_real(centro.x,centro.y,opuesta=True)
 if mid=='M070':
  # El patio es estrecho; el punto a siete metros caía en la casa opuesta.
  p=f.punto(f.largo/2,0,1.4);px,py=p.x,p.y
 mirar_alto=2.2 if interior and l['area']<65 else 3.0
 camaras.append((mid,'frente_pie',(px,py,altura_suelo(px,py)+1.6),
                  (centro.x,centro.y,altura_suelo(centro.x,centro.y)+mirar_alto)))
 if mid=='M070':
  p=f.punto(f.largo*.75,0,1.4);q=f.punto(f.largo*.75,0)
  camaras[-1]=(mid,'frente_pie',(p.x,p.y,altura_suelo(p.x,p.y)+1.6),
                       (q.x,q.y,altura_suelo(q.x,q.y)+1.7))
 if mid=='M058':
  # El frente documentado USFX es una huella propia; la mayor arista del
  # lienzo pertenece al interior y su vista opuesta queda dentro del vecino.
  r=json.load(open(os.path.join(datos.RAIZ,'coordinacion/revisiones/R0021/revision.json')))
  p=r['escena']['camara']['lienzo'];q=r['escena']['centro']
  if not q:
   az=math.radians(r['escena']['camara']['rumbo_grados']);inc=math.radians(r['escena']['camara']['inclinacion_grados'])
   q={'x':p['x']+20*math.sin(az)*math.cos(inc),'y':p['y']+20*math.cos(az)*math.cos(inc),'z':p['z']+20*math.sin(inc)}
  camaras[-1]=(mid,'frente_pie',(p['x'],p['y'],altura_suelo(p['x'],p['y'])+1.6),
                          (q['x'],q['y'],q['z']))
 ss=min(10,f.largo*.2) if mid=='M061' else min(1.6,f.largo*.25)
 inicio=f.punto(ss,0)
 if interior:
  p=f.punto(ss,0,1.4);px,py=p.x,p.y
 else:px,py=vereda_real(inicio.x,inicio.y)
 if mid=='M061':
  # Junto a Nicolás Ortiz el eje más próximo cambia en la esquina; el
  # escorzo se coloca sobre la normal del lado real, fuera de la carpintería.
  p=f.punto(ss,0,1.1);px,py=p.x,p.y
 q=f.punto(min(f.largo-.2,ss+8),0,.02)
 camaras.append((mid,'escorzo_pie',(px,py,altura_suelo(px,py)+1.6),
                  (q.x,q.y,altura_suelo(q.x,q.y)+2.2)))
if '--detalles' in args:
 if not seleccion or 'M055' in seleccion:
  camaras.append(('M055','campanas_apoyadas',(-190,-319,altura_suelo(-190,-319)+1.6),
                  (-206,-303,altura_suelo(-206,-303)+20)))
 if not seleccion or 'M061' in seleccion:
  e=edificio('M061','E311863');f=Fachada(None,lados(e['huella'])[8],0)
  p=f.punto(8,0,10.6);q=f.punto(8,0)
  camaras.append(('M061','guardapolvos_y_acometida',(p.x,p.y,altura_suelo(p.x,p.y)+1.6),
                  (q.x,q.y,altura_suelo(q.x,q.y)+6.1)))
if '--nave' in args:
 from nave_arenales import huella_nave
 from frentes_codex import frente_real
 from detalles_plaza_codex import punto_encadenado
 f,g=frente_real({'huella':huella_nave()},None,normal=(.637,.771))
 for nombre,ss,dist,qs,qh in (('nave_130427',f.largo*.82,10.0,f.largo*.20,5.4),
                             ('nave_130431',f.largo*.40,10.0,f.largo*.07,5.5),
                             ('nave_inicio',1.0,.85,f.largo*.55,3.2),
                             ('nave_fin',f.largo-1,.85,f.largo*.50,3.2)):
  p=punto_encadenado(g,ss,0,dist);q=punto_encadenado(g,qs,qh,0)
  camaras.append(('M037',nombre,(p.x,p.y,altura_suelo(p.x,p.y)+1.6),tuple(q)))
if '--junin-oeste' in args:
 from mobiliario_junin_oeste import posicion
 for mid,lado,x0,x1 in (('M037',1,-336,-327),('M027',-1,-313,-314)):
  if seleccion and mid not in seleccion:continue
  p,_,_=posicion(x0,-lado);q,_,n=posicion(x1,lado);q+=n*.85
  camaras.append((mid,'Junin_frente',(p.x,p.y,altura_suelo(p.x,p.y)+1.6),
                 (q.x,q.y,altura_suelo(q.x,q.y)+4.0)))
 for mid,lado,x0,x1 in (('M037',1,-340,-317),('M027',-1,-317.3,-302)):
  if seleccion and mid not in seleccion:continue
  p,_,_=posicion(x0,lado);q,_,n=posicion(x1,lado);q+=n*.85
  camaras.append((mid,'Junin_escorzo',(p.x,p.y,altura_suelo(p.x,p.y)+1.6),
                 (q.x,q.y,altura_suelo(q.x,q.y)+3.0)))
 for mid,lado,xs in (('M037',1,(-354,-314)),('M027',-1,(-320,))):
  if seleccion and mid not in seleccion:continue
  for j,x in enumerate(xs):
   p,_,_=posicion(x+3,-lado);q,_,_=posicion(x,lado)
   camaras.append((mid,f'Junin_poste_{j}',(p.x,p.y,altura_suelo(p.x,p.y)+1.6),
                  (q.x,q.y,altura_suelo(q.x,q.y)+4.5)))
carpeta_recorrido=os.path.join(datos.RAIZ,'revisiones/codex/recorrido')
os.makedirs(carpeta_recorrido,exist_ok=True)
vistas=next((a.split('=',1)[1].split(',') for a in args if a.startswith('--vistas=')),None)
if vistas:camaras=[c for c in camaras if c[1] in vistas]
hashes={mid:hashlib.sha256(open(os.path.join(datos.RAIZ,'web/public/models/ciudad/codex',mid+'.glb'),'rb').read()).hexdigest() for mid in man}
registro=os.path.join(carpeta_recorrido,'camaras.json');inicio=time.time()
fichas=[{'manzana':mid,'nombre':nombre,'posicion':p,'mirar':q,
         'altura_sobre_terreno_m':round(p[2]-altura_suelo(p[0],p[1]),3),
         'inicio_revision_unix':inicio,'modelo_sha256':hashes[mid],
         'contexto_codex_sha256':hashes} for mid,nombre,p,q in camaras]
if '--actualizar' in args:
 assert seleccion and os.path.exists(registro),'Actualizar requiere una selección y un recorrido previo'
 anterior=json.load(open(registro));inicio_anterior=os.path.getmtime(registro)
 claves_nuevas={(f['manzana'],f['nombre']) for f in fichas}
 conservar=[]
 for ficha in anterior['camaras']:
  if (ficha['manzana'],ficha['nombre']) in claves_nuevas:continue
  ficha.setdefault('inicio_revision_unix',inicio_anterior)
  ficha.setdefault('modelo_sha256',anterior['modelos_sha256'][ficha['manzana']])
  ficha.setdefault('contexto_codex_sha256',anterior['modelos_sha256'])
  conservar.append(ficha)
 fichas=sorted(conservar+fichas,key=lambda f:(list(man).index(f['manzana']),f['nombre']))
with open(registro,'w') as fh:
 json.dump({'altura_ojos_sobre_terreno_m':1.6,'modelos_sha256':hashes,
            'validacion':'Versión actual del modelo principal; contexto de cada toma registrado',
            'camaras':fichas},fh,indent=2)
if '--guardar-escena' in args:
 json.dump(hashes,open(escena+'.json','w'),indent=2)
 bpy.ops.wm.save_as_mainfile(filepath=escena)
for mid,nombre,p,q in camaras:
 carpeta=os.path.join(datos.RAIZ,'revisiones/codex/recorrido',mid);os.makedirs(carpeta,exist_ok=True)
 lente=13 if mid=='M070' and nombre=='frente_pie' else 20
 ob=salida.camara(p,q,lente=lente);sc.render.filepath=os.path.join(carpeta,nombre+'.jpg')
 bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(ob,do_unlink=True)
 print('[recorrido]',mid,nombre,flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
