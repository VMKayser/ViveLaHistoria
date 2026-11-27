"""Iteración local de un edificio de Dalence conservando sus vecinos propios.
El script canónico M055/M061 sigue reconstruyendo la manzana completa.
Uso con ejecutar.py: actualizar_dalence.py --mid=M055 --sin-render
"""
import os,sys
import bpy
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from kit import *
from dalence_codex import asamblea,edificio_moderno
mid=next(a.split('=',1)[1] for a in sys.argv if a.startswith('--mid='))
target,funcion={'M055':('Eae1b1b',asamblea),'M061':('E00e8b2',edificio_moderno)}[mid]
m,col=iniciar('codex',mid)
bpy.ops.import_scene.gltf(filepath=os.path.join(datos.RAIZ,'web/public/models/ciudad/codex',mid+'.glb'))
for ob in list(bpy.context.scene.objects):
 if ob.type!='MESH':continue
 if (ob.name in (target,'M061_arbol_Dalence') and '--solo-mobiliario' not in sys.argv) or ob.name.startswith(mid+'_Dalence_'):
  me=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
  if me.users==0:bpy.data.meshes.remove(me)
 else:
  for co in list(ob.users_collection):co.objects.unlink(ob)
  col.objects.link(ob)
if '--solo-mobiliario' not in sys.argv:funcion(edificio(mid,target),col)
from dalence_codex import mobiliario_dalence
mobiliario_dalence(mid,col)
exportar('codex',mid)
