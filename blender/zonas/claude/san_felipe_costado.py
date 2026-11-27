"""Costado de San Felipe Neri sobre la Calle Colón y su portada lateral (R0175–R0178), rehecho desde cero el
2026-11-24 con las fotos estudiadas a resolución completa (pedido del usuario: "muy estricto").

Fachada local: s = 0 en el extremo NO (pegado a la casa antigua de R0174) y crece hacia el SE (hacia la fachada y las
torres); h sobre la vereda; d hacia la calle.

Secuencia de las fotos (R0175 → R0179), con anchos de 0,42 tramos por contrafuerte y 1,2 tramos la portada (L = 52,6):
  B0 contrafuerte de esquina (0–3,8) · W1 (–10,1) · B1 · W2 · B2 · W3 · B3 (con farol) · PORTADA (30,4–37,9) · B4 · W4 ·
  B5 (con farol, 46,6) · base de la torre (47,9–52,8; san_felipe_frente.base_torre_colon).
Muro: hasta 4,3 m sillares grandes beige rosados con algunos rojos; imposta fina; encima piedra chica beige con muchas
piedras rojas sueltas (el "moteado" de las fotos); al pie un talud de losas oscuras. Contrafuertes angostos (2,6 m) que
salen 1,1 m, de sillares claros, con una cadena de piedras oscuras al centro desde los 5 m; remate blanco y gárgola de
piedra arriba. Ventanas rectangulares de marco verde oscuro en un derrame bajo un arco de descarga de ladrillo, a ~9,6 m.
Cornisa con balaustrada de balaustres cortos.
Portada (R0177, R0178), toda de arenisca rosada más clara que el muro: escalinata, puerta verde de tableros en arco de
medio punto, archivolta de dovelas alternadas, a cada lado pedestal y dos pilastras con tableros octogonales, entablamento,
y arriba una gran cartela de lados cóncavos con volutas en C, florón al centro y pináculos sobre las pilastras.
"""
import math

import colon_cuadra as P
from piezas_claude import adelantada

TRAMO = 6.26
CONTRA = 2.6
CONTRAFUERTES = [(1.9, 3.8)] + [(c, CONTRA) for c in (11.36, 20.22, 29.08, 39.2, 46.6)]
FIN_COSTADO = 47.9          # desde aquí, base de la torre (san_felipe_frente.base_torre_colon)
PORTADA = (30.38, 37.9)
VENTANAS = [6.93, 15.79, 24.65, 42.9]
H_SILLAR = 4.3

MURO = "#b07d68"           # tono general (juntas y piedra media)
CLARAS = ("#c99b80", "#c2917a", "#cfa68b", "#bb8a73")
ROJAS = ("#a35b4b", "#94503f", "#b06a58", "#8a4a3d")
SILLARES = ("#c7a184", "#bd9478", "#b4876f", "#ccab90", "#9f6152")
OSCURA = "#5f3c33"
TALUD = ("#5e4e47", "#6d5a50", "#54453f")
VERDE = "#24372f"
PORTADA_C = ("#d6a689", "#c99479", "#deb196")


def _h(*a):
    """Valor fijo en [0, 1) a partir de una posición (el moteado de la piedra no cambia entre exportaciones)."""
    x = math.sin(sum(v * k for v, k in zip(a, (12.9898, 78.233, 37.719, 4.581)))) * 43758.5453
    return x - math.floor(x)


def _tramos_libres(s0, s1, huecos):
    out, a = [], s0
    for h0, h1 in sorted(huecos):
        if h1 <= a or h0 >= s1:
            continue
        if h0 > a:
            out.append((a, h0))
        a = max(a, h1)
    if a < s1:
        out.append((a, s1))
    return out


def sillares(f, s0, s1, h0, h1, d, alto=0.46, largo=(0.7, 1.25), colores=SILLARES, rojo=0.14, todos=True, semilla=0):
    """Hiladas de sillares (cajas finas) entre s0..s1 y h0..h1, a la salida d."""
    h, fila = h0, 0
    while h < h1 - 0.05:
        hh = min(h1, h + alto)
        s = s0 - _h(fila, semilla) * largo[0]
        while s < s1:
            L = largo[0] + (largo[1] - largo[0]) * _h(s, fila, semilla)
            a, b = max(s0, s + 0.02), min(s1, s + L - 0.02)
            if b - a > 0.08:
                r = _h(s * 3.1, fila, semilla + 7)
                if r < rojo:
                    col = colores[-1]
                elif todos or r < 0.55:
                    col = colores[int(_h(s, fila * 5, semilla) * (len(colores) - 1))]
                else:
                    col = None
                if col:
                    f.caja(a, b, h + 0.02, hh - 0.02, d, d + 0.025, "zocalo_piedra", col)
            s += L
        h += alto
        fila += 1


def piedra_chica(f, s0, s1, h0, h1, d, semilla=0):
    """Mampostería de piedra chica: sobre el tono general, piedras claras y muchas rojas sueltas (no todas)."""
    alto, h, fila = 0.27, h0, 0
    while h < h1 - 0.05:
        s = s0 - _h(fila, semilla) * 0.4
        while s < s1:
            L = 0.36 + 0.14 * _h(s, fila, semilla)
            a, b = max(s0, s + 0.025), min(s1, s + L - 0.025)
            r = _h(s * 1.7, fila * 1.3, semilla + 3)
            if b - a > 0.08 and r < 0.88:
                col = ROJAS[int(r * 40) % len(ROJAS)] if r < 0.33 else CLARAS[int(r * 50) % len(CLARAS)]
                f.caja(a, b, h + 0.025, min(h1, h + alto) - 0.025, d, d + 0.02, "zocalo_piedra", col)
            s += L
        h += alto
        fila += 1


# ---------------------------------------------------------------------------------------------- partes
def contrafuerte(c, f, sc, w, off, alto, desde, farol=None, esquina=False):
    a = w / 2
    sal = 1.5 if esquina else 1.1
    fa = adelantada(f, sal)
    f.caja(sc - a, sc + a, desde, alto + 0.55 + off, 0.0, sal, "zocalo_piedra", "#c29c82")       # cuerpo
    f.caja(sc - a - 0.08, sc + a + 0.08, desde, H_SILLAR + off, 0.0, sal + 0.12, "zocalo_piedra", "#c9a58b")
    f.caja(sc - a - 0.12, sc + a + 0.12, H_SILLAR - 0.12 + off, H_SILLAR + 0.05 + off, 0.0, sal + 0.2, "piedra", "#c6a084")
    sillares(adelantada(f, sal + 0.12), sc - a - 0.08, sc + a + 0.08, desde, H_SILLAR + off - 0.12, 0.0,
             semilla=int(sc * 10))
    sillares(fa, sc - a, sc + a, H_SILLAR + off + 0.05, alto + off, 0.0, alto=0.42, largo=(0.45, 0.9),
             colores=("#c9a68b", "#bf9a80", "#d0ad93", "#a86f5c"), rojo=0.12, semilla=int(sc * 10) + 1)
    if not esquina:                                                                             # cadena oscura
        h, j = 5.0, 0
        while h < alto - 1.2:
            dx = 0.16 * math.sin(j * 1.9) * (1.0 if h < 9 else 0.6)
            n = 2 if _h(j, sc) < 0.6 else 1
            for k in range(n):
                x0 = sc + dx - 0.3 + k * 0.32
                f.caja(x0, x0 + 0.28, h + off, h + 0.24 + off, sal + 0.025, sal + 0.05, "zocalo_piedra",
                       OSCURA if _h(j, k, sc) < 0.7 else "#7a4a3e")
            h += 0.28
            j += 1
    # remate: pedestal blanco y gárgola
    q = f.punto(sc, alto + 0.55 + off, sal * 0.5)
    c.caja(q.x - 0.45, q.y - 0.45, q.z, q.x + 0.45, q.y + 0.45, q.z + 0.75, "moldura", "#f3efe8")
    c.caja(q.x - 0.55, q.y - 0.55, q.z + 0.75, q.x + 0.55, q.y + 0.55, q.z + 0.9, "moldura", "#f7f4ee")
    f.caja(sc - 0.13, sc + 0.13, alto - 0.35 + off, alto - 0.1 + off, sal, sal + 0.75, "piedra", "#b98c74")
    if farol:
        P.farol_brazo(fa, sc, farol + off)


def ventana_derrame(f, sc, off):
    """Ventana de marco verde metida en un derrame, bajo un arco de descarga de ladrillo (R0176)."""
    h0, h1, a = 9.35 + off, 10.95 + off, 0.55
    f.caja(sc - 1.15, sc + 1.15, h0 - 0.15, h1 + 0.35, 0.0, 0.03, "zocalo_piedra", "#a97a66")      # fondo del derrame
    for s0, s1 in ((sc - 1.15, sc - a - 0.1), (sc + a + 0.1, sc + 1.15)):                        # derrames en sombra
        f.caja(s0, s1, h0 - 0.15, h1 + 0.35, 0.03, 0.05, "zocalo_piedra", "#9c6c5a")
    f.caja(sc - a, sc + a, h0, h1, 0.05, 0.06, "vidrio", "#2a3640")
    for k in (-a, -0.03, a - 0.07):
        f.caja(sc + k, sc + k + 0.07, h0, h1, 0.06, 0.1, "marco_ventana", VERDE)
    for hh in (h0, h0 + 0.8, h1 - 0.07):
        f.caja(sc - a, sc + a, hh, hh + 0.07, 0.06, 0.1, "marco_ventana", VERDE)
    for hh in (h0 + 0.4, h0 + 1.2):
        f.caja(sc - a, sc + a, hh, hh + 0.03, 0.06, 0.09, "marco_ventana", VERDE)
    f.caja(sc - 1.25, sc + 1.25, h0 - 0.3, h0 - 0.15, 0.0, 0.16, "piedra", "#c49c82")             # alféizar
    for k in range(11):                                                                         # arco de ladrillo
        t0 = k / 11
        x0 = sc - 1.3 + 2.6 * t0
        hb = h1 + 0.35 + 0.55 * math.sin(math.pi * (t0 + 0.5 / 11))
        f.caja(x0 + 0.02, x0 + 2.6 / 11 - 0.02, hb - 0.3, hb, 0.0, 0.06, "zocalo_piedra",
               "#9a4e3e" if k % 2 else "#8c4536")


def balaustrada(f, s0, s1, h, d=0.1):
    f.caja(s0, s1, h, h + 0.14, 0.0, 0.32, "moldura", "#cfae96")
    k = s0 + 0.2
    while k < s1 - 0.1:
        f.cilindro_vertical(k, h + 0.14, h + 0.34, d + 0.08, 0.07, "piedra", "#d6b8a0", lados=6)
        f.cilindro_vertical(k, h + 0.34, h + 0.62, d + 0.08, 0.05, "piedra", "#d6b8a0", lados=6)
        k += 0.26
    f.caja(s0, s1, h + 0.62, h + 0.74, 0.0, 0.3, "moldura", "#d9bea6")


def portada(c, f, s0, s1, off):
    """Portada lateral de arenisca rosada (R0177, R0178)."""
    sm, W = (s0 + s1) / 2, s1 - s0
    C1, C2, C3 = PORTADA_C
    fa = adelantada(f, 0.45)
    # escalinata: tres peldaños fuera (vuelo 1,05 m) que siguen dentro del vano
    for j in range(3):
        a = W / 2 + 0.6 - j * 0.35
        f.caja(sm - a, sm + a, -0.6, 0.18 * (j + 1), 0.0, 1.05 - j * 0.35, "piedra", "#7d6a62" if j % 2 else "#8a766c")
    umbral = 0.54
    f.caja(s0 - 0.3, s1 + 0.3, -0.6, 7.0 + off, 0.0, 0.45, "zocalo_piedra", C2)                   # cuerpo de la portada
    for a_, b_ in _tramos_libres(s0 - 0.3, s1 + 0.3, [(sm - 2.1, sm + 2.1)]):
        sillares(fa, a_, b_, umbral, 7.0 + off, 0.0, alto=0.42, largo=(0.5, 0.95),
                 colores=(C1, C2, C3, "#b97f69"), rojo=0.2, semilla=55)
    sillares(fa, sm - 2.1, sm + 2.1, umbral + 5.6, 7.0 + off, 0.0, alto=0.42, largo=(0.5, 0.95),
             colores=(C1, C2, C3, "#b97f69"), rojo=0.2, semilla=56)
    # puerta en arco de medio punto
    r = 1.4
    hs = umbral + 3.6
    fp = adelantada(f, 0.5)
    fp.caja(sm - r, sm + r, umbral, hs, -0.02, 0.0, "madera", VERDE)
    fp.timpano_arco(sm, r, hs, 0.0, "madera", VERDE)
    for k in (-1, 1):                                                                           # tableros de las hojas
        for hh in (0.35, 1.6, 2.7):
            fp.caja(sm + k * 0.7 - 0.5, sm + k * 0.7 + 0.5, umbral + hh, umbral + hh + 0.9, 0.0, 0.04, "madera", "#2e463b")
        fp.arco(sm + k * 0.7, 0.42, 0.06, hs + 0.15, 0.0, 0.04, "madera", "#2e463b", segmentos=6)
    fp.caja(sm - 0.03, sm + 0.03, umbral, hs + r, 0.0, 0.05, "madera", "#1b2a23")
    for j in range(15):                                                                         # archivolta de dovelas
        a0, a1 = math.pi * j / 15, math.pi * (j + 1) / 15
        am = (a0 + a1) / 2
        rr = r + 0.28
        s_ = sm - math.cos(am) * rr
        h_ = hs + math.sin(am) * rr
        col = C3 if j % 2 else "#c58f78"
        fp.caja(s_ - 0.22, s_ + 0.22, h_ - 0.22, h_ + 0.22, 0.0, 0.18, "piedra", col)
    fp.arco(sm, r + 0.56, 0.16, hs, 0.0, 0.28, "piedra", C1, segmentos=14)                        # moldura exterior
    for k in (-1, 1):                                                                           # jambas
        fp.caja(sm + k * (r + 0.28) - 0.28, sm + k * (r + 0.28) + 0.28, umbral, hs, 0.0, 0.16, "piedra", C1)
        fp.caja(sm + k * (r + 0.28) - 0.34, sm + k * (r + 0.28) + 0.34, hs - 0.2, hs, 0.0, 0.26, "piedra", C3)  # impostas
    # a cada lado: pedestal y dos pilastras con tableros octogonales
    for k in (-1, 1):
        for j, sp in enumerate((r + 0.95, r + 1.75)):
            x = sm + k * sp
            fp.caja(x - 0.38, x + 0.38, umbral - 0.1, umbral + 2.1, 0.0, 0.35 + 0.08 * j, "piedra", C2)   # pedestal
            _octogono(fp, x, umbral + 1.05, 0.28, 0.36 + 0.08 * j, C3)
            fp.caja(x - 0.42, x + 0.42, umbral + 2.1, umbral + 2.3, 0.0, 0.45 + 0.08 * j, "piedra", C1)
            fp.caja(x - 0.3, x + 0.3, umbral + 2.3, umbral + 6.15, 0.0, 0.3 + 0.08 * j, "piedra", C1)     # fuste
            for hh in (2.7, 3.9, 5.1):
                _octogono(fp, x, umbral + hh + 0.4, 0.2, 0.31 + 0.08 * j, C3)
            fp.caja(x - 0.4, x + 0.4, umbral + 6.15, umbral + 6.4, 0.0, 0.42 + 0.08 * j, "piedra", C3)  # capitel
    # entablamento
    e0 = umbral + 6.4
    fp.caja(s0 - 0.1, s1 + 0.1, e0, e0 + 0.3, 0.0, 0.5, "piedra", C2)
    fp.caja(s0 - 0.05, s1 + 0.05, e0 + 0.3, e0 + 0.65, 0.0, 0.4, "piedra", C1)
    fp.caja(s0 - 0.25, s1 + 0.25, e0 + 0.65, e0 + 0.85, 0.0, 0.62, "piedra", C3)
    # cartela de lados cóncavos con volutas en C y florón
    h0 = e0 + 0.85
    for j in range(12):
        t = (j + 0.5) / 12
        hh = h0 + 0.2 + 2.3 * t
        medio = 1.25 + 0.55 * (2 * t - 1) ** 2 + 0.35 * t                                      # se abre hacia arriba
        fp.caja(sm - medio, sm + medio, hh - 0.11, hh + 0.11, 0.0, 0.35, "piedra", C1 if j % 3 else C3)
    fp.caja(sm - 1.0, sm + 1.0, h0 + 0.6, h0 + 2.1, 0.35, 0.4, "piedra", "#e2c2aa")                # tarja lisa
    for k in (-1, 1):
        for rr, hc in ((0.42, 0.6), (0.3, 2.35)):
            fp.arco(sm + k * (1.85 if hc < 1 else 2.0), rr, 0.13, h0 + hc, 0.2, 0.42, "piedra", C3, segmentos=8, medio=False)
        fp.caja(sm + k * 1.3 - 0.9, sm + k * 1.3 + 0.9, h0 + 2.55, h0 + 2.75, 0.0, 0.5, "piedra", C2)   # remate curvo
    q = fp.punto(sm, h0 + 2.75, 0.25)
    c.cilindro(q.x, q.y, q.z, q.z + 0.3, 0.28, "piedra", C2, lados=8)
    c.esfera(q.x, q.y, q.z + 0.5, 0.24, "piedra", C1, segmentos=8)
    c.cilindro(q.x, q.y, q.z + 0.7, q.z + 1.1, 0.06, "piedra", C1, lados=6, radio_arriba=0.02)
    for k in (-1, 1):                                                                           # pináculos laterales
        for sp in (r + 0.95, r + 1.75):
            q = fp.punto(sm + k * sp, e0 + 0.85, 0.25)
            c.caja(q.x - 0.3, q.y - 0.3, q.z, q.x + 0.3, q.y + 0.3, q.z + 0.7, "piedra", C2)
            c.cilindro(q.x, q.y, q.z + 0.7, q.z + 1.3, 0.24, "piedra", C1, lados=8, radio_arriba=0.14)
            c.esfera(q.x, q.y, q.z + 1.5, 0.2, "piedra", C3, segmentos=8)
            c.cilindro(q.x, q.y, q.z + 1.65, q.z + 2.4, 0.09, "piedra", C1, lados=6, radio_arriba=0.02)


def _octogono(f, s, h, r, d, color):
    """Tablero octogonal en relieve (tres cajas cruzadas)."""
    f.caja(s - r, s + r, h - r * 0.42, h + r * 0.42, d, d + 0.04, "piedra", color)
    f.caja(s - r * 0.42, s + r * 0.42, h - r, h + r, d, d + 0.04, "piedra", color)
    f.caja(s - r * 0.75, s + r * 0.75, h - r * 0.75, h + r * 0.75, d, d + 0.03, "piedra", color)


# ---------------------------------------------------------------------------------------------- costado
def costado(c, f, off, alto, desde):
    """Todo el costado sobre Colón hasta la base de la torre (FIN_COSTADO)."""
    L = min(f.largo, FIN_COSTADO)
    huecos = [(sc - w / 2, sc + w / 2) for sc, w in CONTRAFUERTES] + [(PORTADA[0] - 0.3, PORTADA[1] + 0.3)]
    f.caja(0.0, L, desde, alto + off, 0.0, 0.01, "zocalo_piedra", MURO)                         # tono general
    for a, b in _tramos_libres(0.0, L, huecos):
        sillares(f, a, b, 0.0, H_SILLAR + off - 0.1, 0.01, semilla=int(a))
        piedra_chica(f, a, b, H_SILLAR + off + 0.08, alto + off - 0.2, 0.01, semilla=int(a) + 11)
        f.caja(a, b, H_SILLAR - 0.1 + off, H_SILLAR + 0.06 + off, 0.0, 0.1, "piedra", "#c09a80")    # imposta
        # talud de losas oscuras al pie
        s, j = a, 0
        while s < b - 0.05:
            w = 0.6 + 0.5 * _h(s, 3)
            e = min(b, s + w)
            col = TALUD[int(_h(s, 9) * 3)]
            for k in range(4):
                f.caja(s + 0.02, e - 0.02, desde if k == 0 else 0.22 * k, 0.22 * (k + 1), 0.0, 0.55 - 0.13 * k,
                       "zocalo_piedra", col)
            s = e
            j += 1
    for sc in VENTANAS:
        ventana_derrame(f, sc, off)
    for i, (sc, w) in enumerate(CONTRAFUERTES):
        farol = 7.4 if i == 0 else (6.0 if i in (3, 5) else None)
        contrafuerte(c, f, sc, w, off, alto, desde, farol=farol, esquina=(i == 0))
    f.caja(0.0, L, alto - 0.2 + off, alto + off, 0.0, 0.3, "moldura", "#c9a58c")                  # cornisa
    for a, b in _tramos_libres(0.0, L, [(sc - w / 2, sc + w / 2) for sc, w in CONTRAFUERTES]):
        balaustrada(f, a, b, alto + off)
    portada(c, f, PORTADA[0], PORTADA[1], off)
