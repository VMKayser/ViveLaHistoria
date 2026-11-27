"""Iteración barata de la nave, conservando los otros edificios de M037."""
import os,sys
import bpy
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from nave_arenales import construir_nave
m,col=iniciar('codex','M037')
bpy.ops.import_scene.gltf(filepath=os.path.join(datos.RAIZ,'web/public/models/ciudad/codex/M037.glb'))
for ob in list(bpy.context.scene.objects):
    if ob.type!='MESH':continue
    if ob.name.startswith(('M037_SanMiguel_nave_Arenales','M037_SanMiguel_cubierta_Arenales','M037_SanMiguel_enredadera')):
        me=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
        if me.users==0:bpy.data.meshes.remove(me)
    else:
        for cc in list(ob.users_collection):cc.objects.unlink(ob)
        col.objects.link(ob)
construir_nave(col)
exportar('codex','M037')
