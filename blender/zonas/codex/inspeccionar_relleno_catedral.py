"""Localiza relleno de BASE delante de las fachadas fotografiadas de M055.
Solo lectura; no altera ni exporta BASE ni los modelos de Claude.
"""
import os,sys,json,math
import bpy
from mathutils.bvhtree import BVHTree
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
from kit import *
bpy.ops.wm.read_factory_settings(use_empty=True)
base=next((a.split('=',1)[1] for a in sys.argv if a.startswith('--base=')),None)
bpy.ops.import_scene.gltf(filepath=base or os.path.join(datos.RAIZ,'web/public/models/ciudad/claude/BASE.glb'))
ob=bpy.data.objects.get('BASE_relleno')
vs=[ob.matrix_world@v.co for v in ob.data.vertices]
fs=[list(f.vertices) for f in ob.data.polygons]
bvh=BVHTree.FromPolygons(vs,fs)
resultados=[]
for eid,indice in (('E2c6601',0),('E03fe1d',2),('E03fe1d',0)):
    e=edificio('M055',eid);f=Fachada(None,lados(e['huella'])[indice],max(altura_suelo(*p) for p in e['huella']))
    for k in range(math.ceil(f.largo*2)):
        s=min(f.largo-.1,k*.5+.1)
        for hh in (1,3,5,7,9):
            p=f.punto(s,hh,14);q=f.punto(s,hh,.01);delta=q-p
            hit,_,_,dist=bvh.ray_cast(p,delta.normalized(),delta.length)
            if hit is not None:
                resultados.append({'fachada':eid,'lado':indice,'s':round(s,2),'altura':hh,
                    'relleno':[round(v,3) for v in hit],'distancia_a_fachada':round(14-dist,3)})
nombre='relleno_frente_catedral_borrador.json' if base else 'relleno_frente_catedral.json'
ruta=os.path.join(datos.RAIZ,'revisiones/codex/repaso_20261113',nombre)
json.dump(resultados,open(ruta,'w'),indent=2)
print('[Catedral] Rayos que chocan con relleno antes de la fachada:',len(resultados),flush=True)
if resultados:print(resultados[:5],flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(1 if '--exigir-libre' in sys.argv and resultados else 0)
