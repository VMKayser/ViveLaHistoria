"""Adornos de terceros CC0 (registrados en recursos/LICENCIAS.md) convertidos a la geometría y los ROLES del proyecto:
el color lo pone nuestra paleta, no las texturas del pack (así encajan en el estilo pintado y el visor los fusiona).

- Quaternius, Stylized Nature MegaKit (CC0): flores en grupo, arbustos con flores, plantas, pastos, trébol, rocas.
- yd, Street Lamp 03 (CC0): farol de poste con linterna colgada de voluta.

Uso (dentro de un script de manzana o de la BASE, con un Constructor c):
    from adornos_claude import planta, farol_cc0
    planta(c, "Flower_3_Group", x, y, z, ang=0.5, escala=0.6, semilla=3)
    farol_cc0(c, x, y, z, ang)
"""

import math
import os
import random

import bpy
from mathutils import Matrix, Vector

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
QUATERNIUS = os.path.join(RAIZ, "recursos", "originales", "quaternius_nature_megakit", "glTF")
FAROL = os.path.join(RAIZ, "recursos", "originales", "oga_farol", "street lamp_03.blend")

FLORES = ["#d9658a", "#e8742c", "#f2c94c", "#f4f1ec", "#c94f6d", "#e59bb4"]   # buganvillas, geranios, cartuchos
_cache = {}


def _rol_material(nombre, rnd):
    n = nombre.lower()
    if "flower" in n or "petal" in n:
        return "flor", rnd.choice(FLORES)
    if "bark" in n or "trunk" in n or "wood" in n:
        return "tronco", "#5a3f2c"
    if "rock" in n or "pebble" in n or "stone" in n:
        return "piedra", "#b8a996"
    if "grass" in n:
        return "follaje_claro", "#8aa64a"
    return "follaje", "#4f7a32"


def _cargar(clave, cargador):
    """Triángulos (en coordenadas locales, Z arriba) y nombre de material de cada uno; se cachea."""
    if clave in _cache:
        return _cache[clave]
    antes = set(bpy.data.objects)
    cargador()
    nuevos = [o for o in set(bpy.data.objects) - antes if o.type == "MESH"]
    tris = []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in nuevos:
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        mw = o.matrix_world.copy()
        mats = [m.name if m else "" for m in me.materials]
        for t in me.loop_triangles:
            pts = [mw @ me.vertices[i].co for i in t.vertices]
            tris.append((pts, mats[t.material_index] if t.material_index < len(mats) else ""))
        o.evaluated_get(dg).to_mesh_clear()
    for o in set(bpy.data.objects) - antes:
        bpy.data.objects.remove(o, do_unlink=True)
    # apoyar en z = 0 y centrar en x, y
    zs = [p.z for tri, _ in tris for p in tri]
    xs = [p.x for tri, _ in tris for p in tri]
    ys = [p.y for tri, _ in tris for p in tri]
    off = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    tris = [([p - off for p in tri], m) for tri, m in tris]
    _cache[clave] = tris
    return tris


def _colocar(c, tris, x, y, z, ang, escala, rol_de):
    rot = Matrix.Rotation(ang, 3, "Z")
    for tri, mat in tris:
        rol, color = rol_de(mat, tri)
        pts = [tuple(Vector((x, y, z)) + rot @ (p * escala)) for p in tri]
        c.poligono(pts, rol, color)


def planta(c, nombre, x, y, z, ang=0.0, escala=1.0, semilla=0):
    """Una pieza del Stylized Nature MegaKit (p. ej. "Flower_3_Group", "Bush_Common_Flowers", "Plant_1_Big")."""
    ruta = os.path.join(QUATERNIUS, nombre + ".gltf")
    tris = _cargar(nombre, lambda: bpy.ops.import_scene.gltf(filepath=ruta))
    rnd = random.Random(semilla)
    colores = {}

    def rol_de(mat, _tri):
        if mat not in colores:
            colores[mat] = _rol_material(mat, rnd)
        return colores[mat]
    _colocar(c, tris, x, y, z, ang, escala, rol_de)


def farol_cc0(c, x, y, z, ang=0.0, alto=3.8):
    """Farol de poste (CC0, yd). Cuerpo de hierro; la linterna, en vidrio cálido."""
    def cargar():
        with bpy.data.libraries.load(FAROL, link=False) as (src, dst):
            dst.objects = [n for n in src.objects]
        for o in dst.objects:
            if o is not None:
                bpy.context.scene.collection.objects.link(o)
    tris = _cargar("farol_cc0", cargar)
    zs = [p.z for t, _ in tris for p in t]
    xs = [p.x for t, _ in tris for p in t]
    h = max(zs)
    xmax = max(xs)
    escala = alto / h

    def rol_de(_mat, tri):
        cx = sum(p.x for p in tri) / 3
        cz = sum(p.z for p in tri) / 3
        if cx > xmax - 0.5 and 0.5 * h < cz < 0.76 * h:
            return "vidrio", "#efe2b5"
        return "hierro", "#2f2b28"
    _colocar(c, tris, x, y, z, ang, escala, rol_de)
