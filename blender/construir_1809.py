"""Modela La Plata (hoy Sucre) en 1809 y exporta los .glb para Godot.

Uso (sin abrir la interfaz):
    blender -b --factory-startup --python blender/construir_1809.py

Genera en godot/assets/modelos/:
    ciudad_1809.glb   plaza, manzanas, Catedral, Universidad, Audiencia, San Francisco,
                      suelo y cerros, más marcadores (Empties) para la historia
    campana.glb       campana de San Francisco con su badajo (origen en el eje)
    farol.glb         farol colonial de pared (con un Empty "luz" en la llama)
    barril.glb, antorcha.glb

Convenciones: Blender Z arriba, X este, Y norte. Las fachadas se arman en un marco
local (x a lo largo de la fachada, y hacia adentro del edificio, z arriba).
Los objetos con sufijo "-col" generan colisión al importarse en Godot.
"""
import math
import random
from math import cos, pi, radians, sin, tan
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "godot" / "assets" / "modelos"
SALIDA.mkdir(parents=True, exist_ok=True)

rnd = random.Random(1809)

# Metros que cubre una repetición de la textura de cada material.
ESCALA = {
    "empedrado": 1.7, "plaza": 2.3, "losa": 1.6, "revoque_blanco": 3.0, "revoque_ocre": 3.0,
    "zocalo": 2.0, "tejas": 2.2, "madera": 1.2, "madera_puerta": 1.6, "piedra": 2.5,
    "piedra_revocada": 3.5, "cerro": 30.0,
}
# Color de respaldo (si en Godot no se reemplaza el material).
COLOR = {
    "empedrado": (0.35, 0.33, 0.3), "plaza": (0.4, 0.38, 0.34), "losa": (0.45, 0.43, 0.4),
    "revoque_blanco": (0.85, 0.84, 0.8), "revoque_ocre": (0.78, 0.62, 0.38), "zocalo": (0.55, 0.35, 0.25),
    "tejas": (0.55, 0.28, 0.18), "madera": (0.3, 0.2, 0.12), "madera_puerta": (0.22, 0.14, 0.08),
    "piedra": (0.55, 0.5, 0.42), "piedra_revocada": (0.75, 0.72, 0.66), "hierro": (0.05, 0.05, 0.05),
    "bronce": (0.45, 0.3, 0.15), "cerro": (0.3, 0.27, 0.2), "ventana_luz": (1.0, 0.6, 0.25),
    "vidrio_farol": (1.0, 0.75, 0.4), "cera": (0.95, 0.9, 0.75), "agua": (0.1, 0.15, 0.18),
    "tela": (0.15, 0.1, 0.08), "presencia": (0.9, 0.7, 0.4),
}


# ---------------------------------------------------------------- utilidades

def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(nombre):
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre)
    c = COLOR.get(nombre, (0.7, 0.7, 0.7))
    m.diffuse_color = (*c, 1.0)
    try:
        m.use_nodes = True
    except Exception:
        pass
    if m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                n.inputs["Base Color"].default_value = (*c, 1.0)
                n.inputs["Roughness"].default_value = 0.85
    return m


def Rz(grados):
    return Matrix.Rotation(radians(grados), 4, "Z")


def T(x, y, z=0.0):
    return Matrix.Translation((x, y, z))


class Pieza:
    """Malla acumulada (varios materiales) que termina en un solo objeto de Blender."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.verify()
        self.mats = []
        self.desfase = (rnd.random() * 7.0, rnd.random() * 7.0)

    def _idx(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def _cerrar(self, caras, M, mat, suave=False, uv_giro=False):
        """Material, sombreado y UV proyectadas en el marco local (escala real)."""
        i = self._idx(mat)
        tile = ESCALA.get(mat, 2.0)
        Minv = M.inverted()
        R = Minv.to_3x3()
        ox, oy = self.desfase
        for f in caras:
            f.material_index = i
            f.smooth = suave
            f.normal_update()
            n = R @ f.normal
            eje = max(range(3), key=lambda k: abs(n[k]))
            a, b = ((1, 2), (0, 2), (0, 1))[eje]
            if uv_giro:
                a, b = b, a
            for l in f.loops:
                p = Minv @ l.vert.co
                l[self.uv].uv = (p[a] / tile + ox, p[b] / tile + oy)

    def caja(self, mat, M, x0, x1, y0, y1, z0, z1, uv_giro=False):
        if x1 - x0 < 1e-4 or y1 - y0 < 1e-4 or z1 - z0 < 1e-4:
            return
        v = {}
        for xi, x in enumerate((x0, x1)):
            for yi, y in enumerate((y0, y1)):
                for zi, z in enumerate((z0, z1)):
                    v[xi, yi, zi] = self.bm.verts.new(M @ Vector((x, y, z)))
        quads = [
            (v[0, 0, 0], v[0, 1, 0], v[1, 1, 0], v[1, 0, 0]),
            (v[0, 0, 1], v[1, 0, 1], v[1, 1, 1], v[0, 1, 1]),
            (v[0, 0, 0], v[1, 0, 0], v[1, 0, 1], v[0, 0, 1]),
            (v[0, 1, 0], v[0, 1, 1], v[1, 1, 1], v[1, 1, 0]),
            (v[0, 0, 0], v[0, 0, 1], v[0, 1, 1], v[0, 1, 0]),
            (v[1, 0, 0], v[1, 1, 0], v[1, 1, 1], v[1, 0, 1]),
        ]
        caras = [self.bm.faces.new(q) for q in quads]
        bmesh.ops.recalc_face_normals(self.bm, faces=caras)
        self._cerrar(caras, M, mat, uv_giro=uv_giro)

    def prisma(self, mat, M, pts, eje, a0, a1, suave=False, uv_giro=False):
        """Polígono 2D extruido. eje='y': pts son (x, z); eje='x': pts son (y, z)."""
        def P(u, w, t):
            return Vector((u, t, w)) if eje == "y" else Vector((t, u, w))
        A = [self.bm.verts.new(M @ P(u, w, a0)) for u, w in pts]
        B = [self.bm.verts.new(M @ P(u, w, a1)) for u, w in pts]
        caras = [self.bm.faces.new(A), self.bm.faces.new(B)]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            caras.append(self.bm.faces.new((A[i], A[j], B[j], B[i])))
        bmesh.ops.recalc_face_normals(self.bm, faces=caras)
        self._cerrar(caras, M, mat, suave, uv_giro)

    def torno(self, mat, M, perfil, seg, tapas=True, cerrado=False, suave=True, giro=0.0):
        """Superficie de revolución alrededor del eje z local. perfil: [(r, z), ...]."""
        anillos = []
        for r, z in perfil:
            r = max(r, 0.002)
            anillos.append([
                self.bm.verts.new(M @ Vector((r * cos(giro + 2 * pi * k / seg), r * sin(giro + 2 * pi * k / seg), z)))
                for k in range(seg)
            ])
        pares = list(zip(anillos, anillos[1:]))
        if cerrado:
            pares.append((anillos[-1], anillos[0]))
        caras = []
        for a, b in pares:
            for k in range(seg):
                kk = (k + 1) % seg
                caras.append(self.bm.faces.new((a[k], a[kk], b[kk], b[k])))
        if tapas and not cerrado:
            caras.append(self.bm.faces.new(anillos[0]))
            caras.append(self.bm.faces.new(anillos[-1]))
        bmesh.ops.recalc_face_normals(self.bm, faces=caras)
        self._cerrar(caras, M, mat, suave)

    def muro(self, mat, M, x0, x1, z0, z1, y0, y1, vanos):
        """Muro con vanos rectangulares (x_a, x_b, z_a, z_b), armado con bloques."""
        cortes = {z0, z1}
        for v in vanos:
            cortes.update(z for z in (v[2], v[3]) if z0 < z < z1)
        cortes = sorted(cortes)
        for za, zb in zip(cortes, cortes[1:]):
            zm = (za + zb) / 2
            huecos = sorted((v[0], v[1]) for v in vanos if v[2] < zm < v[3])
            x = x0
            for ha, hb in huecos:
                if ha > x:
                    self.caja(mat, M, x, ha, y0, y1, za, zb)
                x = max(x, hb)
            if x < x1:
                self.caja(mat, M, x, x1, y0, y1, za, zb)

    def arco(self, mat, M, xa, xb, zs, y0, y1, pasos=10):
        """Rellena las enjutas de un arco de medio punto sobre un vano rectangular."""
        r = (xb - xa) / 2
        xc = xa + r
        izq = [(xa, zs)]
        for k in range(1, pasos + 1):
            t = pi - (pi / 2) * k / pasos
            izq.append((xc + r * cos(t), zs + r * sin(t)))
        izq.append((xa, zs + r))
        self.prisma(mat, M, izq, "y", y0, y1)
        der = [(2 * xc - x, z) for x, z in reversed(izq)]
        self.prisma(mat, M, der, "y", y0, y1)

    def objeto(self):
        me = bpy.data.meshes.new(self.nombre)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(material(m))
        ob = bpy.data.objects.new(self.nombre, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


def marcador(nombre, pos, rot_z=0.0):
    e = bpy.data.objects.new(nombre, None)
    e.empty_display_type = "PLAIN_AXES"
    e.location = Vector(pos)
    e.rotation_euler = (0.0, 0.0, rot_z)
    bpy.context.scene.collection.objects.link(e)
    return e


CONTADOR = {"farol": 0, "barril": 0, "cantaro": 0}


def marca_prop(tipo, M, x, y, z=0.12):
    CONTADOR[tipo] += 1
    p = M @ Vector((x, y, z))
    rot = M.to_euler().z
    marcador(f"P_{tipo}_{CONTADOR[tipo]:02d}", p, rot)


# ---------------------------------------------------------------- arquitectura

def puerta(o, M, c, a, h, portal):
    o.caja("madera_puerta", M, c - a / 2, c - 0.01, 0.38, 0.46, 0, h)
    o.caja("madera_puerta", M, c + 0.01, c + a / 2, 0.38, 0.46, 0, h)
    for lado in (-1, 1):  # cuarterones en relieve
        x0 = c + (0.08 if lado > 0 else -a / 2 + 0.08)
        x1 = x0 + a / 2 - 0.16
        for k in range(3):
            z0 = 0.25 + k * (h - 0.4) / 3
            o.caja("madera_puerta", M, x0, x1, 0.34, 0.38, z0, z0 + (h - 0.4) / 3 - 0.18)
    if portal:
        o.caja("piedra", M, c - a / 2 - 0.5, c - a / 2, -0.2, 0.02, 0, h + 0.1)
        o.caja("piedra", M, c + a / 2, c + a / 2 + 0.5, -0.2, 0.02, 0, h + 0.1)
        o.caja("piedra", M, c - a / 2 - 0.7, c + a / 2 + 0.7, -0.28, 0.02, h + 0.1, h + 0.45)
        o.prisma("piedra", M, [(c - a / 2 - 0.45, h + 0.45), (c + a / 2 + 0.45, h + 0.45), (c, h + 1.0)], "y", -0.18, 0.02)
    else:
        o.caja("madera", M, c - a / 2 - 0.12, c - a / 2, -0.03, 0.06, 0, h + 0.12)
        o.caja("madera", M, c + a / 2, c + a / 2 + 0.12, -0.03, 0.06, 0, h + 0.12)
        o.caja("madera", M, c - a / 2 - 0.12, c + a / 2 + 0.12, -0.03, 0.06, h, h + 0.14)


def ventana_baja(o, M, c, iluminada):
    z0, z1, a = 1.0, 2.55, 1.1
    if iluminada:
        o.caja("ventana_luz", M, c - a / 2, c + a / 2, 0.42, 0.47, z0, z1)
        o.caja("madera", M, c - 0.03, c + 0.03, 0.36, 0.42, z0, z1)
        o.caja("madera", M, c - a / 2, c + a / 2, 0.36, 0.42, (z0 + z1) / 2 - 0.03, (z0 + z1) / 2 + 0.03)
    else:
        o.caja("madera_puerta", M, c - a / 2, c + a / 2, 0.36, 0.46, z0, z1)
        o.caja("madera_puerta", M, c - 0.02, c + 0.02, 0.33, 0.36, z0, z1)
    o.caja("piedra", M, c - a / 2 - 0.12, c + a / 2 + 0.12, -0.16, 0.36, z0 - 0.1, z0)
    nb = 9
    for k in range(nb):
        x = c - a / 2 + 0.06 + k * (a - 0.12) / (nb - 1)
        o.caja("hierro", M, x - 0.013, x + 0.013, -0.125, -0.1, z0 - 0.05, z1 + 0.06)
    for z in (z0 + 0.12, (z0 + z1) / 2, z1 - 0.04):
        o.caja("hierro", M, c - a / 2 - 0.03, c + a / 2 + 0.03, -0.135, -0.09, z - 0.016, z + 0.016)
    for x in (c - a / 2 - 0.02, c + a / 2 + 0.02):
        for z in (z0 - 0.04, z1 + 0.05):
            o.caja("hierro", M, x - 0.013, x + 0.013, -0.13, 0.0, z - 0.013, z + 0.013)


def balconera(o, M, c, iluminada):
    z0, z1, a = 4.15, 6.35, 1.1
    if iluminada:
        o.caja("ventana_luz", M, c - a / 2, c + a / 2, 0.42, 0.47, z0, z1)
        o.caja("madera", M, c - 0.03, c + 0.03, 0.36, 0.42, z0, z1)
        for z in (z0 + 0.9, z0 + 1.6):
            o.caja("madera", M, c - a / 2, c + a / 2, 0.36, 0.42, z - 0.03, z + 0.03)
    else:
        o.caja("madera_puerta", M, c - a / 2, c - 0.01, 0.38, 0.46, z0, z1)
        o.caja("madera_puerta", M, c + 0.01, c + a / 2, 0.38, 0.46, z0, z1)
    o.caja("madera", M, c - a / 2 - 0.1, c + a / 2 + 0.1, -0.04, 0.06, z1, z1 + 0.12)


def balcon(o, M, xa, xb, z=3.95, vuelo=0.95):
    o.caja("madera", M, xa, xb, -vuelo, 0.0, z - 0.12, z)
    k = xa + 0.2
    while k < xb - 0.15:
        o.prisma("madera", M, [(0.0, z - 0.12), (-vuelo + 0.15, z - 0.12), (0.0, z - 0.42)], "x", k - 0.04, k + 0.04)
        k += 0.9
    x = xa + 0.06
    while x < xb - 0.05:
        o.caja("madera", M, x - 0.02, x + 0.02, -vuelo + 0.04, -vuelo + 0.08, z, z + 0.95)
        x += 0.13
    for xs in (xa + 0.04, xb - 0.04):
        y = -vuelo + 0.15
        while y < -0.05:
            o.caja("madera", M, xs - 0.02, xs + 0.02, y - 0.02, y + 0.02, z, z + 0.95)
            y += 0.13
    o.caja("madera", M, xa, xb, -vuelo, -vuelo + 0.1, z + 0.95, z + 1.03)
    o.caja("madera", M, xa, xb, -vuelo, -vuelo + 0.08, z, z + 0.06)
    o.caja("madera", M, xa, xa + 0.08, -vuelo, 0.0, z + 0.95, z + 1.03)
    o.caja("madera", M, xb - 0.08, xb, -vuelo, 0.0, z + 0.95, z + 1.03)


def tejado(o, M, ancho, fondo, alto, vuelo=0.75, pend=22.0):
    t = tan(radians(pend))
    yr = fondo * 0.5
    zr = alto + (yr + vuelo) * t
    yb = fondo + 0.2
    zb = zr - (yb - yr) * t
    e = 0.14
    perfil = [(-vuelo, alto), (yr, zr), (yb, zb), (yb, zb + e), (yr, zr + e), (-vuelo, alto + e)]
    o.prisma("tejas", M, perfil, "x", -0.06, ancho + 0.06)
    hastial = [(-vuelo, alto), (yr, zr), (yb, zb), (yb, alto - 0.5), (-vuelo, alto - 0.5)]
    o.prisma("revoque_blanco", M, hastial, "x", 0.0, 0.2)
    o.prisma("revoque_blanco", M, hastial, "x", ancho - 0.2, ancho)
    o.caja("madera", M, 0.0, ancho, -vuelo, 0.0, alto - 0.05, alto)
    x = 0.3
    while x < ancho - 0.2:
        o.caja("madera", M, x - 0.05, x + 0.05, -vuelo + 0.06, 0.0, alto - 0.2, alto - 0.05)
        x += 0.55


def acera(o, M, x0, x1):
    o.prisma("losa", M, [(0.0, 0.0), (-1.25, 0.0), (-1.05, 0.12), (0.0, 0.12)], "x", x0, x1)


def costado(o, M, x, lado, fondo, alto, pisos, color, luces):
    """Fachada lateral de una casa de esquina: zócalo y ventanas hacia la otra calle."""
    Ml = M @ T(x, fondo, 0) @ Rz(-90) if lado < 0 else M @ T(x, 0.0, 0) @ Rz(90)
    o.caja("zocalo", Ml, 0.0, fondo, -0.03, 0.0, 0, 0.85)
    o.caja(color, Ml, -0.02, fondo + 0.02, -0.16, 0.0, alto - 0.3, alto - 0.05)
    for c in (fondo * 0.3, fondo * 0.7):
        o.caja("madera_puerta", Ml, c - 0.55, c + 0.55, -0.05, 0.0, 1.0, 2.55)
        o.caja("madera", Ml, c - 0.65, c + 0.65, -0.08, 0.0, 0.92, 1.0)
        for k in range(7):
            xb = c - 0.5 + k * (1.0 / 6)
            o.caja("hierro", Ml, xb - 0.013, xb + 0.013, -0.2, -0.17, 0.95, 2.6)
        for z in (1.12, 1.78, 2.5):
            o.caja("hierro", Ml, c - 0.56, c + 0.56, -0.21, -0.16, z - 0.016, z + 0.016)
        if pisos == 2:
            if rnd.random() < luces:
                o.caja("ventana_luz", Ml, c - 0.5, c + 0.5, -0.04, 0.0, 4.5, 6.1)
            else:
                o.caja("madera_puerta", Ml, c - 0.5, c + 0.5, -0.05, 0.0, 4.5, 6.1)
            o.caja("madera", Ml, c - 0.6, c + 0.6, -0.12, 0.0, 4.42, 4.5)
            o.caja("madera", Ml, c - 0.6, c + 0.6, -0.08, 0.0, 6.1, 6.2)


def casa(o, M, ancho, alto=None, fondo=12.0, color=None, portal=False, corrido=None,
         pisos=None, luces=0.35, props=True, lado_izq=False, lado_der=False):
    """Casa colonial en el marco M (origen en la esquina izquierda de la fachada)."""
    pisos = pisos or rnd.choices([2, 1], [0.8, 0.2])[0]
    alto = alto or (rnd.uniform(7.0, 8.1) if pisos == 2 else rnd.uniform(4.1, 4.7))
    color = color or rnd.choices(["revoque_blanco", "revoque_ocre"], [0.8, 0.2])[0]
    corrido = rnd.random() < 0.4 if corrido is None else corrido
    grosor = 0.55
    n = max(1, round(ancho / 3.3))
    w = ancho / n
    centros = [(i + 0.5) * w for i in range(n)]
    i_puerta = n // 2 if portal else rnd.randrange(n)
    a_p, h_p = (2.1, 3.3) if portal else (1.6, 2.8)

    vanos, baja = [], []
    for i, c in enumerate(centros):
        if i == i_puerta:
            vanos.append((c - a_p / 2, c + a_p / 2, 0.0, h_p))
        else:
            vanos.append((c - 0.55, c + 0.55, 1.0, 2.55))
            baja.append(c)
        if pisos == 2:
            vanos.append((c - 0.55, c + 0.55, 4.15, 6.35))

    o.muro(color, M, 0, ancho, 0, alto, 0, grosor, vanos)
    o.caja(color, M, 0, ancho, grosor, fondo, 0, alto)
    o.muro("zocalo", M, 0, ancho, 0, 0.85, -0.03, 0.0, [v for v in vanos if v[2] == 0.0])
    o.caja(color, M, -0.02, ancho + 0.02, -0.16, 0.0, alto - 0.3, alto - 0.05)
    if pisos == 2:
        o.caja(color, M, 0, ancho, -0.07, 0.0, 3.72, 3.84)

    puerta(o, M, centros[i_puerta], a_p, h_p, portal)
    for c in baja:
        ventana_baja(o, M, c, rnd.random() < luces)
    if pisos == 2:
        for c in centros:
            balconera(o, M, c, rnd.random() < luces)
        if corrido:
            balcon(o, M, 0.35, ancho - 0.35)
        else:
            for c in centros:
                balcon(o, M, c - 0.85, c + 0.85)
    tejado(o, M, ancho, fondo, alto)
    acera(o, M, 0.0, ancho)
    if lado_izq:
        costado(o, M, 0.0, -1, fondo, alto, pisos, color, luces)
    if lado_der:
        costado(o, M, ancho, 1, fondo, alto, pisos, color, luces)

    if props and rnd.random() < 0.35:
        lado = 1 if rnd.random() < 0.5 else -1
        marca_prop("barril", M, centros[i_puerta] + lado * (a_p / 2 + 0.7), -0.55)
    if props and rnd.random() < 0.25 and baja:
        marca_prop("cantaro", M, rnd.choice(baja) + 0.3, -0.4)
    return centros[i_puerta]


def templo(o, M, ancho, fondo, alto, mat, torre_ancho, piso_camp, prefijo, mat_torre=None, cupula="revoque_blanco"):
    """Iglesia: torre a la izquierda de la fachada y nave con portada de piedra."""
    mat_torre = mat_torre or mat
    tw = torre_ancho
    xn0, xn1 = tw + 0.4, ancho
    c = (xn0 + xn1) / 2
    a, zs = 3.2, 4.4
    r = a / 2
    # nave
    coro = (c - 0.7, c + 0.7, alto - 4.6, alto - 2.6)
    o.muro(mat, M, xn0, xn1, 0, alto, 0, 1.0, [(c - a / 2, c + a / 2, 0.0, zs + r), coro])
    o.arco(mat, M, c - a / 2, c + a / 2, zs, 0, 1.0)
    o.arco(mat, M, coro[0], coro[1], alto - 3.3, 0, 1.0)
    o.caja(mat, M, xn0, xn1, 1.0, fondo, 0, alto)
    o.caja("madera_puerta", M, c - a / 2, c - 0.01, 0.7, 0.85, 0, zs)
    o.caja("madera_puerta", M, c + 0.01, c + a / 2, 0.7, 0.85, 0, zs)
    semi = [(c + r * cos(pi * k / 12), zs + r * sin(pi * k / 12)) for k in range(13)]
    o.prisma("madera_puerta", M, semi, "y", 0.7, 0.85)
    o.caja("ventana_luz", M, coro[0], coro[1], 0.85, 0.9, coro[2], coro[3])
    # portada
    for lado in (-1, 1):
        xc = c + lado * (a / 2 + 0.75)
        o.caja("piedra", M, xc - 0.45, xc + 0.45, -0.6, 0.02, 0, 0.9)
        o.torno("piedra", M @ T(xc, -0.3, 0.9), [(0.3, zs + r + 0.4 - 0.9), (0.3, 0.0)], 12, suave=True)
        o.caja("piedra", M, xc - 0.42, xc + 0.42, -0.6, 0.02, zs + r - 0.45, zs + r + 0.15)
    o.caja("piedra", M, c - a / 2 - 1.5, c + a / 2 + 1.5, -0.7, 0.02, zs + r + 0.15, zs + r + 0.75)
    o.caja("piedra", M, c - 0.9, c + 0.9, -0.4, 0.02, zs + r + 0.75, zs + r + 2.6)
    o.prisma("piedra", M, [(c - 1.1, zs + r + 2.6), (c + 1.1, zs + r + 2.6), (c, zs + r + 3.4)], "y", -0.45, 0.02)
    # cornisa y frontón
    o.caja(mat, M, xn0 - 0.15, xn1 + 0.15, -0.3, 1.0, alto - 0.45, alto)
    o.prisma(mat, M, [(xn0, alto), (xn1, alto), (c, alto + 2.8)], "y", -0.05, 1.0)
    o.torno("hierro", M @ T(c, 0.4, alto + 2.8), [(0.05, 1.6), (0.05, 0.0)], 6)
    o.caja("hierro", M, c - 0.4, c + 0.4, 0.35, 0.45, alto + 3.9, alto + 4.0)
    # techo de la nave (cumbrera a lo largo de la nave)
    ta = tan(radians(26))
    mitad = (xn1 - xn0) / 2
    perfil = [(xn0 - 0.3, alto - 0.25), (c, alto + mitad * ta), (xn1 + 0.3, alto - 0.25),
              (xn1 + 0.3, alto - 0.1), (c, alto + mitad * ta + 0.16), (xn0 - 0.3, alto - 0.1)]
    o.prisma("tejas", M, [(x, z) for x, z in perfil], "y", 1.0, fondo + 0.3, uv_giro=True)
    acera(o, M, xn0, xn1)

    # torre
    y0 = -0.5
    dc = tw / 2
    o.muro(mat_torre, M, 0, tw, 0, piso_camp, y0, 0.4, [(dc - 0.65, dc + 0.65, 0.0, 2.6)])
    o.caja(mat_torre, M, 0, tw, 0.4, tw + y0, 0, piso_camp)
    o.caja("madera_puerta", M, dc - 0.65, dc + 0.65, 0.2, 0.3, 0, 2.6)
    o.caja("piedra", M, dc - 0.95, dc - 0.65, y0 - 0.15, y0 + 0.02, 0, 2.8)
    o.caja("piedra", M, dc + 0.65, dc + 0.95, y0 - 0.15, y0 + 0.02, 0, 2.8)
    o.caja("piedra", M, dc - 1.05, dc + 1.05, y0 - 0.2, y0 + 0.02, 2.6, 2.95)
    o.caja("piedra", M, -0.25, tw + 0.25, y0 - 0.25, tw + y0 + 0.25, piso_camp - 0.4, piso_camp)
    hc, g = 5.0, 0.8
    zs_c = piso_camp + 3.0
    marcos = [
        M @ T(0, y0, 0),
        M @ T(tw, tw + y0, 0) @ Rz(180),
        M @ T(0, tw + y0, 0) @ Rz(-90),
        M @ T(tw, y0, 0) @ Rz(90),
    ]
    for Mx in marcos:
        o.muro(mat_torre, Mx, 0, tw, piso_camp, piso_camp + hc, 0, g, [(dc - 1.0, dc + 1.0, piso_camp + 0.95, zs_c + 1.0)])
        o.arco(mat_torre, Mx, dc - 1.0, dc + 1.0, zs_c, 0, g)
        o.caja("piedra", Mx, dc - 1.1, dc + 1.1, -0.12, g, piso_camp + 0.85, piso_camp + 0.95)
    techo = piso_camp + hc
    o.caja("piedra", M, -0.3, tw + 0.3, y0 - 0.3, tw + y0 + 0.3, techo, techo + 0.45)
    o.caja(mat_torre, M, 0.4, tw - 0.4, y0 + 0.4, tw + y0 - 0.4, techo + 0.45, techo + 1.3)
    cx, cy = tw / 2, tw / 2 + y0
    rc = tw / 2 - 0.55
    domo = [(rc * cos(radians(a_)), rc * sin(radians(a_))) for a_ in range(0, 91, 10)]
    o.torno(cupula, M @ T(cx, cy, techo + 1.3), [(r_, z_) for r_, z_ in reversed(domo)], 8, suave=False, giro=pi / 8)
    o.torno(mat_torre, M @ T(cx, cy, techo + 1.3 + rc), [(0.35, 0.9), (0.35, 0.0)], 8, suave=False)
    o.torno("hierro", M @ T(cx, cy, techo + 2.2 + rc), [(0.04, 1.4), (0.04, 0.0)], 6)
    o.caja("hierro", M @ T(cx, cy, 0), -0.35, 0.35, -0.04, 0.04, techo + 3.1 + rc, techo + 3.18 + rc)
    # yugo de la campana en el vano frontal
    o.caja("madera", M, dc - 1.25, dc + 1.25, y0 + 0.28, y0 + 0.52, zs_c + 0.45, zs_c + 0.7)

    pos = lambda x, y, z: tuple(M @ Vector((x, y, z)))
    rot = M.to_euler().z
    marcador(f"M_{prefijo}_portal", pos(c, -2.5, 0), rot)
    marcador(f"M_{prefijo}_puerta_torre", pos(dc, y0 - 1.6, 0), rot)
    marcador(f"M_{prefijo}_campanario", pos(dc, y0 + g + 1.5, piso_camp + 0.02), rot)
    marcador(f"M_{prefijo}_campana", pos(dc, y0 + 0.4, zs_c + 0.2), rot)


# ---------------------------------------------------------------- ciudad

def fila(nombre, a, b, adentro, segmentos=None, props=True, libre_ini=0.0, libre_fin=0.0):
    """Fachada continua de a a b (2D); 'adentro' apunta hacia el interior de la manzana.

    segmentos: lista de (ancho, funcion(o, M)) para edificios especiales; el resto se
    llena con casas de ancho variable.
    """
    a, b = Vector((*a, 0)), Vector((*b, 0))
    d = (b - a).normalized()
    izq = Vector((-d.y, d.x, 0))
    if izq.dot(Vector((*adentro, 0))) < 0:
        a, b = b, a
        d = -d
        libre_ini, libre_fin = libre_fin, libre_ini
    largo = (b - a).length
    ang = math.degrees(math.atan2(d.y, d.x))
    M0 = T(a.x, a.y) @ Rz(ang)
    o = Pieza(f"{nombre}-col")
    # libre_ini/libre_fin: tramo que ocupa el edificio de la esquina de la fila perpendicular.
    x = libre_ini
    largo -= libre_fin
    especiales = list(segmentos or [])
    while x < largo - 0.5:
        if especiales and especiales[0][0] is not None and x >= especiales[0][0] - 0.01:
            _, ancho, fn = especiales.pop(0)
            fn(o, M0 @ T(x, 0))
            x += ancho
            continue
        limite = especiales[0][0] if especiales else largo
        ancho = min(rnd.uniform(7.5, 11.5), limite - x)
        if limite - x - ancho < 5.0:
            ancho = limite - x
        casa(o, M0 @ T(x, 0), ancho, props=props, lado_izq=x <= libre_ini + 0.01,
             lado_der=x + ancho >= largo - 0.01)
        if rnd.random() < 0.45:
            CONTADOR["farol"] += 1
            p = M0 @ Vector((x + 0.25, 0.0, 3.35))
            marcador(f"P_farol_{CONTADOR['farol']:02d}", p, radians(ang))
        x += ancho
    return o.objeto()


def construir_ciudad():
    escena_vacia()
    P, C = 24.0, 31.0  # borde de la plaza y línea de fachadas del anillo

    # --- Lado norte: Catedral y Palacio Arzobispal
    def catedral(o, M):
        templo(o, M, 26.0, 34.0, 15.0, "piedra", 7.0, 17.0, "catedral", mat_torre="piedra", cupula="tejas")

    def palacio_arzobispal(o, M):
        c = casa(o, M, 22.0, alto=8.4, portal=True, corrido=True, color="revoque_blanco", pisos=2, luces=0.6, props=False, lado_der=True)
        marcador("M_arzobispo", tuple(M @ Vector((c, -4.0, 0))), M.to_euler().z)
        marcador("M_balcon_arzobispo", tuple(M @ Vector((c, -0.5, 3.97))), M.to_euler().z)

    fila("fila_norte", (-P, C), (P, C), (0, 1), [(0.0, 26.0, catedral), (26.0, 22.0, palacio_arzobispal)])

    # --- Lado este: la Universidad (hoy Casa de la Libertad)
    def universidad(o, M):
        c = casa(o, M, 24.0, alto=8.6, portal=True, corrido=False, color="revoque_blanco", pisos=2, luces=0.7, props=False)
        marcador("M_universidad", tuple(M @ Vector((c, -3.0, 0))), M.to_euler().z)

    fila("fila_este", (C, P), (C, -P), (1, 0), [(12.0, 24.0, universidad)])

    # --- Lado sur: la Real Audiencia (casa del presidente García Pizarro)
    def audiencia(o, M):
        c = casa(o, M, 28.0, alto=8.8, portal=True, corrido=True, color="revoque_blanco", pisos=2, luces=0.5, props=False)
        marcador("M_audiencia", tuple(M @ Vector((c, -4.0, 0))), M.to_euler().z)
        marcador("M_balcon_audiencia", tuple(M @ Vector((c, -0.5, 3.97))), M.to_euler().z)

    fila("fila_sur", (P, -C), (-P, -C), (0, -1), [(10.0, 28.0, audiencia)])
    fila("fila_oeste", (-C, -P), (-C, P), (-1, 0))

    # --- Calle a San Francisco (sale de la esquina noreste hacia el norte)
    largo_calle = 82.0

    def san_francisco(o, M):
        templo(o, M, 22.0, 36.0, 12.5, "revoque_blanco", 6.0, 13.0, "sanfrancisco", mat_torre="piedra_revocada")

    fila("calle_sf_este", (C, C + largo_calle), (C, C), (1, 0), [(18.0, 22.0, san_francisco)], libre_fin=12.0)
    fila("calle_sf_oeste", (P, C), (P, C + largo_calle), (-1, 0), libre_ini=12.0)
    fila("calle_sf_fondo", (P - 6, C + largo_calle + 0.5), (C + 6, C + largo_calle + 0.5), (0, 1))

    # --- Esquinas: tramos cortos de las otras calles y casas que cierran la vista
    tramo = 29.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            nom = f"{'n' if sy > 0 else 's'}{'e' if sx > 0 else 'o'}"
            # manzana de la esquina: fachada hacia la calle horizontal y hacia la vertical
            fila(f"esq_{nom}_h", (sx * C, sy * C), (sx * (C + tramo), sy * C), (0, sy))
            if not (sx > 0 and sy > 0):  # la noreste ya es la calle de San Francisco
                fila(f"esq_{nom}_v", (sx * C, sy * C), (sx * C, sy * (C + tramo)), (sx, 0), libre_ini=12.0)
            # manzanas de la plaza: sus costados hacia las calles que salen
            if not (sx > 0 and sy > 0):
                fila(f"lat_{nom}_v", (sx * P, sy * C), (sx * P, sy * (C + tramo)), (-sx, 0), libre_ini=12.0)
            fila(f"lat_{nom}_h", (sx * C, sy * P), (sx * (C + tramo), sy * P), (0, -sy), libre_ini=12.0)
            # cierres al fondo de cada calle
            if not (sx > 0 and sy > 0):
                fila(f"cierre_{nom}_v", (sx * (P - 6), sy * (C + tramo + 0.5)), (sx * (C + 6), sy * (C + tramo + 0.5)), (0, sy))
            fila(f"cierre_{nom}_h", (sx * (C + tramo + 0.5), sy * (P - 6)), (sx * (C + tramo + 0.5), sy * (C + 6)), (sx, 0))

    # --- Suelo en baldosas de 24 m (la luz de las antorchas se reparte mejor por pieza)
    k = 0
    for x0 in range(-72, 72, 48):
        for y0 in range(-72, 168, 48):
            dentro = -P <= x0 and x0 + 48 <= P and -P <= y0 and y0 + 48 <= P
            o = Pieza(f"suelo_{k:02d}-col")
            o.caja("plaza" if dentro else "empedrado", Matrix(), x0, x0 + 48, y0, y0 + 48, -0.3, 0.0)
            o.objeto()
            k += 1
    # borde de piedra de la plaza
    o = Pieza("borde_plaza")
    for lado in range(4):
        M = Rz(90 * lado)
        o.caja("losa", M, -P, P, -P - 0.3, -P + 0.3, 0.0, 0.03)
    o.objeto()

    # --- Pila (fuente) en el centro de la plaza
    o = Pieza("pila-col")
    I = Matrix()
    o.torno("piedra", I, [(2.3, 0.75), (2.7, 0.75), (2.75, 0.68), (2.75, 0.0), (2.3, 0.0)], 8, cerrado=True, suave=False, giro=pi / 8)
    o.torno("piedra", I, [(2.32, 0.3), (2.32, 0.0)], 8, suave=False, giro=pi / 8)
    o.torno("agua", I, [(2.3, 0.58), (2.3, 0.52)], 8, suave=False, giro=pi / 8)
    o.torno("piedra", I, [(0.5, 0.75), (0.3, 1.0), (0.26, 1.9), (0.4, 2.0), (0.4, 0.3)], 8, suave=True)
    o.torno("piedra", I, [(0.15, 2.0), (0.9, 2.2), (0.95, 2.35), (0.8, 2.35), (0.15, 2.15)], 8, cerrado=True, suave=True)
    o.torno("piedra", I, [(0.02, 2.95), (0.2, 2.75), (0.12, 2.5), (0.2, 2.35), (0.02, 2.3)], 8, suave=True)
    o.objeto()
    for i, ang in enumerate((45, 135, 225, 315)):
        p = Rz(ang) @ Vector((7.5, 0, 0))
        marcador(f"P_banca_{i + 1:02d}", tuple(p), radians(ang + 90))

    # --- Terreno lejano y cerros (Churuquella y Sica Sica al fondo)
    o = Pieza("terreno")
    disco = o.bm.faces.new([o.bm.verts.new((600 * cos(2 * pi * k / 48), 600 * sin(2 * pi * k / 48), -0.35)) for k in range(48)])
    disco.normal_update()
    if disco.normal.z < 0:
        disco.normal_flip()
    o._cerrar([disco], Matrix(), "cerro")
    seg = 144

    def alt(a, f=1.0):
        este = max(0.0, cos(a)) ** 2  # Churuquella y Sica Sica, al este
        return f * (18 + 34 * este + 11 * sin(3 * a + 1.3) + 7 * sin(7 * a + 0.4) + 5 * sin(13 * a + 2.1) + 3 * sin(29 * a + 0.7))

    radios = [(330.0, lambda a: -0.3), (385.0, lambda a: alt(a + 0.07, 0.55)), (430.0, lambda a: alt(a)),
              (480.0, lambda a: alt(a - 0.05, 0.75)), (560.0, lambda a: -0.3)]
    for k in range(seg):
        a0, a1 = 2 * pi * k / seg, 2 * pi * (k + 1) / seg
        anillo = []
        for a in (a0, a1):
            anillo.append([Vector((r * cos(a), r * sin(a), fz(a))) for r, fz in radios])
        bm = o.bm
        vs = [[bm.verts.new(v) for v in fila_] for fila_ in anillo]
        caras = [bm.faces.new((vs[0][i], vs[1][i], vs[1][i + 1], vs[0][i + 1])) for i in range(len(radios) - 1)]
        for f in caras:
            f.normal_update()
            if f.normal.z < 0:
                f.normal_flip()
        o._cerrar(caras, Matrix(), "cerro", suave=True)
    o.objeto()

    # --- Recorrido de la escolta que lleva preso a Zudáñez
    ruta = [(27.5, 92.0), (27.5, 60.0), (27.5, 34.0), (21.0, 18.0), (12.0, 0.0), (4.0, -14.0), (2.0, -24.5)]
    for i, (x, y) in enumerate(ruta):
        marcador(f"R_escolta_{i}", (x, y, 0.0))
    marcador("M_lemoine", (8.0, -18.0, 0.0))

    exportar(SALIDA / "ciudad_1809.glb", todo=True)


# ---------------------------------------------------------------- objetos sueltos

def exportar(ruta, todo=False, nombres=None):
    for ob in bpy.context.scene.objects:
        ob.select_set(todo or (nombres is not None and ob.name in nombres))
    bpy.ops.export_scene.gltf(
        filepath=str(ruta),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
    )
    print(f"[exportado] {ruta.name}")


def construir_campana():
    escena_vacia()
    o = Pieza("campana")
    I = Matrix()
    perfil = [(0.05, -0.2), (0.24, -0.24), (0.31, -0.36), (0.33, -0.6), (0.37, -0.88), (0.46, -1.12),
              (0.58, -1.3), (0.62, -1.36), (0.55, -1.37), (0.45, -1.22), (0.31, -0.92), (0.27, -0.55),
              (0.2, -0.32), (0.05, -0.3)]
    o.torno("bronce", I, perfil, 32, cerrado=True, suave=True)
    o.caja("bronce", I, -0.12, 0.12, -0.05, 0.05, -0.24, -0.06)
    o.caja("madera", I, -0.45, 0.45, -0.16, 0.16, -0.12, 0.22)
    o.torno("hierro", I @ Matrix.Rotation(pi / 2, 4, "Y"), [(0.035, 0.5), (0.035, -0.5)], 8)
    o.objeto()
    b = Pieza("badajo")
    b.torno("hierro", I, [(0.025, 0.0), (0.025, -0.7)], 8)
    b.torno("hierro", I, [(0.02, -0.66), (0.08, -0.74), (0.09, -0.83), (0.05, -0.92), (0.02, -0.95)], 12)
    ob = b.objeto()
    ob.location = (0, 0, -0.3)
    exportar(SALIDA / "campana.glb", todo=True)


def construir_farol():
    escena_vacia()
    o = Pieza("farol")
    I = Matrix()
    o.caja("hierro", I, -0.03, 0.03, -0.62, 0.0, -0.03, 0.03)
    o.prisma("hierro", I, [(0.0, -0.35), (-0.03, -0.35), (-0.45, 0.0), (-0.42, 0.0)], "x", -0.015, 0.015)
    o.caja("hierro", I, -0.08, 0.08, -0.06, 0.0, -0.45, 0.06)
    cx, cy = 0.0, -0.62
    o.caja("hierro", I, cx - 0.17, cx + 0.17, cy - 0.17, cy + 0.17, -0.5, -0.46)
    for sx in (-1, 1):
        for sy in (-1, 1):
            o.caja("hierro", I, cx + sx * 0.15 - 0.012, cx + sx * 0.15 + 0.012, cy + sy * 0.15 - 0.012, cy + sy * 0.15 + 0.012, -0.46, -0.06)
    o.caja("vidrio_farol", I, cx - 0.14, cx + 0.14, cy - 0.14, cy + 0.14, -0.46, -0.08)
    o.torno("hierro", I @ T(cx, cy, -0.08), [(0.03, 0.2), (0.24, 0.0), (0.2, -0.03)], 4, suave=False, giro=pi / 4)
    o.torno("hierro", I @ T(cx, cy, 0.0), [(0.03, 0.12), (0.03, 0.0)], 6)
    o.torno("cera", I @ T(cx, cy, -0.46), [(0.03, 0.14), (0.03, 0.0)], 8)
    o.objeto()
    marcador("luz", (cx, cy, -0.28))
    exportar(SALIDA / "farol.glb", todo=True)


def construir_barril():
    escena_vacia()
    o = Pieza("barril")
    I = Matrix()
    perfil = [(0.27, 0.86), (0.31, 0.72), (0.335, 0.43), (0.31, 0.14), (0.27, 0.0)]
    o.torno("madera", I, perfil, 16, suave=False)
    for z, r in ((0.1, 0.3), (0.24, 0.322), (0.62, 0.322), (0.76, 0.3)):
        o.torno("hierro", I, [(r + 0.012, z + 0.03), (r + 0.012, z - 0.03), (r - 0.01, z - 0.03), (r - 0.01, z + 0.03)], 16, cerrado=True, suave=False)
    o.objeto()
    exportar(SALIDA / "barril.glb", todo=True)


def construir_antorcha():
    escena_vacia()
    o = Pieza("antorcha")
    I = Matrix()
    o.torno("madera", I, [(0.022, 0.95), (0.026, 0.0)], 8)
    o.torno("tela", I, [(0.02, 1.08), (0.05, 1.04), (0.055, 0.95), (0.045, 0.88), (0.025, 0.86)], 8)
    o.objeto()
    marcador("fuego", (0, 0, 1.12))
    exportar(SALIDA / "antorcha.glb", todo=True)


if __name__ == "__main__":
    construir_ciudad()
    construir_campana()
    construir_farol()
    construir_barril()
    construir_antorcha()
    print("[listo] modelos en", SALIDA)
