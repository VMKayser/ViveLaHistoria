"""M075, esquina NE con mirador que aparece enfrente en R0095.
No es la casona SUR de AMP_S. Inventario: INVENTARIO_M075.md.
Huella propia ampliada desde el lienzo interior y recortada por ambas calles.
"""
import math
from kit import *
from mathutils import Vector
from piezas_codex import prisma_seguro,recorte_estricto,trasladar,ventana_rebajada
from casas_codex import _cortar,cubierta_baja
from dalence_codex import decorar
from frentes_codex import frente_real,roseta
from varillas_codex import rama
from balcon_verde_codex import balcon_verde
BLANCO='#eeeae3';CREMA='#e1d7c6';MADERA='#784333';PIEDRA='#b59b79';HIERRO='#354239'
MIRADA_R0095=(-254,-389,67.0,14.0)


def huella_casona():
    x=Vector((-257.73,-402.35));n=Vector((.65,.76)).normalized();d=Vector((.75,-.66)).normalized()
    h=[tuple(p) for p in (x,x+n*17,x+n*17+d*15,x+d*15)]
    h=recorte_estricto(datos.recortar_a_calles(h))
    # Ochava corta de la esquina blanca, con medallón y cornisa que dobla.
    return _cortar(h,(min(p[0] for p in h),0),(1,0),1.05,1)


def comprobar_vecinos(h):
    """La ampliación fotográfica no puede ocupar otra huella del reparto."""
    borde=datos.orientar_ccw(h);probadas=0
    for m in datos.reparto()['manzanas']:
        if m['id']=='M075':continue
        for e in m['edificios']:
            p=[tuple(v) for v in e['huella']]
            if max(v[0] for v in p)<min(v[0] for v in h) or min(v[0] for v in p)>max(v[0] for v in h) or max(v[1] for v in p)<min(v[1] for v in h) or min(v[1] for v in p)>max(v[1] for v in h):continue
            probadas+=1
            for a,b in zip(borde,borde[1:]+borde[:1]):
                p=_cortar(p,a,(-(b[1]-a[1]),b[0]-a[0]),0,1)
                if len(p)<3:break
            area=abs(datos._area(p)) if len(p)>2 else 0
            assert area<.05,('Ampliación ocupa huella vecina',m['id'],e['id'],area)
    print('[M075] Solapes con huellas vecinas: 0;',probadas,'candidatas comprobadas',flush=True)


def mirador_madera(f,s,h=4.55,w=3.6,H=2.70):
    a,b=s-w/2,s+w/2;vuelo=.72
    # Caja con antepecho macizo y montantes, sobre cuatro ménsulas.
    f.caja(a,b,h,h+.65,.015,vuelo,'madera',MADERA)
    f.caja(a,b,h+.65,h+H,.015,vuelo,'vidrio','#adb9ae')
    for hh in (h-.10,h,h+.65,h+1.3,h+2.0,h+H):f.caja(a-.04,b+.04,hh,hh+.065,.005,vuelo+.045,'marco_ventana',MADERA)
    for j in range(6):
        ss=a+j*w/5
        f.caja(ss-.035,ss+.035,h+.60,h+H,.005,vuelo+.05,'marco_ventana',MADERA)
        f.caja(ss-.02,ss+.02,h+.09,h+.56,vuelo+.002,vuelo+.025,'madera','#8b523b')
    # Dos paños en cada costado: divisiones de profundidad además del frente.
    for ss in (a,b):
        for dd in (0,vuelo*.5,vuelo):f.caja(ss-.045,ss+.045,h+.60,h+H,dd-.025,dd+.025,'marco_ventana',MADERA)
    for j in range(4):
        ss=a+.35+j*(w-.7)/3
        f.caja(ss-.08,ss+.08,h-.65,h,.005,.16,'madera','#644130')
        rama(f.c,f.punto(ss,h-.65,.06),f.punto(ss,h-.03,vuelo-.06),.065,.065,'madera','#644130')
    for ss in (a,b):
        f.caja(ss-.08,ss+.08,h-.07,h+H+.10,.005,vuelo+.075,'marco_ventana','#643a2b')
    # El pequeño tejado del mirador se apoya en la cabeza del marco.
    alero_tejas(trasladar(f,d=vuelo),h+H+.07,s0=a-.12,s1=b+.12,vuelo=.12,fondo=.9,canes=True)

def pinaculo(f,s):
    f.caja(s-.14,s+.14,9.30,9.55,-.25,.025,'moldura',CREMA)
    p=f.punto(s,9.55,-.10)
    f.c.cilindro(p.x,p.y,p.z,p.z+.35,.12,'moldura',CREMA,lados=6,radio_arriba=.04)
    f.c.esfera(p.x,p.y,p.z+.35,.075,'moldura',CREMA,segmentos=6)

def frente_ortiz(f):
    L=f.largo
    zocalo(f,1.25,desde=-.8,color=PIEDRA)
    # Un balcón fino al extremo de la calle, mirador junto a la esquina.
    ss=L*.20
    ventana_rebajada(f,ss,5.05,ancho=1.25,alto=2.25,color_carpinteria=MADERA,color_moldura=CREMA,panel=True)
    balcon_verde(f,ss,4.95,ancho=1.65)
    puerta(trasladar(f,h=.08,d=.07),ss,ancho=1.65,alto=2.75,arco=True,color='#59382b',color_moldura=PIEDRA)
    ms=L*.66
    mirador_madera(f,ms,w=min(3.6,L*.40))
    ventana(f,ms,1.55,ancho=1.4,alto=2.0,reja=True,color_carpinteria=MADERA,color_moldura=CREMA)
    cornisa(f,4.25,alto=.20,vuelo=.20,color=CREMA)
    cornisa(f,8.55,alto=.35,vuelo=.30,color=CREMA)
    parapeto(f,8.90,alto=.45,color=BLANCO)
    for s in (.25,L*.48,L-.25):pinaculo(f,s)

def retorno_dalence(f):
    zocalo(f,1.25,desde=-.8,color=PIEDRA)
    for j,ss in enumerate((f.largo*.18,f.largo*.52,f.largo*.84)):
        if j==1:mirador_madera(f,ss,w=min(2.7,f.largo*.28),H=2.5)
        else:
            ventana_rebajada(f,ss,5.05,ancho=1.2,alto=2.25,color_carpinteria=MADERA,color_moldura=CREMA,panel=True)
            balcon_verde(f,ss,4.95,ancho=1.55)
        if j==0:puerta(trasladar(f,h=.08,d=.07),ss,ancho=1.45,alto=3.05,color=MADERA,color_moldura=CREMA)
        else:ventana(f,ss,1.55,ancho=1.15,alto=2.05,reja=True,color_carpinteria=MADERA,color_moldura=CREMA)
    cornisa(f,4.25,alto=.20,vuelo=.20,color=CREMA)
    cornisa(f,8.55,alto=.35,vuelo=.30,color=CREMA)
    parapeto(f,8.90,alto=.45,color=BLANCO)
    for ss in (.25,f.largo*.43,f.largo*.77,f.largo-.25):pinaculo(f,ss)


def construir_casona(e,col):
    h=huella_casona();comprobar_vecinos(h);c=Constructor(e['id']+'_detalles');masa=Constructor(e['id'])
    fn,gn=frente_real({'huella':h},c,normal=(-.76,.65))
    p=fn.punto(fn.largo/2,0);z=altura_suelo(p.x,p.y)
    from parcelas_codex import volumen_colonial
    from triangulacion_codex import triangular_huella
    plan={'principal':h,'anillos':[h],'piezas':[list(t) for t in triangular_huella(h)]}
    volumen_colonial(masa,plan,min(altura_suelo(*p) for p in h)-.4,z+8.75,BLANCO,'#a45b41',altura_cubierta_max=.60)
    masa.objeto(col,huella=h);c.huella=h
    decorar(c,h,z,(-.76,.65),frente_ortiz)
    decorar(c,h,z,(-.65,-.76),retorno_dalence)
    l=min(lados(h),key=lambda l:l['a'][0]+l['b'][0])
    f=Fachada(c,l,z);s=f.largo/2
    zocalo(f,1.25,desde=-.8,color=PIEDRA)
    cornisa(f,4.25,alto=.20,vuelo=.20,color=CREMA)
    cornisa(f,8.55,alto=.35,vuelo=.30,color=CREMA)
    parapeto(f,8.90,alto=.45,color=BLANCO)
    f.timpano_arco(s,.60,9.1,.025,'muro',BLANCO)
    f.arco(s,.60,.10,9.1,.025,.13,'moldura',CREMA,segmentos=18)
    roseta(f,s,9.43,.23,d=.14,color=CREMA)
    c.objeto(col)
    return [fn]
