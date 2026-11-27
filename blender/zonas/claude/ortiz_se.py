"""Calle Nicolás Ortiz, vereda SE, de la Facultad a la esquina del mirador (R0191–R0198), rehecha desde cero el
2026-11-24 con las fotos del usuario. `t` es la distancia a lo largo del eje de la calle desde la esquina con Azurduy
(la de la Facultad); la línea de fachada va a 6 m del eje, como las demás casas de la cuadra.

En cada fachada `s` crece con `t` (hacia la esquina del mirador): en las fotos, tomadas mirando al SE, lo de la
IZQUIERDA tiene `s` mayor.

  t  27,0–37,5  casa de los "4 Siglos" (R0191, der.): columnas blancas con capitel, tableros con filete ocre, balcones
                de hierro con persianas, rejas labradas abajo, zócalo de sillares pardos, cornisa y pretil de tejuelas.
  t  37,5–47,0  casa en venta (R0191 izq., R0192 der.): dos plantas gris claro, balcón corrido con baranda de tubo y
                letrero, persianas, guardapolvos, puerta y tienda abajo, zócalo de sillares, pretil de tejuelas.
  t  47,0–59,0  casa del balcón de cajón (R0192 izq.): alero de tejas, dos balcones de panza sobre canes, balcón
                cerrado de madera con vidrios de colores en el eje, portón grande debajo, zócalo de piedra bola.
  t  59,0–73,0  casa de la panadería (R0193): alero de tejas, tres balcones de panza sobre canes, marcos grises,
                panadería con rejas abiertas, librería y portón de madera, zócalo de piedra bola, farol de pared.
  t  73,0–83,5  casa de la farmacia (R0194): alero de tejas, balcón cerrado de madera entre dos balcones con marcos
                grises almohadillados, farmacia con cruz verde y portón del instituto de inglés.
  t  83,5–…     casona de pilastras crema (R0195–R0198): pilastras estriadas con capitel corintio, balcones sobre
                losas crema, vanos con marco crema, zócalo bajo de sillares, cornisa y pretil liso; sigue en la casona
                de la esquina del mirador (AMP_S.esquina_mirador usa `fachada_crema` en su cara a Ortiz).
"""
import math

import colon_cuadra as cc_
import facultad
from piezas_claude import mirador
from san_felipe_costado import sillares

BL = "#f6f4ef"
GRIS = "#8e9192"
MADERA = "#5a261c"
CAJON = "#6a2a20"
HIERRO = "#1d1d1d"
OCRE = "#d6a245"
CREMA = "#d8c4a2"
PARDO = ("#86705e", "#7a624f", "#917a66", "#6f5a49", "#8a6c58")
BOLA = ("#8a7a66", "#6f6352", "#9d8b74", "#7c6a58", "#a49480")
ARENISCA = ("#cdb89a", "#c2ab8b", "#d6c3a6", "#bba283")


# ---------------------------------------------------------------------------------------------------- piezas
def zocalo_bola(f, s0, s1, h, desde):
    """Zócalo de piedra bola (cantos rodados) con junta clara, como en R0192/R0193."""
    f.caja(s0, s1, desde, h, 0.0, 0.05, "zocalo_piedra", "#cfc6b6")
    fila, hh = 0, desde + 0.1
    while hh < h - 0.12:
        k = s0 + (0.17 if fila % 2 else 0.04)
        j = 0
        while k < s1 - 0.25:
            w = 0.24 + 0.08 * ((j * 7 + fila * 3) % 3)
            f.caja(k, min(k + w, s1 - 0.03), hh, hh + 0.2, 0.05, 0.1, "zocalo_piedra", BOLA[(j + fila) % len(BOLA)])
            k += w + 0.05
            j += 1
        hh += 0.24
        fila += 1


def zocalo_sillares(f, s0, s1, h, desde, colores=PARDO, semilla=1):
    f.caja(s0, s1, desde, h, -0.02, 0.06, "zocalo_piedra", colores[0])
    sillares(f, s0, s1, max(desde + 0.3, 0.0), h - 0.02, 0.06, alto=0.36, largo=(0.5, 0.9), colores=colores,
             rojo=0.1, semilla=semilla)
    f.caja(s0, s1, h - 0.02, h + 0.08, 0.0, 0.1, "piedra", colores[2])


def marco_gris(f, s, h0, ancho, alto, almohadillado=False, w=0.2):
    """Marco gris de vano (R0193/R0194); almohadillado: dovelas alternadas que sobresalen."""
    a = ancho / 2
    f.caja(s - a - w, s - a, h0, h0 + alto + w, 0.0, 0.07, "moldura", GRIS)
    f.caja(s + a, s + a + w, h0, h0 + alto + w, 0.0, 0.07, "moldura", GRIS)
    f.caja(s - a - w, s + a + w, h0 + alto, h0 + alto + w, 0.0, 0.07, "moldura", GRIS)
    if almohadillado:
        hh, k = h0, 0
        while hh < h0 + alto:
            if k % 2 == 0:
                for x0 in (s - a - w - 0.06, s + a):
                    f.caja(x0, x0 + w + 0.06, hh, min(hh + 0.28, h0 + alto), 0.0, 0.1, "moldura", GRIS)
            hh += 0.28
            k += 1
    f.caja(s - a - w - 0.12, s + a + w + 0.12, h0 + alto + w, h0 + alto + w + 0.12, 0.0, 0.16, "moldura", GRIS)


def balcon_panza(f, s, h, ancho=1.6, vuelo=0.55, canes=4, losa=BL, can_color="#4a2a1c"):
    """Balcón de panza (baranda abombada de hierro) sobre losa y canes de madera."""
    s0, s1 = s - ancho / 2, s + ancho / 2
    f.caja(s0, s1, h - 0.15, h, 0.0, vuelo, "moldura", losa)
    for k in range(canes):
        x = s0 + 0.2 + (ancho - 0.4) * k / max(1, canes - 1)
        f.caja(x - 0.06, x + 0.06, h - 0.34, h - 0.15, 0.0, vuelo * 0.85, "madera", can_color)
    for j, (hh, dd) in enumerate(((0.05, vuelo - 0.08), (0.35, vuelo + 0.06), (0.7, vuelo + 0.04), (0.98, vuelo - 0.04))):
        f.caja(s0 + 0.04, s1 - 0.04, h + hh, h + hh + 0.035, dd - 0.02, dd + 0.02, "hierro", HIERRO)
    k = s0 + 0.08
    while k < s1 - 0.05:                                                         # barrotes que se abomban
        f.caja(k - 0.012, k + 0.012, h + 0.05, h + 0.35, vuelo - 0.08, vuelo + 0.06, "hierro", HIERRO)
        f.caja(k - 0.012, k + 0.012, h + 0.35, h + 1.0, vuelo + 0.0, vuelo + 0.06, "hierro", HIERRO)
        k += 0.13
    for lado in (s0 + 0.05, s1 - 0.05):
        f.caja(lado - 0.015, lado + 0.015, h, h + 1.0, 0.0, vuelo, "hierro", HIERRO)


def cuarterones(f, s, h, ancho=1.15, alto=2.25, color=MADERA, vidrios="#2b2e33"):
    """Puerta-ventana de madera con cuarterones (vidrios chicos), para los balcones de las casas."""
    a = ancho / 2
    f.caja(s - a, s + a, h, h + alto, -0.14, -0.12, "vidrio", vidrios)
    for k in (-a, -0.035, a - 0.07):
        f.caja(s + k, s + k + 0.07, h, h + alto, -0.12, -0.07, "marco_ventana", color)
    f.caja(s - a, s + a, h + alto - 0.07, h + alto, -0.12, -0.07, "marco_ventana", color)
    f.caja(s - a, s + a, h, h + 0.35, -0.12, -0.08, "marco_ventana", color)
    for x in (s - a / 2, s + a / 2):
        f.caja(x - 0.015, x + 0.015, h + 0.35, h + alto, -0.12, -0.09, "marco_ventana", color)
    for j in range(1, 5):
        hh = h + 0.35 + (alto - 0.42) * j / 5
        f.caja(s - a, s + a, hh - 0.015, hh + 0.015, -0.12, -0.09, "marco_ventana", color)


def persianas(f, s, h, ancho=1.15, alto=2.3, abiertas=False, color="#4a2a1e"):
    """Puerta-ventana con persianas de tablillas (cerradas, o abiertas contra el muro)."""
    a = ancho / 2
    if abiertas:
        f.caja(s - a, s + a, h, h + alto, -0.14, -0.12, "vidrio", "#2b2e33")
        for k in (-a, -0.035, a - 0.07):
            f.caja(s + k, s + k + 0.07, h, h + alto, -0.12, -0.07, "marco_ventana", color)
        for x0 in (s - a - 0.6, s + a):                                         # hojas abiertas
            f.caja(x0, x0 + 0.6, h, h + alto, 0.0, 0.05, "madera", color)
        return
    f.caja(s - a, s + a, h, h + alto, -0.12, -0.08, "madera", color)
    hh = h + 0.1
    while hh < h + alto - 0.1:
        f.caja(s - a + 0.06, s + a - 0.06, hh, hh + 0.05, -0.08, -0.05, "madera", "#3a2016")
        hh += 0.13
    f.caja(s - 0.02, s + 0.02, h, h + alto, -0.08, -0.04, "madera", "#2a160e")


def puerta(f, s, ancho, alto, color=MADERA, tableros=True):
    a = ancho / 2
    f.caja(s - a, s + a, -0.05, alto, -0.12, -0.08, "madera", color)
    f.caja(s - 0.02, s + 0.02, 0.0, alto, -0.08, -0.05, "madera", "#2a140c")
    if tableros:
        for x0 in (s - a + 0.12, s + 0.1):
            for hh in (0.3, alto * 0.42, alto * 0.72):
                f.caja(x0, x0 + a - 0.22, hh, hh + alto * 0.22, -0.08, -0.05, "madera", "#6e3424")


def tienda(f, s, ancho, alto, abierta=True):
    """Local abierto: hueco oscuro con estantes y mercadería apenas visibles."""
    a = ancho / 2
    f.caja(s - a, s + a, -0.05, alto, -0.3, -0.28, "vidrio", "#1f1c1a")
    if abierta:
        for hh in (0.6, 1.2, 1.8):
            f.caja(s - a + 0.1, s + a - 0.1, hh, hh + 0.04, -0.28, -0.2, "madera", "#6b5444")


def rejas_abiertas(f, s, ancho, alto):
    """Hojas de reja abiertas contra el muro a los dos lados del vano (panadería, librería)."""
    a = ancho / 2
    for x0 in (s - a - 0.75, s + a + 0.05):
        f.caja(x0, x0 + 0.7, 0.0, 0.04, 0.02, 0.06, "hierro", HIERRO)
        f.caja(x0, x0 + 0.7, alto - 0.04, alto, 0.02, 0.06, "hierro", HIERRO)
        k = x0
        while k <= x0 + 0.71:
            f.caja(k - 0.012, k + 0.012, 0.0, alto, 0.02, 0.06, "hierro", HIERRO)
            k += 0.1
        for hh in (alto * 0.33, alto * 0.66):
            f.caja(x0, x0 + 0.7, hh - 0.015, hh + 0.015, 0.02, 0.06, "hierro", HIERRO)


def balcon_cajon(f, s, h, ancho, alto=2.3, vuelo=0.8, colores=False):
    """Balcón cerrado de madera (cajón) sobre canes tallados, con banda de vidrios de colores arriba (R0192, R0194)."""
    mirador(f, s, h, ancho=ancho, alto=alto, vuelo=vuelo, base=("madera", "#5a2219"), madera=("marco_ventana", CAJON),
            antepecho=("madera", CAJON))
    s0, s1 = s - ancho / 2, s + ancho / 2
    k = s0 + 0.15
    while k < s1 - 0.1:                                                          # tableros del antepecho
        f.caja(k, min(k + 0.5, s1 - 0.1), h + 0.1, h + 0.5, vuelo, vuelo + 0.02, "madera", "#7a3428")
        k += 0.58
    if colores:
        n = max(3, int(ancho / 0.4))
        for j in range(n):
            x = s0 + 0.08 + (ancho - 0.16) * (j + 0.5) / n
            c = ("#3b6fa0", "#3f8a55", "#b8a040", "#a04a3a")[j % 4]
            f.caja(x - 0.12, x + 0.12, h + alto - 0.42, h + alto - 0.12, vuelo - 0.06, vuelo - 0.04, "vidrio", c)
    for j in range(5):                                                           # canes tallados con colgante
        x = s0 + 0.2 + (ancho - 0.4) * j / 4
        f.caja(x - 0.08, x + 0.08, h - 0.95, h - 0.5, 0.0, vuelo * 0.9, "madera", "#5a2219")
        q = f.punto(x, h - 1.02, vuelo * 0.85)
        f.c.esfera(q.x, q.y, q.z, 0.07, "madera", "#5a2219", segmentos=6)
    f.caja(s0 - 0.15, s1 + 0.15, h + alto + 0.18, h + alto + 0.3, 0.0, vuelo + 0.2, "teja", "#a4523a")   # tejadillo


def farol_pared(f, s, h):
    f.caja(s - 0.03, s + 0.03, h - 0.05, h + 0.05, 0.0, 0.3, "hierro", HIERRO)
    q = f.punto(s, h - 0.3, 0.3)
    f.c.cilindro(q.x, q.y, q.z, q.z + 0.3, 0.1, "vidrio", "#efe2b5", lados=6, radio_arriba=0.13)
    f.c.cilindro(q.x, q.y, q.z + 0.3, q.z + 0.42, 0.15, "hierro", HIERRO, lados=6, radio_arriba=0.03)


def alero_borde(f, L, h):
    """Tabla blanca y moldura bajo el alero de tejas."""
    f.caja(0, L, h - 0.35, h - 0.2, 0.0, 0.12, "moldura", "#ece8df")
    f.caja(0, L, h - 0.2, h, 0.0, 0.3, "moldura", BL)


# ---------------------------------------------------------------------------------------------------- casas
def cuatro_siglos(f0, L, alto, off, desde):
    f = cc_._Frente(f0)
    anchos = (1.4, 2.6, 2.4, 2.6, 1.4)
    k = L / sum(anchos)
    cols, x = [0.0], 0.0
    for a in anchos:
        x += a * k
        cols.append(x)
    hz = 1.5 + off
    zocalo_sillares(f, 0, L, hz, desde, semilla=31)
    h1 = 5.0 + off                                                               # entablamento entre plantas
    h_cor = alto - 1.4 + off
    for c in cols:                                                               # pedestales y columnas blancas
        c = min(max(c, 0.3), L - 0.3)
        f.caja(c - 0.32, c + 0.32, desde, hz + 0.05, 0.0, 0.2, "zocalo_piedra", "#6f5747")
        for h0, h_ in ((hz + 0.05, h1 - 0.35), (h1 + 0.55, h_cor - 0.4)):
            q = f.punto(c, h0, 0.12)
            f.c.cilindro(q.x, q.y, q.z, q.z + (h_ - h0), 0.19, "moldura", "#f7f5f0", lados=10)
            f.caja(c - 0.27, c + 0.27, h_ - 0.05, h_ + 0.35, 0.0, 0.32, "moldura", "#ece7dc")       # capitel
            f.caja(c - 0.3, c + 0.3, h_ + 0.25, h_ + 0.38, 0.0, 0.36, "pintura_acento", OCRE)
    f.caja(0, L, h1 - 0.1, h1 + 0.25, 0.0, 0.2, "pintura_acento", OCRE)
    f.caja(0, L, h1 + 0.25, h1 + 0.55, 0.0, 0.14, "moldura", "#f2efe8")
    for i in range(len(anchos)):
        s0, s1 = cols[i], cols[i + 1]
        sm = (s0 + s1) / 2
        ventana = i in (1, 3)
        for h0, h_ in ((hz + 0.25, h1 - 0.35), (h1 + 0.8, h_cor - 0.55)):
            if not ventana:                                                      # tablero con filete ocre
                f.caja(s0 + 0.35, s1 - 0.35, h0 + 0.2, h_ - 0.2, 0.0, 0.03, "muro", "#f1eee6")
                for a, b, c_, d_ in ((s0 + 0.35, s0 + 0.42, h0 + 0.2, h_ - 0.2), (s1 - 0.42, s1 - 0.35, h0 + 0.2, h_ - 0.2),
                                     (s0 + 0.35, s1 - 0.35, h0 + 0.2, h0 + 0.27), (s0 + 0.35, s1 - 0.35, h_ - 0.27, h_ - 0.2)):
                    f.caja(a, b, c_, d_, 0.03, 0.05, "pintura_acento", OCRE)
        if ventana:
            # abajo: ventana alta con reja labrada y filete ocre
            w = 1.2
            cc_.ventana_recta(f, sm, hz + 0.45, w, 2.6, marco="#f1eee6", carpinteria=MADERA, reja=True)
            for a, b in ((sm - w / 2 - 0.42, sm - w / 2 - 0.35), (sm + w / 2 + 0.35, sm + w / 2 + 0.42)):
                f.caja(a, b, hz + 0.3, hz + 3.35, 0.06, 0.08, "pintura_acento", OCRE)
            f.caja(sm - w / 2 - 0.42, sm + w / 2 + 0.42, hz + 3.28, hz + 3.35, 0.06, 0.08, "pintura_acento", OCRE)
            for hh in (hz + 0.7, hz + 1.5, hz + 2.3):                            # volutas de la reja
                for dx in (-0.3, 0.0, 0.3):
                    cc_._anillo(f, sm + dx, hh, -0.02, 0.13, n=8)
            # arriba: persianas, balcón de hierro y guardapolvo con talla ocre
            persianas(f, sm, h1 + 0.75, ancho=1.15, alto=2.35)
            cc_.balcon_forjado(f, sm, h1 + 0.75, ancho=1.75, vuelo=0.45, losa="#f2efe8", menulas=3)
            f.caja(sm - 0.95, sm + 0.95, h1 + 3.25, h1 + 3.4, 0.0, 0.22, "moldura", "#f2efe8")
            f.caja(sm - 0.7, sm + 0.7, h1 + 3.4, h1 + 3.62, 0.0, 0.1, "pintura_acento", OCRE)
            for dx in (-0.85, 0.85):
                f.caja(sm + dx - 0.07, sm + dx + 0.07, h1 + 2.85, h1 + 3.25, 0.0, 0.16, "pintura_acento", OCRE)
    facultad.remate(f, L, h_cor)


def casa_venta(f0, L, alto, off, desde):
    f = cc_._Frente(f0)
    MURO = "#e7e4dc"
    zocalo_sillares(f, 0, L, 1.0 + off, desde, semilla=37)
    # planta baja: puerta (izquierda en la foto, s alta) y tienda abierta (derecha), con guardapolvos rectos
    sp, st = 0.88 * L, 0.36 * L
    puerta(f, sp, 1.25, 2.6 + off)
    f.caja(sp - 0.8, sp + 0.8, 2.6 + off, 2.7 + off, 0.0, 0.08, "moldura", MURO)
    tienda(f, st, 2.4, 2.75 + off)
    for s_, a in ((sp, 1.6), (st, 2.6)):
        f.caja(s_ - a / 2 - 0.15, s_ + a / 2 + 0.15, 3.05 + off, 3.45 + off, 0.0, 0.18, "moldura", "#f1efe9")
    f.caja(st - 1.4, st - 1.2, 0.5 + off, 2.2 + off, 0.0, 0.06, "letrero", "#c43a2c")
    # planta alta: dos puertas-ventana con persianas y balcón corrido de baranda de tubo con el letrero
    h2 = 4.6 + off
    for s_, ab in ((0.74 * L, False), (0.3 * L, True)):
        persianas(f, s_, h2, ancho=1.1, alto=2.3, abiertas=ab)
        f.caja(s_ - 0.85, s_ + 0.85, h2 + 2.55, h2 + 2.8, 0.0, 0.18, "moldura", "#f1efe9")
    b0, b1 = 0.18 * L, 0.96 * L
    f.caja(b0, b1, h2 - 0.25, h2, 0.0, 0.7, "moldura", "#ecebe5")
    f.caja(b0 + 0.05, b1 - 0.05, h2 - 0.4, h2 - 0.25, 0.0, 0.62, "moldura", "#d9d6cf")
    for hh in (0.05, 0.5, 0.95):
        f.caja(b0, b1, h2 + hh, h2 + hh + 0.04, 0.64, 0.68, "metal", "#9ea2a4")
    for x in [b0 + 0.03 + k * 0.9 for k in range(int((b1 - b0) / 0.9) + 1)] + [b1 - 0.03]:
        f.caja(x - 0.02, x + 0.02, h2, h2 + 1.0, 0.64, 0.68, "metal", "#9ea2a4")
    f.caja(0.36 * L - 0.65, 0.36 * L + 0.65, h2 + 0.1, h2 + 0.95, 0.7, 0.73, "letrero", "#e0a020")
    f.caja(0.36 * L - 0.55, 0.36 * L + 0.55, h2 + 0.45, h2 + 0.62, 0.73, 0.74, "letrero", "#b8262a")
    # cornisa y pretil de tejuelas con pedestales
    h_cor = alto - 0.8 + off
    f.caja(0, L, h_cor - 0.3, h_cor - 0.1, 0.0, 0.18, "moldura", "#ece9e2")
    f.caja(0, L, h_cor - 0.1, h_cor + 0.08, 0.0, 0.32, "moldura", "#f1efe9")
    zp = h_cor + 0.08
    for fila in range(2):
        k = 0.15 + (0.12 if fila else 0.0)
        while k < L - 0.3:
            f.caja(k, k + 0.2, zp + 0.05 + fila * 0.2, zp + 0.21 + fila * 0.2, 0.04, 0.08, "moldura", "#e9e5dc")
            k += 0.24
    f.caja(0, L, zp, zp + 0.5, 0.0, 0.04, "moldura", "#dcd7cc")
    f.caja(0, L, zp + 0.5, zp + 0.6, 0.0, 0.14, "moldura", "#f1efe9")
    for s_ in (0.25, L * 0.36, L * 0.68, L - 0.25):
        f.caja(s_ - 0.22, s_ + 0.22, zp, zp + 0.72, 0.0, 0.16, "moldura", "#f1efe9")


def casa_cajon(f0, L, alto, off, desde):
    f = cc_._Frente(f0)
    sc, sb2, sb1 = 2.6, 6.9, 10.6
    zocalo_bola(f, 0.2, L - 0.2, 0.85 + off, desde)
    # planta baja: portón grande bajo el cajón, puerta tallada y local de fotos, con marcos grises
    puerta(f, sc, 2.4, 3.0 + off, color="#4e1f16")
    marco_gris(f, sc, 0.0, 2.4, 3.0 + off, w=0.18)
    puerta(f, sb2 + 0.2, 1.4, 2.85 + off, color="#4e1f16")
    marco_gris(f, sb2 + 0.2, 0.0, 1.4, 2.85 + off, w=0.16)
    tienda(f, sb1 + 0.3, 1.5, 2.7 + off)
    marco_gris(f, sb1 + 0.3, 0.0, 1.5, 2.7 + off, w=0.15)
    f.caja(sb1 - 0.35, sb1 - 0.05, 0.6 + off, 2.2 + off, 0.06, 0.1, "letrero", "#d9a43a")
    farol_pared(f, 8.6, 3.9 + off)
    # planta alta
    h2 = 4.55 + off
    for s_ in (sb2, sb1):
        cuarterones(f, s_, h2 + 0.05, ancho=1.15, alto=2.2)
        marco_gris(f, s_, h2 + 0.05, 1.15, 2.2, w=0.16)
        balcon_panza(f, s_, h2 + 0.05, ancho=1.7, canes=4)
    balcon_cajon(f0, sc, h2 + 0.15, ancho=3.2, alto=2.4, vuelo=0.8, colores=True)
    alero_borde(f, L, alto + off)


def casa_panaderia(f0, L, alto, off, desde):
    f = cc_._Frente(f0)
    sl, sp, spa = 1.4, 6.1, 11.9
    zocalo_bola(f, 0.0, L, 0.75 + off, desde)
    # planta baja: portón (s baja), librería con rejas abiertas y panadería con rejas abiertas y gradas
    puerta(f, sl, 1.9, 3.1 + off)
    marco_gris(f, sl, 0.0, 1.9, 3.1 + off, w=0.22)
    tienda(f, sp, 1.6, 2.9 + off)
    marco_gris(f, sp, 0.0, 1.6, 2.9 + off, w=0.2)
    rejas_abiertas(f, sp, 1.6 + 0.4, 2.9 + off)
    f.caja(sp - 1.3, sp - 0.9, 0.6 + off, 2.6 + off, 0.08, 0.12, "letrero", "#c43a2c")
    f.caja(sp + 0.9, sp + 1.3, 0.6 + off, 2.6 + off, 0.08, 0.12, "letrero", "#d9a43a")
    tienda(f, spa, 1.7, 3.0 + off)
    marco_gris(f, spa, 0.0, 1.7, 3.0 + off, w=0.2)
    rejas_abiertas(f, spa, 1.7 + 0.4, 3.0 + off)
    q = f.punto(spa - 1.6, 3.45 + off, 0.5)                                      # letrero redondo de la panadería
    f.c.cilindro(q.x, q.y, q.z - 0.38, q.z + 0.38, 0.06, "letrero", "#c99a3a", lados=12)
    f.caja(spa - 1.6 - 0.03, spa - 1.6 + 0.03, 3.85 + off, 3.95 + off, 0.0, 0.5, "hierro", HIERRO)
    farol_pared(f, 2.6, 4.0 + off)
    # faja gris entre plantas
    f.caja(0, L, 4.25 + off, 4.38 + off, 0.0, 0.08, "moldura", "#a7a9a8")
    h2 = 4.65 + off
    for s_ in (1.4, 6.3, 11.6):
        cuarterones(f, s_, h2, ancho=1.15, alto=2.25)
        marco_gris(f, s_, h2, 1.15, 2.25, w=0.2)
        balcon_panza(f, s_, h2, ancho=1.75, canes=4)
    alero_borde(f, L, alto + off)


def casa_farmacia(f0, L, alto, off, desde):
    f = cc_._Frente(f0)
    sg, sc, sf = 2.6, 5.5, 8.6
    zocalo_sillares(f, 0.0, L, 0.6 + off, desde, colores=ARENISCA, semilla=41)
    # planta baja: portón del instituto (s baja) y farmacia con cruz verde
    puerta(f, sg, 2.4, 3.0 + off, color="#5a2a1c")
    marco_gris(f, sg, 0.0, 2.4, 3.0 + off, almohadillado=True, w=0.24)
    f.caja(sg - 0.9, sg - 0.2, 1.0 + off, 2.2 + off, 0.06, 0.08, "letrero", "#e9e2c8")
    f.caja(sg + 1.6, sg + 2.4, 2.4 + off, 2.9 + off, 0.02, 0.05, "letrero", "#e6ecf0")
    tienda(f, sf, 1.4, 2.8 + off)
    marco_gris(f, sf, 0.0, 1.4, 2.8 + off, almohadillado=True, w=0.22)
    f.caja(sf - 0.75, sf + 0.75, 3.15 + off, 3.6 + off, 0.04, 0.08, "letrero", "#9a3a28")   # letrero de la farmacia
    cc_.ventana_recta(f, sf, 3.75 + off, 1.1, 0.55, carpinteria="#2a2a2a", reja=True)
    f.caja(L - 0.64, L - 0.56, 3.55 + off, 3.65 + off, 0.0, 0.3, "hierro", HIERRO)   # cruz verde en bandera
    f.caja(L - 0.67, L - 0.53, 2.7 + off, 3.5 + off, 0.3, 0.95, "letrero", "#22a07a")
    f.caja(L - 0.69, L - 0.51, 3.0 + off, 3.2 + off, 0.5, 0.75, "letrero", "#f4f2ec")
    f.caja(L - 0.69, L - 0.51, 2.85 + off, 3.35 + off, 0.57, 0.68, "letrero", "#f4f2ec")
    # planta alta
    f.caja(0, L, 4.25 + off, 4.4 + off, 0.0, 0.1, "moldura", GRIS)
    h2 = 4.7 + off
    for s_ in (sg + 0.1, sf):
        cuarterones(f, s_, h2, ancho=1.1, alto=2.3, vidrios="#5a3a5a")
        marco_gris(f, s_, h2, 1.1, 2.3, almohadillado=True, w=0.22)
        cc_.balcon_forjado(f, s_, h2, ancho=1.6, vuelo=0.45, losa=GRIS, menulas=2)
    balcon_cajon(f0, sc, h2 + 0.1, ancho=2.3, alto=2.5, vuelo=0.75)
    alero_borde(f, L, alto + off)


def fachada_crema(f0, L, alto, off, desde, bahias=None, entradas=None, borde_s0=True, farol_en=None):
    """Casona blanca de pilastras crema estriadas con capitel (R0195, R0197). bahias: n.º de módulos; entradas: tipo
    de vano bajo cada módulo ('puerta', 'tienda', 'portal')."""
    f = cc_._Frente(f0)
    n = bahias or max(1, round(L / 4.1))
    hz = 0.65 + off
    zocalo_sillares(f, 0, L, hz, desde, colores=ARENISCA, semilla=int(L * 7))
    h1 = 4.55 + off                                                              # faja bajo los balcones
    h_cor = alto - 0.9 + off
    for k in range(n + 1):                                                       # pilastras estriadas
        s = L * k / n
        w = 0.55 if (k == 0 and borde_s0) else 0.42
        s = min(max(s, w / 2), L - w / 2)
        f.caja(s - w / 2, s + w / 2, hz, h_cor - 0.45, 0.0, 0.1, "moldura", CREMA)
        for dx in (-w / 4, 0.0, w / 4):
            f.caja(s + dx - 0.025, s + dx + 0.025, hz + 0.3, h_cor - 0.75, 0.1, 0.12, "moldura", "#c9b28c")
        f.caja(s - w / 2 - 0.06, s + w / 2 + 0.06, h_cor - 0.75, h_cor - 0.45, 0.0, 0.18, "moldura", "#e2d2b4")  # capitel
        for dx in (-w / 3, w / 3):                                               # volutas
            q = f.punto(s + dx, h_cor - 0.6, 0.2)
            f.c.esfera(q.x, q.y, q.z, 0.07, "moldura", "#e2d2b4", segmentos=6)
    f.caja(0, L, h1 - 0.15, h1 + 0.02, 0.0, 0.08, "moldura", CREMA)
    tipos = entradas or ["tienda", "puerta", "portal"]
    for k in range(n):
        sm = L * (k + 0.5) / n
        t = tipos[k % len(tipos)]
        aw = {"tienda": 1.5, "puerta": 1.2, "portal": 2.0}[t]
        ah = {"tienda": 2.9, "puerta": 2.85, "portal": 3.0}[t] + off
        if t == "puerta":
            puerta(f, sm, aw, ah)
        else:
            tienda(f, sm, aw, ah)
        for a, b in ((sm - aw / 2 - 0.22, sm - aw / 2), (sm + aw / 2, sm + aw / 2 + 0.22)):
            f.caja(a, b, 0.0, ah + 0.22, 0.0, 0.1, "moldura", CREMA)
        f.caja(sm - aw / 2 - 0.22, sm + aw / 2 + 0.22, ah, ah + 0.22, 0.0, 0.1, "moldura", CREMA)
        f.caja(sm - aw / 2 - 0.3, sm + aw / 2 + 0.3, ah + 0.22, ah + 0.34, 0.0, 0.15, "moldura", "#e2d2b4")
        h2 = h1 + 0.1
        cuarterones(f, sm, h2, ancho=1.1, alto=2.3)
        for a, b in ((sm - 0.55 - 0.24, sm - 0.55), (sm + 0.55, sm + 0.55 + 0.24)):
            f.caja(a, b, h2, h2 + 2.54, 0.0, 0.09, "moldura", CREMA)
        f.caja(sm - 0.79, sm + 0.79, h2 + 2.3, h2 + 2.54, 0.0, 0.09, "moldura", CREMA)
        for dx in (-0.9, 0.9):                                                   # orejas
            f.caja(sm + dx - 0.12, sm + dx + 0.12, h2 + 2.2, h2 + 2.54, 0.0, 0.1, "moldura", CREMA)
        f.caja(sm - 0.95, sm + 0.95, h2 + 2.54, h2 + 2.66, 0.0, 0.16, "moldura", "#e2d2b4")
        cc_.balcon_forjado(f, sm, h2, ancho=1.65, vuelo=0.45, losa=CREMA, menulas=3)
    # friso, cornisa y pretil liso con albardilla crema
    f.caja(0, L, h_cor - 0.45, h_cor - 0.3, 0.0, 0.1, "moldura", CREMA)
    f.caja(0, L, h_cor, h_cor + 0.14, 0.0, 0.14, "moldura", CREMA)
    f.caja(0, L, h_cor + 0.14, h_cor + 0.36, 0.0, 0.3, "moldura", "#e2d2b4")
    f.caja(0, L, h_cor + 0.36, h_cor + 0.9, 0.0, 0.06, "moldura", "#ece6da")
    f.caja(0, L, h_cor + 0.9, h_cor + 1.0, 0.0, 0.12, "moldura", CREMA)
    if farol_en is not None:
        cc_.farol_brazo(f, farol_en, h_cor - 1.0)


def casa_crema(f0, L, alto, off, desde):
    fachada_crema(f0, L, alto, off, desde, entradas=["portal", "puerta", "tienda"], farol_en=0.6)


# alto de cada casa = pisos × alto de piso (como en casas_de_frente)
CASAS = [  # (ancho, pisos, alto_piso, muro, remate, función)
    (10.5, 2, 5.1, "#f4f2ec", "plano", cuatro_siglos),
    (9.5, 2, 4.5, "#e7e4dc", "plano", casa_venta),
    (12.0, 2, 3.95, "#f6f4ef", "alero", casa_cajon),
    (14.0, 2, 4.0, "#f6f4ef", "alero", casa_panaderia),
    (10.5, 2, 4.05, "#f6f4ef", "alero", casa_farmacia),
]
T0 = 27.0
T_CREMA = T0 + sum(c[0] for c in CASAS)


def t_de(tramo, x, y):
    """Distancia a lo largo del eje del tramo del punto (x, y) proyectado (muestreo cada 0,25 m)."""
    from piezas_claude import sobre_calle
    mejor = min((((sobre_calle(tramo, k * 0.25, 0)[0] - x) ** 2 + (sobre_calle(tramo, k * 0.25, 0)[1] - y) ** 2), k * 0.25)
                for k in range(0, 800))
    return mejor[1]


def construir(col, tramo, t_mirador):
    """Las casas de la vereda SE entre la Facultad (t = T0) y la casona del mirador (t_mirador)."""
    from piezas_claude import casas_de_frente
    casas = [(a, p, ap, m, r, dict(a_mano=fn)) for a, p, ap, m, r, fn in CASAS]
    if t_mirador - T_CREMA > 3.0:
        # fondo fijo: el lienzo de atrás llega hasta la línea de fachada junto a la casona (lo recorta preparar())
        casas.append((t_mirador - T_CREMA - 0.05, 2, 4.4, "#f4f2ec", "plano", dict(a_mano=casa_crema, fondo=9.0)))
    return casas_de_frente(col, "AMP_S_ortiz_se", tramo, -1, casas, t0=T0, fondo_max=11.0)


def faroles(c, tramo, altura_suelo):
    """Faroles de poste junto al bordillo, donde los muestran las fotos (R0192 y R0194/R0195)."""
    from base_plazas import farol_poste
    from piezas_claude import sobre_calle
    d = tramo["ancho"] / 2 - tramo["vereda"] + 0.45
    for t in (T0 + 10.5 + 9.5 + 5.6, T_CREMA - 0.3):
        x, y, _, _ = sobre_calle(tramo, t, -d)
        farol_poste(c, x, y, altura_suelo(x, y) + 0.15, alto=3.9)
