"""Mide cruces reales del tejado de relleno con la casona M075.
Solo lectura de BASE y M075; informe propio, sin alterar modelos de Claude.
"""
import os,sys,json,hashlib
import bpy
from mathutils.bvhtree import BVHTree
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import datos
from esquina_ortiz_dalence import huella_casona
bpy.ops.wm.read_factory_settings(use_empty=True)
hashes={}
for ag,mid in (('claude','BASE'),('codex','M075')):
    ruta=os.path.join(datos.RAIZ,'web/public/models/ciudad',ag,mid+'.glb')
    hashes[mid]=hashlib.sha256(open(ruta,'rb').read()).hexdigest()
    bpy.ops.import_scene.gltf(filepath=ruta)
    assert hashlib.sha256(open(ruta,'rb').read()).hexdigest()==hashes[mid],'El modelo cambió durante la lectura'
base=bpy.data.objects['BASE_relleno'];casa=bpy.data.objects['Ea7714b']
h=huella_casona();x0=min(p[0] for p in h)-1;x1=max(p[0] for p in h)+1;y0=min(p[1] for p in h)-1;y1=max(p[1] for p in h)+1
roles={i for i,m in enumerate(base.data.materials) if m.name.split('__')[0]=='teja'}
vs=[base.matrix_world@v.co for v in base.data.vertices];fs=[]
for f in base.data.polygons:
    if f.material_index not in roles:continue
    p=[vs[i] for i in f.vertices]
    if max(v.x for v in p)<x0 or min(v.x for v in p)>x1 or max(v.y for v in p)<y0 or min(v.y for v in p)>y1:continue
    fs.append(list(f.vertices))
bs=BVHTree.FromPolygons(vs,fs)
cv=[casa.matrix_world@v.co for v in casa.data.vertices];cf=[list(f.vertices) for f in casa.data.polygons]
cs=BVHTree.FromPolygons(cv,cf)
cruces=[]
for origen,vertices,caras,destino in (('M075',cv,cf,bs),('BASE',vs,fs,cs)):
    for f in caras:
        for ia,ib in zip(f,f[1:]+f[:1]):
            a,b=vertices[ia],vertices[ib];d=b-a
            if d.length<.025:continue
            u=d.normalized();p,n,indice,dist=destino.ray_cast(a+u*.01,u,d.length-.02)
            if p is not None:
                xyz=[round(v,3) for v in p]
                if xyz not in [r['punto'] for r in cruces]:cruces.append({'arista_de':origen,'punto':xyz})
r={'modelos_sha256':hashes,'huella_M075':h,'caras_teja_relleno_cercanas':len(fs),'cruces_superficies':len(cruces),'ejemplos':cruces[:100]}
ruta=os.path.join(datos.RAIZ,'revisiones/codex/M075/encuentro_BASE.json')
json.dump(r,open(ruta,'w'),indent=2)
print('[M075/BASE]',len(fs),'caras de tejado próximas;',len(cruces),'cruces reales →',ruta,flush=True)
print('[M075/BASE] Ejemplos:',cruces[:3],flush=True)
if '--exigir-libre' in sys.argv and cruces:raise SystemExit(1)
