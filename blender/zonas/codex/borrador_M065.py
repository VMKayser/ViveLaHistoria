# BORRADOR DE PAUSA 2026-11-12: NO VALIDADO NI EXPORTADO.
"""M065 — R0022, ala baja de dos pisos al final de la cuadra de la USFX.
Referencia: vanos rectangulares de carpintería oscura, balcón de hierro,
guardapolvos dentados, sillería blanca y pretil con remates redondeados.
Franja propia en el vacío del lienzo, entre USFX y el cruce Nicolás Ortiz.
El resto fuera del encuadre se completa con ritmo colonial; interiores sin
foto. No se ocupa la calzada: huella recortada por el kit antes de modelar.
"""
import os,sys,math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from detalles_plaza_codex import *
from casas_codex import casa_minima
from piezas_codex import farol_pie
m,col=iniciar('codex','M065')
_usfx,guia=frente_encadenado({'id':'USFX','huella':huella_usfx()},None)
a=tuple(punto_encadenado(guia,_usfx.largo,0)[:2])
e64=next(e for e in manzana('M064')['edificios'] if e['id']=='Ed8b92f')
b=max(e64['huella'],key=lambda p:p[1]);dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);n=(dy/L,-dx/L)
h=datos.recortar_a_calles([a,b,(b[0]-n[0]*6,b[1]-n[1]*6),(a[0]-n[0]*6,a[1]-n[1]*6)])
z=max(altura_suelo(*p) for p in h)
c=Constructor('M065_ala_plaza');f,guia_ala=frente_encadenado({'id':'ala plaza','huella':h},c,z);L=f.largo
rustica(f,8.3)
n=max(2,round(L/4.5))
for k in range(n):
 s=(k+.5)*L/n
 puerta(trasladar(f,d=.025),s,ancho=1.6,alto=3.0,rol='vidrio',color='#3b4843',color_moldura=BLANCO)
 vano(f,s,4.5,1.35,2.45)
 balcon_hierro(f,s-.98,s+.98,4.5,vuelo=.65)
 f.caja(s-.98,s+.98,7.1,7.28,.02,.17,'moldura',BLANCO)
 for j in range(7):
  ss=s-.84+j*.28
  f.caja(ss-.045,ss+.045,6.99,7.12,.02,.13,'moldura',BLANCO)
 for ss in (s-.86,s+.86):pilastra(f,ss,4.5,7.0,ancho=.11,color=BLANCO)
for hh in (3.95,7.75):cornisa(f,hh,alto=.28,vuelo=.26,color=BLANCO)
parapeto(f,8.3,alto=.6,color=BLANCO)
for k in range(n+1):
 ss=k*L/n
 f.caja(ss-.13,ss+.13,8.3,8.88,-.18,.05,'moldura',BLANCO)
 f.arco(ss,.13,.05,8.88,-.18,.05,'moldura',BLANCO,segmentos=8)
 f.timpano_arco(ss,.13,8.88,.055,'moldura',BLANCO)
ajustar_fachada(c,guia_ala)
prisma_seguro(c,h,min(altura_suelo(*p) for p in h)-.65,z+8.3,'muro',BLANCO)
c.objeto(col)
f.punto=lambda s,h,d=0:punto_encadenado(guia_ala,s,h,d)
for e in m['edificios']:
 casa_minima(e,col)
for j,ss in enumerate((L*.2,L*.7)):
 p=f.punto(ss,0,2.0);arbol_podado(f'M065_arbol_{j}',p.x,p.y,col,radio=1.2,alto=3.2)
p=f.punto(L*.55,0,2.0);farol_pie('M065_farol',p.x,p.y,col,alto=5.2)
revisar_correcciones('M065',[22],[f])
