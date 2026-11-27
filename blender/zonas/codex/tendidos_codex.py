"""Acometidas: ancladas al primer muro encontrado y comprobadas por rayos.
Geometría propia; solo lee la colección de la manzana que se está modelando.
"""
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from piezas_codex import cable_curvo


def bvh_coleccion(col):
    vs=[];fs=[]
    for ob in col.all_objects:
        if ob.type!='MESH' or 'arbol' in ob.name:continue
        inicio=len(vs);vs += [ob.matrix_world@v.co for v in ob.data.vertices]
        fs += [[inicio+i for i in f.vertices] for f in ob.data.polygons]
    return BVHTree.FromPolygons(vs,fs)


def acometida(c,arbol,a,objetivo,flecha=.4):
    a=Vector(a);q=Vector(objetivo);delta=q-a
    hit,n,indice,d=arbol.ray_cast(a,delta.normalized(),delta.length+2)
    if hit is None:raise ValueError('Acometida sin muro de destino')
    if n.dot(a-hit)<0:n=-n
    final=hit+n*.08
    # El aislador hace contacto con el muro y con el extremo del cable.
    c.esfera(*final,.085,'vidrio','#b3b8a6',segmentos=8)
    puntos=[]
    for k in range(17):
        t=k/16;p=a.lerp(final,t);p.z-=4*flecha*t*(1-t);puntos.append(p)
    for p,q in zip(puntos[:-2],puntos[1:-1]):
        delta=q-p
        r=arbol.ray_cast(p,delta.normalized(),delta.length)
        if r[0] is not None:
            raise ValueError('Acometida cruza geometría antes de su anclaje')
    cable_curvo(c,a,final,flecha=flecha,radio=.012)
    return tuple(final)
