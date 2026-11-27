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
# piezas de codex (solo lectura): este conjunto lo empezó codex y pasó a claude el 2026-11-14 (pedido del usuario)
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','codex'))
sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
from kit import *
from piezas_codex import reja_porton,farol_pie,arbol_podado,pavimentar,trasladar
from triangulacion_codex import triangular_huella
from luminarias_codex import farol_curvo
m,col=iniciar('claude','M056')
e=m['edificios'][0]
cat=edificio('M055','E03fe1d');l=lados(cat['huella'])[0]
fcat=Fachada(None,l,0)
# El atrio es una huella propia; se recorta entero y el cerramiento sigue el lado exterior real.
# 2026-11-14 (claude, R0108/R0110: "cerrar el muro de la catedral", "falta el muro que resguarda la catedral"): el
# muro llegaba solo hasta el extremo de la nave y el atrio quedaba abierto hacia la esquina con Nicolás Ortiz. Ahora
# sigue hasta el corredor de Nicolás Ortiz, dobla por esa calle hasta la Catedral y en la esquina lleva el pedestal
# de piedra con la cruz (foto de referencia de R0110).
from piezas_claude import cerramiento_atrio, junto_al_bordillo  # noqa: E402
S0, S1 = -14.0, 36.5
a0=fcat.punto(S0,0,22.3);b0=fcat.punto(S1,0,23.55)
h=datos.recortar_a_calles([tuple(a0[:2]),tuple(b0[:2]),
 tuple(fcat.punto(S1,0)[:2]),tuple(fcat.punto(S0,0)[:2])])
_ls=[ll for ll in lados(h) if ll['a_calle']]
l=max(_ls,key=lambda ll:ll['normal'][0]*fcat.n.x+ll['normal'][1]*fcat.n.y)            # frente a la plaza
lo=max(_ls,key=lambda ll:-(ll['normal'][0]*fcat.u.x+ll['normal'][1]*fcat.u.y))         # frente a Nicolás Ortiz
a,b=l['a'],l['b'];nx,ny=l['normal']
# objeto propio (no lleva el id del fragmento E7ab30d del lienzo: el recorte a medianeras lo amputaba)
c=Constructor('M056_cerramiento')
color='#a77b60'


def cerramiento(f, puerta_s=None):
    cerramiento_atrio(c, f, puertas=() if puerta_s is None else (puerta_s,), color=color)


# R0169: el muro de la plaza llegaba 10 m antes de la esquina con Nicolás Ortiz y el pilar de la cruz quedaba suelto.
# Ahora se prolonga hasta la esquina real (donde cierra el muro de M055) y el pilar va en ese vértice.
from piezas_claude import esquina_atrio_ortiz, pilar_esquina_cruz  # noqa: E402
_t_esq,C,_=esquina_atrio_ortiz(lados(cat['huella'])[12]['a'])
_ux,_uy=(b[0]-a[0])/math.hypot(b[0]-a[0],b[1]-a[1]),(b[1]-a[1])/math.hypot(b[0]-a[0],b[1]-a[1])
s_esq=(C[0]-a[0])*_ux+(C[1]-a[1])*_uy                                   # negativo: la esquina queda antes de 'a'
l={**l,'a':(a[0]+_ux*s_esq,a[1]+_uy*s_esq)}
a=l['a']
z=max(altura_suelo(*a),altura_suelo(*b))+.12
f=Fachada(c,l,z)
# el portón sigue frente a la portada lateral de la Catedral (s = 30,8 del costado de la nave)
g_=fcat.punto(30.8,0,23.0)
puerta_s=(g_.x-a[0])*f.u.x+(g_.y-a[1])*f.u.y
cerramiento(f,puerta_s)
# extremo NO del atrio (R0108: "¿por qué no cerraron este muro?"): del muro de la plaza hasta la esquina de la
# Catedral (su lado 1 ocupa el resto de ese borde)
p_out=min((l['a'],l['b']),key=lambda q:math.dist(q,b0[:2]))                  # esquina NO del muro de la plaza
cat_l1=lados(cat['huella'])[1]
p_in=min((cat_l1['a'],cat_l1['b']),key=lambda q:math.dist(q,p_out))           # esquina de la Catedral más cercana
largo_libre=math.dist(p_out,p_in)
if largo_libre>1.0:
    dx_,dy_=(p_in[0]-p_out[0])/largo_libre,(p_in[1]-p_out[1])/largo_libre
    nrm=(dy_,-dx_)
    if nrm[0]*fcat.u.x+nrm[1]*fcat.u.y<0:                                      # hacia afuera del atrio (NO)
        nrm=(-dy_,dx_)
        lnw={'a':tuple(p_in),'b':tuple(p_out),'normal':nrm}
    else:
        lnw={'a':tuple(p_out),'b':tuple(p_in),'normal':nrm}
    print('[M056] cierre NO', [round(v,1) for v in p_out], [round(v,1) for v in p_in], round(largo_libre,1))
    cerramiento(Fachada(c,lnw,max(altura_suelo(*lnw['a']),altura_suelo(*lnw['b']))+.12))
# pilar de la esquina con la cruz de piedra (R0110, R0169): en el vértice donde se encuentran los dos muros
pilar_esquina_cruz(c,C[0],C[1],altura_suelo(*C)+.12,(nx,ny),(-_ux,-_uy),'#b07f66')
c.objeto(col)
# Suelo interior; todos los puntos quedan detrás del cerramiento y fuera de la calzada.
c=Constructor('M056_pavimento_atrio')
pavimentar(c,h,'adoquin',offset=.14,color='#c7b59d')
c.objeto(col)
# Árboles podados de vereda (130755–130818 y referencia de R0110): JUNTO AL BORDILLO, uno cada ~7 m, nunca
# pegados al muro (R0108/R0109)
k=0
ss=3.5
while ss<f.largo-2.0:
    if abs(ss-puerta_s)>2.6:
        p=f.punto(ss,0)
        x,y=junto_al_bordillo(p.x,p.y,nx,ny,retiro=.7)
        arbol_podado(f'M056_arbol_{k}',x,y,col,radio=1.3,alto=3.8,direccion=(nx,ny))
        k+=1
    ss+=7.0
# (sin farol propio junto al portón: la BASE ya pone uno ahí y quedaban dos juntos, R0109)
from esquina_ortiz_plaza import esquina_farmacia, cebra_ortiz  # noqa: E402
cebra_ortiz(col)
esquina_farmacia(col)            # R0168: fachada de la esquina SE (piel sobre el paño ciego del ala de M065)
exportar('claude','M056')
if '--sin-render' not in sys.argv:
    from detalles_plaza_codex import revisar_correcciones
    revisar_correcciones('M056',[],[f])
