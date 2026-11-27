"""Figura de bronce de pie para el remate del monumento a Sucre (R0145/R0151), desde un modelo real CC0.

Origen: "Statue holding a lightpost" (OpenGameArt, CC0 1.0) — https://opengameart.org/content/statue-holding-lightpost
Se separa la estatua del farol, se reduce, se escala a ~3,4 m y se guarda `assets/estatua.glb` (base en z=0, frente hacia +X).
Es una figura de pie con el brazo extendido: no es la efigie exacta de Sucre (no hay modelo libre de ella).
    ~/apps/blender-5.2.3-linux-x64/blender -b -P blender/zonas/claude/preparar_estatua.py
"""
import os
import sys

import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
ORIGEN = os.path.join(RAIZ, "recursos", "originales", "esculturas", "statue_lightpost", "Statue", "Statue_With_Lamp_LP.obj")
SALIDA = os.path.join(AQUI, "assets", "estatua.glb")
sys.path.insert(0, os.path.join(RAIZ, "blender"))
from kit import paleta  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=ORIGEN)
mallas = [o for o in bpy.data.objects if o.type == "MESH"]
print("OBJ partes", [(o.name, len(o.data.polygons), tuple(round(x, 2) for x in o.dimensions)) for o in mallas])
bpy.ops.object.select_all(action="DESELECT")
for o in mallas:
    o.select_set(True)
bpy.context.view_layer.objects.active = mallas[0]
if len(mallas) > 1:
    bpy.ops.object.join()
o = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# partir en islas y quedarse con la más voluminosa (la estatua); el farol es otra isla
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.separate(type="LOOSE")
bpy.ops.object.mode_set(mode="OBJECT")
partes = [p for p in bpy.data.objects if p.type == "MESH"]
partes.sort(key=lambda p: -len(p.data.polygons))
print("islas", [(p.name, len(p.data.polygons), tuple(round(x, 2) for x in p.dimensions)) for p in partes[:6]])
est = partes[0]
for p in partes[1:]:
    bpy.data.objects.remove(p, do_unlink=True)
bpy.ops.object.select_all(action="DESELECT")
est.select_set(True)
bpy.context.view_layer.objects.active = est
GIRO = float(os.environ.get("GIRO", "270"))
import math
est.rotation_euler = (0, 0, math.radians(GIRO))
bpy.ops.object.transform_apply(rotation=True)
alto = est.dimensions.z
est.scale = (3.4 / alto,) * 3
bpy.ops.object.transform_apply(scale=True)
pts = [Vector(c) for c in est.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
for v in est.data.vertices:
    v.co -= Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
est.modifiers.new("dec", "DECIMATE").ratio = min(1.0, 4000 / len(est.data.polygons))
bpy.ops.object.modifier_apply(modifier="dec")
est.data.materials.clear()
est.data.materials.append(paleta.material("metal", "#6f4b2c"))
for p in est.data.polygons:
    p.use_smooth = True
est.name = "estatua"
print("estatua", len(est.data.polygons), tuple(round(x, 2) for x in est.dimensions))
bpy.ops.object.select_all(action="DESELECT")
est.select_set(True)
bpy.ops.export_scene.gltf(filepath=SALIDA, export_format="GLB", use_selection=True, export_yup=True,
                          export_apply=True, export_normals=True, export_materials="EXPORT")
