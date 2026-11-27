"""Maestro editable del GLB adaptado, con las formas clave y sus pistas."""
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from construir import PUBLICO, guardar_estudio

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.render.fps = 24
bpy.ops.import_scene.gltf(filepath=str(PUBLICO/"caballo_rome.glb"))
raiz = bpy.data.objects["caballo_rome"]

# Blender recibe normales planas y las formas originales del caballo.
for o in raiz.children_recursive:
    if o.type == "MESH":
        for cara in o.data.polygons:
            cara.use_smooth = False
    for id_anim in (o,getattr(o.data,"shape_keys",None)):
        if id_anim and id_anim.animation_data and id_anim.animation_data.nla_tracks:
            animacion = id_anim.animation_data
            # El importador deja una acción activa encima de las pistas NLA.
            animacion.action = None
            for pista in animacion.nla_tracks:
                pista.mute = pista.name != "reposo"
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 37
bpy.context.scene.frame_set(1)
estudio = dict(largo=3.2,ancho=.72,alto=1.86,ejes=(-.8,.51),semivia_ruedas=.24,radio_rueda=.23)
guardar_estudio(raiz,estudio,PUBLICO/"caballo_rome.blend")
