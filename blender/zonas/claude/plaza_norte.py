"""Frente NE de la Plaza 25 de Mayo (mitad de claude) — correcciones del usuario R0001–R0012 (2026-11-12).

El lienzo trae aquí pocas huellas mal ubicadas (M040, M042, M046 y el frente de M048) y entre ellas la BASE metía
casas genéricas. Las fotos de referencia muestran OCHO edificios seguidos, de la esquina NO a la esquina SE:

  t (m)     edificio (fotos)                       qué tiene
  107–131   B1 palacio blanco (R0001)              3 plantas, 7 vanos; PB comercial; P1 con frontones alternos y
                                                   balconcillos de balaustres; P2 con balaustres; cornisa con canes y
                                                   balaustrada con pedestales y remates
  92–107    B2 blanco de carpintería oscura (R0002) 3 plantas; mirador en P1; frontón central en el remate
  84–92     B3 angosto con cartela (R0003)         3 plantas; balcón curvo al centro; remate con cartela redonda
  68–84     B4 blanco de 2 plantas altas (R0004)   frontoncitos sobre las ventanas, mirador central, balaustrada,
                                                   portón en arco
  46–68     B5 de sillería rosada (R0005, R0007)   3 plantas, 7 vanos, balcones de hierro, frontones curvos en P1,
                                                   portones en arco, balaustrada con pedestales
  30–46     B6 blanco con molduras gris azuladas   2 plantas; dos frontones en el remate con tímpano gris; marcos
            (R0007, R0008)                         grises, balcones con macetas; zócalo de piedra
  20–30     B7 blanco con mirador (R0008, R0010)   2 plantas; mirador a la izquierda; cornisa con dentellones
  0–20      B8 banco de la esquina (R0010, R0011)  2 plantas; PB en arcos; P1 ventanas en arco con guardapolvo
                                                   ornamental, balcones de hierro, balcón largo en la esquina

t = 0 en el extremo SE del eje de la calzada de la plaza (reparto/calles_reales.json), creciendo hacia el NO.
La línea de fachadas está a ancho/2 del tramo recto del eje. Árboles podados en paraguas en la vereda.

Uso: cada script de manzana llama frente_plaza(col, t0, t1) y construye solo los edificios cuyo centro cae en
[t0, t1); `en_franja(x, y)` dice si un punto del lienzo queda dentro de la franja que ahora ocupa este frente.
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit import *  # noqa: E402,F403
from kit import arquitectura as A  # noqa: E402
from kit.datos import RAIZ, recortar_a_calles  # noqa: E402
from piezas_claude import (arbol_paraguas, fronton, guardapolvo, lado_virtual, mensula, mirador,  # noqa: E402
                           suelo_huella, techo_auto)

_c = [c for c in json.load(open(os.path.join(RAIZ, "reparto", "calles_reales.json")))["calles"]
      if c["nombre"] == "Plaza 25 de Mayo" and abs(c["eje"][0][0] + 90.56) < 3 and abs(c["eje"][0][1] + 201.27) < 3][0]
_a, _b = _c["eje"][0], _c["eje"][-1]
_L = math.hypot(_b[0] - _a[0], _b[1] - _a[1])
U = ((_b[0] - _a[0]) / _L, (_b[1] - _a[1]) / _L)       # hacia el NO
NP = (-U[1], U[0])                                     # hacia la plaza
_tramo = sorted((p[0] - _a[0]) * NP[0] + (p[1] - _a[1]) * NP[1] for p in _c["eje"][5:-5])
D_FACHADA = _tramo[len(_tramo) // 2] - _c["ancho"] / 2  # línea de fachadas (d < 0: lado de los edificios)
VEREDA = _c["vereda"]
FONDO = 15.0                                           # fondo de los cuerpos que dan a la plaza


def P(t, d=0.0):
    """Punto a lo largo del frente: t sobre la línea de fachadas, d hacia la plaza (negativo = adentro)."""
    return (_a[0] + U[0] * t + NP[0] * (D_FACHADA + d), _a[1] + U[1] * t + NP[1] * (D_FACHADA + d))


def en_franja(x, y, margen=0.5):
    t = (x - _a[0]) * U[0] + (y - _a[1]) * U[1]
    d = (x - _a[0]) * NP[0] + (y - _a[1]) * NP[1] - D_FACHADA
    return -3 < t < _L + 3 and -FONDO - margen < d < 6


# ---------------------------------------------------------------------------------------------- piezas


BLANCO = "#f5f3ee"
GRIS_AZ = "#7f8b98"
SILLERIA = "#dcbfa6"
SILLERIA_J = "#c9a88f"
MADERA = "#5a3324"
CARP_OSC = "#3b3f46"


def balaustrada(f, s0, s1, h, alto=0.95, color=BLANCO, pedestal_cada=3.2, remates="urna", d=-0.05):
    """Pretil de balaustres con pedestales y remates (urnas o bolas)."""
    f.caja(s0, s1, h, h + 0.18, d - 0.3, d, "moldura", color)
    f.caja(s0 - 0.05, s1 + 0.05, h + alto - 0.15, h + alto, d - 0.33, d + 0.03, "moldura", color)
    k = s0 + 0.2
    while k < s1 - 0.1:
        f.cilindro_vertical(k, h + 0.18, h + alto - 0.15, d - 0.15, 0.07, "moldura", color, lados=6)
        k += 0.28
    n = max(1, round((s1 - s0) / pedestal_cada))
    for i in range(n + 1):
        sp = s0 + (s1 - s0) * i / n
        sp = min(max(sp, s0 + 0.25), s1 - 0.25)
        f.caja(sp - 0.25, sp + 0.25, h, h + alto + 0.1, d - 0.35, d + 0.05, "moldura", color)
        if remates == "urna":
            f.cilindro_vertical(sp, h + alto + 0.1, h + alto + 0.3, d - 0.15, 0.1, "moldura", color, lados=8)
            f.esfera(sp, h + alto + 0.48, d - 0.15, 0.2, "moldura", color)
            f.cilindro_vertical(sp, h + alto + 0.62, h + alto + 0.85, d - 0.15, 0.05, "moldura", color, lados=6)
        elif remates == "bola":
            f.esfera(sp, h + alto + 0.32, d - 0.15, 0.2, "moldura", color)


def cornisa_canes(f, s0, s1, h, color=BLANCO, vuelo=0.5):
    """Cornisa con canecillos (modillones) debajo."""
    f.caja(s0 - 0.1, s1 + 0.1, h - 0.15, h + 0.1, 0.0, vuelo, "moldura", color)
    f.caja(s0 - 0.05, s1 + 0.05, h - 0.4, h - 0.15, 0.0, vuelo * 0.45, "moldura", color)
    k = s0 + 0.2
    while k < s1 - 0.1:
        f.caja(k - 0.06, k + 0.06, h - 0.42, h - 0.15, 0.0, vuelo * 0.85, "moldura", color)
        k += 0.55


def dentellones(f, s0, s1, h, color=BLANCO):
    f.caja(s0 - 0.08, s1 + 0.08, h, h + 0.3, 0.0, 0.42, "moldura", color)
    k = s0 + 0.1
    while k < s1 - 0.05:
        f.caja(k - 0.05, k + 0.05, h - 0.16, h, 0.0, 0.2, "moldura", color)
        k += 0.22
    f.caja(s0, s1, h - 0.3, h - 0.16, 0.0, 0.12, "moldura", color)


def fronton_curvo(f, s, h, ancho, color=BLANCO, d=0.04):
    """Frontón segmental (arco rebajado) sobre una ventana."""
    r = ancho * 0.75
    f.caja(s - ancho / 2 - 0.08, s + ancho / 2 + 0.08, h - 0.1, h + 0.02, 0.0, 0.16, "moldura", color)
    seg = 7
    a0 = math.asin(min(1.0, (ancho / 2 + 0.05) / r))
    hc = h - r * math.cos(a0)
    for k in range(seg):
        x0 = -a0 + 2 * a0 * k / seg
        x1 = -a0 + 2 * a0 * (k + 1) / seg
        sa, sb = s + r * math.sin(x0), s + r * math.sin(x1)
        ha, hb = hc + r * math.cos(x0), hc + r * math.cos(x1)
        p = [f.punto(sa, ha - 0.02, d), f.punto(sb, hb - 0.02, d), f.punto(sb, hb + 0.14, d), f.punto(sa, ha + 0.14, d)]
        f.c.poligono(p, "moldura", color, grosor=0.14, normal_extrusion=tuple(f.n))


def balconcillo_balaustres(f, s, h, ancho, color=BLANCO):
    """Balcón de piedra corto con balaustres (P1 y P2 del palacio B1)."""
    s0, s1 = s - ancho / 2 - 0.2, s + ancho / 2 + 0.2
    f.caja(s0, s1, h - 0.18, h, 0.0, 0.45, "piedra", color)
    for k in range(int((s1 - s0) / 0.24)):
        f.cilindro_vertical(s0 + 0.12 + k * 0.24, h, h + 0.75, 0.36, 0.055, "moldura", color, lados=6)
    f.caja(s0, s1, h + 0.75, h + 0.88, 0.25, 0.47, "moldura", color)
    for x in (s0, s1 - 0.12):
        f.caja(x, x + 0.12, h, h + 0.88, 0.0, 0.45, "moldura", color)
    for dm in (s0 + 0.25, s1 - 0.25):
        mensula(f, dm, h - 0.18, 0.4, color)


def vano(f, s, h, ancho, alto, carp=MADERA, moldura=BLANCO, arco=False, balcon=False, reja=False):
    A.ventana(f, s, h, ancho=ancho, alto=alto, arco=arco, reja=reja, balcon="hierro" if balcon else None,
              moldura="moldura", color_moldura=moldura, carpinteria="marco_ventana", color_carpinteria=carp)
    # postigos interiores abiertos (madera oscura dentro del vano): las ventanas de la plaza se ven oscuras
    f.caja(s - ancho / 2 + 0.08, s + ancho / 2 - 0.08, h + 0.08, h + alto - 0.08, -0.02, 0.0, "madera", carp)


def portal(f, s, ancho, alto, color=MADERA, moldura=BLANCO, arco=True):
    A.puerta(f, s, ancho=ancho, alto=alto, arco=arco, color=color, moldura="moldura", color_moldura=moldura)


def vitrina(f, s, ancho, alto, moldura=BLANCO, arco=False):
    """Local comercial: vidriera alta con marco, en un vano de la planta baja."""
    s0, s1 = s - ancho / 2, s + ancho / 2
    f.caja(s0 - 0.2, s0, 0.0, alto, 0.0, 0.1, "moldura", moldura)
    f.caja(s1, s1 + 0.2, 0.0, alto, 0.0, 0.1, "moldura", moldura)
    f.caja(s0, s1, 0.0, 0.5, 0.0, 0.05, "marco_ventana", "#3a3a3a")
    f.caja(s0, s1, 0.5, alto, 0.0, 0.01, "vidrio")
    for x in (s0, (s0 + s1) / 2 - 0.03, s1 - 0.06):
        f.caja(x, x + 0.06, 0.5, alto, 0.0, 0.04, "marco_ventana", "#3a3a3a")
    f.caja(s0, s1, alto - 0.6, alto - 0.55, 0.0, 0.04, "marco_ventana", "#3a3a3a")
    if arco:
        f.arco(s, ancho / 2, 0.2, alto, 0.0, 0.1, "moldura", moldura, segmentos=10)
        f.timpano_arco(s, ancho / 2, alto, 0.01, "vidrio")
    else:
        f.caja(s0 - 0.25, s1 + 0.25, alto, alto + 0.25, 0.0, 0.14, "moldura", moldura)


def cuerpo(nombre, t0, t1, alto, color=BLANCO, fondo=FONDO, col=None):
    """Volumen del edificio (recortado a las calles reales) y su fachada a la plaza."""
    h = [P(t0, 0.0), P(t1, 0.0), P(t1, -fondo), P(t0, -fondo)]
    h = recortar_a_calles(h, area_min=10) or h
    # la fachada va sobre el lado REAL del volumen recortado que mira a la plaza (auditoría: cerca de las esquinas la
    # calzada se curva y en las esquinas manda la calle transversal; con la recta fija invadía hasta 5 m)
    from kit.datos import lados as _lados
    cand = [l for l in _lados(h) if l["normal"][0] * NP[0] + l["normal"][1] * NP[1] > 0.9 and l["largo"] > 3]
    lado_f = max(cand, key=lambda l: l["largo"]) if cand else lado_virtual(P(t0), P(t1), NP)
    if (lado_f["b"][0] - lado_f["a"][0]) * U[0] + (lado_f["b"][1] - lado_f["a"][1]) * U[1] < 0:
        lado_f = lado_virtual(lado_f["b"], lado_f["a"], NP)   # s crece hacia el NO, como en el diseño
    zb, zr = suelo_huella(h)
    c = Constructor(nombre)
    c.huella_cuerpo = h
    c.prisma(h, zb - 0.6, zr + alto, "muro", color, tapa=False)
    techo_auto(c, h, zr + alto - 0.02, zpatio=zb, muro=("muro", color))
    f = Fachada(c, lado_f, altura_suelo((lado_f["a"][0] + lado_f["b"][0]) / 2, (lado_f["a"][1] + lado_f["b"][1]) / 2))
    off = zr - f.suelo
    return c, f, off, zb


def zocalo_liso(f, alto, color, off):
    f.caja(0.0, f.largo, -0.6, alto + off, 0.0, 0.08, "zocalo_piedra", color)


# ---------------------------------------------------------------------------------------------- edificios


def b1_palacio(col):
    t0, t1 = 107.0, 131.0
    c, f, off, zb = cuerpo("PN_B1_palacio", t0, t1, 16.2)
    L = f.largo
    n = 7
    vs = [L * (k + 0.5) / n for k in range(n)]
    zocalo_liso(f, 0.5, "#cfc8bd", off)
    for k, s in enumerate(vs):                                   # PB comercial con vanos altos
        if k == 3:
            portal(f, s, 2.0, 4.0 + off)
        else:
            vitrina(f, s, 2.1, 4.1 + off)
    A.imposta(f, 5.2 + off, alto=0.3, vuelo=0.15, rol="moldura", color=BLANCO)
    for k, s in enumerate(vs):                                   # P1: frontones alternos + balconcillos
        vano(f, s, 5.9 + off, 1.15, 2.4)
        balconcillo_balaustres(f, s, 5.9 + off, 1.15)
        if k % 2 == 0:
            fronton(f, s, 8.55 + off, 1.9, 0.55, color=BLANCO)
        else:
            fronton_curvo(f, s, 8.55 + off, 1.6)
    A.imposta(f, 9.9 + off, alto=0.25, vuelo=0.12, rol="moldura", color=BLANCO)
    for s in vs:                                                 # P2
        vano(f, s, 10.6 + off, 1.1, 2.2)
        balconcillo_balaustres(f, s, 10.6 + off, 1.1)
        guardapolvo(f, s, 12.95 + off, 1.1, BLANCO)
    for s in [0.25] + [(vs[i] + vs[i + 1]) / 2 for i in range(n - 1)] + [L - 0.25]:   # pilastras de orden gigante
        A.pilastra(f, s, 5.4 + off, 15.4 + off, ancho=0.45, vuelo=0.08, rol="moldura", color=BLANCO)
    cornisa_canes(f, 0.0, L, 15.9 + off)
    balaustrada(f, 0.0, L, 16.0 + off, pedestal_cada=L / 8)
    # vuelta a la calle Arce (sección piloto, 2026-11-14: desde Arce se veía un muro liso de 16 m): mismo orden
    from kit.datos import lados as _lados
    for l in _lados(c.huella_cuerpo):
        if not l["a_calle"] or "Arce" not in l["calle"] or l["largo"] < 4:
            continue
        fa = Fachada(c, l, altura_suelo((l["a"][0] + l["b"][0]) / 2, (l["a"][1] + l["b"][1]) / 2))
        oa = off + f.suelo - fa.suelo
        La = fa.largo
        na = max(1, round(La / 3.4))
        va = [La * (k + 0.5) / na for k in range(na)]
        zocalo_liso(fa, 0.5, "#cfc8bd", oa)
        for s in va:
            vitrina(fa, s, 2.1, 4.1 + oa)
        A.imposta(fa, 5.2 + oa, alto=0.3, vuelo=0.15, rol="moldura", color=BLANCO)
        for k, s in enumerate(va):
            vano(fa, s, 5.9 + oa, 1.15, 2.4)
            balconcillo_balaustres(fa, s, 5.9 + oa, 1.15)
            if k % 2 == 0:
                fronton(fa, s, 8.55 + oa, 1.9, 0.55, color=BLANCO)
            else:
                fronton_curvo(fa, s, 8.55 + oa, 1.6)
        A.imposta(fa, 9.9 + oa, alto=0.25, vuelo=0.12, rol="moldura", color=BLANCO)
        for s in va:
            vano(fa, s, 10.6 + oa, 1.1, 2.2)
            guardapolvo(fa, s, 12.95 + oa, 1.1, BLANCO)
        for s in [0.25] + [(va[i] + va[i + 1]) / 2 for i in range(na - 1)] + [La - 0.25]:
            A.pilastra(fa, s, 5.4 + oa, 15.4 + oa, ancho=0.45, vuelo=0.08, rol="moldura", color=BLANCO)
        cornisa_canes(fa, 0.0, La, 15.9 + oa)
        balaustrada(fa, 0.0, La, 16.0 + oa, pedestal_cada=max(2.5, La / 6))
    c.objeto(col)


def b2_carpinteria_oscura(col):
    t0, t1 = 92.0, 107.0
    c, f, off, zb = cuerpo("PN_B2", t0, t1, 14.6)
    L = f.largo
    vs = [L * (k + 0.5) / 5 for k in range(5)]
    zocalo_liso(f, 0.6, "#c8c2b8", off)
    for k, s in enumerate(vs):
        if k == 2:
            portal(f, s, 1.8, 3.6 + off, arco=False)
        else:
            vitrina(f, s, 2.0, 3.8 + off)
    A.imposta(f, 4.8 + off, alto=0.25, vuelo=0.12, rol="moldura", color=BLANCO)
    for k, s in enumerate(vs):
        if k == 1:
            mirador(f, s, 5.6 + off, ancho=2.6, alto=2.4, vuelo=0.75, base=("muro", BLANCO), madera=("marco_ventana", CARP_OSC))
        else:
            vano(f, s, 5.5 + off, 1.1, 2.3, carp=CARP_OSC, balcon=k in (0, 4))
            guardapolvo(f, s, 7.95 + off, 1.1, BLANCO)
    A.imposta(f, 9.3 + off, alto=0.22, vuelo=0.1, rol="moldura", color=BLANCO)
    for s in vs:
        vano(f, s, 9.9 + off, 1.1, 2.1, carp=CARP_OSC, balcon=True)
    for s in (0.3, L - 0.3):
        A.pilastra(f, s, 4.8 + off, 14.0 + off, ancho=0.5, vuelo=0.1, rol="moldura", color=BLANCO)
    cornisa_canes(f, 0.0, L, 14.3 + off, vuelo=0.4)
    A.parapeto(f, 14.4 + off, alto=0.7, rol="muro", color=BLANCO)
    fronton(f, L / 2, 15.1 + off, 5.5, 1.6, color=BLANCO, d=0.0, grosor=0.3)        # frontón central del remate
    f.esfera(L / 2, 16.9 + off, 0.1, 0.2, "moldura", BLANCO)
    c.objeto(col)


def b3_cartela(col):
    t0, t1 = 84.0, 92.0
    c, f, off, zb = cuerpo("PN_B3", t0, t1, 14.2)
    L = f.largo
    zocalo_liso(f, 0.6, "#c8c2b8", off)
    vitrina(f, L * 0.3, 2.2, 3.8 + off)
    portal(f, L * 0.75, 1.5, 3.6 + off, arco=False)
    A.imposta(f, 4.8 + off, alto=0.22, vuelo=0.1, rol="moldura", color=BLANCO)
    vano(f, L * 0.25, 5.5 + off, 1.0, 2.3)
    vano(f, L * 0.75, 5.5 + off, 1.0, 2.3)
    vano(f, L / 2, 5.5 + off, 0.9, 2.3)                        # balcón curvo central
    q = f.punto(L / 2, 0, 0.0)
    c.cilindro(q.x, q.y, f.suelo + 5.3 + off, f.suelo + 5.5 + off, 0.9, "piedra", BLANCO, lados=14)
    c.cilindro(q.x, q.y, f.suelo + 5.5 + off, f.suelo + 6.4 + off, 0.88, "moldura", BLANCO, lados=14)
    for s in (L * 0.25, L * 0.5, L * 0.75):
        vano(f, s, 9.6 + off, 1.0, 2.2, balcon=s != L / 2)
        guardapolvo(f, s, 11.95 + off, 1.0, BLANCO)
    A.pilastra(f, 0.25, 4.8 + off, 13.6 + off, ancho=0.4, vuelo=0.08, rol="moldura", color=BLANCO)
    A.pilastra(f, L - 0.25, 4.8 + off, 13.6 + off, ancho=0.4, vuelo=0.08, rol="moldura", color=BLANCO)
    cornisa_canes(f, 0.0, L, 13.9 + off, vuelo=0.35)
    A.parapeto(f, 14.0 + off, alto=0.6, rol="muro", color=BLANCO)
    # cartela redonda con escudo, sobre el centro
    f.caja(L / 2 - 1.3, L / 2 + 1.3, 14.6 + off, 15.2 + off, -0.1, 0.15, "muro", BLANCO)
    f.arco(L / 2, 0.75, 0.3, 15.2 + off, -0.1, 0.18, "moldura", BLANCO, segmentos=12)
    f.timpano_arco(L / 2, 0.75, 15.2 + off, 0.05, "muro", BLANCO)
    f.esfera(L / 2, 15.6 + off, 0.1, 0.32, "moldura", BLANCO)
    c.objeto(col)


def b4_frontoncitos(col):
    t0, t1 = 68.0, 84.0
    c, f, off, zb = cuerpo("PN_B4", t0, t1, 11.0)
    L = f.largo
    vs = [L * (k + 0.5) / 5 for k in range(5)]
    zocalo_liso(f, 0.7, "#c8c2b8", off)
    for k, s in enumerate(vs):
        if k == 1:
            portal(f, s, 1.9, 3.9 + off, arco=True)
        else:
            vitrina(f, s, 2.2, 4.0 + off)
    A.imposta(f, 5.3 + off, alto=0.25, vuelo=0.12, rol="moldura", color=BLANCO)
    for k, s in enumerate(vs):
        if k == 2:
            mirador(f, s, 6.0 + off, ancho=2.7, alto=2.5, vuelo=0.8, base=("muro", BLANCO), madera=("marco_ventana", "#3d2c24"))
        else:
            vano(f, s, 6.0 + off, 1.1, 2.4, balcon=k in (0, 4))
            fronton(f, s, 8.65 + off, 1.8, 0.5, color=BLANCO)
    for s in [0.3] + [(vs[i] + vs[i + 1]) / 2 for i in range(4)] + [L - 0.3]:
        A.pilastra(f, s, 5.3 + off, 10.3 + off, ancho=0.4, vuelo=0.08, rol="moldura", color=BLANCO)
    cornisa_canes(f, 0.0, L, 10.7 + off, vuelo=0.4)
    balaustrada(f, 0.0, L, 10.8 + off, pedestal_cada=L / 5, remates="bola")
    c.objeto(col)


def b5_silleria(col):
    t0, t1 = 46.0, 68.0
    c, f, off, zb = cuerpo("PN_B5_silleria", t0, t1, 14.8, color=SILLERIA)
    L = f.largo
    n = 7
    vs = [L * (k + 0.5) / n for k in range(n)]
    # sillería: hiladas y juntas verticales alternas en todo el frente
    h = 0.6
    fila = 0
    while h < 14.4:
        f.caja(0.0, L, h + off, h + 0.035 + off, 0.0, 0.03, "zocalo_piedra", SILLERIA_J)
        k = 0.6 if fila % 2 else 0.0
        while k < L:
            f.caja(k, k + 0.035, h + off, h + 0.6 + off, 0.0, 0.03, "zocalo_piedra", SILLERIA_J)
            k += 1.2
        h += 0.6
        fila += 1
    f.caja(0.0, L, -0.6, 0.7 + off, 0.0, 0.1, "zocalo_piedra", "#b89277")
    for k, s in enumerate(vs):                                   # PB: portones en arco y vidrieras en arco
        if k in (1, 3, 5):
            portal(f, s, 1.8, 3.6 + off, color="#4a2a1e", moldura=SILLERIA)
        else:
            vitrina(f, s, 1.9, 3.2 + off, moldura=SILLERIA, arco=True)
    A.imposta(f, 5.0 + off, alto=0.3, vuelo=0.14, rol="piedra", color=SILLERIA)
    for s in vs:                                                 # P1: frontón curvo + balcón de hierro
        vano(f, s, 5.6 + off, 1.1, 2.4, carp="#4a2a1e", moldura=SILLERIA, balcon=True)
        fronton_curvo(f, s, 8.25 + off, 1.5, color=SILLERIA)
    A.imposta(f, 9.4 + off, alto=0.25, vuelo=0.12, rol="piedra", color=SILLERIA)
    for s in vs:                                                 # P2: balcones de hierro
        vano(f, s, 10.0 + off, 1.05, 2.2, carp="#4a2a1e", moldura=SILLERIA, balcon=True)
        guardapolvo(f, s, 12.35 + off, 1.05, SILLERIA, rol="piedra")
    cornisa_canes(f, 0.0, L, 14.6 + off, color="#e6d3c0", vuelo=0.45)
    balaustrada(f, 0.0, L, 14.7 + off, color="#e9dccd", pedestal_cada=L / 5, remates=None)
    c.objeto(col)


def b6_molduras_grises(col):
    t0, t1 = 30.0, 46.0
    c, f, off, zb = cuerpo("PN_B6", t0, t1, 9.8)
    L = f.largo
    vs = [L * (k + 0.5) / 5 for k in range(5)]
    zocalo_liso(f, 1.3, "#b9a48a", off)
    for k, s in enumerate(vs):
        if k in (0, 3):
            portal(f, s, 1.7, 3.3 + off, color=MADERA, moldura=GRIS_AZ, arco=False)
        elif k == 2:
            portal(f, s, 2.2, 3.4 + off, color="#3c3c3c", moldura=GRIS_AZ, arco=True)   # acceso con marquesina
            f.caja(s - 1.6, s + 1.6, 4.4 + off, 4.55 + off, 0.0, 0.9, "hierro")
        else:
            vitrina(f, s, 2.0, 3.4 + off, moldura=GRIS_AZ)
    f.caja(0.0, L, 4.6 + off, 4.85 + off, 0.0, 0.14, "moldura", GRIS_AZ)          # imposta gris
    for s in vs:
        vano(f, s, 5.3 + off, 1.15, 2.3, moldura=GRIS_AZ, balcon=True)
        f.caja(s - 0.8, s + 0.8, 7.75 + off, 7.95 + off, 0.0, 0.16, "moldura", GRIS_AZ)
        f.esfera(s, 8.35 + off, 0.06, 0.16, "moldura", GRIS_AZ)                    # medallón
        for dm in (-0.4, 0.4):                                                       # macetas en el balcón
            f.cilindro_vertical(s + dm, 5.3 + off, 5.55 + off, 0.4, 0.12, "teja", lados=6)
            f.esfera(s + dm, 5.7 + off, 0.4, 0.17, "flor")
    f.caja(0.0, L, 9.0 + off, 9.35 + off, 0.0, 0.35, "moldura", GRIS_AZ)          # cornisa gris
    A.parapeto(f, 9.35 + off, alto=0.6, rol="muro", color=BLANCO)
    for s in (L * 0.2, L * 0.8):                                                     # dos frontones en el remate
        fronton(f, s, 9.95 + off, 5.4, 1.4, color=BLANCO, d=0.0, grosor=0.3)
        p = [f.punto(s - 2.0, 10.1 + off, 0.31), f.punto(s + 2.0, 10.1 + off, 0.31), f.punto(s, 11.1 + off, 0.31)]
        f.c.poligono(p, "moldura", GRIS_AZ, grosor=0.02, normal_extrusion=tuple(f.n))      # tímpano gris
    c.objeto(col)


def b7_mirador(col):
    t0, t1 = 20.0, 30.0
    c, f, off, zb = cuerpo("PN_B7", t0, t1, 9.6)
    L = f.largo
    zocalo_liso(f, 0.8, "#c3b7a6", off)
    vitrina(f, L * 0.2, 2.0, 3.6 + off)
    portal(f, L * 0.5, 1.6, 3.4 + off, arco=False)
    vitrina(f, L * 0.8, 2.0, 3.6 + off)
    A.imposta(f, 4.7 + off, alto=0.2, vuelo=0.1, rol="moldura", color=BLANCO)
    mirador(f, L * 0.75, 5.4 + off, ancho=3.0, alto=2.3, vuelo=0.8, base=("muro", BLANCO), madera=("marco_ventana", "#4a3328"))
    vano(f, L * 0.42, 5.3 + off, 1.0, 2.2)
    vano(f, L * 0.18, 5.3 + off, 1.0, 2.2, balcon=True)
    dentellones(f, 0.0, L, 9.0 + off)
    A.parapeto(f, 9.3 + off, alto=0.5, rol="muro", color=BLANCO)
    c.objeto(col)


def b8_banco_esquina(col):
    t0, t1 = -2.0, 20.0
    c, f, off, zb = cuerpo("PN_B8_banco", t0, t1, 11.2)
    L = f.largo
    n = 7
    vs = [L * (k + 0.5) / n for k in range(n)]
    zocalo_liso(f, 0.6, "#c8c2b8", off)
    for k, s in enumerate(vs):                                   # PB en arcos: puertas y vidrieras
        if k == 3:
            portal(f, s, 2.0, 3.9 + off, arco=True)
        else:
            vitrina(f, s, 2.0, 3.6 + off, arco=True)
    A.imposta(f, 5.3 + off, alto=0.3, vuelo=0.14, rol="moldura", color=BLANCO)
    for k, s in enumerate(vs):                                   # P1: ventanas en arco con guardapolvo y balcón
        vano(f, s, 6.0 + off, 1.15, 2.6, arco=True, balcon=k < n - 1)
        f.arco(s, 0.75, 0.22, 8.6 + off, 0.0, 0.14, "moldura", BLANCO, segmentos=10)
        f.caja(s - 0.16, s + 0.16, 9.3 + off, 9.75 + off, 0.0, 0.18, "moldura", BLANCO)     # clave
        for dm in (-0.95, 0.95):                                                             # orejeras
            f.caja(s + dm - 0.12, s + dm + 0.12, 8.3 + off, 8.75 + off, 0.0, 0.12, "moldura", BLANCO)
    A.balcon_corrido(f, vs[-1] - 1.2, L - 0.1, 6.0 + off)       # balcón largo hacia la esquina
    for s in [0.3] + [(vs[i] + vs[i + 1]) / 2 for i in range(n - 1)] + [L - 0.3]:
        A.pilastra(f, s, 5.3 + off, 10.4 + off, ancho=0.4, vuelo=0.08, rol="moldura", color=BLANCO)
    cornisa_canes(f, 0.0, L, 10.8 + off, vuelo=0.45)
    A.parapeto(f, 10.9 + off, alto=0.6, rol="muro", color=BLANCO)
    # vuelta a la calle España (sección piloto, 2026-11-14: desde España se veía su costado liso): mismo orden
    from kit.datos import lados as _lados
    for l in _lados(c.huella_cuerpo):
        if not l["a_calle"] or "Plaza" in l["calle"] or l["largo"] < 4:
            continue
        fa = Fachada(c, l, altura_suelo((l["a"][0] + l["b"][0]) / 2, (l["a"][1] + l["b"][1]) / 2))
        oa = off + f.suelo - fa.suelo
        La = fa.largo
        na = max(1, round(La / 3.2))
        va = [La * (k + 0.5) / na for k in range(na)]
        zocalo_liso(fa, 0.6, "#c8c2b8", oa)
        for k, s in enumerate(va):
            if k == na // 2:
                portal(fa, s, 2.0, 3.9 + oa, arco=True)
            else:
                vitrina(fa, s, 2.0, 3.6 + oa, arco=True)
        A.imposta(fa, 5.3 + oa, alto=0.3, vuelo=0.14, rol="moldura", color=BLANCO)
        for s in va:
            vano(fa, s, 6.0 + oa, 1.15, 2.6, arco=True, balcon=True)
            fa.arco(s, 0.75, 0.22, 8.6 + oa, 0.0, 0.14, "moldura", BLANCO, segmentos=10)
            fa.caja(s - 0.16, s + 0.16, 9.3 + oa, 9.75 + oa, 0.0, 0.18, "moldura", BLANCO)
        for s in [0.3] + [(va[i] + va[i + 1]) / 2 for i in range(na - 1)] + [La - 0.3]:
            A.pilastra(fa, s, 5.3 + oa, 10.4 + oa, ancho=0.4, vuelo=0.08, rol="moldura", color=BLANCO)
        cornisa_canes(fa, 0.0, La, 10.8 + oa, vuelo=0.45)
        A.parapeto(fa, 10.9 + oa, alto=0.6, rol="muro", color=BLANCO)
    c.objeto(col)


EDIFICIOS = [(119.0, b1_palacio), (99.5, b2_carpinteria_oscura), (88.0, b3_cartela), (76.0, b4_frontoncitos),
             (57.0, b5_silleria), (38.0, b6_molduras_grises), (25.0, b7_mirador), (9.0, b8_banco_esquina)]


_BORDILLO = []


def _bordillo():
    """Bordillo REAL de la vereda del frente (el de la sección de la plaza, trazado.py), cargado una vez. Medido desde la
    línea de fachadas, los árboles quedaban sobre el bordillo o en la calzada: la calzada de la sección no es paralela
    a esa línea (revisión por MCP, 2026-11-24: "árboles entre la calle y la vereda")."""
    if not _BORDILLO:
        sys.path.insert(1, os.path.join(RAIZ, "blender", "secciones"))
        import trazado as T
        g = T.trazar(T.cargar_seccion("plaza_25_mayo"))
        _BORDILLO.append((g["vereda"].boundary.intersection(g["calzada"].buffer(0.05)), g["vereda"]))
    return _BORDILLO[0]


def junto_al_bordillo(x, y, retiro=0.7):
    """El punto de la vereda a `retiro` m del bordillo más cercano a (x, y)."""
    from shapely.geometry import Point
    from shapely.ops import nearest_points
    curb, vereda = _bordillo()
    p = Point(x, y)
    q = nearest_points(curb, p)[0]
    d = p.distance(q)
    if d < 1e-6 or not vereda.buffer(0.05).contains(p):
        # en la calzada o sobre el bordillo: hacia la fachada (opuesto a la plaza)
        ux, uy = -NP[0], -NP[1]
    else:
        ux, uy = (x - q.x) / d, (y - q.y) / d
    return q.x + ux * retiro, q.y + uy * retiro


def arboles(col, t0, t1, nombre):
    """Árboles podados en paraguas en la vereda, cada ~7 m (R0006, R0008, R0011)."""
    c = Constructor(nombre)
    t = 3.5 + 7.0 * math.ceil((t0 - 3.5) / 7.0)
    k = 0
    hubo = False
    while t < t1 and t < _L - 4:
        x, y = junto_al_bordillo(*P(t, VEREDA - 0.55))   # la copa no entra en los balcones del primer piso
        # copa corrida 0,7 m hacia la calle (recorrido a pie 2026-11-13: con la copa centrada se metía en la fachada)
        q0, q1 = P(t, 0.0), P(t, 1.0)
        arbol_paraguas(c, x, y, altura_suelo(x, y) + 0.18, alto=4.8, copa=3.0, semilla=int(t * 10),
                       desplazar=((q1[0] - q0[0]) * 0.7, (q1[1] - q0[1]) * 0.7))
        hubo = True
        t += 7.0
        k += 1
    if hubo:
        c.objeto(col)
    else:
        c.bm.free()


def frente_plaza(col, t0, t1, mid):
    for tc, fn in EDIFICIOS:
        if t0 <= tc < t1:
            fn(col)
    arboles(col, t0, t1, mid + "_arboles_plaza")


def filtro_franja(e):
    """Para generica.construir: quita de la huella del lienzo la franja que ahora ocupa el frente de la plaza."""
    from kit.datos import _area, _cortar_semiplano
    h = _cortar_semiplano(e["huella"], _a[0], _a[1], -NP[0], -NP[1], FONDO - D_FACHADA + 0.3)
    return h if len(h) >= 3 and abs(_area(h)) > 15 else None


def camaras_revision(ids):
    """Cámaras de las correcciones del usuario (posición del revisor → punto mirado)."""
    out = []
    for rid in ids:
        r = json.load(open(os.path.join(RAIZ, "coordinacion", "revisiones", rid, "revision.json")))
        o = r["escena"]["camara"]["lienzo"]
        m = r["escena"]["centro"]
        if not m:
            rb = math.radians(r["escena"]["camara"]["rumbo_grados"])
            m = {"x": o["x"] + math.sin(rb) * 15, "y": o["y"] + math.cos(rb) * 15, "z": o["z"] + 2}
        out.append((rid, (o["x"], o["y"], o["z"]), (m["x"], m["y"], m["z"] + 1.5)))
    return out


def script_manzana(mid, t0, t1, revisiones, vecinas=()):
    """Cuerpo común de M040/M042/M046/M048: lo del lienzo fuera de la franja con generica, más este frente."""
    from generica import construir
    construir("claude", mid, extra=lambda m, col: frente_plaza(col, t0, t1, mid), filtro_huella=filtro_franja,
              camaras=camaras_revision(revisiones), vecinas=vecinas)
