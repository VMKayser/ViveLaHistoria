"""R0025 — Rectorado, inventario contado en INVENTARIO_JUNIN.md.
Chaflán de tres ejes, portada y escalinata dentro del lote; tercer cuerpo
retranqueado. Alas sin foto completa: se conserva su extensión recortada.
"""
import math
from kit import *
from piezas_codex import prisma_seguro,trasladar,recortar_interior,recorte_estricto,rama
from frentes_codex import frente_real,farol_muro,roseta,columna_tallada
from detalles_plaza_codex import balustrada
BLANCO='#eeeae3';MOLDURA='#f3eee4';ROJO='#9b6955';MADERA='#48372e'


def construir_rectorado(e,col):
    c=Constructor(e['id']);original=e['huella'];ls=lados(original)
    ch=min(ls,key=lambda l:abs(l['normal'][0]+1)+abs(l['normal'][1]+.08))
    marco=Fachada(c,ch,0);p=marco.punto(marco.largo/2,0)
    z=altura_suelo(p.x,p.y)+1.25
    h=recorte_estricto(recortar_interior(original,marco,-2.1))
    zmin=min(altura_suelo(*p) for p in original)-.5
    prisma_seguro(c,h,zmin,z+9.8,'muro',BLANCO)
    # Chaflán real del cuerpo retirado: no se decora sobre el lado anterior.
    f,g=frente_real({'id':e['id'],'huella':h},c,z,normal=ch['normal'])
    L=f.largo;s=L/2
    # Pilastras laterales y dos ventanas que flanquean la portada.
    for ss in (L*.12,L*.88):
        ventana(trasladar(f,d=.03),ss,.9,ancho=1.12,alto=2.9,reja=True,color_moldura=MOLDURA,color_carpinteria='#403c37')
        ventana(trasladar(f,d=.03),ss,5.1,ancho=1.17,alto=2.25,color_moldura=MOLDURA,color_carpinteria='#403c37')
        cornisa(f,7.6,s0=ss-.85,s1=ss+.85,alto=.12,vuelo=.25,color=MOLDURA)
        for ds in (-.7,.7):pilastra(f,ss+ds,.5,8.5,ancho=.15,vuelo=.10,color=MOLDURA)
        for j in (-1,0,1):roseta(f,ss+j*.22,7.98,.09,color=MOLDURA)
    # Portada central: columnas dobles continuas y arcos de piedra encalada.
    puerta(trasladar(f,d=.04),s,ancho=2.45,alto=3.1,arco=True,color=MADERA,color_moldura=MOLDURA)
    for ds in (-2.05,-1.6,1.6,2.05):
        f.caja(s+ds-.27,s+ds+.27,0,.65,-.02,.4,'moldura',MOLDURA)
        columna_tallada(f,s+ds,.65,4.25,.15,.23,color=MOLDURA)
        columna_tallada(f,s+ds,4.9,8.5,.13,.21,color=MOLDURA)
    for rr in (1.45,1.67):f.arco(s,rr,.13,3.1,-.02,.25,'moldura',MOLDURA,segmentos=24)
    for k in range(17):
        a=k*math.pi/16
        rama(c,f.punto(s+.22*math.cos(a),3.12+.22*math.sin(a),.13),
             f.punto(s+1.22*math.cos(a),3.12+1.22*math.sin(a),.13),.015,.015,'hierro','#342f29')
    ventana(trasladar(f,d=.04),s,5.1,ancho=1.55,alto=2.35,arco=True,color_carpinteria='#393c3a',color_moldura=MOLDURA)
    # Guirnaldas de las jambas y ménsulas bajo los balconcillos.
    for ds in (-2.65,2.65):
        for hh in (.95,1.6,2.25,2.9,5.4,6.15,6.9,7.65):
            roseta(f,s+ds,hh,.10,color=MOLDURA)
    f.arco(s,.2,.025,3.12,.11,.16,'hierro','#342f29',segmentos=16)
    for i in range(4):
        for j in range(4):
            ss=s-.91+i*.60;hh=.28+j*.66
            for a,b,h0,h1 in ((ss-.23,ss+.23,hh,hh+.035),(ss-.23,ss+.23,hh+.49,hh+.525),
                              (ss-.23,ss-.195,hh,hh+.525),(ss+.195,ss+.23,hh,hh+.525)):
                f.caja(a,b,h0,h1,.10,.14,'madera','#5c4834')
    f.caja(s-1.65,s+1.65,4.95,5.08,-.1,.42,'moldura',MOLDURA)
    for hh in (4.5,8.8,9.45):cornisa(f,hh,alto=.20,vuelo=.33,color=MOLDURA)
    # Frontón mixtilíneo sostenido sobre la cornisa, con rosetón ocre.
    ancho=min(L*.84,8.8);n=40
    for k in range(n):
        a=-ancho/2+k*ancho/n;b=a+ancho/n
        def cima(x):return 9.7+1.62*math.exp(-(x/1.05)**2)+.5*math.exp(-((abs(x)-2.1)/.55)**2)
        pa,pb=f.punto(s+a,cima(a),.13),f.punto(s+b,cima(b),.13)
        c.poligono([f.punto(s+a,9.45,-.15),f.punto(s+b,9.45,-.15),
                    f.punto(s+b,cima(b),-.15),f.punto(s+a,cima(a),-.15)],'muro',BLANCO,grosor=.28,normal_extrusion=f.n)
        rama(c,pa,pb,.065,.065,'moldura',MOLDURA)
    f.c.poligono([f.punto(s+.50*math.cos(k*math.tau/32),10.36+.5*math.sin(k*math.tau/32),.16) for k in range(32)],'pintura_acento','#b48b4a')
    f.arco(s,.54,.09,10.36,.14,.24,'moldura',MOLDURA,medio=False,segmentos=24)
    for k in range(12):
        a=k*math.tau/12
        rama(c,f.punto(s,10.36,.23),f.punto(s+.44*math.cos(a),10.36+.44*math.sin(a),.23),.012,.012,'pintura_acento','#dfbf78')
    # Ocho peldaños en abanico recortados dentro de la propiedad.
    for k in range(8):
        d0=-.28*k;d1=-.28*(k+1)-.02
        w=marco.largo-.20*k;ss=marco.largo/2
        hh=[tuple(marco.punto(a,0,d)[:2]) for a,d in ((ss-w/2,d0),(ss+w/2,d0),(ss+w/2,d1),(ss-w/2,d1))]
        hh=recorte_estricto(datos.recortar_a_calles(hh,area_min=.1))
        prisma_seguro(c,hh,z-1.45,z-1.25+(k+1)*1.25/8,'piedra','#9d8d78')
    # Alas: los lados físicos de la huella nueva dan continuidad al chaflán.
    for l in lados(h):
        if not l['a_calle'] or l['largo']<15:continue
        ff=Fachada(c,l,z);N=8 if l['normal'][0]<-.7 else 9;paso=ff.largo/N
        for k in range(N):
            ss=(k+.5)*paso;w=min(1.25,paso*.52)
            ventana(trasladar(ff,d=.03),ss,.9,ancho=w,alto=2.9,reja=True,color_moldura=MOLDURA)
            ventana(trasladar(ff,d=.03),ss,5.0,ancho=w,alto=2.5,arco=l['normal'][0]<-.7,color_moldura=MOLDURA)
            balcon_hierro(ff,ss-.78,ss+.78,5.0,vuelo=.45)
            for ds in (-.85,.85):pilastra(ff,ss+ds,4.8,8.4,ancho=.16,color=MOLDURA)
        for hh in (4.4,8.8,9.5):cornisa(ff,hh,alto=.17,vuelo=.27,color=MOLDURA)
        zocalo(ff,.15,desde=zmin-z,rol='zocalo_piedra',color=ROJO,sillares=True)
    # Tercer cuerpo de la esquina, retirado cuatro metros tras el frontón.
    alto_h=[tuple(f.punto(a,0,d)[:2]) for a,d in ((0,-1.8),(L,-1.8),(L,-7.8),(0,-7.8))]
    alto_h=recorte_estricto(datos.recortar_a_calles(alto_h))
    prisma_seguro(c,alto_h,z+9.75,z+14.2,'muro',BLANCO)
    t=trasladar(f,d=-1.8)
    for k in range(3):
        centro=(k+.5)*L/3
        for ds in (-.48,.48):ventana(trasladar(t,d=.025),centro+ds,10.5,ancho=.72,alto=2.5,arco=True,color_moldura=MOLDURA)
    cornisa(t,14.0,alto=.25,vuelo=.32,color=MOLDURA)
    balustrada(t,.1,L-.1,14.35,d=-.12)
    for k in range(6):
        ss=k*L/5
        t.caja(ss-.14,ss+.14,14.2,15.75,-.35,.10,'moldura',MOLDURA)
        p=t.punto(ss,15.75,-.12)
        c.cilindro(p.x,p.y,p.z,p.z+.30,.19,'moldura',MOLDURA,lados=4,radio_arriba=.015)
    farol_muro(f,.45,4.35);farol_muro(f,L-.45,4.35)
    c.objeto(col)
    return [f]
