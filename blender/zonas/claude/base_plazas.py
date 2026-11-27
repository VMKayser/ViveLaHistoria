"""Plazas sin dueño de la BASE (claude).

PLAZA SAN FRANCISCO (Arce × Ravelo; fotos 130020–130034, 125950, 130006, 130107):
plataforma elevada ~0,7 m sobre la calle con muro de piedra rosada, escalinata hacia la esquina, pavimento de losas,
dos canteros largos con césped, flores y reja baja de hierro, palmeras de abanico altas (7), un árbol de copa grande,
estatua blanca sobre pedestal en el centro, faroles negros de poste y bancos.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit import Constructor, altura_suelo  # noqa: E402
from kit.datos import recortar_a_calles  # noqa: E402

from base_mobiliario import tubo  # noqa: E402
from piezas_claude import arbol  # noqa: E402

# polígono OSM (leisure=park, name=Plaza San Francisco)
PLAZA_SF = [(-106.2, -15.2), (-92.1, -26.9), (-57.3, 15.0), (-71.5, 26.7)]


from adornos_claude import farol_cc0, planta  # noqa: E402

def _inset(poly, d):
    """Encoge un polígono convexo d metros (desplaza cada lado hacia adentro e intersecta)."""
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sg = 1 if area > 0 else -1
    lineas = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        nx, ny = -(b[1] - a[1]) / L * sg, (b[0] - a[0]) / L * sg     # hacia adentro
        lineas.append(((a[0] + nx * d, a[1] + ny * d), (b[0] - a[0], b[1] - a[1])))
    res = []
    for i in range(n):
        (p, r), (q, s) = lineas[i - 1], lineas[i]
        den = r[0] * s[1] - r[1] * s[0]
        t = ((q[0] - p[0]) * s[1] - (q[1] - p[1]) * s[0]) / den
        res.append((p[0] + r[0] * t, p[1] + r[1] * t))
    return res


def palmera(c, x, y, z, alto, rnd):
    """Palmera de las plazuelas: del catálogo elegido por el usuario (palmera alta de Yughues o canaria, CC0)."""
    from arboles_catalogo import poner
    poner(c, rnd.choice(("palmera_alta", "palmera_canaria_b")), x, y, z - 0.05, alto, semilla=rnd.randint(0, 9999))


def farol_poste(c, x, y, z, alto=3.6):
    """Farol colonial negro de poste (vereda de la plaza)."""
    c.cilindro(x, y, z, z + 0.4, 0.14, "hierro", lados=8)
    c.cilindro(x, y, z + 0.4, z + alto, 0.06, "hierro", lados=8)
    c.cilindro(x, y, z + alto, z + alto + 0.12, 0.12, "hierro", lados=6)
    c.cilindro(x, y, z + alto + 0.12, z + alto + 0.55, 0.16, "vidrio", "#efe2b5", lados=6, radio_arriba=0.2)
    c.cilindro(x, y, z + alto + 0.55, z + alto + 0.72, 0.24, "hierro", lados=6, radio_arriba=0.03)


def banco(c, x, y, z, ang):
    ux, uy = math.cos(ang), math.sin(ang)
    vx, vy = -uy, ux
    c.caja_ejes((x, y, z + 0.44), (ux, uy, 0), (vx, vy, 0), (0, 0, 1), 1.7, 0.45, 0.06, "madera", "#6e4a2e")
    c.caja_ejes((x - vx * 0.22, y - vy * 0.22, z + 0.72), (ux, uy, 0), (vx, vy, 0), (0, 0, 1), 1.7, 0.05, 0.4, "madera", "#6e4a2e")
    for s in (-0.7, 0.7):
        c.caja_ejes((x + ux * s, y + uy * s, z + 0.22), (ux, uy, 0), (vx, vy, 0), (0, 0, 1), 0.06, 0.45, 0.44, "hierro")


def plaza_san_francisco(col, cs):
    rnd = random.Random("plaza-sf")
    borde = recortar_a_calles(PLAZA_SF) or PLAZA_SF
    borde = [tuple(p) for p in borde]
    # el borde recortado queda en la línea de fachadas de la calle, justo detrás de la vereda de la BASE
    plat = borde
    zt = lambda x, y: altura_suelo(x, y) + 0.75
    c = Constructor("BASE_plaza_san_francisco")
    # plataforma: tapa sobre el terreno (+0,75) y muro de piedra perimetral
    n = len(plat)
    cx = sum(p[0] for p in plat) / n
    cy = sum(p[1] for p in plat) / n
    for i in range(n):
        a, b = plat[i], plat[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(L // 2))
        for j in range(k):
            p = (a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k)
            q = (a[0] + (b[0] - a[0]) * (j + 1) / k, a[1] + (b[1] - a[1]) * (j + 1) / k)
            c.poligono([(p[0], p[1], altura_suelo(*p) - 0.3), (q[0], q[1], altura_suelo(*q) - 0.3),
                        (q[0], q[1], zt(*q) + 0.05), (p[0], p[1], zt(*p) + 0.05)], "piedra", "#b98a76")
            # pavimento en abanico hacia el centro (sigue la pendiente)
            c.poligono([(p[0], p[1], zt(*p)), (q[0], q[1], zt(*q)), (cx, cy, zt(cx, cy))], "adoquin", "#c9b29a")
    # ejes de la plaza (largo = lado más largo)
    i_l = max(range(n), key=lambda i: math.hypot(plat[(i + 1) % n][0] - plat[i][0], plat[(i + 1) % n][1] - plat[i][1]))
    a, b = plat[i_l], plat[(i_l + 1) % n]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    vx, vy = -uy, ux
    if (cx - a[0]) * vx + (cy - a[1]) * vy < 0:
        vx, vy = -vx, -vy
    ancho = max((p[0] - a[0]) * vx + (p[1] - a[1]) * vy for p in plat)
    P = lambda s, t: (a[0] + ux * s + vx * t, a[1] + uy * s + vy * t)
    # dos canteros largos a cada lado del paseo central, con césped, flores y reja baja
    for t0, t1 in ((1.4, ancho / 2 - 1.6), (ancho / 2 + 1.6, ancho - 1.4)):
        for s0, s1 in ((3.0, L / 2 - 3.5), (L / 2 + 3.5, L - 3.0)):
            esq = [P(s0, t0), P(s1, t0), P(s1, t1), P(s0, t1)]
            c.prisma(esq, min(zt(*p) for p in esq) - 0.1, max(zt(*p) for p in esq) + 0.22, "piedra", "#a98270")
            c.tapa(esq, max(zt(*p) for p in esq) + 0.24, "cesped", "#7c9b45")
            # flores y arbustos (Quaternius, CC0) en lugar de bolas: grupos de flores, arbustos floridos y plantas
            for k in range(int((s1 - s0) // 1.8)):
                fx, fy = P(s0 + 0.9 + k * 1.8, t0 + 0.6 + rnd.random() * (t1 - t0 - 1.2))
                pieza = rnd.choice(["Flower_3_Group", "Flower_4_Group", "Bush_Common_Flowers", "Flower_3_Group",
                                    "Plant_1_Big"])
                planta(c, pieza, fx, fy, max(zt(*p) for p in esq) + 0.24, ang=rnd.uniform(0, 6.28),
                       escala=rnd.uniform(0.45, 0.65), semilla=rnd.randint(0, 999))
            zr = max(zt(*p) for p in esq) + 0.25
            for p, q in zip(esq, esq[1:] + esq[:1]):
                tubo(c, (p[0], p[1], zr + 0.45), (q[0], q[1], zr + 0.45), 0.025, "hierro")
                ll = math.hypot(q[0] - p[0], q[1] - p[1])
                for k in range(int(ll // 0.9) + 1):
                    x = p[0] + (q[0] - p[0]) * k * 0.9 / ll
                    y = p[1] + (q[1] - p[1]) * k * 0.9 / ll
                    tubo(c, (x, y, zr), (x, y, zr + 0.5), 0.018, "hierro")
    # estatua blanca en el centro
    sx, sy = P(L / 2, ancho / 2)
    z0 = zt(sx, sy)
    c.caja_ejes((sx, sy, z0 + 0.3), (ux, uy, 0), (vx, vy, 0), (0, 0, 1), 2.2, 2.2, 0.6, "piedra", "#d9cfc2")
    c.caja_ejes((sx, sy, z0 + 1.6), (ux, uy, 0), (vx, vy, 0), (0, 0, 1), 1.1, 1.1, 2.0, "moldura", "#efeae2")
    c.caja_ejes((sx, sy, z0 + 2.7), (ux, uy, 0), (vx, vy, 0), (0, 0, 1), 1.4, 1.4, 0.2, "moldura", "#efeae2")
    c.cilindro(sx, sy, z0 + 2.8, z0 + 4.2, 0.32, "moldura", "#f4f1ec", lados=8, radio_arriba=0.22)
    c.esfera(sx, sy, z0 + 4.4, 0.2, "moldura", "#f4f1ec", segmentos=8)
    # escalinata en la punta NO (esquina Arce × Ravelo): 4 peldaños hacia afuera
    e0 = P(0, ancho / 2)
    for k in range(4):
        d = 0.35 * (k + 1)
        pa, pb = P(-d, ancho / 2 - 4), P(-d, ancho / 2 + 4)
        pc, pd = P(-d + 0.35, ancho / 2 + 4), P(-d + 0.35, ancho / 2 - 4)
        h = zt(*e0) - 0.18 * (k + 1)
        c.prisma([pa, pb, pc, pd], h - 0.4, h + 0.18, "piedra", "#b98a76")
    # palmeras sobre los canteros y un árbol grande
    for k, s in enumerate((4.5, 12.0, 19.0, 27.0, 35.0, 43.0, 50.0)):
        if s > L - 3:
            continue
        t = (0.9 if k % 2 == 0 else 2.6) + (0 if k % 2 == 0 else ancho / 2)
        px, py = P(s, min(t, ancho - 1.0))
        palmera(c, px, py, zt(px, py), rnd.uniform(8.5, 11.5), rnd)
    ax_, ay_ = P(L * 0.62, ancho * 0.3)
    arbol(c, ax_, ay_, zt(ax_, ay_), alto=8.5, copa=7.0, semilla=7)
    # faroles y bancos a lo largo del paseo
    for s in (2.0, L / 2 - 4.5, L / 2 + 4.5, L - 2.0):
        for t in (ancho / 2 - 1.1, ancho / 2 + 1.1):
            fx, fy = P(s, t)
            farol_cc0(c, fx, fy, zt(fx, fy), ang=math.atan2(vy, vx) * (1 if t < ancho / 2 else -1))
    ang = math.atan2(uy, ux)
    for s in (L / 4, 3 * L / 4):
        for t, g in ((ancho / 2 - 1.2, 0), (ancho / 2 + 1.2, math.pi)):
            bx, by = P(s, t)
            banco(c, bx, by, zt(bx, by), ang + g)
    return [c.objeto(col)]
