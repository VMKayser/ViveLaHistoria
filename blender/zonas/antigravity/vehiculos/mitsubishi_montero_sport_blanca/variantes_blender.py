"""Genera copias `.blend` por variante de pintura de la Mitsubishi Montero Sport sin reconstruir geometría."""
import json
import shutil
import sys
from pathlib import Path

import bpy

DIRECTORIO = Path(__file__).resolve().parent
RAIZ = DIRECTORIO.parents[4]
SKILL_SCRIPTS = RAIZ / ".agents" / "skills" / "vehiculo-3d-desde-diseno" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
from generar_variantes_glb import color_lineal  # noqa: E402

D = json.loads((DIRECTORIO / "mitsubishi_montero_sport_blanca.json").read_text())
SALIDA = RAIZ / "web" / "public" / "models" / "ciudad" / "antigravity" / "vehiculos" / D["id"]
pred = D["variante_predeterminada"]
hex_base = D["variantes"][pred]["principal"].lstrip("#").lower()
mat_pintura = bpy.data.materials[f"muro__{hex_base}"]

bpy.context.preferences.filepaths.save_version = 0
shutil.copyfile(SALIDA / f"{D['id']}.blend", SALIDA / f"{D['id']}_{pred}.blend")

for id_var, info in D["variantes"].items():
    if id_var == pred:
        continue
    hex_nuevo = info["principal"].lstrip("#").lower()
    mat_pintura.name = f"muro__{hex_nuevo}"
    rgba = (*color_lineal(info["principal"]), 1.0)
    mat_pintura.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = rgba
    mat_pintura.diffuse_color = rgba
    mat_pintura["pintura_vehiculo"] = "principal"
    bpy.data.objects[D["id"]]["variante"] = id_var
    bpy.ops.wm.save_as_mainfile(filepath=str(SALIDA / f"{D['id']}_{id_var}.blend"))
