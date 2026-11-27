"""AMP_S — ampliación sur (fuera de la zona original), revisiones de prioridad alta del usuario (2026-11-13):

1. ESQUINA SUR del cruce Pantaleón Dalence × Nicolás Ortiz (R0096–R0098): casona colonial de 2 plantas, blanca, con
   pilastras y marcos color crema, zócalo de sillería ocre, ochava con un GRAN MIRADOR de madera rojiza que dobla la
   esquina sobre ménsulas y una columna; balcones de hierro en el piso alto; cornisa con remates.
2. TEMPLO DE SAN FELIPE NERI (R0099–R0102): huella de OSM; los dos campanarios de OSM están en el extremo SE, que da
   al cruce de Colón / Pérez / Azurduy / Nicolás Ortiz. Fachada de sillería rojiza (hiladas rosa y ocre) con portada
   en arco y reja verde, ventana alta, cornisa y remate mixtilíneo; DOS TORRES BLANCAS altas con campanarios en arco,
   balaustrada y cupulines; espadaña con campana al centro. Naves de piedra con contrafuertes y cúpula blanca. ATRIO
   delante con muro bajo de sillería, balaustrada de piedra, pilares con pináculos y reja de hierro.
   Convento de San Felipe Neri (OSM) blanco, de 2 plantas.
3. PLAZUELA COCHABAMBA (R0103–R0104): huella de OSM al otro lado de Colón: senderos de los footway de OSM, canteros con
   reja baja de hierro sobre bordillo de piedra, palmeras canarias altas junto al templo, árboles podados en paraguas
   con el tronco encalado (puntos de OSM), faroles, bancos y la escultura.
4. ENTORNO (2026-11-14, sin relleno genérico): lo que rodea la plazuela y el templo, a mano sobre las huellas de OSM
   (sin fotos propias, R0104: "se puede ver la pared del edificio contiguo"): Colegio Alemán Cardenal Maurer sobre
   Colón, Templo de La Merced en la esquina Pérez × Azurduy, Facultad de Humanidades sobre Nicolás Ortiz y Azurduy, y
   casas de 2 plantas con tejado en los dos lados de la plazuela que no dan a una calle. Solo fachadas a calle o a la
   plazuela; detrás de ellas no hay nada.
"""

import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from kit import arquitectura as A_  # noqa: E402
from kit.datos import _cortar_semiplano, _dentro, calles_reales, lados, recortar_a_calles  # noqa: E402
from piezas_claude import (arbol_paraguas, fachada, hilera_sobre_linea, lado_virtual, mirador, suelo_huella,  # noqa: E402
                           techo_auto, tejado_dos_aguas)
from base_plazas import banco, farol_poste  # noqa: E402

AGENTE, MID = "claude", "AMP_S"
# Las coordenadas de OSM (osm_amp_s.json y los puntos de árboles/senderos de abajo) se pasaron a metros con una
# conversión propia que quedó 2,81 m al norte del lienzo (medido en 7 nodos de calle comunes con calles.json):
# todo dato de OSM pasa por osm() antes de usarse.
DESFASE_OSM = (0.0, -2.81)


def osm(pts):
    return [(x + DESFASE_OSM[0], y + DESFASE_OSM[1]) for x, y in pts]

m, col = iniciar(AGENTE, MID)
RND = random.Random("amp-s")
BL = "#f6f4ef"
CREMA = "#e7d8b4"
# sillería rojiza casi uniforme (R0099–R0102: piedra arenisca rojiza; las hiladas rosa/ocre se leían como bandas)
SILLAR = "#a8705a"
SILLAR2 = "#ae7963"
OCRE = "#c6a074"

OSM = {
    "convento": [(-376.54, -441.67), (-337.25, -477.5), (-335.01, -479.54), (-309.3, -449.4)],
    "templo": [(-376.5, -441.7), (-386.8, -453.19), (-348.31, -489.11), (-337.25, -477.5)],
    "plazuela": [(-402.29, -524.22), (-380.83, -542.18), (-367.21, -525.48), (-347.4, -501.6), (-346.5, -499.6),
                 (-346.8, -497.4), (-364.9, -482.3)],
}
_here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "osm_amp_s.json")
if os.path.exists(_here):
    _o = json.load(open(_here))
    OSM["convento"] = [tuple(p) for p in _o["Convento de San Felipe de Neri"][0]]
    OSM["templo"] = [tuple(p) for p in _o["church"][0]]
    OSM["plazuela"] = [tuple(p) for p in _o["Plazuela Cochabamba"][0]]
for k in OSM:
    if OSM[k][0] == OSM[k][-1]:
        OSM[k] = OSM[k][:-1]
    OSM[k] = osm(OSM[k])


def _u(a, b):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def _eje(nombre, cerca):
    """Tramo (a, b) del eje de la calle más cercano al punto."""
    mejor = None
    for c in calles_reales():
        if c["nombre"] != nombre:
            continue
        for a, b in zip(c["eje"], c["eje"][1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            d = math.hypot(mx - cerca[0], my - cerca[1])
            if mejor is None or d < mejor[0]:
                mejor = (d, tuple(a), tuple(b), c["ancho"])
    return mejor[1], mejor[2], mejor[3]


# ======================================================================================= fachada colonial genérica
def fachada_colonial(f, off, zb, pisos=2, alto_piso=4.4, ventanas=None, balcones=True, remates=True, puertas=None):
    """Casona blanca: zócalo de sillería ocre, pilastras y marcos crema, ventanas de madera con balcón de hierro,
    cornisa con remates (R0096–R0098)."""
    L = f.largo
    if L < 2.5:
        return
    A_.zocalo(f, 1.3 + off, color=OCRE, sillares=True, desde=zb - 0.6 - f.suelo)
    n = ventanas or max(1, round(L / 3.6))
    vs = [L * (k + 0.5) / n for k in range(n)]
    for k in range(n + 1):                                                        # pilastras crema
        sp = L * k / n
        f.caja(max(0.0, sp - 0.25), min(L, sp + 0.25), 1.3 + off, pisos * alto_piso + off, 0.0, 0.08, "moldura", CREMA)
    f.caja(0.0, L, alto_piso - 0.1 + off, alto_piso + 0.15 + off, 0.0, 0.12, "moldura", CREMA)   # imposta
    for j, v in enumerate(vs):
        if puertas and j in puertas:
            A_.puerta(f, v, ancho=1.5, alto=3.0 + off, color="#5a3a26", moldura="moldura", color_moldura=CREMA)
        else:
            f.caja(v - 0.75, v + 0.75, 0.0, 2.9 + off, 0.0, 0.05, "marco_ventana", "#3b3f42")      # local
            f.caja(v - 0.65, v + 0.65, 0.3, 2.8 + off, 0.05, 0.06, "vidrio")
            f.caja(v - 0.9, v + 0.9, 2.9 + off, 3.15 + off, 0.0, 0.12, "moldura", CREMA)
        if pisos >= 2:
            A_.ventana(f, v, alto_piso + 0.4 + off, ancho=1.2, alto=2.2, moldura="moldura", color_moldura=CREMA,
                       carpinteria="madera", color_carpinteria="#5a3020")
            if balcones:
                A_.balcon_hierro(f, v - 0.9, v + 0.9, alto_piso + 0.4 + off, vuelo=0.5)
            f.caja(v - 0.9, v + 0.9, alto_piso + 2.75 + off, alto_piso + 2.95 + off, 0.0, 0.18, "moldura", CREMA)
    alto = pisos * alto_piso
    A_.cornisa(f, alto - 0.35 + off, vuelo=0.3, alto=0.35, color=CREMA)
    A_.parapeto(f, alto + off, alto=0.6, color=BL)
    if remates:
        k = 0.3
        while k < L - 0.2:
            f.caja(k - 0.15, k + 0.15, alto + 0.6 + off, alto + 0.85 + off, -0.1, 0.12, "moldura", CREMA)
            p = f.punto(k, alto + 1.0 + off, 0.0)
            f.c.esfera(p.x, p.y, p.z, 0.17, "moldura", CREMA, segmentos=6)
            k += L / max(1, round(L / 3.6))


# ======================================================================================= 1. esquina del mirador
H_MIRADOR = None


def esquina_mirador():
    global H_MIRADOR
    a1, b1, w1 = _eje("Calle Pantaleón Dalence", (-240, -415))
    a2, b2, w2 = _eje("Calle Nicolás Ortiz", (-270, -415))
    # punto de cruce de los dos ejes
    ud, un = _u(a1, b1), _u(a2, b2)
    den = ud[0] * un[1] - ud[1] * un[0]
    t = ((a2[0] - a1[0]) * un[1] - (a2[1] - a1[1]) * un[0]) / den
    X = (a1[0] + ud[0] * t, a1[1] + ud[1] * t)
    # direcciones hacia la cuadra sur: por Dalence hacia el SE y por Nicolás Ortiz hacia el SO
    dD = ud if ud[1] < 0 else (-ud[0], -ud[1])
    dN = un if un[1] < 0 else (-un[0], -un[1])
    pts = [X, (X[0] + dD[0] * 30, X[1] + dD[1] * 30), (X[0] + dD[0] * 30 + dN[0] * 22, X[1] + dD[1] * 30 + dN[1] * 22),
           (X[0] + dN[0] * 26, X[1] + dN[1] * 26)]
    h = recortar_a_calles(pts, area_min=20)
    if not h:
        print("[AMP_S] la esquina no quedó")
        return
    # ochava de 3 m sobre la esquina (el mirador va en ella)
    bis = _u((0, 0), (dD[0] + dN[0], dD[1] + dN[1]))
    ce = min(h, key=lambda p: (p[0] - X[0]) * bis[0] + (p[1] - X[1]) * bis[1])
    dmin = (ce[0] - X[0]) * bis[0] + (ce[1] - X[1]) * bis[1]
    h = _cortar_semiplano(h, X[0], X[1], bis[0], bis[1], dmin + 2.0)
    H_MIRADOR = h
    zb, zr = suelo_huella(h)
    alto = 8.8
    c = Constructor("AMP_S_casona_mirador")
    c.prisma(h, zb - 0.6, zr + alto, "muro", BL, tapa=False)
    techo_auto(c, h, zr + alto - 0.02, zpatio=zb, muro=("muro", BL))
    for l in lados(h):
        if not l["a_calle"] or l["largo"] < 2.0:
            continue
        f = fachada(c, l)
        off = zr - f.suelo
        mx, my = (l["a"][0] + l["b"][0]) / 2, (l["a"][1] + l["b"][1]) / 2
        es_ochava = l["largo"] < 4.5 and math.hypot(mx - X[0], my - X[1]) < 12
        if es_ochava:
            A_.zocalo(f, 1.3 + off, color=OCRE, sillares=True, desde=zb - 0.6 - f.suelo)
            sm = f.largo / 2
            # R0115 ("¿eso es una puerta o qué?"): el pilar que sostiene el mirador va a un lado de la ochava, con
            # basa de sillería y capitel, y la puerta del local al otro, con su marco de piedra y letrero (foto R0098)
            sp, sd = f.largo * 0.24, f.largo * 0.66
            f.caja(sp - 0.42, sp + 0.42, -0.6, 1.3 + off, 0.0, 0.62, "piedra", OCRE)              # basa
            f.caja(sp - 0.34, sp + 0.34, 1.3 + off, 4.2 + off, 0.0, 0.54, "moldura", CREMA)       # fuste
            f.caja(sp - 0.5, sp + 0.5, 4.2 + off, 4.45 + off, 0.0, 0.72, "moldura", CREMA)        # capitel
            if f.largo > 2.6:
                ancho_p = min(1.3, f.largo - sp - 1.0)
                A_.puerta(f, sd, ancho=ancho_p, alto=2.9 + off, color="#3a2a20", moldura="piedra", color_moldura=OCRE)
                f.caja(sd - ancho_p / 2 - 0.1, sd + ancho_p / 2 + 0.1, 3.05 + off, 3.5 + off, 0.06, 0.12,
                       "letrero", "#2f3a4a")
            # gran mirador rojizo que dobla la esquina, con ménsulas y tejadillo
            MAD = ("marco_ventana", "#7a3326")
            mirador(f, sm, 4.4 + off, ancho=f.largo + 3.2, alto=2.7, vuelo=1.35, base=("madera", "#6a2c20"), madera=MAD,
                    antepecho=("madera", "#7a3326"))
            for dx in (-1.6, -0.5, 0.5, 1.6):
                f.caja(sm + dx - 0.1, sm + dx + 0.1, 3.5 + off, 4.4 + off, 0.0, 1.1, "madera", "#5a2418")  # ménsulas
            f.caja(-1.8, f.largo + 1.8, 7.1 + off, 7.3 + off, 0.0, 1.6, "teja", "#9a4a32")
            A_.cornisa(f, alto - 0.35 + off, vuelo=0.3, alto=0.35, color=CREMA)
            A_.parapeto(f, alto + off, alto=0.6, color=BL)
        elif abs((l["b"][0] - l["a"][0]) * dN[0] + (l["b"][1] - l["a"][1]) * dN[1]) > 0.9 * l["largo"]:
            # cara a Nicolás Ortiz (R0195–R0198): la misma casona de pilastras crema que sigue por la calle
            import ortiz_se
            ortiz_se.fachada_crema(f, f.largo, alto, off, zb - 0.6 - f.suelo,
                                   entradas=["tienda", "puerta", "portal", "tienda", "puerta"])
        else:
            fachada_colonial(f, off, zb, puertas={1} if l["largo"] > 9 else None)
            # miradores menores a lo largo de la calle (R0096: casonas con miradores)
            if l["largo"] > 16:
                mirador(f, f.largo * 0.72, 4.6 + off, ancho=3.4, alto=2.4, vuelo=1.0, base=("madera", "#6a2c20"),
                        madera=("marco_ventana", "#7a3326"), antepecho=("madera", "#7a3326"))
    c.objeto(col)
    print("[AMP_S] esquina del mirador en", tuple(round(v, 1) for v in X))


# ======================================================================================= 2. San Felipe Neri
def san_felipe():
    T = recortar_a_calles(OSM["templo"], area_min=50) or OSM["templo"]
    # extremo SE (el de los campanarios de OSM): el lado más cercano al cruce de Colón/Pérez
    cruce = osm([(-342.4, -498.7)])[0]
    ls = lados(T)
    fr = min(ls, key=lambda l: math.hypot((l["a"][0] + l["b"][0]) / 2 - cruce[0], (l["a"][1] + l["b"][1]) / 2 - cruce[1]))
    zb, zr = suelo_huella(T)
    c = Constructor("AMP_S_san_felipe_naves")
    ALTO = 13.0
    c.prisma(T, zb - 0.6, zr + ALTO, "muro", "#b07d68", tapa=False)
    A_.techo_plano(c, T, zr + ALTO - 0.02, rol="azotea", color="#efece6")
    # costado sobre Colón (R0175–R0178), rehecho desde cero el 2026-11-24: ver san_felipe_costado.py
    for l in ls:
        if l is fr or l["largo"] < 6:
            continue
        f = fachada(c, l)
        off = zr - f.suelo
        if l["a_calle"]:
            import san_felipe_costado
            san_felipe_costado.costado(c, f, off, ALTO, zb - 0.6 - f.suelo)
            import san_felipe_frente
            san_felipe_frente.base_torre_colon(c, f, off, zb - 0.6 - f.suelo, san_felipe_costado.FIN_COSTADO, f.largo, 16.2)
        else:
            f.caja(0.0, f.largo, -0.6, ALTO + off, 0.0, 0.04, "zocalo_piedra", SILLAR)
            A_.cornisa(f, ALTO - 0.4 + off, vuelo=0.35, alto=0.4, color="#d9c7a8")
    # cúpula blanca hacia el crucero (a 2/3 de la nave desde la fachada)
    cx = sum(p[0] for p in T) / len(T)
    cy = sum(p[1] for p in T) / len(T)
    fm = ((fr["a"][0] + fr["b"][0]) / 2, (fr["a"][1] + fr["b"][1]) / 2)
    dx, dy = cx - fm[0], cy - fm[1]
    kx, ky = cx + dx * 0.35, cy + dy * 0.35
    z0 = zr + ALTO
    c.cilindro(kx, ky, z0, z0 + 3.0, 4.2, "muro", BL, lados=16)                          # tambor
    for j in range(8):
        a = 2 * math.pi * j / 8
        c.caja_ejes((kx + math.cos(a) * 4.21, ky + math.sin(a) * 4.21, z0 + 1.5), (-math.sin(a), math.cos(a), 0),
                    (math.cos(a), math.sin(a), 0), (0, 0, 1), 0.8, 0.04, 1.6, "vidrio", "#3f5a63")
    c.cilindro(kx, ky, z0 + 3.0, z0 + 3.3, 4.5, "moldura", "#e9e4da", lados=16)
    for j in range(6):                                                                   # media naranja
        t0, t1 = j / 6, (j + 1) / 6
        r0, r1 = 4.2 * math.cos(t0 * math.pi / 2), 4.2 * math.cos(t1 * math.pi / 2)
        c.cilindro(kx, ky, z0 + 3.3 + 4.2 * math.sin(t0 * math.pi / 2), z0 + 3.3 + 4.2 * math.sin(t1 * math.pi / 2),
                   max(0.05, r0), "muro", BL, lados=16, radio_arriba=max(0.05, r1))
    c.cilindro(kx, ky, z0 + 7.4, z0 + 9.0, 0.7, "muro", BL, lados=8)                      # linterna
    c.cilindro(kx, ky, z0 + 9.0, z0 + 9.6, 0.85, "muro", BL, lados=8, radio_arriba=0.1)
    c.caja(kx - 0.05, ky - 0.05, z0 + 9.6, kx + 0.05, ky + 0.05, z0 + 10.8, "hierro", "#2f2b28")
    c.caja(kx - 0.35, ky - 0.05, z0 + 10.3, kx + 0.35, ky + 0.05, z0 + 10.4, "hierro", "#2f2b28")
    c.objeto(col)

    # ---- fachada de piedra (extremo SE) con las dos torres blancas
    c = Constructor("AMP_S_san_felipe_fachada")
    f = fachada(c, fr)
    off = zr - f.suelo
    L = f.largo
    # rehecho desde cero el 2026-11-24 (R0099–R0102, R0179): ver san_felipe_frente.py
    import san_felipe_frente
    san_felipe_frente.frente(c, f, off, L)
    c.objeto(col)
    # ---- atrio: muro de sillería con balaustrada y pináculos, reja delante de la portada
    atrio(f, off, L)
    return T, fr


def atrio(f, off, L):
    """Atrio delante de la fachada hasta la vereda: piso de piedra, muro bajo de sillería con balaustrada, pilares con
    pináculos y reja de hierro frente a la portada."""
    c = Constructor("AMP_S_san_felipe_atrio")
    # profundidad: hasta 1 m antes del corredor de la calle de enfrente
    prof = 1.0
    while prof < 14.0:
        p = f.punto(L / 2, 0, prof + 1.0)
        if _en_calle(p.x, p.y):
            break
        prof += 0.5
    pts = [f.punto(-0.7, 0, 0.3), f.punto(L + 2.0, 0, 0.3), f.punto(L + 2.0, 0, prof), f.punto(-0.7, 0, prof)]
    zp = max(p.z for p in pts) + 0.25
    c.prisma([(p.x, p.y) for p in pts], min(p.z for p in pts) - 0.4, zp, "piedra", SILLAR, tapa=False)
    c.tapa([(p.x, p.y) for p in pts], zp, "adoquin", "#c9b59a")
    ze = zp - f.suelo
    # muro de sillares con balaustrada y pináculos en el frente y los lados, dejando el vano de la reja (R0099–R0102,
    # R0179); ver san_felipe_frente.muro_atrio
    import san_felipe_frente
    S0 = -0.7                                                     # lado de Colón: un poco delante de la base de la torre
    tramos = [((S0, prof), (L / 2 - 1.8, prof)), ((L / 2 + 1.8, prof), (L + 2.0, prof)),
              ((S0, 0.3), (S0, prof)), ((L + 2.0, prof), (L + 2.0, 0.6))]
    san_felipe_frente.muro_atrio(c, [((f.punto(s0, 0, d0).x, f.punto(s0, 0, d0).y), (f.punto(s1, 0, d1).x, f.punto(s1, 0, d1).y))
                                     for (s0, d0), (s1, d1) in tramos], altura_suelo,
                                    tuple(f.punto(L / 2, 0, prof / 2))[:2])
    # reja forjada verde frente a la portada (R0187/R0188, fotos del usuario): barrotes, dos hileras de volutas,
    # copete en arco con volutas y pilares de piedra con urna
    a, b = f.punto(L / 2 - 1.8, 0, prof), f.punto(L / 2 + 1.8, 0, prof)
    ux, uy = (b.x - a.x) / 3.6, (b.y - a.y) / 3.6
    z0 = f.suelo + ze
    VERDE = "#2f5e48"

    def barra(p, q, r=0.018):
        dx, dy, dz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
        Lb = math.sqrt(dx * dx + dy * dy + dz * dz)
        if Lb < 1e-3:
            return
        ez = (dx / Lb, dy / Lb, dz / Lb)
        ex = (-uy, ux, 0.0)
        ey = (ez[1] * ex[2] - ez[2] * ex[1], ez[2] * ex[0] - ez[0] * ex[2], ez[0] * ex[1] - ez[1] * ex[0])
        c.caja_ejes(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, (p[2] + q[2]) / 2), ex, ey, ez, r * 2, r * 2, Lb, "hierro", VERDE)

    def voluta(sx, h, r):
        cx_, cy_ = a.x + ux * sx, a.y + uy * sx
        pts = [(cx_ + ux * r * math.cos(t), cy_ + uy * r * math.cos(t), z0 + h + r * math.sin(t))
               for t in [k * math.tau / 12 for k in range(13)]]
        for p, q in zip(pts, pts[1:]):
            barra(p, q, 0.018)

    k = 0.1
    while k < 3.55:
        x, y = a.x + ux * k, a.y + uy * k
        c.cilindro(x, y, z0, z0 + 2.6, 0.022, "hierro", VERDE, lados=4)
        k += 0.14
    for hh in (0.15, 1.25, 1.75, 2.6):
        barra((a.x, a.y, z0 + hh), (b.x, b.y, z0 + hh), 0.025)
    for j in range(8):                                                                   # volutas en C enfrentadas
        sx = 0.25 + j * 0.45
        voluta(sx - 0.1, 1.5, 0.2)                                                       # C grandes (R0187)
        voluta(sx + 0.1, 1.5, 0.2)
    for j in range(8):                                                                   # fila bajo el pasamanos
        voluta(0.25 + j * 0.45, 2.38, 0.19)
    for sx, hh, r in ((0.55, 2.85, 0.22), (1.25, 3.0, 0.25), (2.35, 3.0, 0.25), (3.05, 2.85, 0.22),      # copete en corazones
                      (1.5, 3.35, 0.22), (2.1, 3.35, 0.22), (1.8, 3.7, 0.18)):
        voluta(sx, hh, r)
    for j in range(9):                                                                   # contorno del copete
        t0, t1 = j / 9, (j + 1) / 9
        p = (a.x + ux * 3.6 * t0, a.y + uy * 3.6 * t0, z0 + 2.6 + 1.0 * math.sin(math.pi * t0) ** 1.5)
        q = (a.x + ux * 3.6 * t1, a.y + uy * 3.6 * t1, z0 + 2.6 + 1.0 * math.sin(math.pi * t1) ** 1.5)
        barra(p, q, 0.022)
    m = (a.x + ux * 1.8, a.y + uy * 1.8)
    barra((m[0], m[1], z0), (m[0], m[1], z0 + 4.05), 0.03)                                # montante central y punta
    for p in (a, b):                                                                     # pilares de arenisca
        c.caja(p.x - 0.45, p.y - 0.45, z0, p.x + 0.45, p.y + 0.45, z0 + 2.9, "zocalo_piedra", "#bb8c6c")
        c.caja(p.x - 0.55, p.y - 0.55, z0 + 2.9, p.x + 0.55, p.y + 0.55, z0 + 3.1, "piedra", "#c99b78")
        c.caja(p.x - 0.42, p.y - 0.42, z0 + 3.1, p.x + 0.42, p.y + 0.42, z0 + 3.35, "piedra", "#b98663")
        c.caja(p.x - 0.3, p.y - 0.3, z0 + 3.35, p.x + 0.3, p.y + 0.3, z0 + 3.9, "piedra", "#cfa483")
        c.caja(p.x - 0.18, p.y - 0.18, z0 + 3.9, p.x + 0.18, p.y + 0.18, z0 + 4.3, "piedra", "#b98663")
    # escalones del atrio a la vereda
    for j in range(3):
        q0, q1 = f.punto(L / 2 - 1.8, 0, prof + 0.3 * j), f.punto(L / 2 + 1.8, 0, prof + 0.3 * (j + 1))
        pts = [f.punto(L / 2 - 1.8, 0, prof + 0.35 * j), f.punto(L / 2 + 1.8, 0, prof + 0.35 * j),
               f.punto(L / 2 + 1.8, 0, prof + 0.35 * (j + 1)), f.punto(L / 2 - 1.8, 0, prof + 0.35 * (j + 1))]
        c.prisma([(p.x, p.y) for p in pts], f.suelo - 0.3, zp - 0.08 * (j + 1), "piedra", "#b8a996")
    c.objeto(col)


def _en_calle(x, y):
    for cc in calles_reales():
        w = cc["ancho"] / 2
        for a, b in zip(cc["eje"], cc["eje"][1:]):
            ex, ey = b[0] - a[0], b[1] - a[1]
            L2 = ex * ex + ey * ey or 1
            t = ((x - a[0]) * ex + (y - a[1]) * ey) / L2
            if 0 <= t <= 1 and math.hypot(x - a[0] - t * ex, y - a[1] - t * ey) < w:
                return True
    return False


def convento():
    h = recortar_a_calles(OSM["convento"], area_min=40)
    if not h:
        return
    zb, zr = suelo_huella(h)
    alto = 9.0
    c = Constructor("AMP_S_convento_san_felipe")
    c.prisma(h, zb - 0.6, zr + alto, "muro", BL, tapa=False)
    techo_auto(c, h, zr + alto - 0.02, zpatio=zb, muro=("muro", BL))
    for l in lados(h):
        if l["a_calle"] and l["largo"] > 4:
            f = fachada(c, l)
            off = zr - f.suelo
            L = f.largo
            A_.zocalo(f, 0.9 + off, color="#d9cfbd", sillares=False, desde=zb - 0.6 - f.suelo)
            n = max(1, round(L / 4.0))
            for j in range(n):
                v = L * (j + 0.5) / n
                A_.ventana(f, v, 1.6 + off, ancho=1.0, alto=1.8, arco=True, reja=True, moldura="moldura",
                           color_moldura="#ece8df", carpinteria="madera", color_carpinteria="#5a3a26")
                A_.ventana(f, v, 5.6 + off, ancho=0.9, alto=1.5, arco=True, moldura="moldura", color_moldura="#ece8df",
                           carpinteria="madera", color_carpinteria="#5a3a26")
            A_.cornisa(f, alto - 0.3 + off, vuelo=0.25, alto=0.3, color="#ece8df")
    c.objeto(col)


# ======================================================================================= 3. Plazuela Cochabamba
# rehecha desde cero el 2026-11-24 (R0180, R0181, R0183, R0103, R0104): ver plazuela_cochabamba.py


def explanada():
    """Explanada empedrada al frente y al costado SO del templo hasta las veredas (el relleno no pone casas ahí)."""
    pol = recortar_a_calles(FRANJA_TEMPLO, area_min=10)
    if not pol:
        return
    c = Constructor("AMP_S_explanada_san_felipe")
    zs = [altura_suelo(*p) for p in pol]
    c.prisma(pol, min(zs) - 0.4, max(zs) + 0.16, "piedra", "#b8a996", tapa=False)
    c.tapa(pol, max(zs) + 0.16, "adoquin", "#c9b59a")
    c.objeto(col)


FRANJA_TEMPLO = osm([(-386.8, -453.19), (-390.9, -457.6), (-348.1, -497.6), (-332.9, -481.6), (-337.25, -477.5),
                     (-348.31, -489.11)])

# ======================================================================================= 4. entorno de la plazuela
# Puntos donde se paró el usuario al marcar las correcciones de esta sección: son calle o vereda (R0100: "la calle
# que separa la iglesia de la plazuela también es más ancha"). Ningún edificio del entorno se acerca a menos de
# LIBRE m de ellos, y los lados que los miran llevan fachada.
_REV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "coordinacion", "revisiones")
CAMS_REV = []
CAM_ID = {}        # punto de cada revisión, por id
MIRADAS_REV = []   # y hacia dónde miraba: lo que tenía delante (la referencia) no se tapa
for _r in ("R0096", "R0097", "R0098", "R0099", "R0100", "R0101", "R0102", "R0103", "R0104", "R0115"):
    _p = os.path.join(_REV, _r, "revision.json")
    if os.path.exists(_p):
        _cm = json.load(open(_p))["escena"]["camara"]
        CAMS_REV.append((_cm["lienzo"]["x"], _cm["lienzo"]["y"]))
        CAM_ID[_r] = CAMS_REV[-1]
        MIRADAS_REV.append((_cm["lienzo"]["x"], _cm["lienzo"]["y"], math.radians(_cm["rumbo_grados"])))
LIBRE = 3.0


def _despejar(h, excluir=()):
    """Recorta la huella para dejar LIBRE m alrededor de cada punto de revisión (corte paralelo al lado más cercano).
    excluir: puntos de revisión que no cuentan para esta huella."""
    for cx, cy in CAMS_REV:
        if not h or len(h) < 3:
            return None
        if (cx, cy) in excluir:
            continue
        l = min(lados(h), key=lambda l: _dseg(cx, cy, l["a"], l["b"]))
        if _dseg(cx, cy, l["a"], l["b"]) >= LIBRE and not _dentro(cx, cy, h):
            continue
        nx, ny = l["normal"]
        h = _cortar_semiplano(h, cx, cy, -nx, -ny, LIBRE)
    # lo que el usuario miraba (su foto de referencia) queda a la vista: si la huella corta la línea de mirada a
    # menos de 30 m, se recorta por detrás de la cámara
    for cx, cy, rb in MIRADAS_REV:
        if not h or len(h) < 3:
            return None
        if (cx, cy) in excluir:
            continue
        dx, dy = math.sin(rb), math.cos(rb)
        if any(_dentro(cx + dx * t, cy + dy * t, h) for t in range(1, 30)):
            h = _cortar_semiplano(h, cx, cy, -dx, -dy, 1.0)
    return h if h and len(h) >= 3 else None


def _dseg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy or 1e-9
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / l2))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)


def _a_la_vista(l):
    mx, my = (l["a"][0] + l["b"][0]) / 2, (l["a"][1] + l["b"][1]) / 2
    return l["a_calle"] or any(math.hypot(mx - x, my - y) < 16 for x, y in CAMS_REV)


def _poligono_osm(nombre):
    return osm([tuple(p) for p in json.load(open(_here))[nombre][0]])


def edificio_osm(nombre, ident, pisos, alto_piso, muro, estilo, puertas_centro=True, corte=None, excluir=()):
    """Volumen sobre la huella de OSM recortada a las calles; fachada solo en los lados a la calle.
    corte: (x, y, nx, ny) semiplano que se conserva; excluir: puntos de revisión que no recortan esta huella."""
    h = recortar_a_calles(_poligono_osm(nombre), area_min=40)
    if h and corte:
        h = _cortar_semiplano(h, *corte, 0.0)
    h = _despejar(h, excluir)
    if not h:
        return None
    zb, zr = suelo_huella(h)
    alto = pisos * alto_piso
    c = Constructor(ident)
    c.huella = h
    c.prisma(h, zb - 0.6, zr + alto, "muro", muro, tapa=False)
    techo_auto(c, h, zr + alto - 0.02, zpatio=zb, muro=("muro", muro))
    for l in lados(h):
        if not _a_la_vista(l) or l["largo"] < 4.0:
            continue
        f = fachada(c, l)
        off = zr - f.suelo
        if estilo == "facultad":     # rehecha desde cero el 2026-11-24 (R0186, R0189, R0190): ver facultad.py
            import facultad
            cruce = osm([(-342.4, -498.7)])[0]
            esq = 0.0 if math.dist(l["a"], cruce) < 9 else (l["largo"] if math.dist(l["b"], cruce) < 9 else None)
            facultad.fachada(f, zb + 0.35 * (zr - zb) - f.suelo + 0.9, zb - 0.6 - f.suelo, alto_piso,
                             max(1, round(l["largo"] / 4.4)), alto_total=zr + alto - f.suelo, esquina_en=esq)
            continue
        n = max(1, round(l["largo"] / (3.2 if estilo == "institucion" else 3.6)))
        fachada_colonial(f, off, zb, pisos=pisos, alto_piso=alto_piso, ventanas=n,
                         balcones=(estilo != "institucion"), remates=(estilo != "institucion"),
                         puertas={n // 2} if puertas_centro else None)
    c.objeto(col)
    return h


def la_merced():
    """Templo de La Merced (esquina Pérez × Azurduy): huella y volúmenes; la fachada a la plazuela está en la_merced.py."""
    # la huella de OSM cae donde camina el usuario (R0101–R0104): se corre alejándose del cruce lo justo para que
    # quede casi entera después de despejar sus puntos de vista
    base = _poligono_osm("Templo de La Merced")
    cruce = osm([(-342.4, -498.7)])[0]
    cx0, cy0 = sum(p[0] for p in base) / len(base), sum(p[1] for p in base) / len(base)
    L0 = math.hypot(cx0 - cruce[0], cy0 - cruce[1])
    ux0, uy0 = (cx0 - cruce[0]) / L0, (cy0 - cruce[1]) / L0
    area = lambda q: abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(q, q[1:] + q[:1]))) / 2 if q else 0
    a0 = area(recortar_a_calles(base, area_min=40))
    h = None
    for dd in (0, 3, 6, 9, 12, 15):
        cand = recortar_a_calles([(x + ux0 * dd, y + uy0 * dd) for x, y in base], area_min=40)
        h = _despejar(cand)
        if h and area(h) > 0.75 * a0:
            print("[AMP_S] La Merced corrida", dd, "m")
            break
    if not h:
        return
    zb, zr = suelo_huella(h)
    ALTO, ALTO_CONV = 11.5, 8.5
    calle = [l for l in lados(h) if _a_la_vista(l) and l["largo"] > 6] or [l for l in lados(h) if l["largo"] > 6]
    if not calle:
        return
    # R0182/R0184/R0185 (fotos del usuario estudiadas a resolución completa). FRENTE: el lado que mira a la toma R0184
    # (noroeste): muro blanco liso con ventana alta de arco y cuarterones, paño apenas saliente debajo, ventana chica de
    # arco y base gris; la TORRE sube desde lo alto del frente junto a la esquina norte (fuste que se angosta, campanario
    # chico con vano en arco, cornisa y remate). COSTADO: el lado que comparte la esquina norte (noreste): portada de
    # pilastras finas pareadas, arco con reja negra y cuerpo alto con nicho, frontón mixtilíneo y urnas; más allá, el
    # convento, más bajo, de dos plantas con balcones y alero de teja.
    toma = (-349.25, -509.57)
    frente = max(calle, key=lambda l: ((toma[0] - (l["a"][0] + l["b"][0]) / 2) * l["normal"][0]
                                       + (toma[1] - (l["a"][1] + l["b"][1]) / 2) * l["normal"][1]))
    N = min((frente["a"], frente["b"]), key=lambda p: math.dist(p, toma))
    # en las tres fotos la torre, la portada y el convento se ven seguidos sobre la misma cara (la que mira a las
    # tomas, a lo largo de la calle): la portada y el convento van sobre el frente, más allá de la torre
    costado = frente
    otro = costado["b"] if math.dist(costado["a"], N) < math.dist(costado["b"], N) else costado["a"]
    uc = ((otro[0] - N[0]) / costado["largo"], (otro[1] - N[1]) / costado["largo"])
    P = (N[0] + uc[0] * 15.8, N[1] + uc[1] * 15.8)
    iglesia = _cortar_semiplano(h, P[0], P[1], -uc[0], -uc[1], 0.0)
    conv = _cortar_semiplano(h, P[0], P[1], uc[0], uc[1], 0.0)
    c = Constructor("AMP_S_la_merced")
    c.huella = h
    c.prisma(iglesia, zb - 0.6, zr + ALTO, "muro", BL, tapa=False)
    A_.techo_plano(c, iglesia, zr + ALTO - 0.02, rol="azotea", color="#efece6")
    if len(conv) >= 3:
        c.prisma(conv, zb - 0.6, zr + ALTO_CONV, "muro", BL, tapa=False)
        tejado_dos_aguas(c, conv, zr + ALTO_CONV, pendiente=22, cumbrera=uc)   # el faldón cae a la calle (R0185)
    for l in calle:
        if l is not frente:
            f = fachada(c, l)
            A_.zocalo(f, 1.2 + (zb + zr) / 2 - f.suelo, color="#a7a196", sillares=False, desde=zb - 0.6 - f.suelo)
    # fachada a la plazuela rehecha desde cero el 2026-11-24 (R0182, R0184, R0185): ver la_merced.py
    import la_merced as LM
    f = fachada(c, frente)
    off = zr - f.suelo
    L = f.largo
    desde_a = math.dist(frente["a"], N) < 0.5
    S = (lambda d: d) if desde_a else (lambda d: L - d)                 # distancia desde la esquina del cruce → s
    LM.fachada(c, f, S, off, ALTO, ALTO_CONV, zb - 0.6 - f.suelo)
    c.objeto(col)


def entorno():
    from piezas_claude import tramo_calle
    edificio_osm("Unidad Educativa Colegio Boliviano Alemán Cardenal Maurer", "AMP_S_colegio_aleman", 2, 4.3,
                 "#f4f1ea", "institucion")
    # la Facultad ocupa solo los primeros 27 m de Ortiz (R0189, R0191); sigue la hilera de ortiz_se.py. Va sobre la
    # línea de fachada de la cuadra: las tomas de San Felipe R0099/R0100 (en su vereda) no la retiran
    import ortiz_se
    from piezas_claude import sobre_calle as _sc
    ortiz = tramo_calle("Calle Nicolás Ortiz", (-300.0, -455.0))
    xc, yc, ux_, uy_ = _sc(ortiz, ortiz_se.T0, -6.0)
    edificio_osm("Facultad de Humanidades y Ciencias de la Educación", "AMP_S_facultad_humanidades", 2, 4.6,
                 "#f5f2ea", "facultad", corte=(xc, yc, -ux_, -uy_), excluir=(CAM_ID.get("R0099"), CAM_ID.get("R0100")))
    la_merced()
    # los dos lados de la plazuela sin calle: casas de 2 plantas con tejado y balcones, mirando a la plazuela
    pz = _poligono_osm("Plazuela Cochabamba")
    no_a, no_b = pz[0], pz[6]          # lado NO (hacia el colegio): de (-402,-527) a (-365,-485)
    so_a, so_b = pz[1], pz[0]          # lado SO: de (-381,-545) a (-402,-527)
    hilera_sobre_linea(col, "AMP_S_plazuela_no", no_a, no_b, [
        (9.0, 2, 4.2, "#f6f4ef", "alero", dict(vanos=[1.6, 4.5, 7.4], puertas=[4.5], balcones=[1.6, 7.4])),
        (8.0, 2, 4.0, "#f1e6cf", "alero", dict(vanos=[1.5, 4.0, 6.5], puertas=[1.5], balcones=[4.0])),
        (10.5, 2, 4.4, "#f6f4ef", "cornisa", dict(vanos=[1.5, 4.0, 6.5, 9.0], puertas=[6.5], balcones=[1.5, 4.0, 9.0])),
        (7.5, 2, 4.0, "#efe3c4", "alero", dict(vanos=[1.8, 5.7], puertas=[5.7], balcones=[1.8])),
        (9.0, 2, 4.2, "#f4efe4", "alero", dict(vanos=[1.5, 4.5, 7.5], puertas=[1.5], balcones=[4.5, 7.5])),
        (8.0, 2, 4.2, "#f6f4ef", "cornisa", dict(vanos=[1.6, 4.0, 6.4], puertas=[4.0], balcones=[1.6, 6.4])),
    ], fondo=8.0, libres=CAMS_REV)
    # frentes de calle que quedaban abiertos (frente_calle.py, 2026-11-14); casas de la cuadra diseñadas a mano
    from piezas_claude import casas_de_frente
    C2 = lambda w_, p_, m_, r_, v_, pu_, b_: (w_, 2, p_, m_, r_, dict(vanos=v_, puertas=pu_, balcones=b_))
    # vereda SE de Nicolás Ortiz, de la Facultad a la casona del mirador (R0191–R0198): ver ortiz_se.py
    t_mir = min(ortiz_se.t_de(ortiz, x, y) for x, y in H_MIRADOR) if H_MIRADOR else 95.0
    ortiz_se.construir(col, ortiz, t_mir)
    cf = Constructor("AMP_S_ortiz_faroles")
    ortiz_se.faroles(cf, ortiz, altura_suelo)
    cf.objeto(col)
    casas_de_frente(col, "AMP_S_azurduy_ne", tramo_calle("Calle Azurduy", (-300.0, -540.0)), +1, [
        C2(8.5, 4.2, "#f6f4ef", "alero", [1.5, 4.25, 7.0], [4.25], [1.5, 7.0]),
        C2(8.0, 4.0, "#f1e6cf", "cornisa", [1.6, 4.0, 6.4], [1.6], [4.0]),
        C2(7.5, 4.2, "#f6f4ef", "alero", [1.8, 5.7], [5.7], [1.8]),
    ], t0=61.5, fondo_max=10.0)
    colon = tramo_calle("Calle Colón", (-400.0, -450.0))
    # frente NE de Colón desde la esquina de Bustillo hasta San Felipe (R0170–R0174), rehecho desde cero el
    # 2026-11-23: casona del mirador, casa de modillones, casa de tiendas y casa antigua, ver colon_ne.py
    import colon_ne
    colon_ne.construir(col)
    casas_de_frente(col, "AMP_S_colon_so", colon, -1, [
        C2(7.4, 4.2, "#f6f4ef", "alero", [1.6, 3.7, 5.8], [3.7], [1.6, 5.8]),
        C2(7.2, 4.0, "#f1e6cf", "cornisa", [1.6, 5.6], [1.6], [5.6]),
    ], t0=80.4, fondo_max=9.0)
    hilera_sobre_linea(col, "AMP_S_plazuela_so", so_a, so_b, [
        (9.5, 2, 4.2, "#f6f4ef", "alero", dict(vanos=[1.6, 4.75, 7.9], puertas=[4.75], balcones=[1.6, 7.9])),
        (9.0, 2, 4.0, "#f3e6d3", "alero", dict(vanos=[1.5, 4.5, 7.5], puertas=[1.5], balcones=[4.5])),
        (8.5, 2, 4.2, "#f6f4ef", "cornisa", dict(vanos=[1.5, 4.25, 7.0], puertas=[7.0], balcones=[1.5, 4.25])),
    ], fondo=9.0, libres=CAMS_REV)

esquina_mirador()
explanada()
san_felipe()
convento()
import plazuela_cochabamba  # noqa: E402
plazuela_cochabamba.construir(col, OSM["plazuela"], osm)
entorno()
from vecinos_claude import preparar  # noqa: E402
preparar(col, MID)          # recorte contra el muro del vecino (SIAMESES)
exportar(AGENTE, MID)
