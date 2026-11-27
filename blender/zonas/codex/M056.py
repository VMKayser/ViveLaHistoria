"""M056 — cerramiento y pavimento del atrio lateral de la Catedral.

Fotos 130746, 130751, 130755, 130759, 130805, 130808, 130812 y 130818:
no es un edificio de 9.6 m. Muro pétreo rojizo, balaustres y pilares con
urnas; portón alineado con la portada lateral de M055, árboles de vereda.
El fragmento E7ab30d del lienzo solo cubre parte del atrio. Se completa
el cerramiento paralelo al costado de Catedral hasta la portada, situándolo
tras la vereda según el ancho real de Plaza 25 de Mayo; ocho vistas
comparadas, con paños apoyados en cotas locales de terreno.
No se construyen calzada, vereda ni bordillo exterior de BASE.
"""
import os
import sys
import math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from kit import *
from piezas_codex import reja_porton,farol_pie,arbol_podado,pavimentar,trasladar
from triangulacion_codex import triangular_huella
from luminarias_codex import farol_curvo
m,col=iniciar('codex','M056')
e=m['edificios'][0]
cat=edificio('M055','E03fe1d');l=lados(cat['huella'])[0]
fcat=Fachada(None,l,0)
# El atrio es una huella propia; se recorta entero y el cerramiento sigue
# exactamente el lado exterior real. La línea anterior invadía la nueva calzada.
a0=fcat.punto(0,0,22.3);b0=fcat.punto(36.5,0,23.55)
h=datos.recortar_a_calles([tuple(a0[:2]),tuple(b0[:2]),
 tuple(fcat.punto(36.5,0)[:2]),tuple(fcat.punto(0,0)[:2])])
l=max((ll for ll in lados(h) if ll['a_calle']),
      key=lambda ll:ll['normal'][0]*fcat.n.x+ll['normal'][1]*fcat.n.y)
a,b=l['a'],l['b'];nx,ny=l['normal']
c=Constructor(e['id'])
z=max(altura_suelo(*a),altura_suelo(*b))+.12
f=Fachada(c,l,z)
color='#a77b60';puerta_s=30.8
# Hiladas por paños cortos, apoyadas en la pendiente de la vereda.
# Una única cota máxima levantaba el muro varios metros en el extremo bajo.
for aa,bb in ((0,7),(7,14),(14,21),(21,puerta_s-1.6),(puerta_s+1.6,f.largo)):
    p=f.punto((aa+bb)/2,0)
    local_z=altura_suelo(p.x,p.y)+.12
    ff=trasladar(f,h=local_z-z)
    pa,pb=f.punto(aa,0),f.punto(bb,0)
    desde=min(altura_suelo(pa.x,pa.y),altura_suelo(pb.x,pb.y))-.2-local_z
    zocalo(ff,1.1,s0=aa,s1=bb,desde=desde,rol='piedra',color=color)
    ff.caja(aa,bb,1.9,2.05,-.28,.04,'piedra',color)
    n=max(1,round((bb-aa)/.42))
    for i in range(n+1):
        ss=aa+(bb-aa)*i/n
        ff.cilindro_vertical(ss,1.1,1.9,-.1,.055,'piedra',color,lados=6)
        ff.cilindro_vertical(ss,1.3,1.55,-.1,.115,'piedra',color,lados=8)
for ss in (0,7,14,21,puerta_s-1.85,puerta_s+1.85,f.largo):
    p=f.punto(ss,0);ff=trasladar(f,h=altura_suelo(p.x,p.y)+.12-z)
    ff.caja(ss-.25,ss+.25,-.2,2.2,-.32,.14,'piedra',color)
    ff.caja(ss-.33,ss+.33,2.2,2.35,-.4,.22,'piedra',color)
    p=ff.punto(ss,2.35,-.1)
    c.cilindro(p.x,p.y,p.z,p.z+.32,.19,'piedra',color,lados=8,radio_arriba=.12)
    c.esfera(p.x,p.y,p.z+.41,.15,'piedra',color,segmentos=8)
p=f.punto(puerta_s,0)
fp=trasladar(f,h=altura_suelo(p.x,p.y)+.12-z)
reja_porton(fp,puerta_s,ancho=3.2,alto=2.8)
c.objeto(col)
# Suelo interior; todos los puntos quedan detrás del cerramiento y fuera
# de la calzada. La nave y torre de M055 cierran el otro lado del patio.
c=Constructor('M056_pavimento_atrio')
pavimentar(c,h,'adoquin',offset=.14,color='#c7b59d')
c.objeto(col)
# Árboles podados y farol del portón observados en 130755–130818.
for k,ss in enumerate((3.5,11,19,26)):
    p=f.punto(ss,0,1.05)
    arbol_podado(f'M056_arbol_{k}',p.x,p.y,col,radio=1.6,alto=3.8,direccion=(nx,ny))
p=f.punto(puerta_s-2.3,0,.7)
farol_curvo('M056_farol_porton',p.x,p.y,col,direccion=(nx,ny),alto=4.6)
exportar('codex','M056')
if '--sin-render' not in sys.argv:
    from detalles_plaza_codex import revisar_correcciones
    revisar_correcciones('M056',[],[f])
