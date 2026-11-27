"""Cierra las rendijas detectadas en la copia privada de BASE.

Resta las caras de suelo existentes a cajas pequeñas alrededor de los
rayos fallidos. Añade únicamente el hueco real, sin superponer parches.
Divide adoquín/asfalto por los corredores finitos de calzada. No publica.
"""
import os,sys,json,math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from pavimentos_codex import _partir,_area
base=os.path.join(datos.RAIZ,'revisiones/codex/repaso_20261113')
ruta=os.path.join(base,'BASE_limpia.glb');meta=json.load(open(ruta+'.json'))
informe=json.load(open(os.path.join(base,'cobertura_Catedral_borrador.json')))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=ruta)
if '--ajustar-roles' in sys.argv:
    ob=bpy.data.objects['BASE_reparacion_suelo_institucional']
    asfalto=next(i for i,m in enumerate(ob.data.materials) if m.name.split('__')[0]=='calzada')
    corregidas=0
    for f in ob.data.polygons:
        if ob.data.materials[f.material_index].name.split('__')[0]!='adoquin':continue
        extremos=False
        for i in f.vertices:
            p=ob.matrix_world@ob.data.vertices[i].co
            for calle in datos.calles_reales():
                radio=calle['ancho']/2-calle['vereda']
                for a,b in zip(calle['eje'],calle['eje'][1:]):
                    dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
                    if L<.01:continue
                    s=((p.x-a[0])*dx+(p.y-a[1])*dy)/L
                    d=abs((p.x-a[0])*dy-(p.y-a[1])*dx)/L
                    if 0<=s<=L and d<radio-.001:
                        assert min(s,L-s)<.04,'Adoquín dentro de un tramo, no en su extremo'
                        extremos=True
        if extremos:f.material_index=asfalto;corregidas+=1
    temporal=os.path.join(base,'BASE_limpia_roles.glb')
    bpy.ops.export_scene.gltf(filepath=temporal,export_format='GLB',export_yup=True,
                             export_apply=True,export_normals=True,export_materials='EXPORT')
    os.replace(temporal,ruta)
    meta['reparacion_roles_extremos_calzada']=corregidas
    json.dump(meta,open(ruta+'.json','w'),indent=2,ensure_ascii=False)
    print('[BASE borrador] Caras de unión a calzada reclasificadas:',corregidas,flush=True)
    sys.stdout.flush();sys.stderr.flush();os._exit(0)
vs,fs,triangulos=[],[],[]
for ob in bpy.data.objects:
    if ob.type!='MESH':continue
    for f in ob.data.polygons:
        if ob.data.materials[f.material_index].name.split('__')[0] not in ('calzada','vereda','adoquin','piedra'):continue
        pts=[ob.matrix_world@ob.data.vertices[i].co for i in f.vertices]
        if any(abs(p.z-altura_suelo(p.x,p.y))>1.2 for p in pts):continue
        if abs((pts[1]-pts[0]).cross(pts[2]-pts[0]).z)<1e-9:continue
        fs.append(list(range(len(vs),len(vs)+len(pts))));vs.extend(pts)
        t=[tuple(p[:2]) for p in pts]
        triangulos.append((datos.orientar_ccw(t),(min(p[0] for p in t),min(p[1] for p in t),max(p[0] for p in t),max(p[1] for p in t))))
arbol=BVHTree.FromPolygons(vs,fs)


def interseccion(p,recorte):
    for a,b in zip(recorte,recorte[1:]+recorte[:1]):
        if len(p)<3:return []
        p,_=_partir(p,lambda q:(b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0]))
    return p


def diferencia(p,recorte):
    comun=interseccion(p,recorte)
    if len(comun)<3 or _area(comun)<1e-9:return [p]
    fuera=[]
    for a,b in zip(recorte,recorte[1:]+recorte[:1]):
        if len(p)<3:break
        p,exterior=_partir(p,lambda q:(b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0]))
        if len(exterior)>=3 and _area(exterior)>1e-8:fuera.append(exterior)
    return fuera


def choca(a,b):return not (a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1])


cajas=[]
for x,y in informe['puntos_sin_suelo']:
    bb=(x-.35,y-.35,x+.35,y+.35)
    while True:
        j=next((j for j,q in enumerate(cajas) if choca(bb,q)),None)
        if j is None:break
        q=cajas.pop(j);bb=(min(bb[0],q[0]),min(bb[1],q[1]),max(bb[2],q[2]),max(bb[3],q[3]))
    cajas.append(bb)
col=bpy.data.collections.new('reparacion_borrador');bpy.context.scene.collection.children.link(col)
c=Constructor('BASE_reparacion_suelo_institucional');n=0
for bb in cajas:
    piezas=[[(bb[0],bb[1]),(bb[2],bb[1]),(bb[2],bb[3]),(bb[0],bb[3])]]
    for tri,caja in triangulos:
        if not choca(bb,caja):continue
        piezas=[out for p in piezas for out in diferencia(p,tri)]
        if not piezas:break
    for p in piezas:
        p=interseccion(p,datos.orientar_ccw(meta['poligono']))
        if len(p)<3 or _area(p)<1e-7:continue
        asfalto=[];resto=[p]
        for calle in datos.calles_reales():
            radio=calle['ancho']/2-calle['vereda']
            for a,b in zip(calle['eje'],calle['eje'][1:]):
                dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
                if L<.01:continue
                nx,ny=-dy/L*radio,dx/L*radio
                aa=(a[0]-dx/L*.03,a[1]-dy/L*.03);bb=(b[0]+dx/L*.03,b[1]+dy/L*.03)
                rect=datos.orientar_ccw([(aa[0]+nx,aa[1]+ny),(aa[0]-nx,aa[1]-ny),
                                         (bb[0]-nx,bb[1]-ny),(bb[0]+nx,bb[1]+ny)])
                siguientes=[]
                for q in resto:
                    dentro=interseccion(q,rect)
                    if len(dentro)>=3 and _area(dentro)>1e-8:asfalto.append(dentro)
                    siguientes.extend(diferencia(q,rect))
                resto=siguientes
        for rol,poligonos in (('calzada',asfalto),('adoquin',resto)):
            for pol in poligonos:
                limpia=[]
                for p in pol:
                    if not limpia or math.dist(p,limpia[-1])>1e-6:limpia.append(p)
                if len(limpia)>2 and math.dist(limpia[0],limpia[-1])<1e-6:limpia.pop()
                if len(limpia)<3 or _area(limpia)<1e-7:continue
                pts=[]
                for x,y in limpia:
                    hit,_,_,_=arbol.find_nearest(Vector((x,y,altura_suelo(x,y)+.13)))
                    pts.append((x,y,hit.z))
                c.poligono(pts,rol,'#77706b' if rol=='calzada' else '#c9c0aa');n+=1
if n:
    c.objeto(col)
    temporal=os.path.join(base,'BASE_limpia_suelo.glb')
    bpy.ops.export_scene.gltf(filepath=temporal,export_format='GLB',export_yup=True,
                             export_apply=True,export_normals=True,export_materials='EXPORT')
    os.replace(temporal,ruta)
else:c.bm.free()
meta['reparacion_suelo']={'rayos_fallidos_antes':informe['sin_suelo'],'poligonos_nuevos':n,
                        'metodo':'Diferencia exacta con suelo previo, alturas del borde existente'}
json.dump(meta,open(ruta+'.json','w'),indent=2,ensure_ascii=False)
print('[BASE borrador] Huecos reparados:',n,'polígonos, sin superponer el suelo existente',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
