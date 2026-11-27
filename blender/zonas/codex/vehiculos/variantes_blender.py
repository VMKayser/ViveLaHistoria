"""Guarda copias Blender de la misma escena con cuatro pinturas.

blender -b web/public/models/ciudad/codex/vehiculos/autobus_bronco.blend
  -P blender/zonas/codex/vehiculos/variantes_blender.py
No reconstruye, remalla ni renderiza la geometría; conserva rig, NLA y estudio.
"""
import json
import shutil
import sys
from pathlib import Path

import bpy

DIRECTORIO = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORIO))
from generar_variantes import color_lineal  # noqa: E402
RAIZ = DIRECTORIO.parents[3]
SALIDA = RAIZ / "web/public/models/ciudad/codex/vehiculos"
datos = json.loads((DIRECTORIO / "bronco.json").read_text())
materiales = {k: bpy.data.materials["pintura_acento__"+datos["colores"][h].lstrip("#")]
              for k, h in [("principal", "azul"), ("detalle", "azul_claro")]}
bpy.context.preferences.filepaths.save_version = 0
shutil.copyfile(SALIDA / "autobus_bronco.blend", SALIDA / "autobus_bronco_azul.blend")
for id_color, variante in datos["variantes"].items():
    if id_color == "azul":
        continue
    for k, m in materiales.items():
        m.name = "pintura_acento__"+variante[k].lstrip("#")
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color_lineal(variante[k]), 1)
        m.diffuse_color = (*color_lineal(variante[k]), 1)
        m["pintura_bronco"] = k
    bpy.data.objects["autobus_bronco"]["variante"] = id_color
    bpy.ops.wm.save_as_mainfile(filepath=str(SALIDA / f"autobus_bronco_{id_color}.blend"))
