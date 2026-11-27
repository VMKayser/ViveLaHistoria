"""P01 — Plaza 25 de Mayo, con revisión de calle y aérea.

Hoja de 16 fotos; detalles 130603, 130631 y 130635 examinados.
Se ven árboles altos de sombra, copas podadas bajas, bancos de madera,
faroles oscuros, jardines con reja baja, mástiles y quioscos pétreos con
cubierta rojiza. Se usa el polígono P01 y las sendas OSM ya ubicadas;
fuentes y monumentos conservan la posición de los puntos OSM originales.
El pedestal y las figuras son simplificados: las fotos periféricas no
muestran sus detalles. Distribución de vegetación y bancos provisional.
Solo interior: no hay calzada, vereda ni bordillo exterior de BASE.
"""
import os
import sys
import math
import json
import lzma
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from kit import *
from piezas_codex import copa_elipsoide,arbol_podado,farol_pie,rama,objeto_vegetal,recorte_estricto
from triangulacion_codex import triangular_huella
from pavimentos_codex import pavimento_fuera_calles
from luminarias_codex import farol_globos
from monumentos_codex import figura_monumento
AGENTE='codex';MANZANA='P01'
m,col=iniciar(AGENTE,MANZANA)
huella=m['poligono'];cx,cy=-176.72,-208.93


def dentro(x,y):return datos._dentro(x,y,huella)


def suelo_triangulo(c,tri,rol,offset=.15):
    # Dividir los triángulos grandes para seguir la rejilla de terreno de 5 m.
    a,b,d=tri
    ds=[math.dist(a,b),math.dist(b,d),math.dist(d,a)]
    k=max(range(3),key=lambda i:ds[i])
    if ds[k]>5:
        aa,bb,cc=((a,b,d),(b,d,a),(d,a,b))[k]
        med=((aa[0]+bb[0])/2,(aa[1]+bb[1])/2)
        suelo_triangulo(c,(aa,med,cc),rol,offset)
        suelo_triangulo(c,(med,bb,cc),rol,offset)
    else:c.poligono([(x,y,altura_suelo(x,y)+offset) for x,y in tri],rol,
                      '#c9c0aa' if rol=='adoquin' else None)


def superficie(c,pts,rol,offset=.15):
    for tri in triangular_huella(pts):suelo_triangulo(c,tri,rol,offset)


def disco(c,x,y,r,rol,offset=.19):
    for k in range(40):
        a=k*math.tau/40;b=(k+1)*math.tau/40
        suelo_triangulo(c,((x,y),(x+r*math.cos(a),y+r*math.sin(a)),
                           (x+r*math.cos(b),y+r*math.sin(b))),rol,offset)


def senda(c,puntos,ancho=4):
    for a,b in zip(puntos,puntos[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
        if L<.01:continue
        nx,ny=-dy/L*ancho/2,dx/L*ancho/2
        pts=[(a[0]+nx,a[1]+ny),(a[0]-nx,a[1]-ny),
             (b[0]-nx,b[1]-ny),(b[0]+nx,b[1]+ny)]
        superficie(c,pts,'adoquin',.19)


# El perímetro interior es paseo pavimentado; los jardines quedan dentro.
c=Constructor('P01_pavimento_interior')
for pieza in pavimento_fuera_calles(huella,datos.calles_reales()):
    superficie(c,pieza,'adoquin',.14)
c.objeto(col)
contorno=[(-238.34,-212.45),(-171.57,-271.01),(-114.38,-204.12),(-184.85,-144.43)]
def recortar(h,a,n,distancia):
    res=[]
    def d(p):return (p[0]-a[0])*n[0]+(p[1]-a[1])*n[1]-distancia
    for p,q in zip(h,h[1:]+h[:1]):
        dp,dq=d(p),d(q)
        if dp>=0:res.append(p)
        if (dp>=0)!=(dq>=0):
            t=dp/(dp-dq);res.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    return res
for j,(a,b) in enumerate(zip(contorno,contorno[1:]+contorno[:1])):
    tri=datos.orientar_ccw([a,b,(cx,cy)])
    h=tri[:]
    for aa,bb in zip(tri,tri[1:]+tri[:1]):
        dx,dy=bb[0]-aa[0],bb[1]-aa[1];L=math.hypot(dx,dy)
        h=recortar(h,aa,(-dy/L,dx/L),3.2)
    nx,ny=(a[0]+b[0])/2-cx,(a[1]+b[1])/2-cy
    L=math.hypot(nx,ny);h=recortar(h,(cx,cy),(nx/L,ny/L),14)
    c=Constructor(f'P01_jardin_{j}');superficie(c,h,'cesped',.18);c.objeto(col)

# Caminos radiales, anillo central y paseo perimetral según OSM del proyecto.
cs=json.load(open(os.path.join(datos.RAIZ,'web/public/mapa/calles.json')))
interiores=[cc for cc in cs if cc['tipo']=='footway' and cc['puntos'] and
            all(dentro(p[0],p[1]) for p in cc['puntos'])]
c=Constructor('P01_caminos')
for cc in interiores:senda(c,cc['puntos'],ancho=4.2)
disco(c,cx,cy,12.0,'adoquin')
c.objeto(col)


def banco(nombre,x,y,ux,uy):
    z=altura_suelo(x,y)+.20;c=Constructor(nombre)
    lado={'a':(x-ux,y-uy),'b':(x+ux,y+uy),'normal':(uy,-ux)}
    f=Fachada(c,lado,z)
    for k in range(4):f.caja(0,2,.42,.49,-.24+k*.13,-.13+k*.13,'madera','#66402b')
    for k in range(3):f.caja(0,2,.65+k*.13,.74+k*.13,-.28,-.22,'madera','#66402b')
    for ss in (.18,1.82):
        f.caja(ss-.045,ss+.045,0,.45,-.22,.22,'hierro')
        f.caja(ss-.04,ss+.04,.4,1.02,-.28,-.22,'hierro')
        f.caja(ss-.04,ss+.04,.68,.73,-.25,.27,'hierro')
    c.objeto(col)

# Paseo perimetral: puntos sobre las cuatro sendas que unen las esquinas.
contorno=[(-238.34,-212.45),(-171.57,-271.01),(-114.38,-204.12),(-184.85,-144.43)]
for lado,(a,b) in enumerate(zip(contorno,contorno[1:]+contorno[:1])):
    dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);ux,uy=dx/L,dy/L
    nx,ny=-uy,ux
    # Orientar el desplazamiento hacia el centro de la plaza.
    if ((cx-(a[0]+b[0])/2)*nx+(cy-(a[1]+b[1])/2)*ny)<0:nx,ny=-nx,-ny
    for k in range(1,9):
        t=k/9;x=a[0]+dx*t+nx*4.5;y=a[1]+dy*t+ny*4.5
        arbol_podado(f'P01_arbol_borde_{lado}_{k}',x,y,col,radio=2.4,alto=4.3,direccion=(nx,ny))
        if k%2==0:
            banco(f'P01_banco_{lado}_{k}',x-nx*3,y-ny*3,ux,uy)
    for k in (1,3,5,7):
        t=k/8;x=a[0]+dx*t+nx*1.0;y=a[1]+dy*t+ny*1.0
        farol_globos(f'P01_farol_{lado}_{k}',x,y,col,alto=5.8)
    # Reja baja de jardines detrás del paseo.
    rc=Constructor(f'P01_reja_jardin_{lado}')
    f=Fachada(rc,{'a':(a[0]+nx*3,a[1]+ny*3),
                   'b':(b[0]+nx*3,b[1]+ny*3),'normal':(nx,ny)},0)
    for j in range(round(L/.65)+1):
        ss=min(L,j*.65);p=f.punto(ss,0)
        z=altura_suelo(p.x,p.y)+.2
        rc.cilindro(p.x,p.y,z,z+.45,.018,'hierro',lados=4)
    # Dos largueros continuos; los postes solos no forman la reja fotografiada.
    tramos=max(1,round(L/4))
    for j in range(tramos):
        a0=f.punto(L*j/tramos,0);b0=f.punto(L*(j+1)/tramos,0)
        for hh in (.18,.43):
            rama(rc,(a0.x,a0.y,altura_suelo(a0.x,a0.y)+.2+hh),
                 (b0.x,b0.y,altura_suelo(b0.x,b0.y)+.2+hh),.015,.015,rol='hierro')
    rc.objeto(col)
# Árboles de sombra del interior: agrupados fuera de las sendas.
def distancia_sendas(x,y):
    return min(datos._dist_seg(x,y,a,b)[0] for cc in interiores
               for a,b in zip(cc['puntos'],cc['puntos'][1:]))
n=0
for x in range(-223,-124,12):
    for y in range(-255,-155,12):
        if not dentro(x,y) or math.hypot(x-cx,y-cy)<18 or distancia_sendas(x,y)<6:continue
        n+=1;z=altura_suelo(x,y);c=Constructor(f'P01_arbol_alto_{n}')
        c.cilindro(x,y,z,z+9.5,.34,'tronco',lados=8,radio_arriba=.13)
        for j,(dx,dy) in enumerate(((-2,0),(1.8,1),(0,-1.8))):
            rama(c,(x,y,z+6.8),(x+dx,y+dy,z+10.5),.20,.085)
            copa_elipsoide(c,x+dx,y+dy,z+11+(j%2),4.4,4.0,2.8,
                           'follaje_claro' if j==1 else 'follaje')
        objeto_vegetal(c,col)

# Elementos OSM: posición real de fuentes y monumentos del parque.
sys.path.insert(0,os.path.join(datos.RAIZ,'blender','scripts'))
from geo import a_metros
features=json.load(lzma.open(os.path.join(datos.RAIZ,'Sucre.osm.geojson.xz')))['features']
for i,ff in enumerate(features):
    g=ff['geometry'];pr=ff['properties']
    if g['type']!='Point':continue
    lon,lat=g['coordinates'];x,y=a_metros(lat,lon)
    if not dentro(x,y):continue
    z=altura_suelo(x,y)+.2
    if pr.get('amenity')=='fountain':
        c=Constructor(f'P01_fuente_{i}')
        c.cilindro(x,y,z,z+.4,2.3,'piedra',lados=24)
        c.cilindro(x,y,z+.40,z+.43,2.05,'agua',lados=24)
        c.cilindro(x,y,z+.43,z+1.5,.18,'piedra',lados=10)
        c.cilindro(x,y,z+1.4,z+1.6,.85,'piedra',lados=16,radio_arriba=1.0)
        c.objeto(col)
    elif pr.get('tourism')=='artwork':
        central=pr.get('name')=='Antonio José de Sucre'
        c=Constructor('P01_monumento_Sucre' if central else f'P01_monumento_{i}')
        w=1.3 if central else .65;h=3.4 if central else 1.4
        c.caja(x-w,y-w,z,x+w,y+w,z+.3,'piedra','#bba98b')
        c.caja(x-w*.65,y-w*.65,z+.3,x+w*.65,y+w*.65,z+h,'piedra','#cbbba0')
        c.caja(x-w*.8,y-w*.8,z+h,x+w*.8,y+w*.8,z+h+.22,'piedra','#bba98b')
        # Silueta de estatua: pendiente de referencia de detalle.
        figura_monumento(c,x,y,z+h+.22,escala=1.15 if central else 1.0)
        c.objeto(col)
    elif pr.get('name')=='Km 0':
        c=Constructor('P01_Km0')
        c.cilindro(x,y,z,z+.55,.55,'piedra',lados=12)
        c.cilindro(x,y,z+.55,z+.58,.44,'metal',lados=12)
        c.objeto(col)
# Dos quioscos pétreos visibles desde el lado oeste: implantación aproximada.
for k,(x,y) in enumerate(((-204,-173),(-225,-205))):
    z=altura_suelo(x,y)+.2;c=Constructor(f'P01_quiosco_{k}')
    c.cilindro(x,y,z,z+.3,1.45,'piedra','#a48b6a',lados=8)
    c.cilindro(x,y,z+.3,z+2.6,1.1,'piedra','#bca586',lados=8)
    for a in range(4):
        ang=a*math.pi/2;ux,uy=math.cos(ang),math.sin(ang)
        f=Fachada(c,{'a':(x+ux*1.12-uy*.6,y+uy*1.12+ux*.6),
                     'b':(x+ux*1.12+uy*.6,y+uy*1.12-ux*.6),'normal':(ux,uy)},z)
        ventana(f,.6,.9,ancho=.65,alto=1.2,color_carpinteria='#714335')
    c.cilindro(x,y,z+2.55,z+2.75,1.5,'piedra','#bca586',lados=8)
    c.cilindro(x,y,z+2.75,z+4.0,1.5,'teja','#a9624b',lados=4,radio_arriba=.05)
    c.objeto(col)
# Mástiles documentados en el frente oeste (130631, 130635).
for k in range(7):
    x=-221+k*4.1;y=-192-k*4.8
    if not dentro(x,y):continue
    z=altura_suelo(x,y)+.2;c=Constructor(f'P01_mastil_{k}')
    c.cilindro(x,y,z,z+8,.035,'metal',lados=6)
    c.esfera(x,y,z+8.05,.07,'metal',segmentos=6)
    c.objeto(col)
exportar(AGENTE,MANZANA)
