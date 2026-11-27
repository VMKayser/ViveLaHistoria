"""Revisión selectiva de GLB, con cámaras de corrección y a pie a 1,6 m.
Uso mediante ejecutar.py: revisar_exportados.py --mid=M053 --revisiones=13,14 --vistas=R0013
"""
import os,sys,json,math
import bpy
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from detalles_plaza_codex import revisar_correcciones
mid=next(a.split('=',1)[1] for a in sys.argv if a.startswith('--mid='))
nums=next((a.split('=',1)[1] for a in sys.argv if a.startswith('--revisiones=')),'')
nums=[int(n) for n in nums.split(',') if n]
m,col=iniciar('codex',mid)
ruta=os.path.join(datos.RAIZ,'web/public/models/ciudad/codex',mid+'.glb')
bpy.ops.import_scene.gltf(filepath=ruta)
for ob in list(bpy.context.scene.objects):
 if ob.type=='MESH':
  for co in list(ob.users_collection):co.objects.unlink(ob)
  col.objects.link(ob)
# Tres vistas en escorzo por cada fachada de más de 8 m.
frentes=[]
for e in m['edificios']:
 for l in lados(e['huella']):
  if l['a_calle'] and l['largo']>8:frentes.append(Fachada(None,l,altura_suelo(*l['a'])))
miradas=None
if '--encuadre-dalence' in sys.argv:
 from dalence_codex import MIRADAS_DALENCE
 miradas=MIRADAS_DALENCE
 eid={'M055':'Eae1b1b','M060':'E834ca0','M061':'E00e8b2'}[mid]
 ls=[l for e in m['edificios'] if e['id']==eid for l in lados(e['huella']) if l['calle']=='Calle Pantaleón Dalence']
 if ls:
  l=max(ls,key=lambda l:l['largo']);frentes=[Fachada(None,l,altura_suelo(*l['a']))]
if mid=='M061' and any(88<=n<=95 for n in nums):
 from ucb_dalence import huella_conjunto,huella_tramo,N
 from frentes_codex import frente_real
 from dalence_codex import MIRADAS_DALENCE
 miradas=dict(MIRADAS_DALENCE)
 from piezas_codex import recorte_estricto
 fm,_=frente_real({'huella':recorte_estricto(edificio(mid,'E00e8b2')['huella'])},None,normal=N)
 qm=fm.punto(fm.largo*.60,0)
 miradas[88]=(qm.x,qm.y,altura_suelo(qm.x,qm.y)+7.0)
 fp,_=frente_real({'huella':huella_tramo(edificio(mid,'E311863'),0,10)},None,normal=N)
 qp=fp.punto(fp.largo*.50,0)
 miradas[89]=(qp.x,qp.y,altura_suelo(qp.x,qp.y)+6.8)
 # R0093 tiene impacto en el suelo: conservar ojos y recuperar rumbo original.
 d=json.load(open(os.path.join(datos.RAIZ,'coordinacion/revisiones/R0093/revision.json')))
 p=d['escena']['camara']['lienzo'];az=math.radians(d['escena']['camara']['rumbo_grados'])
 miradas[93]=(p['x']+15*math.sin(az),p['y']+15*math.cos(az),p['z']+4.5)
 fe,_=frente_real({'huella':huella_tramo(edificio(mid,'E311863'),58,90)},None,normal=N)
 qe=fe.punto(fe.largo*.5,0);miradas[94]=(qe.x,qe.y,altura_suelo(qe.x,qe.y)+5.0)
 f,g=frente_real({'huella':huella_conjunto(edificio(mid,'E311863'))},None,normal=N)
 frentes=[f]
if mid in ('M061','M075') and 95 in nums:
 miradas={} if miradas is None else miradas
 miradas[95]=(-254,-389,67.0,14.0)
revisar_correcciones(mid,nums,frentes,miradas=miradas)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
