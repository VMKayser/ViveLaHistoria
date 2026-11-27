"""BASE — suelo urbano de toda la zona a partir de reparto/calles_reales.json.

Por cada calle (corredor de ancho real, fachada a fachada):
- calzada de asfalto en el centro (ancho − 2 veredas), siguiendo el terreno;
- veredas a ambos lados, 18 cm más altas, con bordillo de piedra (pintado de amarillo cerca de las esquinas,
  como en las fotos de Ravelo, Arce y Junín);
- línea central discontinua blanca y pasos de cebra antes de cada cruce.

En los cruces manda la calle más ancha: la otra calzada se corta donde entra en ella y sus veredas terminan en el
bordillo de la calle que cruza.
"""

import functools
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit import Constructor, altura_suelo  # noqa: E402
from kit.datos import calles_reales, reparto  # noqa: E402

ALTO_VEREDA = 0.18
SOBRE_TERRENO = 0.07       # la calzada flota un poco sobre el terreno del lienzo (rejilla de 5 m)
COLOR_CALZADA = "#77706b"
COLOR_VEREDA = "#bfbab2"   # baldosa de cemento gris (usuario 2026-11-14: "la acera parece de tierra, no de ciudad")
COLOR_BORDILLO = "#b3aca3"
COLOR_AMARILLO = "#e0b43a"
COLOR_LINEA = "#ecebe6"


# Ampliaciones fuera de la zona original donde también hay calles modeladas (correcciones del usuario): la Calle
# Batalla de Junín hasta la Av. Hernando Siles (R0045–R0076) y el oeste de Junín (AMP_O).
AMPLIACIONES = [(-235.0, 95.0, -55.0, 235.0)]


@functools.lru_cache(maxsize=1)
def _secciones():
    """Polígonos de las SECCIONES nuevas (secciones/*.json, refactor 2026-11-14): ahí la BASE no dibuja nada; el suelo
    y el mobiliario los pone la sección."""
    import glob
    import json
    from kit.datos import RAIZ
    res = []
    for r in glob.glob(os.path.join(RAIZ, "secciones", "*.json")):
        d = json.load(open(r))
        if d.get("limite"):
            res.append([tuple(p) for p in d["limite"]])
    return res


def en_seccion(x, y):
    from kit.datos import _dentro
    return any(_dentro(x, y, p) for p in _secciones())


def _zona(margen=20):
    """Caja que cubre la zona y las ampliaciones (espacios AMP_* del reparto y AMPLIACIONES)."""
    z = reparto()["zona"]
    cajas = [(z["xmin"], z["ymin"], z["xmax"], z["ymax"])] + AMPLIACIONES
    for e in reparto().get("espacios", []):
        if e["id"].startswith("AMP_") and e.get("poligono"):
            xs = [p[0] for p in e["poligono"]]
            ys = [p[1] for p in e["poligono"]]
            cajas.append((min(xs) - 15, min(ys) - 15, max(xs) + 15, max(ys) + 15))
    return (min(c[0] for c in cajas) - margen, min(c[1] for c in cajas) - margen,
            max(c[2] for c in cajas) + margen, max(c[3] for c in cajas) + margen)


def _dist_seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy or 1e-9
    t = (((px - a[0]) * dx + (py - a[1]) * dy) / l2)
    tc = max(0.0, min(1.0, t))
    return math.hypot(px - a[0] - tc * dx, py - a[1] - tc * dy)



def _area(poly):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1])) / 2


def _sobre_linea(u, v, a, b, tol=0.05):
    """¿El segmento u–v está sobre la recta a–b?"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-9
    d = lambda p: abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / L
    return d(u) < tol and d(v) < tol


def _fuera_de_calzada(poly, o):
    """Recorta el polígono quitándole la parte que cae en la calzada de la calle o (el tramo de su eje más cercano):
    se conserva el lado del bordillo donde está el centro del polígono."""
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    a, b = min(zip(o.eje, o.eje[1:]), key=lambda s_: _dist_seg(cx, cy, s_[0], s_[1]))
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1e-9
    nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L          # izquierda del eje
    d = lambda p: (p[0] - a[0]) * nx + (p[1] - a[1]) * ny - o.off
    lado = 1.0 if d((cx, cy)) >= 0 else -1.0
    f = lambda p: lado * d(p) - o.c                          # >= 0: fuera de la calzada
    res = []
    for p, q in zip(poly, poly[1:] + poly[:1]):
        fp, fq = f(p), f(q)
        if fp >= 0:
            res.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            res.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return res

class Calle:
    def __init__(self, d, idx):
        self.nombre = d["nombre"]
        self.idx = idx
        self.w = d["ancho"] / 2
        self.v = d["vereda"]
        self.c = self.w - self.v          # medio ancho de calzada
        self.peatonal = bool(d.get("peatonal"))   # Peatonal de Junín: adoquín de piedra, sin marcas
        # veredas distintas a cada lado (izquierda = normal (-ty, tx) del sentido del eje): la calzada se corre `off`
        vi, vd = d.get("vereda_izq", self.v), d.get("vereda_der", self.v)
        self.c = (2 * self.w - vi - vd) / 2
        self.off = (vd - vi) / 2
        self.eje = [tuple(p) for p in d["eje"]]
        self.extra = d.get("vereda_extra", 0.0)   # vereda que sigue por debajo de las fachadas retiradas (R0112)
        self.prioridad = (d["ancho"], -idx)
        xs = [p[0] for p in self.eje]
        ys = [p[1] for p in self.eje]
        self.caja = (min(xs) - self.w - 1, min(ys) - self.w - 1, max(xs) + self.w + 1, max(ys) + self.w + 1)

    def dist(self, x, y):
        if not (self.caja[0] <= x <= self.caja[2] and self.caja[1] <= y <= self.caja[3]):
            return 1e9
        return min(_dist_seg(x, y, a, b) for a, b in zip(self.eje, self.eje[1:]))

    def cubre(self, x, y, r, off=0.0):
        """True si (x, y) cae sobre la franja de ancho ±r de algún tramo (sin los extremos redondeados), corrida `off`
        hacia la izquierda del eje."""
        if not (self.caja[0] <= x <= self.caja[2] and self.caja[1] <= y <= self.caja[3]):
            return False
        for a, b in zip(self.eje, self.eje[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            l2 = dx * dx + dy * dy
            if l2 < 1e-6:
                continue
            t = ((x - a[0]) * dx + (y - a[1]) * dy) / l2
            L = math.sqrt(l2)
            if -0.3 / L <= t <= 1 + 0.3 / L:
                if abs(-((x - a[0]) * dy - (y - a[1]) * dx) / L - off) < r:
                    return True
        return False

    def muestras(self, paso):
        """[(x, y, tx, ty, nx, ny, s)] cada `paso` m a lo largo del eje (normal = izquierda)."""
        res, s0 = [], 0.0
        for a, b in zip(self.eje, self.eje[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 1e-3:
                continue
            tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            n = max(1, round(L / paso))
            for k in range(n + (1 if b == self.eje[-1] else 0)):
                t = L * k / n
                res.append((a[0] + tx * t, a[1] + ty * t, tx, ty, -ty, tx, s0 + t))
            s0 += L
        return res


def calles_zona():
    z = _zona(40)
    res = []
    for i, d in enumerate(calles_reales()):
        if any(z[0] < x < z[2] and z[1] < y < z[3] for x, y in d["eje"]):
            res.append(Calle(d, i))
    # Cruces: los ejes corregidos de dos calles que se encuentran a veces no llegan uno al otro y el hueco del cruce
    # quedaba lleno de puntas de vereda ("la acera tiene forma de estrella", R0110). Cada extremo que llega a otra calle
    # se prolonga 4 m: la calzada cubre el cruce y los trozos de vereda que caen en ella se descartan.
    for C in res:
        for k, j in ((0, 1), (-1, -2)):
            if len(C.eje) < 2:
                continue
            p, q = C.eje[k], C.eje[j]
            L = math.hypot(p[0] - q[0], p[1] - q[1]) or 1.0
            ux_, uy_ = (p[0] - q[0]) / L, (p[1] - q[1]) / L

            def _otra_direccion(o):
                # otra calle, o la misma que dobla (tramos de la plaza en sus esquinas)
                if o.nombre != C.nombre:
                    return True
                a_, b_ = min(zip(o.eje, o.eje[1:]), key=lambda s_: _dist_seg(p[0], p[1], s_[0], s_[1]))
                Lo = math.hypot(b_[0] - a_[0], b_[1] - a_[1]) or 1.0
                return abs(ux_ * (b_[0] - a_[0]) / Lo + uy_ * (b_[1] - a_[1]) / Lo) < 0.87
            if not any(o is not C and o.dist(*p) < o.w + 3.0 and _otra_direccion(o) for o in res):
                continue
            L = math.hypot(p[0] - q[0], p[1] - q[1]) or 1.0
            nuevo = (p[0] + (p[0] - q[0]) / L * 4.0, p[1] + (p[1] - q[1]) / L * 4.0)
            if k == 0:
                C.eje.insert(0, nuevo)
            else:
                C.eje.append(nuevo)
        xs = [p[0] for p in C.eje]
        ys = [p[1] for p in C.eje]
        C.caja = (min(xs) - C.w - 1, min(ys) - C.w - 1, max(xs) + C.w + 1, max(ys) + C.w + 1)
    return res


def _en_calzada(cs, x, y, salvo):
    return [o for o in cs if o is not salvo and o.cubre(x, y, o.c, o.off)]


def _en_corredor(cs, x, y, salvo):
    return [o for o in cs if o is not salvo and o.cubre(x, y, o.w)]


def construir_suelo(col, caja=None):
    """caja (x0, y0, x1, y1): solo los tramos que EMPIEZAN en esa tesela (BASE por teselas; sin duplicados en los
    bordes)."""
    cs = calles_zona()
    z = _zona()
    if caja:
        dentro = lambda x, y: (z[0] < x < z[2] and z[1] < y < z[3] and caja[0] <= x < caja[2] and caja[1] <= y < caja[3]
                               and not en_seccion(x, y))
    else:
        dentro = lambda x, y: z[0] < x < z[2] and z[1] < y < z[3] and not en_seccion(x, y)
    calzada = Constructor("BASE_calzada")
    veredas = Constructor("BASE_veredas")
    marcas = Constructor("BASE_marcas")
    zs = lambda x, y: altura_suelo(x, y)

    for C in cs:
        # ------------------------------------------------------------------ calzada
        M = C.muestras(1.0)
        div = max(2, round(2 * C.c / 2.5))
        for p, q in zip(M, M[1:]):
            if not (dentro(p[0], p[1]) if caja else (dentro(p[0], p[1]) or dentro(q[0], q[1]))):
                continue
            # en un cruce, la calle de menos prioridad no pone calzada donde ya está la de la otra
            o_ = C.off
            esquinas = [(p[0] + p[4] * (o_ + C.c), p[1] + p[5] * (o_ + C.c)), (p[0] + p[4] * (o_ - C.c), p[1] + p[5] * (o_ - C.c)),
                        (q[0] + q[4] * (o_ + C.c), q[1] + q[5] * (o_ + C.c)), (q[0] + q[4] * (o_ - C.c), q[1] + q[5] * (o_ - C.c))]
            if any(all(o.cubre(x, y, o.c, o.off) for x, y in esquinas) for o in cs if o is not C and o.prioridad > C.prioridad):
                continue
            # cruce parcial: esta calzada queda 1,5 cm DEBAJO de la de más prioridad (coplanares parpadeaban, R0132)
            dz = -0.015 if any(any(o.cubre(x, y, o.c, o.off) for x, y in esquinas) for o in cs
                               if o is not C and o.prioridad > C.prioridad) else 0.0
            for k in range(div):
                u0, u1 = o_ - C.c + 2 * C.c * k / div, o_ - C.c + 2 * C.c * (k + 1) / div
                pts = [(p[0] + p[4] * u0, p[1] + p[5] * u0), (q[0] + q[4] * u0, q[1] + q[5] * u0),
                       (q[0] + q[4] * u1, q[1] + q[5] * u1), (p[0] + p[4] * u1, p[1] + p[5] * u1)]
                # la Peatonal también es de asfalto (usuario R0132 y fotos Peatonal/), solo que sin marcas
                calzada.poligono([(x, y, zs(x, y) + SOBRE_TERRENO + dz) for x, y in pts], "calzada", COLOR_CALZADA)

        # ------------------------------------------------------------------ veredas y bordillos
        M = C.muestras(0.5)
        for sg in (1, -1):
            vivo = []
            for p, q in zip(M, M[1:]):
                ci = C.off + sg * C.c                       # borde de la calzada de este lado
                mx, my = (p[0] + q[0]) / 2 + p[4] * (ci + sg * C.w) / 2, (p[1] + q[1]) / 2 + p[5] * (ci + sg * C.w) / 2
                ok = dentro(mx, my) and not _en_calzada(cs, mx, my, C)
                if ok:
                    # esquina compartida con otra vereda: se la queda la calle de más prioridad
                    otras = [o for o in _en_corredor(cs, mx, my, C)]
                    if any(o.prioridad > C.prioridad for o in otras):
                        ok = False
                vivo.append(ok)
            for i, (p, q) in enumerate(zip(M, M[1:])):
                if not vivo[i]:
                    continue
                ci = C.off + sg * C.c
                cerca_cruce = any(_en_calzada(cs, r[0] + r[4] * ci, r[1] + r[5] * ci, C)
                                  for r in M[max(0, i - 14): i + 16: 3])
                a_in = (p[0] + p[4] * ci, p[1] + p[5] * ci)
                b_in = (q[0] + q[4] * ci, q[1] + q[5] * ci)
                a_out = (p[0] + p[4] * sg * (C.w + 0.1 + C.extra), p[1] + p[5] * sg * (C.w + 0.1 + C.extra))
                b_out = (q[0] + q[4] * sg * (C.w + 0.1 + C.extra), q[1] + q[5] * sg * (C.w + 0.1 + C.extra))
                top = lambda pt: (pt[0], pt[1], zs(*pt) + SOBRE_TERRENO + ALTO_VEREDA)
                bot = lambda pt: (pt[0], pt[1], zs(*pt) + SOBRE_TERRENO - 0.05)
                color_b = COLOR_AMARILLO if cerca_cruce else COLOR_BORDILLO
                # en los cruces, el trozo de vereda se RECORTA contra el bordillo de la otra calle (antes se dejaba
                # entero o se descartaba y la esquina quedaba en dientes: "la acera tiene forma de estrella", R0110)
                quad = [a_in, b_in, b_out, a_out]
                otras = [o for o in cs if o is not C and any(o.cubre(x_, y_, o.c, o.off) for x_, y_ in quad)]
                if otras:
                    poly = quad
                    for o in otras:
                        poly = _fuera_de_calzada(poly, o)
                        if len(poly) < 3:
                            break
                    if len(poly) >= 3 and abs(_area(poly)) > 0.02:
                        veredas.poligono([top(pt) for pt in poly], "vereda", COLOR_VEREDA)
                        # bordillo en todo el contorno salvo el borde exterior (el de las fachadas)
                        for u_, v_ in zip(poly, poly[1:] + poly[:1]):
                            if _sobre_linea(u_, v_, a_out, b_out):
                                continue
                            veredas.poligono([bot(u_), bot(v_), top(v_), top(u_)], "piedra", COLOR_AMARILLO)
                    continue
                veredas.poligono([top(a_in), top(b_in), top(b_out), top(a_out)], "vereda", COLOR_VEREDA)
                veredas.poligono([bot(a_in), bot(b_in), top(b_in), top(a_in)], "piedra", color_b)
                # tapas al final de un tramo de vereda (frente al cruce)
                if i == 0 or not vivo[i - 1]:
                    veredas.poligono([bot(a_in), top(a_in), top(a_out), bot(a_out)], "piedra", color_b)
                if i == len(vivo) - 1 or not vivo[i + 1]:
                    veredas.poligono([bot(b_in), bot(b_out), top(b_out), top(b_in)], "piedra", color_b)

        # ------------------------------------------------------------------ marcas: línea central y cebras
        if C.c >= 3.0 and not C.peatonal:
            M = C.muestras(0.5)
            for p, q in zip(M, M[1:]):
                if (p[6] % 8.0) >= 3.0 or not dentro(p[0], p[1]):
                    continue
                if _en_calzada(cs, p[0], p[1], C) or _en_calzada(cs, q[0], q[1], C):
                    continue
                e = 0.06
                pts = [(p[0] + p[4] * e, p[1] + p[5] * e), (q[0] + q[4] * e, q[1] + q[5] * e),
                       (q[0] - q[4] * e, q[1] - q[5] * e), (p[0] - p[4] * e, p[1] - p[5] * e)]
                marcas.poligono([(x, y, zs(x, y) + SOBRE_TERRENO + 0.02) for x, y in pts], "pintura_acento", COLOR_LINEA)
        # cebras: donde el eje entra en la calzada de otra calle, 3 m de franjas antes del bordillo de esa calle
        M = C.muestras(0.5) if not C.peatonal else []
        estado = [bool(_en_calzada(cs, p[0], p[1], C)) for p in M]
        for i in range(1, len(M)):
            for entra, j0, paso in ((estado[i] and not estado[i - 1], i, -1), (estado[i - 1] and not estado[i], i - 1, 1)):
                if not entra:
                    continue
                otra = _en_calzada(cs, M[j0][0], M[j0][1], C)[0]
                # la cebra arranca a la altura de la vereda de la otra calle
                s_ini = M[j0][6] + paso * (otra.v + 0.4)
                s_fin = s_ini + paso * 3.0
                _cebra(marcas, C, min(s_ini, s_fin), max(s_ini, s_fin), zs, dentro)

    # ---------------------------------------------------------------------- detalles del piso (fotos: parches, tapas)
    import random
    piso = Constructor("BASE_piso_detalles")
    for C in cs:
        rnd = random.Random("piso" + C.nombre)
        M = C.muestras(1.0)
        if len(M) < 4:
            continue
        L = M[-1][6]
        s = rnd.uniform(3, 10)
        while s < L:
            x0, y0, tx, ty = _punto_en(C, s)
            nx, ny = -ty, tx
            if dentro(x0, y0) and not _en_calzada(cs, x0, y0, C):
                tipo = rnd.random()
                u = C.off + rnd.uniform(-C.c + 1.2, C.c - 1.2)
                x, y = x0 + nx * u, y0 + ny * u
                zc = zs(x, y) + SOBRE_TERRENO + 0.015
                if tipo < 0.35:          # tapa de alcantarilla
                    piso.cilindro(x, y, zc - 0.02, zc + 0.005, 0.34, "hierro", "#4b4743", lados=10)
                elif tipo < 0.8:
                    # (aquí iban parches de asfalto repartidos al azar, oscuros y claros: el usuario los vio como
                    # "cemento en la calle", 2026-11-24; las reglas prohíben adornos al azar en toda la ciudad)
                    pass
                else:                    # sumidero junto al bordillo
                    sg = rnd.choice([-1, 1])
                    x, y = x0 + nx * (C.off + sg * (C.c - 0.25)), y0 + ny * (C.off + sg * (C.c - 0.25))
                    piso.caja_ejes((x, y, zs(x, y) + SOBRE_TERRENO + 0.008), (tx, ty, 0), (nx, ny, 0), (0, 0, 1), 0.9, 0.4, 0.02,
                                   "hierro", "#3d3a37")
            s += rnd.uniform(7, 16)
    obs = [calzada.objeto(col), veredas.objeto(col), marcas.objeto(col), piso.objeto(col)]
    return cs, obs


def _punto_en(C, s):
    s0 = 0.0
    for a, b in zip(C.eje, C.eje[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1e-3:
            continue
        if s <= s0 + L or b == C.eje[-1]:
            t = max(0.0, min(L, s - s0))
            tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            return a[0] + tx * t, a[1] + ty * t, tx, ty
        s0 += L
    return None


def _cebra(marcas, C, s0, s1, zs, dentro):
    """Franjas de 0,5 m (paralelas al eje de la calle) cada 1 m, a lo ancho de la calzada, entre s0 y s1."""
    pa, pb = _punto_en(C, s0), _punto_en(C, s1)
    if not pa or not pb or not dentro(pa[0], pa[1]):
        return
    tx, ty = pa[2], pa[3]
    nx, ny = -ty, tx
    L = s1 - s0
    u = -C.c + 0.6
    while u + 0.5 <= C.c - 0.6:
        pts = [(pa[0] + nx * u, pa[1] + ny * u), (pa[0] + nx * (u + 0.5), pa[1] + ny * (u + 0.5)),
               (pa[0] + nx * (u + 0.5) + tx * L, pa[1] + ny * (u + 0.5) + ty * L), (pa[0] + nx * u + tx * L, pa[1] + ny * u + ty * L)]
        marcas.poligono([(x, y, zs(x, y) + SOBRE_TERRENO + 0.02) for x, y in pts], "pintura_acento", COLOR_LINEA)
        u += 1.0
