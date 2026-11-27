"""Plantas de los canteros de la plaza (R0152/R0153/R0154) a partir del Stylized Nature MegaKit (Quaternius, CC0, ya
registrado en recursos/LICENCIAS.md). Reasigna los materiales a roles de la paleta (hojas → follaje, flores → flor con color
propio), reduce triángulos y guarda cada variante en `assets/`.
    ~/apps/blender-5.2.3-linux-x64/blender -b -P blender/zonas/claude/preparar_plantas.py
"""
import os
import sys

import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
KIT = os.path.join(RAIZ, "recursos", "originales", "quaternius_nature_megakit")
sys.path.insert(0, os.path.join(RAIZ, "blender"))
from kit import paleta  # noqa: E402

# (archivo, salida, triángulos máx., color de hojas, color de flores)
PLANTAS = [
    ("Bush_Common_Flowers", "arbusto_flor_rosa", 520, "#4f7f2f", "#e58aa8"),
    ("Bush_Common_Flowers", "arbusto_flor_amarilla", 520, "#4f7f2f", "#f2c230"),
    ("Flower_4_Group", "flores_naranja", 220, "#5d8f33", "#ee7a22"),
    ("Flower_4_Group", "flores_amarilla", 220, "#5d8f33", "#f4d03f"),
    ("Flower_3_Group", "flores_roja", 200, "#5d8f33", "#d6432f"),
    ("Plant_1_Big", "planta_grande", 300, "#6f9b3a", None),
    ("Fern_1", "helecho", 200, "#5b8a34", None),
]


def ruta(nombre):
    for r, _, fs in os.walk(KIT):
        if nombre + ".gltf" in fs:
            return os.path.join(r, nombre + ".gltf")
    raise FileNotFoundError(nombre)


for archivo, salida, tris, c_hoja, c_flor in PLANTAS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=ruta(archivo))
    mallas = [o for o in bpy.data.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in mallas:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mallas[0]
    if len(mallas) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    mats = [m.name for m in o.data.materials]
    nuevo = [paleta.material("flor", c_flor) if ("Flower" in n and c_flor) else paleta.material("follaje", c_hoja)
             for n in mats]
    for i, m in enumerate(nuevo):
        o.data.materials[i] = m
    o.modifiers.new("dec", "DECIMATE").ratio = min(1.0, tris / max(1, len(o.data.polygons)))
    bpy.ops.object.modifier_apply(modifier="dec")
    for p in o.data.polygons:
        p.use_smooth = True
    o.name = salida
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(AQUI, "assets", salida + ".glb"), export_format="GLB",
                              use_selection=True, export_yup=True, export_apply=True, export_normals=True,
                              export_materials="EXPORT")
    print("OK", salida, len(o.data.polygons), [tuple(round(x, 2) for x in o.dimensions)])
