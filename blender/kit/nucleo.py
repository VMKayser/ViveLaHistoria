"""Construcción de geometría: un Constructor acumula piezas por material y crea UN objeto por edificio.

Unidades: metros. Ejes del lienzo: X este, Y norte, Z arriba (coordenadas absolutas del mapa).
Una Fachada da un sistema local sobre un lado de la huella:
    s = distancia a lo largo del lado (0 .. largo, de a hacia b)
    h = altura sobre el suelo de esa fachada
    d = salida hacia la calle (positivo = hacia afuera del muro, negativo = hacia adentro)
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import paleta


class Constructor:
    def __init__(self, nombre):
        self.nombre = nombre
        self.bm = bmesh.new()
        self.mats = []

    # --- materiales -------------------------------------------------------
    def _idx(self, rol, color=None):
        nombre = paleta.nombre_material(rol, color)
        if nombre not in self.mats:
            self.mats.append(nombre)
        return self.mats.index(nombre)

    def _pintar(self, verts, rol, color):
        k = self._idx(rol, color)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = k

    # --- primitivas -------------------------------------------------------
    def caja_ejes(self, centro, ex, ey, ez, sx, sy, sz, rol, color=None):
        """Caja de medidas (sx, sy, sz) en los ejes unitarios ex, ey, ez."""
        m = Matrix((
            (ex[0] * sx, ey[0] * sy, ez[0] * sz, centro[0]),
            (ex[1] * sx, ey[1] * sy, ez[1] * sz, centro[1]),
            (ex[2] * sx, ey[2] * sy, ez[2] * sz, centro[2]),
            (0, 0, 0, 1),
        ))
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self._pintar(r["verts"], rol, color)
        return r["verts"]

    def caja(self, x0, y0, z0, x1, y1, z1, rol, color=None):
        c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        return self.caja_ejes(c, (1, 0, 0), (0, 1, 0), (0, 0, 1), abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), rol, color)

    def cilindro(self, x, y, z0, z1, radio, rol, color=None, lados=8, radio_arriba=None):
        m = Matrix.Translation((x, y, (z0 + z1) / 2))
        r = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=lados, radius1=radio,
                                  radius2=radio if radio_arriba is None else radio_arriba,
                                  depth=z1 - z0, matrix=m)
        self._pintar(r["verts"], rol, color)
        return r["verts"]

    def esfera(self, x, y, z, radio, rol, color=None, segmentos=10):
        r = bmesh.ops.create_uvsphere(self.bm, u_segments=segmentos, v_segments=max(4, segmentos // 2),
                                      radius=radio, matrix=Matrix.Translation((x, y, z)))
        self._pintar(r["verts"], rol, color)
        return r["verts"]

    def prisma(self, huella, z0, z1, rol, color=None, tapa=True, piso=False):
        """Extruye una huella (lista de (x, y)) entre z0 y z1. Huellas cóncavas OK."""
        h = _ccw(huella)
        abajo = [self.bm.verts.new((x, y, z0)) for x, y in h]
        arriba = [self.bm.verts.new((x, y, z1)) for x, y in h]
        k = self._idx(rol, color)
        n = len(h)
        for i in range(n):
            f = self.bm.faces.new((abajo[i], abajo[(i + 1) % n], arriba[(i + 1) % n], arriba[i]))
            f.material_index = k
        if tapa:
            f = self.bm.faces.new(arriba)
            f.material_index = k
            self._triangular(f)
        if piso:
            f = self.bm.faces.new(list(reversed(abajo)))
            f.material_index = k
            self._triangular(f)
        return arriba

    def tapa(self, huella, z, rol, color=None):
        """Cara horizontal (techo plano, suelo de patio) con la forma de la huella."""
        vs = [self.bm.verts.new((x, y, z)) for x, y in _ccw(huella)]
        f = self.bm.faces.new(vs)
        f.material_index = self._idx(rol, color)
        self._triangular(f)

    def poligono(self, puntos3d, rol, color=None, grosor=0.0, normal_extrusion=None):
        """Polígono plano en 3D; con grosor > 0 se extruye (p. ej. frontón, hastial, arco macizo)."""
        vs = [self.bm.verts.new(p) for p in puntos3d]
        f = self.bm.faces.new(vs)
        f.material_index = self._idx(rol, color)
        if grosor:
            f.normal_update()
            n = Vector(normal_extrusion) if normal_extrusion else f.normal
            r = bmesh.ops.extrude_face_region(self.bm, geom=[f])
            nuevos = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
            bmesh.ops.translate(self.bm, vec=n.normalized() * grosor, verts=nuevos)
        return vs

    def _triangular(self, cara):
        bmesh.ops.triangulate(self.bm, faces=[cara], quad_method="BEAUTY", ngon_method="EAR_CLIP")

    # --- salida -----------------------------------------------------------
    def objeto(self, coleccion=None, biselar=0.0, huella=None):
        """Crea el objeto de Blender (un objeto, varios materiales). biselar: chaflán en m (0.02–0.05) para bordes suaves.
        huella: polígono del edificio; si se da, al exportar se recorta a sus medianeras (kit/medianeras.py)."""
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=0.0005)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(self.nombre)
        self.bm.to_mesh(me)
        self.bm.free()
        for nombre in self.mats:
            rol, _, color = nombre.partition("__")
            me.materials.append(paleta.material(rol, "#" + color if color else None))
        ob = bpy.data.objects.new(self.nombre, me)
        huella = huella or getattr(self, "huella", None)
        if huella:
            import json as _json
            ob["huella"] = _json.dumps([[round(p[0], 3), round(p[1], 3)] for p in huella])
        (coleccion or bpy.context.scene.collection).objects.link(ob)
        if biselar > 0:
            mod = ob.modifiers.new("bisel", "BEVEL")
            mod.width = biselar
            mod.segments = 1
            mod.limit_method = "ANGLE"
            mod.angle_limit = math.radians(40)
            mod.harden_normals = False
        for p in me.polygons:
            p.use_smooth = False
        return ob


def _ccw(huella):
    h = [tuple(p[:2]) for p in huella]
    if len(h) > 2 and h[0] == h[-1]:
        h = h[:-1]
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(h, h[1:] + h[:1]))
    return h if area > 0 else list(reversed(h))


class Fachada:
    """Sistema local sobre un lado de la huella (ver docstring del módulo)."""

    def __init__(self, c, lado, suelo):
        """c: Constructor. lado: un elemento de datos.lados(). suelo: altura del terreno al pie de esta fachada."""
        self.c = c
        self.a = Vector((*lado["a"], 0))
        b = Vector((*lado["b"], 0))
        self.largo = (b - self.a).length
        self.u = (b - self.a).normalized()
        self.n = Vector((*lado["normal"], 0))
        self.z = Vector((0, 0, 1))
        self.suelo = suelo

    def punto(self, s, h, d=0.0):
        p = self.a + self.u * s + self.n * d
        return Vector((p.x, p.y, self.suelo + h))

    def caja(self, s0, s1, h0, h1, d0, d1, rol, color=None):
        """Caja alineada con la fachada: s0..s1 a lo largo, h0..h1 de alto, d0..d1 de salida."""
        c = self.punto((s0 + s1) / 2, (h0 + h1) / 2, (d0 + d1) / 2)
        return self.c.caja_ejes(c, self.u, self.n, self.z, abs(s1 - s0), abs(d1 - d0), abs(h1 - h0), rol, color)

    def cilindro_vertical(self, s, h0, h1, d, radio, rol, color=None, lados=6):
        p = self.punto(s, 0, d)
        return self.c.cilindro(p.x, p.y, self.suelo + h0, self.suelo + h1, radio, rol, color, lados)

    def esfera(self, s, h, d, radio, rol, color=None):
        p = self.punto(s, h, d)
        return self.c.esfera(p.x, p.y, p.z, radio, rol, color)

    def arco(self, s_centro, radio_int, grosor, h_arranque, d0, d1, rol, color=None, segmentos=10, medio=True):
        """Rosca de un arco (medio punto) como dovelas: de s_centro-radio a s_centro+radio, arrancando en h_arranque."""
        tramos = segmentos if medio else segmentos * 2
        ang_total = math.pi if medio else 2 * math.pi
        for k in range(tramos):
            a0 = k * ang_total / tramos
            a1 = (k + 1) * ang_total / tramos
            am = (a0 + a1) / 2
            r = radio_int + grosor / 2
            s = s_centro - math.cos(am) * r
            h = h_arranque + math.sin(am) * r
            largo = 2 * (radio_int + grosor) * math.sin((a1 - a0) / 2) + 0.01
            # dovela orientada tangente al arco
            # tangente (sin, cos) y radial (-cos, sin) en coordenadas (s, h)
            eje_s = self.u * math.sin(am) + self.z * math.cos(am)
            eje_s.normalize()
            eje_h = self.u * (-math.cos(am)) + self.z * math.sin(am)
            c = self.punto(s, h, (d0 + d1) / 2)
            self.c.caja_ejes(c, eje_s, self.n, eje_h, largo, abs(d1 - d0), grosor, rol, color)

    def timpano_arco(self, s_centro, radio, h_arranque, d, rol, color=None, segmentos=10):
        """Relleno semicircular plano (p. ej. vidrio o madera de la parte alta de una ventana/puerta en arco)."""
        pts = []
        for k in range(segmentos + 1):
            a = math.pi * k / segmentos
            pts.append(self.punto(s_centro - math.cos(a) * radio, h_arranque + math.sin(a) * radio, d))
        pts.reverse()
        return self.c.poligono(pts, rol, color)
