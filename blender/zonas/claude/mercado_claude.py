"""Piezas del Mercado Central (M013 frente a Junín, M021 frente a Ravelo), según las correcciones R0046–R0051:
locales ABIERTOS con mercadería y toldo de lona sobre la vereda (no vidrieras), y lunetos (ventanales de medio punto)
en la planta alta."""

import math

TOLDOS = ["#f1eee6", "#f1eee6", "#efe7d6", "#e9e2d2", "#f1eee6", "#3f6fb0", "#e8823a"]
# mercadería en tonos apagados (en la foto es un mosaico menudo, no barras de color)
MERCADERIA = ["#b9694f", "#6f8fa8", "#c9b067", "#7d9a6a", "#b98a72", "#8a7a9a", "#e2ddd2", "#a8a29a"]


def tienda(f, s0, s1, off, rnd, toldo=None, vuelo=1.9):
    """Local abierto del mercado (R0046–R0057): hueco en sombra, mostrador y estantes con mercadería menuda, cortina
    enrollada arriba y un toldo de lona clara grande e inclinado con su faldón."""
    a0, a1 = s0 + 0.2, s1 - 0.2
    # interior en sombra: 2 cm delante del muro (coplanar con él parpadeaba, R0129)
    f.caja(a0, a1, 0.0, 3.0 + off, 0.0, 0.02, "madera", "#2a2420")
    f.caja(a0, a1, 3.0 + off, 3.3 + off, 0.0, 0.12, "metal", "#9aa0a3")               # cortina enrollada
    # estantes laterales y mostrador al frente
    for sx in (a0 + 0.05, a1 - 0.45):
        f.caja(sx, sx + 0.4, 0.0, 2.3 + off, 0.0, 0.35, "madera", "#6b5444")
        for hh in (0.6, 1.1, 1.6, 2.1):
            f.caja(sx, sx + 0.4, hh + off, hh + 0.25 + off, 0.36, 0.38, "letrero", rnd.choice(MERCADERIA))
    if a1 - a0 > 2.0:
        f.caja(a0 + 0.6, a1 - 0.6, 0.0, 0.9 + off, 0.0, 0.55, "madera", "#7a5e4a")       # mostrador
        k = a0 + 0.7
        while k < a1 - 0.8:                                                             # mercadería sobre el mostrador
            w = rnd.uniform(0.15, 0.35)
            f.caja(k, k + w, 0.9 + off, 0.9 + rnd.uniform(0.1, 0.35) + off, 0.1, 0.45, "letrero", rnd.choice(MERCADERIA))
            k += w + 0.05
    col = toldo or rnd.choice(TOLDOS)
    p0, p1 = f.punto(a0 - 0.15, 3.45 + off, 0.0), f.punto(a1 + 0.15, 3.45 + off, 0.0)
    q0, q1 = f.punto(a0 - 0.15, 2.75 + off, vuelo), f.punto(a1 + 0.15, 2.75 + off, vuelo)
    f.c.poligono([p0, p1, q1, q0], "letrero", col, grosor=0.06, normal_extrusion=(0, 0, 1))
    f.caja(a0 - 0.15, a1 + 0.15, 2.4 + off, 2.78 + off, vuelo - 0.03, vuelo + 0.03, "letrero", col)    # faldón
    for sx in (a0 - 0.1, a1 + 0.1):                                                    # varillas del toldo
        f.caja(sx - 0.02, sx + 0.02, 2.75 + off, 3.45 + off, 0.0, vuelo, "metal", "#9aa0a3")


def toldo(f, s0, s1, off, rnd, toldo=None, vuelo=1.1):
    """Solo el toldo de lona con faldón y varillas, para locales de fachada sin hueco abierto (vidriera o cortina
    de casa_sencilla): sin estantes delante del muro."""
    a0, a1 = s0 + 0.2, s1 - 0.2
    col = toldo or rnd.choice(TOLDOS)
    p0, p1 = f.punto(a0 - 0.15, 3.45 + off, 0.0), f.punto(a1 + 0.15, 3.45 + off, 0.0)
    q0, q1 = f.punto(a0 - 0.15, 2.85 + off, vuelo), f.punto(a1 + 0.15, 2.85 + off, vuelo)
    f.c.poligono([p0, p1, q1, q0], "letrero", col, grosor=0.06, normal_extrusion=(0, 0, 1))
    f.caja(a0 - 0.15, a1 + 0.15, 2.55 + off, 2.88 + off, vuelo - 0.03, vuelo + 0.03, "letrero", col)    # faldón
    for sx in (a0 - 0.1, a1 + 0.1):
        f.caja(sx - 0.02, sx + 0.02, 2.85 + off, 3.45 + off, 0.0, vuelo, "metal", "#9aa0a3")


def luneto(f, s, off, r=1.35, h=4.75, blanco="#f5f4f0"):
    h = h + off
    f.timpano_arco(s, r, h, 0.02, "vidrio", "#33505a")
    f.arco(s, r, 0.16, h, 0.0, 0.08, "moldura", blanco, segmentos=12)
    for ang in (0.5, 1.05, 1.57, 2.1, 2.65):
        f.caja(s + math.cos(ang) * r * 0.5 - 0.025, s + math.cos(ang) * r * 0.5 + 0.025, h, h + math.sin(ang) * r - 0.05,
               0.0, 0.05, "marco_ventana", "#e9ecef")
    f.caja(s - r - 0.1, s + r + 0.1, h - 0.15, h, 0.0, 0.14, "moldura", blanco)
