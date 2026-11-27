"""Facultad de Humanidades, esquina Nicolás Ortiz × Azurduy (R0186, R0189, R0190), rehecha desde cero el 2026-11-24
con las fotos del usuario a resolución completa ("falta mucho detalle, borrar y rehacer").

Dos plantas de cal blanca con molduras ocres:
- zócalo de sillares de arenisca parda-rosada con la cara superior a nivel (crece hacia la esquina, R0186);
- planta baja: ventanas altas de madera roja con cuarterones, marco blanco, pilastras ocres a los lados con basa y
  capitel y dintel ocre; el portón de madera tallada en el eje, entre pilastras, con gradas;
- faja ocre entre plantas con relieves de volutas y macetas de barro bajo los balcones;
- planta alta: puertas-ventana rojas con cuarterones, marco ocre con orejas, friso tallado y cornisa; balcón de hierro
  forjado sobre ménsulas ocres; el eje central entre dos pilastras ocres con capitel, con balcón más ancho;
- remate: friso blanco con medallones ocres, dentículos, modillones, cornisa ocre y pretil de tejuelas blancas con
  pedestales ocres; la esquina queda blanca (sin esquinero) y lleva un farol de brazo.
"""
import math

import colon_cuadra as cc_
from san_felipe_costado import sillares

OCRE = "#d6a245"
OCRE2 = "#bf8a2c"
CAL = "#f7f4ee"
ROJO = "#5e1f17"
BARRO = "#b5532f"
ZOCALO = ("#94705c", "#8a6450", "#a07a64", "#7f5a49", "#9c6a58")


def _ventana_cuarterones(f, s, h0, w, alto, d=0.05):
    """Carpintería roja de cuarterones (dos hojas con vidrios chicos)."""
    f.caja(s - w / 2, s + w / 2, h0, h0 + alto, d - 0.02, d - 0.01, "vidrio", "#2b2e33")
    f.caja(s - w / 2, s + w / 2, h0, h0 + 0.08, d - 0.01, d + 0.03, "marco_ventana", ROJO)
    f.caja(s - w / 2, s + w / 2, h0 + alto - 0.08, h0 + alto, d - 0.01, d + 0.03, "marco_ventana", ROJO)
    for k in (-w / 2, -0.03, w / 2 - 0.07):
        f.caja(s + k, s + k + 0.07, h0, h0 + alto, d - 0.01, d + 0.03, "marco_ventana", ROJO)
    for k in (-w / 4, w / 4):
        f.caja(s + k - 0.015, s + k + 0.015, h0, h0 + alto, d - 0.01, d + 0.02, "marco_ventana", ROJO)
    n = max(3, round(alto / 0.4))
    for j in range(1, n):
        hh = h0 + alto * j / n
        f.caja(s - w / 2, s + w / 2, hh - 0.015, hh + 0.015, d - 0.01, d + 0.02, "marco_ventana", ROJO)


def _pilastra(f, s, h0, h1, ancho=0.34, vuelo=0.12, capitel=True):
    f.caja(s - ancho / 2 - 0.05, s + ancho / 2 + 0.05, h0, h0 + 0.25, 0.0, vuelo + 0.04, "pintura_acento", OCRE2)
    f.caja(s - ancho / 2, s + ancho / 2, h0 + 0.25, h1 - 0.3, 0.0, vuelo, "pintura_acento", OCRE)
    if capitel:
        f.caja(s - ancho / 2 - 0.04, s + ancho / 2 + 0.04, h1 - 0.3, h1 - 0.12, 0.0, vuelo + 0.05, "pintura_acento", OCRE2)
        f.caja(s - ancho / 2 - 0.08, s + ancho / 2 + 0.08, h1 - 0.12, h1, 0.0, vuelo + 0.08, "pintura_acento", OCRE)


def planta_baja(f, s, hz, h1, puerta, off):
    if puerta:
        cc_.puerta_madera(f, s, 1.9, hz + 3.3, color="#7a5232", marco=CAL, dintel=False)
        for dz in (0.5, 1.6, 2.6):                                               # tallas de las hojas
            for dx in (-0.48, 0.48):
                f.caja(s + dx - 0.3, s + dx + 0.3, hz + dz, hz + dz + 0.7, -0.03, 0.0, "madera", "#946640")
        for dx in (-1.3, 1.3):
            _pilastra(f, s + dx, hz, h1 - 0.3, ancho=0.38)
        f.caja(s - 1.2, s + 1.2, hz - 0.5, hz, 0.0, 0.45, "piedra", "#8c7a6a")       # grada
        return
    w, alto = 1.2, 2.55
    h0 = hz + 0.25
    _ventana_cuarterones(f, s, h0, w, alto)
    for k in (-1, 1):                                                            # marco blanco y pilastras ocres
        f.caja(s + k * (w / 2 + 0.06) - 0.06, s + k * (w / 2 + 0.06) + 0.06, h0, h0 + alto + 0.1, 0.0, 0.08, "moldura", CAL)
        _pilastra(f, s + k * (w / 2 + 0.32), hz, h0 + alto + 0.35, ancho=0.3, capitel=False)
    f.caja(s - w / 2 - 0.12, s + w / 2 + 0.12, h0 + alto, h0 + alto + 0.12, 0.0, 0.1, "moldura", CAL)
    f.caja(s - w / 2 - 0.55, s + w / 2 + 0.55, h0 + alto + 0.35, h0 + alto + 0.5, 0.0, 0.16, "pintura_acento", OCRE)
    f.caja(s - w / 2 - 0.62, s + w / 2 + 0.62, h0 + alto + 0.5, h0 + alto + 0.6, 0.0, 0.2, "pintura_acento", OCRE2)
    f.caja(s - w / 2 - 0.1, s + w / 2 + 0.1, h0 - 0.12, h0, 0.0, 0.12, "moldura", CAL)          # alféizar
    for k in range(int(w / 0.13) + 1):                                           # reja
        x = s - w / 2 + 0.05 + k * 0.13
        if x < s + w / 2:
            f.caja(x - 0.012, x + 0.012, h0, h0 + alto, 0.1, 0.12, "hierro", "#1d1d1d")


def planta_alta(f, s, h1, h_cor, central):
    w, alto = 1.2, 2.5
    h0 = h1 + 0.15
    _ventana_cuarterones(f, s, h0, w, alto)
    f.caja(s - w / 2 - 0.22, s - w / 2, h0, h0 + alto + 0.2, 0.0, 0.12, "pintura_acento", OCRE)      # marco con orejas
    f.caja(s + w / 2, s + w / 2 + 0.22, h0, h0 + alto + 0.2, 0.0, 0.12, "pintura_acento", OCRE)
    f.caja(s - w / 2 - 0.35, s + w / 2 + 0.35, h0 + alto + 0.2, h0 + alto + 0.36, 0.0, 0.14, "pintura_acento", OCRE)
    for k in (-1, 1):                                                            # orejas y volutas colgantes
        f.caja(s + k * (w / 2 + 0.3) - 0.07, s + k * (w / 2 + 0.3) + 0.07, h0 + alto - 0.45, h0 + alto + 0.2, 0.0, 0.16,
               "pintura_acento", OCRE2)
    f.caja(s - w / 2 - 0.3, s + w / 2 + 0.3, h0 + alto + 0.36, h0 + alto + 0.72, 0.0, 0.1, "pintura_acento", OCRE)  # friso
    for j in range(5):
        x = s - 0.6 + j * 0.3
        f.caja(x - 0.09, x + 0.09, h0 + alto + 0.42, h0 + alto + 0.66, 0.1, 0.15, "pintura_acento", OCRE2)
    f.caja(s - w / 2 - 0.5, s + w / 2 + 0.5, h0 + alto + 0.72, h0 + alto + 0.88, 0.0, 0.24, "pintura_acento", OCRE)  # cornisa
    ancho_b = 2.7 if central else 1.9
    cc_.balcon_forjado(f, s, h0, ancho=ancho_b, vuelo=0.55, losa=OCRE, menulas=4 if central else 3)
    for k in ((-1, 0, 1) if central else (-1, 1)):                               # macetas de barro bajo el balcón
        q = f.punto(s + k * (ancho_b / 2 - 0.25), h0 - 0.45, 0.28)
        f.c.cilindro(q.x, q.y, q.z, q.z + 0.28, 0.12, "piedra", BARRO, lados=8, radio_arriba=0.16)
    if central:
        for dx in (-1.55, 1.55):
            _pilastra(f, s + dx, h1, h_cor, ancho=0.4, vuelo=0.14)


def faja(f, L, h1):
    f.caja(0, L, h1 - 0.4, h1 - 0.25, 0.0, 0.12, "pintura_acento", OCRE2)
    f.caja(0, L, h1 - 0.25, h1 - 0.05, 0.0, 0.18, "pintura_acento", OCRE)
    f.caja(0, L, h1 - 0.05, h1 + 0.05, 0.0, 0.24, "pintura_acento", OCRE2)
    k = 0.6
    while k < L - 0.5:                                                           # volutas en relieve bajo la faja
        for dx in (-0.22, 0.22):
            f.caja(k + dx - 0.18, k + dx + 0.18, h1 - 0.62, h1 - 0.45, 0.0, 0.06, "pintura_acento", OCRE)
        f.caja(k - 0.06, k + 0.06, h1 - 0.7, h1 - 0.4, 0.0, 0.08, "pintura_acento", OCRE2)
        k += 1.45


def remate(f, L, h_cor):
    hf = h_cor
    f.caja(0, L, hf, hf + 0.12, 0.0, 0.1, "pintura_acento", OCRE)
    k, j = 0.25, 0
    while k < L - 0.2:                                                           # medallones
        q = f.punto(k, hf + 0.36, 0.06)
        f.c.cilindro(q.x, q.y, q.z - 0.13, q.z + 0.13, 0.12, "pintura_acento", OCRE, lados=10)
        k += 0.48
    f.caja(0, L, hf + 0.6, hf + 0.72, 0.0, 0.14, "pintura_acento", OCRE)
    k = 0.1
    while k < L - 0.1:                                                           # dentículos
        f.caja(k, k + 0.09, hf + 0.72, hf + 0.86, 0.0, 0.18, "pintura_acento", OCRE2)
        k += 0.17
    f.caja(0, L, hf + 0.86, hf + 0.96, 0.0, 0.22, "pintura_acento", OCRE)
    k = 0.15
    while k < L - 0.15:                                                          # modillones
        f.caja(k, k + 0.14, hf + 0.96, hf + 1.2, 0.0, 0.34, "pintura_acento", OCRE)
        k += 0.42
    f.caja(0, L, hf + 1.2, hf + 1.36, 0.0, 0.48, "pintura_acento", OCRE)                       # cornisa
    zp = hf + 1.36
    f.caja(0, L, zp, zp + 0.6, 0.0, 0.08, "moldura", "#ece6da")                               # pretil de tejuelas
    k, fila = 0.0, 0
    for fila in range(3):
        k = 0.0 + (0.12 if fila % 2 else 0.0)
        while k < L - 0.2:
            f.caja(k + 0.02, k + 0.22, zp + 0.04 + fila * 0.19, zp + 0.2 + fila * 0.19, 0.08, 0.12, "moldura", CAL)
            k += 0.24
    f.caja(0, L, zp + 0.6, zp + 0.7, 0.0, 0.18, "pintura_acento", OCRE)
    n = max(1, round(L / 4.0))
    for k in range(n + 1):
        s = min(max(k * L / n, 0.3), L - 0.3)
        f.caja(s - 0.25, s + 0.25, zp, zp + 0.95, 0.0, 0.22, "pintura_acento", OCRE)
        f.caja(s - 0.3, s + 0.3, zp + 0.95, zp + 1.05, 0.0, 0.27, "pintura_acento", OCRE2)


def fachada(f0, off, desde, alto_piso, n, alto_total=None, esquina_en=None):
    """off: altura (sobre el suelo de la fachada) de la cara superior del zócalo; esquina_en: 0 o L si la fachada
    tiene la esquina del cruce en ese extremo (farol de brazo junto a ella)."""
    f = cc_._Frente(f0)
    L = f.largo
    h_top = alto_total if alto_total is not None else off + 2 * alto_piso
    hz = off + 0.15                                                              # piso de la planta baja
    f.caja(0, L, desde, off + 0.1, -0.02, 0.06, "zocalo_piedra", "#8a6450")      # zócalo de sillares
    sillares(f, 0, L, desde + 0.3, off + 0.05, 0.06, alto=0.42, largo=(0.55, 1.0), colores=ZOCALO, rojo=0.15,
             semilla=int(L * 10))
    f.caja(0, L, off + 0.05, off + 0.15, 0.0, 0.12, "piedra", "#a0806a")
    h1 = hz + 3.45                                                               # faja entre plantas (R0189)
    h_cor = min(h1 + 3.6, h_top - 0.4)                                           # friso del remate
    faja(f, L, h1)
    pk = n // 2
    for k in range(n):
        s = (k + 0.5) * L / n
        planta_baja(f, s, hz, h1, k == pk, off)
        planta_alta(f, s, h1 + 0.05, h_cor, k == pk)
    remate(f, L, h_cor)
    if esquina_en is not None:
        cc_.farol_brazo(f, abs(esquina_en - 1.0), h1 + 1.6)
