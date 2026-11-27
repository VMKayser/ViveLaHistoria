"""Mobiliario de vereda de claude (frente a SUS manzanas y en los espacios sin dueño), visto en las fotos:

- postes de hormigón de ~9 m junto al bordillo, con cruceta, aisladores y a veces transformador;
- MUCHOS cables negros entre postes (de 6 a 10 por vano, con flecha), cruces de calle y acometidas a las fachadas;
- farol de brazo curvo en los postes (pescante con campana);
- semáforos amarillos en los cruces de calles principales.

Todo determinista (semilla = nombre de la calle + posición).
"""

import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit import Constructor, altura_suelo  # noqa: E402
from kit.datos import RAIZ, reparto  # noqa: E402

from base_suelo import ALTO_VEREDA, SOBRE_TERRENO, _en_calzada, _en_corredor, _punto_en  # noqa: E402

COLOR_POSTE = "#b4afa6"
COLOR_CABLE = "#2b2522"
COLOR_SEMAFORO = "#e3b52f"


# --------------------------------------------------------------------------- dueño de cada punto de vereda

_huellas = None


def _dentro(px, py, pts):
    r = False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 > py) != (y1 > py) and px < x0 + (py - y0) * (x1 - x0) / (y1 - y0):
            r = not r
    return r


def _dist_poly(px, py, pts):
    m = 1e9
    for a, b in zip(pts, pts[1:] + pts[:1]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        l2 = dx * dx + dy * dy or 1e-9
        t = max(0, min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / l2))
        m = min(m, math.hypot(px - a[0] - t * dx, py - a[1] - t * dy))
    return m


def dueno_en(x, y, radio=9.0):
    """Dueño de la manzana más cercana (≤ radio m); 'claude' si no hay ninguna (espacio sin dueño → BASE)."""
    global _huellas
    if _huellas is None:
        hm = json.load(open(os.path.join(RAIZ, "web", "public", "mapa", "huellas_manzanas.json")))
        duenos = {m["id"]: m["dueno"] for m in reparto()["manzanas"]}
        _huellas = [(duenos.get(mid), [tuple(p) for p in poly]) for mid, polys in hm.items() for poly in polys]
        for e in reparto().get("espacios", []):
            if e.get("poligono"):
                _huellas.append((e["dueno"], [tuple(p) for p in e["poligono"]]))
    mejor = (radio, "claude")
    for d, poly in _huellas:
        if _dentro(x, y, poly):
            return d
        dd = _dist_poly(x, y, poly)
        if dd < mejor[0]:
            mejor = (dd, d)
    return mejor[1]


_propios = None


def mobiliario_propio_en(x, y, radio=9.0):
    """True si (x, y) es la vereda de un espacio con `mobiliario_propio` en el reparto (p. ej. SAN_MIGUEL): ese espacio
    coloca a mano, según las fotos, sus faroles y postes; la BASE no pone los suyos (ni dentro ni a ≤ radio m)."""
    global _propios
    if _propios is None:
        _propios = [[tuple(p) for p in e["poligono"]] for e in reparto().get("espacios", [])
                    if e.get("mobiliario_propio") and e.get("poligono")]
    return any(_dentro(x, y, poly) or _dist_poly(x, y, poly) < radio for poly in _propios)


# --------------------------------------------------------------------------- piezas

def tubo(c, p0, p1, radio, rol, color=None):
    """Barra fina de sección cuadrada entre dos puntos 3D."""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    L = math.sqrt(dx * dx + dy * dy + dz * dz)
    if L < 1e-4:
        return
    ex = (dx / L, dy / L, dz / L)
    ref = (0, 0, 1) if abs(ex[2]) < 0.9 else (1, 0, 0)
    ey = (ex[1] * ref[2] - ex[2] * ref[1], ex[2] * ref[0] - ex[0] * ref[2], ex[0] * ref[1] - ex[1] * ref[0])
    n = math.sqrt(sum(v * v for v in ey))
    ey = tuple(v / n for v in ey)
    ez = (ex[1] * ey[2] - ex[2] * ey[1], ex[2] * ey[0] - ex[0] * ey[2], ex[0] * ey[1] - ex[1] * ey[0])
    centro = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2)
    c.caja_ejes(centro, ex, ey, ez, L, radio * 2, radio * 2, rol, color)


def cable(c, p0, p1, flecha, radio=0.018, segmentos=7):
    """Cable colgado (parábola) entre dos puntos: tubo continuo de sección triangular (6 triángulos por tramo)."""
    pts = []
    for k in range(segmentos + 1):
        t = k / segmentos
        pts.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t,
                    p0[2] + (p1[2] - p0[2]) * t - 4 * flecha * t * (1 - t)))
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    lat = (-dy / L, dx / L, 0.0)                 # horizontal, perpendicular al cable
    anillos = []
    for x, y, z in pts:
        anillo = []
        for k in range(3):
            a = 2 * math.pi * k / 3 + math.pi / 2
            u, w = math.cos(a) * radio, math.sin(a) * radio
            anillo.append((x + lat[0] * u, y + lat[1] * u, z + w))
        anillos.append(anillo)
    for r0, r1 in zip(anillos, anillos[1:]):
        for k in range(3):
            c.poligono([r0[k], r0[(k + 1) % 3], r1[(k + 1) % 3], r1[k]], "hierro", COLOR_CABLE)


class Poste:
    """Poste de hormigón junto al bordillo. (x, y) en la vereda; (nx, ny) apunta hacia la calzada."""

    def __init__(self, x, y, nx, ny, tx, ty, rnd):
        self.x, self.y, self.nx, self.ny, self.tx, self.ty = x, y, nx, ny, tx, ty
        self.z = altura_suelo(x, y) + SOBRE_TERRENO + ALTO_VEREDA
        self.alto = rnd.uniform(8.6, 9.6)
        self.transformador = rnd.random() < 0.3
        self.rnd = rnd

    def anclajes(self, n):
        """n puntos de amarre de cables: en la cruceta (arriba) y en abrazaderas más abajo, repartidos a lo ancho."""
        r = []
        for k in range(n):
            h = self.alto - 0.45 - (k % 4) * 0.55 - (0.25 if k >= 4 else 0)
            lat = ((k % 3) - 1) * 0.55 if h > self.alto - 1.0 else ((k % 2) - 0.5) * 0.25
            r.append((self.x + self.nx * lat, self.y + self.ny * lat, self.z + h))
        return r

    def construir(self, c):
        x, y, z, A = self.x, self.y, self.z, self.alto
        c.cilindro(x, y, z - 0.3, z + A, 0.15, "piedra", COLOR_POSTE, lados=8, radio_arriba=0.09)
        # cruceta perpendicular a la calle, con aisladores
        hc = z + A - 0.35
        tubo(c, (x - self.nx * 0.9, y - self.ny * 0.9, hc), (x + self.nx * 0.9, y + self.ny * 0.9, hc), 0.05, "piedra", COLOR_POSTE)
        for u in (-0.75, 0.0, 0.75):
            c.cilindro(x + self.nx * u, y + self.ny * u, hc + 0.05, hc + 0.22, 0.04, "metal", lados=5)
        # abrazaderas y rollos de cable (los postes de Sucre llevan mucho cable enrollado)
        for h in (A - 1.4, A - 2.1):
            c.cilindro(x, y, z + h - 0.06, z + h + 0.06, 0.19, "hierro", COLOR_CABLE, lados=8)
        if self.rnd.random() < 0.5:
            c.cilindro(x + self.tx * 0.25, y + self.ty * 0.25, z + A - 3.3, z + A - 2.7, 0.22, "hierro", COLOR_CABLE, lados=8)
        if self.transformador:
            ox, oy = x - self.nx * 0.45, y - self.ny * 0.45
            c.cilindro(ox, oy, z + A - 3.4, z + A - 2.4, 0.32, "metal", "#8e918c", lados=8)
            c.cilindro(ox, oy, z + A - 2.4, z + A - 2.32, 0.34, "metal", "#7d807b", lados=8)
        # farol de brazo curvo hacia la calzada
        hb = z + A - 1.7
        prev = (x, y, hb)
        for k in range(1, 6):
            a = k / 5
            s = 1.5 * math.sin(a * math.pi / 2)
            h = hb + 0.55 * math.sin(a * math.pi)
            p = (x + self.nx * s, y + self.ny * s, h)
            tubo(c, prev, p, 0.035, "hierro")
            prev = p
        lx, ly, lz = prev
        c.cilindro(lx, ly, lz - 0.32, lz - 0.02, 0.24, "hierro", lados=8, radio_arriba=0.06)
        c.cilindro(lx, ly, lz - 0.36, lz - 0.30, 0.2, "vidrio", "#e9dfb8", lados=8)


def farol_ornamental(c, x, y, nx, ny):
    """Farol de poste metálico oscuro (Ravelo, foto 125838): fuste con basa, brazo curvo hacia la calzada con campana
    y remate de bola de terracota arriba. (nx, ny) apunta hacia la calzada."""
    z = altura_suelo(x, y) + SOBRE_TERRENO + ALTO_VEREDA
    c.cilindro(x, y, z, z + 0.6, 0.16, "hierro", "#2f2b28", lados=8, radio_arriba=0.1)
    c.cilindro(x, y, z + 0.6, z + 6.2, 0.075, "hierro", "#2f2b28", lados=8, radio_arriba=0.06)
    c.esfera(x, y, z + 6.4, 0.2, "pintura_acento", "#b5523a", segmentos=8)
    c.cilindro(x, y, z + 6.2, z + 6.25, 0.1, "hierro", "#2f2b28", lados=8)
    prev = (x, y, z + 5.6)
    for k in range(1, 6):
        a = k / 5
        s = 1.3 * math.sin(a * math.pi / 2)
        h = z + 5.6 + 0.5 * math.sin(a * math.pi)
        p = (x + nx * s, y + ny * s, h)
        tubo(c, prev, p, 0.03, "hierro", "#2f2b28")
        prev = p
    lx, ly, lz = prev
    c.cilindro(lx, ly, lz - 0.45, lz - 0.05, 0.2, "hierro", "#2f2b28", lados=8, radio_arriba=0.05)
    c.cilindro(lx, ly, lz - 0.55, lz - 0.42, 0.17, "vidrio", "#efe2b5", lados=8)


def semaforo(c, x, y, nx, ny, tx, ty):
    """Semáforo de poste amarillo; la caja mira hacia la calle que llega (−t)."""
    z = altura_suelo(x, y) + SOBRE_TERRENO + ALTO_VEREDA
    c.cilindro(x, y, z, z + 3.4, 0.07, "pintura_acento", COLOR_SEMAFORO, lados=8)
    cx, cy = x - tx * 0.2, y - ty * 0.2
    ex, ey = (-tx, -ty, 0), (nx, ny, 0)
    c.caja_ejes((cx, cy, z + 3.0), ex, ey, (0, 0, 1), 0.28, 0.34, 1.0, "hierro", "#2f3a33")
    for k, col in enumerate(("#c9483a", "#d6a23a", "#4f9a5a")):
        c.esfera(cx - tx * 0.15, cy - ty * 0.15, z + 3.32 - k * 0.32, 0.09, "pintura_acento", col)


# --------------------------------------------------------------------------- colocación

PRINCIPALES = {"Calle Capitán Agustín Ravelo", "Calle Batalla de Junín", "Calle Aniceto Arce",
               "Calle José Álvarez de Arenales", "Calle Fray José Antonio de San Alberto"}


# --------------------------------------------------------------------------- coherencia (pedido del usuario 2026-11-12)
# "cables que cruzan paredes o que terminan en lugares sin sentido": todo cable se comprueba con rayos contra la
# geometría ya modelada (GLB de los dos agentes + relleno y plazas de la BASE). Un vano que atraviesa algo no se
# tiende; una acometida termina EXACTAMENTE en el muro que encuentra (con su aislador), o no se pone.
_BVH = None


def fijar_obstaculos(bvh):
    global _BVH
    _BVH = bvh


def _libre(p0, p1, flecha=0.0, tramos=8, margen=0.15):
    if _BVH is None:
        return True
    from mathutils import Vector
    prev = Vector(p0)
    for k in range(1, tramos + 1):
        t = k / tramos
        q = Vector((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t,
                    p0[2] + (p1[2] - p0[2]) * t - 4 * flecha * t * (1 - t)))
        d = q - prev
        L = d.length
        if L > 1e-6:
            o = prev + d.normalized() * (margen if k == 1 else 0.0)
            largo = L - (margen if k == 1 else 0.0) - (margen if k == tramos else 0.0)
            if largo > 0 and _BVH.ray_cast(o, d.normalized(), largo)[0] is not None:
                return False
        prev = q
    return True


def _hasta_muro(p0, objetivo, extra=2.5):
    """Punto del muro que encuentra un rayo desde p0 hacia 'objetivo' (o None si no hay muro razonablemente cerca)."""
    if _BVH is None:
        return objetivo
    from mathutils import Vector
    a, b = Vector(p0), Vector(objetivo)
    d = b - a
    L = d.length
    hit = _BVH.ray_cast(a + d.normalized() * 0.3, d.normalized(), L + extra)
    if hit[0] is None:
        return None
    # el muro debe estar más o menos donde se esperaba la fachada (no un balcón a mitad de camino)
    if hit[3] + 0.3 < L * 0.6:
        return None
    q = hit[0] - d.normalized() * 0.04
    return (q.x, q.y, q.z)


DIST_MIN_MURO = 1.4      # un poste nunca a menos de esto de una pared (pedido del usuario 2026-11-18)
DIST_BORDILLO = 0.4      # del borde de la calzada hacia la vereda


def _dist_muro(x, y, z, nx, ny, maximo=6.0):
    """Distancia de (x, y) a la pared más cercana hacia (nx, ny) (hacia afuera de la calzada), a 1,2 m de altura; None si no hay."""
    if _BVH is None:
        return None
    from mathutils import Vector
    h = _BVH.ray_cast(Vector((x, y, z + 1.2)), Vector((nx, ny, 0.0)).normalized(), maximo)
    return None if h[0] is None else h[3]


def _lugar_poste(C, x0, y0, tx, ty, nx, ny, o_, z0):
    """Lugar del poste en la vereda: a DIST_BORDILLO del bordillo y a más de DIST_MIN_MURO de cualquier pared; si la vereda
    es demasiado angosta para las dos cosas, no hay poste (None)."""
    for d_extra in (DIST_BORDILLO, 0.3):
        d = C.c + d_extra
        x, y = x0 - ty * o_ + nx * d, y0 + tx * o_ + ny * d
        dw = _dist_muro(x, y, z0, nx, ny)
        if dw is None or dw >= DIST_MIN_MURO:
            return x, y
    return None


def _poste_libre(x, y, z):
    if _BVH is None:
        return True
    from mathutils import Vector
    for h in (1.0, 3.5, 6.0):
        n = _BVH.find_nearest(Vector((x, y, z + h)), 0.6)
        if n[0] is not None:
            return False
    return True


def construir_mobiliario(col, cs, agente="claude", dentro=None):
    postes_c = Constructor("BASE_postes")
    cables_c = Constructor("BASE_cables")
    semaf_c = Constructor("BASE_semaforos")
    todos = []
    for C in cs:
        for sg in (1, -1):
            rnd = random.Random(f"{C.nombre}{sg}")
            fila = []
            L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(C.eje, C.eje[1:]))
            s = rnd.uniform(4, 16) + (0 if sg > 0 else 13)
            while s < L:
                p = _punto_en(C, s)
                x0, y0, tx, ty = p
                nx, ny = -ty * sg, tx * sg                 # hacia afuera (vereda)
                d = C.c + DIST_BORDILLO
                o_ = getattr(C, "off", 0.0)
                lugar = _lugar_poste(C, x0, y0, tx, ty, nx, ny, o_, altura_suelo(x0, y0))
                x, y = lugar if lugar else (x0 - ty * o_ + nx * d, y0 + tx * o_ + ny * d)
                ok = lugar is not None and (dentro is None or dentro(x, y)) and not _en_calzada(cs, x, y, C) \
                    and not _en_corredor(cs, x + tx * 3, y + ty * 3, C) and not _en_corredor(cs, x - tx * 3, y - ty * 3, C)
                if ok and dueno_en(x, y) == agente and not mobiliario_propio_en(x, y) and \
                        _poste_libre(x, y, altura_suelo(x, y)):
                    po = Poste(x, y, -nx, -ny, tx, ty, random.Random(f"{C.nombre}{sg}{int(s)}"))
                    po.construir(postes_c)
                    fila.append(po)
                    todos.append((C, sg, po))
                    # entre poste y poste, en las calles principales, un farol ornamental
                    if C.nombre in PRINCIPALES and not getattr(C, "peatonal", False):
                        pm = _punto_en(C, s + 13)
                        if pm:
                            lug_m = _lugar_poste(C, pm[0], pm[1], pm[2], pm[3], nx, ny, o_, altura_suelo(pm[0], pm[1]))
                            xm, ym = lug_m if lug_m else (pm[0] + nx * d, pm[1] + ny * d)
                            if lug_m is not None and (dentro is None or dentro(xm, ym)) and not _en_corredor(cs, xm, ym, C) \
                                    and dueno_en(xm, ym) == agente and not mobiliario_propio_en(xm, ym) \
                                    and _poste_libre(xm, ym, altura_suelo(xm, ym)):
                                farol_ornamental(postes_c, xm, ym, -nx, -ny)
                else:
                    fila.append(None)
                s += rnd.uniform(24, 32)
            # cables entre postes consecutivos de la misma vereda
            for a, b in zip(fila, fila[1:]):
                if not a or not b:
                    continue
                n = rnd.randint(6, 10)
                for pa, pb in zip(a.anclajes(n), b.anclajes(n)):
                    fl = rnd.uniform(0.35, 0.95)
                    if _libre(pa, pb, fl):
                        cable(cables_c, pa, pb, fl)
            # acometidas: de cada poste a la fachada de enfrente y a la propia
            for po in fila:
                if not po:
                    continue
                for k in range(rnd.randint(1, 3)):
                    lado = -1 if k % 2 == 0 else 1
                    dist = 2 * C.w - 0.7 if lado < 0 else C.v - 0.2
                    off = rnd.uniform(-4, 4)
                    fx = po.x + po.nx * dist * (1 if lado < 0 else -1) + po.tx * off
                    fy = po.y + po.ny * dist * (1 if lado < 0 else -1) + po.ty * off
                    if dentro is not None and not dentro(fx, fy):
                        continue
                    fz = altura_suelo(fx, fy) + rnd.uniform(4.8, 6.0)
                    pa = po.anclajes(6)[3 + k % 3]
                    q = _hasta_muro(pa, (fx, fy, fz))
                    fl = rnd.uniform(0.25, 0.6)
                    if q is None or not _libre(pa, q, fl, margen=0.25):
                        continue
                    cable(cables_c, pa, q, fl, radio=0.013, segmentos=5)
                    # grampa y aislador donde el cable llega a la fachada
                    cables_c.cilindro(q[0], q[1], q[2] - 0.05, q[2] + 0.05, 0.04, "moldura", "#e8e4dc", lados=6)
    # cruces de calle: del poste a otro poste del otro lado, si hay uno cerca
    for C, sg, po in todos:
        rnd = random.Random(f"x{po.x:.1f}{po.y:.1f}")
        if rnd.random() > 0.45:
            continue
        otros = [q for (C2, sg2, q) in todos if C2 is C and sg2 != sg and math.hypot(q.x - po.x, q.y - po.y) < C.w * 2 + 14]
        if not otros:
            continue
        q = min(otros, key=lambda q: math.hypot(q.x - po.x, q.y - po.y))
        for pa, pb in list(zip(po.anclajes(4), q.anclajes(4)))[: rnd.randint(2, 4)]:
            fl = rnd.uniform(0.3, 0.7)
            if _libre(pa, pb, fl):
                cable(cables_c, pa, pb, fl)
    # semáforos en los cruces de calles principales
    hechos = []
    for C in cs:
        if C.nombre not in PRINCIPALES:
            continue
        M = C.muestras(0.5)
        estado = [bool([o for o in _en_calzada(cs, p[0], p[1], C) if o.nombre in PRINCIPALES]) for p in M]
        for i in range(1, len(M)):
            if estado[i] and not estado[i - 1]:
                p = M[i - 1]
                x0, y0, tx, ty = p[0], p[1], p[2], p[3]
                otra = [o for o in _en_calzada(cs, M[i][0], M[i][1], C) if o.nombre in PRINCIPALES][0]
                # en la esquina de la derecha (al llegar), sobre la vereda de la otra calle
                nx, ny = ty, -tx
                o_ = getattr(C, "off", 0.0)
                x = x0 - ty * o_ + nx * (C.c + 0.5) - tx * (otra.v - 0.6)
                y = y0 + tx * o_ + ny * (C.c + 0.5) - ty * (otra.v - 0.6)
                if (dentro is None or dentro(x, y)) and dueno_en(x, y) == agente and \
                        all(math.hypot(x - hx, y - hy) > 4 for hx, hy in hechos):
                    semaforo(semaf_c, x, y, nx, ny, tx, ty)
                    hechos.append((x, y))
    return [postes_c.objeto(col), cables_c.objeto(col), semaf_c.objeto(col)]
