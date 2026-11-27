"""Frentes propios orientados; recorte estricto y piezas compartidas de Codex."""
import math
from kit import *
from piezas_codex import prisma_seguro,recorte_estricto,trasladar,rama
from detalles_plaza_codex import ajustar_fachada,punto_encadenado
from seleccion_frentes_codex import lados_de_calle


def frente_de_calle(e,c,calle,normal,z=None):
    """Frente sobre su polilínea real; decorar y después ajustar_fachada(c,g)."""
    from mathutils import Vector
    ls=lados_de_calle(lados(e['huella']),calle,normal)
    L=sum(math.dist(l['a'],l['b']) for l in ls)
    a=Vector((*ls[0]['a'],0));u=(Vector((*ls[0]['b'],0))-a).normalized()
    z=max(altura_suelo(*p) for p in e['huella']) if z is None else z
    f=Fachada(c,{'a':tuple(a[:2]),'b':tuple((a+u*L)[:2]),'normal':ls[0]['normal']},z)
    return f,{'lados':ls,'suelo':z,'a':f.a.copy(),'u':f.u.copy(),'n':f.n.copy(),'largo':L}


def frente_real(e,c,z=None,normal=(.78,-.63)):
    from mathutils import Vector
    normal=Vector((*normal,0)).normalized()
    ls=[l for l in lados(e['huella']) if l['normal'][0]*normal.x+l['normal'][1]*normal.y>.90]
    if not ls:raise ValueError('Sin frente equivalente '+e.get('id',''))
    ls.sort(key=lambda l:l['i'])
    if len(ls)>1:
        for i in range(len(ls)):
            orden=ls[i:]+ls[:i]
            if all(math.dist(a['b'],b['a'])<.02 for a,b in zip(orden,orden[1:])):ls=orden;break
        else:
            # Retornos distintos nunca se atan atravesando un vacío.
            mayor=max(ls,key=lambda l:l['largo']);ls=[mayor]
    L=sum(math.dist(l['a'],l['b']) for l in ls)
    a=Vector((*ls[0]['a'],0));u=(Vector((*ls[0]['b'],0))-a).normalized()
    z=max(altura_suelo(*p) for p in e['huella']) if z is None else z
    f=Fachada(c,{'a':tuple(a[:2]),'b':tuple((a+u*L)[:2]),'normal':ls[0]['normal']},z)
    return f,{'lados':ls,'suelo':z,'a':f.a.copy(),'u':f.u.copy(),'n':f.n.copy(),'largo':L}


def volumen_frente(nombre,huella,H,col,normal=(.78,-.63),z=None,color='#eeeae3'):
    h=recorte_estricto(datos.recortar_a_calles(huella))
    c=Constructor(nombre);f,g=frente_real({'id':nombre,'huella':h},c,z,normal)
    c._huella=h;c._alto=H;c._guia=g;c._color=color
    return c,f


def cerrar_frente(c,col):
    ajustar_fachada(c,c._guia)
    h=c._huella;z=c._guia['suelo']
    prisma_seguro(c,h,min(altura_suelo(*p) for p in h)-.5,z+c._alto,'muro',c._color)
    return c.objeto(col)


def farol_muro(f,s,h=4.1):
    c=f.c
    rama(c,f.punto(s,h+.55,-.02),f.punto(s,h+.55,.62),.025,.025,'hierro','#33433a')
    rama(c,f.punto(s,h+.87,-.02),f.punto(s,h+.55,.62),.022,.022,'hierro','#33433a')
    c.esfera(*f.punto(s,h+.15,.58),.18,'vidrio','#bfc5af',segmentos=8)
    p=f.punto(s,h+.31,.58)
    c.cilindro(p.x,p.y,p.z,p.z+.15,.24,'hierro','#33433a',lados=12,radio_arriba=.08)


def roseta(f,s,h,r=.25,rol='moldura',color='#f3ecdf',d=.18):
    rama(f.c,f.punto(s,h,-.035),f.punto(s,h,d),r*.3,r*.3,rol,color)
    for k in range(8):
        a=k*math.tau/8
        f.c.esfera(*f.punto(s+math.cos(a)*r*.62,h+math.sin(a)*r*.62,d),r*.31,rol,color,segmentos=4)
    f.c.esfera(*f.punto(s,h,d),r*.34,rol,color,segmentos=6)


def columna_tallada(f,s,h0,h1,r=.19,d=.25,salomonica=False,color='#eee7d8'):
    # Eje continuo con capiteles, base y talla adherida al fuste.
    f.cilindro_vertical(s,h0,h1,d,r,'piedra',color,lados=10)
    for hh in (h0,h0+.15,h1-.24,h1-.1):
        f.caja(s-r*1.6,s+r*1.6,hh,hh+.12,-.02,d+r*1.5,'piedra',color)
    if salomonica:
        N=60
        for k in range(N):
            a=k*math.tau/10;b=(k+1)*math.tau/10
            hh=h0+.3+k*(h1-h0-.65)/N;hh2=h0+.3+(k+1)*(h1-h0-.65)/N
            rama(f.c,f.punto(s+math.cos(a)*r,hh,d+math.sin(a)*r),
                 f.punto(s+math.cos(b)*r,hh2,d+math.sin(b)*r),r*.32,r*.32,'piedra',color)
    else:
        for k in range(28):
            hh=h0+.3+k*(h1-h0-.65)/28
            ds=r*.8*math.sin(k*math.pi/2)
            f.c.poligono([f.punto(s+ds,hh,d+r),f.punto(s+ds+.08,hh+.08,d+r+.025),f.punto(s+ds,hh+.16,d+r),f.punto(s+ds-.08,hh+.08,d+r+.025)],'piedra',color,grosor=.04,normal_extrusion=-f.n)


def portada_baroqua(f,s,ancho=6.6,H=8.6,color='#eee7d8',puerta_color='#67432f'):
    """Dos cuerpos, pares de columnas, hornacina, concha y coronación tallada.
    R0035: cal blanca; R0036: piedra crema. Puerta de dos hojas a escala humana.
    """
    k=H/8.6;w=ancho/6.6
    def caja(a,b,h0,h1,d0,d1,rol='piedra'):f.caja(s+a*w,s+b*w,h0*k,h1*k,d0,d1,rol,color)
    caja(-3.3,3.3,0,4.92,-.08,.1)
    caja(-2.45,2.45,4.92,7.65,-.08,.1)
    puerta(trasladar(f,d=.12),s,ancho=2.35*w,alto=3.15*k,arco=True,color=puerta_color,
           moldura='piedra',color_moldura=color)
    # Clavos y cuarterones del portón; no hay carteles publicitarios.
    for ds in (-.84,-.42,0,.42,.84):
        for hh in (.35,.8,1.25,1.7,2.15,2.6):
            f.caja(s+ds*w-.025,s+ds*w+.025,hh*k,hh*k+.04,.17,.21,'hierro','#4c3930')
    for ds in (-2.65,-1.95,1.95,2.65):
        caja(ds-.32,ds+.32,0,.72,-.01,.52)
        columna_tallada(f,s+ds*w,.72*k,4.35*k,.18*w,.28,salomonica=True,color=color)
    for hh,v in ((4.35,6.7),(4.65,6.9),(4.92,6.5)):
        cornisa(f,hh*k,s0=s-v*w/2,s1=s+v*w/2,alto=.17*k,vuelo=.53,rol='piedra',color=color)
    for ds in (-2.1,-1.55,1.55,2.1):
        columna_tallada(f,s+ds*w,5.08*k,7.3*k,.14*w,.24,color=color)
    # Hornacina ciega y concha con estrías radiales, no vidrio inventado.
    caja(-.73,.73,5.1,6.7,.11,.13)
    f.arco(s,.72*w,.12,6.15*k,.14,.28,'piedra',color,segmentos=18)
    for j in range(11):
        a=j*math.pi/10
        rama(f.c,f.punto(s,6.15*k,.27),f.punto(s+.65*w*math.cos(a),6.15*k+.65*k*math.sin(a),.27),.015,.015,'piedra',color)
    for ds in (-1.05,1.05):roseta(f,s+ds*w,5.45*k,.16,rol='piedra',color=color)
    for hh,v in ((7.35,5.4),(7.58,5.0),(7.8,3.9)):
        cornisa(f,hh*k,s0=s-v*w/2,s1=s+v*w/2,alto=.15*k,vuelo=.36,rol='piedra',color=color)
    for signo in (-1,1):
        f.arco(s+signo*.55*w,.48*w,.075,7.95*k,-.02,.2,'piedra',color,medio=False,segmentos=12)
        for ds in (2.4,1.35):
            ss=s+signo*ds*w
            p=f.punto(ss,7.75*k,.15)
            f.c.cilindro(p.x,p.y,p.z,p.z+.30*k,.13,'piedra',color,lados=8,radio_arriba=.075)
            f.c.esfera(*f.punto(ss,8.17*k,.15),.10,'piedra',color,segmentos=6)
    roseta(f,s,8.28*k,.28,rol='piedra',color=color)
    # Friso vegetal: hojas ligadas a un tallo central en relieve.
    for i in range(13):
        ss=s-2.6*w+i*5.2*w/12
        rama(f.c,f.punto(ss-.12,4.8*k,.21),f.punto(ss+.12,4.8*k,.21),.02,.02,'piedra',color)
        for signo in (-1,1):
            f.c.poligono([f.punto(ss,4.8*k,.22),f.punto(ss+signo*.12,4.99*k,.22),f.punto(ss+signo*.2,4.84*k,.27)],'piedra',color,grosor=.045,normal_extrusion=-f.n)
