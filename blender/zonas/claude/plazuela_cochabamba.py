"""Plazuela Cochabamba, rehecha desde cero el 2026-11-24 (R0180, R0181, R0183, R0103, R0104; fotos del usuario a
resolución completa). Pedido: "falta mucho detalle, fíjate el suelo, ancho, jardines", "tiene balaustrada especial".

Marco local: u a lo largo de la Calle Juan José Pérez desde la esquina de Colón (0) hacia el SO (54,6); v desde el borde
de Pérez (0) hacia las casas del NO (~25). Datos de OSM: el sendero central (v ≈ 12,5) con la escultura en u = 40,7, el
pasaje junto a las casas (v ≈ 24), 12 árboles (filas en v ≈ 8,5 y v ≈ 15, y tres junto al borde de Pérez) y 3 palmeras.

Inventario de las fotos:
- piso de losas grandes rosado-grisáceas en toda la plazuela; el piso sigue la pendiente (2,7 m de la esquina de Colón
  al extremo SO), sin muros de contención;
- borde a las dos calles: pilares de arenisca gris-beige de ~1,5 m con remate, sobre un murete, y entre ellos baranda
  negra de cuadros con una cruz; por dentro un murete-banco de piedra rosada; abierto en los senderos;
- canteros rectangulares con bordillo bajo de cemento, reja baja de arcos de varilla, pasto, franjas de flores naranjas
  y amarillas y rosales; árboles de copa ancha en paraguas con el pie encalado (en el piso, con reja redonda);
- palmeras canarias de tronco grueso y una palmera de abanico junto a la esquina de Colón;
- bancos de listones rojizos, faroles negros, la casetita con techo de teja y la escultura del sendero central.
"""
import math
import random

from kit import Constructor, altura_suelo
from piezas_claude import arbol_paraguas
from base_plazas import banco, farol_poste

LOSA = "#c4a294"
LOSA2 = "#b9998d"
BORDILLO = "#d2c9b8"
PILAR = "#b3a088"
ROSADA = "#c08f80"
NEGRO = "#1e1f1f"

# canteros (u0, u1, v0, v1): dos hileras a los lados del sendero central, cortadas por senderos transversales
HILERAS = ((4.6, 11.0), (14.0, 19.6))
TRAMOS_U = ((6.5, 17.3), (20.3, 28.8), (31.8, 37.0), (44.6, 52.4))
ESCULTURA = (40.7, 13.2)
ARBOLES = [(11.6, 8.0), (23.7, 8.6), (35.6, 9.2), (22.7, 14.9), (34.9, 15.9), (30.1, 15.8), (12.4, 14.6), (7.2, 21.9),
           (50.4, 8.9), (47.4, 2.7), (41.5, 2.5), (34.4, 3.4),
           (48.5, 16.8), (19.0, 21.2), (31.0, 21.2), (47.0, 21.4)]   # los cuatro últimos, de las fotos (cantero y pasaje)
PALMERAS = [((3.9, 11.1), "palmera_canaria"), ((2.3, 23.4), "palmera_canaria_b"), ((42.0, 20.5), "palmera_canaria"),
            ((8.5, 17.5), "palmera_alta")]            # la de abanico, entre las dos canarias de Colón (R0103, R0181)
ENTRADAS_PEREZ = ((17.3, 20.3), (28.8, 31.8), (37.0, 44.6))      # tramos de u sin pilares (senderos transversales)
ENTRADAS_COLON = ((11.0, 14.0), (19.6, 30.0))                    # sendero central y pasaje de las casas


def _baranda_cuadros(c, p, q, z0, z1, ux, uy):
    """Baranda de hierro de la plazuela (R0181/R0183): marco y cuadros con una cruz dentro, entre dos pilares."""
    GR = "#34383a"
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    nx, ny = -uy, ux
    for zz in (z0, z1):
        c.caja_ejes(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, zz), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), L, 0.04, 0.04,
                    "hierro", GR)
    n = max(1, round(L / 0.55))
    paso = L / n
    for k in range(n + 1):
        x, y = p[0] + ux * paso * k, p[1] + uy * paso * k
        c.cilindro(x, y, z0, z1, 0.018, "hierro", GR, lados=4)
    lado = min(0.3, (z1 - z0) * 0.55)
    zc = (z0 + z1) / 2
    for k in range(n):                                                                    # cuadro con cruz
        x, y = p[0] + ux * paso * (k + 0.5), p[1] + uy * paso * (k + 0.5)
        for dz in (-lado / 2, lado / 2):
            c.caja_ejes((x, y, zc + dz), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), lado, 0.025, 0.025, "hierro", GR)
        for dd in (-lado / 2, lado / 2):
            c.caja_ejes((x + ux * dd, y + uy * dd, zc), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 0.025, 0.025, lado, "hierro", GR)
        c.caja_ejes((x, y, zc), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), lado * 0.7, 0.02, 0.02, "hierro", GR)
        c.caja_ejes((x, y, zc), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 0.02, 0.02, lado * 0.7, "hierro", GR)


def _reja_arcos(c, p, q, z, alto=0.6):
    """Reja baja de los jardines (R0180/R0181): pasamanos y arcos de varilla que se cruzan."""
    NG = "#1e1f1f"
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    if L < 0.4:
        return
    ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    nx, ny = -uy, ux
    c.caja_ejes(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, z + alto), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), L, 0.03, 0.03, "hierro", NG)
    k = 0.0
    while k < L:
        x, y = p[0] + ux * k, p[1] + uy * k
        c.cilindro(x, y, z, z + alto, 0.012, "hierro", NG, lados=4)
        for j in range(6):                                                                # arco de varilla
            t0, t1 = j / 6 * math.pi, (j + 1) / 6 * math.pi
            r = 0.22
            a0 = (x + ux * (r - r * math.cos(t0)), y + uy * (r - r * math.cos(t0)), z + 0.1 + r * math.sin(t0))
            a1 = (x + ux * (r - r * math.cos(t1)), y + uy * (r - r * math.cos(t1)), z + 0.1 + r * math.sin(t1))
            dx, dy, dz = a1[0] - a0[0], a1[1] - a0[1], a1[2] - a0[2]
            Lb = math.sqrt(dx * dx + dy * dy + dz * dz)
            ez = (dx / Lb, dy / Lb, dz / Lb)
            ey = (ez[1] * 0 - ez[2] * ny, ez[2] * nx - ez[0] * 0, ez[0] * ny - ez[1] * nx)
            c.caja_ejes(((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2, (a0[2] + a1[2]) / 2), (nx, ny, 0), ey, ez, 0.015, 0.015, Lb,
                        "hierro", NG)
        k += 0.22


class Marco:
    """Marco local de la plazuela (u, v) → (x, y) y el piso, que sigue el terreno."""

    def __init__(self, pol):
        self.pol = pol
        B, D, E = pol[1], pol[3], pol[4]
        L = math.hypot(B[0] - D[0], B[1] - D[1])
        self.u = ((B[0] - D[0]) / L, (B[1] - D[1]) / L)
        v = (-self.u[1], self.u[0])
        G = pol[6]
        if (G[0] - E[0]) * v[0] + (G[1] - E[1]) * v[1] < 0:
            v = (-v[0], -v[1])
        self.v = v
        self.o = E

    def xy(self, u, v):
        return (self.o[0] + self.u[0] * u + self.v[0] * v, self.o[1] + self.u[1] * u + self.v[1] * v)

    def uv(self, x, y):
        dx, dy = x - self.o[0], y - self.o[1]
        return (dx * self.u[0] + dy * self.u[1], dx * self.v[0] + dy * self.v[1])

    def z(self, x, y):
        return altura_suelo(x, y) + 0.15


def _recortar(poly, conv):
    """Sutherland–Hodgman: poly recortado por el polígono convexo conv (los dos en planta)."""
    conv = _envolvente(conv)
    s = 1 if sum(conv[i - 1][0] * conv[i][1] - conv[i][0] * conv[i - 1][1] for i in range(len(conv))) > 0 else -1
    out = list(poly)
    for i in range(len(conv)):
        a, b = conv[i - 1], conv[i]
        inp, out = out, []
        if not inp:
            break

        def dentro(p):
            return s * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) >= -1e-9

        for j in range(len(inp)):
            p, q = inp[j - 1], inp[j]
            if dentro(q):
                if not dentro(p):
                    out.append(_corte(p, q, a, b))
                out.append(q)
            elif dentro(p):
                out.append(_corte(p, q, a, b))
    return out


def _envolvente(pts):
    """Envolvente convexa (el borde de OSM tiene un vértice casi alineado que lo hace apenas cóncavo)."""
    pts = sorted(set(pts))

    def giro(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    abajo, arriba = [], []
    for p in pts:
        while len(abajo) >= 2 and giro(abajo[-2], abajo[-1], p) <= 0:
            abajo.pop()
        abajo.append(p)
    for p in reversed(pts):
        while len(arriba) >= 2 and giro(arriba[-2], arriba[-1], p) <= 0:
            arriba.pop()
        arriba.append(p)
    return abajo[:-1] + arriba[:-1]


def _corte(p, q, a, b):
    x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
    x3, y3, x4, y4 = a[0], a[1], b[0], b[1]
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4) or 1e-12
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def losa(c, M, conv, dz, rol, color, paso=2.0):
    """Superficie que sigue el terreno (dz sobre el piso) sobre el polígono convexo conv, en celdas de `paso` m."""
    us = [M.uv(*p) for p in conv]
    u0, u1 = min(p[0] for p in us), max(p[0] for p in us)
    v0, v1 = min(p[1] for p in us), max(p[1] for p in us)
    u = u0
    while u < u1:
        v = v0
        while v < v1:
            celda = [M.xy(u, v), M.xy(u + paso, v), M.xy(u + paso, v + paso), M.xy(u, v + paso)]
            r = _recortar(celda, conv)
            if len(r) >= 3:
                if sum(r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1] for i in range(len(r))) < 0:
                    r = r[::-1]                                                      # cara hacia arriba
                c.poligono([(x, y, M.z(x, y) + dz) for x, y in r], rol, color)
            v += paso
        u += paso


def _rect(M, u0, u1, v0, v1, chaflan=0.0):
    k = chaflan
    pts = [(u0 + k, v0), (u1 - k, v0), (u1, v0 + k), (u1, v1 - k), (u1 - k, v1), (u0 + k, v1), (u0, v1 - k), (u0, v0 + k)]
    if not k:
        pts = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    return [M.xy(u, v) for u, v in pts]


def _pared(c, M, p, q, dz0, dz1, rol, color):
    """Cara vertical entre p y q, de dz0 a dz1 sobre el piso (sigue la pendiente)."""
    c.poligono([(p[0], p[1], M.z(*p) + dz0), (q[0], q[1], M.z(*q) + dz0), (q[0], q[1], M.z(*q) + dz1),
                (p[0], p[1], M.z(*p) + dz1)], rol, color)


def _por_tramos(p, q, largo):
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    n = max(1, round(L / largo))
    return [((p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n),
             (p[0] + (q[0] - p[0]) * (k + 1) / n, p[1] + (q[1] - p[1]) * (k + 1) / n)) for k in range(n)]


# ---------------------------------------------------------------------------------------------- partes
def piso(c, M):
    losa(c, M, M.pol, 0.0, "vereda", LOSA)
    for p, q in zip(M.pol, M.pol[1:] + M.pol[:1]):                                   # canto hasta el terreno
        _pared(c, M, p, q, -0.45, 0.0, "piedra", LOSA2)
    # sendero central y roseta de la escultura, de losa más gris
    for a, b in ((0.0, ESCULTURA[0] - 3.2), (ESCULTURA[0] + 3.2, 54.6)):
        losa(c, M, _rect(M, a, b, 11.3, 13.7), 0.015, "vereda", LOSA2)
    pts = [M.xy(ESCULTURA[0] + 3.2 * math.cos(t), ESCULTURA[1] + 3.2 * math.sin(t)) for t in
           [k * math.tau / 16 for k in range(16)]]
    losa(c, M, pts, 0.015, "vereda", LOSA2)


def cantero(c, M, u0, u1, v0, v1, rnd):
    conv = _rect(M, u0, u1, v0, v1, chaflan=0.8)
    interior = _rect(M, u0 + 0.18, u1 - 0.18, v0 + 0.18, v1 - 0.18, chaflan=0.7)
    for p, q in zip(conv, conv[1:] + conv[:1]):                                      # bordillo
        _pared(c, M, p, q, -0.05, 0.2, "piedra", BORDILLO)
    for p, q, pi, qi in zip(conv, conv[1:] + conv[:1], interior, interior[1:] + interior[:1]):
        c.poligono([(x, y, M.z(x, y) + 0.2) for x, y in (p, q, qi, pi)], "piedra", BORDILLO)
    losa(c, M, interior, 0.16, "cesped", "#6d9a45", paso=2.5)
    for p, q in zip(interior, interior[1:] + interior[:1]):                          # reja baja de arcos
        for a, b in _por_tramos(p, q, 1.1):
            _reja_arcos(c, a, b, min(M.z(*a), M.z(*b)) + 0.2, alto=0.5)
    # franjas de flores naranjas y amarillas a lo largo, rosales en dos esquinas
    for vv, col in ((v0 + 0.9, "#e48a1f"), (v1 - 0.9, "#e9b824")):
        for a in _tramos_flor(u0 + 1.4, u1 - 1.4, rnd):
            losa(c, M, _rect(M, a[0], a[1], vv - 0.45, vv + 0.45), 0.32, "flor", col, paso=3.0)
    for uu, vv in ((u0 + 1.1, v0 + 1.1), (u1 - 1.1, v1 - 1.1)):
        x, y = M.xy(uu, vv)
        z = M.z(x, y) + 0.16
        c.esfera(x, y, z + 0.45, 0.6, "follaje", "#3f6a2c", segmentos=8)
        for k in range(5):
            t = k * math.tau / 5 + rnd.uniform(0, 1)
            c.esfera(x + 0.4 * math.cos(t), y + 0.4 * math.sin(t), z + 0.7 + rnd.uniform(0, 0.25), 0.16, "flor", "#e46b8e",
                     segmentos=6)


def _tramos_flor(a, b, rnd):
    out, u = [], a
    while u < b - 0.8:
        L = min(b - u, rnd.uniform(2.0, 3.5))
        out.append((u, u + L))
        u += L + rnd.uniform(0.6, 1.2)
    return out


def borde(c, M):
    """Pilares de arenisca con baranda de cuadros y murete-banco rosado, en Pérez y en Colón."""
    perez = [(u0, u1) for u0, u1 in _libres(1.2, 54.4, ENTRADAS_PEREZ)]
    colon = [(v0, v1) for v0, v1 in _libres(1.6, 24.5, ENTRADAS_COLON)]
    tramos = [(M.xy(a, 0.35), M.xy(b, 0.35)) for a, b in perez]
    pc = M.pol[5]
    p6 = M.pol[6]
    for a, b in colon:                                                               # lado de Colón (F→G)
        L = math.hypot(p6[0] - pc[0], p6[1] - pc[1])
        ux, uy = (p6[0] - pc[0]) / L, (p6[1] - pc[1]) / L
        ix, iy = M.u[0] * 0.35, M.u[1] * 0.35                                       # hacia dentro
        tramos.append(((pc[0] + ux * a + ix, pc[1] + uy * a + iy), (pc[0] + ux * b + ix, pc[1] + uy * b + iy)))
    for p, q in tramos:
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if L < 1.0:
            continue
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        n = max(1, round(L / 2.3))
        pts = [(p[0] + ux * L * k / n, p[1] + uy * L * k / n) for k in range(n + 1)]
        for x, y in pts:                                                             # pilares
            z = M.z(x, y)
            c.caja_ejes((x, y, z + 0.75), (ux, uy, 0), (-uy, ux, 0), (0, 0, 1), 0.5, 0.5, 1.5, "zocalo_piedra", PILAR)
            c.caja_ejes((x, y, z + 1.55), (ux, uy, 0), (-uy, ux, 0), (0, 0, 1), 0.6, 0.6, 0.1, "piedra", "#d5c7b0")
            c.caja_ejes((x, y, z + 1.66), (ux, uy, 0), (-uy, ux, 0), (0, 0, 1), 0.44, 0.44, 0.12, "piedra", "#cdbda4")
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            z = min(M.z(x0, y0), M.z(x1, y1))
            a = (x0 + ux * 0.25, y0 + uy * 0.25)
            b = (x1 - ux * 0.25, y1 - uy * 0.25)
            _pared(c, M, a, b, -0.1, 0.3, "zocalo_piedra", PILAR)                    # murete bajo la baranda
            _baranda_cuadros(c, a, b, z + 0.3, z + 1.25, ux, uy)
            # murete-banco rosado por dentro
            ix, iy = M.v if abs(ux * M.u[0] + uy * M.u[1]) > 0.7 else M.u
            ai = (a[0] + ix * 0.55, a[1] + iy * 0.55)
            bi = (b[0] + ix * 0.55, b[1] + iy * 0.55)
            mx, my = (ai[0] + bi[0]) / 2, (ai[1] + bi[1]) / 2
            Lb = math.hypot(bi[0] - ai[0], bi[1] - ai[1])
            zb = M.z(mx, my)
            c.caja_ejes((mx, my, zb + 0.2), (ux, uy, 0), (-uy, ux, 0), (0, 0, 1), Lb, 0.45, 0.5, "piedra", ROSADA)


def _libres(a, b, huecos):
    out, x = [], a
    for h0, h1 in sorted(huecos):
        if h0 > x:
            out.append((x, min(h0, b)))
        x = max(x, h1)
    if x < b:
        out.append((x, b))
    return out


def gradas_esquina(c, M):
    """Gradas de losa rosada en la esquina de Colón y Pérez (R0181): tres peldaños bajos a lo largo del chaflán."""
    p, q = M.pol[3], M.pol[5]
    ux, uy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    nx, ny = -(M.u[0] + M.v[0]) * 0.7071, -(M.u[1] + M.v[1]) * 0.7071
    for j in range(3):
        d = 0.35 * j
        mx, my = (p[0] + q[0]) / 2 - nx * (0.2 + d), (p[1] + q[1]) / 2 - ny * (0.2 + d)
        z = M.z(mx, my)
        c.caja_ejes((mx, my, z - 0.15 - 0.15 * j + 0.075), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), L + 2.5, 0.35, 0.3,
                    "piedra", ROSADA)


def arbol(c, M, u, v, rnd, en_piso):
    x, y = M.xy(u, v)
    z = M.z(x, y) + (0.0 if en_piso else 0.16)
    arbol_paraguas(c, x, y, z, alto=rnd.uniform(6.0, 7.0), copa=rnd.uniform(7.0, 8.2), semilla=rnd.randint(0, 999),
                   alcorque=False)
    if en_piso:                                                                      # reja redonda al pie
        for j in range(18):
            t = j * math.tau / 18
            c.cilindro(x + 0.8 * math.cos(t), y + 0.8 * math.sin(t), z, z + 0.6, 0.012, "hierro", NEGRO, lados=4)
        for hh in (0.08, 0.6):
            for j in range(18):
                t0, t1 = j * math.tau / 18, (j + 1) * math.tau / 18
                p0 = (x + 0.8 * math.cos(t0), y + 0.8 * math.sin(t0))
                p1 = (x + 0.8 * math.cos(t1), y + 0.8 * math.sin(t1))
                Lb = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                ux, uy = (p1[0] - p0[0]) / Lb, (p1[1] - p0[1]) / Lb
                c.caja_ejes(((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, z + hh), (ux, uy, 0), (-uy, ux, 0), (0, 0, 1),
                            Lb, 0.025, 0.025, "hierro", NEGRO)


def caseta(c, M):
    """Casetita de madera con techo de teja roja junto a la esquina (R0181)."""
    kx, ky = M.xy(4.6, 2.6)
    z0 = M.z(kx, ky)
    ux, uy = M.u
    vx, vy = M.v
    for su in (-0.8, 0.8):
        for sv in (-0.6, 0.6):
            c.cilindro(kx + ux * su + vx * sv, ky + uy * su + vy * sv, z0, z0 + 2.3, 0.05, "madera", "#5a3b26", lados=6)
    c.caja_ejes((kx, ky, z0 + 0.5), (ux, uy, 0), (vx, vy, 0), (0, 0, 1), 1.7, 1.3, 1.0, "madera", "#6e4a2e")
    a = 0.5
    cumbre = z0 + 2.95
    for s in (-1, 1):                                                                # techo a dos aguas
        e2 = (s * vx * math.cos(a), s * vy * math.cos(a), -math.sin(a))
        nrm = (uy * e2[2], -ux * e2[2], ux * e2[1] - uy * e2[0])
        c.caja_ejes((kx + vx * s * 0.6 * math.cos(a), ky + vy * s * 0.6 * math.cos(a), cumbre - 0.6 * math.sin(a)),
                    (ux, uy, 0), e2, nrm, 2.4, 1.3, 0.08, "teja", "#a8432f")
    c.caja_ejes((kx, ky, cumbre), (ux, uy, 0), (vx, vy, 0), (0, 0, 1), 2.4, 0.18, 0.12, "teja", "#963a28")


def escultura(c, M):
    x, y = M.xy(*ESCULTURA)
    z = M.z(x, y)
    for r, h0, h1, col in ((1.4, 0.0, 0.35, "#bfae96"), (0.9, 0.35, 2.0, "#cbbba3"), (1.05, 2.0, 2.2, "#d4c5ad")):
        pts = [(x + r * math.cos(t), y + r * math.sin(t)) for t in [k * math.tau / 8 + math.pi / 8 for k in range(8)]]
        c.prisma(pts, z + h0, z + h1, "piedra", col, tapa=True)
    c.cilindro(x, y, z + 2.2, z + 3.2, 0.32, "metal", "#4f4e47", lados=8, radio_arriba=0.24)
    c.esfera(x, y, z + 3.45, 0.26, "metal", "#4f4e47", segmentos=8)


def mobiliario(c, M):
    """Bancos frente a los canteros, a los dos lados del sendero central y en el pasaje, y faroles negros."""
    ang = math.atan2(M.u[1], M.u[0])
    for u0, u1 in TRAMOS_U:
        for uu in ((u0 + u1) / 2 - 2.2, (u0 + u1) / 2 + 2.2) if u1 - u0 > 7 else ((u0 + u1) / 2,):
            for vv, a in ((11.6, ang + math.pi), (13.4, ang)):                       # mirando al sendero
                x, y = M.xy(uu, vv)
                banco(c, x, y, M.z(x, y), a)
    for uu in (10.0, 24.5, 34.0, 48.0):                                              # pasaje: bancos contra el cantero
        x, y = M.xy(uu, 20.1)
        banco(c, x, y, M.z(x, y), ang)
    for uu, vv in ((18.8, 12.5), (30.3, 12.5), (40.7 - 4.0, 10.6), (40.7 + 4.0, 14.4), (5.0, 12.5), (53.0, 12.5),
                   (18.8, 3.0), (30.3, 3.0), (18.8, 21.0), (30.3, 21.0), (44.5, 21.0)):
        x, y = M.xy(uu, vv)
        farol_poste(c, x, y, M.z(x, y), alto=4.2)


def construir(col, pol, osm=None):
    rnd = random.Random("plazuela-cochabamba-2")
    M = Marco(pol)
    c = Constructor("AMP_S_plazuela_cochabamba")
    piso(c, M)
    for v0, v1 in HILERAS:
        for u0, u1 in TRAMOS_U:
            cantero(c, M, u0, u1, v0, v1, rnd)
    borde(c, M)
    gradas_esquina(c, M)
    for u, v in ARBOLES:
        en_cantero = any(u0 + 0.5 < u < u1 - 0.5 and v0 + 0.5 < v < v1 - 0.5 for v0, v1 in HILERAS for u0, u1 in TRAMOS_U)
        arbol(c, M, u, v, rnd, not en_cantero)
    from arboles_catalogo import poner
    for (u, v), esp in PALMERAS:
        x, y = M.xy(u, v)
        if esp == "palmera_alta":
            poner(c, esp, x, y, M.z(x, y) - 0.05, 14.0, semilla=rnd.randint(0, 9999))
        else:                                                                        # canarias de copa grande
            poner(c, esp, x, y, M.z(x, y) - 0.05, rnd.uniform(12.5, 14.0), semilla=rnd.randint(0, 9999), ancho=1.35,
                  encalado=1.3)
    caseta(c, M)
    escultura(c, M)
    mobiliario(c, M)
    c.objeto(col)
    return M
