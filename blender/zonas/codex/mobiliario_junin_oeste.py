"""Postes/faroles del Junín al oeste de Arenales, #22.
Frente SE en M037 (Eeb6abd/rectorado), frente NO en M027. M036 es
una huella interior: no se confunde su centro con el frente de la calle.
"""
import math
from mathutils import Vector
from kit import *
from piezas_codex import rama,cable_curvo
from tendidos_codex import bvh_coleccion


def posicion(x,lado):
    calle=next(c for c in datos.calles_reales() if c['nombre']=='Calle Batalla de Junín' and c['eje'][0][0]<-365)
    for a,b in zip(calle['eje'],calle['eje'][1:]):
        if a[0]<=x<=b[0]:break
    t=(x-a[0])/(b[0]-a[0]);u=Vector((b[0]-a[0],b[1]-a[1],0)).normalized()
    n=Vector((u.y,-u.x,0))*lado
    # junto al BORDILLO (claude, R0119 2026-11-14: "postes muy pegados a la pared")
    p=Vector((x,a[1]+t*(b[1]-a[1]),0))+n*(calle['ancho']/2-calle['vereda']+.4)
    p.z=altura_suelo(p.x,p.y)+.25
    return p,u,n


def construir_mobiliario(mid,col):
    lado,postes,faroles={'M037':(1,(-354,-314),(-365,-347,-329,-308)),
                         'M027':(-1,(-320,-302),(-319,-311,-299))}[mid]
    arbol=bvh_coleccion(col);anclajes=[]
    for i,x in enumerate(postes):
        p,u,n=posicion(x,lado);c=Constructor(f'{mid}_Junin_poste_{i}')
        c.cilindro(p.x,p.y,p.z-.35,p.z+8.6,.10,'piedra','#b5afa0',lados=10,radio_arriba=.075)
        c.caja_ejes(p+Vector((0,0,8.05)),u,n,(0,0,1),1.8,.14,.14,'metal','#6c6455')
        puntas=[]
        for j in range(6):
            q=p+u*(-.7+j*.28)+Vector((0,0,8.4));puntas.append(q)
            c.cilindro(q.x,q.y,q.z-.28,q.z,.05,'vidrio','#8d9b8b',lados=6)
        c.objeto(col);anclajes.append(puntas)
    c=Constructor(f'{mid}_Junin_cables')
    for a,b in zip(anclajes[0],anclajes[1]):
        puntos=[]
        for k in range(33):
            t=k/32;q=a.lerp(b,t);q.z-=.65*4*t*(1-t);puntos.append(q)
        for p,q in zip(puntos,puntos[1:]):
            delta=q-p
            if arbol.ray_cast(p,delta.normalized(),delta.length)[0] is not None:
                raise ValueError('Cable de Junín cruza fachada: '+mid)
        cable_curvo(c,a,b,flecha=.65,radio=.012,segmentos=32)
    c.objeto(col)
    for i,x in enumerate(faroles):
        p,u,n=posicion(x,lado);c=Constructor(f'{mid}_Junin_farol_{i}')
        c.cilindro(p.x,p.y,p.z-.2,p.z+.20,.16,'hierro','#334139',lados=8)
        c.cilindro(p.x,p.y,p.z+.20,p.z+4.35,.045,'hierro','#334139',lados=8)
        q=p-n*.45+Vector((0,0,4.25))
        cable_curvo(c,p+Vector((0,0,4.25)),q,flecha=-.18,radio=.025,segmentos=10)
        c.cilindro(q.x,q.y,q.z-.16,q.z,.23,'hierro','#334139',lados=10,radio_arriba=.07)
        c.esfera(q.x,q.y,q.z-.22,.16,'vidrio','#c4c3ac',segmentos=8)
        c.objeto(col)
    print('[Junín]',mid,': dos postes, seis vanos libres y',len(faroles),'faroles',flush=True)
