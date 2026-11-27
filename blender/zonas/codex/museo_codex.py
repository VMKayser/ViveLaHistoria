"""Museo: cuerpo posterior M063 y frente sobre E02ae75 de M061.

130907–130916 muestran cinco ejes junto a Guadalupe. 130923 muestra su
encuentro con el paño blanco. Las fotos posteriores de la Universidad
corresponden al extremo de Dalence de E311863, no a este pequeño frente.
No se desplazan las huellas: el POI del museo está en el cuerpo posterior.
"""
from kit import datos,Fachada,ventana,puerta,zocalo,cornisa,pilastra,parapeto
from piezas_codex import trasladar
import math
BLANCO='#eeeae1'


def plano_museo():
    datos.verificar_dueno('codex','M063')
    e=datos.edificio('M063','Ebf5fdd')
    l=datos.lados(datos.edificio('M061','E02ae75')['huella'])[5]
    cat=datos.lados(datos.edificio('M055','E03fe1d')['huella'])[12]
    ax,ay=cat['a'];bx,by=cat['b'];L=math.hypot(bx-ax,by-ay)
    ux,uy=(bx-ax)/L,(by-ay)/L
    ss=lambda p:(p[0]-ax)*ux+(p[1]-ay)*uy
    return e['huella'],l,max(ss(l['a']),ss(l['b']))


def avance_museo():
    _,l,_=plano_museo()
    cat=datos.lados(datos.edificio('M055','E03fe1d')['huella'])[12]
    a=cat['a'];n=cat['normal']
    return sum(((p[0]-a[0])*n[0]+(p[1]-a[1])*n[1]) for p in (l['a'],l['b']))/2


def huellas_ala():
    """Ala de Guadalupe y cierre frontal, sin invadir el cuerpo posterior."""
    h,_,union=plano_museo()
    l=datos.lados(datos.edificio('M055','E03fe1d')['huella'])[12]
    f=Fachada(None,l,0);avance=avance_museo()
    limite=max((p[0]-f.a.x)*f.u.x+(p[1]-f.a.y)*f.u.y for p in h)+.02
    cuerpo=[tuple(f.punto(s,0,d)[:2]) for s,d in
            ((limite,-8.75),(0,-8.75),(0,avance),(limite,avance))]
    cierre=[tuple(f.punto(s,0,d)[:2]) for s,d in
            ((union+.02,avance-.3),(limite,avance-.3),(limite,avance),(union+.02,avance))]
    return [cuerpo,cierre]


def detallar_museo(c,l,z,zb):
    """Cinco ejes, puerta central, carpintería y paneles según las fotos."""
    f=Fachada(c,l,z);paso=f.largo/5
    for k in range(5):
        ss=(k+.5)*paso
        if k==2:
            p=f.punto(ss,0);fp=trasladar(f,h=datos.altura_suelo(p.x,p.y)+.12-z)
            puerta(fp,ss,ancho=1.35,alto=3.1,color='#633c2e',color_moldura=BLANCO)
            for a,b in ((k*paso,ss-.9),(ss+.9,(k+1)*paso)):
                zocalo(f,.85,s0=a,s1=b,desde=zb-z,color='#b69c7c')
        else:
            zocalo(f,.85,s0=k*paso,s1=(k+1)*paso,desde=zb-z,color='#b69c7c')
            ventana(f,ss,1.3,ancho=1.15,alto=2.25,reja=k<2,color_moldura=BLANCO,color_carpinteria='#714335')
            if k>2:f.caja(ss-.5,ss+.5,1.35,3.5,.05,.075,'letrero','#c6ceb5')
        ventana(f,ss,4.85,ancho=1.2,alto=2.3,color_moldura=BLANCO,color_carpinteria='#714335')
        f.caja(ss-.6,ss+.6,4.85,5.45,.04,.06,'madera','#714335')
        for hh in (4.92,5.52):f.caja(ss-.61,ss+.61,hh,hh+.035,.09,.125,'hierro')
        for j in range(8):
            sx=ss-.57+j*1.14/7;f.caja(sx-.012,sx+.012,4.92,5.55,.09,.12,'hierro')
        if k!=2:
            for ds in (-.30,0,.30):
                f.arco(ss+ds,.12,.035,7.42,.05,.12,'moldura',BLANCO,medio=False,segmentos=8)
            cornisa(f,7.2,s0=ss-.8,s1=ss+.8,alto=.1,vuelo=.12,color=BLANCO)
        for hh in (.95,1.45,1.95,2.45,2.95,3.45,4.6,5.1,5.6,6.1,6.6,7.1,7.7):
            for a,b in ((k*paso+.1,ss-.84),(ss+.84,(k+1)*paso-.1)):
                if b>a:f.caja(a,b,hh,hh+.025,.012,.035,'moldura',BLANCO)
    for k in range(6):pilastra(f,k*paso,.85,8.35,ancho=.26,vuelo=.07,color=BLANCO)
    for hh in (4.0,4.25,8.2):cornisa(f,hh,alto=.16,vuelo=.2,color=BLANCO)
    parapeto(f,8.35,alto=.3,color=BLANCO)
    for k in range(6):
        ss=k*paso;f.caja(ss-.18,ss+.18,8.65,8.85,-.15,.12,'moldura',BLANCO)
        p=f.punto(ss,8.85,-.01)
        c.cilindro(p.x,p.y,p.z,p.z+.22,.22,'moldura',BLANCO,lados=4,radio_arriba=.025)
    return f
