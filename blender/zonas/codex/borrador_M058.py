# BORRADOR DE PAUSA 2026-11-12: NO VALIDADO NI EXPORTADO.
"""M058 — USFX en R0020/R0021/R0022: frente continuo de cinco ejes.
La asignación a huellas interiores es aproximada: fachada propia de 30 m
en el vacío del lienzo, desde el edificio del gran arco de vidrio hacia el
final de la cuadra. Tres niveles; dos miradores extremos en el intermedio,
tres balcones centrales de hierro, cinco ventanas altas bajo arquivoltas
ornamentadas, balaustradas y cornisa dentada. Vidrio oscuro, madera vino,
cal blanca. Sin cartel temporal, vehículos ni toldos. Interior sin foto.
"""
import os,sys,math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from detalles_plaza_codex import *
from casas_codex import casa_minima
from piezas_codex import ventana_rebajada
m,col=iniciar('codex','M058')
h=huella_usfx();z=max(altura_suelo(*p) for p in h)
c=Constructor('M058_USFX');f,guia_usfx=frente_encadenado({'id':'M058_USFX','huella':h},c,z);L=f.largo
rustica(f,12.45)
paso=L/5
for k in range(5):
 s=(k+.5)*paso;w=1.6
 puerta(trasladar(f,d=.025),s,ancho=2.65 if k in (0,2,4) else 1.65,alto=2.65,arco=True,color='#47443d',color_moldura=BLANCO)
 if k in (0,4):
  f.caja(s-1.18,s+1.18,4.2,7.3,0,.58,'moldura',BLANCO)
  ventana_rebajada(trasladar(f,d=.59),s,4.55,ancho=1.8,alto=2.3,color_moldura=BLANCO)
  for ds in (-1.1,1.1):
   f.caja(s+ds-.04,s+ds+.04,4.3,7.1,.60,.68,'moldura',BLANCO)
  volutas(f,s,4.3,1.4)
 else:
  ventana_rebajada(trasladar(f,d=.025),s,4.45,ancho=w,alto=2.55,color_moldura=BLANCO)
  balcon_hierro(f,s-1.1,s+1.1,4.45,vuelo=.65)
  for ds in (-.4,.4):
   f.arco(s+ds,.17,.015,4.97,.60,.64,'hierro',segmentos=5,medio=False)
 volutas(f,s,7.4,1.3)
 vano(f,s,9.0,1.5,2.35,arco=True)
 balustrada(f,s-1,s+1,9.0,d=.45 if k in (0,4) else .15)
 r=1.2
 f.arco(s,r,.14,10.05,.04,.16,'moldura',BLANCO,segmentos=18)
 for j in range(11):
  a=j*math.pi/10
  flores(f,s-r*.86*math.cos(a),10.05+r*.86*math.sin(a),.075)
 for ds in (-r,r):flautas(f,s+ds,9.65,10.05,ancho=.15)
 flores(f,s,10.95,.17)
for h0 in (3.8,7.8,12.1):cornisa(f,h0,alto=.28,vuelo=.26,color=BLANCO)
for k in range(int(L/.22)):
 s=(k+.5)*L/int(L/.22)
 f.caja(s-.045,s+.045,12.06,12.19,.14,.26,'moldura',BLANCO)
parapeto(f,12.45,alto=.4,color=BLANCO)
# Placa institucional, sin reproducir la lona temporal.
f.caja(L/2+.85,L/2+1.25,6.0,6.5,.03,.08,'letrero','#bdac8c')
ajustar_fachada(c,guia_usfx)
prisma_seguro(c,h,z-.65,z+12.45,'muro',BLANCO)
c.objeto(col)
f.punto=lambda s,h,d=0:punto_encadenado(guia_usfx,s,h,d)
for e in m['edificios']:
 casa_minima(e,col)
for j,ss in enumerate((2.6,8.6,14.6,20.6,26.5)):
 p=f.punto(ss,0,2.0);arbol_podado(f'M058_arbol_{j}',p.x,p.y,col,radio=1.25,alto=3.3)
revisar_correcciones('M058',[21],[f])
