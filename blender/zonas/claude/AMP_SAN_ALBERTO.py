"""AMP_SAN_ALBERTO — Calle San Alberto, vereda NE, de la esquina con España (Banco Prodem) a la arquería de la Plaza
San Francisco (correcciones R0216–R0218 y R0220–R0223 del usuario y fotos 115529–115737 del 2026-11-13; inventario en
SAN_ALBERTO_INVENTARIO.md). Espacio AMP_SAN_ALBERTO del reparto, dueño claude, con su mobiliario propio.

Marco: el eje real de San Alberto (reparto/calles_reales.json) arranca en el cruce con Ravelo/Arce; t = distancia a lo
largo de ese eje. La fachada NE está a 5,75 m a la izquierda del eje. Cada casa es un tramo recto entre dos puntos de esa
línea; s crece de SE (España) a NO (plaza), en el mismo orden en que el usuario caminó y sacó las fotos.

De la esquina hacia la plaza:
  A. Casa del Banco Prodem (esquina, también 12 m sobre España): dos plantas, alero de tejas sobre canes, esquinas de
     sillares grises, pilastras grises arriba, dinteles grises con relieve, balcones de hierro, zócalo de arenisca;
     abajo: puerta de Prodem con su letrero verde, ventana enrejada, zaguán de arco de piedra, puerta de Tigo Money e
     internet, tienda.
  B. Casa de balaustrada: tres ventanas de arco con balconcillo, planta alta con juntas horizontales, puertas de madera
     (una de arco), zócalo de arenisca.
  C. Casa de pilastras almohadilladas grises: Centro Óptico Valentina, ventana de reja plegable, portada central más
     alta con ventana de arco, balcón, ménsulas y cartela, tiendas; ventanas de marco rojo con guardapolvo curvo gris.
  D. Instituto Médico Sucre: planta baja toda de sillería rosada (ventanas enrejadas con marco de piedra, portón tallado,
     quiosco de libros), arriba pilastras pareadas, cinco ventanas blancas con balcón de baranda roja, letrero en el
     friso, balaustrada.
  E. Casa blanca de faroles: dos ventanales de arco enrejados y puerta de vidrio, cuatro faroles de pared, ventanas
     con guardapolvo de arco y balcón.
  F. Casa crema de El Patio: juntas horizontales, pilastras blancas, portada de arco de piedra, tres tiendas con su
     letrero granate y reja plegable, ventanas con balcón, pretil con pedestales y pináculos; placa de la calle.
  G. Arquería blanca de la Plaza San Francisco en la esquina: arcos de medio punto sobre pilares con tableros,
     entablamento, pretil con pedestales y remates verdes, faroles colgados.
"""

import copy
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from kit import datos  # noqa: E402
import colon_cuadra as cc_  # noqa: E402
from base_mobiliario import tubo  # noqa: E402
from base_suelo import ALTO_VEREDA, SOBRE_TERRENO  # noqa: E402
from ortiz_se import cuarterones  # noqa: E402
from piezas_claude import arqueria_lisa, sobre_calle, tramo_calle  # noqa: E402
from san_felipe_costado import sillares  # noqa: E402
from SAN_MIGUEL import alero_canes, mover, pinaculo  # noqa: E402
from AMP_ESPANA import abanico, hueco_arco, letras, pano, reja_barras, soporte_cable, vestir_sillares  # noqa: E402
import AMP_ESPANA as ae  # noqa: E402

AGENTE, MID = "claude", "AMP_SAN_ALBERTO"

TRAMO = tramo_calle("Calle Fray José Antonio de San Alberto", (-60.0, -60.0))
DF = 6.75                         # línea de fachada NE (a la izquierda del eje); 5,75 hasta el ensanche del 2026-11-24
PROF = 0.35                       # espesor del paño (los vanos tienen derrame)
T_ESQ = 130.0                     # esquina con España (intersección con la fachada NO de España, 1 m atrás tras el ensanche)
T_PLAZA = 23.0                    # fin de la casa de El Patio, comienzo de la arquería
T_ARCO1 = 8.25                    # arquería hasta la esquina con Arce, donde apoya el pilar del Arco de San Francisco (7,25 antes del ensanche de Arce)
#                                   (M013 lo pone de T_ARCO1 − 2,2 a T_ARCO1, en la línea de esta arquería)
D_ARCO = DF + 0.45                # eje de esa línea para M013 (centro del espesor de la arquería)

# casas de SE a NO: (letra, largo aproximado según las fotos); se escalan para llenar T_ESQ → T_PLAZA
CASAS = [("A", 26.0), ("B", 11.0), ("C", 20.0), ("D", 21.0), ("E", 10.0), ("F", 20.0)]

BLANCO = "#f2f0eb"
GRIS = "#9a9e9e"
GRIS_OSC = "#868b8b"
ARENISCA = ("#a98a68", "#b59674", "#9c7e5e", "#bf9f7c", "#a2845f")
ROSADA = ("#b99880", "#c4a48b", "#ab8a72", "#caa992", "#b3917a")
PIEDRA_MARCO = "#b29272"
MADERA = "#4a2a1a"
MADERA_ROJA = "#7a2a24"
HIERRO = "#1e1e1e"
CREMA = "#e3d5bf"
CREMA_BAJO = "#ece4d2"
TEJA = "#b3633f"
BALAUSTRE = "#ead8cf"


def F(t, d=DF):
    x, y, _, _ = sobre_calle(TRAMO, t, d)
    return (x, y)


def zv_xy(x, y):
    return altura_suelo(x, y) + SOBRE_TERRENO + ALTO_VEREDA


def tramos_casas():
    total = sum(L for _, L in CASAS)
    k = (T_ESQ - T_PLAZA) / total
    t, out = T_ESQ, {}
    for letra, L in CASAS:
        out[letra] = (t, t - L * k)
        t -= L * k
    return out


def fachada_de(c, t0, t1):
    """Fachada recta de F(t0) (SE) a F(t1) (NO), normal hacia la calle; suelo = vereda en el medio."""
    a, b = F(t0), F(t1)
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return Fachada(c, {"a": a, "b": b, "normal": (-uy, ux)}, zv_xy(*m))


def cuerpo(c, f, fondo, alto, techo=True, color=BLANCO, medianeras=(True, True)):
    """Volumen de la casa detrás del paño: medianeras, muro del fondo y techo, SIN cara delantera, para que zaguanes,
    tiendas y puertas abiertas tengan hondura de verdad (un prisma macizo pegado al paño se veía como pared blanca
    dentro de cada vano). A 3,2 m del paño, la penumbra del interior de la planta baja."""
    L = f.largo
    b = -1.2
    if medianeras[0]:                       # en la esquina no: caería sobre el plano de la otra fachada
        f.caja(0.0, 0.12, b, alto, -PROF, -fondo, "muro", color)
    if medianeras[1]:
        f.caja(L - 0.12, L, b, alto, -PROF, -fondo, "muro", color)
    f.caja(0.0, L, b, alto, -fondo, -fondo + 0.12, "muro", color)
    f.caja(0.12, L - 0.12, b, 4.5, -3.3, -3.2, "muro", "#3b3631")                      # penumbra interior
    f.caja(0.12, L - 0.12, 4.3, 4.5, -PROF, -3.2, "muro", "#4a443d")                   # techo de la planta baja
    f.caja(0.12, L - 0.12, b, -0.06, -PROF, -3.2, "piedra", "#5c564c")                 # piso del interior
    if techo:
        pts = [f.punto(0, 0, -PROF), f.punto(L, 0, -PROF), f.punto(L, 0, -fondo), f.punto(0, 0, -fondo)]
        c.tapa(datos.orientar_ccw([(p.x, p.y) for p in pts]), f.suelo + alto, "azotea", "#c9c3b8")


def desde_de(f):
    return min(zv_xy(*(lambda p: (p.x, p.y))(f.punto(s, 0))) for s in (0.0, f.largo)) - f.suelo - 0.8


def a_vereda(f, s):
    """Fachada con h = 0 en la vereda delante de s; devuelve (fachada, dz)."""
    q = f.punto(s, 0.0)
    dz = zv_xy(q.x, q.y) - f.suelo
    g = copy.copy(f)
    g.suelo = f.suelo + dz
    return g, dz


# ------------------------------------------------------------------------------------------------ piezas de vano
def fondo_vano(f):
    return mover(f, -PROF + 0.02)


def puerta(f, s, w, alto, tipo="madera", color=MADERA):
    """Puerta en el hueco (pie en la vereda delante de s). alto: tope sobre f.suelo. Tipos: madera, tallada, vidrio,
    tienda, zaguan, plegable."""
    g, dz = a_vereda(fondo_vano(f), s)
    h = alto - dz
    a = w / 2
    if tipo in ("madera", "tallada"):
        cc_.puerta_madera(mover(g, 0.1), s, w, h, color=color)
        if tipo == "tallada":
            for x in (s - a * 0.5, s + a * 0.5):
                for hh in (h * 0.25, h * 0.55, h * 0.8):
                    g.caja(x - a * 0.3, x + a * 0.3, hh - 0.18, hh + 0.18, 0.06, 0.1, "madera", "#6a3e22")
        g.caja(s - a, s + a, -0.05, h, -0.01, 0.0, "vidrio", "#15130f")
    elif tipo == "vidrio":
        g.caja(s - a, s + a, -0.05, h, 0.0, 0.01, "vidrio", "#3a4448")
        for x in (s - a, s - 0.03, s + a - 0.07):
            g.caja(x, x + 0.07, 0.0, h, 0.01, 0.06, "marco_ventana", "#3a2a20")
        for hh in (0.0, h - 0.6, h - 0.07):
            g.caja(s - a, s + a, hh, hh + 0.07, 0.01, 0.06, "marco_ventana", "#3a2a20")
    elif tipo == "tienda":
        g.caja(s - a, s + a, -0.05, h, -0.3, -0.29, "vidrio", "#1e1b18")
        for hh in (0.7, 1.3, 1.9):
            g.caja(s - a + 0.1, s + a - 0.1, hh, hh + 0.04, -0.28, -0.18, "madera", "#6b5444")
        g.caja(s - a, s + a, h - 0.15, h, 0.0, 0.04, "madera", "#4a3424")
    elif tipo == "zaguan":
        g.caja(s - a, s + a, -0.05, h, -2.5, -2.49, "muro", "#6f685d")             # fondo del zaguán
        g.caja(s - a - 0.02, s + a + 0.02, -0.06, 0.0, -2.5, 0.0, "piedra", "#8f8676")   # piso
        for x0, x1 in ((s - a - 0.02, s - a), (s + a, s + a + 0.02)):
            g.caja(x0, x1, -0.05, h, -2.5, 0.0, "muro", "#a8a196")
        g.caja(s - a, s + a, h - 0.02, h, -2.5, 0.0, "muro", "#9a9388")
        for x0 in (s - a + 0.02, s + a - 0.1):                                       # hojas abiertas
            g.caja(x0, x0 + 0.08, 0.0, h - 0.1, -0.85, -0.05, "madera", color)
    elif tipo == "plegable":
        g.caja(s - a, s + a, -0.05, h, -0.2, -0.19, "vidrio", "#1c1a18")
        k = s - a + 0.06
        while k < s + a - 0.03:
            g.caja(k - 0.012, k + 0.012, 0.0, h, 0.0, 0.03, "metal", "#4a4d4f")
            k += 0.14
        for hh in (0.15, h * 0.5, h - 0.1):
            g.caja(s - a, s + a, hh - 0.02, hh + 0.02, 0.0, 0.03, "metal", "#4a4d4f")


def ventana_francesa(f, s, h0, w, alto, color=MADERA_ROJA, vidrio=True):
    cuarterones(mover(f, -PROF + 0.15), s, h0, ancho=w, alto=alto, color=color)


def ventana_vidrios(f, s, h0, w, alto, color="#f4f2ec"):
    """Ventana de guillotina de muchos vidrios con carpintería blanca (Instituto Médico)."""
    fi = fondo_vano(f)
    fi.caja(s - w / 2, s + w / 2, h0, h0 + alto, 0.0, 0.01, "vidrio", "#2c3236")
    for x in [s - w / 2 + w * k / 3 for k in range(4)]:
        fi.caja(x - 0.03, x + 0.03, h0, h0 + alto, 0.01, 0.06, "marco_ventana", color)
    for hh in [h0 + alto * k / 4 for k in range(5)]:
        fi.caja(s - w / 2, s + w / 2, hh - 0.03, hh + 0.03, 0.01, 0.06, "marco_ventana", color)


def balcon(f, s, h, ancho=1.7, vuelo=0.5, losa="#d6cfc2", menulas=2, baranda=None):
    cc_.balcon_forjado(f, s, h, ancho=ancho, vuelo=vuelo, losa=losa, menulas=menulas)
    if baranda:                                                               # pasamanos rojo (Instituto, casa E)
        f.caja(s - ancho / 2 + 0.05, s + ancho / 2 - 0.05, h + 1.0, h + 1.06, vuelo - 0.08, vuelo - 0.01, "hierro", baranda)
        for x in (s - ancho / 2 + 0.05, s + ancho / 2 - 0.1):
            f.caja(x, x + 0.05, h, h + 1.06, 0.06, vuelo - 0.01, "hierro", baranda)


def balaustrada(f, s0, s1, h, alto=0.85, paso=0.26, pedestales=(), color=BLANCO, balaustre=BALAUSTRE):
    """Pretil de balaustres entre pedestales (casas B, C y D)."""
    f.caja(s0, s1, h, h + 0.14, -PROF, 0.04, "moldura", color)
    f.caja(s0, s1, h + alto - 0.12, h + alto, -PROF, 0.06, "moldura", color)
    s = s0 + 0.2
    while s < s1 - 0.15:
        if not any(abs(s - p) < 0.4 for p in pedestales):
            q = f.punto(s, h + 0.14, -0.12)
            f.c.cilindro(q.x, q.y, q.z, q.z + alto - 0.26, 0.07, "moldura", balaustre, lados=6, radio_arriba=0.05)
            q2 = f.punto(s, h + 0.14 + (alto - 0.26) * 0.35, -0.12)
            f.c.esfera(q2.x, q2.y, q2.z, 0.085, "moldura", balaustre, segmentos=5)
        s += paso
    for p in list(pedestales) + [s0 + 0.2, s1 - 0.2]:
        p = min(max(p, s0 + 0.2), s1 - 0.2)
        f.caja(p - 0.22, p + 0.22, h, h + alto + 0.12, -PROF, 0.08, "moldura", color)


def esquinal(f, s0, s1, h0, h1, color=GRIS, alto=0.42, salida=0.08):
    """Pilastra de sillares grises alternados (esquinas de Prodem, pilastras de la casa C)."""
    h, k = h0, 0
    ancho = s1 - s0
    while h < h1 - 0.05:
        ext = 0.18 if k % 2 == 0 else 0.0
        a = max(s0 - ext, 0.0) if s0 > 0.01 else s0
        b = min(s1 + ext, f.largo) if s1 < f.largo - 0.01 else s1
        f.caja(a, b, h + 0.025, min(h + alto - 0.025, h1), 0.0, salida, "moldura", color)
        h += alto
        k += 1
    f.caja(s0 + ancho * 0.1, s1 - ancho * 0.1, h0, h1, 0.0, salida * 0.6, "moldura", GRIS_OSC)


def guardapolvo_curvo(f, s, w, h, color=GRIS):
    """Guardapolvo de arco rebajado sobre una ventana (casa C)."""
    pts = []
    for k in range(9):
        x = -w / 2 + w * k / 8
        pts.append((s + x, h + 0.25 * math.cos(x / (w / 2) * math.pi / 2)))
    for (s0, h0), (s1, h1) in zip(pts, pts[1:]):
        tubo(f.c, f.punto(s0, h0, 0.08), f.punto(s1, h1, 0.08), 0.07, "moldura", color)


def guardapolvo_arco(f, s, w, h, color=BLANCO):
    """Medio punto pequeño sobre la ventana (casas E y F)."""
    f.arco(s, w / 2 - 0.05, 0.1, h, 0.0, 0.1, "moldura", color, segmentos=8)
    f.caja(s - w / 2 - 0.1, s + w / 2 + 0.1, h - 0.1, h, 0.0, 0.12, "moldura", color)


def juntas_horizontales(f, s0, s1, h0, h1, paso=0.42, color="#e6e2da"):
    h = h0 + paso
    while h < h1 - 0.05:
        f.caja(s0, s1, h - 0.025, h + 0.025, -0.02, 0.005, "moldura", color)
        h += paso


def marco_piedra(f, s, w, h0, h1, color=PIEDRA_MARCO, ancho=0.24, arco=False):
    a = w / 2
    f.caja(s - a - ancho, s - a, h0, h1, 0.0, 0.08, "piedra", color)
    f.caja(s + a, s + a + ancho, h0, h1, 0.0, 0.08, "piedra", color)
    if arco:
        f.arco(s, a, ancho, h1, 0.0, 0.08, "piedra", color, segmentos=12)
        f.caja(s - 0.14, s + 0.14, h1 + a - 0.04, h1 + a + ancho + 0.08, 0.0, 0.12, "piedra", color)
    else:
        f.caja(s - a - ancho, s + a + ancho, h1, h1 + ancho, 0.0, 0.08, "piedra", color)


def letrero(f, s0, s1, h0, h1, fondo, texto, color_texto, d=0.12):
    f.caja(s0, s1, h0, h1, 0.0, d, "letrero", fondo)
    pad = (h1 - h0) * 0.22
    letras(f, s0 + 0.12, s1 - 0.12, h0 + pad, h1 - pad, d, texto, "letrero", color_texto)


def zocalo(f, vanos, h, desde, colores=ARENISCA, semilla=0):
    """Zócalo de sillares a lo largo de la cara, cortado en los vanos [(s0, s1)] que bajan a la vereda."""
    cortes = [0.0]
    for a, b in sorted(vanos):
        cortes += [max(a, 0.0), min(b, f.largo)]
    cortes.append(f.largo)
    for k in range(0, len(cortes), 2):
        a, b = cortes[k], cortes[k + 1]
        if b - a > 0.05:
            f.caja(a, b, desde, h, -0.02, 0.06, "zocalo_piedra", colores[0])
            sillares(f, a, b, 0.0, h - 0.02, 0.06, alto=0.36, largo=(0.5, 0.9), colores=colores, rojo=0.08,
                     semilla=semilla + k)
            f.caja(a, b, h - 0.02, h + 0.07, 0.0, 0.1, "piedra", colores[2])


# ------------------------------------------------------------------------------------------------ A. Prodem
A_VANOS = [3.6, 8.4, 13.2, 18.0, 22.8]          # proporción sobre 26 m (se escalan al largo real)
A_TECHO = 8.3


def prodem_cara(f, vanos, bajos, desde, esq_ini=True, esq_fin=True):
    """Una cara de la casa de Prodem. vanos: s de cada eje; bajos: tipo de vano en la planta baja."""
    L = f.largo
    huecos, por_bajar = [], []
    for s, tipo in zip(vanos, bajos):
        if tipo == "prodem":
            huecos.append((s - 1.15, s + 1.15, desde, 3.3)); por_bajar.append((s - 1.4, s + 1.4))
        elif tipo == "ventana":
            huecos.append((s - 0.7, s + 0.7, 1.0, 3.0))
        elif tipo == "zaguan":
            r, top = hueco_arco(f, s, 2.2, 2.75, -PROF, "muro", BLANCO)
            huecos.append((s - r, s + r, desde, top)); por_bajar.append((s - r - 0.35, s + r + 0.35))
        elif tipo in ("puerta", "tienda"):
            w = 1.3 if tipo == "puerta" else 1.8
            huecos.append((s - w / 2, s + w / 2, desde, 2.9)); por_bajar.append((s - w / 2 - 0.3, s + w / 2 + 0.3))
    altos = [(s - 0.58, s + 0.58, 5.15, 7.45) for s in vanos]
    pano(f, 0.0, L, desde, 4.55, huecos, -PROF, 0.0, "muro", BLANCO)
    pano(f, 0.0, L, 4.55, A_TECHO, altos, -PROF, 0.0, "muro", BLANCO)
    zocalo(f, por_bajar, 1.25, desde, semilla=31)
    for s, tipo in zip(vanos, bajos):
        if tipo == "prodem":
            puerta(f, s, 2.3, 3.3, "vidrio")
            for x0, x1 in ((s - 1.4, s - 1.15), (s + 1.15, s + 1.4)):              # marco de madera grueso
                g, dz = a_vereda(f, s)
                g.caja(x0, x1, -0.05, 3.3 - dz, 0.0, 0.1, "madera", "#5a3a26")
            f.caja(s - 1.4, s + 1.4, 3.3, 3.55, 0.0, 0.1, "madera", "#5a3a26")
            f.caja(s - 1.55, s + 1.55, 3.7, 4.35, 0.0, 0.1, "letrero", "#1f7a3a")       # letrero verde
            f.caja(s - 1.45, s + 1.45, 3.76, 4.29, 0.1, 0.11, "letrero", "#f2f2ee")
            f.caja(s - 1.4, s + 1.4, 3.8, 4.25, 0.11, 0.12, "letrero", "#2c8a46")
            letras(f, s - 0.6, s + 1.3, 3.88, 4.18, 0.12, "prodem", "letrero", "#f4f4f0")
            q = f.punto(s - 1.0, 4.03, 0.125)
            f.c.esfera(q.x, q.y, q.z, 0.15, "letrero", "#f4f4f0", segmentos=6)
        elif tipo == "ventana":
            fondo_vano(f).caja(s - 0.7, s + 0.7, 1.0, 3.0, 0.0, 0.01, "vidrio", "#25292c")
            reja_barras(f, s, 1.02, 3.0, 1.36, -0.12, paso=0.12, cruces=2)
            marco_piedra(f, s, 1.4, 0.95, 3.0, color="#8a6a4e", ancho=0.2)
        elif tipo == "zaguan":
            puerta(f, s, 2.2, 2.75 + 1.1, "zaguan", color="#5a3622")
            abanico(fondo_vano(f), s, 1.1, 2.75, 0.04, n=11)
            g, dz = a_vereda(f, s)
            for x0 in (s - 1.45, s + 1.1):                                          # jambas de piedra
                g.caja(x0, x0 + 0.35, -0.05, 2.75 - dz, 0.0, 0.1, "piedra", ARENISCA[3])
                sillares(g, x0, x0 + 0.35, 0.0, 2.75 - dz, 0.1, alto=0.45, largo=(0.35, 0.35),
                         colores=ARENISCA, rojo=0.0, semilla=int(s))
            f.arco(s, 1.1, 0.35, 2.75, 0.0, 0.1, "piedra", ARENISCA[3], segmentos=12)
            f.arco(s, 1.45, 0.08, 2.75, 0.0, 0.13, "piedra", ARENISCA[1], segmentos=12)
            f.caja(s - 1.6, s - 1.1, 2.6, 2.8, 0.0, 0.14, "piedra", ARENISCA[1])
            f.caja(s + 1.1, s + 1.6, 2.6, 2.8, 0.0, 0.14, "piedra", ARENISCA[1])
        elif tipo == "puerta":
            puerta(f, s, 1.3, 2.9, "madera", color="#6a4a32")
            marco_piedra(f, s, 1.3, desde, 2.9, color=PIEDRA_MARCO)
            f.caja(s - 1.5, s - 0.85, 2.3, 3.5, 0.0, 0.08, "letrero", "#2a5cb0")         # Tigo Money
            f.caja(s - 1.45, s - 0.9, 2.95, 3.3, 0.08, 0.09, "letrero", "#f0c020")
            f.caja(s + 0.9, s + 1.05, 0.5, 2.6, 0.0, 0.12, "letrero", "#e8e6e0")         # «INTERNET»
        elif tipo == "tienda":
            puerta(f, s, 1.8, 2.9, "tienda")
            marco_piedra(f, s, 1.8, desde, 2.9, color=PIEDRA_MARCO)
    f.caja(0.0, L, 4.4, 4.6, -PROF, 0.12, "moldura", GRIS)                         # faja
    for s in vanos:                                                                # planta alta
        ventana_francesa(f, s, 5.15, 1.16, 2.3, color="#5a2a1e")
        a = 0.58
        f.caja(s - a - 0.18, s - a, 5.15, 7.45, 0.0, 0.07, "moldura", GRIS)
        f.caja(s + a, s + a + 0.18, 5.15, 7.45, 0.0, 0.07, "moldura", GRIS)
        f.caja(s - 0.95, s + 0.95, 7.45, 7.95, 0.0, 0.1, "moldura", GRIS)            # dintel con relieve
        for k in range(5):
            x = s - 0.6 + 0.3 * k
            q = f.punto(x, 7.7, 0.12)
            f.c.esfera(q.x, q.y, q.z, 0.07 if k % 2 else 0.1, "moldura", "#b3b6b5", segmentos=5)
        f.caja(s - 1.05, s + 1.05, 7.95, 8.05, 0.0, 0.16, "moldura", GRIS)
        balcon(f, s, 5.15, ancho=1.75, vuelo=0.55, losa="#c9ad86", menulas=3)
    pil = [(vanos[k] + vanos[k + 1]) / 2 for k in range(len(vanos) - 1)]
    for s in pil:                                                                  # pilastras grises arriba
        f.caja(s - 0.2, s + 0.2, 4.6, 8.0, 0.0, 0.1, "moldura", GRIS)
        f.caja(s - 0.27, s + 0.27, 7.75, 8.0, 0.0, 0.15, "moldura", GRIS)
    if esq_ini:
        esquinal(f, 0.0, 0.95, 1.25, A_TECHO - 0.05)
    if esq_fin:
        esquinal(f, L - 0.95, L, 1.25, A_TECHO - 0.05)
    alero_canes(f, 0.0, L, A_TECHO, 0.75, sofito=BLANCO)


def tejado(c, f, s0, s1, h, vuelo=0.75, faldon=4.5, pend=24.0, limatesa=False):
    """Faldón de tejas que cae a la calle. limatesa: en la esquina (s0) el faldón se corta en diagonal y se junta con
    el de la otra cara (tejado a cuatro aguas en la esquina)."""
    t = math.tan(math.radians(pend))
    e = h - 0.12
    a0, a1 = (s0 - vuelo, s0 + faldon) if limatesa else (s0, s0)
    pts = [f.punto(a0, e, vuelo), f.punto(s1, e, vuelo), f.punto(s1, e + (vuelo + faldon) * t, -faldon),
           f.punto(a1, e + (vuelo + faldon) * t, -faldon)]
    c.poligono([tuple(p) for p in pts], "teja", TEJA, grosor=0.12, normal_extrusion=(0, 0, 1))
    f.caja(a0, s1, e - 0.02, e + 0.18, vuelo - 0.1, vuelo + 0.03, "teja", TEJA)
    s = a0 + 0.12
    while s < s1:                                                                   # canales de teja
        u = 0.0 if s >= a1 else (s - a0) / (a1 - a0)            # en la limatesa el canal arranca en la diagonal
        p = f.punto(s, e + 0.12 + u * (vuelo + faldon) * t, vuelo - u * (vuelo + faldon))
        q = f.punto(s, e + 0.12 + (vuelo + faldon) * t, -faldon)
        if u < 0.98:
            tubo(c, tuple(p), tuple(q), 0.05, "teja", "#a85a38")
        s += 0.3
    if limatesa:
        tubo(c, tuple(f.punto(a0, e + 0.14, vuelo)), tuple(f.punto(a1, e + 0.14 + (vuelo + faldon) * t, -faldon)), 0.1,
             "teja", TEJA)


def prodem(c, t0, t1):
    f = fachada_de(c, t0, t1)
    L = f.largo
    k = L / 26.0
    vanos = [s * k for s in A_VANOS]
    cuerpo(c, f, 12.0, A_TECHO - 0.1, techo=True, medianeras=(False, True))
    prodem_cara(f, vanos, ["prodem", "ventana", "zaguan", "puerta", "tienda"], desde_de(f))
    tejado(c, f, 0.0, L, A_TECHO, limatesa=True)
    # cara a España: 12 m, dos ejes (ventana enrejada y puerta), alero que dobla la esquina
    O = (-45.227, -145.778)
    U = (0.6344838, 0.7729362)
    N = (-U[1], U[0])
    a = F(t0)
    T1 = 131.75 + 12.0
    b = (O[0] + (T1 - 70) * U[0] + DF * N[0], O[1] + (T1 - 70) * U[1] + DF * N[1])
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    fe = Fachada(c, {"a": a, "b": b, "normal": (U[1], -U[0])}, f.suelo)
    if abs(zv_xy(*m) - f.suelo) > 0.01:
        fe.suelo = f.suelo                     # mismos pisos que la cara a San Alberto (el muro baja con desde)
    cuerpo(c, fe, 10.0, A_TECHO - 0.1, medianeras=(False, True))
    prodem_cara(fe, [4.4, 8.9], ["ventana", "puerta"], desde_de(fe), esq_ini=False, esq_fin=False)
    esquinal(fe, 0.0, 0.95, 1.25, A_TECHO - 0.05)
    tejado(c, fe, 0.0, fe.largo, A_TECHO, limatesa=True)
    return f, fe


# ------------------------------------------------------------------------------------------------ B. balaustrada
def casa_b(c, t0, t1):
    f = fachada_de(c, t0, t1)
    L = f.largo
    desde = desde_de(f)
    cuerpo(c, f, 12.0, 8.5)
    vs = [L * 0.2, L * 0.5, L * 0.8]
    huecos = [(vs[0] - 0.6, vs[0] + 0.6, desde, 2.7), (vs[1] - 0.9, vs[1] + 0.9, desde, 3.3),
              (vs[2] - 0.6, vs[2] + 0.6, desde, 2.7)]
    hueco_arco(f, vs[1], 1.8, 2.4, -PROF, "muro", BLANCO)
    pano(f, 0.0, L, desde, 4.35, huecos, -PROF, 0.0, "muro", BLANCO)
    zocalo(f, [(a - 0.12, b + 0.12) for a, b, _, _ in huecos], 1.4, desde, semilla=41)
    puerta(f, vs[0], 1.2, 2.7, "madera", color="#4a2c1e")
    puerta(f, vs[1], 1.8, 3.3, "madera", color="#3e2418")
    puerta(f, vs[2], 1.2, 2.7, "madera", color="#4a2c1e")
    for s, w, top in ((vs[0], 1.2, 2.7), (vs[2], 1.2, 2.7)):
        g, dz = a_vereda(f, s)
        for x0 in (s - w / 2 - 0.16, s + w / 2):
            g.caja(x0, x0 + 0.16, 1.4 - dz, top - dz, 0.0, 0.06, "moldura", "#e9e6e0")
        f.caja(s - w / 2 - 0.16, s + w / 2 + 0.16, top, top + 0.16, 0.0, 0.06, "moldura", "#e9e6e0")
    f.arco(vs[1], 0.9, 0.16, 2.4, 0.0, 0.06, "moldura", "#e9e6e0", segmentos=12)
    f.caja(0.0, L, 4.35, 4.6, -PROF, 0.14, "moldura", BLANCO)
    # planta alta: juntas horizontales y tres ventanas de arco con balconcillo
    altos = []
    for s in vs:
        r, top = hueco_arco(f, s, 1.1, 6.8, -PROF, "muro", BLANCO)
        altos.append((s - r, s + r, 5.0, top))
    pano(f, 0.0, L, 4.6, 8.2, altos, -PROF, 0.0, "muro", BLANCO)
    juntas_horizontales(f, 0.0, L, 4.6, 8.0)
    for s in vs:
        ventana_francesa(f, s, 5.0, 1.1, 1.8, color="#3a2418")
        fondo_vano(f).timpano_arco(s, 0.55, 6.8, 0.0, "vidrio", "#2a2c2e")
        f.arco(s, 0.55, 0.14, 6.8, 0.0, 0.08, "moldura", "#ebe8e2", segmentos=10)
        balcon(f, s, 5.0, ancho=1.5, vuelo=0.4, losa="#e4e0d8", menulas=0)
    f.caja(0.0, L, 8.2, 8.5, -PROF, 0.3, "moldura", BLANCO)
    balaustrada(f, 0.0, L, 8.5, pedestales=[L * 0.35, L * 0.65])
    return f


# ------------------------------------------------------------------------------------------------ C. pilastras grises
def casa_c(c, t0, t1):
    f = fachada_de(c, t0, t1)
    L = f.largo
    k = L / 20.0
    desde = desde_de(f)
    cuerpo(c, f, 12.0, 8.7)
    S = lambda x: x * k
    val, reja, portal, maniq, ipach = S(2.2), S(7.0), S(10.0), S(13.0), S(17.6)
    esq = [(S(4.3), S(4.9)), (S(15.0), S(15.6))]
    huecos = [(val - 1.0, val + 1.0, desde, 3.1), (reja - 1.05, reja + 1.05, 0.7, 2.9),
              (portal - 0.95, portal + 0.95, desde, 3.3), (maniq - 1.0, maniq + 1.0, desde, 3.0),
              (ipach - 1.05, ipach + 1.05, 0.75, 2.95)]
    pano(f, 0.0, L, desde, 4.3, huecos, -PROF, 0.0, "muro", BLANCO)
    zocalo(f, [(val - 1.1, val + 1.1), (portal - 1.25, portal + 1.25), (maniq - 1.1, maniq + 1.1)], 0.75, desde,
           colores=ARENISCA, semilla=51)
    # Centro Óptico Valentina
    puerta(f, val, 2.0, 3.1, "vidrio")
    letrero(f, val - 1.2, val + 1.2, 3.3, 4.05, "#2a2a30", "CENTRO OPTICO", "#e8e8e8")
    f.caja(val - 1.0, val + 1.0, 3.32, 3.6, 0.12, 0.13, "letrero", "#1f3f8a")
    # ventana de reja plegable
    fondo_vano(f).caja(reja - 1.05, reja + 1.05, 0.7, 2.9, 0.0, 0.01, "vidrio", "#202326")
    for kk in range(13):                                                      # rombos de la reja plegable
        x = reja - 1.0 + 2.0 * kk / 12
        tubo(f.c, tuple(f.punto(x, 0.72, -0.1)), tuple(f.punto(min(x + 0.35, reja + 1.0), 2.88, -0.1)), 0.012,
             "hierro", HIERRO)
        tubo(f.c, tuple(f.punto(x, 0.72, -0.1)), tuple(f.punto(max(x - 0.35, reja - 1.0), 2.88, -0.1)), 0.012,
             "hierro", HIERRO)
    f.caja(reja - 1.15, reja + 1.15, 0.6, 0.7, 0.0, 0.1, "moldura", BLANCO)
    # portada central
    puerta(f, portal, 1.9, 3.3, "madera", color="#4e2a1a")
    for x in (portal - 1.2, portal + 1.2):
        f.caja(x - 0.25, x + 0.25, desde, 4.3, 0.0, 0.14, "moldura", BLANCO)
        f.caja(x - 0.2, x + 0.2, 3.5, 4.4, 0.14, 0.4, "moldura", "#e6e3dc")                 # ménsulas
    f.caja(portal - 1.45, portal + 1.45, 4.4, 4.6, 0.0, 0.5, "moldura", BLANCO)
    f.caja(portal - 0.3, portal + 0.3, 3.4, 3.65, 0.0, 0.2, "letrero", "#3a2c20")            # «Residencial»
    # tiendas
    puerta(f, maniq, 2.0, 3.0, "tienda")
    for x in (maniq - 0.8, maniq, maniq + 0.8):                                    # reflectores
        f.caja(x - 0.03, x + 0.03, 3.4, 3.5, 0.0, 0.4, "hierro", HIERRO)
        f.caja(x - 0.12, x + 0.12, 3.3, 3.48, 0.32, 0.5, "hierro", "#d0d0d0")
    fi = fondo_vano(f)
    fi.caja(ipach - 1.05, ipach + 1.05, 0.75, 2.95, 0.0, 0.01, "vidrio", "#3a4044")
    fi.caja(ipach - 1.05, ipach + 1.05, 2.85, 2.95, 0.01, 0.06, "marco_ventana", "#222222")
    letras(fi, ipach - 0.4, ipach + 0.4, 2.55, 2.75, 0.02, "Ipach", "letrero", "#1a1a1a")
    f.caja(ipach - 1.15, ipach + 1.15, 0.65, 0.75, 0.0, 0.1, "moldura", BLANCO)
    # faja con friso de dentículos gris
    f.caja(0.0, L, 4.3, 4.45, -PROF, 0.1, "moldura", BLANCO)
    x = 0.1
    while x < L - 0.1:
        f.caja(x, x + 0.12, 4.45, 4.62, 0.0, 0.08, "moldura", GRIS)
        x += 0.26
    f.caja(0.0, L, 4.62, 4.72, -PROF, 0.13, "moldura", BLANCO)
    # planta alta: ventanas de marco rojo con guardapolvo curvo; pareadas sobre Valentina; arco en la portada
    altos_v = [(val - 0.65, 1.0), (val + 0.65, 1.0), (reja, 1.1), (maniq, 1.1), (ipach, 1.1)]
    altos = [(s - w / 2, s + w / 2, 5.1, 7.35) for s, w in altos_v]
    r, top = hueco_arco(f, portal, 1.3, 6.95, -PROF, "muro", BLANCO)
    altos.append((portal - r, portal + r, 5.1, top))
    pano(f, 0.0, L, 4.72, 8.4, altos, -PROF, 0.0, "muro", BLANCO)
    for s, w in altos_v:
        ventana_francesa(f, s, 5.1, w, 2.25, color=MADERA_ROJA)
    for s in (val, reja, maniq, ipach):
        w = 2.4 if s == val else 1.4
        guardapolvo_curvo(f, s, w, 7.6)
        balcon(f, s, 5.1, ancho=w + 0.4, vuelo=0.5, losa="#dcd6cc", menulas=2)
    ventana_francesa(f, portal, 5.1, 1.3, 1.85, color=MADERA_ROJA)
    fondo_vano(f).timpano_arco(portal, 0.65, 6.95, 0.0, "vidrio", "#2a2c2e")
    for kk in range(5):
        a = math.pi * (kk + 0.5) / 5
        tubo(f.c, tuple(fondo_vano(f).punto(portal, 6.95, 0.05)),
             tuple(fondo_vano(f).punto(portal + 0.62 * math.cos(a), 6.95 + 0.62 * math.sin(a), 0.05)), 0.02,
             "marco_ventana", MADERA_ROJA)
    f.arco(portal, 0.65, 0.16, 6.95, 0.0, 0.1, "moldura", "#e9e6e0", segmentos=12)
    balcon(f, portal, 4.6, ancho=2.6, vuelo=0.95, losa="#e4e0d8", menulas=0)
    for x in (portal - 1.2, portal + 1.2):                                         # pilastras de la portada
        f.caja(x - 0.22, x + 0.22, 4.72, 9.4, 0.0, 0.12, "moldura", BLANCO)
        f.caja(x - 0.12, x + 0.12, 5.0, 9.2, 0.12, 0.16, "moldura", GRIS)
    for a, b in esq:                                                               # pilastras almohadilladas grises
        esquinal(f, a, b, 0.75, 8.4)
    # cornisa, balaustrada y remate de la portada con cartela
    f.caja(0.0, L, 8.4, 8.7, -PROF, 0.32, "moldura", BLANCO)
    balaustrada(f, 0.0, portal - 1.45, 8.7, pedestales=[S(4.6)])
    balaustrada(f, portal + 1.45, L, 8.7, pedestales=[S(15.3)])
    f.caja(portal - 1.45, portal + 1.45, 8.7, 9.9, -PROF, 0.06, "muro", BLANCO)
    perfil = [(portal - 1.45, 9.9), (portal - 0.9, 10.25), (portal - 0.3, 10.6), (portal + 0.3, 10.6),
              (portal + 0.9, 10.25), (portal + 1.45, 9.9)]
    f.c.poligono([tuple(f.punto(portal - 1.45, 9.85, 0.04))] + [tuple(f.punto(s, h, 0.04)) for s, h in perfil] +
                 [tuple(f.punto(portal + 1.45, 9.85, 0.04))], "muro", BLANCO, grosor=PROF + 0.04,
                 normal_extrusion=tuple(-f.n))
    for (s0, h0), (s1, h1) in zip(perfil, perfil[1:]):
        tubo(f.c, tuple(f.punto(s0, h0, 0.06)), tuple(f.punto(s1, h1, 0.06)), 0.06, "moldura", "#e6e3dc")
    f.caja(portal - 0.55, portal + 0.55, 8.85, 9.75, 0.06, 0.14, "moldura", GRIS)            # cartela
    for kk, (dx, hh) in enumerate(((-0.75, 9.1), (0.75, 9.1), (0.0, 9.85))):
        q = f.punto(portal + dx, hh, 0.14)
        f.c.esfera(q.x, q.y, q.z, 0.14, "moldura", GRIS, segmentos=6)
    for x in (portal - 1.2, portal + 1.2):
        q = f.punto(x, 9.95, -0.1)
        pinaculo(c, q.x, q.y, q.z, base=0.32, alto=0.5, color=BLANCO)
    return f


# ------------------------------------------------------------------------------------------------ D. Instituto Médico
def casa_d(c, t0, t1):
    f = fachada_de(c, t0, t1)
    L = f.largo
    desde = desde_de(f)
    cuerpo(c, f, 14.0, 8.9)
    ejes = [L * (0.11 + 0.195 * k) for k in range(5)]                              # kiosco, portón, 3 ventanas
    huecos = [(ejes[0] - 0.75, ejes[0] + 0.75, desde, 3.0), (ejes[1] - 1.0, ejes[1] + 1.0, desde, 3.45)]
    huecos += [(s - 0.7, s + 0.7, 0.9, 3.1) for s in ejes[2:]]
    llenos = pano(f, 0.0, L, desde, 4.5, huecos, -PROF, 0.0, "zocalo_piedra", ROSADA[0])
    vestir_sillares(f, llenos, desde, 4.48, 0.0, ROSADA, alto=0.5, largo=(0.7, 1.2), semilla=61)
    puerta(f, ejes[0], 1.5, 3.0, "tienda")
    g, dz = a_vereda(fondo_vano(f), ejes[0])
    tonos = ("#9a3a2e", "#2e5288", "#b08a34", "#3e6a42", "#6a3070", "#a85a2a", "#c9c2b0", "#4a4a4a")
    for fila in range(6):                                                        # libros y revistas del quiosco
        for col_ in range(5):
            x = ejes[0] - 0.62 + col_ * 0.25
            g.caja(x, x + 0.21, 0.45 + fila * 0.38, 0.75 + fila * 0.38, -0.2, -0.12, "letrero",
                   tonos[(fila * 3 + col_ * 5) % len(tonos)])
    puerta(f, ejes[1], 2.0, 3.45, "zaguan", color="#6a3e22")
    g, dz = a_vereda(f, ejes[1])
    cc_.puerta_madera(mover(g, -PROF + 0.12), ejes[1] - 0.5, 1.0, 3.45 - dz, color="#7a4a2a", hojas=1)
    for s in ejes[2:]:
        fondo_vano(f).caja(s - 0.7, s + 0.7, 0.9, 3.1, 0.0, 0.01, "vidrio", "#202326")
        reja_barras(f, s, 0.92, 3.1, 1.36, -0.12, paso=0.15, cruces=3)
    for s, w, h0, h1 in [(ejes[0], 1.5, desde, 3.0), (ejes[1], 2.0, desde, 3.45)] + [(s, 1.4, 0.8, 3.1) for s in ejes[2:]]:
        marco_piedra(f, s, w, max(h0, -0.3), h1, color=ROSADA[3], ancho=0.28)
        f.caja(s - w / 2 - 0.4, s + w / 2 + 0.4, h1 + 0.28, h1 + 0.4, 0.0, 0.14, "piedra", ROSADA[2])
    f.caja(0.0, L, 4.5, 4.78, -PROF, 0.16, "piedra", ROSADA[3])
    # planta alta blanca: pilastras pareadas, ventanas de vidrios con marco, balcones de pasamanos rojo
    altos = [(s - 0.65, s + 0.65, 5.2, 7.25) for s in ejes]
    pano(f, 0.0, L, 4.78, 8.6, altos, -PROF, 0.0, "muro", BLANCO)
    for s in ejes:
        ventana_vidrios(f, s, 5.2, 1.3, 2.05)
        marco_piedra(f, s, 1.3, 5.2, 7.25, color="#ecebe6", ancho=0.16)
        f.caja(s - 0.95, s + 0.95, 7.41, 7.55, 0.0, 0.16, "moldura", "#ecebe6")
        balcon(f, s, 5.2, ancho=1.8, vuelo=0.5, losa="#e2ddd4", menulas=2, baranda="#8a2a24")
    pil = [0.35] + [(ejes[k] + ejes[k + 1]) / 2 for k in range(4)] + [L - 0.35]
    for s in pil:
        for dx in ((-0.3, 0.3) if 0.5 < s < L - 0.5 else (0.0,)):
            x = min(max(s + dx, 0.2), L - 0.2)
            f.caja(x - 0.17, x + 0.17, 4.78, 8.0, 0.0, 0.1, "moldura", "#ecebe6")
    f.caja(0.0, L, 7.95, 8.6, -PROF, 0.04, "muro", BLANCO)                           # friso con el letrero
    letras(f, L * 0.22, L * 0.78, 8.08, 8.45, 0.04, "INSTITUTO MEDICO SUCRE", "letrero", "#4a4a48")
    f.caja(0.0, L, 8.6, 8.9, -PROF, 0.32, "moldura", BLANCO)
    balaustrada(f, 0.0, L, 8.9, pedestales=pil[1:-1])
    return f


# ------------------------------------------------------------------------------------------------ E. casa de faroles
def casa_e(c, t0, t1):
    f = fachada_de(c, t0, t1)
    L = f.largo
    desde = desde_de(f)
    cuerpo(c, f, 12.0, 8.6)
    v1, pu, v2 = L * 0.22, L * 0.5, L * 0.78
    huecos = [(pu - 0.65, pu + 0.65, desde, 2.9)]
    for s in (v1, v2):
        r, top = hueco_arco(f, s, 1.7, 2.6, -PROF, "muro", CREMA_BAJO)
        huecos.append((s - r, s + r, 0.75, top))
    pano(f, 0.0, L, desde, 4.3, huecos, -PROF, 0.0, "muro", CREMA_BAJO)
    zocalo(f, [(pu - 0.8, pu + 0.8)], 0.75, desde, semilla=71)
    puerta(f, pu, 1.3, 2.9, "vidrio")
    marco_piedra(f, pu, 1.3, 0.75, 2.9, color="#5a3a26", ancho=0.12)
    for s in (v1, v2):
        fi = fondo_vano(f)
        fi.caja(s - 0.85, s + 0.85, 0.75, 2.6, 0.0, 0.01, "vidrio", "#202326")
        fi.timpano_arco(s, 0.85, 2.6, 0.0, "vidrio", "#202326")
        reja_barras(f, s, 0.77, 2.6, 1.66, -0.12, paso=0.14, cruces=3)
        abanico(f, s, 0.85, 2.6, -0.12, n=9)
        f.arco(s, 0.85, 0.12, 2.6, 0.0, 0.06, "moldura", "#f4f1ea", segmentos=12)
    for s in (0.25, L * 0.36, L * 0.64, L - 0.25):                                # faroles de pared
        s = min(max(s, 0.3), L - 0.3)
        f.caja(s - 0.02, s + 0.02, 3.2, 3.25, 0.0, 0.25, "hierro", HIERRO)
        q = f.punto(s, 3.0, 0.25)
        f.c.cilindro(q.x, q.y, q.z - 0.15, q.z + 0.15, 0.09, "hierro", HIERRO, lados=6)
        f.c.cilindro(q.x, q.y, q.z - 0.1, q.z + 0.1, 0.07, "vidrio", "#e8dcb0", lados=6)
    f.caja(pu + 0.8, pu + 1.15, 2.2, 2.6, 0.0, 0.03, "letrero", "#e8e4dc")                  # placa
    f.caja(0.0, L, 4.3, 4.55, -PROF, 0.12, "moldura", BLANCO)
    altos = [(s - 0.55, s + 0.55, 5.1, 7.15) for s in (v1, v2)]
    pano(f, 0.0, L, 4.55, 8.4, altos, -PROF, 0.0, "muro", BLANCO)
    for s in (v1, v2):
        ventana_vidrios(f, s, 5.1, 1.1, 2.05, color="#f0eee8")
        marco_piedra(f, s, 1.1, 5.1, 7.15, color="#ecebe6", ancho=0.14)
        guardapolvo_arco(f, s, 1.3, 7.45)
        balcon(f, s, 5.1, ancho=1.55, vuelo=0.45, losa="#c9ad86", menulas=3, baranda="#8a2a24")
    for s in (0.25, L - 0.25):
        f.caja(s - 0.25, s + 0.25, 4.55, 8.4, 0.0, 0.1, "moldura", "#ecebe6")
    f.caja(0.0, L, 8.4, 8.65, -PROF, 0.3, "moldura", BLANCO)
    f.caja(0.0, L, 8.65, 9.3, -PROF, -0.04, "muro", BLANCO)
    f.caja(0.0, L, 9.3, 9.4, -PROF, 0.02, "moldura", "#e6e2da")
    for s in (0.3, L / 2, L - 0.3):
        f.caja(s - 0.25, s + 0.25, 8.65, 9.55, -PROF, 0.06, "moldura", BLANCO)
        q = f.punto(s, 9.55, -0.12)
        pinaculo(c, q.x, q.y, q.z, base=0.3, alto=0.45, color=BLANCO)
    return f


# ------------------------------------------------------------------------------------------------ F. El Patio
def casa_f(c, t0, t1):
    f = fachada_de(c, t0, t1)
    L = f.largo
    desde = desde_de(f)
    cuerpo(c, f, 14.0, 8.7, color=CREMA)
    paso = (L - 0.5) / 4
    ejes = [0.25 + paso * (k + 0.5) for k in range(4)]                             # portada + 3 tiendas
    pil = [0.25 + paso * k for k in range(5)]
    huecos = []
    r, top = hueco_arco(f, ejes[0], 2.2, 2.7, -PROF, "muro", CREMA)
    huecos.append((ejes[0] - r, ejes[0] + r, desde, top))
    huecos += [(s - 0.85, s + 0.85, desde, 2.95) for s in ejes[1:]]
    pano(f, 0.0, L, desde, 4.4, huecos, -PROF, 0.0, "muro", CREMA)
    juntas_horizontales(f, 0.0, L, 1.2, 4.3, color="#d8c9b2")
    zocalo(f, [(ejes[0] - 1.55, ejes[0] + 1.55)] + [(s - 1.0, s + 1.0) for s in ejes[1:]], 1.2, desde,
           colores=("#8f8270", "#9a8d7a", "#857866", "#a39684", "#8a7d6b"), semilla=81)
    # portada de arco de piedra con las hojas abiertas al patio
    s = ejes[0]
    puerta(f, s, 2.2, 3.8, "zaguan", color="#5a3420")
    g, dz = a_vereda(f, s)
    for x0 in (s - 1.45, s + 1.1):
        g.caja(x0, x0 + 0.35, -0.05, 2.7 - dz, 0.0, 0.12, "piedra", "#a08670")
    f.arco(s, 1.1, 0.35, 2.7, 0.0, 0.12, "piedra", "#a08670", segmentos=12)
    f.arco(s, 1.45, 0.1, 2.7, 0.0, 0.15, "piedra", "#b49a82", segmentos=12)
    f.caja(s - 0.16, s + 0.16, 3.7, 4.2, 0.0, 0.17, "piedra", "#b49a82")
    f.caja(s + 1.7, s + 2.3, 1.6, 2.3, 0.0, 0.04, "letrero", "#3c3a30")                   # placa «El Patio»
    for s in ejes[1:]:
        puerta(f, s, 1.7, 2.95, "plegable")
        marco_piedra(f, s, 1.7, 0.0, 2.95, color="#f1ede4", ancho=0.16)
        f.caja(s - 1.15, s + 1.15, 3.11, 3.25, 0.0, 0.14, "moldura", "#f1ede4")
        letrero(f, s - 0.85, s + 0.85, 2.45, 2.92, "#6a2a1e", "El Patio", "#e0b850", d=0.1)
    f.caja(ejes[-1] - 1.75, ejes[-1] - 1.15, 2.1, 2.45, 0.0, 0.03, "letrero", "#f2f2f0")       # placa de la calle
    f.caja(0.0, L, 4.4, 4.62, -PROF, 0.13, "moldura", "#f4f1ea")
    altos = [(s - 0.55, s + 0.55, 5.15, 7.1) for s in ejes]
    pano(f, 0.0, L, 4.62, 8.5, altos, -PROF, 0.0, "muro", CREMA)
    juntas_horizontales(f, 0.0, L, 4.62, 8.4, color="#d8c9b2")
    for s in ejes:
        ventana_francesa(f, s, 5.15, 1.1, 1.95, color="#4a2e22")
        marco_piedra(f, s, 1.1, 5.15, 7.1, color="#f1ede4", ancho=0.15)
        guardapolvo_arco(f, s, 1.3, 7.4, color="#f4f1ea")
        balcon(f, s, 5.15, ancho=1.6, vuelo=0.5, losa="#c9ad86", menulas=3)
    for s in pil:                                                                    # pilastras blancas
        x = min(max(s, 0.3), L - 0.3)
        f.caja(x - 0.3, x + 0.3, 1.2, 8.5, 0.0, 0.12, "moldura", "#f4f1ea")
    f.caja(0.0, L, 8.5, 8.75, -PROF, 0.3, "moldura", "#f4f1ea")
    f.caja(0.0, L, 8.75, 9.35, -PROF, -0.04, "muro", CREMA)
    f.caja(0.0, L, 9.35, 9.45, -PROF, 0.02, "moldura", "#f4f1ea")
    for s in pil:
        x = min(max(s, 0.3), L - 0.3)
        f.caja(x - 0.28, x + 0.28, 8.75, 9.7, -PROF, 0.1, "moldura", "#f4f1ea")
        q = f.punto(x, 9.7, -0.1)
        pinaculo(c, q.x, q.y, q.z, base=0.34, alto=0.55, color="#f4f1ea")
    return f


# ------------------------------------------------------------------------------------------------ G. arquería
def arqueria(c, t0, t1, n=3):
    f = fachada_de(c, t0, t1)
    L = f.largo
    desde = desde_de(f)
    pil = 1.2
    luz = (L - pil * (n + 1)) / n
    ESP = 0.9                                                                         # espesor del muro de arcos
    arr = 4.3
    # muro de arcos con enjutas que siguen el arco (R0227: con hueco_arco el vano salía en escalones) y muro lleno
    # sobre cada pilar; la rosca de moldura la pone arqueria_lisa
    arqueria_lisa(f, 0.0, n, luz, arr, pilar=pil, d0=-ESP, d1=0.0, alto_total=7.55, muro=("muro", BLANCO),
                  moldura=("moldura", "#f4f2ee"), segmentos=24)
    for k in range(n + 1):                                                            # pilares con tableros
        s0 = k * (pil + luz)
        f.caja(s0 + 0.15, s0 + pil - 0.15, 0.5, arr - 0.4, 0.0, 0.06, "moldura", "#f4f2ee")
        f.caja(s0 + 0.25, s0 + pil - 0.25, 0.6, arr - 0.5, 0.06, 0.08, "moldura", "#e9e6e0")
        f.caja(s0 - 0.05, s0 + pil + 0.05, desde, 0.5, -ESP - 0.05, 0.12, "moldura", "#ecebe6")   # basa
        f.caja(s0 - 0.05, s0 + pil + 0.05, arr - 0.25, arr, -ESP - 0.05, 0.12, "moldura", "#f4f2ee")   # imposta
        if 0 < k < n:
            q = f.punto(s0 + pil / 2, arr + 1.6, 0.0)                                 # farol colgado de ménsula
            f.caja(s0 + pil / 2 - 0.03, s0 + pil / 2 + 0.03, arr + 1.55, arr + 1.65, 0.0, 0.5, "hierro", HIERRO)
            p = f.punto(s0 + pil / 2, arr + 1.0, 0.5)
            f.c.cilindro(p.x, p.y, p.z - 0.22, p.z + 0.22, 0.12, "hierro", HIERRO, lados=6, radio_arriba=0.06)
            f.c.cilindro(p.x, p.y, p.z - 0.15, p.z + 0.12, 0.09, "vidrio", "#e8dcb0", lados=6)
    for k in range(n):
        s = pil * (k + 1) + luz * (k + 0.5)
        f.caja(s - 0.18, s + 0.18, arr + luz / 2 - 0.05, arr + luz / 2 + 0.45, 0.0, 0.14, "moldura", "#f4f2ee")
    # entablamento con tableros, cornisa y pretil con pedestales y remates verdes
    f.caja(0.0, L, 7.0, 7.25, -ESP, 0.12, "moldura", "#f4f2ee")
    for k in range(n * 3):
        s = L * (k + 0.5) / (n * 3)
        f.caja(s - 0.12, s + 0.12, 7.3, 7.55, 0.0, 0.06, "moldura", "#e9e6e0")
    f.caja(0.0, L, 7.6, 7.85, -ESP - 0.1, 0.28, "moldura", "#f4f2ee")
    f.caja(0.0, L, 7.85, 8.45, -ESP, -0.04, "muro", BLANCO)
    f.caja(0.0, L, 8.45, 8.55, -ESP - 0.04, 0.02, "moldura", "#e6e2da")
    for k in range(n + 1):
        s = k * (pil + luz) + pil / 2
        f.caja(s - 0.35, s + 0.35, 7.85, 8.8, -ESP, 0.08, "moldura", BLANCO)
        q = f.punto(s, 8.8, -ESP / 2)
        c.cilindro(q.x, q.y, q.z, q.z + 0.25, 0.2, "moldura", "#f4f2ee", lados=8, radio_arriba=0.12)
        c.esfera(q.x, q.y, q.z + 0.45, 0.2, "piedra", "#3f8a5a", segmentos=8)
        c.cilindro(q.x, q.y, q.z + 0.6, q.z + 0.85, 0.05, "piedra", "#3f8a5a", lados=6, radio_arriba=0.0)
    pz = 2 * pil + luz - pil / 2                                                       # placa «Calle San Alberto»
    f.caja(pz - 0.35, pz + 0.35, 3.0, 3.35, 0.08, 0.1, "letrero", "#1d1d1b")
    f.caja(pz - 0.28, pz + 0.28, 3.12, 3.24, 0.1, 0.105, "letrero", "#d8d4c8")
    return f


# ------------------------------------------------------------------------------------------------ cables
def cables(col, caras):
    """Haz de cables negro por las fachadas, a la altura de la faja (R0216–R0222), de ménsula en ménsula."""
    c = Constructor(MID + "_cables")
    puntos = []
    for f, h, d in caras:
        if puntos:                          # junta entre casas: el haz da la vuelta por fuera de la arista
            p0, p1 = puntos[-1], tuple(f.punto(min(0.25, f.largo), h - 0.05, d))
            nx, ny = f.n.x + ultimo_n[0], f.n.y + ultimo_n[1]
            k = math.hypot(nx, ny) or 1.0
            puntos.append(((p0[0] + p1[0]) / 2 + 0.3 * nx / k, (p0[1] + p1[1]) / 2 + 0.3 * ny / k,
                           (p0[2] + p1[2]) / 2))
        ultimo_n = (f.n.x, f.n.y)
        n = max(2, round(f.largo / 4.5))
        for k in range(n + 1):
            s = min(max(f.largo * k / n, 0.25), f.largo - 0.25)
            g = copy.copy(f)
            g.c = c
            soporte_cable(g, s, h, d)
            puntos.append(tuple(f.punto(s, h - 0.05, d)))
    for p, q in zip(puntos, puntos[1:]):
        for j, (dh, dd) in enumerate(((0.0, 0.0), (0.06, 0.05), (-0.05, 0.08))):
            prev = None
            for k in range(7):
                u = k / 6
                x = p[0] + (q[0] - p[0]) * u
                y = p[1] + (q[1] - p[1]) * u
                z = p[2] + (q[2] - p[2]) * u - 0.12 * math.sin(math.pi * u) + dh
                pt = (x, y, z)
                if prev:
                    tubo(c, prev, pt, 0.03 if j == 0 else 0.02, "hierro", HIERRO)
                prev = pt
    c.objeto(col)


# ------------------------------------------------------------------------------------------------ construcción
def construir(col):
    tr = tramos_casas()
    caras = []
    c = Constructor(MID + "_prodem")
    fa, fe = prodem(c, *tr["A"])
    c.objeto(col)
    hechos = {}
    for letra, fn in (("B", casa_b), ("C", casa_c), ("D", casa_d), ("E", casa_e), ("F", casa_f)):
        c = Constructor(MID + "_casa_" + letra.lower())
        hechos[letra] = fn(c, *tr[letra])
        c.objeto(col)
    c = Constructor(MID + "_arqueria")
    arqueria(c, T_PLAZA, T_ARCO1)
    c.objeto(col)
    caras = [(fa, 4.2, 0.45), (hechos["B"], 4.1, 0.4), (hechos["C"], 4.15, 0.4), (hechos["D"], 4.95, 0.45),
             (hechos["E"], 3.9, 0.4), (hechos["F"], 4.2, 0.4)]
    cables(col, caras)


if __name__ == "__main__":
    m, col = iniciar(AGENTE, MID)
    construir(col)
    exportar(AGENTE, MID)
