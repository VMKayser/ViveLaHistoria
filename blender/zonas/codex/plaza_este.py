"""Frente este de Plaza 25 de Mayo: inventario contado en INVENTARIO_PLAZA.md.
Funciones por edificio; geometría siempre sobre lados de huellas recortadas.
R0013–R0022. Medidas y conteos de vanos documentados antes de modelar.
"""
import math,os,sys,json
from kit import *
from piezas_codex import (prisma_seguro,trasladar,rama,arbol_podado,farol_pie,
 ventana_rebajada,recortar_interior,copa_elipsoide,objeto_vegetal,copa_fina,recorte_estricto)
from detalles_plaza_codex import *
from casas_codex import casa_minima
GRIS='#adb6b5';HIERRO='#343637';MADERA='#79504d'
def tramo(f,a,b,c=None):
 return Fachada(c or f.c,{'a':tuple(f.punto(a,0)[:2]),'b':tuple(f.punto(b,0)[:2]),'normal':tuple(f.n[:2])},f.suelo)

def barra(f,a,b,r=.025,rol='hierro',color=HIERRO):
 rama(f.c,f.punto(*a),f.punto(*b),r,r,rol,color)

def disco(f,s,h,r,d,rol='vidrio',color=None):
 f.c.poligono([f.punto(s+r*math.cos(k*math.tau/32),h+r*math.sin(k*math.tau/32),d) for k in range(32)],rol,color)

def oculo(f,s,h,r=.3):
 disco(f,s,h,r,.045)
 f.arco(s,r,.065,h,.05,.10,'moldura',GRIS,segmentos=16,medio=False)

def aro_hierro(f,s,h,r,d):
 # Anillo de sección triangular, seis tramos: conserva volumen y silueta.
 def p(a,b):
  return f.punto(s+(r+.012*math.cos(b))*math.cos(a),h+(r+.012*math.cos(b))*math.sin(a),d+.012*math.sin(b))
 for k in range(6):
  a=k*math.tau/6;b=(k+1)*math.tau/6
  for j in range(3):
   u=j*math.tau/3;v=(j+1)*math.tau/3
   f.c.poligono([p(a,u),p(b,u),p(b,v),p(a,v)],'hierro',HIERRO)

def reja(f,a,b,h,d=.8):
 for hh in (h,h+.12,h+.93,h+1.02):f.caja(a,b,hh,hh+.035,d-.025,d+.025,'hierro',HIERRO)
 n=max(1,int((b-a)/.45))
 for i in range(n):
  ss=a+(i+.5)*(b-a)/n
  for dh in (.5,):
   for signo in (-1,1):
    aro_hierro(f,ss+signo*.085,h+dh,.105,d)
  f.cilindro_vertical(ss,h,h+1.05,d,.013,'hierro',HIERRO,lados=4)
 for ss in (a,b):
  f.caja(ss-.025,ss+.025,h,h+1.06,0,d,'hierro',HIERRO)

def balcon(f,a,b,h):
 f.caja(a,b,h-.16,h,0,.86,'piedra',BLANCO)
 reja(f,a+.04,b-.04,h)
 for s in (a+.3,(a+b)/2,b-.3):
  barra(f,(s,h-.7,.03),(s,h-.13,.71),.045)

def almohadillado(f,H):
 for j in range(int(H/.46)):
  hh=j*.46
  f.c.poligono([f.punto(0,hh,.012),f.punto(f.largo,hh,.012),f.punto(f.largo,hh+.012,.012),f.punto(0,hh+.012,.012)],'moldura',GRIS)
  for k in range(int(f.largo/1.3)):
   ss=k*1.3+(.65 if j%2 else 0)
   f.c.poligono([f.punto(ss,hh+.01,.013),f.punto(ss+.012,hh+.01,.013),f.punto(ss+.012,hh+.46,.013),f.punto(ss,hh+.46,.013)],'moldura',GRIS)

def vano_cooperativa(f,s,h,w,alto,postigos=False,reja_=False):
 ff=trasladar(f,d=.02)
 ventana(ff,s,h,ancho=w,alto=alto,reja=reja_,color_moldura=GRIS,
         color_carpinteria=HIERRO)
 if postigos:
  for signo in (-1,1):
   a=s+signo*(w/2+.24)
   f.caja(a-.18,a+.18,h,h+alto,.04,.11,'madera',HIERRO)
   for k in range(int(alto/.18)):
    f.caja(a-.16,a+.16,h+k*.18,h+k*.18+.035,.11,.13,'madera','#4c4d49')

def cenefa(f,a,b,h,n):
 paso=(b-a)/n
 for k in range(n):
  s=a+(k+.5)*paso
  f.caja(s-paso*.43,s+paso*.43,h,h+.57,.025,.045,'moldura',GRIS)
  f.caja(s-paso*.33,s+paso*.33,h+.07,h+.5,.046,.055,'moldura',BLANCO)
  disco(f,s,h+.285,.13,.065,'moldura',GRIS)

def marquesina(f,a,b,h):
 # Dos faldones laterales y hastial central; apoyados en ménsulas.
 centro=(a+b)/2
 for aa,bb in ((a,centro-1.1),(centro+1.1,b)):
  f.c.poligono([f.punto(aa,h,.0),f.punto(bb,h,0),f.punto(bb,h-.2,.92),f.punto(aa,h-.2,.92)],'metal','#929b96',grosor=.045)
  for k in range(int((bb-aa)/.28)+1):
   ss=min(bb,aa+k*.28)
   barra(f,(ss,h+.035,0),(ss,h-.165,.92),.012)
 f.c.poligono([f.punto(centro-1.35,h-.2,.92),f.punto(centro,h+1.15,.92),f.punto(centro+1.35,h-.2,.92)],'madera',HIERRO)
 for signo in (-1,1):
  barra(f,(centro+signo*1.4,h-.26,.94),(centro,h+1.2,.94),.055)
 for ss in (a+.12,centro-1.1,centro+1.1,b-.12):
  barra(f,(ss,h-1.1,.05),(ss,h-.18,.9),.035)
  barra(f,(ss,h-1.1,.05),(ss,h,.05),.03)
  f.arco(ss,.14,.02,h-.72,.25,.29,'hierro',HIERRO,segmentos=8,medio=False)

def torre(f):
 # Torre apoyada desde el suelo: ningún cuerpo cuelga sobre ventanas.
 a,b=.0,1.55
 f.caja(a,b,-.5,9.2,-1.45,.025,'muro',BLANCO)
 for s in (a,b):f.caja(s-.05,s+.05,0,9.2,0,.08,'moldura',GRIS)
 vano_cooperativa(f,.78,4.1,.83,2.55)
 oculo(f,.78,7.55,.28)
 # Retorno ortogonal del mirador de esquina, visible desde Calvo.
 p=f.punto(0,0,-1.45);q=f.punto(0,0,0)
 lateral=Fachada(f.c,{'a':tuple(p[:2]),'b':tuple(q[:2]),'normal':(-f.u.x,-f.u.y)},f.suelo)
 vano_cooperativa(lateral,.72,4.1,.8,2.55);oculo(lateral,.72,7.55,.28)
 f.caja(-.15,1.7,8.35,8.48,-1.6,.18,'metal',HIERRO)
 centro=f.punto(.77,0,-.72)
 # Aguja cuadrada con rombos de chapa y nervios; base 8.48, punta 11.2.
 r=1.12;z=f.suelo
 esquinas=[(centro.x+r*math.cos(math.pi/4+k*math.pi/2),centro.y+r*math.sin(math.pi/4+k*math.pi/2),z+8.48) for k in range(4)]
 punta=(centro.x,centro.y,z+11.2)
 for k in range(4):
  p,q=esquinas[k],esquinas[(k+1)%4]
  f.c.poligono([p,q,punta],'metal','#b9c4c0')
  rama(f.c,p,punta,.025,.012,'metal','#e2e3db')
  for j in range(1,5):
   t=j/5
   aa=tuple(p[i]*(1-t)+punta[i]*t for i in range(3));bb=tuple(q[i]*(1-t)+punta[i]*t for i in range(3))
   rama(f.c,aa,bb,.014,.014,'metal','#e2e3db')
 f.c.cilindro(centro.x,centro.y,z+11.2,z+11.7,.018,'metal',lados=6)


def remate_escalonado(f,L):
 # Remate escalonado, óculo real sin disco de fondo, balcón con balaustres.
 c=f.c
 g=tramo(f,L,f.largo)
 g.caja(0,g.largo,0,7.7,-.2,.025,'muro',BLANCO)
 puerta(trasladar(g,d=.025),g.largo/2,ancho=2,alto=3.1,color=HIERRO,color_moldura=BLANCO)
 # Hastial por bandas que rodean el hueco, no un muro detrás del óculo.
 g.caja(0,g.largo,8.7,9.0,-.3,.02,'muro',BLANCO)
 for aa,bb in ((0,g.largo/2-.42),(g.largo/2+.42,g.largo)):
  g.caja(aa,bb,9,9.85,-.3,.02,'muro',BLANCO)
 g.caja(0,g.largo,9.85,10.0,-.3,.02,'muro',BLANCO)
 g.arco(g.largo/2,.42,.10,9.42,.02,.09,'moldura',GRIS,segmentos=16,medio=False)
 for k in range(4):
  a=.30+k*.32;b=g.largo-a
  g.caja(a,b,10+k*.28,10.28+k*.28,-.3,.02,'muro',BLANCO)
  g.caja(a-.045,b+.045,10.24+k*.28,10.3+k*.28,-.32,.08,'moldura',GRIS)
 cenefa(g,0,g.largo,7.9,5)
 for ss in (g.largo*.25,g.largo*.5,g.largo*.75):
  vano_cooperativa(g,ss,4.5,.55,2.35,postigos=(ss!=g.largo*.5))
 for ss in (.18,g.largo*.375,g.largo*.625,g.largo-.18):
  pilastra(g,ss,4.4,7.05,ancho=.12,vuelo=.09,color=BLANCO)
 g.arco(g.largo/2,.85,.10,7.1,-.02,.10,'moldura',GRIS,segmentos=20)
 for j in range(9):
  ang=j*math.pi/8
  barra(g,(g.largo/2,7.1,.06),(g.largo/2+.76*math.cos(ang),7.1+.76*math.sin(ang),.06),.016,'moldura',GRIS)
 g.caja(0,g.largo,4.05,4.18,0,.8,'piedra',BLANCO)
 for k in range(9):
  ss=.18+k*(g.largo-.36)/8
  g.cilindro_vertical(ss,4.18,5.15,.74,.035,'moldura',BLANCO)
  g.c.esfera(*g.punto(ss,4.65,.74),.085,'moldura',BLANCO,segmentos=6)
 g.caja(0,g.largo,5.15,5.27,.62,.85,'moldura',BLANCO)

def cooperativa(e,col):
 # Cuerpo principal y fachada de la cooperativa.
 c=Constructor(e['id']);h=e['huella'];z=max(altura_suelo(*p) for p in h)
 prisma_seguro(c,h,min(altura_suelo(*p) for p in h)-.6,z+8.7,'muro',BLANCO)
 # El lado que da a la plaza primero: con la plaza ensanchada (2026-11-24) un lado interior del lote quedó 18 cm más largo
 # y la fachada se dibujaba adentro, con un muro liso hacia la plaza (R0229, R0230).
 ls=lados(h);principal=max((l for l in ls if l['normal'][0]<-.7),key=lambda l:(l['a_calle'],l['largo']))
 f=Fachada(c,principal,z);coop=tramo(f,0,f.largo-3.4);L=coop.largo
 almohadillado(coop,8.7)
 # Tres vanos en planta baja, repetidos por encima del balcón.
 for ss in (L*.28,L*.56,L*.84):
  vano_cooperativa(coop,ss,.45,1.85,2.8,reja_=True)
  vano_cooperativa(coop,ss,4.1,1.25,2.85,postigos=True)
 # Basamento continuo solo bajo el alféizar, nunca tapa puertas.
 coop.caja(0,L,-.6,.42,0,.035,'zocalo_piedra','#aa927a')
 imposta(coop,3.9,alto=.18,color=GRIS)
 balcon(coop,2.15,L-.3,4.1)
 marquesina(coop,2.1,L-.1,7.15)
 cenefa(coop,1.55,L,8.02,12)
 coop.caja(0,L,8.75,8.86,-.2,.85,'metal',HIERRO)
 for i in range(15):
  ss=i*L/14
  barra(coop,(ss,8.1,.02),(ss,8.75,.75),.025)
 torre(coop)
 # Frente lateral a Calvo: seis ejes sin inventar balcones monumentales.
 for l in ls:
  if l['a_calle'] and l['normal'][0]>.3 and l['largo']>8:
   ff=Fachada(c,l,z)
   for k in range(5):
    ss=(k+.5)*ff.largo/5
    vano_cooperativa(ff,ss,1,1.05,2.1,reja_=True);vano_cooperativa(ff,ss,4.45,1.05,2.2)
   cornisa(ff,8.5,alto=.2,color=GRIS)
 remate_escalonado(f,L)
 c.objeto(col)

 return f,principal,z

def mirador_rojizo(e2,principal,z,col):
 # Mirador vecino: huella propia en el vacío del lienzo entre ambos edificios.
 _f2,_guia=frente_encadenado(e2,None);l2=_guia['lados'][0]
 a=principal['b'];b=l2['a'];n=principal['normal']
 cm=Constructor('M053_mirador');fm=Fachada(cm,{'a':a,'b':b,'normal':tuple(n[:2])},z)
 hm=[a,b,tuple(fm.punto(fm.largo,0,-7)[:2]),tuple(fm.punto(0,0,-7)[:2])]
 prisma_seguro(cm,hm,z-.6,z+8.45,'muro',BLANCO)
 for ss in (.65,fm.largo-.65):
  puerta(trasladar(fm,d=.02),ss,ancho=.95,alto=2.3,arco=True,color=MADERA,color_moldura=BLANCO)
 puerta(trasladar(fm,d=.025),fm.largo/2,ancho=min(2.05,fm.largo-2.65),alto=2.45,rol='vidrio',color='#3e4a43',color_moldura=BLANCO)
 # Mirador sale 0,65 m; madera opaca abajo, vidrios cuadriculados arriba.
 mi=tramo(fm,1.05,fm.largo-1.05);w=mi.largo
 mi.caja(0,w,3.7,6.8,0,.65,'madera',MADERA)
 for i in range(4):
  ss=(i+.5)*w/4
  ventana(trasladar(mi,d=.66),ss,4.65,ancho=w/4-.12,alto=1.55,
          color_carpinteria=MADERA,color_moldura=MADERA)
  mi.caja(ss-w/8+.06,ss+w/8-.06,3.83,4.48,.65,.7,'madera','#91635a')
 for ss in (0,w/2,w):
  mi.caja(ss-.04,ss+.04,3.7,6.82,.66,.76,'madera',MADERA)
 # Ventanas estrechas a ambos lados, y ménsulas apoyadas bajo el mirador.
 for ss in (.55,fm.largo-.55):
  ventana(trasladar(fm,d=.025),ss,4.55,ancho=.62,alto=1.65,
          color_carpinteria=MADERA,color_moldura=MADERA)
 for ss in (1.3,fm.largo/2,fm.largo-1.3):
  barra(fm,(ss,3.15,.01),(ss,3.68,.61),.065,'madera',MADERA)
 for ss in (fm.largo*.33,fm.largo*.5,fm.largo*.67):oculo(fm,ss,7.6,.23)
 alero_tejas(mi,6.86,vuelo=.85,fondo=.7,pendiente=20)
 alero_tejas(fm,8.4,vuelo=.35,fondo=2.0,pendiente=14)
 for ss in (.15,fm.largo-.15):pilastra(fm,ss,0,8.3,ancho=.2,color=BLANCO)
 cm.objeto(col)

 return fm

def cafe_tres_arcos(e2,col):
 # Café con tres arcos rebajados y terraza de hierro.
 c=Constructor(e2['id']);h=e2['huella'];z2=max(altura_suelo(*p) for p in h)
 f2,guia_cafe=frente_encadenado(e2,c,z2);L=f2.largo
 for k in range(3):
  s=(k+.5)*L/3;ww=L/3-.7
  puerta(trasladar(f2,d=.03),s,ancho=min(2.5,ww),alto=3.0,color='#685345',color_moldura=BLANCO)
  # Vidrio y rosca elíptica de luz ancha, no arcos de medio punto.
  f2.caja(s-ww/2,s+ww/2,4.35,6.6,.02,.035,'vidrio','#414c50')
  for j in range(24):
   a=j*math.pi/24;b=(j+1)*math.pi/24
   pa=(s-ww/2*math.cos(a),6.6+.72*math.sin(a),.06)
   pb=(s-ww/2*math.cos(b),6.6+.72*math.sin(b),.06)
   pc=(s-(ww/2+.10)*math.cos(b),6.6+.83*math.sin(b),.06)
   pd=(s-(ww/2+.10)*math.cos(a),6.6+.83*math.sin(a),.06)
   c.poligono([f2.punto(*p) for p in (pa,pb,pc,pd)],'moldura','#dbd5c5')
   c.poligono([f2.punto(s,6.6,.035),f2.punto(*pa),f2.punto(*pb)],'vidrio','#414c50')
 for k in range(4):
  ss=k*L/3
  pilastra(f2,ss,4.1,7.8,ancho=.25,color=BLANCO)
  f2.esfera(ss,7.65,.09,.12,'moldura',BLANCO)
 balcon(f2,0,L,4.1)
 cornisa(f2,8.0,alto=.55,vuelo=.32,color=BLANCO)
 # Pretil calado construido con aros, sin fondo opaco.
 f2.caja(0,L,8.55,8.78,-.23,.03,'moldura',BLANCO)
 f2.caja(0,L,9.25,9.36,-.23,.03,'moldura',BLANCO)
 for k in range(18):
  s=(k+.5)*L/18
  f2.arco(s,.19,.048,9.02,-.05,.025,'moldura',BLANCO,segmentos=10,medio=False)
  for j in range(8):
   a=j*math.tau/8
   barra(f2,(s,9.02,-.01),(s+.17*math.cos(a),9.02+.17*math.sin(a),-.01),.012,'moldura',BLANCO)
 cs=L/2
 c.poligono([f2.punto(cs-1,9.25,-.2),f2.punto(cs,10.12,-.2),f2.punto(cs+1,9.25,-.2)],'muro',BLANCO,grosor=.12,normal_extrusion=f2.n)
 for signo in (-1,1):barra(f2,(cs+signo*1.1,9.25,.03),(cs,10.2,.03),.065,'moldura',BLANCO)
 # Friso con guirnaldas y capiteles florales, visible en R0016.
 for k in range(12):
  ss=(k+.5)*L/12
  for j in range(6):
   t=j/5;hh=7.8-.12*math.sin(math.pi*t)
   f2.c.esfera(*f2.punto(ss-.34+.68*t,hh,.09),.04,'moldura','#d6d3c8',segmentos=6)
 for k in range(4):
  ss=k*L/3
  for ds in (-.12,0,.12):
   f2.c.esfera(*f2.punto(ss+ds,7.58+(.08 if ds==0 else 0),.13),.065,'moldura',BLANCO,segmentos=6)
 # Basamento y estrías de las portadas bajas, sin tapar los vanos.
 for k in range(4):
  ss=k*L/3
  f2.caja(ss-.28,ss+.28,-.5,.45,0,.055,'piedra','#c0ab92')
  for ds in (-.1,0,.1):f2.caja(ss+ds-.012,ss+ds+.012,.5,3.5,.02,.07,'moldura','#d5d0c5')
 ajustar_fachada(c,guia_cafe)
 prisma_seguro(c,h,min(altura_suelo(*p) for p in h)-.6,z2+8.8,'muro',BLANCO)
 c.objeto(col)
 f2.punto=lambda s,h,d=0:punto_encadenado(guia_cafe,s,h,d)
 return f2

def construir_M053(m,col):
 f,principal,z=cooperativa(m['edificios'][0],col)
 fm=mirador_rojizo(m['edificios'][1],principal,z,col)
 f2=cafe_tres_arcos(m['edificios'][1],col)
 # Árboles propios frente a los frentes; alcorques de BASE, sin suelo duplicado.
 for i,(ff,ss) in enumerate([(f,2.6),(f,6.6),(f,10.4),(f,14.7),(fm,2.8),(f2,2.4),(f2,9.4)]):
  p=ff.punto(ss,0,2.0)
  arbol_podado('M053_arbol_'+str(i),p.x,p.y,col,radio=1.5 if i!=1 else 1.8,alto=4.0,direccion=tuple(ff.n[:2]))
 p=f2.punto(5.4,0,1.6);farol_pie('M053_farol',p.x,p.y,col,alto=5.3)

 return f,fm,f2

def arco_vidrio(m,col):
 frentes=[]
 e=m['edificios'][0];c,f=cuerpo(e,13.5,col);L=f.largo;frentes.append(f)
 rustica(f,13.5)
 # Paño central desde la entreplanta hasta la rosca de coronación.
 s=L/2;ww=L*.28
 vano(f,s,4.0,ww,9.25,arco=True)
 for ds in (-ww*.27,0,ww*.27):
  f.caja(s+ds-.027,s+ds+.027,4,11.65,.075,.12,'marco_ventana',MADERA)
 for h in (4.25,5.45,6.65,7.85,9.05,10.25,11.45):
  f.caja(s-ww/2,s+ww/2,h,h+.045,.075,.13,'marco_ventana',MADERA)
 for lado in (-1,1):
  centro=L*(.22 if lado<0 else .78)
  for offset in (-.63,.63):
   ss=centro+offset
   for h in (4.15,7.4):
    vano(f,ss,h,1.03,2.35)
    balustrada(f,ss-.58,ss+.58,h,d=.25)
   flautas(f,ss-.63,4.0,9.9,ancho=.18)
  vano(f,centro,11.0,1.25,1.85,arco=True)
 for s in (L*.2,L*.8):
  puerta(trasladar(f,d=.025),s,ancho=2.1,alto=2.4,arco=True,color=MADERA,color_moldura=BLANCO)
 puerta(trasladar(f,d=.025),L/2,ancho=ww,alto=3.25,rol='vidrio',color='#39443e',color_moldura=BLANCO)
 for h in (3.6,10.1):cornisa(f,h,alto=.28,vuelo=.14,color=BLANCO)
 cornisa(f,13.3,alto=.2,vuelo=.12,color=BLANCO)
 terminar_cuerpo(c,col)
 # El frente continuo USFX de R0020/21 cruza los huecos del lienzo.
 # Se reconstruye una sola vez en M058; este id conserva su cuerpo interior.
 e=m['edificios'][1];c=Constructor(e['id']);fondo=frente(e,c);h=recortar_interior(e['huella'],fondo,-6);z=max(altura_suelo(*p) for p in e['huella'])
 prisma_seguro(c,h,min(altura_suelo(*p) for p in h)-.6,z+12.45,'muro',BLANCO)
 c.objeto(col)
 for i,f in enumerate(frentes):
  for j,s in enumerate((f.largo*.22,f.largo*.78)):
   p=f.punto(s,0,2.0);arbol_podado(f'M057_arbol_{i}_{j}',p.x,p.y,col,radio=1.5,alto=3.9,direccion=tuple(f.n[:2]))
 return frentes

def hotel_plaza(m,col):
 vecino,guia=frente_encadenado(manzana('M053')['edificios'][1],None);a=tuple(punto_encadenado(guia,vecino.largo,0)[:2]);vecino2,guia2=frente_encadenado(manzana('M057')['edificios'][0],None);b=tuple(punto_encadenado(guia2,0,0)[:2])
 c=Constructor('M059_hotel_plaza')
 u=((b[0]-a[0]),(b[1]-a[1]));l=math.hypot(*u);n=(u[1]/l,-u[0]/l)
 z=max(altura_suelo(*a),altura_suelo(*b))
 f=Fachada(c,{'a':a,'b':b,'normal':n},z);L=f.largo
 h=[a,b,tuple(f.punto(L,0,-7)[:2]),tuple(f.punto(0,0,-7)[:2])]
 h=datos.recortar_a_calles(h);f,guia_hotel=frente_encadenado({'id':'M059_hotel_plaza','huella':h},c,z);L=f.largo
 rustica(f,12.6)
 GRIS='#727f7b'
 for k in range(5):
  s=(k+.5)*L/5;w=1.35
  puerta(trasladar(f,d=.02),s,ancho=1.85,alto=3.15,arco=(k==0),color='#51483b',color_moldura=BLANCO)
  for h0 in (4.3,8.4):
   if k==2 and h0==4.3:
    ff=trasladar(f,d=.38)
    ff.caja(s-.95,s+.95,h0,h0+3.35,-.38,0,'madera','#7e908e')
    ventana(ff,s,h0+.35,ancho=1.65,alto=2.8,color_carpinteria='#748987',color_moldura='#8e9d98')
    for ds in (-.9,.9):ff.caja(s+ds-.04,s+ds+.04,h0,h0+3.35,0,.08,'marco_ventana','#748987')
   else:
    ventana_rebajada(trasladar(f,d=.025),s,h0,ancho=w,alto=2.75,color_moldura=GRIS)
    for signo in (-1,1):
     ss=s+signo*.87
     f.caja(ss-.15,ss+.15,h0,h0+2.65,.04,.12,'madera',MADERA)
     for j in range(20):f.caja(ss-.13,ss+.13,h0+.1+j*.12,h0+.13+j*.12,.12,.14,'madera','#63443c')
   if h0==8.4:
    for ds in (-.98,.98):
     pilastra(f,s+ds,h0,h0+3.2,ancho=.12,vuelo=.1,color=GRIS)
    volutas(f,s,h0+3.0,w,color=GRIS)
 for h0 in (4.3,8.4):
  for aa,bb in ((.3,L*.4-.2),(L*.6+.2,L-.3)):
   balustrada(f,aa,bb,h0,d=.68)
   for ss in (aa+.25,bb-.25):barra(f,(ss,h0-.65,.03),(ss,h0-.15,.6),.065,'piedra',PIEDRA)
 balustrada(f,L*.4,L*.6,8.4,d=.45)
 for h0 in (3.9,8.0,12.0):cornisa(f,h0,alto=.28,vuelo=.22,color=BLANCO)
 balustrada(f,0,L,12.65,d=-.12)
 s=L/2
 c.poligono([f.punto(s-1.7,12.6,.02),f.punto(s,13.7,.02),f.punto(s+1.7,12.6,.02)],'muro',BLANCO,grosor=.14,normal_extrusion=f.n)
 for signo in (-1,1):barra(f,(s+signo*1.8,12.6,.13),(s,13.8,.13),.08,'moldura',BLANCO)
 volutas(f,s,12.9,1.25,color=GRIS)
 for ss in (1,L-1):remate_bola(f,ss,13.4,radio=.15,rol='moldura',color=BLANCO)
 ajustar_fachada(c,guia_hotel)
 prisma_seguro(c,h,z-.65,z+12.6,'muro',BLANCO)
 c.objeto(col)
 f.punto=lambda s,h,d=0:punto_encadenado(guia_hotel,s,h,d)
 # Los ids del lienzo son cuerpos interiores: se conservan, sin duplicar la franja del hotel.
 for e in m['edificios']:
  casa_minima(e,col)
 # Árbol grande de la referencia, con bifurcación apoyada y copa amplia e irregular.
 # 1,6 m de la fachada (antes 2,0): con la vuelta de la plaza ensanchada el tronco quedaba sobre el bordillo (2026-11-24)
 p=f.punto(.5,0,1.6);x,y=p.x,p.y;z=altura_suelo(x,y)
 c=Constructor('M059_arbol_gigante')
 c.cilindro(x,y,z,z+1.8,.39,'tronco',lados=10,radio_arriba=.30)
 c.cilindro(x,y,z,z+.65,.395,'muro','#cfcec1',lados=10,radio_arriba=.36)
 for k,(ds,dd,hh) in enumerate(((-3.3,.2,7),(-1.8,-.3,8.7),(.1,.2,10),(2.8,.5,8.4),(4.2,-.3,7.8))):
  ds*=1.4;hh*=1.3
  q=f.punto(.5+ds,hh,3.6+dd)
  medio=(x+(q.x-x)*.3,y+(q.y-y)*.3,z+3.3)
  rama(c,(x,y,z+1.6),medio,.24,.16)
  medio_alto=(x+(q.x-x)*.68,y+(q.y-y)*.68,z+hh*.74)
  rama(c,medio,medio_alto,.16,.10)
  rama(c,medio_alto,(q.x,q.y,z+hh),.10,.045)
  for j in (-1,1):
   ex=q.x+j*.8;ey=q.y+j*.5
   dep=(ex-f.a.x)*f.n.x+(ey-f.a.y)*f.n.y
   if dep<3.9:ex+=f.n.x*(3.9-dep);ey+=f.n.y*(3.9-dep)
   rama(c,(q.x,q.y,z+hh-1),(ex,ey,z+hh+.3),.055,.025)
   copa_fina(c,ex,ey,z+hh,2.6,1.9,1.3,semilla=k*9+j)
 objeto_vegetal(c,col)
 for j,ss in enumerate((5.5,10.2,14.4)):
  p=f.punto(ss,0,2.0);arbol_podado(f'M059_arbol_podado_{j}',p.x,p.y,col,radio=1.5,alto=3.9,direccion=tuple(f.n[:2]))
 return [f]

def usfx(m,col):
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
  r=1.35
  f.arco(s,r,.20,10.05,-.025,.20,'moldura',BLANCO,segmentos=18)
  for j in range(11):
   a=j*math.pi/10
   flores(f,s-r*.86*math.cos(a),10.05+r*.86*math.sin(a),.075)
  for ds in (-r,r):flautas(f,s+ds,9.65,10.05,ancho=.15)
  flores(f,s,10.95,.17)
 # Cornisa festoneada: cinco arquivoltas unidas por la línea horizontal,
 # dentellones y claves; no cinco aros aislados flotando sobre los vanos.
 for k in range(6):
  aa=0 if k==0 else (k-.5)*paso+1.35
  bb=L if k==5 else (k+.5)*paso-1.35
  f.caja(aa,bb,10.02,10.19,-.025,.19,'moldura',BLANCO)
  for j in range(max(1,int((bb-aa)/.18))):
   ss=aa+(j+.5)*(bb-aa)/max(1,int((bb-aa)/.18))
   f.caja(ss-.025,ss+.025,9.9,10.03,-.02,.15,'moldura',BLANCO)
 for k in range(5):
  ss=(k+.5)*paso
  flores(f,ss,11.42,.20)
  f.caja(ss-.12,ss+.12,11.14,11.4,-.02,.22,'moldura',BLANCO)
  if k in (0,4):
   # Cristales de retorno: el mirador tiene tres caras, apoyado en ménsulas.
   for signo in (-1,1):
    pa=f.punto(ss+signo*1.18,0,0);pb=f.punto(ss+signo*1.18,0,.58)
    lat=Fachada(c,{'a':tuple(pa[:2]),'b':tuple(pb[:2]),'normal':tuple((f.u*signo)[:2])},z)
    ventana(trasladar(lat,d=.02),lat.largo/2,4.6,ancho=.35,alto=2.15,
            color_carpinteria=MADERA,color_moldura=BLANCO)
   for ds in (-.82,.82):
    barra(f,(ss+ds,3.85,0),(ss+ds,4.2,.55),.065,'moldura',BLANCO)
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
  p=f.punto(ss,0,2.0);arbol_podado(f'M058_arbol_{j}',p.x,p.y,col,radio=1.5,alto=4.0,direccion=tuple(f.n[:2]))
 return [f]

def ala_baja(m,col):
 _usfx,guia=frente_encadenado({'id':'USFX','huella':huella_usfx()},None)
 a=tuple(punto_encadenado(guia,_usfx.largo,0)[:2])
 e64=next(e for e in manzana('M064')['edificios'] if e['id']=='Ed8b92f')
 b=max(e64['huella'],key=lambda p:p[1]);dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);n=(dy/L,-dx/L)
 h=datos.recortar_a_calles([a,b,(b[0]-n[0]*6,b[1]-n[1]*6),(a[0]-n[0]*6,a[1]-n[1]*6)])
 h=recorte_estricto(h)
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
  p=f.punto(ss,0,2.0);arbol_podado(f'M065_arbol_{j}',p.x,p.y,col,radio=1.5,alto=3.9,direccion=tuple(f.n[:2]))
 p=f.punto(L*.55,0,2.0);farol_pie('M065_farol',p.x,p.y,col,alto=5.2)
 return [f]
