"""Iteración selectiva del repaso #22; conserva los otros edificios propios."""
import os,sys
import bpy
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from mobiliario_junin_oeste import construir_mobiliario
mid=next(a.split('=',1)[1] for a in sys.argv if a.startswith('--mid='))
assert mid in ('M027','M037')
m,col=iniciar('codex',mid)
bpy.ops.import_scene.gltf(filepath=os.path.join(datos.RAIZ,'web/public/models/ciudad/codex',mid+'.glb'))
for ob in list(bpy.context.scene.objects):
    if ob.type!='MESH':continue
    if ob.name.startswith(mid+'_Junin_') or (mid=='M037' and ob.name=='Eeb6abd'):
        me=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
        if me.users==0:bpy.data.meshes.remove(me)
    else:
        for cc in list(ob.users_collection):cc.objects.unlink(ob)
        col.objects.link(ob)
if mid=='M037':
    from convento_junin import construir_convento
    construir_convento(edificio(mid,'Eeb6abd'),col)
construir_mobiliario(mid,col)
exportar('codex',mid)
