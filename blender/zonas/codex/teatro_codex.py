"""Teatro 3 de Febrero, 130452/130521. INVENTARIO_REPASO.md.
Once ejes, tres accesos; relieve gris y blanco y portal principal ancho.
El datum sigue las cotas de Arenales para conservar el zócalo de 1,1 m.
"""
import math
from mathutils import Vector
from kit import *
from piezas_codex import prisma_seguro,trasladar,ventana_arco_reja
from frentes_codex import roseta,farol_muro,frente_de_calle
from detalles_plaza_codex import ajustar_fachada
BLANCO='#eeeae7';GRIS='#747b7f';BALAU='#555c60';MADERA='#50362a'


def rama(c,a,b,r0=.07,r1=.035,rol='tronco',color=None):
    """Varilla de cuatro caras, sin un operador BMesh por cada letra/radio."""
    a,b=Vector(a),Vector(b);t=b-a
    if t.length<.001:return
    t.normalize();u=t.cross(Vector((0,0,1)))
    if u.length<.01:u=t.cross(Vector((0,1,0)))
    u.normalize();v=t.cross(u);radios=(u,v,-u,-v)
    aa=[a+q*r0 for q in radios];bb=[b+q*r1 for q in radios]
    for j in range(4):c.poligono([aa[j],aa[(j+1)%4],bb[(j+1)%4],bb[j]],rol,color)
    c.poligono(list(reversed(aa)),rol,color);c.poligono(bb,rol,color)


def fronton(f,s,h,w):
    f.c.poligono([f.punto(s-w/2,h,.11),f.punto(s+w/2,h,.11),f.punto(s,h+.65,.11)],
                 'moldura',BLANCO,grosor=.12,normal_extrusion=f.n)
    f.c.poligono([f.punto(s-w*.37,h+.12,.24),f.punto(s+w*.37,h+.12,.24),
                  f.punto(s,h+.49,.24)],'muro',GRIS)
    cornisa(f,h-.12,s0=s-w/2,s1=s+w/2,alto=.13,vuelo=.3,color=BLANCO)
    f.caja(s-.13,s+.13,h-.20,h+.25,.25,.4,'moldura',BLANCO)
    # Dos pequeños apoyos blancos bajo el tímpano.
    for ds in (-.24,.24):f.caja(s+ds-.07,s+ds+.07,h-.03,h+.21,.17,.29,'moldura',BLANCO)


def antepecho(f,s,h):
    for hh in (h,h+.70):f.caja(s-.83,s+.83,hh,hh+.11,-.015,.24,'moldura',BLANCO)
    perfil=((0,.06),(.10,.04),(.24,.09),(.36,.095),(.49,.04),(.60,.055))
    for k in range(6):
        ss=s-.65+k*.26
        for (h0,r0),(h1,r1) in zip(perfil,perfil[1:]):
            for j in range(6):
                a=j*math.tau/6;b=(j+1)*math.tau/6
                f.c.poligono([f.punto(ss+r0*math.cos(a),h+.10+h0,.10+r0*math.sin(a)),
                  f.punto(ss+r0*math.cos(b),h+.10+h0,.10+r0*math.sin(b)),
                  f.punto(ss+r1*math.cos(b),h+.10+h1,.10+r1*math.sin(b)),
                  f.punto(ss+r1*math.cos(a),h+.10+h1,.10+r1*math.sin(a))],'piedra',BALAU)
    for ds in (-.78,.78):f.caja(s+ds-.065,s+ds+.065,h,h+.8,-.02,.25,'moldura',BLANCO)


def dovelas(f,s,r,arranque):
    # Junta blanca en torno a cada dovela gris del arco del portón.
    f.arco(s,r,.26,arranque,.01,.13,'moldura',BLANCO,segmentos=24)
    for j in range(11):
        a=j*math.pi/11+.016;b=(j+1)*math.pi/11-.016
        f.c.poligono([f.punto(s+r*math.cos(a),arranque+r*math.sin(a),.14),
          f.punto(s+r*math.cos(b),arranque+r*math.sin(b),.14),
          f.punto(s+(r+.22)*math.cos(b),arranque+(r+.22)*math.sin(b),.14),
          f.punto(s+(r+.22)*math.cos(a),arranque+(r+.22)*math.sin(a),.14)],
          'pintura_acento',GRIS,grosor=.025,normal_extrusion=-f.n)


# Letras dibujadas aquí con trazos propios: sin fuentes ni recursos externos.
GLIFOS={
 'T':(((0,1),(.6,1)),((.3,1),(.3,0))),
 'E':(((.6,1),(0,1),(0,0),(.6,0)),((0,.5),(.48,.5))),
 'A':(((0,0),(.3,1),(.6,0)),((.13,.4),(.47,.4))),
 'R':(((0,0),(0,1),(.45,1),(.6,.8),(.45,.55),(0,.55)),((.25,.55),(.65,0))),
 'O':(((.15,0),(0,.18),(0,.82),(.15,1),(.45,1),(.6,.82),(.6,.18),(.45,0),(.15,0)),),
 'D':(((0,0),(0,1),(.36,1),(.6,.75),(.6,.25),(.36,0),(0,0)),),
 'F':(((0,0),(0,1),(.6,1)),((0,.52),(.48,.52))),
 'B':(((0,0),(0,1),(.4,1),(.6,.8),(.4,.52),(0,.52)),((.4,.52),(.6,.25),(.4,0),(0,0))),
 '3':(((0,1),(.45,1),(.6,.8),(.35,.52),(.6,.27),(.45,0),(0,0)),),
}


def letras(f,texto,s,h,alto=.15):
    inicio=s-(len(texto)*.8-.2)*alto/2
    for i,letra in enumerate(texto):
        for trazo in GLIFOS.get(letra,()):
            for a,b in zip(trazo,trazo[1:]):
                rama(f.c,f.punto(inicio+(i*.8+a[0])*alto,h+a[1]*alto,.045),
                     f.punto(inicio+(i*.8+b[0])*alto,h+b[1]*alto,.045),
                     alto*.055,alto*.055,'letrero','#48392f')


def decorar(f,zb,principal):
    n=11 if principal else max(1,round(f.largo/4.7));paso=f.largo/n
    puertas={2,6,10} if principal else set();main=paso*(n-.5)
    for k in range(n):
        ss=(k+.5)*paso
        if k in puertas:
            w,arr=(3.0,2.45) if k==10 else (1.9,3.15)
            puerta(trasladar(f,h=.12,d=.025),ss,ancho=w,alto=arr,arco=True,
                   color=MADERA,color_moldura=GRIS)
            dovelas(f,ss,w/2,arr+.12)
            for signo in (-1,1):
                for hh in (.45,1.15,1.85):
                    x=ss+signo*w*.24
                    f.caja(x-w*.19,x+w*.19,hh,hh+.48,.085,.115,'madera','#604334')
        else:
            ventana_arco_reja(f,ss,1.35,ancho=1.35,alto=3.0,color_moldura=GRIS)
            if principal:
                arranque=1.35+3.0-.675
                for r in (.55,.39):f.arco(ss,r,.015,arranque,.11,.14,'hierro','#343832',segmentos=8)
                for j in range(9):
                    a=j*math.pi/8
                    rama(f.c,f.punto(ss,arranque,.13),
                         f.punto(ss+.54*math.cos(a),arranque+.54*math.sin(a),.13),
                         .010,.010,'hierro','#343832')
        # Recuadros horizontales a los lados de los huecos.
        for hh in (1.5,2.1,2.7,3.3,3.9,5.4,6.0,6.6,7.2,7.8,8.4,9.0):
            ancho=1.75 if k==10 and principal else 1.05
            for a,b in ((k*paso+.55,ss-ancho),(ss+ancho,(k+1)*paso-.55)):
                if b>a:f.caja(a,b,hh,hh+.025,.01,.04,'moldura',BLANCO)
        a,b=k*paso,(k+1)*paso
        if k in puertas:
            radio=1.75 if k==10 else 1.15
            tramos=((a,ss-radio),(ss+radio,b))
        else:tramos=((a,b),)
        for p,q in tramos:
            if q>p:zocalo(f,1.1,s0=p,s1=q,desde=zb-f.suelo,color='#92978e',sillares=False)
        ventana(f,ss,5.0,ancho=1.45,alto=2.55,color_moldura=GRIS,color_carpinteria='#654334')
        antepecho(f,ss,4.9);fronton(f,ss,8.0,2.1)
        for hh in (4.5,8.9):
            if not (principal and k==10 and hh==4.5):
                f.caja(ss-1.2,ss+1.2,hh,hh+.14,.04,.07,'pintura_acento',GRIS)
    for k in range(n+1):
        ss=k*paso;a=max(0,ss-.48);b=min(f.largo,ss+.48)
        if b<=a:continue
        pilastra(f,ss,1.1,4.45,ancho=.9,vuelo=.12,color=BLANCO)
        for hh in (1.25,1.85,2.45,3.05,3.65):
            f.caja(a+.10,b-.10,hh,hh+.4,.13,.15,'pintura_acento',GRIS)
        for ds in (-.22,.22):
            pilastra(f,ss+ds,5.0,9.2,ancho=.26,vuelo=.16,color=BLANCO)
            f.caja(ss+ds-.075,ss+ds+.075,6.25,8.8,.17,.19,'pintura_acento',GRIS)
            f.caja(ss+ds-.17,ss+ds+.17,8.96,9.12,-.015,.22,'moldura',BLANCO)
            roseta(f,ss+ds,9.0,.13,color=BLANCO,d=.22)
        cornisa(f,9.25,s0=a,s1=b,alto=.15,vuelo=.24,color=BLANCO)
        # Pretil con remate rebajado y dos pedestales, fotografiados.
        for signo in (-1,1):f.caja(ss+signo*.14-.09,ss+signo*.14+.09,10.45,10.75,-.10,.13,'moldura',BLANCO)
        for j in range(12):
            x0=-.6+j*.1;x1=x0+.1
            h0=10.38+.22*math.sqrt(max(0,1-(x0/.6)**2))
            h1=10.38+.22*math.sqrt(max(0,1-(x1/.6)**2))
            f.c.poligono([f.punto(ss+x0,h0,.04),f.punto(ss+x1,h1,.04),
                          f.punto(ss+x1,h1+.07,.04),f.punto(ss+x0,h0+.07,.04)],'moldura',BLANCO,
                          grosor=.12,normal_extrusion=-f.n)
    for hh in (4.45,4.85,9.5):
        tramos=((0,main-1.75),(main+1.75,f.largo)) if principal and hh==4.45 else ((0,f.largo),)
        for a,b in tramos:cornisa(f,hh,s0=a,s1=b,alto=.22,vuelo=.32,color=BLANCO)
    for hh in (4.72,9.4):
        for k in range(math.ceil(f.largo/.28)):
            ss=min(f.largo-.05,(k+.5)*.28)
            if principal and hh==4.72 and abs(ss-main)<1.75:continue
            f.caja(ss-.04,ss+.04,hh,hh+.10,.10,.24,'moldura',BLANCO)
    parapeto(f,9.9,alto=.65,color=BLANCO)
    for k in range(n):
        ss=(k+.5)*paso
        f.caja(ss-1.2,ss+1.2,10.05,10.35,.04,.065,'pintura_acento',GRIS)
    if principal:
        # Las tres líneas caben entre la clave de las dovelas (4,33 m)
        # y la imposta superior (4,85 m), con separación del paramento.
        letras(f,'TEATRO',main,4.69,.13);letras(f,'3',main,4.53,.13)
        letras(f,'DE FEBRERO',main,4.37,.13)
        for k in (3,7,10):
            ss=k*paso;farol_muro(f,ss,6.0)
            rama(f.c,f.punto(ss,6.55,.62),f.punto(ss,6.46,.58),.022,.022,'hierro','#33433a')


def construir_teatro(e,col):
    h=e['huella']
    z=max(altura_suelo(*p) for p in h);zb=min(altura_suelo(*p) for p in h)-.5
    c=Constructor(e['id'])
    f,guia=frente_de_calle(e,c,'Calle José Álvarez de Arenales',(.63,.78),z)
    decorar(f,zb,True)
    ajustar_fachada(c,guia)
    # La vuelta occidental de 5 m sí da a Arenales. El lado SE antiguo
    # es medianera: no lleva ventanas, balcones ni cornisas interiores.
    for lado in lados(h):
        if lado['a_calle'] and lado['calle']=='Calle José Álvarez de Arenales' and lado['normal'][0]<-.7:
            decorar(Fachada(c,lado,z),zb,False)
    prisma_seguro(c,h,zb,z+10.0,'muro',BLANCO)
    # Todo el edificio comparte el datum del frente: no se bajan ventanas
    # dejando la cornisa flotando. La cimentación sigue enterrada.
    a=Vector((*guia['lados'][0]['a'],0));b=Vector((*guia['lados'][-1]['b'],0));u=(b-a).normalized();L=(b-a).length
    za,zb_frente=altura_suelo(*a[:2]),altura_suelo(*b[:2])
    for v in c.bm.verts:
        ss=max(0,min(L,(v.co-a).dot(u)))
        # Una recta entre cotas extremas conserva el contacto de dientes y
        # molduras largas; la rejilla bilineal deformaba cada pieza distinto.
        v.co.z+=za+(zb_frente-za)*ss/L-z
    c.objeto(col)
