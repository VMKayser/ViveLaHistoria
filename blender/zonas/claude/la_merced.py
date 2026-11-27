"""Templo de La Merced sobre la Calle Pérez, frente a la Plazuela Cochabamba (R0182, R0184, R0185), rehecho desde cero el
2026-11-24 con las fotos del usuario a resolución completa.

Todo va sobre la cara que mira a la plazuela; d = distancia desde la esquina del cruce (la función S de AMP_S la pasa a
la s de la fachada).
- 0–9,2 m: muro de cal liso (alto 11,5 m), ventana alta de arco con cuarterones a d = 5,5 y ventana chica de arco a
  d = 4,6 abajo; zócalo descascarado beige-gris de ~1,3 m con manchas; cornisa simple.
- Torre detrás del muro, centrada en d = 7: fuste que se angosta de 4,0 a 3,0 m hasta 20,5 m, cornisa, campanario con
  un vano en arco por cara y la campana, cornisa con pináculos en las esquinas, cuerpo alto chico con vano en arco y
  pináculos, cupulín y cruz (≈ 29 m).
- 9,2–15,6 m: portada blanca con molduras cremas: dos pares de pilastras sobre basas altas, puerta en arco (2,7 m de
  luz, clave a 5,5 m) con reja negra, impostas, entablamento a 7,4 m, cuerpo alto con nicho enmarcado y volutas,
  frontón mixtilíneo con tres pináculos de bola; dos gradas de piedra.
- 16 m en adelante: el convento (Universidad Católica), de dos plantas con balcones de hierro y alero de canes.
"""
import math

import colon_cuadra as cc_
from kit import altura_suelo
from kit import arquitectura as A_

CAL = "#f4f1ea"
CREMA = "#d8c39c"
MOLD = "#f7f4ee"
ZOCALO = "#d6ccb8"
MANCHA = "#cbbda3"
MADERA = "#4a2a1e"
NEGRO = "#151515"


def _g(f, s):
    """Suelo de la vereda en s, sobre el suelo de la fachada (la calle Pérez baja desde el cruce)."""
    p = f.punto(s, 0.0, 0.0)
    return altura_suelo(p.x, p.y) - f.suelo


def ventana_arco(f, s, h, w, alto, off):
    """Ventana de arco de medio punto con carpintería de cuarterones marrón y alféizar."""
    f.caja(s - w / 2, s + w / 2, h + off, h + alto + off, 0.02, 0.03, "vidrio", "#2a2a28")
    f.timpano_arco(s, w / 2, h + alto + off, 0.03, "vidrio", "#2a2a28")
    for k in (-w / 2 + 0.05, 0.0, w / 2 - 0.05):
        f.caja(s + k - 0.04, s + k + 0.04, h + off, h + alto + off, 0.03, 0.07, "marco_ventana", MADERA)
    for j in range(1, 4):
        f.caja(s - w / 2, s + w / 2, h + alto * j / 4 + off, h + alto * j / 4 + 0.04 + off, 0.03, 0.07, "marco_ventana", MADERA)
    f.arco(s, w / 2, 0.08, h + alto + off, 0.03, 0.08, "marco_ventana", MADERA, segmentos=10)
    f.caja(s - w / 2 - 0.15, s + w / 2 + 0.15, h - 0.12 + off, h + off, 0.0, 0.12, "moldura", MOLD)


def muro_esquina(f, S, off, ALTO, desde):
    a, b = sorted((S(0.0), S(9.2)))
    g = _g(f, (a + b) / 2)
    f.caja(a, b, desde, 1.3 + g, 0.0, 0.05, "zocalo_piedra", ZOCALO)                # zócalo descascarado (1,3 m sobre la vereda)
    for d0, d1, h1 in ((3.1, 3.7, 1.55), (6.4, 7.6, 1.75)):                     # descascarados (R0184)
        s0, s1 = sorted((S(d0), S(d1)))
        f.caja(s0, s1, 0.2 + g, h1 + g, 0.05, 0.06, "zocalo_piedra", MANCHA)
    ventana_arco(f, S(5.5), 7.4, 1.4, 1.7, _g(f, S(5.5)))
    ventana_arco(f, S(4.6), 2.5, 1.0, 1.2, _g(f, S(4.6)))
    f.caja(a, b, ALTO - 0.4 + off, ALTO - 0.15 + off, 0.0, 0.18, "moldura", MOLD)      # cornisa
    f.caja(a, b, ALTO - 0.15 + off, ALTO + off, 0.0, 0.3, "moldura", "#efebe2")


def torre(c, f, S, off, ALTO):
    """Torre blanca de la esquina (R0182, R0184): fuste que se angosta, campanario, cuerpo alto y cupulín."""
    p = f.punto(S(7.0), ALTO + off, -2.3)
    z0 = f.suelo + ALTO + off - 0.3
    rot = math.atan2(f.u.y, f.u.x) + math.pi / 4
    piezas = [(0.0, 9.3, 4.0, 3.0), (9.3, 9.65, 3.4, 3.4), (9.65, 13.2, 3.0, 3.0), (13.2, 13.6, 3.5, 3.5),
              (13.6, 15.8, 2.2, 2.2), (15.8, 16.1, 2.6, 2.6)]
    for h0, h1, w0, w1 in piezas:
        _prisma4(c, p.x, p.y, z0 + h0, z0 + h1, w0, w1, rot, "muro" if w0 < 3.3 or h1 - h0 > 1 else "moldura",
                 CAL if h1 - h0 > 1 else MOLD)
    # vanos en arco del campanario (uno por cara) y del cuerpo alto
    for k in range(4):
        ang = math.atan2(f.u.y, f.u.x) + k * math.pi / 2
        ox, oy = math.cos(ang), math.sin(ang)
        for (hc, w, alto_, ap) in ((10.2, 1.2, 2.0, 1.51), (14.0, 0.7, 1.1, 1.11)):
            cx, cy = p.x + ox * ap, p.y + oy * ap
            c.caja_ejes((cx, cy, z0 + hc + alto_ / 2), (-oy, ox, 0), (ox, oy, 0), (0, 0, 1), w, 0.03, alto_, "madera", "#2a2622")
            for j in range(5):
                t = math.pi * (j + 0.5) / 5
                c.caja_ejes((cx - oy * w / 2 * math.cos(t), cy + ox * w / 2 * math.cos(t), z0 + hc + alto_ + w / 4 * math.sin(t)),
                            (-oy, ox, 0), (ox, oy, 0), (0, 0, 1), w / 5 + 0.02, 0.03, w / 2 * math.sin(t) + 0.02, "madera",
                            "#2a2622")
        for (hz, r) in ((13.6, 1.6), (16.1, 1.2)):                              # pináculos de las esquinas
            ang2 = ang + math.pi / 4
            q = (p.x + math.cos(ang2) * r * math.sqrt(2), p.y + math.sin(ang2) * r * math.sqrt(2))
            c.cilindro(q[0], q[1], z0 + hz, z0 + hz + 0.35, 0.16, "moldura", MOLD, lados=6)
            c.esfera(q[0], q[1], z0 + hz + 0.5, 0.15, "moldura", MOLD, segmentos=6)
            c.cilindro(q[0], q[1], z0 + hz + 0.6, z0 + hz + 0.95, 0.05, "moldura", MOLD, lados=6, radio_arriba=0.01)
    q = f.punto(S(7.0), 10.8 + ALTO + off - 0.3, -2.3)
    c.cilindro(q.x, q.y, q.z - 0.7, q.z, 0.45, "metal", "#5e5236", lados=10, radio_arriba=0.22)    # campana
    zc = z0 + 16.1
    c.cilindro(p.x, p.y, zc, zc + 0.9, 1.0, "muro", CAL, lados=8, radio_arriba=0.25)              # cupulín
    c.esfera(p.x, p.y, zc + 1.05, 0.2, "moldura", MOLD, segmentos=8)
    c.caja(p.x - 0.04, p.y - 0.04, zc + 1.2, p.x + 0.04, p.y + 0.04, zc + 2.2, "hierro", "#2f2b28")
    c.caja_ejes((p.x, p.y, zc + 1.85), (f.u.x, f.u.y, 0), (f.n.x, f.n.y, 0), (0, 0, 1), 0.6, 0.06, 0.06, "hierro", "#2f2b28")


def _prisma4(c, x, y, z0, z1, w0, w1, rot, rol, color):
    """Prisma cuadrado (que puede angostarse) alineado con la fachada."""
    pts0 = [(x + w0 / math.sqrt(2) * math.cos(rot + k * math.pi / 2), y + w0 / math.sqrt(2) * math.sin(rot + k * math.pi / 2))
            for k in range(4)]
    if abs(w0 - w1) < 1e-6:
        c.prisma(pts0, z0, z1, rol, color, tapa=True)
        return
    pts1 = [(x + w1 / math.sqrt(2) * math.cos(rot + k * math.pi / 2), y + w1 / math.sqrt(2) * math.sin(rot + k * math.pi / 2))
            for k in range(4)]
    for k in range(4):
        a0, b0, a1, b1 = pts0[k], pts0[(k + 1) % 4], pts1[k], pts1[(k + 1) % 4]
        c.poligono([(a0[0], a0[1], z0), (b0[0], b0[1], z0), (b1[0], b1[1], z1), (a1[0], a1[1], z1)], rol, color)
    c.poligono([(p[0], p[1], z1) for p in pts1], rol, color)


def portada(c, f, S, off):
    """Portada (R0184, R0185): pilastras pareadas, arco con reja, entablamento, cuerpo alto con nicho y frontón."""
    sm = S(12.4)
    off = _g(f, sm)                                                              # alturas desde la vereda de la portada
    f.caja(sm - 3.2, sm + 3.2, -0.5, 7.4 + off, 0.0, 0.15, "muro", CAL)         # cuerpo
    for a_, b_ in ((sm - 3.2, sm - 1.62), (sm + 1.62, sm + 3.2)):                # basa, sin tapar la puerta
        f.caja(a_, b_, -0.5, 1.3 + off, 0.15, 0.2, "zocalo_piedra", ZOCALO)
    r, hs = 1.35, 4.15 + off
    f.caja(sm - r, sm + r, -0.3, hs, 0.12, 0.14, "madera", "#1c1c1b")                  # puerta y reja
    f.timpano_arco(sm, r, hs, 0.14, "madera", "#1c1c1b")
    k = sm - r + 0.06
    while k < sm + r:
        f.caja(k - 0.015, k + 0.015, 0.0, hs + 0.2, 0.16, 0.19, "hierro", NEGRO)
        k += 0.14
    for hh in (1.0, 2.2, 3.4):
        f.caja(sm - r, sm + r, hh + off, hh + 0.04 + off, 0.16, 0.19, "hierro", NEGRO)
    for j in range(9):                                                            # abanico de la reja
        t = math.pi * (j + 0.5) / 9
        f.caja(sm - math.cos(t) * r * 0.5 - 0.015, sm - math.cos(t) * r * 0.5 + 0.015, hs, hs + math.sin(t) * r * 0.95,
               0.16, 0.19, "hierro", NEGRO)
    f.arco(sm, r, 0.25, hs, 0.12, 0.3, "moldura", CREMA, segmentos=14)                # rosca crema
    for kk in (-1, 1):
        f.caja(sm + kk * (r + 0.12) - 0.13, sm + kk * (r + 0.12) + 0.13, -0.3, hs, 0.12, 0.28, "moldura", CREMA)
        f.caja(sm + kk * (r + 0.12) - 0.22, sm + kk * (r + 0.12) + 0.22, hs - 0.25, hs, 0.12, 0.36, "moldura", CREMA)
        for sp in (2.25, 2.9):                                                    # pilastras pareadas
            x = sm + kk * sp
            f.caja(x - 0.26, x + 0.26, -0.3, 1.3 + off, 0.15, 0.55, "moldura", ZOCALO)   # basa alta
            f.caja(x - 0.3, x + 0.3, 1.3 + off, 1.45 + off, 0.15, 0.6, "moldura", CREMA)
            f.caja(x - 0.22, x + 0.22, 1.45 + off, 7.0 + off, 0.15, 0.45, "moldura", MOLD)
            f.caja(x - 0.03, x + 0.03, 1.7 + off, 6.7 + off, 0.45, 0.47, "moldura", CREMA)  # filete crema
            f.caja(x - 0.3, x + 0.3, 6.8 + off, 7.05 + off, 0.15, 0.58, "moldura", CREMA)   # capitel
    # entablamento
    f.caja(sm - 3.25, sm + 3.25, 7.05 + off, 7.35 + off, 0.15, 0.55, "moldura", MOLD)
    f.caja(sm - 3.15, sm + 3.15, 7.35 + off, 7.75 + off, 0.15, 0.45, "moldura", CAL)
    f.caja(sm - 3.35, sm + 3.35, 7.75 + off, 7.95 + off, 0.15, 0.68, "moldura", CREMA)
    # cuerpo alto: nicho enmarcado con repisa, pilastrillas y volutas
    f.caja(sm - 2.2, sm + 2.2, 7.95 + off, 10.3 + off, 0.0, 0.3, "muro", CAL)
    f.caja(sm - 0.65, sm + 0.65, 8.35 + off, 9.7 + off, 0.3, 0.32, "muro", "#e3dfd5")
    f.timpano_arco(sm, 0.65, 9.7 + off, 0.32, "muro", "#e3dfd5")
    f.arco(sm, 0.65, 0.15, 9.7 + off, 0.3, 0.45, "moldura", MOLD, segmentos=10)
    for kk in (-1, 1):
        f.caja(sm + kk * 0.82 - 0.12, sm + kk * 0.82 + 0.12, 8.2 + off, 9.7 + off, 0.3, 0.48, "moldura", MOLD)
        f.caja(sm + kk * 1.75 - 0.15, sm + kk * 1.75 + 0.15, 7.95 + off, 10.1 + off, 0.3, 0.5, "moldura", MOLD)
        f.arco(sm + kk * 2.45, 0.35, 0.14, 8.25 + off, 0.15, 0.4, "moldura", MOLD, segmentos=6)   # volutas
    f.caja(sm - 1.0, sm + 1.0, 8.05 + off, 8.3 + off, 0.3, 0.7, "moldura", CREMA)                 # repisa del nicho
    # frontón mixtilíneo
    for j in range(13):
        t = j / 12
        x0 = sm - 2.6 + 5.2 * t
        hh = 10.3 + 0.35 * math.sin(math.pi * t) + 0.55 * max(0.0, math.cos((t - 0.5) * math.pi * 2.6)) ** 2
        f.caja(x0 - 0.22, x0 + 0.22, 10.15 + off, hh + 0.2 + off, 0.0, 0.32, "muro", CAL)
        f.caja(x0 - 0.24, x0 + 0.24, hh + 0.2 + off, hh + 0.36 + off, 0.0, 0.42, "moldura", MOLD)
    for dx, hh in ((-2.9, 7.95), (2.9, 7.95), (-1.75, 10.3), (1.75, 10.3), (0.0, 11.3)):  # pináculos de bola
        q = f.punto(sm + dx, hh + off, 0.3)
        c.caja(q.x - 0.2, q.y - 0.2, q.z, q.x + 0.2, q.y + 0.2, q.z + 0.35, "moldura", MOLD)
        c.cilindro(q.x, q.y, q.z + 0.35, q.z + 0.75, 0.14, "moldura", MOLD, lados=8, radio_arriba=0.08)
        c.esfera(q.x, q.y, q.z + 0.9, 0.16, "moldura", MOLD, segmentos=8)
        c.cilindro(q.x, q.y, q.z + 1.03, q.z + 1.35, 0.05, "moldura", MOLD, lados=6, radio_arriba=0.01)
    for j in range(2):                                                            # gradas
        f.caja(sm - 1.9 + 0.2 * j, sm + 1.9 - 0.2 * j, -0.5, 0.15 * (2 - j) + off, 0.15, 0.15 + 0.38 * (2 - j),
               "piedra", "#a59c8e")


def convento(c, f, Sc, off, Lc, ALTO_CONV):
    """Convento (R0182, R0185): dos plantas, balcones de hierro arriba, puertas de arco y ventanas con reja abajo."""
    fc = cc_._Frente(f)
    d, k = 18.0, 0
    while d < Lc - 1.5:
        sc_ = Sc(d)
        cc_.puerta_ventana(fc, sc_, 4.4 + off, ancho=1.0, alto=2.1, marco="#f6f2ea", carpinteria="#6a2a20", guardapolvo=False)
        cc_.balcon_forjado(fc, sc_, 4.4 + off, ancho=1.4, vuelo=0.4, losa="#f6f2ea", menulas=2)
        if k % 2 == 0:
            fc.caja(sc_ - 0.6, sc_ + 0.6, 0.0, 2.2 + off, -0.12, -0.04, "madera", MADERA)
            fc.timpano_arco(sc_, 0.6, 2.2 + off, -0.04, "madera", MADERA)
        else:
            cc_.ventana_recta(fc, sc_, 1.1 + off, 0.9, 1.6, marco="#f6f2ea", reja=True)
        d += 4.0
        k += 1
    A_.alero_tejas(f, ALTO_CONV + off, vuelo=0.55, s0=min(Sc(16.0), Sc(Lc)), s1=max(Sc(16.0), Sc(Lc)), canes=True)


def fachada(c, f, S, off, ALTO, ALTO_CONV, desde):
    muro_esquina(f, S, off, ALTO, desde)
    torre(c, f, S, off, ALTO)
    portada(c, f, S, off)
    convento(c, f, S, off, f.largo, ALTO_CONV)
