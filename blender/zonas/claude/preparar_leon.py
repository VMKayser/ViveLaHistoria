"""Prepara el león de bronce del monumento (R0151) a partir de un modelo real con licencia CC0.

Origen: "Lion" de Grab3D, CC0 1.0 (https://grab3d.com/models/animals/lion/), GLB ligero de 400 000 triángulos, en pie.
Lo que se hace aquí: poner al león echado (como los del monumento: patas delanteras extendidas, cuerpo apoyado), reducir a
~6 000 triángulos, material de bronce (rol `metal`) y guardar `assets/leon_bronce.glb` con la cabeza hacia +X, base en z=0.
    ~/apps/blender-5.2.3-linux-x64/blender -b -P blender/zonas/claude/preparar_leon.py
"""
import math
import os

import bpy
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
ORIGEN = os.path.join(RAIZ, "recursos", "originales", "esculturas", "lion-light.glb")
SALIDA = os.path.join(AQUI, "assets", "leon_bronce.glb")
TRIS = 3000

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=ORIGEN)
o = [o for o in bpy.data.objects if o.type == "MESH"][0]
n = len(o.data.vertices)
v = np.empty(n * 3)
o.data.vertices.foreach_get("co", v)
v = v.reshape(-1, 3)

# eje del cuerpo en planta (PCA); la cabeza es el extremo donde el cuerpo es más alto
xy = v[:, :2] - v[:, :2].mean(0)
w, vec = np.linalg.eigh(np.cov(xy.T))
u = vec[:, 1]
if v[(xy @ u) > np.percentile(xy @ u, 90), 2].mean() < v[(xy @ u) < np.percentile(xy @ u, 10), 2].mean():
    u = -u                                          # u apunta hacia la cabeza
side = np.array([-u[1], u[0]])
f = xy @ u
s = xy @ side
z = v[:, 2].copy()

zp = 0.62                                           # altura del vientre en pie
baja = 0.45                                         # cuánto baja el torso al echarse
f_sh = np.percentile(f, 80)                         # hombro: patas delanteras por delante de esto
f_mid = (np.percentile(f, 15) + np.percentile(f, 85)) / 2

f2, z2, s2 = f.copy(), z.copy(), s.copy()
torso = z >= zp
z2[torso] = z[torso] - baja
pata = ~torso
delant = pata & (f > f_mid)
trasera = pata & (f <= f_mid)
# patas delanteras: se acortan y se estiran hacia adelante sobre el suelo (zarpas adelantadas, como el león echado)
kd = z[delant] / zp
z2[delant] = 0.03 + kd * 0.2
f2[delant] = f[delant] + 0.55 * (1 - kd)
s2[delant] = s[delant] * (1 + 0.1 * (1 - kd))
# patas traseras: se pliegan bajo la grupa (se aplastan contra el suelo) con la zarpa algo adelantada
k = z[trasera] / zp
z2[trasera] = 0.02 + k * 0.17
f2[trasera] = f[trasera] + 0.25 * (1 - k)
s2[trasera] = s[trasera] * (1 + 0.25 * (1 - k))

xy2 = np.outer(f2, u) + np.outer(s2, side)
# cabeza hacia +X, centrado y apoyado
ang = -math.atan2(u[1], u[0])
c, sn = math.cos(ang), math.sin(ang)
xr = xy2[:, 0] * c - xy2[:, 1] * sn
yr = xy2[:, 0] * sn + xy2[:, 1] * c
nv = np.stack([xr - (xr.max() + xr.min()) / 2, yr - (yr.max() + yr.min()) / 2, z2 - z2.min()], 1)
# el mallado original pasa por f/s relativos al centro: el recentrado de arriba basta
o.data.vertices.foreach_set("co", nv.ravel())
o.data.update()

# reducir
bpy.context.view_layer.objects.active = o
o.select_set(True)
rem = o.modifiers.new("rem", "REMESH")           # cierra la malla (la melena son láminas con huecos) antes de reducir
rem.mode = "VOXEL"
rem.voxel_size = 0.022
bpy.ops.object.modifier_apply(modifier="rem")
print("tras remallar", len(o.data.polygons))
mod = o.modifiers.new("dec", "DECIMATE")
mod.ratio = TRIS / len(o.data.polygons)
bpy.ops.object.modifier_apply(modifier="dec")
# bronce
sys_path = os.path.join(RAIZ, "blender")
import sys
sys.path.insert(0, sys_path)
from kit import paleta
o.data.materials.clear()
o.data.materials.append(paleta.material("metal", "#8a5a30"))
for p in o.data.polygons:
    p.use_smooth = True
o.name = "leon_bronce"
print("tris", len(o.data.polygons), "dim", o.dimensions)
bpy.ops.object.select_all(action="DESELECT")
o.select_set(True)
os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=SALIDA, export_format="GLB", use_selection=True, export_yup=True,
                          export_apply=True, export_normals=True, export_materials="EXPORT")
