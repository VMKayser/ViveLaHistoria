"""M055 — Catedral y Palacio, revisados con las fotos del conjunto.

Fotos examinadas: hoja completa; detalles 130715, 130736, 130840, 130902,
130913. Las asociaciones de foto no equivalen siempre al edificio visible:
130709 muestra el Palacio aunque está asociada a la Catedral.

E2c6601, lado 0: Palacio, fotos 1–6. Tres niveles (3.4 + 4.0 + 4.0 m),
4 ejes por ala y tres accesos centrales; blanco #eeeae2, fondo gris #7b8588,
zócalo arenisca 0.8 m. Balustradas, pilastras, arco y mansarda central.
E03fe1d, lado 2: fotos 7–11, blanco, tres ventanas altas y dos arcos
sobre balcón corrido; puerta bajo balcón, coronación de balaustres.
Lados 10–14: fotos 12–25; portadas arenisca #ae805e, puertas verde
#24594d, columnas pareadas, torre blanca con bandas de piedra, dos
campanarios decrecientes de dos arcos por cara y cuerpo de reloj.
Las alturas son estimadas, no levantamiento. El atrio se retranquea respecto
de la portada de Guadalupe, alineada con el frente del museo en E02ae75.
El ala se comprueba sin solapamientos con otras huellas y fuera de calzada.
E749b6b y Eae1b1b: sin foto propia; dos plantas sencillas, sin atribuir
al bloque ventanas de las fotos del museo (edificio vecino fuera de M055).
"""
import os
import sys
import math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from kit import *
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# piezas de codex (solo lectura): este conjunto lo empezó codex y pasó a claude el 2026-11-14 (pedido del usuario)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'codex'))
from piezas_codex import trasladar, campanario, reja_porton, juntas, prisma_seguro, recortar_interior, arbol_podado, farol_pie

from casas_codex import casa_minima
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
from piezas_claude import junto_al_bordillo
from catedral_gobernacion import patio_institucional,suelo_frente_institucional,cubiertas_catedral
AGENTE = 'claude'
MANZANA = 'M055'
BLANCO = '#eeeae2'
PIEDRA = '#ae805e'
m, col = iniciar(AGENTE, MANZANA)


def base(e, alto, color=BLANCO):
    c = Constructor(e['id'])
    ls = lados(e['huella'])
    z = max(altura_suelo(*p) for p in e['huella'])
    zb = min(altura_suelo(*p) for p in e['huella']) - .65
    prisma_seguro(c,e['huella'],zb,z+alto,'muro',color)
    return c, ls, z, zb


def balaustrada(f, h, s0=0, s1=None, piedra=False):
    s1 = f.largo if s1 is None else s1
    rol, color = ('piedra', PIEDRA) if piedra else ('moldura', BLANCO)
    for hh in (h, h + .88):
        f.caja(s0, s1, hh, hh + .13, -.22, .18, rol, color)
    n = max(1, round((s1-s0)/.52))
    for i in range(n+1):
        s = s0 + (s1-s0)*i/n
        f.cilindro_vertical(s, h+.13, h+.88, 0, .065, rol, color)
        p=f.punto(s,h+.48)
        # Bulbo de ocho caras: legible a escala urbana y sin exceder presupuesto.
        vs=[p+f.u*.105,p+f.n*.105,p-f.u*.105,p-f.n*.105]
        for j in range(4):
            for signo in (-1,1):
                f.c.poligono([vs[j],vs[(j+1)%4],p+f.z*(.13*signo)],rol,color)
    for i in range(max(1, round((s1-s0)/3.5))+1):
        s = s0+(s1-s0)*i/max(1, round((s1-s0)/3.5))
        f.caja(s-.18,s+.18,h,h+1.03,-.25,.21,rol,color)
        if piedra:
            remate_bola(f,s,h+1.03,radio=.16,rol=rol,color=color)
        else:
            # Urnas oscuras del pretil, en lugar de bolas blancas (130724/743).
            p=f.punto(s,h+1.03)
            for h0,h1,r0,r1 in ((0,.10,.13,.08),(.10,.27,.08,.17),
                                (.27,.40,.17,.065),(.40,.49,.065,.025)):
                f.c.cilindro(p.x,p.y,p.z+h0,p.z+h1,r0,'piedra','#52604e',
                              lados=6,radio_arriba=r1)


def imagen_sacra(c,x,y,z,alto=1.2):
    """Silueta de túnica y cabeza de los santos sobre las cornisas de torre."""
    s=alto/1.2;color='#717363'
    c.cilindro(x,y,z,z+.77*s,.18*s,'piedra',color,lados=8,radio_arriba=.12*s)
    c.esfera(x,y,z+.94*s,.13*s,'piedra',color,segmentos=8)
    c.caja(x-.20*s,y-.08*s,z+.61*s,x+.20*s,y+.08*s,z+.73*s,'piedra',color)
    c.cilindro(x+.15*s,y,z+.40*s,z+.65*s,.055*s,'piedra',color,lados=6)


def portada(f, s, ancho=7.5, alto=12, iconografia=False):
    """Portada simplificada en relieve, columnas pareadas y coronación."""
    vertices_anteriores=set(f.c.bm.verts)
    f.caja(s-ancho/2,s+ancho/2,0,6.9,-.12,.18,'piedra',PIEDRA)
    perfil=[(-.5,6.9),(-.5,10.0),(-.43,10.7),(-.35,10.0),
            (-.23,10.0),(-.18,11.0),(-.08,11.0),(0,12),
            (.08,11.0),(.18,11.0),(.23,10.0),(.35,10.0),
            (.43,10.7),(.5,10.0),(.5,6.9)]
    f.c.poligono([f.punto(s+x*ancho,h,.18) for x,h in perfil],
                  'piedra',PIEDRA,grosor=.3,normal_extrusion=-f.n)
    # La carpintería se adelanta al paño para evitar ocultarla con la portada.
    ff = Fachada(f.c, {'a':tuple(f.punto(0,0,.2)[:2]),
        'b':tuple(f.punto(f.largo,0,.2)[:2]), 'normal':tuple(f.n[:2])}, f.suelo)
    puerta(ff,s,ancho=3.1,alto=4.3,arco=True,color='#24594d',color_moldura=PIEDRA)
    for fila in range(10):
        for k in range(7):
            ss=s-1.3+k*.43; hh=.35+fila*.43
            ff.caja(ss-.035,ss+.035,hh-.035,hh+.035,.06,.10,'hierro')
    for a,b in ((s-ancho/2,s-1.85),(s+1.85,s+ancho/2)):
        juntas(ff,0,6.9,a,b)
    ff.arco(s,1.45,.20,8.3,0,.35,'piedra',PIEDRA,segmentos=16)
    for signo in (-1,1):
        for k in range(2):
            ff.arco(s+signo*(ancho*.27+k*.22),.30-k*.07,.07,
                    7.35+k*.43,.15,.30,'piedra',PIEDRA,medio=False,segmentos=10)
    for ds in (-ancho*.4,-ancho*.29,ancho*.29,ancho*.4):
        x=s+ds
        ff.caja(x-.4,x+.4,0,1.5,-.1,.65,'piedra',PIEDRA)
        ff.cilindro_vertical(x,1.5,6.2,.36,.24,'piedra',PIEDRA,lados=12)
        for h in (1.5,1.7,5.9,6.2):
            ff.caja(x-.37,x+.37,h,h+.18,0,.7,'piedra',PIEDRA)
        remate_bola(ff,x,7.0,d=.2,radio=.22,rol='piedra',color=PIEDRA)
    cornisa(ff,6.5,s0=s-ancho/2,s1=s+ancho/2,rol='piedra',color=PIEDRA)
    if not iconografia:
        ventana(ff,s,7.5,ancho=1.25,alto=1.5,arco=True,reja=True,moldura='piedra',color_moldura=PIEDRA)
    else:
        # La portada hacia plaza tiene esculturas en nichos, no una ventana.
        ff.caja(s-.65,s+.65,6.9,8.5,0,.02,'piedra',PIEDRA)
        for ss in (s-.72,s+.72):pilastra(ff,ss,6.8,8.2,ancho=.16,vuelo=.25,rol='piedra',color=PIEDRA)
        ff.arco(s,.65,.14,8.1,.15,.32,'piedra',PIEDRA,segmentos=12)
        p=ff.punto(s,7.1,.24)
        ff.c.cilindro(p.x,p.y,p.z,p.z+.7,.24,'piedra','#c8b493',lados=8,radio_arriba=.13)
        ff.c.esfera(p.x,p.y,p.z+.9,.15,'piedra','#c8b493',segmentos=8)
        ff.caja(s-.3,s+.3,7.45,7.57,.23,.37,'piedra','#c8b493')
    for w,h in ((ancho*.72,9.5),(ancho*.5,10.2),(ancho*.3,10.8),(ancho*.12,11.4)):
        ff.caja(s-w/2,s+w/2,h,h+.65,-.1,.3,'piedra',PIEDRA)
        cornisa(ff,h+.4,s0=s-w/2,s1=s+w/2,rol='piedra',color=PIEDRA,alto=.2)
    if iconografia:
        # Segundo nicho de la coronación, documentado en 130755 y 130818.
        ff.caja(s-.45,s+.45,9.65,10.8,.31,.33,'piedra',PIEDRA)
        ff.arco(s,.45,.12,10.25,.42,.58,'piedra',PIEDRA,segmentos=10)
        p=ff.punto(s,9.75,.52)
        ff.c.cilindro(p.x,p.y,p.z,p.z+.48,.16,'piedra','#c8b493',lados=8,radio_arriba=.10)
        ff.c.esfera(p.x,p.y,p.z+.63,.12,'piedra','#c8b493',segmentos=8)
    if alto!=12:
        # Alargar solo el cuerpo superior: mantener a escala humana la puerta.
        for v in f.c.bm.verts:
            if v in vertices_anteriores:continue
            h=v.co.z-f.suelo
            if h>6.5:v.co.z=f.suelo+6.5+(h-6.5)*(alto-6.5)/5.5


for e in m['edificios']:
    if e['id']=='Eae1b1b':
        from dalence_codex import asamblea
        asamblea(e,col)
        continue
    if e['id']=='E749b6b':
        # Pedido del usuario: solo el conjunto institucional, sin viviendas
        # genéricas inventadas. Área despejada con suelo propio.
        patio_institucional(e,col)
        continue
    if e['id']=='E2c6601':
        c, ls, z, zb = base(e,11.4,'#9aa7b6')   # R0160–R0162: el muro del Palacio es gris azulado con molduras blancas
        f=Fachada(c,ls[0],z)
        L=f.largo; centro=L/2
        zocalo(f,.85,s1=centro-3.3,color=PIEDRA,desde=zb-z)
        zocalo(f,.85,s0=centro+3.3,color=PIEDRA,desde=zb-z)
        f.caja(centro-4,centro+4,3.5,11.4,0,.001,'muro','#8794a4')
        for h in (3.4,7.4,10.8):
            cornisa(f,h,alto=.22,vuelo=.22,color=BLANCO,s1=centro-4.2)
            cornisa(f,h,alto=.22,vuelo=.22,color=BLANCO,s0=centro+4.2)
        # Cuatro ejes por ala, visibles en la fotografía frontal.
        for s in [2.0,4.7,7.4,10.1,L-10.1,L-7.4,L-4.7,L-2.0]:
            for h in (1.0,4.0,8.0):
                ventana(f,s,h,ancho=1.25,alto=2.15,color_moldura=BLANCO,color_carpinteria='#5b2b22',reja=(h==1.0))
            balaustrada(f,3.7,s-.8,s+.8)
            balaustrada(f,7.7,s-.65,s+.65)
            # Guardapolvos, medallones y ménsulas de las dos plantas nobles (130715).
            for h in (6.7,10.5):
                f.arco(s,.23,.08,h,.07,.22,'moldura',BLANCO,medio=False,segmentos=12)
                f.esfera(s,h,.16,.12,'moldura',BLANCO)
                for signo in (-1,1):
                    f.arco(s+signo*.43,.16,.055,h-.12,.08,.20,
                           'moldura',BLANCO,medio=False,segmentos=10)
                cornisa(f,h+.34,s0=s-.85,s1=s+.85,alto=.11,vuelo=.22,color=BLANCO)
            for h in (3.45,7.45):
                for ds in (-.57,.57):
                    f.caja(s+ds-.1,s+ds+.1,h-.22,h+.15,0,.24,'moldura',BLANCO)
        for s in [0.4,3.35,6.05,8.75,11.5,L-11.5,L-8.75,L-6.05,L-3.35,L-.4]:
            pilastra(f,s,3.6,10.9,ancho=.62,vuelo=.2,color=BLANCO)
            for ds in (-.17,0,.17):                       # acanaladuras del fuste
                f.caja(s+ds-.012,s+ds+.012,4.0,10.4,.19,.215,'muro','#aeb9c6')
        # Detalles de las alas (R0160: "le falta mucho detalle a la gobernación"; foto de frente y de escorzo):
        # hiladas blancas en la planta baja, tableros bajo los balcones, rosetones sobre las ventanas, friso de
        # dentículos bajo la cornisa y óculos con guirnalda en el ala.
        for lo,hi in ((0,centro-4.2),(centro+4.2,L)):
            for h in (1.25,1.85,2.45,3.05):
                imposta(f,h,alto=.1,vuelo=.03,s0=lo,s1=hi,color=BLANCO)
            n=int((hi-lo)/.34)
            for k in range(n+1):
                ss=lo+(hi-lo)*k/n
                f.caja(ss-.09,ss+.09,10.95,11.3,0,.2,'moldura',BLANCO)
        for s in [2.0,4.7,7.4,10.1,L-10.1,L-7.4,L-4.7,L-2.0]:
            for h in (4.0,8.0):
                f.caja(s-.55,s+.55,h-.95,h-.35,.0,.07,'moldura',BLANCO)          # tablero bajo el balcón
                f.caja(s-.45,s+.45,h-.85,h-.45,.07,.09,'muro','#aeb9c6')
            for h in (6.95,10.75):
                f.esfera(s,h,.08,.17,'moldura',BLANCO)                                # roseta
                f.arco(s,.17,.035,h,.0,.06,'muro','#6f7c8a',medio=False,segmentos=10)
        for ds in (-2.4,0,2.4):
            pie=f.punto(centro+ds,0)
            dz=altura_suelo(pie.x,pie.y)+.08-z
            puerta(trasladar(f,h=dz),centro+ds,ancho=1.65 if ds==0 else 1.2,
                   alto=2.5-dz,arco=True,color='#76462a')
            ventana(f,centro+ds,4.1,ancho=1.6 if ds==0 else 1.2,alto=1.8,arco=True)
        balaustrada(f,3.65,centro-3.7,centro+3.7)
        for ds in (-4.2,4.2):
            pilastra(f,centro+ds,3.6,12.8,ancho=.65,vuelo=.3)
        f.arco(centro,3.6,.35,8.0,0,.3,'moldura',BLANCO,segmentos=24)
        # Medallón oval con el cóndor y las alas de colores bajo el gran arco (R0160, foto de frente): anillo blanco y
        # alas amarillo / verde / rojo sobre fondo morado; escudo central en relieve.
        def elipse(ss,hh,rx,ry,d,rol,color,n=28,grosor=.05):
            pts=[f.punto(ss+rx*math.cos(-k*math.tau/n),hh+ry*math.sin(-k*math.tau/n),d) for k in range(n)]
            c.poligono(pts,rol,color,grosor=grosor,normal_extrusion=f.n)
        elipse(centro,8.85,2.15,1.35,.07,'moldura',BLANCO,grosor=.1)
        elipse(centro,8.85,1.95,1.15,.14,'pintura_acento','#5b4a7a')
        elipse(centro,8.85,1.72,1.0,.17,'pintura_acento','#d9b23a')
        elipse(centro,8.85,1.4,.82,.20,'pintura_acento','#3f7d4a')
        elipse(centro,8.85,1.08,.64,.23,'pintura_acento','#b23a2e')
        elipse(centro,8.85,.8,.5,.26,'pintura_acento','#e7e1d0')
        for signo in (-1,1):                                     # figuras alegóricas a los lados del escudo
            ss=centro+signo*1.05
            c.cilindro(f.punto(ss,0).x,f.punto(ss,0).y,f.suelo+7.55,f.suelo+8.45,.2,'moldura',BLANCO,lados=8,radio_arriba=.14)
            c.esfera(f.punto(ss,0).x,f.punto(ss,0).y,f.suelo+8.65,.14,'moldura',BLANCO,segmentos=8)
        escudo=[(-.55,9.3),(.55,9.3),(.48,8.5),(0,8.15),(-.48,8.5)]
        c.poligono([f.punto(centro+x,h,.32) for x,h in escudo],
                   'pintura_acento','#b99b55',grosor=.08,normal_extrusion=f.n)
        f.arco(centro,.32,.10,8.8,.41,.48,'moldura',BLANCO,medio=False)
        cornisa(f,11.4,color=BLANCO)
        balaustrada(f,11.85)
        f.caja(centro-4.5,centro+4.5,11.8,13.3,-6,0,'muro','#7b8588')
        cornisa(f,13.2,s0=centro-4.7,s1=centro+4.7)
        # Perfil de cubierta con hombros curvos y meseta central.
        perfil=[(-3.7,13.6)]
        for k in range(9):
            ang=math.pi-k*math.pi/16
            perfil.append((-2.2+1.5*math.cos(ang),13.6+1.5*math.sin(ang)))
        perfil.append((2.2,15.1))
        for k in range(1,9):
            ang=math.pi/2-k*math.pi/16
            perfil.append((2.2+1.5*math.cos(ang),13.6+1.5*math.sin(ang)))
        c.poligono([f.punto(centro+x,h,-.3) for x,h in perfil],
                   'metal','#69766c',grosor=5.2,normal_extrusion=-f.n)
        # Juntas elevadas del metal siguiendo el perfil de la cubierta.
        for (x0,h0),(x1,h1) in zip(perfil[1:],perfil[2:]):
            c.poligono([f.punto(centro+x0,h0+.035,-.28),
                        f.punto(centro+x1,h1+.035,-.28),
                        f.punto(centro+x1,h1+.035,-5.5),
                        f.punto(centro+x0,h0+.035,-5.5)],'metal','#839087')
        lucarna=trasladar(f,d=-.18)
        for ds in (-2.5,0,2.5):
            ventana(lucarna,centro+ds,13.7,ancho=.70,alto=.8,arco=True)
            lucarna.arco(centro+ds,.5,.10,14.65,0,.2,'moldura',BLANCO,
                         medio=False,segmentos=16)
        # Crestería superior de la mansarda, documentada en la foto frontal.
        for ds in (-2.1,0,2.1):
            f.caja(centro+ds-.035,centro+ds+.035,15.05,15.6,-1,-.92,'hierro')
            remate_bola(f,centro+ds,15.6,d=-.96,radio=.10,rol='metal')
        # Retorno Argentina: sin foto, terminación sobria.
        g=Fachada(c,ls[1],z)
        zocalo(g,.85,desde=zb-z)
        for h in (1,4,8):
            for s in (2.2,5.5,8.8,12): ventana(g,s,h)
        cornisa(g,11.4)
        c.objeto(col)
        continue

    c=Constructor(e['id'])
    ls=lados(e['huella'])
    z=max(altura_suelo(*p) for p in e['huella'])
    zb=min(altura_suelo(*p) for p in e['huella'])-.65
    frente=Fachada(c,ls[12],z)
    # La nave termina detrás del atrio y del campanario, que tiene su propio
    # basamento. Evitar un paño blanco delante de las bandas pétreas de la torre.
    profundidad=8.75
    nave=recortar_interior(e['huella'],frente,-profundidad)
    prisma_seguro(c,nave,zb,z+10.2,'muro',BLANCO)
    # Ala de la portada principal: en las fotos avanza hasta el frente del
    # museo; no comparte el retranqueo de la portada interior del atrio.
    from museo_codex import huellas_ala,avance_museo
    avance=avance_museo()
    for ala in huellas_ala():
        prisma_seguro(c,ala,zb,z+10.2,'muro',BLANCO)
    # huella real del objeto = Catedral + ala de la portada (claude 2026-11-14: con la huella sola de E03fe1d el
    # recorte a medianeras borraba los muros del ala y su cubierta quedaba flotando)
    from shapely.geometry import Polygon as _Pg
    from shapely.ops import unary_union as _uu
    _u=_uu([_Pg(e['huella'])]+[_Pg(a) for a in huellas_ala()]).buffer(0.05).buffer(-0.05)
    if _u.geom_type=='Polygon':
        c.huella=[tuple(p) for p in _u.exterior.coords][:-1]

    patio=[frente.punto(ss,0,d) for ss,d in
           ((0,0),(frente.largo,0),(frente.largo,-profundidad),(0,-profundidad))]
    # Triángulos para respetar el desnivel sin un polígono no plano.
    pts=[(p.x,p.y,altura_suelo(p.x,p.y)+.14) for p in patio]
    for ids in ((0,1,2),(0,2,3)):
        c.poligono([pts[i] for i in ids],'piedra','#cab394')
    f=Fachada(c,ls[2],z)
    zocalo(f,.4,s1=16.5,color='#d8c8b5',desde=zb-z)
    zocalo(f,.4,s0=18.5,color='#d8c8b5',desde=zb-z)
    for s in (3.2,6.3,9.4): ventana(f,s,4.6,ancho=1.15,alto=1.9,reja=True)
    for s in (15.7,19.3): ventana(f,s,4.6,ancho=1.25,alto=2.0,arco=True,reja=True)
    balcon_corrido(f,14.5,20.6,4.5)
    pie=f.punto(17.5,0)
    fp=trasladar(f,h=altura_suelo(pie.x,pie.y)+.08-z)
    puerta(fp,17.5,alto=3.0,arco=True)
    cornisa(f,10.0,alto=.2)
    balaustrada(f,10.2)
    # Costado hacia la plaza (130741): dos ventanas y portada lateral.
    lateral=Fachada(c,ls[0],z)
    for ss in (12.5,21.5):
        ventana(lateral,ss,4.5,ancho=1.3,alto=2.5,reja=True)
        lateral.arco(ss,1.0,.12,7.1,0,.15,'moldura',segmentos=12)
    for ss in (8.1,17,26):
        pilastra(lateral,ss,0,10.2,ancho=.5,rol='piedra',color=PIEDRA)
    cornisa(lateral,10,alto=.2)
    balaustrada(lateral,10.2,s0=8)
    pie=lateral.punto(30.8,0)
    portada(trasladar(lateral,h=altura_suelo(pie.x,pie.y)+.12-z),30.8,ancho=7.0,iconografia=True)
    # Frente Nicolás Ortiz: portadas en los dos tramos salientes.
    for idx in (10,12):
        g=Fachada(c,ls[idx],z)
        if idx==12:g=trasladar(g,d=-profundidad)
        else:g=trasladar(g,d=profundidad+avance)
        pie=g.punto(g.largo/2,0)
        g=trasladar(g,h=altura_suelo(pie.x,pie.y)+.12-z)
        portada(g,g.largo/2,ancho=min(8.2,g.largo-.5),alto=14 if idx==10 else 12)
    # Claristorio del paño retranqueado: dos vanos sobre la portada (130853).
    g=trasladar(Fachada(c,ls[12],z),d=-profundidad)
    g.caja(0,g.largo,10.15,13.0,-.4,0,'muro',BLANCO)
    for ss in (3.2,9.2):
        ventana(g,ss,10.8,ancho=1.25,alto=.9,reja=True)
        g.arco(ss,1.15,.15,11.7,0,.12,'moldura',BLANCO,segmentos=12)
    cornisa(g,13.0,alto=.2,color=BLANCO)
    balaustrada(g,13.2)
    # Atrio de la fachada (claude, 2026-11-14, fotos 130844–130851): el muro de sillería con balaustrada va sobre la
    # línea de la vereda de Nicolás Ortiz (en el lienzo quedaba 14 m adentro, sobre la huella), con un portón de
    # hierro frente a cada portada y la vuelta hacia la Catedral en el extremo SO.
    from piezas_claude import cerramiento_atrio, tramo_calle, sobre_calle, esquina_atrio_ortiz
    ca=Constructor('M055_atrio_ortiz')     # objeto propio: el recorte a la huella de E03fe1d lo borraría
    ortiz=tramo_calle("Calle Nicolás Ortiz",(-200.0,-320.0))
    w_=ortiz["ancho"]/2
    def _t(pt):
        (x0,y0),(x1,y1)=ortiz["eje"][0],ortiz["eje"][-1]; L_=math.hypot(x1-x0,y1-y0)
        return ((pt[0]-x0)*(x1-x0)+(pt[1]-y0)*(y1-y0))/L_
    t_ini=_t(ls[10]['a'])
    # hasta la esquina con la plaza (R0169: el muro tiene que cerrar contra el pilar de la cruz de M056)
    t_fin,_esq,_=esquina_atrio_ortiz(ls[12]['a'])
    lado_cal=1 if ((ls[12]['a'][0]-ortiz["eje"][0][0])*-(ortiz["eje"][-1][1]-ortiz["eje"][0][1])+(ls[12]['a'][1]-ortiz["eje"][0][1])*(ortiz["eje"][-1][0]-ortiz["eje"][0][0]))>0 else -1
    pa_=sobre_calle(ortiz,t_ini,lado_cal*w_)[:2]; pb_=sobre_calle(ortiz,t_fin,lado_cal*w_)[:2]
    ux_,uy_=(pb_[0]-pa_[0]),(pb_[1]-pa_[1]); Lw=math.hypot(ux_,uy_)
    nrm=(-ls[12]['normal'][0]*-1,-ls[12]['normal'][1]*-1)          # hacia la calle
    lf={'a':pa_,'b':pb_,'normal':nrm} if (ux_*nrm[1]-uy_*nrm[0])>0 else {'a':pb_,'b':pa_,'normal':nrm}
    fw=Fachada(ca,lf,altura_suelo(*pa_)+.12)
    s_de=lambda pt:((pt[0]-lf['a'][0])*(lf['b'][0]-lf['a'][0])+(pt[1]-lf['a'][1])*(lf['b'][1]-lf['a'][1]))/Lw
    medio=lambda l:((l['a'][0]+l['b'][0])/2,(l['a'][1]+l['b'][1])/2)
    def s_frente(l):
        # el portón va donde la normal de la portada (centro del lado) corta el cerramiento, no en la proyección
        # perpendicular al cerramiento: los dos no son paralelos y el portón quedaba corrido, tapando media puerta
        # verde con muro (revisión del usuario, 2026-11-24)
        m_=medio(l); n_=l['normal']; a_=lf['a']; ex,ey=(lf['b'][0]-a_[0])/Lw,(lf['b'][1]-a_[1])/Lw
        den=n_[0]*(-ey)+n_[1]*ex
        if abs(den)<1e-6: return s_de(m_)
        t_=((m_[0]-a_[0])*ey-(m_[1]-a_[1])*ex)/den
        return s_de((m_[0]+n_[0]*t_,m_[1]+n_[1]*t_))
    cerramiento_atrio(ca,fw,puertas=(s_frente(ls[10]),s_frente(ls[12])),color=PIEDRA)
    # vuelta hacia la Catedral en el extremo SO
    ext=pa_ if math.dist(pa_,ls[10]['a'])<math.dist(pb_,ls[10]['a']) else pb_
    dx_,dy_=ls[10]['a'][0]-ext[0],ls[10]['a'][1]-ext[1]; Lv=math.hypot(dx_,dy_)
    nv=(dy_/Lv,-dx_/Lv)
    if nv[0]*ux_/Lw+nv[1]*uy_/Lw>0: nv=(-nv[0],-nv[1])
    lv={'a':ext,'b':ls[10]['a'],'normal':nv} if (dx_*nv[1]-dy_*nv[0])>0 else {'a':ls[10]['a'],'b':ext,'normal':nv}
    cerramiento_atrio(ca,Fachada(ca,lv,altura_suelo(*ext)+.12),color=PIEDRA)
    ca.objeto(col)
    # Torre asentada dentro de la esquina oriental de la huella.
    g=Fachada(c,ls[14],z)
    ancho=7.7
    origen=g.punto(g.largo/2,0,-4.05)
    z=altura_suelo(origen.x,origen.y)+.12
    for nivel,(h0,h1,w) in enumerate(((0,14.5,ancho),(14.5,20.1,6.7),(20.1,24.5,5.7),(24.5,27.1,4.9))):
        pts=[tuple(origen+g.u*a+g.n*b)[:2] for a,b in ((-w/2,-w/2),(w/2,-w/2),(w/2,w/2),(-w/2,w/2))]
        if nivel not in (1,2):
            c.prisma(pts,zb if nivel==0 else z+h0,z+h1,'muro',BLANCO)
        else:
            c.tapa(pts,z+h0,'piedra',PIEDRA)
        # Lados de la torre: no necesitan detección de calles del mapa.
        contorno = datos.orientar_ccw(pts)
        for a,b in zip(contorno,contorno[1:]+contorno[:1]):
            dx,dy=b[0]-a[0],b[1]-a[1]
            largo=math.hypot(dx,dy)
            l={'a':a,'b':b,'normal':(dy/largo,-dx/largo)}
            t=Fachada(c,l,z)
            for s in (.5,w-.5): pilastra(t,s,h0,h1,ancho=1.0,rol='piedra',color=PIEDRA)
            cornisa(t,h1-.4,color=BLANCO)
            if nivel==0:
                for h in (4,8,12):
                    imposta(t,h,alto=.45,vuelo=.11,rol='piedra',color=PIEDRA)
                    juntas(trasladar(t,d=.12),h,h+.45,0,w,paso=.45)
                for a,b in ((0,1.0),(w-1.0,w)):
                    juntas(trasladar(t,d=.12),0,h1,a,b,paso=.65)
                pilastra(t,w/2,0,h1,ancho=.26,rol='piedra',color=PIEDRA)
            elif nivel in (1,2):
                campanario(t,h0,h1-.5)
                balaustrada(t,h0)
            else:
                c.poligono([t.punto(w/2-1.7,h1-.4,.16),
                            t.punto(w/2+1.7,h1-.4,.16),
                            t.punto(w/2,h1+.6,.16)],'moldura',BLANCO,
                           grosor=.12,normal_extrusion=t.n)
                for k in range(12):
                    ang=k*math.tau/12
                    ss=w/2+.63*math.sin(ang); hh=h0+1.2+.63*math.cos(ang)
                    t.caja(ss-.025,ss+.025,hh-.07,hh+.07,.08,.11,'hierro')
                t.arco(w/2,.75,.12,h0+1.2,0,.08,'moldura',medio=False,segmentos=24)
                t.caja(w/2-.035,w/2+.035,h0+.7,h0+1.6,.08,.11,'hierro')
                t.caja(w/2-.02,w/2+.5,h0+1.17,h0+1.23,.08,.11,'hierro')
    c.cilindro(origen.x,origen.y,z+27.1,z+29.2,2.4,'teja','#bd8c73',lados=4,radio_arriba=.3)
    c.caja(origen.x-.05,origen.y-.05,z+29,origen.x+.05,origen.y+.05,z+30,'hierro')
    c.caja(origen.x-.35,origen.y-.05,z+29.65,origen.x+.35,origen.y+.05,z+29.73,'hierro')
    # Santos en las esquinas de las terrazas, visibles en 130838/130857.
    for hh,w in ((14.5,7.7),(20.1,6.7),(27.1,4.9)):
        for aa,bb in ((-1,-1),(-1,1),(1,-1),(1,1)):
            p=origen+g.u*(aa*(w/2-.3))+g.n*(bb*(w/2-.3))
            imagen_sacra(c,p.x,p.y,z+hh,alto=1.15 if hh<27 else .95)
    c.objeto(col)

# Árboles podados de vereda, documentados en 130715 y 130736.
# Sus pies se apoyan en el terreno; las veredas se mantienen en BASE.
for eid,indice,posiciones in (
    ('E2c6601',0,(2.2,7.4,12.0,22.0,27.2,32.0)),
    ('E03fe1d',2,(2.5,7.4,12.0,17.8,21.4)),
):
    e=edificio(MANZANA,eid)
    f=Fachada(None,lados(e['huella'])[indice],0)
    for k,ss in enumerate(posiciones):
        # junto al BORDILLO (R0107/R0109: "los árboles de vereda siempre cerca del borde de la acera")
        p=f.punto(ss,0,0)
        x,y=junto_al_bordillo(p.x,p.y,f.n.x,f.n.y,retiro=.7)
        arbol_podado(f'M055_arbol_{eid}_{k}',x,y,col,
                     radio=1.3,direccion=tuple(f.n[:2]))
# Farol documentado junto al portón del atrio (130853).
e=edificio(MANZANA,'E03fe1d')
f=Fachada(None,lados(e['huella'])[12],0)
p=f.punto(2.8,0,.6)
farol_pie('M055_farol_atrio_0',p.x,p.y,col,alto=3.5)

from dalence_codex import mobiliario_dalence
mobiliario_dalence(MANZANA,col)
suelo_frente_institucional(col)
cubiertas_catedral(col)
exportar(AGENTE,MANZANA)
# Selección explícita para iterar; ampliar antes de dar la manzana por terminada.
if '--sin-render' not in sys.argv:
    revisar(AGENTE,MANZANA,fotos=['IMG_20261105_'+n+'.jpg' for n in ('130715','130736','130840')],ancho=1000,alto=750)
