"""SAN_MIGUEL — templo de San Miguel sobre la Calle Arenales, de Junín al Teatro (R0219, 2026-11-24).

Traspaso de codex a claude pedido por el usuario en R0219 ("hazlo tu, cambio de dueno"): espacio SAN_MIGUEL del
reparto; la nave sale de blender/zonas/codex/M037.py. Inventario y planta: SAN_MIGUEL_INVENTARIO.md.
Fotos: 130401, 130404, 130406, 130413 (nave desde Junín), 130427, 130431, 130435, 130438 (nave hacia el SE),
130440, 130442, 130445 (atrio, torre y portada), 130448 (casa del café junto al Teatro).

Marco de la sección: s a lo largo de Arenales desde la fachada a Junín hacia el SE; d hacia la calle (la línea de
fachada está en d = -0,2; el eje de Arenales, en d = 6,0). Detrás (d < -16,5) está el convento de codex (Eeb6abd).

Piezas:
1. Nave (s 0–49,5): muro blanco liso sin zócalo; cuerpo junto a Junín más alto (13 m) y el resto con el alero en
   escalones (11,4 → 10,4 → 9,4 m), pináculos en cada escalón, gárgolas; vanos altos en nichos abocinados y de
   arco, dos con bandera boliviana, faroles de brazo verdes; dos puertas de madera y el letrero del Café Valentino
   junto a Junín; enredadera en la esquina del atrio.
2. Portada (fachada SE, mira al atrio): hastial con tejaroz de tejas sobre canes, portada barroca blanca (puerta de
   arco, columnas pareadas sobre pedestales, entablamento, hornacina con frontón, remate escalonado con pináculos).
3. Torre (fondo del atrio, junto a la portada): fuste blanco con filetes rosados, cuerpo de campanas con dos arcos
   por cara, cornisa con pináculos, segundo cuerpo de un arco, linterna con óculos, cupulín y pararrayos.
4. Atrio (s 49,5–59): piso de losas pardas 0,5 m sobre la vereda, muro de sillares con reja de lanzas, pilares de
   sillar con remate piramidal, portón de pilares blancos con reja de dos hojas, arco de volutas y cruz; gradas;
   terraza del café con su reja y bancos; buganvillas y macetas; al fondo la casa de dos plantas de los souvenirs.
5. Casa del café La Torre Café Mirador (s 59–64,35): dos plantas, techo a cuatro aguas con alero sobre canes rojizos,
   balcón de hierro con macetas sobre ménsulas de volutas, ventana de arco rebajado con reja, zócalo y esquinal de
   sillares; ventanas rojas en el lado del atrio.
6. Faroles de poste junto al bordillo (frente al portón y a la casa del café).
"""

import copy
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from kit.arquitectura import _enjuta  # noqa: E402
from base_mobiliario import tubo  # noqa: E402
from base_suelo import ALTO_VEREDA, SOBRE_TERRENO  # noqa: E402
from ortiz_se import zocalo_sillares  # noqa: E402
from piezas_claude import al_bordillo, fronton  # noqa: E402
from san_felipe_costado import sillares  # noqa: E402

AGENTE, MID = "claude", "SAN_MIGUEL"

# ------------------------------------------------------------------------------------------------ marco y datos
O = (-292.582, -40.463)
U = (0.771, -0.637)              # a lo largo de Arenales, hacia el SE
N = (0.637, 0.771)               # hacia la calle
NU = (-U[0], -U[1])
NN = (-N[0], -N[1])
DF = -1.2                        # línea de fachada (−0,2 hasta el ensanche de Arenales del 2026-11-24)
S_ATRIO, S_CAFE, S_FIN = 49.5, 59.0, 64.35
TORRE = (47.2, 52.4, -11.0)      # s0, s1, d del frente de la torre (el fondo va contra el convento)
D_PORTADA = -8.2

BLANCO = "#f3f1ec"
MOLD = "#e8e4db"
ROSA = "#e3bcae"
TEJA = "#b4593a"
CAN = "#7a2f22"
ROJO = "#8e2a22"
MADERA = "#5a3324"
HIERRO = "#24221f"
VERDE_FAROL = "#2f5a4f"
PARDO = ("#a98a6c", "#957759", "#b39577", "#86694f", "#9c7f62")
PILAR = "#b09072"
LOSA = "#9a8269"

# alero de la nave por tramos (s0, s1, z absoluta del alero): sube hacia Junín en escalones (130406, 130413)
TRAMOS = [(0.0, 17.0, 69.0), (17.0, 29.0, 67.9), (29.0, 38.0, 67.4), (38.0, S_ATRIO, 67.0)]
PEND = 22.0


def P(s, d):
    return (O[0] + s * U[0] + d * N[0], O[1] + s * U[1] + d * N[1])


def zv(s, d=DF):
    """Altura de la vereda (o del suelo) al pie de la fachada en s."""
    x, y = P(s, d)
    return altura_suelo(x, y) + SOBRE_TERRENO + ALTO_VEREDA


def fondo(s):
    """d del fondo: la arista del convento de codex (Eeb6abd) menos 3 cm; sin convento detrás, -16,4."""
    if s > 57.8:
        return -16.4
    return -16.0 - 0.5 * (s + 0.7) / 50.9 + 0.03


ZA = 58.65                       # piso del atrio (+0,5 sobre la vereda del portón)
WT = 59.25                       # coronación del muro del atrio
Z_CAFE = zv(S_CAFE)              # piso de la casa del café


def fach(c, s0, d0, s1, d1, normal, suelo=0.0):
    return Fachada(c, {"a": P(s0, d0), "b": P(s1, d1), "normal": normal}, suelo)


def mover(f, dd=0.0, suelo=None):
    g = copy.copy(f)
    g.a = f.a + f.n * dd
    if suelo is not None:
        g.suelo = suelo
    return g


def quad(s0, s1, d0, d1):
    return [P(s0, d0), P(s1, d0), P(s1, d1), P(s0, d1)]


def pinaculo(c, x, y, z, base=0.36, alto=0.95, color=BLANCO):
    c.caja(x - base / 2, y - base / 2, z, x + base / 2, y + base / 2, z + 0.3, "moldura", color)
    c.cilindro(x, y, z + 0.3, z + 0.3 + alto, base * 0.42, "moldura", color, lados=8, radio_arriba=0.02)
    c.esfera(x, y, z + 0.32 + alto, 0.06, "moldura", color, segmentos=6)


def disco(f, s, h, d, r, rol, color, lados=12):
    pts = [f.punto(s + r * math.cos(2 * math.pi * k / lados), h + r * math.sin(2 * math.pi * k / lados), d)
           for k in range(lados)]
    f.c.poligono(pts, rol, color, grosor=0.03, normal_extrusion=tuple(f.n))


def matorral(c, x, y, z, r, semilla, flores=0.35, alto=1.0, n=14):
    """Mata de buganvilla: muchas bolitas de follaje de dos verdes, más densas abajo, con flores naranjas."""
    import random
    rnd = random.Random(semilla)
    for k in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        rr = r * math.sqrt(rnd.random())
        dz = alto * rnd.random() ** 0.8
        ancho = 1.0 - 0.45 * dz / max(alto, 0.01)
        px, py = x + math.cos(a) * rr * ancho, y + math.sin(a) * rr * ancho
        rb = r * rnd.uniform(0.28, 0.42)
        c.esfera(px, py, z + 0.2 + dz, rb, "follaje" if k % 3 else "follaje_claro", None, segmentos=6)
        if rnd.random() < flores:
            c.esfera(px + rnd.uniform(-.1, .1), py + rnd.uniform(-.1, .1), z + 0.2 + dz + rb * 0.7, rb * 0.4, "flor",
                     "#e2783a", segmentos=5)


def enredadera(f, s0, s1, h0, h1, semilla, n=300):
    """Enredadera pegada al muro (130431, 130435): masa tupida arriba y guías colgantes, hojas en racimos chatos."""
    import random
    rnd = random.Random(semilla)
    guias = [s0 + (s1 - s0) * (0.62 + 0.15 * k) for k in range(3)]
    for k in range(n):
        if k < n * 0.55:                                                         # masa de arriba
            s = rnd.uniform(s0, s1)
            h = h1 - (h1 - h0) * 0.4 * rnd.random() ** 1.6
        else:                                                                    # guías que cuelgan
            g = guias[k % len(guias)]
            h = h1 - (h1 - h0) * rnd.random()
            s = g + 0.3 * math.sin(h * 0.9 + k) + rnd.uniform(-0.45, 0.45)
        q = f.punto(s, h, rnd.uniform(0.06, 0.28))
        rb = rnd.uniform(0.09, 0.2)
        f.c.esfera(q.x, q.y, q.z, rb, "follaje" if k % 3 else "follaje_claro", None, segmentos=5)
    for g in guias:                                                              # tallos
        tubo(f.c, f.punto(g, h1 - 0.3, 0.06), f.punto(g + 0.15, h0 + 0.4, 0.06), 0.02, "tronco", "#4a3626")


def maceta(c, x, y, z, semilla=0):
    c.cilindro(x, y, z, z + 0.32, 0.16, "piedra", "#b0603e", lados=8, radio_arriba=0.2)
    c.esfera(x, y, z + 0.45, 0.22, "follaje" if semilla % 2 else "follaje_claro", None, segmentos=6)
    if semilla % 3 == 0:
        c.esfera(x, y, z + 0.6, 0.1, "flor", "#d8433a", segmentos=6)


# ------------------------------------------------------------------------------------------------ piezas de fachada
def muro_con_huecos(f, s0, s1, techo, huecos, z_pie, prof=0.45, rol=("muro", BLANCO)):
    """Paño de muro de espesor `prof` (d de -prof a 0) entre s0 y s1 con huecos rectangulares (sa, sb, ha, hb) en z
    absoluta (f.suelo = 0). techo(s): z del tope del paño en s. Los cortes del paño siguen los huecos y los tramos."""
    cortes = {s0, s1}
    for a, b, _, _ in huecos:
        cortes |= {a, b}
    for a, _, _ in TRAMOS:
        if s0 < a < s1:
            cortes.add(a)
    cortes = sorted(c for c in cortes if s0 <= c <= s1)
    for a, b in zip(cortes, cortes[1:]):
        if b - a < 1e-3:
            continue
        m = (a + b) / 2
        top = techo(m)
        abajo = z_pie(m)
        for ha, hb in sorted((h[2], h[3]) for h in huecos if h[0] <= m <= h[1]):
            if ha > abajo:
                f.caja(a, b, abajo, ha, -prof, 0.0, *rol)
            abajo = max(abajo, hb)
        if top > abajo:
            f.caja(a, b, abajo, top, -prof, 0.0, *rol)


def nicho_abocinado(f, s, z0, w, alto, prof=0.45, abre=0.32):
    """Ventana honda en nicho de jambas abocinadas (130406): devuelve el hueco del paño; dibuja derrames y ventana."""
    a0, a1 = s - w / 2 - abre, s + w / 2 + abre
    b0, b1 = z0 - abre * 0.6, z0 + alto + abre
    i0, i1, j0, j1 = s - w / 2, s + w / 2, z0, z0 + alto
    q = lambda ss, hh, dd: f.punto(ss, hh, dd)
    for pts in ([q(a0, b0, 0), q(a0, b1, 0), q(i0, j1, -prof), q(i0, j0, -prof)],
                [q(i1, j0, -prof), q(i1, j1, -prof), q(a1, b1, 0), q(a1, b0, 0)],
                [q(a0, b1, 0), q(a1, b1, 0), q(i1, j1, -prof), q(i0, j1, -prof)],
                [q(i0, j0, -prof), q(i1, j0, -prof), q(a1, b0, 0), q(a0, b0, 0)]):
        f.c.poligono(pts, "muro", BLANCO)
    fi = mover(f, -prof + 0.01)
    fi.caja(i0, i1, j0, j1, -0.01, 0.0, "vidrio", "#2e3236")
    for x in (i0, s - 0.02, i1 - 0.06):
        fi.caja(x, x + 0.06, j0, j1, 0.0, 0.04, "marco_ventana", MADERA)
    for k in range(5):                                                           # reja de cuadros
        x = i0 + w * (k + 0.5) / 5
        fi.caja(x - 0.012, x + 0.012, j0, j1, 0.06, 0.09, "hierro", HIERRO)
    for k in range(6):
        hh = j0 + alto * (k + 0.5) / 6
        fi.caja(i0, i1, hh - 0.012, hh + 0.012, 0.06, 0.09, "hierro", HIERRO)
    return (a0, a1, b0, b1)


def ventana_arco_honda(f, s, z0, w, alto, prof=0.45, recuadro=False):
    """Ventana de arco metida en el muro (jambas rectas); con recuadro moldurado alrededor (130413)."""
    r = w / 2
    arr = z0 + alto - r
    _enjuta(f, s, r, arr, z0 + alto + 0.02, -prof, 0.0, "muro", BLANCO)
    f.arco(s, r - 0.02, 0.1, arr, -prof, -0.01, "muro", BLANCO, segmentos=10)
    fi = mover(f, -prof + 0.01)
    fi.caja(s - r, s + r, z0, arr, -0.01, 0.0, "vidrio", "#2e3236")
    fi.timpano_arco(s, r, arr, 0.0, "vidrio", "#2e3236")
    for x in (s - r, s - 0.03, s + r - 0.06):
        fi.caja(x, x + 0.06, z0, arr, 0.0, 0.04, "marco_ventana", MADERA)
    for k in range(5):
        x = s - r + w * (k + 0.5) / 5
        top = arr + math.sqrt(max(0.0, r * r - (x - s) ** 2)) - 0.05
        fi.caja(x - 0.012, x + 0.012, z0, top, 0.06, 0.09, "hierro", HIERRO)
    for k in range(5):
        hh = z0 + (arr - z0) * (k + 0.5) / 5
        fi.caja(s - r, s + r, hh - 0.012, hh + 0.012, 0.06, 0.09, "hierro", HIERRO)
    f.caja(s - r - 0.1, s + r + 0.1, z0 - 0.12, z0, -0.02, 0.1, "moldura", MOLD)            # alféizar
    if recuadro:
        e, g = 0.55, 0.16
        for x0, x1 in ((s - r - e, s - r - e + g), (s + r + e - g, s + r + e)):
            f.caja(x0, x1, z0 - 0.45, z0 + alto + 0.45, 0.0, 0.07, "moldura", MOLD)
        for h0 in (z0 - 0.45, z0 + alto + 0.45 - g):
            f.caja(s - r - e, s + r + e, h0, h0 + g, 0.0, 0.07, "moldura", MOLD)
    return (s - r, s + r, z0, z0 + alto + 0.02)


def bandera(f, s, h):
    """Bandera boliviana en un asta inclinada que sale del alféizar (130427, 130431)."""
    p0 = f.punto(s - 0.25, h, 0.05)
    p1 = f.punto(s - 0.25, h + 0.75, 0.75)
    tubo(f.c, p0, p1, 0.02, "madera", "#6b4a33")
    for j, color in enumerate(("#c8302a", "#e9c42c", "#2f7d3a")):
        a = 0.26
        top = h + 0.72 - j * a
        f.c.poligono([f.punto(s - 0.25, top, 0.72), f.punto(s + 0.45, top - 0.06, 0.55),
                      f.punto(s + 0.45, top - a - 0.06, 0.55), f.punto(s - 0.25, top - a, 0.72)],
                     "pintura_acento", color, grosor=0.01, normal_extrusion=tuple(f.n))


def farol_brazo(f, s, h, vuelo=0.85):
    """Farol de brazo con pantalla verde (130406, 130431)."""
    f.caja(s - 0.09, s + 0.09, h - 0.25, h + 0.25, 0.0, 0.05, "hierro", VERDE_FAROL)
    tubo(f.c, f.punto(s, h + 0.15, 0.05), f.punto(s, h + 0.15, vuelo), 0.025, "hierro", VERDE_FAROL)
    tubo(f.c, f.punto(s, h - 0.2, 0.05), f.punto(s, h + 0.15, vuelo * 0.6), 0.02, "hierro", VERDE_FAROL)
    q = f.punto(s, h + 0.15, vuelo)
    f.c.cilindro(q.x, q.y, q.z - 0.42, q.z - 0.05, 0.27, "hierro", VERDE_FAROL, lados=10, radio_arriba=0.06)
    f.c.cilindro(q.x, q.y, q.z - 0.55, q.z - 0.42, 0.12, "vidrio", "#efe2b5", lados=8)


def farol_cuello(c, x, y, z, nx, ny, alto=3.5):
    """Farol negro de poste con el brazo en cuello de cisne y el farol colgado (130440, 130442, 130448)."""
    c.cilindro(x, y, z, z + 0.45, 0.13, "hierro", HIERRO, lados=8, radio_arriba=0.08)
    c.cilindro(x, y, z + 0.45, z + alto, 0.055, "hierro", HIERRO, lados=8)
    prev = (x, y, z + alto)
    for k in range(1, 7):
        a = math.pi * k / 6
        p = (x + nx * 0.25 * (1 - math.cos(a)), y + ny * 0.25 * (1 - math.cos(a)), z + alto + 0.3 * math.sin(a))
        tubo(c, prev, p, 0.022, "hierro", HIERRO)
        prev = p
    lx, ly, lz = prev
    c.caja(lx - 0.02, ly - 0.02, lz - 0.2, lx + 0.02, ly + 0.02, lz, "hierro", HIERRO)
    c.cilindro(lx, ly, lz - 0.32, lz - 0.2, 0.17, "hierro", HIERRO, lados=6, radio_arriba=0.05)
    c.cilindro(lx, ly, lz - 0.7, lz - 0.32, 0.12, "vidrio", "#efe2b5", lados=6, radio_arriba=0.15)
    c.cilindro(lx, ly, lz - 0.78, lz - 0.7, 0.1, "hierro", HIERRO, lados=6)


def reja_lanzas(f, s0, s1, h0, h1, d=-0.2, paso=0.13):
    """Reja de lanzas con friso de volutas abajo (aros) y puntas arriba."""
    for hh in (h0 + 0.06, h0 + 0.5, h1 - 0.12):
        f.caja(s0, s1, hh - 0.025, hh + 0.025, d - 0.025, d + 0.025, "hierro", HIERRO)
    n = max(1, int((s1 - s0) / paso))
    for k in range(n + 1):
        s = s0 + (s1 - s0) * k / n
        f.caja(s - 0.012, s + 0.012, h0, h1, d - 0.012, d + 0.012, "hierro", HIERRO)
        q = f.punto(s, h1, d)
        f.c.cilindro(q.x, q.y, q.z, q.z + 0.12, 0.03, "hierro", HIERRO, lados=4, radio_arriba=0.002)
    m = max(1, int((s1 - s0) / 0.3))
    for k in range(m):                                                           # aros del friso
        sc = s0 + (s1 - s0) * (k + 0.5) / m
        r = 0.13
        for j in range(8):
            a0, a1 = 2 * math.pi * j / 8, 2 * math.pi * (j + 1) / 8
            tubo(f.c, f.punto(sc + r * math.cos(a0), h0 + 0.28 + r * math.sin(a0), d),
                 f.punto(sc + r * math.cos(a1), h0 + 0.28 + r * math.sin(a1), d), 0.01, "hierro", HIERRO)


def cuatro_aguas(c, s0, s1, d0, d1, z, vuelos, pend=24.0, rol=("teja", TEJA)):
    """Tejado a cuatro aguas sobre el rectángulo s0..s1 × d1..d0 (d0 > d1); vuelos = (s0, s1, d0, d1).
    Cumbrera a lo largo de d (el lado largo). Devuelve la altura de la cumbrera sobre z."""
    t = math.tan(math.radians(pend))
    a0, a1 = s0 - vuelos[0], s1 + vuelos[1]
    b0, b1 = d0 + vuelos[2], d1 - vuelos[3]
    zl = z - 0.1
    w = (a1 - a0) / 2
    sm = (a0 + a1) / 2
    alto = w * t
    r0, r1 = b0 - w, b1 + w
    Q = lambda s, d, h: (*P(s, d), zl + h)
    caras = [[Q(a0, b0, 0), Q(a1, b0, 0), Q(sm, r0, alto)],
             [Q(a1, b1, 0), Q(a0, b1, 0), Q(sm, r1, alto)],
             [Q(a1, b0, 0), Q(a1, b1, 0), Q(sm, r1, alto), Q(sm, r0, alto)],
             [Q(a0, b1, 0), Q(a0, b0, 0), Q(sm, r0, alto), Q(sm, r1, alto)]]
    for cara in caras:
        c.poligono(cara, *rol, grosor=0.12, normal_extrusion=(0, 0, 1))
    pa, pb = Q(sm, r0, alto + 0.12), Q(sm, r1, alto + 0.12)
    tubo(c, pa, pb, 0.11, *rol)
    for (s_, d_) in ((a0, b0), (a1, b0), (a0, b1), (a1, b1)):                  # limatesas
        tubo(c, Q(s_, d_, 0.14), Q(sm, r0 if d_ == b0 else r1, alto + 0.12), 0.07, *rol)
    return alto


def alero_canes(f, s0, s1, h, vuelo, pend=24.0, paso=0.62, sofito=BLANCO):
    """Sofito blanco y canes rojizos bajo el alero de un tejado que vuela `vuelo` desde la fachada (h: tope del muro)."""
    t = math.tan(math.radians(pend))
    h_borde = h - 0.1 - 0.02
    sube = (-f.n + f.z * t).normalized()
    perp = f.u.cross(sube).normalized()
    if perp.z < 0:
        perp = -perp
    largo = vuelo / math.cos(math.radians(pend))
    centro = f.punto((s0 + s1) / 2, h_borde, vuelo) + sube * (largo / 2) - perp * 0.02
    f.c.caja_ejes(centro, f.u, sube, perp, s1 - s0, largo, 0.03, "moldura", sofito)
    f.caja(s0, s1, h - 0.3, h + vuelo * t - 0.1, 0.0, 0.03, "moldura", sofito)               # friso
    s = s0 + 0.3
    while s < s1 - 0.15:
        f.caja(s - 0.06, s + 0.06, h - 0.3, h - 0.12, 0.0, vuelo - 0.05, "madera", CAN)
        s += paso


# ------------------------------------------------------------------------------------------------ 1. nave
def nave(c):
    def techo_de(s):
        for a, b, z in TRAMOS:
            if a <= s <= b:
                return z
        return TRAMOS[-1][2]

    zb = zv(0.0) - 0.8
    for a, b, z in TRAMOS:                                                       # cuerpo (detrás del paño)
        c.prisma([P(a, DF - 0.45), P(b, DF - 0.45), P(b, fondo(b)), P(a, fondo(a))], zb, z, "muro", BLANCO)

    # --- tejados a dos aguas por tramo (cumbrera paralela a la calle), con hastiales en los escalones
    t = math.tan(math.radians(PEND))
    for k, (a, b, z) in enumerate(TRAMOS):
        va = 0.35 if k == 0 else 0.0
        vb = 1.2 if k == len(TRAMOS) - 1 else 0.35                               # tejaroz sobre la portada
        dm = (DF + fondo((a + b) / 2)) / 2
        alto = (DF - dm) * t
        v = 0.45
        aa, bb = a - va, b + vb
        Q = lambda s, d, h: (*P(s, d), h)
        e0, e1 = z - v * t, z - v * t
        c.poligono([Q(aa, DF + v, e0), Q(bb, DF + v, e0), Q(bb, dm, z + alto), Q(aa, dm, z + alto)],
                   "teja", TEJA, grosor=0.14, normal_extrusion=(0, 0, 1))
        c.poligono([Q(bb, fondo(b) - 0.1, z - 0.1 * t), Q(aa, fondo(a) - 0.1, z - 0.1 * t), Q(aa, dm, z + alto),
                    Q(bb, dm, z + alto)], "teja", TEJA, grosor=0.14, normal_extrusion=(0, 0, 1))
        tubo(c, Q(aa, dm, z + alto + 0.14), Q(bb, dm, z + alto + 0.14), 0.12, "teja", TEJA)
        fa = fach(c, aa, DF, bb, DF, N)
        fa.caja(0.0, bb - aa, e0 - 0.02, e0 + 0.2, v - 0.08, v + 0.04, "teja", TEJA)   # boca de teja
        for s_h in (a, b):                                                       # hastiales
            c.poligono([Q(s_h, DF - 0.02, z), Q(s_h, fondo(s_h) + 0.02, z), Q(s_h, dm, z + alto - 0.05)], "muro",
                       BLANCO, grosor=0.3, normal_extrusion=(NU[0], NU[1], 0) if s_h == b else (U[0], U[1], 0))

    # --- paño de la fachada a Arenales con sus vanos
    f = fach(c, 0.0, DF, S_ATRIO, DF, N)
    huecos = []
    huecos.append(nicho_abocinado(f, 7.5, zv(7.5) + 9.0, 0.95, 1.25))
    huecos.append(ventana_arco_honda(f, 12.6, zv(12.6) + 6.6, 1.1, 2.1))
    huecos.append(nicho_abocinado(f, 20.3, zv(20.3) + 7.1, 0.9, 1.15))
    huecos.append(ventana_arco_honda(f, 26.0, zv(26.0) + 6.2, 1.0, 1.8, recuadro=True))
    huecos.append(nicho_abocinado(f, 33.6, zv(33.6) + 6.3, 0.9, 1.1))
    huecos.append(nicho_abocinado(f, 44.2, zv(44.2) + 6.0, 0.9, 1.1))
    muro_con_huecos(f, 0.0, S_ATRIO, techo_de, huecos, lambda s: zv(s) - 0.8)
    bandera(f, 33.6, zv(33.6) + 6.3)
    bandera(f, 44.2, zv(44.2) + 6.0)
    farol_brazo(f, 24.2, zv(24.2) + 5.0)
    farol_brazo(f, 42.3, zv(42.3) + 5.3)
    # cornisa blanca bajo el alero, pináculos en los escalones y gárgolas
    for k, (a, b, z) in enumerate(TRAMOS):
        f.caja(a, b, z - 0.42, z - 0.22, 0.0, 0.12, "moldura", MOLD)
        f.caja(a, b, z - 0.22, z - 0.1, 0.0, 0.22, "moldura", MOLD)
        if k > 0:
            x, y = P(a - 0.25, DF - 0.25)
            pinaculo(c, x, y, z - 0.05)
        for sg in (a + 0.35 * (b - a), a + 0.8 * (b - a)):
            tubo(c, f.punto(sg, z - 0.7, -0.05), f.punto(sg, z - 0.62, 0.6), 0.07, "moldura", MOLD)
    # planta baja junto a Junín: dos puertas de madera y el letrero del Café Valentino (130404, 130406)
    for s, w, alto, reja in ((3.0, 2.0, 3.0, True), (7.0, 1.3, 2.7, False)):
        g = mover(f, 0.0, zv(s))
        g.caja(s - w / 2 - 0.12, s + w / 2 + 0.12, -0.05, alto + 0.12, 0.0, 0.03, "moldura", MOLD)
        g.caja(s - w / 2, s + w / 2, 0.0, alto, 0.03, 0.06, "madera", "#6e3a26")
        g.caja(s - 0.015, s + 0.015, 0.0, alto, 0.06, 0.075, "madera", "#4a2618")
        for hh in (0.5, 1.5) if not reja else (0.5,):
            for x in (s - w / 4, s + w / 4):
                g.caja(x - w / 4 + 0.1, x + w / 4 - 0.1, hh, hh + 0.8, 0.06, 0.08, "madera", "#5e301f")
        if reja:
            for k in range(7):
                x = s - w / 2 + 0.2 + (w - 0.4) * k / 6
                g.caja(x - 0.015, x + 0.015, 1.6, alto - 0.2, 0.07, 0.1, "hierro", HIERRO)
            g.caja(s - w / 2 + 0.2, s + w / 2 - 0.2, 1.6, 1.64, 0.07, 0.1, "hierro", HIERRO)
            g.caja(s - w / 2 + 0.2, s + w / 2 - 0.2, alto - 0.24, alto - 0.2, 0.07, 0.1, "hierro", HIERRO)
        g.caja(s - w / 2 - 0.2, s + w / 2 + 0.2, -0.05, 0.12, 0.0, 0.25, "piedra", "#b9a58d")      # umbral
    g = mover(f, 0.0, zv(5.0))
    g.caja(4.45, 5.55, 3.05, 3.65, 0.0, 0.05, "madera", "#5b2e1e")
    g.caja(4.53, 5.47, 3.12, 3.58, 0.05, 0.07, "letrero", "#efe0c2")
    g = mover(f, 0.0, zv(0.6))
    g.caja(0.25, 1.15, 3.55, 3.85, 0.0, 0.04, "letrero", "#5b6e7d")                         # placa de la calle
    # enredadera en la esquina del atrio (130431, 130435)
    enredadera(f, 44.6, 49.4, zv(48.0) + 0.2, zv(48.0) + 8.7, 400)

    # --- fachada a Junín (cabecera): muro liso con alero y hastial
    fj = fach(c, 0.0, fondo(0.0), 0.0, DF, NU)
    fj.caja(0.0, DF - fondo(0.0), zb, TRAMOS[0][2] - 0.42, -0.02, 0.0, "muro", BLANCO)
    fj.caja(0.0, DF - fondo(0.0), TRAMOS[0][2] - 0.42, TRAMOS[0][2] - 0.22, 0.0, 0.12, "moldura", MOLD)
    nicho_abocinado(mover(fj, 0.46), (DF - fondo(0.0)) / 2, zv(0.0) + 8.6, 0.9, 1.2)


def cables_nave(c, g):
    """Haz de cables que corre por el muro de la nave sobre grampas (130404–130413); g: Constructor del templo."""
    from base_mobiliario import cable
    f = fach(g, 0.0, DF, S_ATRIO, DF, N)
    grampas = [0.6, 8.5, 16.5, 24.2, 32.0, 40.0, 48.0]
    for s in grampas:
        h = zv(s) + 4.6
        f.caja(s - 0.04, s + 0.04, h - 0.1, h + 0.35, 0.0, 0.24, "hierro", "#3a3a36")
    for k in range(5):
        for a, b in zip(grampas, grampas[1:]):
            p0 = f.punto(a, zv(a) + 4.62 + 0.06 * k, 0.12 + 0.025 * k)
            p1 = f.punto(b, zv(b) + 4.62 + 0.06 * k, 0.12 + 0.025 * k)
            cable(c, tuple(p0), tuple(p1), 0.12 + 0.05 * k, radio=0.014)


# ------------------------------------------------------------------------------------------------ 2. portada
def portada(c):
    """Fachada SE de la nave, sobre el atrio (130440, 130442, 130445). Local: s = DF - d."""
    a, b, z4 = TRAMOS[-1]
    f = fach(c, S_ATRIO, DF, S_ATRIO, fondo(S_ATRIO), U, ZA)
    sc = DF - D_PORTADA
    L = DF - TORRE[2]
    f.caja(0.0, L, -0.6, z4 - ZA - 0.42, 0.0, 0.02, "muro", BLANCO)
    f.caja(0.0, L, z4 - ZA - 0.42, z4 - ZA - 0.1, 0.0, 0.2, "moldura", MOLD)
    # tejaroz: canes rojizos bajo el vuelo de 1,2 m de los faldones
    t = math.tan(math.radians(PEND))
    dm = (DF + fondo(S_ATRIO)) / 2
    for k in range(1, 15):
        d = DF - (DF - dm) * k / 14
        h = z4 + (DF - d) * t - ZA
        s_loc = DF - d
        if s_loc > L - 0.3:
            break
        f.caja(s_loc - 0.06, s_loc + 0.06, h - 0.22, h - 0.04, 0.0, 1.12, "madera", CAN)
    # cuerpo bajo: pedestales, columnas pareadas, puerta de arco
    f.caja(sc - 2.9, sc + 2.9, -0.6, 0.25, 0.0, 0.75, "piedra", "#cbbfae")                    # grada
    f.caja(sc - 1.1, sc + 1.1, 0.25, 3.4, 0.0, 0.08, "moldura", MOLD)
    f.caja(sc - 0.95, sc + 0.95, 0.25, 3.25, 0.08, 0.11, "madera", "#4f2b1c")
    f.timpano_arco(sc, 0.95, 3.25, 0.11, "madera", "#4f2b1c")
    f.caja(sc - 0.015, sc + 0.015, 0.25, 4.2, 0.11, 0.13, "madera", "#3a1e13")
    f.arco(sc, 0.95, 0.28, 3.25, 0.0, 0.2, "moldura", BLANCO, segmentos=12)
    for x in (sc - 1.2, sc + 1.2):
        f.caja(x - 0.17, x + 0.17, 0.25, 3.25, 0.0, 0.2, "moldura", BLANCO)                  # jambas
    f.caja(sc - 0.22, sc + 0.22, 4.15, 4.6, 0.0, 0.3, "moldura", MOLD)                       # clave
    for lado in (-1, 1):
        for x in (sc + lado * 1.75, sc + lado * 2.45):
            f.caja(x - 0.36, x + 0.36, 0.25, 1.55, 0.0, 0.75, "moldura", BLANCO)            # pedestal
            f.caja(x - 0.42, x + 0.42, 1.45, 1.6, 0.0, 0.82, "moldura", MOLD)
            q = f.punto(x, 1.6, 0.42)
            c.cilindro(q.x, q.y, q.z, q.z + 3.75, 0.21, "moldura", BLANCO, lados=10, radio_arriba=0.18)
            for hh in (2.4, 3.5, 4.5):                                              # anillos
                c.cilindro(q.x, q.y, q.z + hh - 1.6, q.z + hh - 1.5, 0.23, "moldura", MOLD, lados=10)
            f.caja(x - 0.32, x + 0.32, 5.35, 5.65, 0.0, 0.72, "moldura", MOLD)            # capitel
        f.caja(sc + lado * 2.1 - 0.12, sc + lado * 2.1 + 0.12, 0.25, 5.35, 0.0, 0.25, "moldura", BLANCO)
    f.caja(sc - 2.95, sc + 2.95, 5.65, 6.25, 0.0, 0.7, "moldura", BLANCO)                    # entablamento
    f.caja(sc - 3.05, sc + 3.05, 6.25, 6.5, 0.0, 0.85, "moldura", MOLD)
    for k in range(13):
        x = sc - 2.85 + 5.7 * k / 12
        f.caja(x - 0.06, x + 0.06, 5.75, 5.95, 0.7, 0.78, "moldura", MOLD)
    # segundo cuerpo: hornacina con frontón, pilastras, volutas
    f.caja(sc - 2.1, sc + 2.1, 6.5, 9.7, 0.0, 0.25, "moldura", BLANCO)
    for lado in (-1, 1):
        x = sc + lado * 1.7
        f.caja(x - 0.28, x + 0.28, 6.5, 7.0, 0.0, 0.6, "moldura", MOLD)
        q = f.punto(x, 7.0, 0.33)
        c.cilindro(q.x, q.y, q.z, q.z + 2.4, 0.17, "moldura", BLANCO, lados=10, radio_arriba=0.15)
        f.caja(x - 0.26, x + 0.26, 9.4, 9.7, 0.0, 0.58, "moldura", MOLD)
        for j in range(5):                                                      # voluta escalonada
            x0 = sc + lado * (2.1 + 0.18 * j)
            f.caja(min(x0, x0 + lado * 0.2), max(x0, x0 + lado * 0.2), 6.5, 6.5 + 1.9 - 0.36 * j, 0.0, 0.22,
                   "moldura", BLANCO)
    f.caja(sc - 0.7, sc + 0.7, 7.1, 8.6, 0.25, 0.27, "madera", "#6c5848")                    # hornacina
    f.timpano_arco(sc, 0.7, 8.6, 0.27, "madera", "#6c5848")
    f.arco(sc, 0.7, 0.14, 8.6, 0.25, 0.4, "moldura", MOLD, segmentos=10)
    q = f.punto(sc, 7.15, 0.45)
    c.cilindro(q.x, q.y, q.z, q.z + 1.1, 0.2, "moldura", "#efeae0", lados=8, radio_arriba=0.13)  # san Miguel
    c.esfera(q.x, q.y, q.z + 1.25, 0.13, "moldura", "#efeae0", segmentos=8)
    f.caja(sc - 0.7, sc + 0.7, 7.0, 7.12, 0.25, 0.55, "moldura", MOLD)
    fronton(mover(f, 0.25), sc, 9.75, 2.0, 0.65, rol="moldura", color=MOLD)
    f.caja(sc - 2.2, sc + 2.2, 9.7, 10.0, 0.0, 0.5, "moldura", MOLD)
    # remate escalonado con pináculos
    f.caja(sc - 1.5, sc + 1.5, 10.0, 10.9, 0.0, 0.3, "moldura", BLANCO)
    f.caja(sc - 0.8, sc + 0.8, 10.9, 11.7, 0.0, 0.3, "moldura", BLANCO)
    f.caja(sc - 1.6, sc + 1.6, 10.85, 11.0, 0.0, 0.4, "moldura", MOLD)
    for x, h in ((sc - 1.5, 10.9), (sc + 1.5, 10.9), (sc - 2.2, 10.0), (sc + 2.2, 10.0)):
        q = f.punto(x, h, 0.18)
        pinaculo(c, q.x, q.y, q.z, base=0.3, alto=0.8)
    q = f.punto(sc, 11.7, 0.15)
    c.caja(q.x - 0.04, q.y - 0.04, q.z, q.x + 0.04, q.y + 0.04, q.z + 0.95, "hierro", HIERRO)       # cruz
    c.caja_ejes((q.x, q.y, q.z + 0.68), (f.u.x, f.u.y, 0), (f.n.x, f.n.y, 0), (0, 0, 1), 0.5, 0.06, 0.06,
                "hierro", HIERRO)


# ------------------------------------------------------------------------------------------------ 3. torre
def caras(c, s0, s1, d0, d1, suelo):
    """Las cuatro caras de un prisma (s0..s1 × d1..d0), normales hacia afuera."""
    return [fach(c, s0, d0, s1, d0, N, suelo), fach(c, s1, d0, s1, d1, U, suelo),
            fach(c, s1, d1, s0, d1, NN, suelo), fach(c, s0, d1, s0, d0, NU, suelo)]


def cuerpo_campanas(c, s0, s1, d0, d1, h0, h1, n_arcos, luz, campana_r, nucleo=0.75):
    """Cuerpo de campanas con arcos abiertos: núcleo metido, pilares, arcos y enjutas; campana en cada arco."""
    c.prisma(quad(s0 + nucleo, s1 - nucleo, d0 - nucleo, d1 + nucleo), ZA + h0, ZA + h1, "muro", "#d8d2c8")
    for f in caras(c, s0, s1, d0, d1, ZA):
        W = f.largo
        pil = (W - n_arcos * luz) / (n_arcos + 1)
        arr = h0 + (h1 - h0) * 0.62
        r = luz / 2
        x = 0.0
        for k in range(n_arcos + 1):
            f.caja(x, x + pil, h0, h1, -nucleo, 0.0, "muro", BLANCO)
            f.caja(x - 0.03, x + pil + 0.03, arr - 0.15, arr, -nucleo, 0.06, "moldura", MOLD)         # impostas
            if k < n_arcos:
                cs = x + pil + r
                _enjuta(f, cs, r, arr, h1, -nucleo, 0.0, "muro", BLANCO)
                f.arco(cs, r - 0.02, 0.12, arr, -nucleo, 0.04, "moldura", MOLD, segmentos=10)
                q = f.punto(cs, arr + r * 0.3, -nucleo / 2 - 0.05)
                c.cilindro(q.x, q.y, q.z - campana_r * 1.5, q.z, campana_r, "metal", "#6b5a3a", lados=10,
                           radio_arriba=campana_r * 0.5)
                c.caja(q.x - 0.03, q.y - 0.03, q.z, q.x + 0.03, q.y + 0.03, ZA + h1 - 0.2, "madera", "#3a2a1e")
                x = cs + r
        # filetes rosados en las esquinas
        for xx in (0.12, W - 0.2):
            f.caja(xx, xx + 0.08, h0 + 0.1, h1 - 0.1, 0.0, 0.015, "pintura_acento", ROSA)


def torre(c):
    s0, s1, d0 = TORRE
    d1 = fondo(s1) - 0.0
    d1 = max(fondo(s0), fondo(s1))
    # fuste
    c.prisma(quad(s0, s1, d0, d1), ZA - 0.6, ZA + 10.7, "muro", BLANCO)
    for f in caras(c, s0, s1, d0, d1, ZA):
        W = f.largo
        for xx in (0.25, W - 0.33):
            f.caja(xx, xx + 0.08, 0.3, 10.2, 0.0, 0.015, "pintura_acento", ROSA)
        f.caja(0.25, W - 0.25, 10.2, 10.28, 0.0, 0.015, "pintura_acento", ROSA)
        f.caja(-0.1, W + 0.1, 10.5, 10.75, 0.0, 0.18, "moldura", MOLD)
        f.caja(-0.2, W + 0.2, 10.75, 11.0, 0.0, 0.3, "moldura", MOLD)
    for f in caras(c, s0, s1, d0, d1, ZA)[:2]:                                       # ventanita del fuste
        W = f.largo
        f.caja(W / 2 - 0.3, W / 2 + 0.3, 7.2, 8.2, 0.0, 0.02, "vidrio", "#2e3236")
        f.caja(W / 2 - 0.42, W / 2 + 0.42, 8.2, 8.34, 0.0, 0.1, "moldura", MOLD)
    # cuerpo de campanas (dos arcos por cara)
    e = 0.3
    cuerpo_campanas(c, s0 + e, s1 - e, d0 - e, d1 + e, 11.0, 15.0, 2, 1.0, 0.36)
    for f in caras(c, s0 + e, s1 - e, d0 - e, d1 + e, ZA):
        W = f.largo
        f.caja(-0.1, W + 0.1, 15.0, 15.3, 0.0, 0.22, "moldura", MOLD)
        f.caja(-0.22, W + 0.22, 15.3, 15.5, 0.0, 0.36, "moldura", MOLD)
    for s_, d_ in ((s0 + e + 0.1, d0 - e - 0.1), (s1 - e - 0.1, d0 - e - 0.1), (s0 + e + 0.1, d1 + e + 0.1),
                   (s1 - e - 0.1, d1 + e + 0.1)):
        x, y = P(s_, d_)
        pinaculo(c, x, y, ZA + 15.5, base=0.42, alto=1.0)
    # segundo cuerpo (un arco por cara)
    e2 = 1.05
    cuerpo_campanas(c, s0 + e2, s1 - e2, d0 - e2, d1 + e2, 15.5, 18.5, 1, 0.85, 0.26, nucleo=0.5)
    for f in caras(c, s0 + e2, s1 - e2, d0 - e2, d1 + e2, ZA):
        W = f.largo
        f.caja(-0.1, W + 0.1, 18.5, 18.75, 0.0, 0.2, "moldura", MOLD)
        f.caja(-0.18, W + 0.18, 18.75, 18.9, 0.0, 0.3, "moldura", MOLD)
    # linterna con óculos, cupulín y pararrayos
    e3 = 1.55
    c.prisma(quad(s0 + e3, s1 - e3, d0 - e3, d1 + e3), ZA + 18.9, ZA + 20.2, "muro", BLANCO)
    for f in caras(c, s0 + e3, s1 - e3, d0 - e3, d1 + e3, ZA):
        disco(f, f.largo / 2, 19.55, 0.0, 0.28, "madera", "#2a2622")
        f.caja(-0.08, f.largo + 0.08, 20.2, 20.4, 0.0, 0.15, "moldura", MOLD)
    sm, dmid = (s0 + s1) / 2, (d0 + d1) / 2
    x, y = P(sm, dmid)
    zc = ZA + 20.4
    for j in range(5):
        t0, t1 = j / 5, (j + 1) / 5
        c.cilindro(x, y, zc + 1.0 * math.sin(t0 * math.pi / 2), zc + 1.0 * math.sin(t1 * math.pi / 2),
                   1.05 * math.cos(t0 * math.pi / 2) + 0.05, "muro", BLANCO, lados=10,
                   radio_arriba=1.05 * math.cos(t1 * math.pi / 2) + 0.05)
    c.cilindro(x, y, zc + 1.0, zc + 1.4, 0.18, "muro", BLANCO, lados=8)
    c.esfera(x, y, zc + 1.55, 0.17, "muro", BLANCO, segmentos=8)
    c.cilindro(x, y, zc + 1.7, zc + 3.4, 0.03, "hierro", HIERRO, lados=4)


# ------------------------------------------------------------------------------------------------ 4. atrio
G0, G1 = 54.3, 56.3                       # vano del portón
PILARES = [(S_ATRIO, 50.0), (51.0, 51.9), (58.55, S_CAFE)]
PORTON = [(53.4, G0), (G1, 57.2)]
REJAS = [(50.0, 51.0), (51.9, 53.4), (57.2, 58.55)]


def atrio(c):
    # piso de losas pardas
    for s_a, s_b, d_a, d_b in ((S_ATRIO, S_CAFE, DF - 0.42, TORRE[2]), (TORRE[1], S_CAFE, TORRE[2], -16.42)):
        c.prisma(quad(s_a, s_b, d_a, d_b), ZA - 0.8, ZA, "adoquin", LOSA)
    for k in range(int((S_CAFE - S_ATRIO) / 0.9)):                                 # juntas de losas
        s = S_ATRIO + 0.9 * (k + 1)
        c.prisma(quad(s - 0.02, s + 0.02, DF - 0.45, TORRE[2] if s < TORRE[1] else -16.4), ZA, ZA + 0.006,
                 "adoquin", "#7d6852")
    # muro de sillares hacia la calle (fuera del vano del portón)
    f = fach(c, 0.0, DF - 0.4, S_CAFE, DF - 0.4, N)                                   # s global; suelo 0: h absoluta
    for a, b in ((S_ATRIO, G0), (G1, S_CAFE)):
        f.caja(a, b, zv(a) - 0.5, WT, 0.0, 0.4, "zocalo_piedra", PARDO[0])
        sillares(mover(f, 0.4), a, b, zv(b), WT - 0.04, 0.0, alto=0.42, largo=(0.55, 1.0), colores=PARDO,
                 rojo=0.12, semilla=int(a * 3))
        f.caja(a - 0.02, b + 0.02, WT - 0.04, WT + 0.08, -0.05, 0.47, "piedra", "#b59a7e")
    for a, b in REJAS:
        reja_lanzas(f, a, b, WT + 0.08, WT + 1.85, d=0.2)
    # pilares de sillar con remate piramidal
    for a, b in PILARES:
        f.caja(a, b, zv(a) - 0.5, WT + 2.0, -0.25, 0.48, "zocalo_piedra", PILAR)
        sillares(mover(f, 0.48), a, b, zv(b), WT + 1.95, 0.0, alto=0.45, largo=(0.4, 0.5), colores=PARDO, rojo=0.1,
                 semilla=int(a * 7))
        f.caja(a - 0.06, b + 0.06, WT + 2.0, WT + 2.15, -0.31, 0.54, "piedra", "#c1a487")
        q = f.punto((a + b) / 2, WT + 2.15, 0.12)
        c.cilindro(q.x, q.y, q.z, q.z + 0.65, 0.3, "piedra", PILAR, lados=4, radio_arriba=0.03)
    # pilares del portón: abajo sillar ocre, arriba blanco con juntas, cornisa y remate
    for a, b in PORTON:
        f.caja(a, b, zv(a) - 0.5, WT + 0.25, -0.3, 0.52, "zocalo_piedra", "#b49572")
        sillares(mover(f, 0.52), a, b, zv(b), WT + 0.22, 0.0, alto=0.42, largo=(0.42, 0.48), colores=PARDO,
                 rojo=0.1, semilla=int(a * 5))
        f.caja(a, b, WT + 0.25, WT + 3.0, -0.3, 0.5, "piedra", "#ebe6dc")
        for k in range(6):                                                         # juntas
            hh = WT + 0.25 + 0.46 * (k + 1)
            f.caja(a - 0.005, b + 0.005, hh - 0.02, hh, -0.305, 0.505, "piedra", "#bdb5a6")
        f.caja(a - 0.08, b + 0.08, WT + 3.0, WT + 3.18, -0.38, 0.58, "piedra", "#d9d1c2")
        f.caja(a - 0.02, b + 0.02, WT + 3.18, WT + 3.36, -0.32, 0.52, "piedra", "#cfc6b6")
        q = f.punto((a + b) / 2, WT + 3.36, 0.1)
        c.cilindro(q.x, q.y, q.z, q.z + 0.75, 0.42, "piedra", "#c9a888", lados=4, radio_arriba=0.12)
        c.esfera(q.x, q.y, q.z + 0.82, 0.12, "piedra", "#c9a888", segmentos=6)
    # gradas del portón
    z_vp = zv((G0 + G1) / 2)
    paso = (ZA - z_vp) / 3
    for k, (da, db) in enumerate(((DF + 0.15, DF - 0.25), (DF - 0.25, DF - 0.6))):
        c.prisma(quad(G0, G1, da, db), z_vp - 0.4, z_vp + paso * (k + 1), "piedra", "#a99178")
    # reja del portón: dos hojas abiertas contra los pilares, arco de volutas y cruz
    fg = fach(c, G0, DF - 0.4, G1, DF - 0.4, N)
    luz = G1 - G0
    for s_h, signo in ((0.0, 1), (luz, -1)):
        fh = fach(c, G0 + s_h, DF - 0.45, G0 + s_h, DF - 0.45 - luz / 2, U if signo > 0 else NU)
        L = luz / 2
        for hh in (ZA + 0.1, ZA + 1.0, ZA + 2.1):
            fh.caja(0.0, L, hh - 0.025, hh + 0.025, -0.02, 0.02, "hierro", HIERRO)
        for k in range(8):
            x = L * k / 7
            fh.caja(x - 0.012, x + 0.012, ZA + 0.05, ZA + 2.2, -0.012, 0.012, "hierro", HIERRO)
    r = luz / 2
    arr = WT + 2.45
    fg.arco(r, r - 0.04, 0.06, arr, 0.18, 0.22, "hierro", HIERRO, segmentos=14)
    fg.arco(r, r - 0.42, 0.04, arr, 0.18, 0.22, "hierro", HIERRO, segmentos=12)
    for k in range(5):                                                             # volutas del arco
        a = math.pi * (k + 0.5) / 5
        cs, ch = r - math.cos(a) * (r - 0.22), arr + math.sin(a) * (r - 0.22)
        for j in range(8):
            a0, a1 = 2 * math.pi * j / 8, 2 * math.pi * (j + 1) / 8
            tubo(c, fg.punto(cs + 0.13 * math.cos(a0), ch + 0.13 * math.sin(a0), 0.2),
                 fg.punto(cs + 0.13 * math.cos(a1), ch + 0.13 * math.sin(a1), 0.2), 0.01, "hierro", HIERRO)
    fg.caja(0.0, luz, arr - 0.03, arr + 0.03, 0.18, 0.22, "hierro", HIERRO)
    q = fg.punto(r, arr + r, 0.2)
    c.caja(q.x - 0.025, q.y - 0.025, q.z, q.x + 0.025, q.y + 0.025, q.z + 0.75, "hierro", HIERRO)
    c.caja_ejes((q.x, q.y, q.z + 0.5), (fg.u.x, fg.u.y, 0), (fg.n.x, fg.n.y, 0), (0, 0, 1), 0.45, 0.04, 0.04,
                "hierro", HIERRO)
    # pizarra del Café Mirador San Miguel junto a las gradas
    x, y = P(55.7, DF - 1.3)
    c.caja_ejes((x, y, ZA + 0.55), (U[0], U[1], 0), (N[0], N[1], 0), (0, 0, 1), 0.6, 0.35, 1.1, "letrero", "#2a2826")
    # terraza del café: parapeto con reja a lo largo del costado de la casa, bancos y macetas
    ft = fach(c, 57.25, -11.5, 57.25, DF - 0.42, U, 0.0)
    ft.caja(0.0, ft.largo, ZA - 0.2, ZA + 0.45, -0.3, 0.0, "zocalo_piedra", PARDO[1])
    sillares(ft, 0.0, ft.largo - 0.1, ZA, ZA + 0.42, 0.0, alto=0.42, colores=PARDO, rojo=0.1, semilla=77)
    reja_lanzas(ft, 0.0, ft.largo - 0.1, ZA + 0.45, ZA + 1.6, d=-0.15, paso=0.16)
    for d in (-3.5, -7.5):
        x, y = P(58.55, d)
        c.caja_ejes((x, y, ZA + 0.44), (N[0], N[1], 0), (U[0], U[1], 0), (0, 0, 1), 1.7, 0.42, 0.06, "madera",
                    "#7a4a2c")
        c.caja_ejes((x + U[0] * 0.2, y + U[1] * 0.2, ZA + 0.72), (N[0], N[1], 0), (U[0], U[1], 0), (0, 0, 1), 1.7,
                    0.05, 0.4, "madera", "#7a4a2c")
        for e in (-0.7, 0.7):
            c.caja_ejes((x + N[0] * e, y + N[1] * e, ZA + 0.22), (N[0], N[1], 0), (U[0], U[1], 0), (0, 0, 1), 0.06,
                        0.42, 0.44, "hierro", HIERRO)
    # letrero redondo "Terraza San Miguel" en la reja de la calle (130440)
    disco(fach(c, 0.0, DF + 0.05, S_CAFE, DF + 0.05, N), 57.9, WT + 1.35, 0.0, 0.32, "letrero", "#3a2f28")
    # buganvillas y macetas sobre el muro, por dentro de la reja (130440, 130442)
    for k, s in enumerate((50.5, 52.3, 53.1)):
        x, y = P(s, DF - 1.1)
        matorral(c, x, y, ZA, 1.0 if k else 0.8, 500 + k, alto=2.6 if k == 2 else 1.9)
    for k, s in enumerate((50.3, 50.8, 52.1, 52.7, 57.5, 58.0)):
        x, y = P(s, DF - 0.65)
        maceta(c, x, y, ZA, k)


def fondo_atrio(c):
    """Casa de dos plantas al fondo del atrio, con ventana roja, balcón y la puerta de los souvenirs (130442)."""
    s0, s1 = TORRE[1], S_CAFE
    f = fach(c, s0, -16.2, s1, -16.2, N, ZA)
    W = s1 - s0
    c.prisma([P(s0, -16.2), P(s1, -16.2), P(s1, -16.46), P(s0, -16.46)], ZA - 0.3, ZA + 7.0, "muro", BLANCO)
    zocalo_sillares(f, 0.0, W, 0.6, -0.3, semilla=91)
    sm = W / 2 + 0.4
    f.caja(sm - 0.65, sm + 0.65, 0.0, 2.5, 0.0, 0.04, "madera", "#5e2e20")                  # puerta de souvenirs
    f.caja(sm - 0.8, sm + 0.8, 2.6, 2.95, 0.0, 0.06, "letrero", "#3b3330")
    f.caja(sm - 0.65, sm + 0.65, 3.9, 6.0, 0.0, 0.04, "marco_ventana", ROJO)                  # ventana roja
    f.caja(sm - 0.5, sm + 0.5, 4.05, 5.85, 0.04, 0.05, "vidrio", "#3b3f44")
    f.caja(sm - 0.9, sm + 0.9, 3.7, 3.85, 0.0, 0.5, "piedra", "#d9d3c8")
    for hh in (3.85, 4.75):
        f.caja(sm - 0.9, sm + 0.9, hh, hh + 0.04, 0.44, 0.48, "hierro", HIERRO)
    for k in range(10):
        x = sm - 0.85 + 1.7 * k / 9
        f.caja(x - 0.01, x + 0.01, 3.85, 4.75, 0.44, 0.47, "hierro", HIERRO)
    for x in (1.0, W - 0.9):
        f.caja(x - 0.45, x + 0.45, 1.1, 2.4, 0.0, 0.04, "marco_ventana", ROJO)
        f.caja(x - 0.35, x + 0.35, 1.2, 2.3, 0.04, 0.05, "vidrio", "#3b3f44")
    alero_canes(f, 0.0, W, 7.0, 0.7)
    t = math.tan(math.radians(24))
    c.poligono([(*P(s0, -16.2 + 0.7), ZA + 7.0 - 0.12), (*P(s1, -16.2 + 0.7), ZA + 7.0 - 0.12),
                (*P(s1, -16.46), ZA + 7.0 + 0.96 * t), (*P(s0, -16.46), ZA + 7.0 + 0.96 * t)], "teja", TEJA,
               grosor=0.12, normal_extrusion=(0, 0, 1))


# ------------------------------------------------------------------------------------------------ 5. casa del café
def casa_cafe(c):
    s0, s1, d0, d1 = S_CAFE, S_FIN, DF, -16.4
    z0 = Z_CAFE
    ze = z0 + 7.45
    c.prisma(quad(s0, s1, d0, d1), z0 - 0.8, ze, "muro", BLANCO)
    cuatro_aguas(c, s0, s1, d0, d1, ze, (0.75, 0.02, 0.8, 0.3))
    # frente a Arenales (130448)
    f = fach(c, s0, d0, s1, d0, N, z0)
    W = s1 - s0
    zocalo_sillares(f, 0.0, W, 1.1, -0.4, semilla=61)
    for k in range(14):                                                           # esquinal de sillares
        hh = 1.1 + k * 0.45
        ancho = 0.55 if k % 2 else 0.38
        f.caja(0.0, ancho, hh + 0.02, hh + 0.43, 0.0, 0.05, "zocalo_piedra", PARDO[k % 5])
    sm = 2.75
    # planta baja: ventana de arco rebajado con marco rojo y reja
    f.caja(sm - 0.95, sm + 0.95, 1.2, 1.32, 0.0, 0.14, "moldura", MOLD)
    f.caja(sm - 0.8, sm + 0.8, 1.32, 3.0, 0.0, 0.02, "vidrio", "#33373b")
    for k in range(7):
        a = math.pi * k / 6
        f.caja(sm - 0.8 * math.cos(a) - 0.14, sm - 0.8 * math.cos(a) + 0.14, 3.0 + 0.28 * math.sin(a) - 0.04,
               3.0 + 0.28 * math.sin(a) + 0.08, 0.0, 0.06, "marco_ventana", ROJO)
    for x in (sm - 0.8, sm - 0.03, sm + 0.74):
        f.caja(x, x + 0.07, 1.32, 3.05, 0.02, 0.06, "marco_ventana", ROJO)
    f.caja(sm - 0.8, sm + 0.8, 2.35, 2.41, 0.02, 0.06, "marco_ventana", ROJO)
    for k in range(6):
        x = sm - 0.7 + 1.4 * k / 5
        f.caja(x - 0.012, x + 0.012, 1.35, 2.95, 0.08, 0.1, "hierro", HIERRO)
    for hh in (1.9, 2.5):
        f.caja(sm - 0.78, sm + 0.78, hh - 0.012, hh + 0.012, 0.08, 0.1, "hierro", HIERRO)
    # planta alta: puerta-ventana roja con balcón de hierro sobre losa con ménsulas de volutas
    f.caja(sm - 0.72, sm + 0.72, 4.3, 6.85, 0.0, 0.02, "vidrio", "#e9e2d4")
    for x in (sm - 0.72, sm - 0.04, sm + 0.64):
        f.caja(x, x + 0.08, 4.3, 6.9, 0.02, 0.06, "marco_ventana", ROJO)
    for hh in (4.3, 5.5, 6.82):
        f.caja(sm - 0.72, sm + 0.72, hh, hh + 0.08, 0.02, 0.06, "marco_ventana", ROJO)
    f.caja(sm - 1.05, sm + 1.05, 4.1, 4.3, 0.0, 0.62, "piedra", "#e2ddd3")
    for x in (sm - 0.85, sm - 0.28, sm + 0.28, sm + 0.85):
        tubo(c, f.punto(x, 3.6, 0.02), f.punto(x, 4.08, 0.55), 0.025, "hierro", HIERRO)
        tubo(c, f.punto(x, 3.6, 0.02), f.punto(x, 3.75, 0.2), 0.03, "hierro", HIERRO)
    for hh in (4.33, 5.3):
        f.caja(sm - 1.0, sm + 1.0, hh, hh + 0.04, 0.54, 0.58, "hierro", HIERRO)
    for x in (sm - 1.0, sm + 0.96):
        f.caja(x, x + 0.04, 4.3, 5.34, 0.0, 0.58, "hierro", HIERRO)
    for k in range(12):
        x = sm - 0.95 + 1.9 * k / 11
        f.caja(x - 0.01, x + 0.01, 4.3, 5.3, 0.54, 0.57, "hierro", HIERRO)
    for k, x in enumerate((sm - 0.75, sm - 0.25, sm + 0.25, sm + 0.75)):
        q = f.punto(x, 4.3, 0.36)
        maceta(c, q.x, q.y, q.z, k)
    alero_canes(f, 0.0, W, ze - z0, 0.75)
    # costado al atrio: ventanas rojas arriba, ventanas y puerta de arco abajo (130440, 130445)
    fs = fach(c, s0, d1, s0, d0, NU, ZA)
    zocalo_sillares(fs, 0.0, fs.largo - 0.45, 0.6, -0.3, semilla=67)
    he = ze - ZA
    for x in (1.6, 4.2, 6.8, 9.4, 12.0, 14.6):
        fs.caja(x - 0.55, x + 0.55, 4.2, 5.85, 0.0, 0.02, "vidrio", "#3b3f44")
        for xx in (x - 0.55, x - 0.03, x + 0.49):
            fs.caja(xx, xx + 0.06, 4.2, 5.85, 0.02, 0.06, "marco_ventana", ROJO)
        for hh in (4.2, 5.2, 5.79):
            fs.caja(x - 0.55, x + 0.55, hh, hh + 0.06, 0.02, 0.06, "marco_ventana", ROJO)
        fs.caja(x - 0.68, x + 0.68, 4.08, 4.2, 0.0, 0.12, "moldura", MOLD)
    for x, tipo in ((14.3, "arco"), (11.6, "ventana"), (8.8, "puerta"), (6.0, "ventana"), (3.2, "ventana")):
        if tipo == "puerta":
            fs.caja(x - 0.6, x + 0.6, 0.0, 2.3, 0.0, 0.04, "marco_ventana", ROJO)
            fs.timpano_arco(x, 0.6, 2.3, 0.04, "marco_ventana", ROJO)
            fs.arco(x, 0.6, 0.12, 2.3, 0.0, 0.06, "moldura", MOLD)
        else:
            arco = tipo == "arco"
            ventana(fs, x, 0.95, ancho=1.1, alto=1.75 if arco else 1.55, arco=arco, reja=True,
                    color_moldura=MOLD, color_carpinteria=ROJO)
    alero_canes(fs, 0.0, fs.largo, he, 0.75)


# ------------------------------------------------------------------------------------------------ 6. faroles
def faroles(c):
    for s in (53.0, 61.2):
        x, y = al_bordillo("Calle José Álvarez de Arenales", *P(s, DF + 2.95 - 0.45))
        farol_cuello(c, x, y, zv(s, DF + 2.5), N[0], N[1])


if __name__ == "__main__":
    m, col = iniciar(AGENTE, MID)
    c = Constructor("SAN_MIGUEL_templo")
    nave(c)
    cc = Constructor("SAN_MIGUEL_cables")
    cables_nave(cc, c)
    cc.objeto(col)
    portada(c)
    torre(c)
    c.objeto(col)
    c = Constructor("SAN_MIGUEL_atrio")
    atrio(c)
    fondo_atrio(c)
    c.objeto(col)
    c = Constructor("SAN_MIGUEL_casa_cafe")
    casa_cafe(c)
    c.objeto(col)
    c = Constructor("SAN_MIGUEL_postes_faroles")
    faroles(c)
    c.objeto(col)
    exportar(AGENTE, MID)
