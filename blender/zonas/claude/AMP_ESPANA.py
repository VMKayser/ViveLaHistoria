"""AMP_ESPANA — Calle España, vereda SE de la segunda cuadra, de la casa gris a la esquina con San Alberto
(correcciones R0211–R0215 del usuario, 2026-11-24). Fuera de la zona original: espacio AMP_ESPANA del reparto, dueño
claude, con su mobiliario propio. Inventario por foto: ESPANA_INVENTARIO.md.

Marco: T = distancia a lo largo del eje de la Calle España desde la Plaza (la misma `t` de espana_se.py); d hacia la
IZQUIERDA del eje (la línea de fachada SE está en d = -5,75; d más negativo = hacia el interior de la cuadra). En las
fotos (tomadas desde la vereda NO mirando al SE) lo de la izquierda tiene T mayor.

1. Casa de piedra (T 67–77, R0212, R0213 derecha): planta baja de sillería arenisca con dos ventanas y una puerta de
   arco de medio punto (archivolta moldurada, rejas de abanico, portón de tableros), fajas almohadilladas en los
   extremos, letrero colgante; planta alta blanca con tres puertas-ventana de madera, dinteles ocres con ménsulas y
   balcones de hierro sobre losas de arenisca; cornisa y pretil lisos.
2. Mercantil Santa Cruz (T 77–90,5, R0213): neogótico crema; planta baja de sillería rosada con pilastras de capitel,
   tres ventanas de arco con reja y la puerta de arco con puertas de vidrio; letrero negro con letras doradas;
   arriba cinco ventanas ojivales con tracería (una + tres + una), balcón corrido en las tres del centro y balcones
   sueltos; entablamento con friso de ménsulas y dentículos; crestería con frontón ondulado y rosetón, pináculos.
3. Fiscalía General del Estado (T 90,5–121,25 y la ochava a San Alberto, R0214, R0215): art déco de tres plantas;
   basamento de granito gris con respiraderos, planta baja almohadillada con ventanales enrejados, imposta; arriba
   paños grises con una ventana por piso, cuatro vanos enmarcados en gris con tablero entre pisos, pilares blancos;
   cuerpo de la esquina más alto: ochava con portada de marcos escalonados, puerta de vidrio, letrero FISCALÍA,
   ventanas, losa con cuatro astas y remate escalonado con el escudo; gradas curvas; vitrina, placa «Calle España».
4. Mobiliario de las fotos: faroles negros de cuello de cisne junto al bordillo, faroles verdes de brazo en las
   fachadas, maceteros blancos con ciprés y palmera frente a la Fiscalía, caseta verde de guardia en San Alberto,
   haz de cables por las fachadas anclado en ménsulas.
"""

import copy
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from kit.arquitectura import _enjuta  # noqa: E402
import colon_cuadra as cc_  # noqa: E402
from base_mobiliario import tubo  # noqa: E402
from base_suelo import ALTO_VEREDA, SOBRE_TERRENO  # noqa: E402
from ortiz_se import cuarterones  # noqa: E402
from piezas_claude import al_bordillo  # noqa: E402
from san_felipe_costado import sillares  # noqa: E402
from SAN_MIGUEL import farol_brazo as farol_verde, farol_cuello, mover, pinaculo, disco  # noqa: E402

AGENTE, MID = "claude", "AMP_ESPANA"

# ------------------------------------------------------------------------------------------------ marco
O = (-45.227, -145.778)          # eje de España en T = 70
U = (0.6344838, 0.7729362)       # a lo largo de España, hacia San Alberto
N = (-U[1], U[0])                # hacia la calle (NO) desde la vereda SE
DF = -6.75                       # línea de fachada SE (−5,75 hasta el ensanche de la calle del 2026-11-24)
PROF = 0.35                      # espesor del paño de fachada (los vanos tienen derrame de verdad)


def P(T, d):
    return (O[0] + (T - 70.0) * U[0] + d * N[0], O[1] + (T - 70.0) * U[1] + d * N[1])


def zv(T, d=DF):
    """Altura de la vereda (o del suelo) en (T, d)."""
    return altura_suelo(*P(T, d)) + SOBRE_TERRENO + ALTO_VEREDA


def fach(c, T0, d0, T1, d1, normal, suelo):
    return Fachada(c, {"a": P(T0, d0), "b": P(T1, d1), "normal": normal}, suelo)


def quad(T0, T1, d0, d1):
    return [P(T0, d0), P(T1, d0), P(T1, d1), P(T0, d1)]


# ------------------------------------------------------------------------------------------------ colores
BLANCO = "#f3f1ec"
HIERRO = "#1e1e1e"
MADERA = "#4a2a1c"
ARENISCA = ("#bf9f78", "#c9ab84", "#ad8e69", "#d1b48f", "#b39470")
OCRE = "#d9b464"
LOSA_AR = "#c4a57c"
CREMA = "#efe5cc"
CREMA2 = "#e2d0a6"
ROSAS = ("#c9a58c", "#d3b199", "#bb967d", "#cfa891", "#c09b84")
GRANITO = ("#8f8d88", "#97958f", "#86847f", "#9d9a94", "#8a8883")
GRIS_F = "#a9aba7"
VIDRIO = "#30353a"
METAL = "#3b3d3f"
VERDE_CASETA = "#2f6b47"


# ------------------------------------------------------------------------------------------------ piezas
def pano(f, s0, s1, h0, h1, huecos, d0, d1, rol, color):
    """Paño de muro entre s0..s1 y h0..h1 (sobre el suelo de f), de d0 a d1, con huecos rectangulares (a, b, ha, hb).
    Devuelve los rectángulos llenos (para vestirlos con sillares o bandas)."""
    cortes = sorted({s0, s1} | {x for a, b, _, _ in huecos for x in (a, b) if s0 < x < s1})
    llenos = []
    for a, b in zip(cortes, cortes[1:]):
        if b - a < 1e-3:
            continue
        m = (a + b) / 2
        abajo = h0
        for ha, hb in sorted((h[2], h[3]) for h in huecos if h[0] < m < h[1]):
            if ha > abajo:
                llenos.append((a, b, abajo, min(ha, h1)))
            abajo = max(abajo, hb)
        if h1 > abajo:
            llenos.append((a, b, abajo, h1))
    for a, b, ha, hb in llenos:
        if hb > ha + 1e-3:
            f.caja(a, b, ha, hb, d0, d1, rol, color)
    return llenos


def vestir_sillares(f, llenos, h0, h1, d, colores, alto=0.36, largo=(0.5, 0.95), semilla=0):
    for k, (a, b, ha, hb) in enumerate(llenos):
        lo, hi = max(ha, h0), min(hb, h1)
        if hi - lo > 0.1 and b - a > 0.1:
            sillares(f, a, b, lo, hi, d, alto=alto, largo=largo, colores=colores, rojo=0.08, semilla=semilla + k)


def almohadillas(f, llenos, h0, h1, d0, d1, rol, color, alto=0.56, junta=0.06):
    """Bandas horizontales con junta hundida (planta baja almohadillada de la Fiscalía)."""
    for a, b, ha, hb in llenos:
        h = max(ha, h0)
        while h < min(hb, h1) - 0.05:
            f.caja(a, b, h + junta / 2, min(h + alto - junta / 2, hb, h1), d0, d1, rol, color)
            h += alto


def hueco_arco(f, s, w, arr, d0, rol, color):
    """Enjutas sobre un vano de arco de medio punto; devuelve el ancho medio y el tope del hueco rectangular."""
    r = w / 2
    _enjuta(f, s, r, arr, arr + r, d0, 0.0, rol, color)
    return r, arr + r


def _ojiva_y(x, w, R):
    """Altura de la ojiva sobre el arranque a la distancia x del centro (arco apuntado de radio R)."""
    c = w / 2 - R
    return math.sqrt(max(0.0, R * R - (abs(x) - c) ** 2))


def enjuta_ojival(f, s, w, R, arr, h1, d0, d1, rol, color, seg=8):
    for lado in (-1, 1):
        for k in range(seg):
            x0, x1 = w / 2 * k / seg, w / 2 * (k + 1) / seg
            hb = arr + _ojiva_y(x1, w, R)
            sa, sb = sorted((s + lado * x0, s + lado * x1))
            f.caja(sa, sb, hb, h1, d0, d1, rol, color)


def curva_ojival(f, s, w, R, arr, d, seg=10, dentro=0.0):
    """Puntos de la ojiva (de un arranque al otro) en el plano d de la fachada."""
    pts = []
    for k in range(seg + 1):
        x = -w / 2 + w * k / seg
        pts.append(f.punto(s + x, arr + _ojiva_y(x, w, R) - dentro, d))
    return pts


def ventana_metal(f, s, h0, h1, w, cortina=True, luces=2):
    """Ventana de perfiles metálicos oscuros metida en el derrame del paño (Fiscalía)."""
    fi = mover(f, -PROF + 0.02)
    fi.caja(s - w / 2, s + w / 2, h0, h1, 0.0, 0.01, "vidrio", VIDRIO)
    if cortina:
        fi.caja(s - w / 2 + 0.05, s + w / 2 - 0.05, h1 - (h1 - h0) * 0.38, h1 - 0.05, 0.01, 0.02, "vidrio", "#d6cfbf")
    for x in [s - w / 2] + [s - w / 2 + w * k / luces - 0.025 for k in range(1, luces)] + [s + w / 2 - 0.05]:
        fi.caja(x, x + 0.05, h0, h1, 0.02, 0.06, "marco_ventana", METAL)
    for hh in (h0, h0 + (h1 - h0) * 0.7, h1 - 0.05):
        fi.caja(s - w / 2, s + w / 2, hh, hh + 0.05, 0.02, 0.06, "marco_ventana", METAL)


def reja_barras(f, s, h0, h1, w, d, paso=0.13, cruces=2):
    for k in range(int(w / paso) + 1):
        x = s - w / 2 + 0.04 + (w - 0.08) * k / int(w / paso)
        f.caja(x - 0.014, x + 0.014, h0, h1, d - 0.014, d + 0.014, "hierro", HIERRO)
    for j in range(cruces + 2):
        hh = h0 + 0.05 + (h1 - h0 - 0.1) * j / (cruces + 1)
        f.caja(s - w / 2, s + w / 2, hh - 0.02, hh + 0.02, d - 0.02, d + 0.02, "hierro", HIERRO)


def abanico(f, s, r, arr, d, n=9, aro=True):
    """Reja de abanico en la cabeza de un arco: rayos y aro interior."""
    for k in range(n):
        a = math.pi * (k + 0.5) / n
        tubo(f.c, f.punto(s, arr, d), f.punto(s + r * 0.97 * math.cos(a), arr + r * 0.97 * math.sin(a), d), 0.012,
             "hierro", HIERRO)
    if aro:
        cc_._anillo(f, s, arr, d, r * 0.38, n=12)
    f.caja(s - r, s + r, arr - 0.03, arr + 0.03, d - 0.02, d + 0.02, "hierro", HIERRO)


FUENTE = {  # 3×5, de arriba abajo
    "A": ("010", "101", "111", "101", "101"), "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"), "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"), "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"), "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"), "J": ("001", "001", "001", "101", "010"),
    "K": ("101", "110", "100", "110", "101"), "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"), "N": ("110", "101", "101", "101", "101"),
    "O": ("010", "101", "101", "101", "010"), "P": ("110", "101", "110", "100", "100"),
    "Q": ("010", "101", "101", "110", "011"), "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"), "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"), "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"), "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"), "Z": ("111", "001", "010", "100", "111"),
    "Í": ("111", "010", "010", "010", "111"), "Á": ("010", "101", "111", "101", "101"),
    "É": ("111", "100", "110", "100", "111"), "Ó": ("010", "101", "101", "101", "010"),
}


def letras(f, s0, s1, h0, h1, d, texto, rol, color):
    """Texto de letrero con una fuente de píxeles de 3×5 (las minúsculas, más bajas). Cada fila de una letra se
    junta en tiras para no multiplicar las cajas. Si la s de la fachada crece hacia la izquierda de quien la mira desde
    la calle, el texto se escribe al revés para que no salga espejado."""
    u = getattr(f, "u", None) or f.f.u
    espejo = -u.x * f.n.y + u.y * f.n.x < 0
    caja = (lambda a, b, *r: f.caja(s0 + s1 - b, s0 + s1 - a, *r)) if espejo else f.caja
    paso = (s1 - s0) / len(texto)
    for k, ch in enumerate(texto):
        g = FUENTE.get(ch.upper())
        if g is None:
            continue
        alto = (h1 - h0) * (1.0 if not ch.islower() else 0.72)
        px = min(paso * 0.78 / 3, alto / 5 * 0.9)                      # lado del píxel
        ph = alto / 5
        a = s0 + k * paso + (paso - 3 * px) / 2
        for fila, bits in enumerate(g):
            hh = h0 + alto - (fila + 1) * ph
            j = 0
            while j < 3:
                if bits[j] == "1":
                    e = j
                    while e + 1 < 3 and bits[e + 1] == "1":
                        e += 1
                    caja(a + j * px, a + (e + 1) * px, hh, hh + ph, d, d + 0.02, rol, color)
                    j = e + 1
                else:
                    j += 1


def mensula_voluta(f, s, h0, h1, vuelo, color, ancho=0.2):
    f.caja(s - ancho / 2, s + ancho / 2, h0 + 0.15, h1, 0.0, vuelo, "moldura", color)
    q = f.punto(s, h0 + 0.12, vuelo * 0.55)
    f.c.esfera(q.x, q.y, q.z, ancho * 0.55, "moldura", color, segmentos=6)


def soporte_cable(f, s, h, d):
    """Ménsula de hierro que sostiene el haz de cables (acometida en la fachada)."""
    f.caja(s - 0.03, s + 0.03, h - 0.05, h + 0.05, 0.0, d, "hierro", HIERRO)
    f.caja(s - 0.04, s + 0.04, h - 0.12, h + 0.02, d - 0.05, d + 0.03, "hierro", HIERRO)


# ------------------------------------------------------------------------------------------------ 1. casa de piedra
CP = (67.0, 77.0, 14.0)          # T0, T1, fondo


def casa_piedra(c):
    T0, T1, fondo = CP
    L = T1 - T0
    z0 = zv((T0 + T1) / 2)
    desde = min(zv(T0), zv(T1)) - z0 - 0.8
    c.prisma(quad(T0, T1, DF - PROF, DF - fondo), z0 - 0.9, z0 + 8.15, "muro", BLANCO, tapa=False)
    c.tapa(quad(T0, T1, DF - PROF, DF - fondo), z0 + 8.15, "azotea", "#c9c2b6")
    f = fach(c, T0, DF, T1, DF, N, z0)
    # planta baja: puerta (T menor) y dos ventanas de arco
    PUERTA, VENT = 1.95, (4.95, 7.95)
    huecos = []
    r, top = hueco_arco(f, PUERTA, 1.8, 2.7, -PROF, "piedra", ARENISCA[0])
    huecos.append((PUERTA - r, PUERTA + r, desde, top))
    for s in VENT:
        r, top = hueco_arco(f, s, 1.5, 2.6, -PROF, "piedra", ARENISCA[0])
        huecos.append((s - r, s + r, 0.7, top))
    llenos = pano(f, 0.0, L, desde, 4.3, huecos, -PROF, 0.0, "piedra", ARENISCA[0])
    vestir_sillares(f, llenos, desde, 4.28, 0.0, ARENISCA, alto=0.42, largo=(0.55, 1.0), semilla=3)
    for a, b in ((0.0, 0.6), (L - 0.6, L)):                                    # fajas almohadilladas
        h = 0.0
        while h < 4.25:
            f.caja(a, b, h + 0.03, h + 0.25, 0.0, 0.07, "zocalo_piedra", ARENISCA[3])
            h += 0.28
    for k, s in enumerate((PUERTA,) + VENT):                                  # archivoltas, impostas, claves
        w, arr = (1.8, 2.7) if k == 0 else (1.5, 2.6)
        f.arco(s, w / 2, 0.24, arr, 0.0, 0.08, "piedra", ARENISCA[3], segmentos=12)
        f.arco(s, w / 2 + 0.24, 0.06, arr, 0.0, 0.11, "piedra", ARENISCA[1], segmentos=12)
        for x in (s - w / 2 - 0.32, s + w / 2 + 0.02):
            f.caja(x, x + 0.3, arr - 0.2, arr, 0.0, 0.12, "piedra", ARENISCA[1])
        f.caja(s - 0.14, s + 0.14, arr + w / 2 - 0.05, arr + w / 2 + 0.32, 0.0, 0.13, "piedra", ARENISCA[3])
        fi = mover(f, -PROF + 0.02)
        if k == 0:                                                           # portón de tableros y montante
            fi.caja(s - w / 2, s + w / 2, arr - 0.05, arr, 0.0, 0.06, "madera", MADERA)
            fi.timpano_arco(s, w / 2, arr, 0.0, "vidrio", "#26292c")
            abanico(fi, s, w / 2, arr, 0.04)
            cc_.puerta_madera(mover(f, -PROF + 0.14), s, w, arr - 0.05, color="#4a3020")
        else:                                                                # ventana con reja y abanico
            fi.caja(s - w / 2, s + w / 2, 0.7, arr, 0.0, 0.01, "vidrio", "#24272a")
            fi.timpano_arco(s, w / 2, arr, 0.0, "vidrio", "#24272a")
            reja_barras(f, s, 0.72, arr, w - 0.04, -0.12, paso=0.15, cruces=3)
            abanico(f, s, w / 2, arr, -0.12)
            f.caja(s - w / 2 - 0.08, s + w / 2 + 0.08, 0.6, 0.7, 0.0, 0.1, "piedra", ARENISCA[1])
    # letrero colgante de hierro entre la puerta y la primera ventana
    f.caja(3.42, 3.48, 3.9, 3.96, 0.0, 0.65, "hierro", HIERRO)
    f.caja(3.43, 3.47, 3.2, 3.86, 0.1, 0.62, "letrero", "#5b4630")
    # faja de arenisca moldurada
    f.caja(0.0, L, 4.3, 4.42, -PROF, 0.1, "piedra", ARENISCA[1])
    f.caja(0.0, L, 4.42, 4.55, -PROF, 0.16, "piedra", ARENISCA[3])
    # planta alta: tres puertas-ventana con marco blanco, dintel ocre con ménsulas y balcón de hierro
    altos = [(s - 0.55, s + 0.55, 4.6, 7.0) for s in (PUERTA,) + VENT]
    pano(f, 0.0, L, 4.55, 8.15, altos, -PROF, 0.0, "muro", BLANCO)
    for s in (PUERTA,) + VENT:
        cuarterones(mover(f, -PROF + 0.16), s, 4.6, ancho=1.1, alto=2.4, color="#3a2418")
        for x0, x1 in ((s - 0.72, s - 0.55), (s + 0.55, s + 0.72)):
            f.caja(x0, x1, 4.6, 7.17, 0.0, 0.06, "moldura", BLANCO)
        f.caja(s - 0.72, s + 0.72, 7.0, 7.17, 0.0, 0.06, "moldura", BLANCO)
        f.caja(s - 0.62, s + 0.62, 7.17, 7.32, 0.0, 0.09, "moldura", OCRE)          # friso ocre
        f.caja(s - 0.98, s + 0.98, 7.32, 7.44, 0.0, 0.2, "moldura", OCRE)
        f.caja(s - 1.05, s + 1.05, 7.44, 7.55, 0.0, 0.26, "moldura", OCRE)
        for x in (s - 0.86, s + 0.86):
            mensula_voluta(f, x, 6.75, 7.32, 0.2, OCRE, ancho=0.17)
        cc_.balcon_forjado(f, s, 4.6, ancho=1.75, vuelo=0.5, losa=LOSA_AR, menulas=2)
    # cornisa y pretil lisos
    f.caja(0.0, L, 7.85, 7.97, -PROF, 0.1, "moldura", BLANCO)
    f.caja(0.0, L, 7.97, 8.15, -PROF, 0.26, "moldura", BLANCO)
    f.caja(0.0, L, 8.15, 8.85, -PROF, -0.05, "muro", BLANCO)
    f.caja(0.0, L, 8.85, 8.95, -PROF - 0.05, 0.02, "moldura", "#e6e2da")


# ------------------------------------------------------------------------------------------------ 2. Mercantil
MS = (77.0, 90.5, 16.0)
M_PIL_BAJO = [0.22, 4.0, 7.5, 10.75, 13.28]
M_PIL_ALTO = [0.22, 4.0, 10.75, 13.28]
M_ARCOS = [(2.1, 1.6, 0.2, 2.75), (5.75, 2.0, None, 2.8), (9.1, 1.6, 0.2, 2.75), (12.0, 1.6, 0.2, 2.75)]
M_OJIVAS = [2.1, 5.75, 7.4, 9.05, 12.0]
M_FRONTON = (4.4, 9.6, 7.0)      # s0, s1, centro de la crestería ondulada


def mercantil(c):
    T0, T1, fondo = MS
    L = T1 - T0
    z0 = zv((T0 + T1) / 2)
    desde = min(zv(T0), zv(T1)) - z0 - 0.8
    c.prisma(quad(T0, T1, DF - PROF, DF - fondo), z0 - 0.9, z0 + 9.3, "muro", CREMA, tapa=False)
    c.tapa(quad(T0, T1, DF - PROF, DF - fondo), z0 + 9.3, "azotea", "#cbc3b4")
    f = fach(c, T0, DF, T1, DF, N, z0)
    # ---- planta baja: sillería rosada hasta la imposta, crema encima, arcos
    huecos = []
    for s, w, pie, arr in M_ARCOS:
        r, top = hueco_arco(f, s, w, arr, -PROF, "muro", CREMA)
        huecos.append((s - r, s + r, desde if pie is None else pie, top))
    bajos = pano(f, 0.0, L, desde, 2.7, huecos, -PROF, 0.0, "zocalo_piedra", ROSAS[0])
    vestir_sillares(f, bajos, desde, 2.68, 0.0, ROSAS, alto=0.45, largo=(0.6, 1.1), semilla=11)
    pano(f, 0.0, L, 2.7, 4.6, huecos, -PROF, 0.0, "muro", CREMA)
    for a, b, ha, hb in bajos:                                                # imposta crema
        if hb > 2.6:
            f.caja(a, b, 2.62, 2.8, 0.0, 0.1, "moldura", CREMA2)
    for s, w, pie, arr in M_ARCOS:
        r = w / 2
        f.arco(s, r, 0.2, arr, 0.0, 0.09, "moldura", CREMA2, segmentos=12)
        f.arco(s, r + 0.2, 0.07, arr, 0.0, 0.105, "moldura", CREMA, segmentos=12)
        f.caja(s - 0.13, s + 0.13, arr + r - 0.04, arr + r + 0.3, 0.0, 0.14, "moldura", CREMA2)       # clave
        fi = mover(f, -PROF + 0.02)
        if pie is None:                                                    # puerta: vidrio, hojas abiertas, abanico
            fi.caja(s - r, s + r, -0.05, arr, 0.0, 0.01, "vidrio", "#3c4246")
            fi.timpano_arco(s, r, arr, 0.0, "vidrio", "#2a2d30")
            for x in (s - r + 0.05, s - 0.03, s + r - 0.1):
                fi.caja(x, x + 0.06, 0.0, 2.35, 0.01, 0.05, "marco_ventana", "#8c9092")
            fi.caja(s - r, s + r, 2.3, 2.42, 0.01, 0.05, "marco_ventana", "#8c9092")
            fi.caja(s - r, s + r, 2.42, arr, 0.01, 0.03, "madera", "#5a2e1c")
            for x0 in (s - r + 0.01, s + r - 0.09):                          # hojas de madera abiertas
                f.caja(x0, x0 + 0.08, 0.0, arr - 0.05, -PROF + 0.04, -0.02, "madera", "#6a3420")
            abanico(fi, s, r, arr, 0.03, n=11)
            f.caja(s + r + 0.3, s + r + 0.5, 3.3, 3.45, 0.0, 0.03, "letrero", "#3a3a3a")              # número
        else:                                                                # ventana de reja con volutas
            fi.caja(s - r, s + r, pie, arr, 0.0, 0.01, "vidrio", "#2a2d31")
            fi.timpano_arco(s, r, arr, 0.0, "vidrio", "#2a2d31")
            reja_barras(f, s, pie + 0.02, arr, w - 0.04, -0.12, paso=0.14, cruces=3)
            for k in range(3):
                cc_._anillo(f, s - 0.45 + 0.45 * k, pie + 0.55, -0.11, 0.15)
            abanico(f, s, r, arr, -0.12, n=11)
    for k, s in enumerate(M_PIL_BAJO):                                       # pilastras de capitel
        a = min(max(s - 0.23, 0.0), L - 0.46)
        f.caja(a, a + 0.46, desde, 3.95, 0.0, 0.12, "piedra", "#d4b6a0")
        sillares(f, a, a + 0.46, 0.1, 3.9, 0.12, alto=0.45, largo=(0.46, 0.46), colores=ROSAS[1:4], rojo=0.0, semilla=k)
        f.caja(a - 0.07, a + 0.53, 3.95, 4.08, 0.0, 0.18, "moldura", CREMA2)
        f.caja(a - 0.04, a + 0.5, 4.08, 4.22, 0.0, 0.15, "moldura", CREMA)
        for x in (a + 0.02, a + 0.44):
            q = f.punto(x, 4.12, 0.17)
            f.c.esfera(q.x, q.y, q.z, 0.06, "moldura", CREMA2, segmentos=6)
    f.caja(0.0, L, 4.22, 4.62, -PROF, 0.12, "moldura", CREMA)                   # faja sobre los arcos
    # letrero negro con letras doradas
    S0, S1 = 4.5, 10.25
    f.caja(S0, S1, 4.06, 4.5, 0.125, 0.165, "letrero", "#1d1c1a")
    letras(f, S0 + 0.25, S1 - 0.25, 4.15, 4.42, 0.165, "Mercantil Santa Cruz", "letrero", "#cfa94e")
    # ---- planta alta: cinco ventanas ojivales con tracería
    W, R, PIE, ARR = 1.2, 0.95, 4.9, 6.85
    huecos = []
    for s in M_OJIVAS:
        enjuta_ojival(f, s, W, R, ARR, ARR + _ojiva_y(0, W, R) + 0.01, -PROF, 0.0, "muro", CREMA)
        huecos.append((s - W / 2, s + W / 2, PIE, ARR + _ojiva_y(0, W, R) + 0.01))
    pano(f, 0.0, L, 4.62, 8.0, huecos, -PROF, 0.0, "muro", CREMA)
    for s in M_OJIVAS:
        fi = mover(f, -PROF + 0.02)
        cuarterones(mover(f, -PROF + 0.15), s, PIE, ancho=W, alto=ARR - PIE, color="#4a2818")
        cabeza = curva_ojival(fi, s, W, R, ARR, 0.0)
        f.c.poligono(cabeza, "vidrio", "#2b2f33")
        for p, q in zip(curva_ojival(fi, s, W, R, ARR, 0.04, dentro=0.05), curva_ojival(fi, s, W, R, ARR, 0.04, dentro=0.05)[1:]):
            tubo(f.c, p, q, 0.03, "marco_ventana", "#4a2818")
        fi.caja(s - 0.025, s + 0.025, ARR, ARR + _ojiva_y(0, W, R) - 0.05, 0.03, 0.06, "marco_ventana", "#4a2818")
        cc_._anillo(fi, s, ARR + 0.42, 0.06, 0.2, n=12, grosor=0.03)
        for x in (s - 0.3, s + 0.3):
            cc_._anillo(fi, x, ARR + 0.17, 0.06, 0.1, n=10, grosor=0.025)
        for p, q in zip(curva_ojival(f, s, W + 0.3, R + 0.15, ARR, 0.07), curva_ojival(f, s, W + 0.3, R + 0.15, ARR, 0.07)[1:]):
            tubo(f.c, p, q, 0.08, "moldura", CREMA2)                          # archivolta apuntada
        for x in (s - W / 2 - 0.1, s + W / 2 + 0.1):                          # columnillas con capitel
            q = f.punto(x, PIE, 0.06)
            f.c.cilindro(q.x, q.y, q.z, q.z + ARR - PIE - 0.2, 0.06, "moldura", CREMA2, lados=8)
            f.caja(x - 0.12, x + 0.12, ARR - 0.2, ARR + 0.02, 0.0, 0.14, "moldura", CREMA2)
        f.caja(s - W / 2 - 0.2, s + W / 2 + 0.2, PIE - 0.08, PIE, 0.0, 0.1, "moldura", CREMA2)
    for s in (M_OJIVAS[0], M_OJIVAS[-1]):                                     # balcones sueltos
        cc_.balcon_forjado(f, s, PIE, ancho=1.8, vuelo=0.5, losa=CREMA2, menulas=3)
    cc_.balcon_forjado(f, 7.4, PIE, ancho=5.2, vuelo=0.5, losa=CREMA2, menulas=0)   # balcón corrido
    f.caja(4.85, 9.95, 4.5, 4.72, 0.0, 0.46, "moldura", CREMA2)
    f.caja(4.95, 9.85, 4.5, 4.56, 0.46, 0.5, "moldura", CREMA)
    for k, s in enumerate(M_PIL_ALTO):                                        # pilastras altas
        a = min(max(s - 0.2, 0.0), L - 0.4)
        f.caja(a, a + 0.4, 4.62, 7.75, 0.0, 0.1, "moldura", CREMA2)
        f.caja(a - 0.06, a + 0.46, 7.75, 8.0, 0.0, 0.16, "moldura", CREMA2)
    # ---- entablamento: arquitrabe, friso de ménsulas, dentículos y cornisa
    f.caja(0.0, L, 8.0, 8.2, -PROF, 0.12, "moldura", CREMA2)
    f.caja(0.0, L, 8.2, 8.7, -PROF, 0.04, "muro", CREMA)
    s = 0.15
    while s < L - 0.15:
        f.caja(s - 0.05, s + 0.05, 8.3, 8.66, 0.0, 0.14, "moldura", CREMA2)
        q = f.punto(s, 8.28, 0.08)
        f.c.esfera(q.x, q.y, q.z, 0.05, "moldura", CREMA2, segmentos=5)
        s += 0.34
    s = 0.05
    while s < L - 0.08:
        f.caja(s, s + 0.08, 8.7, 8.85, 0.0, 0.22, "moldura", CREMA)
        s += 0.16
    f.caja(0.0, L, 8.85, 9.08, -PROF, 0.42, "moldura", CREMA2)
    f.caja(0.0, L, 9.08, 9.3, -PROF, 0.3, "moldura", CREMA)
    # ---- crestería: pretil, frontón ondulado con rosetón y pináculos
    f.caja(0.0, L, 9.3, 9.85, -PROF, -0.08, "muro", CREMA)
    f.caja(0.0, L, 9.85, 9.95, -PROF - 0.05, 0.0, "moldura", CREMA2)
    a0, a1, sc = M_FRONTON
    perfil = []
    for k in range(25):
        x = a0 + (a1 - a0) * k / 24
        u = (x - sc) / ((a1 - a0) / 2)
        h = 9.95 + 1.0 * math.cos(min(1.0, abs(u)) * math.pi / 2) ** 1.4 + 0.18 * math.sin(abs(u) * 3 * math.pi) * (1 - abs(u))
        perfil.append((x, h))
    puntos = [f.punto(a0, 9.9, -0.08)] + [f.punto(x, h, -0.08) for x, h in perfil] + [f.punto(a1, 9.9, -0.08)]
    f.c.poligono(puntos, "muro", CREMA, grosor=0.22, normal_extrusion=tuple(-f.n))
    for (x0, h0), (x1, h1) in zip(perfil, perfil[1:]):
        tubo(f.c, f.punto(x0, h0, -0.05), f.punto(x1, h1, -0.05), 0.07, "moldura", CREMA2)
    disco(f, sc, 10.35, -0.05, 0.36, "moldura", CREMA2, lados=16)
    for k in range(10):                                                       # pétalos del rosetón
        a = 2 * math.pi * k / 10
        q = f.punto(sc + 0.22 * math.cos(a), 10.35 + 0.22 * math.sin(a), 0.0)
        f.c.esfera(q.x, q.y, q.z, 0.07, "moldura", CREMA, segmentos=5)
    q = f.punto(sc, 10.35, 0.0)
    f.c.esfera(q.x, q.y, q.z, 0.09, "moldura", CREMA, segmentos=6)
    for s in (0.6, 1.9, 3.15, 4.15, 9.75, 10.7, 11.65, 12.75):
        q = f.punto(s, 9.95, -0.15)
        pinaculo(c, q.x, q.y, q.z, base=0.3, alto=0.6, color=CREMA2)
        c.esfera(q.x, q.y, q.z + 0.62, 0.1, "moldura", CREMA2, segmentos=6)
    for s in (2.6, 5.3, 8.9, 11.2):                                           # reflectores
        f.caja(s - 0.03, s + 0.03, 9.95, 10.25, -0.12, -0.06, "hierro", HIERRO)
        f.caja(s - 0.1, s + 0.1, 10.2, 10.35, -0.1, 0.05, "hierro", HIERRO)
    farol_verde(f, 10.15, 6.4)
    # retornos del pretil a los costados (para que la crestería no quede como un cartón)
    for T in (T0, T1):
        fs = fach(c, T, DF - PROF, T, DF - 2.0, (U[0], U[1]) if T == T1 else (-U[0], -U[1]), z0)
        fs.caja(0.0, fs.largo, 9.3, 9.85, -0.22, 0.0, "muro", CREMA)


# ------------------------------------------------------------------------------------------------ 3. Fiscalía
FT0, FK = 90.5, 120.25           # inicio sobre España y esquina con San Alberto (1 m atrás por el ensanche)
OCHAVA = 4.2
SA_SESGO = 0.011                 # la línea de fachada a San Alberto se corre en T al alejarse de España
D_FONDO = -52.0
Z_F = None                       # nivel de referencia de los pisos (vereda en T 106)


def T_sa(d):
    return FK + SA_SESGO * (d - DF)


def huella_fiscalia(prof=0.0):
    """Planta (en T, d) con las caras a la calle metidas `prof` (el cuerpo va detrás del paño de fachada)."""
    q = prof * math.sqrt(2) - prof          # corrimiento de los vértices de la ochava
    return [P(FT0, DF - prof), P(FK - OCHAVA - q, DF - prof), P(T_sa(DF - OCHAVA) - prof, DF - OCHAVA - q),
            P(T_sa(D_FONDO) - prof, D_FONDO), P(97.4, D_FONDO), P(97.3, -46.6), P(FT0, -46.6)]


# módulos de las caras: (tipo, s0, s1)
def modulos_espana():
    m = [("fin", 0.0, 2.65), ("gris", 2.65, 5.85), ("pilar", 5.85, 7.05)]
    s = 7.05
    for k in range(4):
        m.append(("marco", s, s + 2.6))
        s += 2.6
        if k < 3:
            m.append(("pilar", s, s + 0.9))
            s += 0.9
    m += [("pilar", 20.15, 21.35), ("gris_balcon", 21.35, 24.55), ("esquina", 24.55, 26.55)]
    return m


def modulos_san_alberto(L):
    m = [("esquina", 0.0, 2.0), ("gris_balcon", 2.0, 5.2), ("pilar", 5.2, 6.4)]
    s = 6.4
    for grupo in range(2):
        for k in range(4):
            m.append(("marco", s, s + 2.6))
            s += 2.6
            m.append(("pilar", s, s + (0.9 if k < 3 else 1.2)))
            s += 0.9 if k < 3 else 1.2
        if grupo == 0:
            m.append(("gris", s, s + 3.2))
            s += 3.2
            m.append(("pilar", s, s + 1.2))
            s += 1.2
    m.append(("fin", s, L))
    return m


def cara_fiscalia(f, mods, suelo_rel, vitrina=None, placa=None, sin_ventana_baja=()):
    """Una cara de la Fiscalía a la calle. suelo_rel(s): suelo del terreno respecto de f.suelo."""
    L = f.largo
    desde = min(suelo_rel(s) for s in (0.0, L / 2, L)) - 0.8
    con_vano = [(t, a, b) for t, a, b in mods if t in ("gris", "gris_balcon", "marco")]
    # ---- basamento de granito con respiraderos
    resp = []
    for t, a, b in con_vano:
        sm = (a + b) / 2
        if suelo_rel(sm) < 0.7 and sm not in sin_ventana_baja:
            resp.append((sm - 0.65, sm + 0.65, 0.85, 1.25))
    llenos = pano(f, 0.0, L, desde, 2.45, resp, -PROF, 0.05, "zocalo_piedra", GRANITO[0])
    vestir_sillares(f, llenos, desde, 2.43, 0.05, GRANITO, alto=0.6, largo=(0.8, 1.4), semilla=21)
    for a, b, ha, hb in resp:
        fi = mover(f, -PROF + 0.02)
        fi.caja(a, b, ha, hb, 0.0, 0.01, "vidrio", "#1b1c1d")
        reja_barras(f, (a + b) / 2, ha, hb, b - a, -0.1, paso=0.1, cruces=0)
    f.caja(0.0, L, 2.45, 2.6, -PROF, 0.1, "piedra", GRANITO[3])
    # ---- planta baja almohadillada con ventanales enrejados
    vb = []
    for t, a, b in con_vano:
        sm = (a + b) / 2
        if sm not in sin_ventana_baja:
            w = 1.7 if t == "marco" else 1.6
            vb.append((sm - w / 2, sm + w / 2, 2.68, 5.45))
    llenos = pano(f, 0.0, L, 2.6, 5.7, vb, -PROF, -0.06, "muro", "#cfcdc6")
    almohadillas(f, llenos, 2.6, 5.7, -0.06, 0.0, "muro", BLANCO, junta=0.08)
    for a, b, ha, hb in vb:
        sm, w = (a + b) / 2, b - a
        ventana_metal(f, sm, ha, hb, w, cortina=False, luces=2)
        reja_barras(f, sm, ha, hb, w - 0.06, -0.09, paso=0.14, cruces=2)
        f.caja(a - 0.05, b + 0.05, ha - 0.1, ha, -PROF, 0.06, "piedra", "#e2e0da")
    f.caja(0.0, L, 5.7, 5.85, -PROF, 0.12, "moldura", BLANCO)                    # imposta
    f.caja(0.0, L, 5.85, 6.05, -PROF, 0.22, "moldura", BLANCO)
    # ---- plantas altas
    vanos_altos = [(a, b, 6.05, 12.3) for t, a, b in con_vano]
    ranuras = [((a + b) / 2 - 0.2, (a + b) / 2 + 0.2, 6.6, 11.8) for t, a, b in mods if t == "esquina"]
    fines = []
    for t, a, b in mods:
        if t == "fin" and b - a > 1.6:
            sm = (a + b) / 2
            fines += [(sm - 0.45, sm + 0.45, 6.7, 8.6), (sm - 0.45, sm + 0.45, 9.7, 11.45)]
    pano(f, 0.0, L, 6.05, 12.3, vanos_altos + ranuras + fines, -PROF, 0.0, "muro", BLANCO)
    for a, b, ha, hb in ranuras:
        f.caja(a, b, ha, hb, -PROF, -0.12, "muro", GRIS_F)
    for a, b, ha, hb in fines:
        ventana_metal(f, (a + b) / 2, ha, hb, b - a, luces=1)
        f.caja(a - 0.06, b + 0.06, ha - 0.1, ha, -PROF, 0.05, "moldura", BLANCO)
    for t, a, b in con_vano:
        sm = (a + b) / 2
        if t in ("gris", "gris_balcon"):
            vs = [(sm - 0.7, sm + 0.7, 6.7, 8.6), (sm - 0.7, sm + 0.7, 9.7, 11.45)]
            pano(f, a, b, 6.05, 12.3, vs, -PROF, -0.12, "muro", GRIS_F)
            for va, vb_, ha, hb in vs:
                ventana_metal(f, sm, ha, hb, 1.4)
                f.caja(va - 0.1, vb_ + 0.1, ha - 0.12, ha, -PROF, 0.06, "moldura", BLANCO)
            if t == "gris_balcon":                                           # baranda baja de hierro
                f.caja(sm - 0.75, sm + 0.75, 7.48, 7.52, 0.1, 0.16, "hierro", HIERRO)
                f.caja(sm - 0.75, sm + 0.75, 6.62, 6.66, 0.1, 0.16, "hierro", HIERRO)
                for k in range(11):
                    x = sm - 0.72 + 1.44 * k / 10
                    f.caja(x - 0.01, x + 0.01, 6.62, 7.5, 0.11, 0.15, "hierro", HIERRO)
                for x in (sm - 0.75, sm + 0.71):
                    f.caja(x, x + 0.04, 6.62, 7.52, -0.12, 0.16, "hierro", HIERRO)
                cc_._anillo(f, sm - 0.35, 7.07, 0.13, 0.16)
                cc_._anillo(f, sm + 0.35, 7.07, 0.13, 0.16)
        else:                                                                # vano enmarcado en gris
            pano(f, a, b, 6.05, 6.3, [], -PROF, 0.0, "muro", BLANCO)
            pano(f, a, b, 12.0, 12.3, [], -PROF, 0.0, "muro", BLANCO)
            pano(f, a, b, 6.3, 12.0, [(a + 0.28, b - 0.28, 6.58, 11.72)], -PROF, -0.06, "muro", GRIS_F)
            vs = [(sm - 0.75, sm + 0.75, 6.7, 8.6), (sm - 0.75, sm + 0.75, 9.7, 11.45)]
            pano(f, a + 0.28, b - 0.28, 6.58, 11.72, vs, -PROF, -0.16, "muro", BLANCO)
            for va, vb_, ha, hb in vs:
                ventana_metal(f, sm, ha, hb, 1.5)
                f.caja(va - 0.08, vb_ + 0.08, ha - 0.1, ha, -0.16, -0.02, "moldura", BLANCO)
            for h0, h1 in ((8.85, 8.95), (9.42, 9.52)):                       # tablero entre pisos
                f.caja(sm - 0.72, sm + 0.72, h0, h1, -0.16, -0.11, "muro", GRIS_F)
            for x in (sm - 0.72, sm + 0.62):
                f.caja(x, x + 0.1, 8.85, 9.52, -0.16, -0.11, "muro", GRIS_F)
    # ---- cornisa y pretil (el cuerpo de la esquina sube más)
    for t, a, b in mods:
        alto = 0.6 if t == "esquina" else 0.0
        f.caja(a, b, 12.3, 12.55, -PROF, 0.3, "moldura", BLANCO)
        f.caja(a, b, 12.55, 13.3 + alto, -PROF, -0.06, "muro", BLANCO)
        f.caja(a, b, 13.3 + alto, 13.42 + alto, -PROF - 0.05, 0.05, "moldura", "#e7e5df")
        if t == "esquina":
            f.caja(a, b, 13.3, 13.5, -0.06, 0.18, "moldura", BLANCO)
    if vitrina is not None:                                                   # vitrina negra con crestería
        a, b = vitrina
        f.caja(a, b, 3.3, 4.5, 0.0, 0.32, "hierro", "#1c1c1c")
        f.caja(a + 0.08, b - 0.08, 3.38, 4.42, 0.32, 0.33, "vidrio", "#3d4a52")
        for k in range(5):
            cc_._anillo(f, a + (b - a) * (k + 0.5) / 5, 4.62, 0.16, 0.1)
        f.caja(a + 0.2, b - 0.2, 3.12, 3.2, 0.0, 0.2, "hierro", HIERRO)
    if placa is not None:                                                    # placa «Calle España»
        f.caja(placa - 0.25, placa + 0.25, 3.25, 3.55, 0.0, 0.03, "letrero", "#2a2a28")
        f.caja(placa - 0.18, placa + 0.18, 3.36, 3.44, 0.03, 0.035, "letrero", "#d8d4c8")


def ochava(c, fc, z_esc):
    """Ochava de la esquina: portada de marcos escalonados, puerta de vidrio, letrero, ventanas, losa con astas y
    remate escalonado con el escudo. z_esc: altura del rellano de las gradas sobre fc.suelo."""
    L = fc.largo
    sm = L / 2
    desde = z_esc - 2.0
    # basamento de granito a los lados de la portada
    for a, b in ((0.0, 0.55), (L - 0.55, L)):
        fc.caja(a, b, desde, 2.45, -PROF, 0.05, "zocalo_piedra", GRANITO[0])
        fc.caja(a, b, 2.45, 2.6, -PROF, 0.1, "piedra", GRANITO[3])
    # muro blanco de la ochava alrededor de la portada
    pano(fc, 0.0, L, desde, 12.3, [(0.55, L - 0.55, desde, 12.3)], -PROF, 0.0, "muro", BLANCO)
    fc.caja(0.55, L - 0.55, desde, z_esc, -PROF, 0.0, "zocalo_piedra", GRANITO[1])
    # portada: marco gris exterior, marco blanco interior, fondo metido
    pano(fc, 0.55, L - 0.55, z_esc, 9.72, [(1.0, L - 1.0, z_esc, 9.4)], -PROF, 0.22, "muro", GRIS_F)
    pano(fc, 1.0, L - 1.0, z_esc, 9.4, [(1.42, L - 1.42, z_esc, 9.0)], -PROF, 0.12, "muro", BLANCO)
    fi = mover(fc, -PROF + 0.02)
    fi.caja(1.42, L - 1.42, z_esc, 9.0, -0.01, 0.0, "muro", "#d9d7d1")
    fi.caja(sm - 1.2, sm + 1.2, z_esc, 5.0, 0.01, 0.02, "vidrio", "#2c3338")                 # puerta de vidrio
    for x in (sm - 1.2, sm - 0.04, sm + 1.12):
        fi.caja(x, x + 0.08, z_esc, 5.0, 0.02, 0.07, "marco_ventana", "#1f2224")
    for hh in (z_esc, 4.3, 4.92):
        fi.caja(sm - 1.2, sm + 1.2, hh, hh + 0.08, 0.02, 0.07, "marco_ventana", "#1f2224")
    fi.caja(sm - 0.45, sm + 0.45, 2.6, 3.5, 0.02, 0.025, "letrero", "#5d6870")               # escudo grabado
    fi.caja(sm - 1.37, sm + 1.37, 5.15, 6.3, 0.0, 0.16, "muro", GRIS_F)                       # letrero
    letras(fi, sm - 1.2, sm + 1.2, 5.68, 6.12, 0.16, "FISCALIA", "letrero", "#5b5e60")
    letras(fi, sm - 1.1, sm + 1.1, 5.3, 5.48, 0.16, "GENERAL DEL ESTADO", "letrero", "#5b5e60")
    ventana_metal(fc, sm, 6.6, 8.75, 2.4, cortina=False, luces=3)
    q = fi.punto(sm, 7.55, 0.06)
    fc.c.esfera(q.x, q.y, q.z, 0.28, "letrero", "#d9b23a", segmentos=8)                       # emblema
    # losa del balcón con las cuatro astas
    fc.caja(0.3, L - 0.3, 9.72, 9.97, -PROF, 0.55, "moldura", BLANCO)
    for k in range(4):
        x = sm - 1.2 + 0.8 * k
        tubo(fc.c, fc.punto(x, 9.97, 0.35), fc.punto(x, 13.1, 1.35), 0.025, "metal", "#9a9c9e")
        q = fc.punto(x, 13.1, 1.35)
        fc.c.esfera(q.x, q.y, q.z, 0.05, "metal", "#c9a54a", segmentos=5)
    # segunda planta: ventana ancha de cuatro luces
    pano(fc, 0.55, L - 0.55, 9.97, 12.3, [(sm - 1.3, sm + 1.3, 10.15, 12.0)], -PROF, 0.0, "muro", BLANCO)
    ventana_metal(fc, sm, 10.15, 12.0, 2.6, luces=4)
    for x0, x1 in ((0.15, 0.5), (L - 0.5, L - 0.15)):                         # ranuras grises de los pilares
        fc.caja(x0, x1, 6.4, 12.0, 0.0, 0.03, "muro", GRIS_F)
    # cornisa y remate escalonado con el escudo
    fc.caja(0.0, L, 12.3, 12.6, -PROF, 0.32, "moldura", BLANCO)
    for k, (a, h) in enumerate(((0.0, 13.8), (0.7, 14.4), (1.35, 15.0), (1.95, 15.6))):
        fc.caja(a, L - a, 12.6 if k == 0 else 13.7, h, -PROF, 0.02 + 0.03 * k, "muro", BLANCO)
        fc.caja(a - 0.03, L - a + 0.03, h, h + 0.1, -PROF - 0.03, 0.06 + 0.03 * k, "moldura", "#e7e5df")
    fc.caja(sm - 0.5, sm + 0.5, 13.75, 14.95, 0.14, 0.24, "moldura", "#e0dccf")                # escudo
    disco(fc, sm, 14.35, 0.25, 0.38, "moldura", "#d6d1c2", lados=14)
    for x in (sm - 0.62, sm + 0.62):
        q = fc.punto(x, 14.0, 0.2)
        fc.c.esfera(q.x, q.y, q.z, 0.17, "moldura", "#d6d1c2", segmentos=6)
    q = fc.punto(sm, 15.05, 0.15)
    fc.c.esfera(q.x, q.y, q.z, 0.16, "moldura", "#d6d1c2", segmentos=6)
    for x in (sm - 0.5, sm + 0.6):                                            # antenas
        q = fc.punto(x, 15.6, -0.25)
        fc.c.cilindro(q.x, q.y, q.z, q.z + 1.6, 0.02, "metal", "#8c8e90", lados=4)


def gradas(c, fc, z_vereda, n=7, contrahuella=0.17):
    """Gradas curvas de granito frente a la ochava (R0215): semi-elipses que crecen hacia abajo."""
    sm = fc.largo / 2
    for k in range(n):
        rx = 1.35 + (n - 1 - k) * 0.26
        ry = 0.5 + (n - 1 - k) * 0.31
        pts = []
        for j in range(19):
            a = math.pi * j / 18
            pts.append(fc.punto(sm + rx * math.cos(a), 0.0, -0.05 + ry * math.sin(a)))
        z_top = z_vereda + contrahuella * (k + 1)
        base = [(p.x, p.y, z_vereda - 0.15) for p in pts]
        c.poligono(base, "zocalo_piedra", GRANITO[1 + k % 3], grosor=z_top - z_vereda + 0.15, normal_extrusion=(0, 0, 1))


def fiscalia(c):
    global Z_F
    Z_F = zv(106.0)
    z_min = min(altura_suelo(*p) for p in huella_fiscalia())
    c.prisma(huella_fiscalia(PROF), z_min - 0.8, Z_F + 12.55, "muro", BLANCO, tapa=False)
    c.tapa(huella_fiscalia(PROF), Z_F + 12.55, "azotea", "#c6c2b9")
    # cara a España
    fe = fach(c, FT0, DF, FK - OCHAVA, DF, N, Z_F)
    cara_fiscalia(fe, modulos_espana(), lambda s: zv(FT0 + s) - Z_F, vitrina=(24.75, 26.35), placa=20.75)
    farol_verde(fe, 17.35, 7.9)
    # cara a San Alberto
    a = P(T_sa(DF - OCHAVA), DF - OCHAVA)
    b = P(T_sa(D_FONDO), D_FONDO)
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    fs = Fachada(c, {"a": a, "b": b, "normal": (-uy, ux)}, Z_F)
    suelo_sa = lambda s: altura_suelo(a[0] + ux * s, a[1] + uy * s) + SOBRE_TERRENO + ALTO_VEREDA - Z_F
    cara_fiscalia(fs, modulos_san_alberto(L), suelo_sa)
    # ochava
    a0, b0 = P(FK - OCHAVA, DF), a
    nx, ny = (U[0] + N[0]) / math.sqrt(2), (U[1] + N[1]) / math.sqrt(2)
    fc = Fachada(c, {"a": a0, "b": b0, "normal": (nx, ny)}, Z_F)
    mx, my = (a0[0] + b0[0]) / 2 + nx * 1.5, (a0[1] + b0[1]) / 2 + ny * 1.5
    z_v = altura_suelo(mx, my) + SOBRE_TERRENO + ALTO_VEREDA
    ochava(c, fc, z_v + 7 * 0.17 - Z_F)
    gradas(c, fc, z_v)
    return fe, fs, fc


# ------------------------------------------------------------------------------------------------ 4. mobiliario
def cipres(c, x, y, z, alto=2.2, r=0.42, semilla=0):
    c.cilindro(x, y, z, z + 0.25, 0.06, "tronco", "#5a4030", lados=5)
    c.cilindro(x, y, z + 0.2, z + alto * 0.55, r, "follaje", "#3f6a35", lados=9, radio_arriba=r * 0.75)
    c.cilindro(x, y, z + alto * 0.55, z + alto, r * 0.75, "follaje", "#3f6a35", lados=9, radio_arriba=0.04)
    for k in range(12):
        a = 2.4 * k + semilla
        hh = 0.35 + (alto - 0.6) * k / 12
        rr = r * (1.05 - 0.85 * k / 12)
        c.esfera(x + math.cos(a) * rr * 0.55, y + math.sin(a) * rr * 0.55, z + hh, rr * 0.6,
                 "follaje_claro" if k % 3 == 0 else "follaje", None, segmentos=6)


def palmera_maceta(c, x, y, z, semilla=0):
    c.cilindro(x, y, z, z + 0.5, 0.07, "tronco", "#6b5a3a", lados=6)
    for k in range(9):
        a = 2 * math.pi * k / 9 + semilla
        largo = 0.75 + 0.15 * (k % 3)
        p0 = (x, y, z + 0.5)
        p1 = (x + math.cos(a) * largo * 0.6, y + math.sin(a) * largo * 0.6, z + 0.95)
        p2 = (x + math.cos(a) * largo, y + math.sin(a) * largo, z + 0.75)
        tubo(c, p0, p1, 0.06, "follaje", "#4c7a3a")
        tubo(c, p1, p2, 0.05, "follaje_claro", "#5d8a45")


def macetero(c, x, y, z, ux, uy, planta, semilla=0):
    """Macetero blanco cuadrado (0,62 m) con su planta: 'cipres', 'cipres_grande', 'palmera' o 'mata'."""
    c.caja_ejes((x, y, z + 0.29), (ux, uy, 0), (-uy, ux, 0), (0, 0, 1), 0.62, 0.62, 0.58, "piedra", "#f1efea")
    c.caja_ejes((x, y, z + 0.6), (ux, uy, 0), (-uy, ux, 0), (0, 0, 1), 0.68, 0.68, 0.05, "piedra", "#e6e3dc")
    c.cilindro(x, y, z + 0.58, z + 0.64, 0.26, "cesped", "#5a4a36", lados=8)
    if planta == "palmera":
        palmera_maceta(c, x, y, z + 0.6, semilla)
    elif planta == "mata":
        for k in range(5):
            a = 1.3 * k + semilla
            c.esfera(x + 0.12 * math.cos(a), y + 0.12 * math.sin(a), z + 0.85 + 0.08 * (k % 2), 0.2,
                     "follaje" if k % 2 else "follaje_claro", None, segmentos=6)
    else:
        cipres(c, x, y, z + 0.6, alto=2.6 if planta == "cipres_grande" else 1.9,
               r=0.48 if planta == "cipres_grande" else 0.38, semilla=semilla)


def caseta_guardia(c, f, s, d):
    """Caseta verde de guardia junto a las gradas, en San Alberto (R0215)."""
    for (a, b) in ((s - 0.6, s + 0.6),):
        f.caja(a, b, -0.05, 2.25, d, d + 1.1, "metal", VERDE_CASETA)
        f.caja(a + 0.1, b - 0.1, 1.1, 1.95, d + 1.1, d + 1.12, "vidrio", "#5a6a6a")
        for k in range(6):                                                    # techo curvo
            a0 = math.pi * k / 6
            f.caja(a - 0.08, b + 0.08, 2.25 + 0.22 * math.sin(a0), 2.32 + 0.22 * math.sin(a0),
                   d + 0.55 - 0.65 * math.cos(a0) - 0.1, d + 0.55 - 0.65 * math.cos(a0) + 0.12, "metal", "#2a5a3c")


def mobiliario(col, fe, fs, fc):
    # faroles negros de cuello de cisne junto al bordillo (R0212, R0213)
    c = Constructor(MID + "_postes_faroles")
    for T in (66.1, 85.6):
        x, y = al_bordillo("Calle España", *P(T, DF + 2.45 - 0.45))
        farol_cuello(c, x, y, zv(T, DF + 2.0), N[0], N[1])
    c.objeto(col)
    # maceteros frente a la Fiscalía (R0214, R0215) y caseta de guardia
    c = Constructor(MID + "_detalles")
    for s, planta in ((23.2, "cipres"), (17.3, "cipres_grande"), (12.1, "palmera"), (7.6, "mata")):
        q = fe.punto(s, 0.0, 1.85)
        macetero(c, q.x, q.y, zv(FT0 + s, DF + 1.85), U[0], U[1], planta, semilla=int(s))
    for s, planta in ((5.0, "cipres"), (7.8, "cipres_grande")):
        q = fs.punto(s, 0.0, 1.85)
        macetero(c, q.x, q.y, altura_suelo(q.x, q.y) + SOBRE_TERRENO + ALTO_VEREDA, fs.u.x, fs.u.y, planta, semilla=int(s))
    g = copy.copy(fs)
    g.c = c
    caseta_guardia(c, g, 3.0, 0.35)
    c.objeto(col)


def cables(col):
    """Haz de cables por las fachadas, de ménsula en ménsula (R0212–R0214): baja en escalones de casa en casa."""
    c = Constructor(MID + "_cables")
    tramos = [  # (T0, T1, h sobre la vereda, salida d, anclajes cada)
        (67.3, 76.7, 4.22, 0.5),
        (77.3, 90.2, 4.36, 0.58),
        (90.8, 116.6, 5.5, 0.4),
    ]
    puntos = []
    for T0, T1, h, d in tramos:
        n = max(2, round((T1 - T0) / 4.4))
        for k in range(n + 1):
            T = T0 + (T1 - T0) * k / n
            puntos.append((T, h, d))
    def z_de(T):
        base = zv(72.0) if T < 77.0 else (zv(83.75) if T < 90.5 else Z_F)
        return base
    for T, h, d in puntos:
        f = fach(c, T - 0.2, DF, T + 0.2, DF, N, z_de(T))
        soporte_cable(f, 0.2, h, d)
    for (Ta, ha, da), (Tb, hb, db) in zip(puntos, puntos[1:]):
        for j, (dh, dd) in enumerate(((0.0, 0.0), (0.06, 0.05), (-0.05, 0.08), (0.03, -0.04))):
            prev = None
            for k in range(7):
                u = k / 6
                T = Ta + (Tb - Ta) * u
                z = (z_de(Ta) + ha) * (1 - u) + (z_de(Tb) + hb) * u - 0.12 * math.sin(math.pi * u) + dh
                d = da * (1 - u) + db * u + dd
                x, y = P(T, DF + d)
                p = (x, y, z)
                if prev:
                    tubo(c, prev, p, 0.022 if j else 0.035, "hierro", HIERRO)
                prev = p
    c.objeto(col)


# ------------------------------------------------------------------------------------------------ construcción
def construir(col):
    c = Constructor(MID + "_casa_piedra")
    casa_piedra(c)
    c.objeto(col)
    c = Constructor(MID + "_mercantil")
    mercantil(c)
    c.objeto(col)
    c = Constructor(MID + "_fiscalia")
    fe, fs, fc = fiscalia(c)
    c.objeto(col)
    mobiliario(col, fe, fs, fc)
    cables(col)


if __name__ == "__main__":
    m, col = iniciar(AGENTE, MID)
    construir(col)
    exportar(AGENTE, MID)
