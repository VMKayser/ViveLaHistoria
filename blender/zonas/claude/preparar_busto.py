"""Prepara el busto de mármol de los monumentos menores de la plaza (R0159) desde un modelo real CC0.

Origen: "Marble Bust 01", Poly Haven (CC0 1.0), https://polyhaven.com/a/marble_bust_01 (escaneo, 17 000 triángulos).
Se reduce a ~2 500 triángulos, material de piedra clara (rol `piedra`) y se guarda `assets/busto.glb` de 1 m de alto,
base en z=0 centrada.
    ~/apps/blender-5.2.3-linux-x64/blender -b -P blender/zonas/claude/preparar_busto.py
"""
import os
import sys

import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
ORIGEN = os.path.join(RAIZ, "recursos", "originales", "esculturas", "marble_bust_01", "marble_bust_01.gltf")
SALIDA = os.path.join(AQUI, "assets", "busto.glb")
sys.path.insert(0, os.path.join(RAIZ, "blender"))
from kit import paleta  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=ORIGEN)
o = [o for o in bpy.data.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = o
o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
alto = o.dimensions.z
o.scale = (1 / alto,) * 3
bpy.ops.object.transform_apply(scale=True)
pts = [Vector(c) for c in o.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
for v in o.data.vertices:
    v.co -= Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
mod = o.modifiers.new("dec", "DECIMATE")
mod.ratio = 800 / len(o.data.polygons)
bpy.ops.object.modifier_apply(modifier="dec")
o.data.materials.clear()
o.data.materials.append(paleta.material("piedra", "#d9d0bb"))
for p in o.data.polygons:
    p.use_smooth = True
o.name = "busto"
print("tris", len(o.data.polygons), o.dimensions)
bpy.ops.object.select_all(action="DESELECT")
o.select_set(True)
bpy.ops.export_scene.gltf(filepath=SALIDA, export_format="GLB", use_selection=True, export_yup=True,
                          export_apply=True, export_normals=True, export_materials="EXPORT")
