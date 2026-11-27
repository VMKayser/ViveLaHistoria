"""Prepara los árboles elegidos por el usuario en el catálogo (2026-11-23, todos CC0) como piezas de la ciudad:
blender/zonas/claude/assets/arbol_<especie>.glb, de 1 m de alto (se escalan al colocarlos), con la base del tronco en el
origen y SOLO materiales de rol (tronco / follaje / follaje_claro con su color), para que entren en el visor como el resto
de la geometría (color por vértice, sin texturas ni transparencias).

- Quaternius (CommonTree_3, TwistedTree_3, Pine_1, Pine_2): sus materiales Bark/Leaves pasan a tronco/follaje, reducidos.
- Palmeras (Exotic Palm Old/Default, Yughues palm v2): una sola textura; cada cara toma el rol por el color de su textura.
- Jacarandá e island tree (Poly Haven): tronco y ramas reducidos; las hojas (millones de tarjetas transparentes) se
  convierten en ~40 masas de follaje donde se agrupan, como en el estilo pintado del proyecto; el jacarandá en flor
  (noviembre) lleva parte de las masas lilas.

    ~/apps/blender-5.2.3-linux-x64/blender -b -P blender/zonas/claude/preparar_arboles.py [-- especie ...]
"""
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ORIG = os.path.join(RAIZ, "recursos", "originales")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
O = "catalogo/oga/"

ESPECIES = {
    # especie: (ruta en recursos/originales, modo, caras objetivo del tronco/total)
    "comun": (f"quaternius_nature_megakit/glTF/CommonTree_3.gltf", "quaternius", 1400),
    "retorcido": (f"quaternius_nature_megakit/glTF/TwistedTree_3.gltf", "quaternius", 2200),
    "pino_a": (f"quaternius_nature_megakit/glTF/Pine_1.gltf", "quaternius", 1500),
    "pino_b": (f"quaternius_nature_megakit/glTF/Pine_2.gltf", "quaternius", 1500),
    "palmera_canaria": (O + "exotic-palms-lowpoly-style/x_exoticpalmslowpolystyle/ExoticPalmOld.fbx", "textura", 3200),
    "palmera_canaria_b": (O + "exotic-palms-lowpoly-style/x_exoticpalmslowpolystyle/ExoticPalmDefalt.fbx", "textura", 2100),
    "palmera_alta": (O + "palm-tree-v2/x_palm_tree_v2/palm_tree.obj", "textura", 700),
    "jacaranda": ("catalogo/polyhaven/jacaranda_tree/jacaranda_tree.gltf", "hojas", 6000),
    "isla": ("catalogo/polyhaven/island_tree_02/island_tree_02.gltf", "hojas", 6000),
}
HOJA = ("leaf", "leave", "hoja", "folia", "needle", "frond")
CORTEZA = ("bark", "trunk", "branch", "wood", "tronco", "stem")


def limpiar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def importar(ruta):
    antes = set(bpy.data.objects)
    ext = ruta.lower().rsplit(".", 1)[1]
    if ext in ("glb", "gltf"):
        bpy.ops.import_scene.gltf(filepath=ruta)
    elif ext == "fbx":
        bpy.ops.import_scene.fbx(filepath=ruta)
    elif ext == "obj":
        bpy.ops.wm.obj_import(filepath=ruta)
    objs = [o for o in bpy.data.objects if o not in antes and o.type == "MESH"]
    for o in objs:                                     # aplica transformaciones y quita jerarquías
        mw = o.matrix_world.copy()
        o.parent = None
        o.data.transform(mw)
        o.matrix_world.identity()
    return objs


def color_material(m):
    if m and m.use_nodes:
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b and not b.inputs["Base Color"].is_linked:
            c = b.inputs["Base Color"].default_value
            return c[0], c[1], c[2]
    return None


def lin_a_srgb(c):
    return tuple(min(1.0, max(0.0, (x * 12.92 if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055))) for x in c)


def hexc(c):
    return "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in c)


def imagen_de(m):
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image and n.image.has_data:
                return n.image
    return None


def buscar_textura(ruta_modelo):
    import glob
    d = os.path.dirname(ruta_modelo)
    for f in sorted(glob.glob(d + "/**/*", recursive=True)):
        b = os.path.basename(f).lower()
        if b.endswith((".png", ".jpg", ".tga")) and not any(k in b for k in ("normal", "_n.", "spec", "prev")):
            return bpy.data.images.load(f)
    return None


def unir(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def reducir(o, caras):
    n = len(o.data.polygons)
    if n > caras:
        md = o.modifiers.new("dec", "DECIMATE")
        md.ratio = max(0.01, caras / n)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=md.name)


COLORES = {"pino_a": "2f5a2a", "pino_b": "35602c", "retorcido": "4f7030", "comun": "4a6b2c"}


def roles_por_material(o, especie):
    """Quaternius: Bark → tronco, Leaves → follaje (su color viene de una textura: se usa el de la paleta)."""
    nuevos = []
    for s in o.material_slots:
        m = s.material
        nom = (m.name if m else "").lower()
        rol = "follaje" if any(k in nom for k in HOJA) else "tronco"
        nuevos.append(bpy.data.materials.new(f"{rol}__{COLORES.get(especie, '4a6b2c') if rol == 'follaje' else '5a4535'}"))
    for i, nm in enumerate(nuevos):
        o.material_slots[i].material = nm


def roles_por_textura(o, ruta):
    """Una sola textura para todo: cada cara toma follaje (verde) o tronco (pardo) por el color de su textura en el
    centro de su UV; el color de cada rol es el promedio de sus caras."""
    img = None
    for s in o.material_slots:
        img = img or imagen_de(s.material)
    img = img or buscar_textura(ruta)
    me = o.data
    uv = me.uv_layers.active.data if me.uv_layers else None
    px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4) if img else None
    clases = {"follaje": [], "tronco": []}
    asign = []
    for p in me.polygons:
        if px is not None and uv is not None:
            u = sum(uv[li].uv[0] for li in p.loop_indices) / p.loop_total
            v = sum(uv[li].uv[1] for li in p.loop_indices) / p.loop_total
            r, g, b, a = px[int((v % 1) * (img.size[1] - 1)), int((u % 1) * (img.size[0] - 1))]
        else:
            r, g, b = 0.4, 0.3, 0.2
        rol = "follaje" if (g > r * 1.02 and g > b) else "tronco"
        clases[rol].append((r, g, b))
        asign.append(rol)
    mats = {}
    if not me.materials:
        me.materials.append(None)
    for rol, cs in clases.items():
        col = tuple(float(np.mean([c[i] for c in cs])) for i in range(3)) if cs else (0.3, 0.4, 0.2)
        # las palmeras canarias tienen el estípite pardo grisáceo (la textura lo trae anaranjado)
        hx = "6b5a48" if (rol == "tronco" and "canaria" in os.path.basename(ruta).lower() + especie_actual[0]) else hexc(col)[1:]
        mats[rol] = bpy.data.materials.new(f"{rol}__{hx}")      # los píxeles ya están en sRGB
    me.materials.clear()
    me.materials.append(mats["follaje"])
    me.materials.append(mats["tronco"])
    for p, rol in zip(me.polygons, asign):
        p.material_index = 0 if rol == "follaje" else 1


def hojas_a_masas(objs, especie, caras_tronco):
    """Poly Haven: tronco reducido + masas de follaje donde se agrupan las hojas. Con numpy y sin duplicar la malla
    (el jacarandá tiene 3,8 millones de caras: separarlo por material en Blender agotaba la memoria)."""
    rng = np.random.default_rng(3)
    P, tv, tf = [], [], []
    for o in objs:
        me = o.data
        nv, nf = len(me.vertices), len(me.polygons)
        co = np.empty(nv * 3, dtype=np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        mi = np.empty(nf, dtype=np.int32); me.polygons.foreach_get("material_index", mi)
        ls = np.empty(nf, dtype=np.int32); me.polygons.foreach_get("loop_start", ls)
        lt = np.empty(nf, dtype=np.int32); me.polygons.foreach_get("loop_total", lt)
        lv = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get("vertex_index", lv)
        noms = [(s_.material.name.lower() if s_.material else "") for s_ in o.material_slots] or [""]
        es_hoja = np.array([any(k in n for k in HOJA) for n in noms])
        es_tronco = np.array([("trunk" in n) or (n.endswith(especie) or n == "island_tree_02") for n in noms])
        hojas_f = np.nonzero(es_hoja[mi])[0]
        sel = rng.choice(hojas_f, size=min(len(hojas_f), 40000), replace=False) if len(hojas_f) else []
        for f in sel:
            P.append(co[lv[ls[f]]])
        tronco_f = np.nonzero(es_tronco[mi] & ~es_hoja[mi])[0]
        base = sum(len(x) for x in tv)
        usados = {}
        for f in tronco_f:
            cara = []
            for li in range(ls[f], ls[f] + lt[f]):
                vi = int(lv[li])
                if vi not in usados:
                    usados[vi] = len(usados)
                cara.append(base + usados[vi])
            tf.append(cara)
        inv = np.empty(len(usados), dtype=np.int64)
        for vi, k in usados.items():
            inv[k] = vi
        tv.append(co[inv])
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    P = np.array(P)
    me = bpy.data.meshes.new("tronco")
    me.from_pydata(np.concatenate(tv).tolist(), [], tf)
    tronco = bpy.data.objects.new("tronco", me)
    bpy.context.scene.collection.objects.link(tronco)
    reducir(tronco, caras_tronco)
    # piezas de madera: se quedan las grandes (tronco y ramas principales); las astillas sueltas que deja la reducción
    # quedarían flotando sin apoyo (las tapan las masas de follaje)
    bm = bmesh.new(); bm.from_mesh(tronco.data); bm.verts.ensure_lookup_table()
    resto, piezas = set(bm.verts), []
    while resto:
        v0 = resto.pop(); pieza, pila = {v0}, [v0]
        while pila:
            v = pila.pop()
            for e in v.link_edges:
                w = e.other_vert(v)
                if w in resto:
                    resto.discard(w); pieza.add(w); pila.append(w)
        piezas.append(pieza)
    total = len(bm.verts)
    fuera = [v for pz in piezas if len(pz) < total * 0.03 for v in pz]
    bmesh.ops.delete(bm, geom=fuera, context="VERTS")
    bm.to_mesh(tronco.data); bm.free()
    tronco.data.materials.append(bpy.data.materials.new("tronco__5a4535"))
    # k-medias: ~40 grupos de hojas
    k = 220
    C = P[rng.choice(len(P), k, replace=False)]
    for _ in range(12):
        d = ((P[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        lab = d.argmin(1)
        C = np.array([P[lab == i].mean(0) if (lab == i).any() else C[i] for i in range(k)])
    verdes = ["follaje__3f6128", "follaje__4a6b2c", "follaje_claro__628a35", "follaje__365a26"]
    lilas = ["follaje_claro__8f6fd0", "follaje__7458b8"]
    bm = bmesh.new()
    mats = []
    azar = random.Random(7)
    for i in range(k):
        q = P[lab == i]
        if len(q) < 15:
            continue
        sd = np.maximum(q.std(0) * 1.7, 0.1)
        nom = azar.choice(lilas) if (especie == "jacaranda" and azar.random() < 0.4) else azar.choice(verdes)
        if nom not in mats:
            mats.append(nom)
        r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        for v in r["verts"]:
            v.co = Vector((C[i][0] + v.co.x * sd[0], C[i][1] + v.co.y * sd[1], C[i][2] + v.co.z * sd[2]))
        for f in {f for v in r["verts"] for f in v.link_faces}:
            f.material_index = mats.index(nom)
            f.smooth = True
    me = bpy.data.meshes.new("masas")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("masas", me)
    bpy.context.scene.collection.objects.link(ob)
    for nom in mats:
        me.materials.append(bpy.data.materials.new(nom))
    return [tronco, ob]


def normalizar(objs):
    pts = [Vector(v.co) for o in objs for v in o.data.vertices]
    zmin = min(p.z for p in pts)
    zmax = max(p.z for p in pts)
    base = [p for p in pts if p.z < zmin + (zmax - zmin) * 0.03] or pts
    cx, cy = sum(p.x for p in base) / len(base), sum(p.y for p in base) / len(base)
    s = 1.0 / (zmax - zmin)
    for o in objs:
        for v in o.data.vertices:
            v.co = Vector(((v.co.x - cx) * s, (v.co.y - cy) * s, (v.co.z - zmin) * s))


especie_actual = [""]


def preparar(especie):
    especie_actual[0] = especie
    ruta_rel, modo, caras = ESPECIES[especie]
    ruta = os.path.join(ORIG, ruta_rel)
    limpiar()
    objs = importar(ruta)
    if modo == "quaternius":
        o = unir(objs)
        roles_por_material(o, especie)
        reducir(o, caras)
        objs = [o]
    elif modo == "textura":
        o = unir(objs)
        reducir(o, caras)
        roles_por_textura(o, ruta)
        objs = [o]
    else:
        objs = hojas_a_masas(objs, especie, caras)
    # alto: Y-arriba de glTF ya convertido por el importador; los FBX/OBJ pueden venir acostados: se corrige
    pts = [v.co for o in objs for v in o.data.vertices]
    ext = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
    if ext[2] < max(ext[0], ext[1]) * 0.6 and modo != "hojas":
        for o in objs:
            o.data.transform(__import__("mathutils").Matrix.Rotation(math.radians(90), 4, "X"))
    normalizar(objs)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"arbol_{especie}.glb"), export_format="GLB", use_selection=True,
                              export_yup=True, export_apply=True, export_normals=True, export_materials="EXPORT",
                              export_texcoords=False)
    caras = sum(len(o.data.polygons) for o in objs)
    print(f"[arboles] {especie}: {caras} caras, materiales {[s.material.name for o in objs for s in o.material_slots]}")


def main():
    pedidos = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(ESPECIES)
    os.makedirs(OUT, exist_ok=True)
    for e in pedidos:
        preparar(e)


main()
