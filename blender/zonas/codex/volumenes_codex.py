"""Envolvente de cuerpos escalonados sin paredes ni tapas en su interior.

Una torre se apoya en el cuerpo inferior. Se particiona su planta antes
de construir las caras; no se apilan cajas cerradas que dejen superficies
coincidentes en la unión.
"""
import math
from collections import defaultdict
from triangulacion_codex import triangular_huella
from parcelas_codex import diferencia_convexa,caja,coinciden
from pavimentos_codex import _area


def cuerpo_escalonado(c,tramos,zbase,color,rol='muro',rol_techo='azotea',vacios=()):
    piezas=[]
    for i,(h,z) in enumerate(tramos):
        pp=[list(t) for t in triangular_huella(h)]
        for j,(otro,altura) in enumerate(tramos):
            if (altura,j)<=(z,i) or not coinciden(caja(h),caja(otro)):continue
            for t in triangular_huella(otro):pp=[q for p in pp for q in diferencia_convexa(p,list(t))]
        for vacio in vacios:
            for t in triangular_huella(vacio):pp=[q for p in pp for q in diferencia_convexa(p,list(t))]
        piezas.extend((p,z) for p in pp if _area(p)>1e-8)
    def key(p):return tuple(round(x,6) for x in p)
    puntos={key(v) for h,z in piezas for v in h}
    bordes=defaultdict(list)
    for h,z in piezas:
        if sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(h,h[1:]+h[:1]))<0:h=list(reversed(h))
        for a,b in zip(h,h[1:]+h[:1]):
            dx,dy=b[0]-a[0],b[1]-a[1];ll=dx*dx+dy*dy
            if ll<1e-14:continue
            entre=[]
            for p in puntos:
                t=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/ll
                if -1e-7<=t<=1+1e-7 and abs(dx*(p[1]-a[1])-dy*(p[0]-a[0]))<2e-6*math.sqrt(ll):entre.append((t,p))
            entre.sort()
            for (_,p),(_,q) in zip(entre,entre[1:]):
                if p!=q:bordes[tuple(sorted((p,q)))].append((p,q,z))
        c.poligono([(x,y,zbase) for x,y in reversed(h)],rol,color)
        c.poligono([(x,y,z) for x,y in h],rol_techo)
    for segmentos in bordes.values():
        assert len(segmentos)<=2,('Celdas superpuestas',segmentos)
        p,q,alto=max(segmentos,key=lambda v:v[2])
        bajo=zbase if len(segmentos)==1 else min(v[2] for v in segmentos)
        if alto-bajo<1e-6:continue
        c.poligono([(p[0],p[1],bajo),(q[0],q[1],bajo),(q[0],q[1],alto),(p[0],p[1],alto)],rol,color)
