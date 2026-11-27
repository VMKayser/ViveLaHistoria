"""Detalles de fachadas de la plaza. Solo geometría propia de Codex."""
import math,os,json,sys
import bpy
from kit import *
from piezas_codex import trasladar,rama,prisma_seguro,arbol_podado
BLANCO='#eeeae3';PIEDRA='#d3c6b0';MADERA='#704644'

def frente(e,c):
 ls=lados(e['huella'])
 # El frente hacia la plaza mira al noroeste, incluso si el detector no lo marca.
 candidatos=[l for l in ls if l['normal'][0]<-.65 and l['normal'][1]>.4]
 l=max(candidatos,key=lambda l:l['largo'])
 return Fachada(c,l,max(altura_suelo(*p) for p in e['huella']))

def barra(f,a,b,r=.025,rol='moldura',color=BLANCO):
 rama(f.c,f.punto(*a),f.punto(*b),r,r,rol,color)

def balustrada(f,a,b,h,d=.68):
 f.caja(a,b,h-.12,h,0,d+.1,'moldura',BLANCO)
 f.caja(a,b,h+.84,h+.96,d-.10,d+.1,'moldura',BLANCO)
 n=max(2,int((b-a)/.23))
 for k in range(n):
  s=a+(k+.5)*(b-a)/n
  # Perfil torneado continuo: una malla por balaustre, sin esferas
  # solapadas ni cientos de operadores globales sobre una malla grande.
  perfil=((0,.035),(.12,.035),(.25,.025),(.38,.065),(.52,.052),(.66,.024),(.78,.035),(.85,.035))
  for (hh0,r0),(hh1,r1) in zip(perfil,perfil[1:]):
   for j in range(6):
    t=j*math.tau/6;u=(j+1)*math.tau/6
    f.c.poligono([f.punto(s+r0*math.cos(t),h+hh0,d+r0*math.sin(t)),
      f.punto(s+r0*math.cos(u),h+hh0,d+r0*math.sin(u)),
      f.punto(s+r1*math.cos(u),h+hh1,d+r1*math.sin(u)),
      f.punto(s+r1*math.cos(t),h+hh1,d+r1*math.sin(t))],'moldura',BLANCO)
 for s in (a,b):f.caja(s-.06,s+.06,h,h+.95,d-.08,d+.08,'moldura',BLANCO)

def rustica(f,H,paso=.38):
 for j in range(int(H/paso)):
  h=j*paso
  f.caja(0,f.largo,h,h+.012,.003,.012,'moldura','#cbd0c8')

def flautas(f,s,h0,h1,ancho=.25):
 pilastra(f,s,h0,h1,ancho=ancho,vuelo=.095,color=BLANCO)
 for ds in (-ancho*.27,0,ancho*.27):
  f.caja(s+ds-.009,s+ds+.009,h0+.18,h1-.25,.096,.11,'moldura','#c7c8bd')

def flores(f,s,h,r=.2,color=BLANCO):
 # Núcleo sujeto al paramento: las flores pequeñas no quedan suspendidas.
 rama(f.c,f.punto(s,h,-.025),f.punto(s,h,.17),r*.28,r*.28,'moldura',color)
 for k in range(6):
  a=k*math.tau/6
  f.c.esfera(*f.punto(s+r*.6*math.cos(a),h+r*.6*math.sin(a),.14),r*.34,'moldura',color,segmentos=4)
 f.c.esfera(*f.punto(s,h,.17),r*.35,'moldura',color,segmentos=4)

def volutas(f,s,h,ancho=1,color=BLANCO):
 for signo in (-1,1):
  f.arco(s+signo*ancho*.25,ancho*.16,.025,h,-.02,.10,'moldura',color,segmentos=10,medio=False)
 flores(f,s,h+.07,.13,color)

def vano(f,s,h,w,H,arco=False):
 ventana(trasladar(f,d=.024),s,h,ancho=w,alto=H-(w/2 if arco else 0),arco=arco,
         color_carpinteria=MADERA,color_moldura=BLANCO)

def cuerpo(e,H,col):
 c=Constructor(e['id']);f,guia=frente_encadenado(e,c)
 c._edificio=e;c._alto=H;c._guia=guia;c._fachada=f
 return c,f


def revisar_correcciones(mid,numeros,frentes,miradas=None):
 from kit import salida
 original=salida._luz_y_mundo
 def luz():
  original();bpy.data.objects['sol'].rotation_euler=(math.radians(40),0,math.radians(-35 if mid=='M061' and any(88<=n<=95 for n in numeros) else 145))
  sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising='--sin-denoise' not in sys.argv;sc.render.threads_mode='FIXED';sc.render.threads=int(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--hilos=')),8))
 salida._luz_y_mundo=luz
 # FOV vertical 68° del revisor: sensor horizontal de 36 mm a 4:3.
 # Ajuste local; no se cambia la cámara compartida del kit.
 camara_original=salida.camara
 lente_revision=float(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--lente=')),20))
 lentes_por_posicion={}
 def camara_revision(pos,mirar,lente=lente_revision):
  lente=lentes_por_posicion.get(tuple(round(float(v),3) for v in pos),lente)
  return camara_original(pos,mirar,lente=lente)
 salida.camara=camara_revision
 raiz=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
 camaras=[]
 for n in numeros:
  d=json.load(open(os.path.join(raiz,f'coordinacion/revisiones/R{n:04}/revision.json')))
  p=d['escena']['camara']['lienzo'];q=d['escena'].get('centro')
  if miradas and n in miradas:
   q=dict(zip(('x','y','z'),miradas[n]))
   if len(miradas[n])>3:lentes_por_posicion[tuple(round(float(p[k]),3) for k in ('x','y','z'))]=miradas[n][3]
  if not q:
   az=math.radians(d['escena']['camara']['rumbo_grados']);inc=math.radians(d['escena']['camara']['inclinacion_grados'])
   q={'x':p['x']+20*math.sin(az)*math.cos(inc),'y':p['y']+20*math.cos(az)*math.cos(inc),'z':p['z']+20*math.sin(inc)}
  elevacion=float(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--mirada=')),0))
  camaras.append((f'R{n:04}',tuple(p[k] for k in ('x','y','z')),(q['x'],q['y'],q['z']+elevacion)))
 for i,f in enumerate(frentes):
  for esquina,s in (('inicio',.2),('fin',f.largo-.2)):
   p=f.punto(s,0,1.1);q=f.punto(f.largo*.5,min(4.5,1.8+f.largo*.12))
   camaras.append((f'pie_{i}_{esquina}',(p.x,p.y,altura_suelo(p.x,p.y)+1.6),tuple(q)))
 seleccion=next((a.split('=',1)[1].split(',') for a in sys.argv if a.startswith('--vistas=')),None)
 if seleccion:camaras=[v for v in camaras if v[0] in seleccion]
 if camaras:
  from contexto_codex import instalar_contexto
  instalar_contexto([p for _,ojo,mirada in camaras for p in (ojo,mirada)],margen=22,solo_terreno='--solo-manzana' in sys.argv)
  if '--solo-manzana' in sys.argv:
   salida.dir_revision=lambda ag,mid:os.path.join(datos.RAIZ,'revisiones/codex',mid,'diagnostico_aislado')
 ancho=int(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--ancho=')),1000))
 revisar('codex',mid,fotos=[],camaras_extra=camaras,ancho=ancho,alto=ancho*3//4)
 if '--exportar' in sys.argv:exportar('codex',mid)


def frente_encadenado(e,c,z=None):
 """Frente completo NO sobre la polilínea recortada, no solo su tramo mayor.

 Se construye en plano y se divide en los quiebres antes de deformarlo.
 Así molduras, losas y dinteles siguen el cuerpo de la casa sin flotar.
 """
 from mathutils import Vector
 ls=[l for l in lados(e['huella']) if l['normal'][0]<-.64 and l['normal'][1]>.4 and l['a_calle']]
 if not ls:raise ValueError('No hay frente NO en '+e.get('id','huella propia'))
 # La huella orientada ya entrega los lados de fachada consecutivos.
 ls.sort(key=lambda l:l['i'])
 # Reordenar si la cadena cruza el índice cero.
 if len(ls)>1:
  for i in range(len(ls)):
   orden=ls[i:]+ls[:i]
   if all(math.dist(a['b'],b['a'])<.015 for a,b in zip(orden,orden[1:])):
    ls=orden;break
 longitud=sum(math.dist(l['a'],l['b']) for l in ls)
 a=Vector((*ls[0]['a'],0));u=(Vector((*ls[0]['b'],0))-a).normalized()
 z=max(altura_suelo(*p) for p in e['huella']) if z is None else z
 f=Fachada(c,{'a':tuple(a[:2]),'b':tuple((a+u*longitud)[:2]),'normal':ls[0]['normal']},z)
 guia={'lados':ls,'suelo':z,'a':f.a.copy(),'u':f.u.copy(),'n':f.n.copy(),'largo':longitud}
 return f,guia


def punto_encadenado(guia,s,h,d=0):
 from mathutils import Vector
 resto=s
 for k,l in enumerate(guia['lados']):
  a=Vector((*l['a'],0));b=Vector((*l['b'],0));L=(b-a).length
  if resto<=L or k==len(guia['lados'])-1:
   normal=Vector((*l['normal'],0))
   if k<len(guia['lados'])-1 and abs(resto-L)<.0001:
    siguiente=Vector((*guia['lados'][k+1]['normal'],0))
    normal=(normal+siguiente)/max(.1,1+normal.dot(siguiente))
   p=a+(b-a).normalized()*resto+normal*d
   return Vector((p.x,p.y,guia['suelo']+h))
  resto-=L


def ajustar_fachada(c,guia):
 import bmesh
 # Partir cada cara en los cambios de dirección: no queda ninguna banda
 # uniendo los extremos por una cuerda recta que se meta en el volumen.
 acumulado=0
 for l in guia['lados'][:-1]:
  acumulado+=math.dist(l['a'],l['b'])
  bmesh.ops.bisect_plane(c.bm,geom=list(c.bm.verts)+list(c.bm.edges)+list(c.bm.faces),
   dist=.00001,plane_co=guia['a']+guia['u']*acumulado,plane_no=guia['u'])
 for v in c.bm.verts:
  delta=v.co-guia['a'];s=delta.dot(guia['u']);d=delta.dot(guia['n'])
  v.co=punto_encadenado(guia,s,v.co.z-guia['suelo'],d)


def terminar_cuerpo(c,col):
 ajustar_fachada(c,c._guia)
 e=c._edificio;z=c._guia['suelo']
 prisma_seguro(c,e['huella'],min(altura_suelo(*p) for p in e['huella'])-.6,z+c._alto,'muro',BLANCO)
 c._fachada.punto=lambda s,h,d=0:punto_encadenado(c._guia,s,h,d)
 return c.objeto(col)


def huella_usfx():
 """Franja faltante del lienzo, recortada a las calles actuales."""
 inicio,guia=frente_encadenado(manzana('M057')['edificios'][1],None)
 a=punto_encadenado(guia,0,0);b=punto_encadenado(guia,inicio.largo,0)
 dx,dy=b.x-a.x,b.y-a.y;L=math.hypot(dx,dy);u=(dx/L,dy/L)
 b=(a.x+u[0]*30,a.y+u[1]*30);a=(a.x,a.y);n=(u[1],-u[0])
 h=[a,b,(b[0]-n[0]*6,b[1]-n[1]*6),(a[0]-n[0]*6,a[1]-n[1]*6)]
 return datos.recortar_a_calles(h)
