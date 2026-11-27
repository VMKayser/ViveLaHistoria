"""Cobertura real del suelo de P01 + BASE mediante rayos, sin terreno de fondo.

Se comprueba toda la plaza cada 25 cm, sus bordes a 2/15/30 cm y los
puntos de #23. Un techo o una copa no puede ocultar un hueco: solo se
leen caras de suelo, a menos de 1,2 m de la cota de terreno.
"""
import os, sys, json, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
from kit import datos

bpy.ops.wm.read_factory_settings(use_empty=True)
cuadra='--catedral-borrador' in sys.argv
if cuadra:
    ruta=os.path.join(datos.RAIZ,'revisiones/codex/repaso_20261113/BASE_limpia.glb')
    bpy.ops.import_scene.gltf(filepath=ruta)
else:
    for agente, mid in (('claude','BASE'), ('codex','P01')):
        bpy.ops.import_scene.gltf(filepath=os.path.join(datos.RAIZ,'web/public/models/ciudad',agente,mid+'.glb'))
vs, fs = [], []
invasiones=[]
corredores=[]
if cuadra:
    for calle in datos.calles_reales():
        radio=calle['ancho']/2-calle['vereda']
        for a,b in zip(calle['eje'],calle['eje'][1:]):
            dx,dy=b[0]-a[0],b[1]-a[1];ll=dx*dx+dy*dy
            if ll>.001:
                corredores.append((a,dx,dy,ll,radio,calle['nombre'],
                    min(a[0],b[0])-radio,max(a[0],b[0])+radio,
                    min(a[1],b[1])-radio,max(a[1],b[1])+radio))
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    if cuadra and ob.name in ('BASE_suelo_conjunto_institucional','BASE_reparacion_suelo_institucional'):
        adoquin={i for f in ob.data.polygons if ob.data.materials[f.material_index].name.split('__')[0]=='adoquin' for i in f.vertices}
        for v in ob.data.vertices:
            if v.index not in adoquin:continue
            p=ob.matrix_world@v.co
            for a,dx,dy,ll,radio,nombre,x0,x1,y0,y1 in corredores:
                if not (x0<=p.x<=x1 and y0<=p.y<=y1):continue
                t=((p.x-a[0])*dx+(p.y-a[1])*dy)/ll
                if 0<=t<=1 and abs((p.x-a[0])*dy-(p.y-a[1])*dx)/math.sqrt(ll)<radio-.001:
                    invasiones.append([round(p.x,3),round(p.y,3),nombre])
    for f in ob.data.polygons:
        rol=ob.data.materials[f.material_index].name.split('__')[0]
        if rol not in ('adoquin','vereda','calzada','cesped','piedra'): continue
        pts=[ob.matrix_world @ ob.data.vertices[i].co for i in f.vertices]
        if any(abs(p.z-datos.altura_suelo(p.x,p.y))>1.2 for p in pts):continue
        fs.append(list(range(len(vs),len(vs)+len(pts))));vs.extend(pts)
arbol=BVHTree.FromPolygons(vs,fs)
print('[suelo] BVH listo;',len(fs),'caras de suelo;',len(invasiones),'vértices nuevos en calzada',flush=True)
h=json.load(open(ruta+'.json'))['poligono'] if cuadra else datos.manzana('P01')['poligono']
cx=sum(p[0] for p in h)/len(h);cy=sum(p[1] for p in h)/len(h)
puntos=[] if cuadra else [(-131.2,-234.0),(-192.4,-145.5)]
for ix in range(math.floor(min(p[0] for p in h)*4),math.ceil(max(p[0] for p in h)*4)+1):
    for iy in range(math.floor(min(p[1] for p in h)*4),math.ceil(max(p[1] for p in h)*4)+1):
        x,y=ix/4,iy/4
        if datos._dentro(x,y,h):puntos.append((x,y))
for a,b in zip(h,h[1:]+h[:1]):
    largo=math.dist(a,b)
    if largo<.01:continue
    nx,ny=-(b[1]-a[1])/largo,(b[0]-a[0])/largo
    if (cx-a[0])*nx+(cy-a[1])*ny<0:nx,ny=-nx,-ny
    for k in range(math.ceil(largo/.1)+1):
        t=min(1,k*.1/largo)
        for d in (.02,.15,.3):
            p=(a[0]+t*(b[0]-a[0])+nx*d,a[1]+t*(b[1]-a[1])+ny*d)
            if datos._dentro(*p,h):puntos.append(p)
fallos=[]
for x,y in puntos:
    z=datos.altura_suelo(x,y)
    p,_,_,_=arbol.ray_cast(Vector((x,y,z+1.25)),Vector((0,0,-1)),2.5)
    if p is None:fallos.append([round(x,3),round(y,3)])
r={'muestras':len(puntos),'sin_suelo':len(fallos),'puntos_sin_suelo':fallos}
if cuadra:r.update(invasiones_calzada_suelo_nuevo=len(invasiones),ejemplos_calzada=invasiones[:10])
nombre='cobertura_Catedral_borrador.json' if cuadra else 'cobertura_P01.json'
ruta=os.path.join(datos.RAIZ,'revisiones/codex/repaso_20261113',nombre)
json.dump(r,open(ruta,'w'),indent=2)
print('[Catedral borrador]' if cuadra else '[P01]', 'Cobertura:',len(puntos),'muestras;',len(fallos),'sin suelo →',ruta,flush=True)
if cuadra:print('[Catedral borrador] Vértices de suelo nuevo en calzada:',len(invasiones),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(1 if fallos or invasiones else 0)
