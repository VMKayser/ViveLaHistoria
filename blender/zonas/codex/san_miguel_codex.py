"""San Miguel en el vacío del lienzo de M037, al sur de Arenales.

Fotos 130357/130401 (frente Junín), 130427/130431/130435 y 130440
(costado Arenales y atrio). Punto OSM del templo: (-263.07,-73.85).
La huella Eeb6abd empieza unos 18 m detrás del frente real. Se completa
esa franja con huellas propias, sin cruzar las líneas de fachada de las
calles reales. Implantación inicial: revisar desde ambas calles.
"""
import math
from kit import *
from piezas_codex import prisma_seguro,trasladar,reja_porton,arbol_podado,farol_pie,arqueria_lisa_codex
from triangulacion_codex import triangular_huella
BLANCO='#eee8dc';PIEDRA='#d8c5a5'


def construir_san_miguel(col):
    # Esquina situada al SE del cruce Junín–Arenales, tras sus veredas.
    ax,ay=-292.582,-40.463
    ux,uy=.771,-.637
    L=math.hypot(ux,uy);ux,uy=ux/L,uy/L
    nx,ny=-uy,ux                    # normal hacia la calle, NE
    def punto(s,d):return (ax+ux*s+nx*d,ay+uy*s+ny*d)
    def rect(s0,s1,d0,d1):return [punto(s0,d0),punto(s1,d0),punto(s1,d1),punto(s0,d1)]
    def fachada(c,s0=0,s1=52,d=0,z=0):
        return Fachada(c,{'a':punto(s0,d),'b':punto(s1,d),'normal':(nx,ny)},z)
    h=rect(0,31,-18,0)
    # El recorte del kit también protege las calzadas para estas huellas nuevas.
    h=datos.recortar_a_calles(h)
    if not h:raise ValueError('San Miguel quedó dentro de una calle')
    z=max(altura_suelo(*p) for p in h);zb=min(altura_suelo(*p) for p in h)-.4
    c=Constructor('M037_SanMiguel_templo')
    prisma_seguro(c,h,zb,z+9.5,'muro',BLANCO)
    f=fachada(c,0,31,z=z)
    cornisa(f,6.2,alto=.20,vuelo=.13,color=BLANCO)
    # Paño largo casi ciego, ventana alta aislada (130427–130431).
    ventana(f,23,6.8,ancho=.9,alto=1.3,reja=True,color_moldura=BLANCO)
    # Bandera boliviana pequeña junto al vano alto, visible en 130431.
    f.caja(23.7,23.75,6.5,7.8,.08,.12,'hierro')
    for j,color in enumerate(('#b55345','#d8b85b','#5b824c')):
        hh=7.5-j*.26
        c.poligono([f.punto(23.75,hh,.12),f.punto(24.12,hh-.05,.35),
                    f.punto(24.12,hh-.31,.35),f.punto(23.75,hh-.26,.12)],
                   'pintura_acento',color)
    alero_tejas(f,9.5,vuelo=.4,fondo=1.8)
    # Frente a Junín: portada clara, columnas salomónicas y nicho alto.
    g=Fachada(c,{'a':punto(0,0),'b':punto(0,-18),'normal':(-ux,-uy)},z)
    s=8.7
    pie=g.punto(s,0);gg=trasladar(g,h=altura_suelo(pie.x,pie.y)+.15-z)
    gg.caja(s-3.8,s+3.8,0,9.4,-.1,.12,'piedra',PIEDRA)
    puerta(trasladar(gg,d=.14),s,ancho=2.5,alto=3.6,arco=True,color='#63422d',color_moldura=PIEDRA)
    for ds in (-3.0,-2.3,2.3,3.0):
        ss=s+ds
        gg.caja(ss-.3,ss+.3,0,1.1,0,.45,'piedra',PIEDRA)
        gg.cilindro_vertical(ss,1.1,5.6,.25,.18,'piedra',PIEDRA,lados=10)
        # Cordón en hélice: relieve legible de las columnas fotografiadas.
        for k in range(22):
            ang=k*math.tau/7
            p=gg.punto(ss+.20*math.cos(ang),1.2+k*.195,.25+.20*math.sin(ang))
            c.esfera(p.x,p.y,p.z,.075,'moldura',PIEDRA,segmentos=6)
        for hh in (1.1,5.5,5.8):gg.caja(ss-.32,ss+.32,hh,hh+.15,0,.52,'piedra',PIEDRA)
    for hh,w in ((6.0,8.0),(6.35,7.6),(9.0,6.0),(9.35,4.8)):
        cornisa(gg,hh,s0=s-w/2,s1=s+w/2,alto=.25,vuelo=.6,rol='piedra',color=PIEDRA)
    ventana(trasladar(gg,d=.15),s,6.7,ancho=1.0,alto=1.3,arco=True,reja=True,color_moldura=PIEDRA)
    for ds in (-2.0,2.0):
        pilastra(gg,s+ds,6.5,9.0,ancho=.3,vuelo=.35,rol='piedra',color=PIEDRA)
        gg.arco(s+ds,.28,.08,7.3,.15,.3,'piedra',PIEDRA,medio=False,segmentos=10)
    for w,hh in ((4.0,9.6),(3.0,10.0),(1.6,10.4)):
        gg.caja(s-w/2,s+w/2,hh,hh+.45,-.15,.18,'piedra',PIEDRA)
    # Ventanas del costado de Junín visibles a la izquierda de la portada.
    for ss in (2.2,15.8):ventana(g,ss,5.0,ancho=.85,alto=2.0,arco=True,reja=True)
    alero_tejas(g,9.5,s0=0,s1=3.5,vuelo=.35,fondo=1.0)
    c.objeto(col)
    # Torre de tres cuerpos, situada dentro de la esquina del templo.
    c=Constructor('M037_SanMiguel_torre')
    tx,ty=punto(4.0,-4.0);z=altura_suelo(tx,ty)+.15
    for j,(h0,h1,w) in enumerate(((0,12.5,5.8),(12.5,17.0,4.9),(17.0,20.6,4.0))):
        hh=[(tx+ux*a+nx*b,ty+uy*a+ny*b) for a,b in ((-w/2,-w/2),(w/2,-w/2),(w/2,w/2),(-w/2,w/2))]
        if j==0:prisma_seguro(c,hh,z-.4,z+h1,'muro',BLANCO)
        else:
            for l in lados(hh):
                t=Fachada(c,l,z+h0)
                arqueria_lisa_codex(t,0,2 if j==1 else 1,(w-3*.55)/2 if j==1 else w-1.1,
                                   2.15 if j==1 else 1.9,pilar=.55,alto_total=h1-h0-.3,color=BLANCO)
                cornisa(t,h1-h0-.3,alto=.3,vuelo=.23,color=BLANCO)
            c.tapa(hh,z+h0,'azotea')
        for l in lados(hh):
            t=Fachada(c,l,z)
            cornisa(t,h1-.1,alto=.3,vuelo=.25,color=BLANCO)
            for ss in (.25,w-.25):pilastra(t,ss,h0,h1,ancho=.35,vuelo=.15,color=PIEDRA)
    c.cilindro(tx,ty,z+20.9,z+22.2,1.8,'muro',BLANCO,lados=8,radio_arriba=.6)
    c.caja(tx-.04,ty-.04,z+22.1,tx+.04,ty+.04,z+23.2,'hierro')
    c.caja(tx-.35,ty-.04,z+22.85,tx+.35,ty+.04,z+22.93,'hierro')
    c.objeto(col)
    # Atrio y casita del extremo SE (foto 130440).
    c=Constructor('M037_SanMiguel_atrio');h=rect(31,44,-8,0)
    for tri in triangular_huella(h):c.poligono([(x,y,altura_suelo(x,y)+.16) for x,y in tri],'adoquin')
    c.objeto(col)
    c=Constructor('M037_SanMiguel_casita');h=datos.recortar_a_calles(rect(44,52,-11,0))
    z=max(altura_suelo(*p) for p in h);zb=min(altura_suelo(*p) for p in h)-.4
    prisma_seguro(c,h,zb,z+7.7,'muro',BLANCO)
    f=fachada(c,44,52,z=z)
    ventana(f,4.0,1.2,ancho=1.1,alto=1.8,reja=True,color_carpinteria='#8c4b3d')
    ventana(f,4.0,4.9,ancho=1.1,alto=1.9,balcon='hierro',color_carpinteria='#8c4b3d')
    retorno=Fachada(c,{'a':punto(44,0),'b':punto(44,-11),'normal':(-ux,-uy)},z)
    for ss in (2,5.5,9):
        ventana(retorno,ss,1.2,ancho=.9,alto=1.7,reja=True,color_carpinteria='#8c4b3d')
        ventana(retorno,ss,5.0,ancho=.85,alto=1.35,color_carpinteria='#8c4b3d')
    alero_tejas(retorno,7.7,vuelo=.6,fondo=1.3)
    alero_tejas(f,7.7,vuelo=.7,fondo=1.4)
    c.objeto(col)
    c=Constructor('M037_SanMiguel_porton')
    p=punto(31,0);z=altura_suelo(*p)+.15;f=fachada(c,31,44,z=z)
    for a,b in ((0,2.4),(5.6,13)):
        zocalo(f,.8,s0=a,s1=b,desde=-.8,color='#a48968')
        for k in range(round((b-a)/.22)+1):
            ss=a+(b-a)*k/max(1,round((b-a)/.22))
            f.cilindro_vertical(ss,.8,2.8,0,.018,'hierro',lados=4)
        f.caja(a,b,2.5,2.55,-.02,.02,'hierro')
    reja_porton(f,4,ancho=3.2,alto=3.0)
    for ss in (0,2.2,5.8,12.8):
        f.caja(ss-.25,ss+.25,-.5,3.1,-.25,.22,'piedra',PIEDRA)
        remate_bola(f,ss,3.1,radio=.22,rol='piedra',color=PIEDRA)
    c.objeto(col)
    for k,(ss,dd) in enumerate(((33,-5),(40,-5),(42,-3))):
        x,y=punto(ss,dd);arbol_podado(f'M037_SanMiguel_arbol_{k}',x,y,col,radio=1.2,alto=3.5)
    x,y=punto(35,.65);farol_pie('M037_SanMiguel_farol',x,y,col,alto=3.4)
