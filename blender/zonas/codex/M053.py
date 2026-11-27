"""M053 — cooperativa, remate, mirador y café: inventario en INVENTARIO_PLAZA.md."""
import os,sys,math,json
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from plaza_este import construir_M053
AGENTE='codex';MID='M053'
m,col=iniciar(AGENTE,MID)
f,fm,f2=construir_M053(m,col)
camaras=[]
raiz=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
for i in range(13,17):
 d=json.load(open(os.path.join(raiz,f'coordinacion/revisiones/R{i:04}/revision.json')))
 p=d['escena']['camara']['lienzo'];q=d['escena']['centro']
 camaras.append((f'R{i:04}',tuple(p[k] for k in ('x','y','z')),tuple(q[k] for k in ('x','y','z'))))
for nombre,ff,ss in [('esquina',f,0),('calvo',f,7),('mirador',fm,2.5),('cafe',f2,6)]:
 p=ff.punto(ss,0,2.0);q=ff.punto(min(ss+6,ff.largo),3.5)
 camaras.append(('pie_'+nombre,(p.x,p.y,altura_suelo(p.x,p.y)+1.6),tuple(q)))
# Luz de comparación de frente; el modelo conserva únicamente albedo.
from kit import salida
_luz_original=salida._luz_y_mundo
def luz_comparacion():
 _luz_original()
 import bpy
 bpy.data.objects['sol'].rotation_euler=(math.radians(40),0,math.radians(145))
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=12;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=8
salida._luz_y_mundo=luz_comparacion
seleccion=next((a.split('=',1)[1].split(',') for a in sys.argv if a.startswith('--vistas=')),None)
if seleccion:camaras=[v for v in camaras if v[0] in seleccion]
revisar(AGENTE,MID,fotos=[],camaras_extra=camaras,ancho=1200,alto=900)
# Exportación explícita después de la inspección de renders.
if '--exportar' in sys.argv:exportar(AGENTE,MID)
