"""Personajes de 1809 con MPFB (MakeHuman para Blender), ropa de época y animaciones.

Uso:
    blender -b --python blender/personajes_1809.py                # todos
    blender -b --python blender/personajes_1809.py -- soldado     # solo algunos
(no usar --factory-startup: hace falta la extensión MPFB y sus assets CC0 instalados)

Principales (detalle alto, malla completa): soldado, zudanez, lemoine, arzobispo.
Multitud (malla proxy liviana): hombre_*, mujer_*, criollo, fraile.

Cada personaje sale como godot/assets/personajes/<nombre>.gltf (+ .bin y texturas/ compartidas) con su esqueleto
"game_engine" (53 huesos) y sus animaciones. La ropa de época (casacas, ponchos,
mantas, mucetas, sombreros) se modela aquí: MakeHuman no trae ropa de 1809.
"""
import math
import random
import sys
import traceback
from math import cos, pi, radians, sin
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.kdtree import KDTree

from bl_ext.blender_org.mpfb.services.humanservice import HumanService
from bl_ext.blender_org.mpfb.services.rigservice import RigService
from bl_ext.blender_org.mpfb.services.targetservice import TargetService

DATA = Path.home() / ".config/blender/5.2/extensions/.user/blender_org/mpfb/data"
RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "godot" / "assets" / "personajes"
FPS = 30
ACTUAL = ""  # personaje en construcción (prefijo de materiales y texturas propias)

ROJO = (0.62, 0.08, 0.06)
AZUL_REAL = (0.07, 0.1, 0.26)
BLANCO = (0.86, 0.83, 0.76)
NEGRO = (0.05, 0.05, 0.06)
VIOLETA = (0.32, 0.06, 0.3)

# ---------------------------------------------------------------- personajes

PRINCIPALES = {
    "soldado": dict(
        macro=dict(gender=1.0, age=0.42, muscle=0.62, weight=0.45, height=0.55),
        raza=dict(caucasian=0.55, asian=0.35, african=0.1), piel="young_caucasian_male", pelo="short02",
        ropa={"rehmanpolanski_viking_pants": BLANCO, "culturalibre_male_boots": None},
        casaca=dict(color=AZUL_REAL, vueltas=ROJO, largo=0.5), sombrero="bicornio", fusil=True,
        animaciones=["reposo", "marcha_fusil", "caminar"]),
    "zudanez": dict(
        macro=dict(gender=1.0, age=0.56, muscle=0.4, weight=0.5, height=0.5),
        raza=dict(caucasian=0.75, asian=0.2, african=0.05), piel="middleage_caucasian_male", pelo="short04",
        ropa={"rehmanpolanski_viking_pants": (0.18, 0.15, 0.12), "shoes03": None},
        casaca=dict(color=(0.08, 0.08, 0.1), vueltas=(0.08, 0.08, 0.1), largo=0.45, chaleco_color=(0.35, 0.28, 0.2)), corbatin=BLANCO,
        animaciones=["reposo", "prisionero", "caminar", "vitorear"]),
    "lemoine": dict(
        macro=dict(gender=1.0, age=0.4, muscle=0.55, weight=0.5, height=0.55),
        raza=dict(caucasian=0.65, asian=0.3, african=0.05), piel="young_caucasian_male2", pelo="short02",
        ropa={"rehmanpolanski_viking_tunic": (0.78, 0.74, 0.66), "rehmanpolanski_viking_pants": (0.25, 0.2, 0.15),
              "rehmanpolanski_viking_boots": None},
        poncho=dict(color=(0.42, 0.22, 0.1), rayas=[(0.1, 0.04, (0.75, 0.62, 0.35)), (0.16, 0.02, ROJO), (0.62, 0.04, (0.75, 0.62, 0.35))]),
        sombrero="ala_ancha", animaciones=["reposo", "llamar", "correr", "caminar"]),
    "arzobispo": dict(
        macro=dict(gender=1.0, age=0.62, muscle=0.35, weight=0.6, height=0.48),
        raza=dict(caucasian=0.9, asian=0.05, african=0.05), piel="middleage_caucasian_male", pelo="short02",
        ropa={"donitz_monk_robe": NEGRO, "shoes03": None}, muceta=VIOLETA, sombrero="solideo", cruz=True,
        animaciones=["reposo", "bendecir"]),
}

ANIM_MULTITUD = ["reposo", "caminar", "correr", "vitorear", "antorcha", "antorcha_caminar"]
MULTITUD = {
    "hombre_a": dict(proxy="male1591", macro=dict(gender=1.0, age=0.45, muscle=0.55, weight=0.45, height=0.42),
                     raza=dict(asian=0.7, caucasian=0.25, african=0.05), piel="middleage_asian_male", pelo="short02",
                     ropa={"rehmanpolanski_viking_tunic": (0.7, 0.66, 0.58), "rehmanpolanski_viking_pants": (0.2, 0.17, 0.14), "rehmanpolanski_viking_boots": None},
                     poncho=dict(color=(0.5, 0.12, 0.08), rayas=[(0.2, 0.03, (0.1, 0.08, 0.06)), (0.55, 0.05, (0.85, 0.7, 0.3))]),
                     sombrero="ala_ancha", animaciones=ANIM_MULTITUD),
    "hombre_b": dict(proxy="male1591", macro=dict(gender=1.0, age=0.6, muscle=0.5, weight=0.55, height=0.4),
                     raza=dict(asian=0.75, caucasian=0.2, african=0.05), piel="old_asian_male", pelo="short01",
                     ropa={"rehmanpolanski_viking_tunic": (0.6, 0.55, 0.45), "rehmanpolanski_viking_pants": (0.3, 0.26, 0.2), "rehmanpolanski_viking_boots": None},
                     poncho=dict(color=(0.3, 0.24, 0.18), rayas=[(0.3, 0.06, (0.55, 0.4, 0.22))]),
                     sombrero="montera", animaciones=ANIM_MULTITUD),
    "hombre_c": dict(proxy="male1591", macro=dict(gender=1.0, age=0.3, muscle=0.6, weight=0.4, height=0.5),
                     raza=dict(asian=0.6, caucasian=0.3, african=0.1), piel="young_asian_male", pelo="short03",
                     ropa={"rehmanpolanski_viking_tunic": (0.75, 0.7, 0.6), "rehmanpolanski_viking_pants": (0.15, 0.15, 0.18), "rehmanpolanski_viking_boots": None},
                     poncho=dict(color=(0.12, 0.18, 0.3), rayas=[(0.12, 0.03, ROJO), (0.4, 0.03, (0.8, 0.75, 0.6))]),
                     sombrero="ala_ancha", animaciones=ANIM_MULTITUD),
    "mujer_a": dict(proxy="female1605", macro=dict(gender=0.0, age=0.4, muscle=0.45, weight=0.55, height=0.55),
                    raza=dict(asian=0.7, caucasian=0.25, african=0.05), piel="middleage_asian_female", pelo="braid01",
                    ropa={"toigo_long_full_skirt": (0.55, 0.1, 0.12), "toigo_flats": (0.2, 0.14, 0.1)}, blusa=(0.82, 0.78, 0.7),
                    manta=dict(color=(0.18, 0.28, 0.2), rayas=[(0.25, 0.04, (0.8, 0.6, 0.2))]), sombrero="ala_ancha",
                    animaciones=ANIM_MULTITUD),
    "mujer_b": dict(proxy="female1605", macro=dict(gender=0.0, age=0.6, muscle=0.4, weight=0.6, height=0.5),
                    raza=dict(asian=0.75, caucasian=0.2, african=0.05), piel="old_asian_female", pelo="braid01",
                    ropa={"toigo_long_full_skirt": (0.12, 0.22, 0.4), "toigo_flats": (0.2, 0.14, 0.1)}, blusa=(0.75, 0.7, 0.62),
                    manta=dict(color=(0.4, 0.15, 0.1), rayas=[(0.15, 0.03, (0.9, 0.8, 0.5)), (0.35, 0.03, (0.1, 0.1, 0.1))]),
                    sombrero="montera", animaciones=ANIM_MULTITUD),
    "mujer_c": dict(proxy="female1605", macro=dict(gender=0.0, age=0.28, muscle=0.45, weight=0.45, height=0.58),
                    raza=dict(asian=0.6, caucasian=0.35, african=0.05), piel="young_asian_female", pelo="braid01",
                    ropa={"toigo_long_full_skirt": (0.2, 0.32, 0.12), "toigo_flats": (0.2, 0.14, 0.1)}, blusa=(0.85, 0.82, 0.75),
                    manta=dict(color=(0.5, 0.42, 0.3), rayas=[(0.3, 0.05, (0.45, 0.1, 0.1))]),
                    animaciones=ANIM_MULTITUD),
    "criollo": dict(proxy="male1591", macro=dict(gender=1.0, age=0.5, muscle=0.45, weight=0.5, height=0.55),
                    raza=dict(caucasian=0.7, asian=0.25, african=0.05), piel="middleage_caucasian_male", pelo="short04",
                    ropa={"rehmanpolanski_viking_pants": (0.55, 0.48, 0.36), "culturalibre_male_boots": None},
                    casaca=dict(color=(0.16, 0.22, 0.14), vueltas=(0.16, 0.22, 0.14), largo=0.45), sombrero="bicornio",
                    animaciones=ANIM_MULTITUD),
    "fraile": dict(proxy="male1591", macro=dict(gender=1.0, age=0.55, muscle=0.4, weight=0.55, height=0.45),
                   raza=dict(caucasian=0.6, asian=0.35, african=0.05), piel="middleage_caucasian_male", pelo="short01",
                   ropa={"donitz_monk_robe": None, "donitz_monk_robe_hood_down": None}, sombrero=None, animaciones=ANIM_MULTITUD),
}


# ---------------------------------------------------------------- utilidades

def nueva_escena():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.context.scene.render.fps = FPS


def tela(nombre, color, rayas=None, tam=256, semilla=0):
    """Textura de tejido de lana (sRGB) con trama y, si se pide, bandas de color."""
    rng = np.random.default_rng(semilla)
    y, x = np.mgrid[0:tam, 0:tam].astype(np.float32)
    trama = 0.5 + 0.5 * np.sin(x * pi / 2.0) * np.sin(y * pi / 2.0)
    grueso = rng.random((tam // 16, tam // 16))
    grueso = np.kron(grueso, np.ones((16, 16)))[:tam, :tam]
    fino = rng.random((tam, tam))
    base = 0.8 + 0.09 * trama + 0.07 * (grueso - 0.5) + 0.05 * (fino - 0.5)
    rgb = np.stack([base * c for c in color], axis=-1)
    if rayas:
        v = y / tam
        for pos, ancho, col in rayas:
            for centro in (pos, 1.0 - pos):
                banda = np.abs(v - centro) < ancho / 2
                rgb[banda] = np.stack([base[banda] * c for c in col], axis=-1)
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((tam, tam, 1), np.float32)], axis=-1)
    img = bpy.data.images.new(nombre, tam, tam)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.pack()
    return img


def material_tela(nombre, color, rayas=None, rugosidad=0.92, metal=0.0):
    nombre = f"{ACTUAL}_{nombre}"
    m = bpy.data.materials.new(nombre)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = rugosidad
    bsdf.inputs["Metallic"].default_value = metal
    if metal > 0:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
    else:
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = tela(nombre + "_tx", color, rayas, semilla=abs(hash(nombre)) % 1000)
        nt.links.new(tx.outputs["Color"], bsdf.inputs["Base Color"])
    return m


class SinMascarasInvertidas:
    """Muestra el cuerpo completo (sin la máscara del proxy) y deja todo como estaba."""

    def __init__(self, base):
        self.base = base

    def __enter__(self):
        self.estado = {m.name: m.show_viewport for m in self.base.modifiers if m.type == "MASK"}
        for m in self.base.modifiers:
            if m.type == "MASK" and m.invert_vertex_group:
                m.show_viewport = False
        bpy.context.view_layer.update()
        return bpy.context.evaluated_depsgraph_get()

    def __exit__(self, *_):
        for m in self.base.modifiers:
            if m.name in self.estado:
                m.show_viewport = self.estado[m.name]
        bpy.context.view_layer.update()


class Cuerpo:
    """Geometría del cuerpo (pose de reposo actual) con sus pesos por hueso."""

    def __init__(self, base):
        nombres = [g.name for g in base.vertex_groups]
        self.pos = []
        self.pesos = []
        with SinMascarasInvertidas(base) as dg:
            ev = base.evaluated_get(dg)
            me = ev.to_mesh()
            for v in me.vertices:
                self.pos.append(base.matrix_world @ v.co)
                self.pesos.append({nombres[g.group]: g.weight for g in v.groups if g.weight > 0.01 and not nombres[g.group].startswith(("helper", "joint", "body", "Left", "Right", "Mid", "Helper", "Joint"))})
            ev.to_mesh_clear()
        self.kd = KDTree(len(self.pos))
        for i, p in enumerate(self.pos):
            self.kd.insert(p, i)
        self.kd.balance()

    def suma(self, i, huesos):
        return sum(self.pesos[i].get(h, 0.0) for h in huesos)

    def pesos_en(self, p, k=6, filtro=None):
        acum, total = {}, 0.0
        for _, i, d in self.kd.find_n(p, k * (4 if filtro else 1)):
            if filtro and not filtro(i):
                continue
            w = 1.0 / max(d, 1e-4)
            for h, x in self.pesos[i].items():
                acum[h] = acum.get(h, 0.0) + x * w
            total += w
        return {h: x / total for h, x in acum.items()} if total else {}

    def perfil(self, incluir, z0, z1, sectores=48, paso=0.02, centro=(0.0, 0.0)):
        """Radio máximo del cuerpo por sector angular y franja de altura."""
        nz = int((z1 - z0) / paso) + 1
        r = np.zeros((nz, sectores))
        cx, cy = centro
        for i, p in enumerate(self.pos):
            if not (z0 <= p.z <= z1) or not incluir(i):
                continue
            a = math.atan2(p.y - cy, p.x - cx) % (2 * pi)
            s = int(a / (2 * pi) * sectores) % sectores
            k = int((p.z - z0) / paso)
            d = math.hypot(p.x - cx, p.y - cy)
            if d > r[k, s]:
                r[k, s] = d
        # rellena sectores vacíos con sus vecinos
        for k in range(nz):
            fila = r[k]
            if fila.max() == 0:
                continue
            for _ in range(sectores):
                vacios = fila == 0
                if not vacios.any():
                    break
                fila[vacios] = np.maximum(np.roll(fila, 1), np.roll(fila, -1))[vacios]
        return r, z0, paso


def objeto_de_bm(nombre, bm, material, rig, cuerpo, pesos_fn, uv_fn=None, grosor=0.0, filtro=None):
    """Crea la prenda: malla, material, UV, pesos copiados del cuerpo y modificador Armature.

    Si la prenda nació de la piel (concha_bm), cada vértice copia los pesos exactos de su
    vértice de origen: así la tela se mueve igual que la piel y no la deja a la vista.
    """
    capa = bm.verts.layers.int.get("orig")
    origen = [v[capa] for v in bm.verts] if capa is not None else None
    # La capa de pesos heredada del cuerpo usa los índices de grupo del cuerpo: se quita
    # para que no se mezcle con los grupos nuevos de la prenda.
    deform = bm.verts.layers.deform.active
    if deform is not None:
        bm.verts.layers.deform.remove(deform)
    if uv_fn:
        uv = bm.loops.layers.uv.verify()
        for f in bm.faces:
            for l in f.loops:
                l[uv].uv = uv_fn(l.vert)
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(material)
    for f in me.polygons:
        f.use_smooth = True
    if "orig" in me.attributes:
        me.attributes.remove(me.attributes["orig"])
    grupos = {}
    huesos = set(rig.data.bones.keys())
    for v in me.vertices:
        pesos = (filtro or dict)(cuerpo.pesos[origen[v.index]]) if origen else pesos_fn(v.co)
        pesos = {h: w for h, w in pesos.items() if h in huesos}
        total = sum(pesos.values()) or 1.0
        for h, w in pesos.items():
            w /= total
            if h not in grupos:
                grupos[h] = ob.vertex_groups.new(name=h)
            grupos[h].add([v.index], w, "REPLACE")
    if grosor:
        s = ob.modifiers.new("grosor", "SOLIDIFY")
        s.thickness = grosor
        s.offset = 1.0
    a = ob.modifiers.new("Armature", "ARMATURE")
    a.object = rig
    ob.parent = rig
    return ob


def pesos_rigidos(hueso):
    return lambda p: {hueso: 1.0}


def mezclar(a, b, t):
    r = {h: x * (1 - t) for h, x in a.items()}
    for h, x in b.items():
        r[h] = r.get(h, 0.0) + x * t
    return r


# ---------------------------------------------------------------- prendas

BRAZOS = ("clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r")
MANOS = ("hand_l", "hand_r") + tuple(f"{d}_0{k}_{s}" for d in ("index", "middle", "pinky", "ring", "thumb") for k in (1, 2, 3) for s in "lr")
PIERNAS = ("thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r")


def concha_bm(base, cuerpo, huesos, separacion, umbral=0.5, z_min=-9.0, z_max=9.0, excluir=()):
    bm = bmesh.new()
    with SinMascarasInvertidas(base) as dg:
        bm.from_object(base, dg)
    if len(bm.verts) != len(cuerpo.pos):
        raise RuntimeError(f"la malla del cuerpo cambió ({len(bm.verts)} != {len(cuerpo.pos)})")
    bm.transform(base.matrix_world)
    bm.verts.ensure_lookup_table()
    capa = bm.verts.layers.int.new("orig")
    for v in bm.verts:
        v[capa] = v.index
    borrar = []
    for f in bm.faces:
        idx = [v.index for v in f.verts]
        w = sum(cuerpo.suma(i, huesos) for i in idx) / len(idx)
        we = sum(cuerpo.suma(i, excluir) for i in idx) / len(idx)
        z = f.calc_center_median().z
        if w < umbral or we > 0.4 or not (z_min <= z <= z_max):
            borrar.append(f)
    bmesh.ops.delete(bm, geom=borrar, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * separacion
    return bm


def envolvente(cuerpo, incluir, z_arriba, hem, separacion, abertura_frente=0.0, anillos=24, sectores=48, centro_y=0.0, ensanche=0.0):
    """Tela que se ciñe por arriba y cae recta desde el punto más ancho (poncho, manta, faldones).

    hem(a) -> altura del ruedo en el ángulo a (0 = +X, pi/2 = +Y atrás, 3pi/2 = -Y frente).
    """
    z_min = min(hem(2 * pi * s / sectores) for s in range(sectores))
    r, z0, paso = cuerpo.perfil(incluir, z_min - 0.02, z_arriba + 0.02, sectores, centro=(0.0, centro_y))
    acumulado = np.maximum.accumulate(r[::-1], axis=0)[::-1]  # máximo de todo lo que está más arriba
    bm = bmesh.new()
    filas = []
    for k in range(anillos + 1):
        s_ = k / anillos
        fila = []
        for s in range(sectores):
            a = 2 * pi * (s + 0.5) / sectores
            z = z_arriba - s_ * (z_arriba - hem(a))
            kz = min(max(int((z - z0) / paso), 0), acumulado.shape[0] - 1)
            radio = acumulado[kz, s] + separacion + ensanche * s_ ** 1.5
            fila.append(bm.verts.new((radio * cos(a), centro_y + radio * sin(a), z)))
        filas.append(fila)
    for k in range(anillos):
        for s in range(sectores):
            a = 2 * pi * (s + 0.5) / sectores
            frente = abs(((a - 1.5 * pi + pi) % (2 * pi)) - pi) < abertura_frente
            if frente and k >= 0:
                continue
            s2 = (s + 1) % sectores
            bm.faces.new((filas[k][s], filas[k][s2], filas[k + 1][s2], filas[k + 1][s]))
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # normales hacia afuera
    bm.normal_update()
    hacia_afuera = sum((f.normal.dot(Vector((f.calc_center_median().x, f.calc_center_median().y - centro_y, 0))) for f in bm.faces))
    if hacia_afuera < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    return bm


def lathe(bm, perfil, seg, M=Matrix(), tapas=True):
    anillos = [[bm.verts.new(M @ Vector((r * cos(2 * pi * k / seg), r * sin(2 * pi * k / seg), z))) for k in range(seg)] for r, z in perfil]
    for a, b in zip(anillos, anillos[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    if tapas:
        bm.faces.new(anillos[0])
        bm.faces.new(anillos[-1])


def cabeza_arriba(cuerpo):
    pts = [p for i, p in enumerate(cuerpo.pos) if cuerpo.pesos[i].get("head", 0) > 0.6]
    zt = max(p.z for p in pts)
    cy = sum(p.y for p in pts) / len(pts)
    return zt, cy


def sombrero(tipo, cuerpo, rig):
    zt, cy = cabeza_arriba(cuerpo)
    bm = bmesh.new()
    if tipo == "ala_ancha":
        M = Matrix.Translation((0, cy, zt - 0.075))
        lathe(bm, [(0.27, 0.0), (0.26, 0.015), (0.115, 0.02), (0.112, 0.12), (0.09, 0.14), (0.02, 0.142)], 32, M, tapas=False)
        bm.faces.new([v for v in bm.verts][:32][::-1])
        color, nombre = (0.16, 0.12, 0.08), "sombrero_fieltro"
    elif tipo == "montera":
        M = Matrix.Translation((0, cy, zt - 0.06))
        lathe(bm, [(0.2, 0.0), (0.19, 0.03), (0.105, 0.035), (0.1, 0.09), (0.06, 0.11), (0.01, 0.112)], 24, M, tapas=False)
        bm.faces.new([v for v in bm.verts][:24][::-1])
        color, nombre = (0.35, 0.08, 0.06), "montera"
    elif tipo == "solideo":
        M = Matrix.Translation((0, cy + 0.01, zt - 0.045))
        lathe(bm, [(0.085, 0.0), (0.075, 0.03), (0.04, 0.045), (0.005, 0.05)], 16, M)
        color, nombre = VIOLETA, "solideo"
    else:  # bicornio, de través (puntas a los costados)
        pts = []
        for k in range(17):
            t = pi * k / 16
            pts.append((0.24 * cos(t), 0.035 + 0.17 * sin(t) ** 0.8))
        pts += [(-0.2, 0.0), (0.0, -0.02), (0.2, 0.0)]
        perfil = pts
        z = zt - 0.075
        A = [bm.verts.new((x, cy - 0.06, z + h)) for x, h in perfil]
        B = [bm.verts.new((x * 0.97, cy + 0.06, z + h * 0.96)) for x, h in perfil]
        bm.faces.new(A)
        bm.faces.new(B[::-1])
        n = len(perfil)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((A[i], A[j], B[j], B[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        lathe(bm, [(0.035, 0.0), (0.035, 0.006)], 12, Matrix.Translation((0.0, cy - 0.065, z + 0.12)) @ Matrix.Rotation(pi / 2, 4, "X"))
        color, nombre = NEGRO, "bicornio"
    return objeto_de_bm(nombre, bm, material_tela(nombre, color, rugosidad=0.8), rig, cuerpo, pesos_rigidos("head"))


def chaleco(base, cuerpo, rig, color):
    """Chaleco bajo la casaca: solo sigue a la columna, así el pecho nunca queda a la vista."""
    columna = ("spine_01", "spine_02", "spine_03")
    z_min = rig.data.bones["spine_01"].head_local.z - 0.06
    bm = concha_bm(base, cuerpo, columna + ("clavicle_l", "clavicle_r"), 0.012, umbral=0.35, z_min=z_min,
                   excluir=("neck_01", "head", "upperarm_l", "upperarm_r") + MANOS + PIERNAS)
    def solo_columna(d):
        w = {h: x for h, x in d.items() if h in columna}
        t = sum(w.values())
        return {h: x / t for h, x in w.items()} if t > 0 else {"spine_02": 1.0}
    return [objeto_de_bm("chaleco", bm, material_tela("chaleco", color), rig, cuerpo, None,
                         uv_fn=lambda v: (v.co.x * 4, v.co.z * 4), grosor=0.004, filtro=solo_columna)]


def casaca(base, cuerpo, rig, color, vueltas, largo, chaleco_color=(0.78, 0.74, 0.64)):
    torso = ("spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r")
    chaleco(base, cuerpo, rig, chaleco_color)
    mat = material_tela("casaca", color)
    bm = concha_bm(base, cuerpo, torso, 0.022, umbral=0.45, excluir=("neck_01", "head") + MANOS + PIERNAS)
    pesos = lambda p: cuerpo.pesos_en(p)
    prendas = [objeto_de_bm("casaca", bm, mat, rig, cuerpo, pesos, uv_fn=lambda v: (v.co.x * 3 + v.co.y * 3, v.co.z * 3), grosor=0.006)]
    # faldones: de la cintura a la rodilla, abiertos por delante
    z_cint = rig.data.bones["spine_01"].head_local.z + 0.02
    z_rod = rig.data.bones["calf_l"].head_local.z
    hem = lambda a: z_rod + 0.02 + (1 - largo) * 0.25 - 0.06 * math.sin(a) ** 2
    piernas = lambda i: cuerpo.suma(i, ("pelvis", "spine_01", "thigh_l", "thigh_r", "calf_l", "calf_r")) > 0.5 and cuerpo.suma(i, MANOS + ("lowerarm_l", "lowerarm_r")) < 0.3
    bm = envolvente(cuerpo, piernas, z_cint, hem, 0.03, abertura_frente=radians(34), anillos=14, ensanche=0.05)
    def pesos_falda(p):
        t = min(max((z_cint - p.z) / max(z_cint - z_rod, 0.1), 0.0), 1.0)
        return mezclar({"pelvis": 1.0}, cuerpo.pesos_en(p, filtro=lambda i: cuerpo.suma(i, ("thigh_l", "thigh_r")) > 0.5), 0.55 * t)
    prendas.append(objeto_de_bm("faldones", bm, mat, rig, cuerpo, pesos_falda, uv_fn=lambda v: (math.atan2(v.co.y, v.co.x) * 0.6, v.co.z * 3), grosor=0.006))
    # vueltas de las mangas y cuello alto
    mv = material_tela("vueltas", vueltas)
    for lado in "lr":
        bm = concha_bm(base, cuerpo, (f"lowerarm_{lado}",), 0.032, umbral=0.5, excluir=MANOS)
        zs = [v.co.z for v in bm.verts]
        corte = min(zs) + 0.09
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z > corte], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        prendas.append(objeto_de_bm(f"vuelta_{lado}", bm, mv, rig, cuerpo, pesos, grosor=0.005))
    bm = concha_bm(base, cuerpo, ("neck_01",), 0.025, umbral=0.5, excluir=("head",))
    zs = [v.co.z for v in bm.verts]
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z > min(zs) + 0.06], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    prendas.append(objeto_de_bm("cuello", bm, mv, rig, cuerpo, pesos, grosor=0.005))
    # botones al frente
    bm = bmesh.new()
    pecho = [p for i, p in enumerate(cuerpo.pos) if cuerpo.pesos[i].get("spine_03", 0) > 0.5 and abs(p.x) < 0.09]
    y_frente = min(p.y for p in pecho) - 0.03
    for k in range(6):
        z = rig.data.bones["spine_03"].head_local.z + 0.2 - k * 0.055
        for x in (-0.07, 0.07):
            lathe(bm, [(0.008, 0.0), (0.008, 0.004)], 8, Matrix.Translation((x, y_frente, z)) @ Matrix.Rotation(pi / 2, 4, "X"))
    prendas.append(objeto_de_bm("botones", bm, material_tela("boton", (0.75, 0.6, 0.25), rugosidad=0.35, metal=1.0), rig, cuerpo, pesos_rigidos("spine_03")))
    return prendas


def poncho_o_manta(cuerpo, rig, spec, nombre, manta=False):
    zt = rig.data.bones["neck_01"].head_local.z + 0.02
    if manta:
        z_cint = rig.data.bones["spine_01"].head_local.z
        hem = lambda a: z_cint + 0.02 + 0.06 * abs(math.cos(a))
        abertura = radians(40)
    else:
        z_rod = rig.data.bones["calf_l"].head_local.z
        hem = lambda a: z_rod + 0.22 + 0.2 * abs(math.cos(a))
        abertura = 0.0
    todo = lambda i: cuerpo.pesos[i].get("head", 0) < 0.3 and cuerpo.pesos[i].get("neck_01", 0) < 0.8
    bm = envolvente(cuerpo, todo, zt, hem, 0.03, abertura_frente=abertura, anillos=26, ensanche=0.03)
    mat = material_tela(nombre, spec["color"], spec.get("rayas"))
    def pesos(p):
        cerca = cuerpo.pesos_en(p, filtro=lambda i: cuerpo.suma(i, ("spine_03", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "spine_02")) > 0.4)
        t = min(max((zt - p.z) / 0.5, 0.0), 1.0)
        return mezclar(cerca, {"spine_02": 0.6, "spine_01": 0.4}, 0.35 + 0.4 * t)
    def uv(v):
        a = math.atan2(v.co.y, v.co.x)
        return (a / (2 * pi) * 2.5, (zt - v.co.z) / (zt - 0.4))
    return [objeto_de_bm(nombre, bm, mat, rig, cuerpo, pesos, uv_fn=uv, grosor=0.008)]


def muceta(base, cuerpo, rig, color):
    zt = rig.data.bones["neck_01"].head_local.z + 0.02
    z_codo = rig.data.bones["lowerarm_l"].head_local.z + 0.06
    todo = lambda i: cuerpo.pesos[i].get("head", 0) < 0.3
    bm = envolvente(cuerpo, todo, zt, lambda a: z_codo, 0.085, anillos=10)
    pesos = lambda p: mezclar(cuerpo.pesos_en(p), {"spine_03": 1.0}, 0.5)
    prendas = [objeto_de_bm("muceta", bm, material_tela("muceta", color), rig, cuerpo, pesos, uv_fn=lambda v: (v.co.x * 3, v.co.z * 3), grosor=0.006)]
    return prendas


def cruz_pectoral(cuerpo, rig):
    pecho = [p for i, p in enumerate(cuerpo.pos) if cuerpo.pesos[i].get("spine_03", 0) > 0.5 and abs(p.x) < 0.06]
    y = min(p.y for p in pecho) - 0.06
    z = rig.data.bones["spine_03"].head_local.z + 0.08
    bm = bmesh.new()
    for x0, x1, z0, z1 in ((-0.008, 0.008, -0.06, 0.03), (-0.03, 0.03, -0.005, 0.01)):
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(((x0 + x1) / 2, y, z + (z0 + z1) / 2)) @ Matrix.Diagonal(((x1 - x0), 0.008, (z1 - z0), 1)))
    return [objeto_de_bm("cruz", bm, material_tela("oro", (0.85, 0.65, 0.25), rugosidad=0.3, metal=1.0), rig, cuerpo, pesos_rigidos("spine_03"))]


def fusil(cuerpo, rig):
    """Fusil con bayoneta, vertical junto al costado derecho, sujeto por la mano."""
    h = rig.data.bones["hand_r"]
    x, y = h.head_local.x - 0.045, h.head_local.y - 0.015
    bm = bmesh.new()
    lathe(bm, [(0.03, 0.06), (0.045, 0.1), (0.032, 0.35), (0.022, 0.6), (0.02, 0.98), (0.014, 1.0)], 8, Matrix.Translation((x, y, 0.0)))
    madera = material_tela("culata", (0.32, 0.2, 0.1), rugosidad=0.6)
    ob = [objeto_de_bm("culata", bm, madera, rig, cuerpo, pesos_rigidos("hand_r"))]
    bm = bmesh.new()
    lathe(bm, [(0.011, 0.55), (0.011, 1.5), (0.013, 1.52)], 8, Matrix.Translation((x, y - 0.012, 0.0)))
    lathe(bm, [(0.006, 1.5), (0.004, 1.85), (0.001, 1.9)], 6, Matrix.Translation((x, y - 0.03, 0.0)))
    ob.append(objeto_de_bm("canon", bm, material_tela("hierro", (0.25, 0.25, 0.27), rugosidad=0.4, metal=1.0), rig, cuerpo, pesos_rigidos("hand_r")))
    return ob


def blusa(base, cuerpo, rig, color):
    torso = ("spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r")
    bm = concha_bm(base, cuerpo, torso, 0.01, umbral=0.45, excluir=("neck_01", "head") + MANOS)
    return [objeto_de_bm("blusa", bm, material_tela("blusa", color), rig, cuerpo, lambda p: cuerpo.pesos_en(p),
                         uv_fn=lambda v: (v.co.x * 4 + v.co.y * 4, v.co.z * 4))]


def corbatin(base, cuerpo, rig, color):
    bm = concha_bm(base, cuerpo, ("neck_01",), 0.038, umbral=0.4, excluir=("head",))
    zs = [v.co.z for v in bm.verts]
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z > min(zs) + 0.1], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    return [objeto_de_bm("corbatin", bm, material_tela("corbatin", color), rig, cuerpo, lambda p: cuerpo.pesos_en(p), grosor=0.004)]


# ---------------------------------------------------------------- pose y animación

class Pose:
    """Rotaciones en el marco del cuerpo (X izquierda, -Y frente, Z arriba) relativas al padre."""

    def __init__(self, rig):
        self.rig = rig
        self.rest = {b.name: b.matrix_local.to_quaternion() for b in rig.data.bones}
        self.padre = {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}
        self.orden = [b.name for b in rig.data.bones]  # padres antes que hijos

    def aplicar(self, giros, pelvis=Vector()):
        """giros: hueso -> Quaternion en el marco del cuerpo (aplicado después del padre)."""
        tot = {}
        for nombre in self.orden:
            pb = self.rig.pose.bones[nombre]
            pb.rotation_mode = "QUATERNION"
            tp = tot.get(self.padre[nombre], Quaternion())
            rc = giros.get(nombre)
            if rc is not None:
                eje, ang = rc.to_axis_angle()
                rc = Quaternion(tp @ eje, ang)
                tot[nombre] = rc @ tp
                A = tp @ self.rest[nombre]
                pb.rotation_quaternion = A.inverted() @ rc @ A
            else:
                tot[nombre] = tp
                pb.rotation_quaternion = Quaternion()
            pb.location = Vector()
        pb = self.rig.pose.bones["pelvis"]
        pb.location = self.rest["pelvis"].inverted() @ pelvis

    def clave(self, frame):
        for pb in self.rig.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=frame)
        self.rig.pose.bones["pelvis"].keyframe_insert("location", frame=frame)


def rx(g):
    return Quaternion((1, 0, 0), radians(g))


def ry(g):
    return Quaternion((0, 1, 0), radians(g))


def rz(g):
    return Quaternion((0, 0, 1), radians(g))


def brazos_abajo(rig):
    """Pone los brazos junto al cuerpo (desde la pose en A) para usarla como reposo."""
    pose = Pose(rig)
    giros = {}
    for lado, sx in (("l", 1), ("r", -1)):
        for hueso, destino in ((f"upperarm_{lado}", Vector((sx * 0.13, 0.03, -1))),
                               (f"lowerarm_{lado}", Vector((sx * 0.05, -0.12, -1))),
                               (f"hand_{lado}", Vector((sx * 0.02, -0.05, -1)))):
            giros[hueso] = destino
    # calcula giros por diferencia de dirección, en orden de jerarquía
    tot = {}
    final = {}
    for nombre in pose.orden:
        b = rig.data.bones[nombre]
        tp = tot.get(pose.padre[nombre], Quaternion())
        if nombre in giros:
            actual = tp @ (b.tail_local - b.head_local).normalized()
            rc = actual.rotation_difference(giros[nombre].normalized())
            final[nombre] = rc
            tot[nombre] = rc @ tp
        else:
            tot[nombre] = tp
    # aplica en marco absoluto (no relativo al padre)
    for nombre in pose.orden:
        pb = rig.pose.bones[nombre]
        pb.rotation_mode = "QUATERNION"
        tp = tot.get(pose.padre[nombre], Quaternion())
        if nombre in final:
            A = tp @ pose.rest[nombre]
            pb.rotation_quaternion = A.inverted() @ final[nombre] @ A
    bpy.context.view_layer.update()
    RigService.apply_pose_as_rest_pose(rig)


def ciclo(nombre, rig, dur, fn, pasos=None):
    pose = Pose(rig)
    act = bpy.data.actions.new(nombre)
    act.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = act
    n = pasos or max(8, int(dur * FPS / 2))
    for k in range(n + 1):
        t = (k / n) * dur
        giros, pelvis = fn(t, 2 * pi * t / dur)
        pose.aplicar(giros, pelvis)
        pose.clave(1 + round(t * FPS))
    tr = rig.animation_data.nla_tracks.new()
    tr.name = nombre
    tr.strips.new(nombre, 1, act)
    rig.animation_data.action = None


def piernas_caminar(f, zancada=24, rodilla=48, lado_fase=0.0):
    g = {}
    for lado, ph in (("l", 0.0), ("r", pi)):
        a = f + ph + lado_fase
        muslo = zancada * sin(a)
        rod = 6 + rodilla * max(0.0, cos(a)) ** 1.6
        g[f"thigh_{lado}"] = rx(-muslo)
        g[f"calf_{lado}"] = rx(rod)
        g[f"foot_{lado}"] = rx(-0.55 * (muslo - rod) * 0.5 + 4)
    return g


def caminar(t, f, zancada=24, brazos=18, fusil=False, prisionero=False, antorcha=False):
    g = piernas_caminar(f, zancada)
    g["pelvis"] = rz(5 * sin(f))
    g["spine_02"] = rz(-4 * sin(f)) @ rx(-3)
    g["neck_01"] = rz(-1.5 * sin(f))
    for lado, sx, ph in (("l", 1, pi), ("r", -1, 0.0)):
        swing = brazos * sin(f + ph)
        g[f"upperarm_{lado}"] = rx(-swing)
        g[f"lowerarm_{lado}"] = rx(-(5 + max(0.0, swing) * 0.45))
    if fusil:
        g["upperarm_r"] = rx(-2) @ ry(3)
        g["lowerarm_r"] = rx(-8)
    if antorcha:
        g["upperarm_r"] = rx(-115) @ ry(-12)
        g["lowerarm_r"] = rx(-35)
        g["hand_r"] = rx(25)
    if prisionero:
        # manos atadas por delante: antebrazos juntos frente al vientre
        for lado, sx in (("l", 1), ("r", -1)):
            g[f"upperarm_{lado}"] = rx(-12) @ rz(-sx * 22)
            g[f"lowerarm_{lado}"] = rx(-78) @ rz(-sx * 18)
            g[f"hand_{lado}"] = rx(8)
        g["head"] = rz(18 * sin(f * 0.25)) @ rx(-6)
    bob = Vector((0.012 * sin(f), 0.0, -0.025 + 0.022 * cos(2 * f)))
    return g, bob


def correr(t, f):
    g = piernas_caminar(f, 38, 85)
    g["pelvis"] = rz(7 * sin(f)) @ rx(-10)
    g["spine_02"] = rz(-6 * sin(f)) @ rx(-5)
    for lado, ph in (("l", pi), ("r", 0.0)):
        swing = 35 * sin(f + ph)
        g[f"upperarm_{lado}"] = rx(-swing)
        g[f"lowerarm_{lado}"] = rx(-80)
    return g, Vector((0.0, 0.0, -0.05 + 0.045 * cos(2 * f)))


def reposo(t, f):
    g = {"spine_02": rx(-1.5 * sin(f)), "spine_01": rz(1.5 * sin(f * 0.5)),
         "head": rz(6 * sin(f * 0.5 + 1)) @ rx(2 * sin(f)),
         "lowerarm_l": rx(-5), "lowerarm_r": rx(-5)}
    return g, Vector((0.008 * sin(f * 0.5), 0.0, -0.004 * sin(f)))


def llamar(t, f):
    g, p = reposo(t, f)
    g["upperarm_r"] = ry(150 + 18 * sin(2 * f))
    g["lowerarm_r"] = rx(-20)
    g["spine_02"] = rz(-8) @ rx(-4)
    g["head"] = rz(-10)
    return g, p


def vitorear(t, f):
    g, p = reposo(t, f)
    s = 0.5 + 0.5 * sin(f)
    g["upperarm_l"] = ry(-(150 + 15 * s)) @ rx(-10)
    g["upperarm_r"] = ry(150 + 15 * s) @ rx(-10)
    g["lowerarm_l"] = rx(-25 - 30 * s)
    g["lowerarm_r"] = rx(-25 - 30 * s)
    g["head"] = rx(-12)
    return g, Vector((0.0, 0.0, 0.015 * s))


def antorcha_quieto(t, f):
    g, p = reposo(t, f)
    g["upperarm_r"] = rx(-115) @ ry(-12)
    g["lowerarm_r"] = rx(-35)
    g["hand_r"] = rx(25)
    return g, p


def bendecir(t, f):
    g, p = reposo(t, f)
    s = sin(f * 0.5)
    g["upperarm_r"] = rx(-70 - 10 * s) @ ry(-10)
    g["lowerarm_r"] = rx(-55)
    g["hand_r"] = rx(-30) @ rz(30 * s)
    g["upperarm_l"] = rx(-20)
    g["lowerarm_l"] = rx(-60)
    return g, p


ANIMACIONES = {
    "reposo": (4.0, reposo),
    "caminar": (1.1, caminar),
    "correr": (0.7, correr),
    "marcha_fusil": (1.1, lambda t, f: caminar(t, f, zancada=26, brazos=14, fusil=True)),
    "prisionero": (1.3, lambda t, f: caminar(t, f, zancada=20, prisionero=True)),
    "llamar": (1.2, llamar),
    "vitorear": (1.0, vitorear),
    "antorcha": (4.0, antorcha_quieto),
    "antorcha_caminar": (1.1, lambda t, f: caminar(t, f, antorcha=True)),
    "bendecir": (4.0, bendecir),
}


# ---------------------------------------------------------------- armado

def limite_textura(img, detalle_alto):
    ruta = img.filepath.replace("\\", "/")
    if any(k in ruta for k in ("/eyes/", "/eyebrows/", "/eyelashes/")):
        return 256
    if "/skins/" in ruta:
        return 1024 if detalle_alto else 512
    if "/hair/" in ruta or "/clothes/" in ruta:
        return 512
    return 256  # telas generadas


def armar(nombre, spec, detalle_alto):
    global ACTUAL
    ACTUAL = nombre
    nueva_escena()
    random.seed(nombre)
    macro = TargetService.get_default_macro_info_dict()
    macro.update(spec["macro"])
    macro["race"] = spec["raza"]
    base = HumanService.create_human(macro_detail_dict=macro)
    base.name = nombre
    rig = HumanService.add_builtin_rig(base, "game_engine")
    rig.name = nombre + "_esqueleto"
    proxy = None
    if not detalle_alto:
        proxy = HumanService.add_mhclo_asset(str(DATA / f"proxymeshes/{spec['proxy']}/{spec['proxy']}.proxy"), base,
                                             asset_type="Proxymeshes", subdiv_levels=0, material_type="NONE")
        m = base.modifiers.new("Ocultar base", "MASK")
        m.vertex_group = "body"
        m.invert_vertex_group = True
    HumanService.set_character_skin(str(DATA / f"skins/{spec['piel']}/{spec['piel']}.mhmat"), base, bodyproxy=proxy, skin_type="GAMEENGINE")
    partes = [("Eyes", "eyes/low-poly/low-poly.mhclo"), ("Eyebrows", "eyebrows/eyebrow001/eyebrow001.mhclo")]
    if detalle_alto:
        partes.append(("Eyelashes", "eyelashes/eyelashes01/eyelashes01.mhclo"))
    if spec.get("pelo"):
        partes.append(("Hair", f"hair/{spec['pelo']}/{spec['pelo']}.mhclo"))
    for tipo, ruta in partes:
        HumanService.add_mhclo_asset(str(DATA / ruta), base, asset_type=tipo, subdiv_levels=0, material_type="GAMEENGINE")
    for prenda, color in spec.get("ropa", {}).items():
        ob = HumanService.add_mhclo_asset(str(DATA / f"clothes/{prenda}/{prenda}.mhclo"), base, asset_type="Clothes",
                                          subdiv_levels=0, material_type="GAMEENGINE")
        if ob is not None and color is not None:
            ob.data.materials.clear()
            ob.data.materials.append(material_tela(prenda, color))

    brazos_abajo(rig)
    cuerpo = Cuerpo(base)

    if "casaca" in spec:
        casaca(base, cuerpo, rig, **spec["casaca"])
    if "poncho" in spec:
        poncho_o_manta(cuerpo, rig, spec["poncho"], "poncho")
    if "blusa" in spec:
        blusa(base, cuerpo, rig, spec["blusa"])
    if "manta" in spec:
        poncho_o_manta(cuerpo, rig, spec["manta"], "manta", manta=True)
    if "muceta" in spec:
        muceta(base, cuerpo, rig, spec["muceta"])
    if spec.get("cruz"):
        cruz_pectoral(cuerpo, rig)
    if "corbatin" in spec:
        corbatin(base, cuerpo, rig, spec["corbatin"])
    if spec.get("sombrero"):
        sombrero(spec["sombrero"], cuerpo, rig)
    if spec.get("fusil"):
        fusil(cuerpo, rig)

    for anim in spec["animaciones"]:
        dur, fn = ANIMACIONES[anim]
        ciclo(anim, rig, dur, fn)

    # Texturas livianas para la web; las de MakeHuman se comparten entre personajes
    # (mismo nombre y tamaño = un solo archivo en texturas/).
    for img in bpy.data.images:
        if img.size[0] == 0:
            continue
        limite = limite_textura(img, detalle_alto)
        w, h = img.size
        if max(w, h) > limite:
            f = limite / max(w, h)
            img.scale(max(1, int(w * f)), max(1, int(h * f)))
        if img.filepath:
            img.name = f"{Path(bpy.path.abspath(img.filepath)).stem}_{max(img.size)}"
        img.pack()

    if proxy is not None:
        bpy.data.objects.remove(base, do_unlink=True)
    for ob in bpy.context.scene.objects:
        ob.select_set(ob.type in ("MESH", "ARMATURE") and ob.visible_get() and not ob.name.startswith("Icosphere"))
    SALIDA.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(SALIDA / f"{nombre}.gltf"), export_format="GLTF_SEPARATE", export_texture_dir="texturas",
        use_selection=True, export_apply=True,
        export_yup=True, export_animations=True, export_animation_mode="NLA_TRACKS", export_cameras=False,
        export_lights=False, export_image_format="AUTO",
    )
    print(f"[personaje] {nombre}: {len(bpy.context.selected_objects)} objetos")


def main():
    pedidos = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    todos = [(n, s, True) for n, s in PRINCIPALES.items()] + [(n, s, False) for n, s in MULTITUD.items()]
    for nombre, spec, alto in todos:
        if pedidos and nombre not in pedidos:
            continue
        try:
            armar(nombre, spec, alto)
        except Exception:
            traceback.print_exc()
            print(f"[error] {nombre}")


if __name__ == "__main__":
    main()
