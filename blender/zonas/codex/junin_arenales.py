"""M027 — R0034–R0037. Inventario por foto en INVENTARIO_JUNIN.md.
Frente Junín del lote real + templo en el vacío hasta Arenales, al oeste
de Junín y al sur de Arenales. El anterior San Miguel aproximado en M037
se retira para no duplicar el templo. AMP_O y R0026–R0033 son de Claude (#12).
"""
import math
from kit import *
from piezas_codex import (prisma_seguro,trasladar,recorte_estricto,ventana_rebajada,
 arqueria_lisa_codex,reja_porton,pavimentar,rama)
from frentes_codex import frente_real,farol_muro,portada_baroqua,roseta
from detalles_plaza_codex import ajustar_fachada,punto_encadenado
BLANCO='#eeeae3';CREMA='#d8c5a5';MADERA='#634337';HIERRO='#343630'


def solar(f,s,h):
    f.c.poligono([f.punto(s+.24*math.cos(j*math.tau/24),h+.24*math.sin(j*math.tau/24),.05) for j in range(24)],'hierro',HIERRO,grosor=.08,normal_extrusion=-f.n)
    for j in range(24):
        a=j*math.tau/24
        f.c.poligono([f.punto(s+.24*math.cos(a-.11),h+.24*math.sin(a-.11),.07),
                     f.punto(s+(.85 if j%2 else .66)*math.cos(a),h+(.85 if j%2 else .66)*math.sin(a),.07),
                     f.punto(s+.24*math.cos(a+.11),h+.24*math.sin(a+.11),.07)],'hierro',HIERRO,grosor=.04,normal_extrusion=-f.n)


def casona_junin(e,col):
    h=recorte_estricto(e['huella']);c=Constructor(e['id'])
    z=max(altura_suelo(*p) for p in h);zb=min(altura_suelo(*p) for p in h)-.5
    f,g=frente_real({'id':e['id'],'huella':h},c,z,normal=(.78,-.63));L=f.largo
    # Tres ejes de la casa con marcos de arco rebajado, final de R0034.
    for ss in (1.35,4.0,6.65):
        ventana(trasladar(f,d=.03),ss,1.1,ancho=1.05,alto=2.55,reja=True,color_moldura='#f0eade',color_carpinteria=MADERA)
        ventana_rebajada(trasladar(f,d=.025),ss,5.05,ancho=1.05,alto=2.35,color_moldura='#f0eade')
    # Separación material entre las dos casas, observada en R0034.
    f.caja(0,8.0,.04,8.5,-.025,.005,'muro','#e3dfd4')
    for ss in (1.35,4.0,6.65):
        zocalo(f,1.0,s0=ss-1.32,s1=min(8,ss+1.32),desde=zb-z,color='#9f6650',sillares=True)
    s=17.0
    # Dos ventanas a cada lado de la portada en R0035; la última prolonga
    # el tramo fuera del encuadre y enlaza con la nave que aparece en R0036.
    for ss in (10.1,12.8,22.0,25.0,28.0):
        ventana(trasladar(f,d=.03),ss,1.1,ancho=1.12,alto=2.5,reja=True,color_moldura=BLANCO,color_carpinteria=MADERA)
        ventana(trasladar(f,d=.03),ss,5.15,ancho=1.08,alto=1.9,arco=True,color_moldura=BLANCO,color_carpinteria=MADERA)
    for a,b in ((8,s-3.5),(s+3.5,L)):
        zocalo(f,1.05,s0=a,s1=b,desde=zb-z,color='#b7946f',sillares=False)
    portada_baroqua(f,s,ancho=6.4,H=8.35,color='#f0e9dc',puerta_color=MADERA)
    # Tres gradas retranqueadas: no ocupan la vereda.
    for k in range(3):
        f.caja(s-1.35,s+1.35,-.12,.12+k*.12,-.24*k,0,'piedra','#b3a18a')
    for hh in (4.05,4.4):cornisa(f,hh,alto=.14,vuelo=.16,color=BLANCO)
    alero_tejas(f,8.6,vuelo=.38,fondo=1.4,pendiente=16)
    # Solar sobre la parte próxima al templo, sin tapar ningún vano.

    farol_muro(f,8.4,4.55);farol_muro(f,20.6,4.55)
    # Ménsulas para los faroles fotografiados a los lados de la portada.
    for ss in (s-3.6,s+3.6):
        rama(c,f.punto(ss,4.35,-.02),f.punto(ss,4.35,.75),.025,.025,'hierro',HIERRO)
        rama(c,f.punto(ss,4.8,-.02),f.punto(ss,4.35,.75),.025,.025,'hierro',HIERRO)
        p=f.punto(ss,4.0,.75)
        c.cilindro(p.x,p.y,p.z-.22,p.z+.17,.15,'vidrio','#a3a899',lados=4,radio_arriba=.2)
        c.cilindro(p.x,p.y,p.z+.17,p.z+.3,.22,'hierro',HIERRO,lados=4,radio_arriba=.025)
    ajustar_fachada(c,g)
    prisma_seguro(c,h,zb,z+8.6,'muro',BLANCO)
    f.punto=lambda s,h,d=0:punto_encadenado(g,s,h,d)
    # Retorno largo no fotografiado: casa coherente con teja y vanos de reja.
    exteriores=[l for l in lados(h) if l['normal'][1]>.7 and l['normal'][0]>.5 and l['largo']>4]
    borde=max(((l['a'][0]+l['b'][0])*.65/2+(l['a'][1]+l['b'][1])*.76/2 for l in exteriores),default=0)
    from shapely.geometry import Point,Polygon
    nave=Polygon(huellas_templo()[1]).buffer(.1)
    for l in exteriores:
        proy=(l['a'][0]+l['b'][0])*.65/2+(l['a'][1]+l['b'][1])*.76/2
        if proy<borde-1.2:continue
        mx,my=(l['a'][0]+l['b'][0])/2+l['normal'][0],(l['a'][1]+l['b'][1])/2+l['normal'][1]
        if nave.contains(Point(mx,my)):continue        # R0120: medianera con la nave de Santa Mónica, sin vanos ni alero
        ff=Fachada(c,l,z)
        puerta(trasladar(ff,d=.03),ff.largo*.22,ancho=1.2,alto=2.8,color=MADERA,color_moldura=BLANCO)
        ventana(ff,ff.largo*.22,5.0,ancho=.8,alto=1.55,arco=True,reja=True,color_moldura=BLANCO)
        if (l['a'][0]+l['b'][0])/2>-330 and ff.largo>5.7:solar(ff,ff.largo*.66,6.6)
        alero_tejas(ff,8.6,vuelo=.35,fondo=1.0)
    c.objeto(col)
    return f


def _marco_templo(c,z):
    ux,uy=.627,.779;L=math.hypot(ux,uy);ux,uy=ux/L,uy/L
    nx,ny=uy,-ux
    a=(-305.4-ux*4.5,-32-uy*4.5)
    return Fachada(c,{'a':a,'b':(a[0]+ux*9,a[1]+uy*9),'normal':(nx,ny)},z)


LARGO_NAVE=-46


def huellas_templo():
    f=_marco_templo(None,0)
    atrio=[tuple(f.punto(s,0,d)[:2]) for s,d in ((0,0),(9,0),(9,-11),(0,-11))]
    # R0120 (claude, 2026-11-23): la nave de Santa Mónica sigue hacia atrás por la calle lateral (el lugar de OSM queda
    # a 33 m de la portada, sobre el eje); con 14 m de fondo quedaba un solar vacío donde va su muro lateral.
    nave=[tuple(f.punto(s,0,d)[:2]) for s,d in ((.15,-11),(8.85,-11),(8.85,LARGO_NAVE),(.15,LARGO_NAVE))]
    nave=recorte_estricto(datos.recortar_a_calles(nave))
    from shapely.geometry import Polygon
    casona=Polygon([tuple(p[:2]) for m in datos.reparto()['manzanas'] if m['id']=='M027' for e in m['edificios'] for p in e['huella']])
    resto=Polygon(nave).difference(casona.buffer(.5))     # la casona se modela algo más ancha que su huella del lienzo
    resto=max(getattr(resto,'geoms',[resto]),key=lambda g:g.area)
    nave=[tuple(p) for p in list(resto.exterior.coords)[:-1]]
    return recorte_estricto(datos.recortar_a_calles(atrio)),nave


def campana(c,f,s,h,radio=.34):
    p=f.punto(s,h,-1.2)
    for a,b,r0,r1 in ((0,.12,radio*1.08,radio),(.12,.65,radio,radio*.44),(.65,.82,radio*.44,radio*.31)):
        c.cilindro(p.x,p.y,p.z+a,p.z+b,r0,'metal','#74694f',lados=14,radio_arriba=r1)
    c.cilindro(p.x,p.y,p.z-.15,p.z+.46,.035,'hierro',HIERRO,lados=6)
    f.caja(s-.7,s+.7,h+.8,h+.91,-1.34,-1.06,'madera',MADERA)


def templo_arenales(col):
    atrio,h=huellas_templo();c=Constructor('M027_templo')
    z=max(altura_suelo(*p) for p in atrio)+.12;zb=min(altura_suelo(*p) for p in h)-.5
    gate=_marco_templo(c,z)
    # La portada se apoya en el lado real del cuerpo, once metros tras la reja.
    prisma_seguro(c,h,zb,z+9.1,'muro',BLANCO)
    f,g=frente_real({'id':'M027_templo','huella':h},c,z,normal=tuple(gate.n[:2]))
    s=f.largo/2
    portada_baroqua(f,s,ancho=7.0,H=9.15,color=CREMA,puerta_color='#61422c')
    # Campanario rectangular continuo desde el suelo, detrás de la portada.
    tx=f.punto(s,0,-1.6);w=4.5
    base=[tuple(f.punto(ss,0,d)[:2]) for ss,d in ((s-w/2,0),(s+w/2,0),(s+w/2,-2.7),(s-w/2,-2.7))]
    prisma_seguro(c,base,z+9.1,z+12.2,'muro',BLANCO)
    t=Fachada(c,{'a':tuple(f.punto(s-w/2,0)[:2]),'b':tuple(f.punto(s+w/2,0)[:2]),'normal':tuple(f.n[:2])},z)
    ventana(trasladar(t,d=.04),w/2,9.65,ancho=1.0,alto=1.3,arco=True,reja=True,color_moldura=CREMA)
    for hh in (9.2,12.1):cornisa(t,hh,alto=.24,vuelo=.25,color=BLANCO)
    b=trasladar(t,h=12.35)
    arqueria_lisa_codex(b,0,2,1.5,1.0,pilar=.5,d0=-2.7,d1=0,alto_total=3.0,color=BLANCO)
    for ss in (1.25,3.25):campana(c,t,ss,12.9,.34)
    cornisa(t,15.3,alto=.25,vuelo=.3,color=BLANCO)
    # Remate de un solo arco con campana y pináculos apoyados.
    u=Fachada(c,{'a':tuple(t.punto(.85,0)[:2]),'b':tuple(t.punto(3.65,0)[:2]),'normal':tuple(t.n[:2])},z+15.55)
    arqueria_lisa_codex(u,0,1,1.6,.8,pilar=.6,d0=-2.7,d1=0,alto_total=2.05,color=BLANCO)
    campana(c,t,2.25,15.9,.25)
    cornisa(u,2.0,alto=.24,vuelo=.20,color=BLANCO)
    u.timpano_arco(1.4,.6,2.1,-.15,'muro',BLANCO,segmentos=20)
    u.arco(1.4,.6,.12,2.1,-.16,.02,'moldura',BLANCO,segmentos=20)
    for ss in (.45,4.05):
        pilastra(t,ss,9.25,12.0,ancho=.23,vuelo=.12,rol='piedra',color=CREMA)
        roseta(t,ss,11.2,.13,rol='piedra',color=CREMA)
    for ss in (.4,4.1):
        t.caja(ss-.15,ss+.15,15.55,16.05,-.4,-.1,'moldura',BLANCO)
        p=t.punto(ss,16.05,-.25);c.cilindro(p.x,p.y,p.z,p.z+.30,.22,'moldura',BLANCO,lados=4,radio_arriba=.01)
    p=t.punto(2.25,17.84,-.25)
    c.cilindro(p.x,p.y,p.z,p.z+.95,.023,'hierro',HIERRO,lados=6)
    rama(c,(p.x-t.u.x*.32,p.y-t.u.y*.32,p.z+.63),(p.x+t.u.x*.32,p.y+t.u.y*.32,p.z+.63),.022,.022,'hierro',HIERRO)
    # Tejado bajo detrás de torre, dentro de la nave; sin vuelo sobre el atrio.
    for l in lados(h):
        if l['largo']>10 and l['a_calle']:
            ff=Fachada(c,l,z)
            # R0120: muro lateral de la nave sobre la calle (el que da a la casona queda oculto): zócalo de piedra,
            # contrafuertes cada ~6 m, ventanas altas de arco con reja y cornisa bajo el alero.
            if l['a_calle']:
                ff.caja(0,ff.largo,-.6,.9,0,.06,'zocalo_piedra','#9a8064')
                n=max(2,round(ff.largo/6.2))
                for k in range(n+1):
                    ss=min(max(k*ff.largo/n,.5),ff.largo-.5)
                    ff.caja(ss-.45,ss+.45,-.6,6.8,0,.45,'muro',BLANCO)
                    ff.caja(ss-.5,ss+.5,6.8,7.1,0,.5,'moldura',BLANCO)
                for k in range(n):
                    ss=(k+.5)*ff.largo/n
                    if 3<ss<ff.largo-3:ventana(trasladar(ff,d=.03),ss,5.4,ancho=1.0,alto=1.9,arco=True,reja=True,color_moldura=BLANCO)
                cornisa(ff,8.75,alto=.25,vuelo=.22,color=BLANCO)
    # R0120: cubierta de teja a dos aguas de la nave (antes azotea blanca con un alero suelto), con hastial blanco en cada
    # extremo; vuela 0,5 m solo sobre la calle (del lado de la casona es medianera).
    d0,d1,s0,s1,cum=-11.0,-43.6,.15,8.85,2.1
    sm=(s0+s1)/2
    for a_,b_,vuelo in ((s0,sm,0.0),(s1,sm,.5)):
        e0=a_-vuelo if a_<sm else a_+vuelo
        ze=9.1-cum*vuelo/(sm-s0)
        q=[gate.punto(e0,ze,d0),gate.punto(e0,ze,d1),gate.punto(b_,9.1+cum,d1),gate.punto(b_,9.1+cum,d0)]
        c.poligono([tuple(p) for p in q],'teja','#b0573c',grosor=.1,normal_extrusion=(0,0,-1))
    for dd in (d0,d1):
        c.poligono([tuple(gate.punto(s0,9.1,dd)),tuple(gate.punto(s1,9.1,dd)),tuple(gate.punto(sm,9.1+cum,dd))],'muro',BLANCO,
                   grosor=.3,normal_extrusion=tuple(gate.n*(1 if dd==d0 else -1)))
    c.objeto(col)
    # Atrio abierto: piso propio, gradas y reja realmente calada.
    c=Constructor('M027_atrio_piso');pavimentar(c,atrio,'adoquin',offset=.15,color='#c6b79d');c.objeto(col)
    c=Constructor('M027_atrio_reja');gate=_marco_templo(c,z)
    for a,b in ((0,2.95),(6.05,9)):
        gate.caja(a,b,-.6,.55,-.22,.02,'zocalo_piedra','#9a8064')
        for k in range(max(2,round((b-a)/.18))):
            ss=a+(k+.5)*(b-a)/max(2,round((b-a)/.18))
            gate.cilindro_vertical(ss,.55,2.05,.01,.018,'hierro',HIERRO,lados=5)
        for hh in (.75,1.75):gate.caja(a,b,hh,hh+.035,-.01,.04,'hierro',HIERRO)
    for ss in (0,2.8,6.2,9):
        gate.caja(ss-.22,ss+.22,-.6,2.15,-.30,.05,'piedra',CREMA)
        gate.caja(ss-.29,ss+.29,2.15,2.32,-.37,.12,'piedra',CREMA)
        p=gate.punto(ss,2.32,-.12);c.cilindro(p.x,p.y,p.z,p.z+.44,.23,'piedra',CREMA,lados=4,radio_arriba=.04)
        c.esfera(p.x,p.y,p.z+.48,.09,'piedra',CREMA,segmentos=6)
    # Hojas abiertas hacia el atrio; ancladas a sus pilares.
    for ss,signo in ((2.99,-1),(6.01,1)):
        a=gate.punto(ss,0,0);b=gate.punto(ss+signo*.38,0,-1.5)
        hoja=Fachada(c,{'a':tuple(a[:2]),'b':tuple(b[:2]),'normal':tuple((gate.u*signo)[:2])},z)
        reja_porton(hoja,hoja.largo/2,ancho=hoja.largo,alto=2.0)
    c.objeto(col)
    return [f,gate]
