"""Iteración de limpieza conservando Catedral, Gobernación y Dalence.
La fuente canónica M055.py reproduce también estos cambios.
"""
import os,sys
import bpy
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from catedral_gobernacion import patio_institucional,suelo_frente_institucional,cubiertas_catedral
m,col=iniciar('codex','M055')
bpy.ops.import_scene.gltf(filepath=os.path.join(datos.RAIZ,'web/public/models/ciudad/codex/M055.glb'))
for ob in list(bpy.context.scene.objects):
    if ob.type!='MESH':continue
    if ob.name in ('E749b6b','M055_suelo_conjunto_institucional','M055_Catedral_cubiertas'):
        me=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
        if me.users==0:bpy.data.meshes.remove(me)
    else:
        for cc in list(ob.users_collection):cc.objects.unlink(ob)
        col.objects.link(ob)
patio_institucional(edificio('M055','E749b6b'),col)
suelo_frente_institucional(col)
cubiertas_catedral(col)
exportar('codex','M055')
