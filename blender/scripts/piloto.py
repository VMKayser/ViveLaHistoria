"""Manzana piloto de prueba (placeholder estilizado).

Uso:
  blender --background --python blender/scripts/piloto.py -- <salida.glb>

Blender es Z-arriba; el exportador glTF lo convierte a Y-arriba para la web:
Blender (x, y, z) -> web (x, z, -y). Unidades: 1 = 1 metro.
"""
import math
import sys

import bpy

salida = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "piloto.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)

_materiales = {}


def mat(nombre, color):
    if nombre not in _materiales:
        m = bpy.data.materials.new(nombre)
        if m.node_tree is None:  # Blender < 5 crea materiales sin nodos
            m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
        r, g, b = (int(color[i : i + 2], 16) / 255 for i in (1, 3, 5))
        bsdf.inputs["Base Color"].default_value = (r**2.2, g**2.2, b**2.2, 1)
        bsdf.inputs["Roughness"].default_value = 0.9
        _materiales[nombre] = m
    return _materiales[nombre]


def caja(nombre, pos, dim, color, bevel=0.15):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.object
    o.name = nombre
    o.scale = dim
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = o.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    o.data.materials.append(mat(color, color))
    return o


def techo(nombre, pos, ancho, largo, alto, color, piramide=False):
    """Techo a dos aguas (o piramidal) como prisma."""
    if piramide:
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=ancho * 0.72, depth=alto, location=pos, rotation=(0, 0, math.pi / 4))
        o = bpy.context.object
    else:
        a, l, h = ancho / 2, largo / 2, alto / 2
        verts = [(-a, -l, -h), (a, -l, -h), (0, -l, h), (-a, l, -h), (a, l, -h), (0, l, h)]
        caras = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (0, 2, 5, 3)]
        me = bpy.data.meshes.new(nombre)
        me.from_pydata(verts, [], caras)
        me.update()
        o = bpy.data.objects.new(nombre, me)
        o.location = pos
        bpy.context.collection.objects.link(o)
    o.name = nombre
    o.data.materials.append(mat(color, color))
    return o


def casa(nombre, x, y, ancho, fondo, alto, color, rot=0):
    c = caja(nombre, (x, y, alto / 2), (ancho, fondo, alto), color)
    t = techo(nombre + "_techo", (x, y, alto + 1.2), ancho + 0.8, fondo + 0.8, 2.4, "#b5523b")
    for o in (c, t):
        o.rotation_euler[2] += rot
    # ventanas
    for i in range(int(ancho // 3)):
        vx = x - ancho / 2 + 1.8 + i * 3
        for piso in range(int(alto // 3.5)):
            caja(f"{nombre}_v{i}_{piso}", (vx, y - fondo / 2 - 0.05, 2 + piso * 3.5), (1.1, 0.2, 1.6), "#4a6b8a", bevel=0)
    return c


def arbol(x, y, s=1.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.3 * s, depth=2 * s, location=(x, y, s))
    bpy.context.object.data.materials.append(mat("#6b4a2f", "#6b4a2f"))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.8 * s, location=(x, y, 3 * s))
    bpy.context.object.data.materials.append(mat("#5f9e4a", "#5f9e4a"))


# Suelo y plaza
caja("suelo", (0, 0, -0.1), (120, 120, 0.2), "#a9c48a", bevel=0)
caja("calle", (0, 0, 0.01), (120, 8, 0.02), "#8d8a85", bevel=0)
caja("plaza", (0, 0, 0.05), (26, 22, 0.1), "#d8cbb0", bevel=0)
caja("fuente_base", (0, 0, 0.4), (4, 4, 0.8), "#c9bda5")
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.6, depth=2.4, location=(0, 0, 1.6))
bpy.context.object.data.materials.append(mat("#c9bda5", "#c9bda5"))

# Iglesia (web: z=-18 -> Blender y=+18)
caja("iglesia", (0, 20, 6), (14, 18, 12), "#efe3c8")
techo("iglesia_techo", (0, 20, 13.5), 15, 19, 4, "#a84a35")
caja("torre", (0, 10.5, 10), (5, 5, 20), "#efe3c8")
techo("torre_techo", (0, 10.5, 22), 5.5, 5.5, 4, "#a84a35", piramide=True)
caja("puerta", (0, 7.9, 2), (2.4, 0.3, 4), "#6b4a2f", bevel=0)

# Casona (web: x=22, z=4 -> Blender x=22, y=-4)
casa("casona", 22, -4, 10, 14, 7, "#f2c99a")
casa("casa_oeste", -22, -4, 10, 14, 6, "#d9b38c")
casa("casa_ne", 22, 16, 9, 10, 6, "#e7d3a7")
casa("casa_no", -22, 16, 9, 10, 8, "#f0dcc0")
casa("casa_se", 18, -24, 12, 10, 6, "#e9b9a0")
casa("casa_so", -18, -24, 12, 10, 7, "#cfe0d0")

for x, y in [(-9, -8), (9, -8), (-9, 8), (9, 8), (-30, -14), (30, -14), (-34, 8), (34, 8)]:
    arbol(x, y)

bpy.ops.export_scene.gltf(filepath=salida, export_format="GLB", export_apply=True)
print("Exportado:", salida)
