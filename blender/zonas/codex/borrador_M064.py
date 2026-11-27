# BORRADOR DE PAUSA 2026-11-12: NO VALIDADO NI EXPORTADO.
"""M064 — R0023/24: esquina Real Audiencia × Nicolás Ortiz.
Referencia real: dos plantas y ático bajo mansarda metálica, cúpula de
chapa clara sobre esquina, linterna de hierro; balcón alto, mirador acristalado
central, balcones individuales, molduras y ménsulas blancas, basamento beige.
Lado largo: ocho ejes; lado corto: tres. Fachadas sobre huella recortada.
El entrante en V del lienzo en la esquina se sustituye por un chaflán dentro
de su envolvente, con apoyo continuo desde el suelo. Sin publicidad/autos.
Edificios pequeños posteriores sin foto: colonial sencillo.
"""
import os,sys,math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from detalles_plaza_codex import *
from casas_codex import casa_minima
from piezas_codex import ventana_rebajada,farol_pie
m,col=iniciar('codex','M064');e=next(e for e in m['edificios'] if e['id']=='Ed8b92f')
# Quitar solo la escotadura del frente norte, conservando las dos alineaciones.
h=datos.orientar_ccw(e['huella']);puntos=sorted(range(len(h)),key=lambda i:h[i][1],reverse=True)
# El vértice cóncavo entre las dos esquinas más al norte es el entrante del lienzo.
i1,i2=puntos[:2]
if (i1-i2)%len(h)==2:
 indice=(i2+1)%len(h);h=[p for i,p in enumerate(h) if i!=indice]
elif (i2-i1)%len(h)==2:
 indice=(i1+1)%len(h);h=[p for i,p in enumerate(h) if i!=indice]
h=datos.recortar_a_calles(h)
c=Constructor(e['id']);z=max(altura_suelo(*p) for p in h)
prisma_seguro(c,h,min(altura_suelo(*p) for p in h)-.65,z+8.45,'muro',BLANCO)
ls=lados(h)
largo=max((l for l in ls if l['normal'][0]<-.65 and l['normal'][1]>.4),key=lambda l:l['largo'])
corto=max((l for l in ls if l['normal'][0]>.4 and l['normal'][1]>.5),key=lambda l:l['largo'])
chaflan=max((l for l in ls if l['normal'][1]>.85),key=lambda l:l['largo'])
frentes=[]

def dormer(f,s):
 w=2.3
 f.caja(s-w/2,s+w/2,8.4,10.75,-1.25,0,'muro',BLANCO)
 vano(f,s,8.65,1.15,1.95,arco=True)
 f.arco(s,.86,.12,9.85,.025,.14,'moldura',BLANCO,segmentos=16)
 c.poligono([f.punto(s-1.25,10.7,0),f.punto(s,11.4,0),f.punto(s+1.25,10.7,0)],'muro',BLANCO,grosor=.2,normal_extrusion=f.n)
 for signo in (-1,1):barra(f,(s+signo*1.3,10.7,.15),(s,11.48,.15),.065)
 balcon_hierro(f,s-.9,s+.9,8.65,vuelo=.5)

for l,n in ((largo,8),(corto,3)):
 f=Fachada(c,l,z);frentes.append(f);L=f.largo;paso=L/n
 rustica(f,8.4,paso=.42)
 f.caja(0,L,min(altura_suelo(*p) for p in h)-.65-z,.65,0,.035,'zocalo_piedra','#c1ab8d')
 for k in range(n):
  s=(k+.5)*paso
  puerta(trasladar(f,d=.045),s,ancho=min(1.55,paso*.55),alto=2.8,arco=True,rol='vidrio',color='#3b4745',color_moldura=BLANCO)
  ventana_rebajada(trasladar(f,d=.025),s,4.35,ancho=1.25,alto=2.65,color_moldura=BLANCO)
  balcon_hierro(f,s-.83,s+.83,4.35,vuelo=.64)
  # Volutas y florón de clave sobre cada vano alto.
  volutas(f,s,7.2,1.15);flores(f,s,3.65,.15)
  for ds in (-.55,.55):
   f.caja(s+ds-.055,s+ds+.055,3.95,4.22,.04,.44,'moldura',BLANCO)
 for h0 in (3.75,7.7):cornisa(f,h0,alto=.26,vuelo=.25,color=BLANCO)
 for k in range(int(L/.42)):
  s=(k+.5)*L/int(L/.42)
  f.caja(s-.055,s+.055,8.03,8.23,.02,.35,'moldura',BLANCO)
 # Mansarda apoyada en la cornisa. Paños de chapa, juntas en relieve.
 c.poligono([f.punto(0,8.4,0),f.punto(L,8.4,0),f.punto(L,10.2,-2),f.punto(0,10.2,-2)],'metal','#a7b7b6',grosor=.08)
 for j in range(1,7):
  t=j/7
  barra(f,(0,8.42+1.8*t,-2*t),(L,8.42+1.8*t,-2*t),.012,'metal','#c3cbc7')
 for k in range(int(L/.48)):
  s=(k+.5)*L/int(L/.48)
  barra(f,(s,8.43,0),(s,10.23,-2),.011,'metal','#c3cbc7')
 for s in (3.1,L-3.1) if n==8 else (L*.57,):dormer(f,s)

# Esquina: mismo cuerpo desde el suelo hasta el ático; mirador sobre ménsulas.
f=Fachada(c,chaflan,z);frentes.append(f);L=f.largo;s=L/2
rustica(f,8.4)
f.caja(0,L,-.65,.65,0,.04,'zocalo_piedra','#c1ab8d')
puerta(trasladar(f,d=.055),s,ancho=min(2.6,L-.7),alto=3.05,rol='vidrio',color='#34413e',color_moldura=BLANCO)
f.caja(.12,L-.12,4.1,7.45,0,.53,'moldura',BLANCO)
for k in range(3):
 ss=L*(.22+.28*k)
 ventana(trasladar(f,d=.54),ss,4.45,ancho=L*.24,alto=2.55,color_carpinteria=MADERA,color_moldura=BLANCO)
for ss in (.15,L/2,L-.15):
 f.caja(ss-.07,ss+.07,3.8,4.1,.02,.5,'moldura',BLANCO)
 volutas(f,ss,3.7,.6)
f.caja(0,L,7.7,8.45,-2,0,'muro',BLANCO)
cornisa(f,7.7,alto=.3,vuelo=.48,color=BLANCO)
for k in range(12):
 ss=(k+.5)*L/12
 f.caja(ss-.065,ss+.065,7.54,7.75,.02,.4,'moldura',BLANCO)
# Cuerpo superior de la puerta del balcón bajo la cúpula.
f.caja(.2,L-.2,8.4,10.75,-2.8,0,'muro',BLANCO)
vano(f,s,8.65,1.15,2.0)
balcon_hierro(f,.15,L-.15,8.65,vuelo=.7)
for ss in (.25,L-.25):pilastra(f,ss,8.4,10.75,ancho=.22,color=BLANCO)
c.poligono([f.punto(s-1.1,10.7,.04),f.punto(s,11.5,.04),f.punto(s+1.1,10.7,.04)],'muro',BLANCO,grosor=.16,normal_extrusion=f.n)
for signo in (-1,1):barra(f,(s+signo*1.2,10.7,.12),(s,11.58,.12),.065)
# Cúpula: casquete con juntas de chapa y alternancia sutil de material.
centro=f.punto(s,0,-2.8);radio=2.75
for j in range(10):
 a=j*math.pi/20;b=(j+1)*math.pi/20
 for k in range(32):
  u=k*math.tau/32;v=(k+1)*math.tau/32
  def p(t,w):return (centro.x+radio*math.cos(t)*math.cos(w),centro.y+radio*math.cos(t)*math.sin(w),z+10.5+3.15*math.sin(t))
  c.poligono([p(a,u),p(a,v),p(b,v),p(b,u)],'metal','#b6c2bf' if (j+k)%2 else '#aebbb8')
 for k in range(32):
  u=k*math.tau/32
  rama(c,p(a,u),p(b,u),.012,.012,'metal','#d4d9d1')
for h0,h1,r in ((13.6,13.75,.64),(14.3,14.38,.54)):
 c.cilindro(centro.x,centro.y,z+h0,z+h1,r,'hierro',lados=20)
for k in range(12):
 a=k*math.tau/12
 c.cilindro(centro.x+.5*math.cos(a),centro.y+.5*math.sin(a),z+13.74,z+14.3,.018,'hierro',lados=5)
c.cilindro(centro.x,centro.y,z+14.35,z+15.4,.015,'metal',lados=6)
c.objeto(col)
for e in m['edificios']:
 if e['id']=='Ed8b92f':continue
 casa_minima(e,col)
for i,ff in enumerate(frentes[:2]):
 p=ff.punto(ff.largo*.55,0,2.0)
 farol_pie(f'M064_farol_{i}',p.x,p.y,col,alto=5.2)
revisar_correcciones('M064',[23,24],frentes)
