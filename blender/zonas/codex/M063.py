"""M063: cuerpo posterior del Museo Eclesiástico, sin fachada a la calle.

El POI OSM está dentro de este cuerpo. Las fotos 130907–130916 muestran
su frente de cinco ejes sobre la huella contigua E02ae75 (M061), que se
modela allí. Mantener aquí la huella original evita duplicar ese frente
y fabricar un pasaje entre dos fachadas del mismo museo.
"""
import os,sys
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from kit import *
from piezas_codex import prisma_seguro,rama
from casas_codex import cubierta_baja
m,col=iniciar('codex','M063');e=m['edificios'][0];h=e['huella']
z=max(altura_suelo(*p) for p in h)
c=Constructor(e['id'])
prisma_seguro(c,h,min(altura_suelo(*p) for p in h)-.4,z+8.4,'muro','#eeeae1')
# Cubierta de teja del cuerpo posterior y cornisa interior. El frente
# real de cinco ejes está en M061: no se duplica una fachada en medianera.
cubierta_baja(c,h,z+8.4,'#b66b4d')
for l in lados(h):
    f=Fachada(c,l,z)
    for hh in (8.05,8.22,8.37):
        f.caja(0,f.largo,hh,hh+.11,-.22,0,'moldura','#eeeae1')
# Cumbrera de piezas de teja, dentro de la huella: el cuerpo posterior
# se lee como una cubierta colonial sin inventar portones en medianeras.
import math
l=max(lados(h),key=lambda l:l['largo']);f=Fachada(c,l,z)
vs=[(p[0]-f.a.x)*f.n.x+(p[1]-f.a.y)*f.n.y for p in h]
vm=(min(vs)+max(vs))/2;lev=min(1.85,max(.45,(max(vs)-min(vs))*.18))
ss=[(p[0]-f.a.x)*f.u.x+(p[1]-f.a.y)*f.u.y for p in h]
inicio,fin=min(ss),max(ss)
for i in range(math.ceil((fin-inicio)/.38)):
    t=inicio+(i+.5)*.38
    esquinas=[f.punto(t+a,0,vm+b) for a,b in ((-.18,-.15),(.18,-.15),(.18,.15),(-.18,.15))]
    if all(datos._dentro(p.x,p.y,h) for p in esquinas):
        rama(c,f.punto(t-.18,8.4+lev+.025,vm),f.punto(t+.18,8.4+lev+.025,vm),.13,.13,'teja','#b96b4c')
c.objeto(col)
exportar('codex','M063')
