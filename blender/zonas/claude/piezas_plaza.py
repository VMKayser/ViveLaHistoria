"""Piezas hechas a mano del interior de la Plaza 25 de Mayo (fotos de las correcciones R0151–R0159).

Cada función arma UNA cosa de la plaza tal como se ve en las fotos y devuelve el Constructor (el que llama la vuelve
objeto). Nada se reparte al azar: las posiciones las decide `retocar_p01.py`, mirando las fotos.
Orientación local: (ux, uy) es el eje "adelante"; (-uy, ux) es el eje "izquierda".
"""
import math
import random

from mathutils import Vector

from kit import Constructor
from kit.datos import altura_suelo

HIERRO = "#2a2d2b"          # forja negra verdosa de rejas y faroles
ORO = "#c9a24a"             # anillos dorados de los faroles
ARENISCA = "#a98a6c"        # arenisca parda de los quioscos y fuentes (R0133, R0136)
PIEDRA_MON = "#b39a7b"      # sillería del monumento
BRONCE = "#5a3b25"
CAL = "#f4f1ea"
PIZARRA = "#2b2f36"


def _ejes(ux, uy):
    return (ux, uy, 0.0), (-uy, ux, 0.0), (0.0, 0.0, 1.0)


def caja_local(c, x, y, z0, z1, ux, uy, sx, sy, rol, color=None, dx=0.0, dy=0.0):
    """Caja de lados sx (adelante) × sy (izquierda), centrada en (x,y)+(dx adelante, dy izquierda)."""
    ex, ey, ez = _ejes(ux, uy)
    cx, cy = x + ux * dx - uy * dy, y + uy * dx + ux * dy
    c.caja_ejes((cx, cy, (z0 + z1) / 2), ex, ey, ez, sx, sy, z1 - z0, rol, color)


def tronco_piramide(c, x, y, z0, z1, w0, w1, ux, uy, rol, color=None):
    """Tronco de pirámide cuadrada (fuste del monumento): base w0, tope w1, alineado a (ux, uy)."""
    def esq(z, w):
        h = w / 2
        return [(x + ux * a - uy * b, y + uy * a + ux * b, z) for a, b in ((h, h), (-h, h), (-h, -h), (h, -h))]
    ab, ar = esq(z0, w0), esq(z1, w1)
    for i in range(4):
        j = (i + 1) % 4
        c.poligono([ab[i], ab[j], ar[j], ar[i]], rol, color)
    c.poligono(list(reversed(ab)), rol, color)
    c.poligono(ar, rol, color)


def elipse_plana(c, x, y, z, rx, ry, rol, color=None, ux=1.0, uy=0.0, n=20, a0=0.0, a1=math.tau, altura=None):
    """Elipse horizontal (parche de flores, escudo): abanico de triángulos visto desde arriba.
    altura: función (x, y) → z del suelo; si se da, la elipse se apoya sobre él vértice por vértice y z es el despegue."""
    pts = []
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        px, py = rx * math.cos(a), ry * math.sin(a)
        pts.append((x + ux * px - uy * py, y + uy * px + ux * py))
    zz = (lambda px, py: altura(px, py) + z) if altura else (lambda px, py: z)
    for p, q in zip(pts, pts[1:]):
        c.poligono([(x, y, zz(x, y)), (p[0], p[1], zz(*p)), (q[0], q[1], zz(*q))], rol, color)


def anillo_plano(c, x, y, z, r0, r1, rol, color=None, n=48, suelo=True):
    """Corona horizontal entre r0 y r1 que sigue el terreno (borde de piedra del óvalo de pizarra)."""
    def pt(r, a):
        px, py = x + r * math.cos(a), y + r * math.sin(a)
        return (px, py, (altura_suelo(px, py) + z) if suelo else z)
    for k in range(n):
        a, b = math.tau * k / n, math.tau * (k + 1) / n
        c.poligono([pt(r0, a), pt(r1, a), pt(r1, b), pt(r0, b)], rol, color)


def disco_suelo(c, x, y, z, r, rol, color=None, n=40):
    for k in range(n):
        a, b = math.tau * k / n, math.tau * (k + 1) / n
        pts = [(x, y), (x + r * math.cos(a), y + r * math.sin(a)), (x + r * math.cos(b), y + r * math.sin(b))]
        c.poligono([(px, py, altura_suelo(px, py) + z) for px, py in pts], rol, color)


# --------------------------------------------------------------------------- monumento a Sucre (R0151)
def leon(c, x, y, z, ux, uy):
    """León de bronce echado (mira hacia (ux, uy)): cuerpo, grupa, pecho, cabeza con melena, patas y cola."""
    caja_local(c, x, y, z + .05, z + .62, ux, uy, 1.25, .56, "metal", BRONCE, dx=-.2)             # cuerpo
    caja_local(c, x, y, z + .05, z + .5, ux, uy, .5, .62, "metal", BRONCE, dx=-.72)                # grupa
    caja_local(c, x, y, z + .2, z + .98, ux, uy, .46, .6, "metal", BRONCE, dx=.28)                 # pecho erguido
    caja_local(c, x, y, z + .55, z + 1.18, ux, uy, .5, .66, "metal", "#3f2a1a", dx=.42)           # melena
    caja_local(c, x, y, z + .55, z + .95, ux, uy, .3, .34, "metal", "#6a4630", dx=.72)            # hocico y rostro
    for s in (-.2, .2):
        caja_local(c, x, y, z + .05, z + .22, ux, uy, .62, .13, "metal", BRONCE, dx=.62, dy=s)      # patas delanteras
    caja_local(c, x, y, z + .05, z + .2, ux, uy, .5, .12, "metal", BRONCE, dx=-.92, dy=.4)         # cola
    caja_local(c, x, y, z - .02, z + .08, ux, uy, 1.9, .95, "metal", "#3a2a1c", dx=-.1)           # plancha de bronce


def escudo_cara(c, x, y, z, ux, uy, ancho, alto, ox, oy):
    """Escudo de armas en corona de laurel, aplicado a una cara del fuste (ox,oy es la normal saliente)."""
    ex, ey = -oy, ox
    def p(px, pz, d):
        return (x + ex * px + ox * d, y + ey * px + oy * d, z + pz)
    def anillo(r0x, r0z, r1x, r1z, d, rol, color):
        for k in range(18):
            a, b = math.tau * k / 18, math.tau * (k + 1) / 18
            c.poligono([p(r0x * math.cos(a), r0z * math.sin(a), d), p(r0x * math.cos(b), r0z * math.sin(b), d),
                        p(r1x * math.cos(b), r1z * math.sin(b), d), p(r1x * math.cos(a), r1z * math.sin(a), d)],
                       rol, color)
    anillo(ancho / 2, alto / 2, ancho / 2 * .78, alto / 2 * .8, .08, "metal", "#4a3322")           # laurel oscuro
    anillo(ancho / 2 * .78, alto / 2 * .8, 0.001, 0.001, .1, "metal", "#6b4a2e")                   # campo
    c.poligono([p(-ancho * .22, alto * .26, .12), p(ancho * .22, alto * .26, .12), p(ancho * .2, -alto * .12, .12),
                p(0, -alto * .3, .12), p(-ancho * .2, -alto * .12, .12)], "metal", "#4a3322")         # escudo


def monumento_sucre(c, x, y, z, ux, uy, fuera):
    """Monumento a Sucre (R0145/R0149/R0151): tambor redondo escalonado, fuste en pirámide con escudo y placas, y dos leones de
    bronce reales (modelo CC0) echados sobre plintos al norte y al sur, mirando hacia afuera, con la misma pose."""
    # gradas redondas
    for r, h0, h1, col in ((6.5, 0, .2, "#a88f70"), (5.8, .2, .42, "#b39a7b"), (5.1, .42, .64, "#a88f70"), (4.6, .64, .8, "#c1a888")):
        c.cilindro(x, y, z + h0, z + h1, r, "piedra", col, lados=16)
    # plintos de los leones (norte y sur): bloque de sillería con moldura y plancha de bronce
    for sgn in (1, -1):
        py = y + sgn * 5.0
        c.caja(x - 1.3, py - 1.35, z + .2, x + 1.3, py + 1.35, z + 1.08, "piedra", "#b39a7b")
        c.caja(x - 1.42, py - 1.47, z + 1.08, x + 1.42, py + 1.47, z + 1.2, "piedra", "#c1a888")
        c.caja(x - 1.15, py - 1.2, z + 1.2, x + 1.15, py + 1.2, z + 1.27, "metal", "#4a3322")
        fuera.append(("leon_bronce", x, py, z + 1.27, math.pi / 2 * sgn, .8))
    # tambor y cornisa
    c.cilindro(x, y, z + .8, z + 3.1, 3.75, "piedra", "#b39a7b", lados=16, radio_arriba=3.55)
    c.cilindro(x, y, z + 3.1, z + 3.35, 3.95, "piedra", "#c1a888", lados=16)
    c.cilindro(x, y, z + 3.35, z + 3.55, 3.2, "piedra", "#b39a7b", lados=16)
    tronco_piramide(c, x, y, z + 3.55, z + 4.6, 3.0, 2.6, ux, uy, "piedra", "#b8a07f")
    caja_local(c, x, y, z + 4.6, z + 4.8, ux, uy, 3.0, 3.0, "piedra", "#c9b392")
    # fuste en pirámide de sillería parda, con hiladas y cornisas (R0147: más alto que antes, ~19 m hasta la cabeza)
    top, h_top = 1.75, 15.2
    w0 = 2.6
    tronco_piramide(c, x, y, z + 4.8, z + h_top, w0, top, ux, uy, "piedra", "#a08a6c")

    def ancho(h):
        return w0 - (w0 - top) * (h - 4.8) / (h_top - 4.8)
    for h in (5.1, 14.3):                                           # cornisas: arranque del fuste y bajo el remate
        caja_local(c, x, y, z + h, z + h + .22, ux, uy, ancho(h) + .26, ancho(h) + .26, "piedra", "#b49c7c")
    for k in range(1, 15):                                          # hiladas de sillería cada ~0,65 m
        h = 5.4 + k * .62
        if h > 14.1:
            break
        caja_local(c, x, y, z + h, z + h + .04, ux, uy, ancho(h) + .05, ancho(h) + .05, "piedra", "#8a7458")
    for k in range(4):
        ang = k * math.pi / 2
        ox, oy = ux * math.cos(ang) - uy * math.sin(ang), uy * math.cos(ang) + ux * math.sin(ang)
        escudo_cara(c, x + ox * ancho(10.6) / 2, y + oy * ancho(10.6) / 2, z + 10.6, ux, uy, 1.15, 1.5, ox, oy)   # escudo de bronce
        ex_, ey_ = -oy, ox                                          # placa de bronce en el arranque
        pc = ancho(6.6) / 2 + .03
        c.caja_ejes((x + ox * pc, y + oy * pc, z + 6.6), (ox, oy, 0), (ex_, ey_, 0), (0, 0, 1), .05, 1.1, .75, "metal", "#4a3322")
    # remate (cornisa con gola) y base de la estatua
    caja_local(c, x, y, z + h_top, z + h_top + .25, ux, uy, 2.35, 2.35, "piedra", "#b49c7c")
    caja_local(c, x, y, z + h_top + .25, z + h_top + .5, ux, uy, 2.05, 2.05, "piedra", "#a08a6c")
    caja_local(c, x, y, z + h_top + .5, z + h_top + 1.5, ux, uy, 1.3, 1.3, "piedra", "#a08a6c")
    caja_local(c, x, y, z + h_top + 1.5, z + h_top + 1.65, ux, uy, 1.6, 1.6, "piedra", "#b49c7c")
    fuera.append(("estatua", x, y, z + h_top + 1.65, math.atan2(uy, ux) + math.pi / 4, 1.25))   # figura de pie real (CC0), ver preparar_estatua.py


def figura_bronce(c, x, y, z, ux, uy, alto):
    """Estatua de bronce de pie: botas, piernas, levita, brazo, cabeza y sombrero (silueta de la foto)."""
    k = alto / 3.2
    caja_local(c, x, y, z, z + .1, ux, uy, .8 * k, .6 * k, "metal", "#3a2a1c")
    caja_local(c, x, y, z + .1, z + 1.1 * k, ux, uy, .5 * k, .5 * k, "metal", BRONCE)
    caja_local(c, x, y, z + 1.1 * k, z + 2.2 * k, ux, uy, .7 * k, .56 * k, "metal", BRONCE)
    caja_local(c, x, y, z + 1.6 * k, z + 2.1 * k, ux, uy, .26 * k, .2 * k, "metal", BRONCE, dy=.42 * k)
    caja_local(c, x, y, z + 2.2 * k, z + 2.62 * k, ux, uy, .42 * k, .4 * k, "metal", "#6a4630")
    caja_local(c, x, y, z + 2.62 * k, z + 2.74 * k, ux, uy, .62 * k, .62 * k, "metal", "#3a2a1c")
    caja_local(c, x, y, z + 2.74 * k, z + 3.0 * k, ux, uy, .36 * k, .36 * k, "metal", "#3a2a1c")


def busto_pedestal(c, x, y, z, ux, uy, fuera):
    """Pedestal de sillería con busto (monumentos menores de las esquinas, R0159)."""
    caja_local(c, x, y, z, z + .3, ux, uy, 2.0, 2.0, "piedra", "#a88f70")
    caja_local(c, x, y, z + .3, z + .55, ux, uy, 1.6, 1.6, "piedra", "#b39a7b")
    tronco_piramide(c, x, y, z + .55, z + 2.7, 1.1, .85, ux, uy, "piedra", "#c1a888")
    caja_local(c, x, y, z + 2.7, z + 2.9, ux, uy, 1.15, 1.15, "piedra", "#b39a7b")
    fuera.append(("busto", x, y, z + 2.9, math.atan2(uy, ux) + math.pi / 2, 1.2))


# --------------------------------------------------------------------------- quiosco de arenisca (R0157/R0156/R0159)
def quiosco(c, x, y, z, rumbo):
    """Quiosco octogonal de arenisca parda con cubierta piramidal de escamas rojas y puertas de madera."""
    n = 8
    R = 1.75                                    # radio al vértice del octógono del cuerpo
    cos22 = math.cos(math.pi / n)

    def vert(r, z_, k):
        a = rumbo + math.pi / n + k * math.tau / n
        return (x + r * math.cos(a), y + r * math.sin(a), z_)

    def prisma(r0, r1, z0, z1, color):
        for k in range(n):
            j = (k + 1) % n
            c.poligono([vert(r0, z0, k), vert(r0, z0, j), vert(r1, z1, j), vert(r1, z1, k)], "piedra", color)

    def tapa(r, z_, color, bajar=False):
        pts = [vert(r, z_, k) for k in range(n)]
        c.poligono(list(reversed(pts)) if bajar else pts, "piedra", color)

    # basamento escalonado y zócalo con tableros
    prisma(2.55, 2.55, z, z + .22, "#977a5e")
    tapa(2.55, z + .22, "#a88a6d")
    prisma(2.2, 2.2, z + .22, z + .95, ARENISCA)
    tapa(2.2, z + .95, "#b49676")
    prisma(2.05, 2.05, z + .95, z + 1.05, "#b89a7a")
    # cuerpo
    prisma(R * 1.1, R * 1.1, z + 1.05, z + 3.35, ARENISCA)
    # cornisa volada y friso
    prisma(R * 1.12, R * 1.12, z + 3.35, z + 3.55, "#b09272")
    prisma(R * 1.28, R * 1.28, z + 3.55, z + 3.72, "#b89a7a")
    tapa(R * 1.28, z + 3.72, "#a88a6d")
    # cubierta: pirámide octogonal de escamas (teja rojiza) con cumbrera
    for k in range(n):
        j = (k + 1) % n
        base1 = vert(R * 1.2, z + 3.72, k), vert(R * 1.2, z + 3.72, j)
        medio = vert(R * .72, z + 4.35, k), vert(R * .72, z + 4.35, j)
        tope = vert(R * .16, z + 5.15, k), vert(R * .16, z + 5.15, j)
        c.poligono([base1[0], base1[1], medio[1], medio[0]], "teja", "#a94a3c")
        c.poligono([medio[0], medio[1], tope[1], tope[0]], "teja", "#9a4034")
    c.poligono([vert(R * .16, z + 5.15, k) for k in range(n)], "teja", "#9a4034")
    c.cilindro(x, y, z + 5.1, z + 5.5, .1, "piedra", "#977a5e", lados=6, radio_arriba=.04)
    # puertas de madera con marco de piedra en 5 de las 8 caras (las otras: paño ciego con tablero)
    ap = R * 1.1 * cos22
    for k in range(n):
        a = rumbo + k * math.tau / n
        ox, oy = math.cos(a), math.sin(a)
        ex, ey = -oy, ox
        pcx, pcy = x + ox * ap, y + oy * ap
        ancho = 2 * R * 1.1 * math.sin(math.pi / n) * .62
        for sgn in (-1, 1):                                                  # pilastras de esquina
            c.caja_ejes((x + ox * (ap + .02) + ex * sgn * ancho * .62, y + oy * (ap + .02) + ey * sgn * ancho * .62,
                         z + 2.2), (ox, oy, 0), (ex, ey, 0), (0, 0, 1), .08, .16, 2.3, "piedra", "#b89a7a")
        if k % 2 == 0:
            for sgn in (-.5, .5):                                            # dos hojas de madera
                c.caja_ejes((pcx + ox * .04 + ex * sgn * ancho * .5, pcy + oy * .04 + ey * sgn * ancho * .5, z + 2.1),
                            (ox, oy, 0), (ex, ey, 0), (0, 0, 1), .07, ancho * .46, 2.0, "madera", "#4e2c20")
            c.caja_ejes((pcx + ox * .03, pcy + oy * .03, z + 3.18), (ox, oy, 0), (ex, ey, 0), (0, 0, 1),
                        .08, ancho * 1.02, .14, "piedra", "#b89a7a")           # dintel
        else:
            c.caja_ejes((pcx + ox * .03, pcy + oy * .03, z + 2.15), (ox, oy, 0), (ex, ey, 0), (0, 0, 1),
                        .05, ancho * .9, 1.7, "piedra", "#977a5e")             # tablero hundido


# --------------------------------------------------------------------------- faroles (R0152, R0159)
def farol(c, x, y, z, ux, uy, doble=False, alto=4.6):
    """Farol de la plaza: base acampanada con anillo dorado, fuste negro con aros dorados y brazo(s) con luminaria."""
    c.cilindro(x, y, z, z + .16, .36, "hierro", HIERRO, lados=8)
    c.cilindro(x, y, z + .16, z + .62, .27, "hierro", HIERRO, lados=8, radio_arriba=.15)
    c.cilindro(x, y, z + .12, z + .2, .38, "metal", ORO, lados=8)
    c.cilindro(x, y, z + .62, z + alto, .085, "hierro", HIERRO, lados=6, radio_arriba=.06)
    for h in (.95, 1.9):
        c.cilindro(x, y, z + h, z + h + .08, .13, "metal", ORO, lados=6)
    lados = (1, -1) if doble else (1,)
    for s in lados:
        # brazo curvo: tres tramos hasta la luminaria
        pts = [(0, alto - .1), (.14 * s, alto + .22), (.4 * s, alto + .38), (.7 * s, alto + .3)]
        for (a0, h0), (a1, h1) in zip(pts, pts[1:]):
            _barra(c, (x - uy * a0, y + ux * a0, z + h0), (x - uy * a1, y + ux * a1, z + h1), .03, "hierro", HIERRO)
        lx, ly, lz = x - uy * .72 * s, y + ux * .72 * s, z + alto + .22
        c.cilindro(lx, ly, lz, lz + .1, .08, "hierro", HIERRO, lados=6)
        c.esfera(lx, ly, lz - .06, .24, "letrero", "#ecebdc", segmentos=8)                       # globo opalino
        c.cilindro(lx, ly, lz + .14, lz + .22, .2, "hierro", HIERRO, lados=8, radio_arriba=.05)  # sombrerete


def _barra(c, p, q, r, rol, color):
    """Cilindro fino entre dos puntos 3D."""
    p, q = Vector(p), Vector(q)
    d = q - p
    L = d.length
    if L < 1e-4:
        return
    ez = d / L
    ex = ez.cross(Vector((0, 0, 1)))
    if ex.length < 1e-3:
        ex = Vector((1, 0, 0))
    ex.normalize()
    ey = ez.cross(ex)
    c.caja_ejes(tuple((p + q) / 2), tuple(ex), tuple(ey), tuple(ez), r * 2, r * 2, L, rol, color)


# --------------------------------------------------------------------------- mobiliario
def banco(c, x, y, z, ux, uy):
    """Banco de listones de madera color vino con costados de fundición (como los de las fotos)."""
    madera = "#6f2b2a"
    for k in range(4):
        caja_local(c, x, y, z + .46, z + .5, ux, uy, 1.9, .1, "madera", madera, dy=-.25 + k * .13)
    for k in range(3):
        caja_local(c, x, y, z + .72 + k * .13, z + .78 + k * .13, ux, uy, 1.9, .03, "madera", madera, dy=-.28)
    for s in (-.82, .82):
        caja_local(c, x, y, z, z + .46, ux, uy, .06, .5, "hierro", HIERRO, dx=s)
        caja_local(c, x, y, z + .46, z + 1.02, ux, uy, .06, .06, "hierro", HIERRO, dx=s, dy=-.29)


def papelera(c, x, y, z):
    c.cilindro(x, y, z, z + .95, .3, "hierro", "#232523", lados=10)
    c.cilindro(x, y, z + .5, z + .56, .31, "metal", ORO, lados=10)
    c.cilindro(x, y, z + .95, z + 1.02, .32, "hierro", "#232523", lados=10)


def maceta_pedestal(c, x, y, z, ux, uy):
    """Pedestal de piedra clara con maceta de hojas grandes (entrada de los caminos, R0156/R0159)."""
    tronco_piramide(c, x, y, z, z + .95, .55, .8, ux, uy, "piedra", "#d8d0bd")
    caja_local(c, x, y, z + .95, z + 1.05, ux, uy, .92, .92, "piedra", "#e4dccb")
    c.cilindro(x, y, z + 1.05, z + 1.3, .3, "piedra", "#cbbfa6", lados=8, radio_arriba=.38)
    for k in range(7):
        a = k * math.tau / 7
        c.esfera(x + .22 * math.cos(a), y + .22 * math.sin(a), z + 1.55 + .1 * (k % 3), .22, "follaje_claro",
                 "#7ea53a" if k % 2 else "#93b84a", segmentos=6)


# --------------------------------------------------------------------------- reja forjada baja (R0154)
def reja_forjada(c, a, b, z_a, z_b):
    """Tramo de reja baja de hierro negro entre a y b: barrotes con punta, travesaños y arcos de volutas."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    if L < .15:
        return
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    n = max(1, round(L / .4))
    for i in range(n + 1):
        t = i / n
        px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        z = z_a + (z_b - z_a) * t
        c.cilindro(px, py, z, z + .56, .011, "hierro", HIERRO, lados=3, radio_arriba=.003)        # barrote con punta de lanza
    for h in (.1, .42):
        _barra(c, (a[0], a[1], z_a + h), (b[0], b[1], z_b + h), .008, "hierro", HIERRO)
    # volutas: un arco en "∧" cada tres barrotes
    for i in range(0, n, 3):
        t0, t1 = i / n, min(1.0, (i + 3) / n)
        pa = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0, z_a + (z_b - z_a) * t0 + .1)
        pb = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1, z_a + (z_b - z_a) * t1 + .1)
        pm = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, (pa[2] + pb[2]) / 2 + .27)
        _barra(c, pa, pm, .007, "hierro", HIERRO)
        _barra(c, pm, pb, .007, "hierro", HIERRO)


# --------------------------------------------------------------------------- vegetación
def _copa(c, x, y, z, rx, ry, rz, rol, color, anillos=5, sect=10):
    """Masa de follaje: elipsoide de pocos polígonos."""
    for j in range(anillos):
        a = -math.pi / 2 + j * math.pi / anillos
        b = a + math.pi / anillos
        for k in range(sect):
            u, v = k * math.tau / sect, (k + 1) * math.tau / sect

            def p(t, w):
                return (x + rx * math.cos(t) * math.cos(w), y + ry * math.cos(t) * math.sin(w), z + rz * math.sin(t))
            ps = [p(a, u), p(a, v), p(b, v), p(b, u)]
            if j == 0:
                ps = [ps[0], ps[2], ps[3]]
            if j == anillos - 1:
                ps = [ps[0], ps[1], ps[2]]
            c.poligono(ps, rol, color)


def _rama(c, p, q, r0, r1):
    p, q = Vector(p), Vector(q)
    d = q - p
    L = d.length
    ez = d / L
    ex = ez.cross(Vector((0, 0, 1)))
    if ex.length < 1e-3:
        ex = Vector((1, 0, 0))
    ex.normalize()
    ey = ez.cross(ex)
    c.caja_ejes(tuple((p + q) / 2), tuple(ex), tuple(ey), tuple(ez), (r0 + r1), (r0 + r1), L, "tronco", None)


def base_blanca(c, x, y, z, r, h=1.25):
    c.cilindro(x, y, z - .04, z + h, r * 1.06, "moldura", CAL, lados=8, radio_arriba=r * 1.0)


def arbol_viejo(c, x, y, z, azar, escala=1.0):
    """Árbol grande de plaza (R0152/R0154/R0155): tronco grueso oscuro con pie encalado, 4 ramas abiertas que se bifurcan y copa ancha
    hecha de muchas masas de follaje de distinto tamaño y tono, con huecos de luz entre ellas."""
    # R0137/R0138/R0144: los árboles reales tienen 15–18 m, fuste limpio hasta 5–6 m (a veces inclinado) y una copa alta y
    # abierta que, vista desde los caminos, tapa las fachadas de alrededor de la plaza.
    s = escala
    r = .55 * s
    alto_fuste = azar.uniform(5.0, 6.2) * s
    inc = azar.uniform(0, math.tau)
    lean = azar.uniform(0, .9) * s                                     # inclinación del fuste
    tx, ty = x + math.cos(inc) * lean, y + math.sin(inc) * lean
    c.cilindro(x, y, z, z + 1.5, r, "tronco", "#3a2f26", lados=8, radio_arriba=r * .92)
    _rama(c, (x, y, z + 1.4), (tx, ty, z + alto_fuste), r * .9, r * .62)
    base_blanca(c, x, y, z, r, 1.3)
    ang0 = azar.uniform(0, math.tau)
    verdes = (("follaje", "#3f6128"), ("follaje", "#4a6b2c"), ("follaje_claro", "#628a35"), ("follaje", "#365a26"))
    for i in range(4):
        a = ang0 + i * math.tau / 4 + azar.uniform(-.35, .35)
        ca, sa = math.cos(a), math.sin(a)
        mx, my, mz = tx + ca * 2.4 * s, ty + sa * 2.4 * s, z + alto_fuste + azar.uniform(2.6, 3.6) * s
        _rama(c, (tx, ty, z + alto_fuste - .3), (mx, my, mz), .3 * s, .16 * s)
        for j in (-1, 1):                                              # cada rama se bifurca
            b = a + j * azar.uniform(.45, .8)
            ex, ey, ez = mx + math.cos(b) * 3.0 * s, my + math.sin(b) * 3.0 * s, mz + azar.uniform(1.8, 3.0) * s
            _rama(c, (mx, my, mz), (ex, ey, ez), .16 * s, .07 * s)
            for k in range(2):
                rr = azar.uniform(1.7, 2.5) * s
                col = verdes[(i + j + k) % 4]
                _copa(c, ex + azar.uniform(-1.3, 1.3) * s, ey + azar.uniform(-1.3, 1.3) * s, ez + azar.uniform(0, 1.6) * s,
                      rr * 1.3, rr * 1.2, rr * .8, col[0], col[1], anillos=4, sect=8)
    _copa(c, tx, ty, z + alto_fuste + 8.5 * s, 3.0 * s, 2.9 * s, 1.8 * s, "follaje_claro", "#6f9438", anillos=4, sect=8)


def arbol_viejo_catalogo(c, x, y, z, azar, escala=1.0):
    """[A prueba, no en uso: el usuario prefirió los anteriores (2026-11-23); se volverán a probar.] Árbol grande de la plaza (R0137/R0138/R0144: 15–18 m, copa alta que tapa las fachadas): jacarandá (en flor en
    noviembre), island tree o TwistedTree del catálogo elegido por el usuario, con el pie encalado."""
    from arboles_catalogo import poner
    esp = azar.choice(("jacaranda", "jacaranda", "isla", "isla", "retorcido"))
    poner(c, esp, x, y, z - 0.05, azar.uniform(14.0, 17.0) * escala, semilla=azar.randint(0, 9999), encalado=1.3)


def arbol_podado(c, x, y, z, azar, radio=2.3):
    """Árbol de copa redonda podada, muy densa, con tronco corto y pie encalado (fila del perímetro)."""
    r = .2
    c.cilindro(x, y, z, z + 1.9, r, "tronco", "#4a3b2e", lados=7, radio_arriba=r * .8)
    base_blanca(c, x, y, z, r, 1.0)
    for i in range(3):
        a = azar.uniform(0, math.tau) + i * 2.1
        _rama(c, (x, y, z + 1.6), (x + math.cos(a) * radio * .5, y + math.sin(a) * radio * .5, z + 3.2), .08, .04)
    _copa(c, x, y, z + 3.9, radio, radio, radio * .78, "follaje", "#3f7a33", anillos=6, sect=12)
    _copa(c, x + azar.uniform(-.5, .5), y + azar.uniform(-.5, .5), z + 4.6, radio * .7, radio * .7, radio * .5,
          "follaje_claro", "#5d9440", anillos=4, sect=9)


def arbol_podado_catalogo(c, x, y, z, azar, radio=2.3):
    """[A prueba, no en uso: el usuario prefirió los anteriores (2026-11-23); se volverán a probar.] Árbol podado del perímetro de la plaza: CommonTree del catálogo, copa redonda de `radio` m, pie encalado."""
    from arboles_catalogo import poner, radio_copa
    alto = azar.uniform(6.0, 7.5)
    poner(c, "comun", x, y, z - 0.05, alto, semilla=azar.randint(0, 9999),
          ancho=max(0.8, min(1.6, radio / radio_copa("comun", alto))), encalado=1.0)


def palmera(c, x, y, z, azar, alto=12.0):
    """Palmera de la plaza (R0151): palmera canaria (Exotic Palm, CC0) o palmera alta (Yughues, CC0) del catálogo."""
    from arboles_catalogo import poner
    esp = azar.choice(("palmera_canaria", "palmera_canaria_b", "palmera_alta"))
    poner(c, esp, x, y, z - 0.05, alto, semilla=azar.randint(0, 9999))


def arbusto(c, x, y, z, r, rol="follaje", color="#3c6a2b"):
    _copa(c, x, y, z + r * .35, r, r, r * .7, rol, color, anillos=4, sect=8)


def parche_flores(c, x, y, rx, ry, rumbo_x, rumbo_y, colores, altura=None):
    """Cantero de flores: orla de seto verde, anillos de colores y centro (visto en R0152/R0153).
    altura: función (x, y) → z del césped, para que el cantero siga su pendiente."""
    if altura is None:
        altura = lambda px, py: altura_suelo(px, py) + .21       # noqa: E731
    z = 0.03
    elipse_plana(c, x, y, z + .02, rx, ry, "cesped", "#3f6e2a", rumbo_x, rumbo_y, altura=altura)
    for i, col in enumerate(colores):
        f = 1 - (i + 1) * .22
        elipse_plana(c, x, y, z + .035 + i * .012, rx * f, ry * f, "flor", col, rumbo_x, rumbo_y, altura=altura)


# --------------------------------------------------------------------------- fuente (R0154)
def fuente(c, x, y, z):
    """Fuente circular de arenisca con taza central de fundición negra (R0154)."""
    c.cilindro(x, y, z, z + .26, 3.6, "piedra", "#8f735a", lados=24)
    c.cilindro(x, y, z + .26, z + .86, 3.45, "piedra", ARENISCA, lados=24, radio_arriba=3.38)
    c.cilindro(x, y, z + .86, z + 1.0, 3.62, "piedra", "#b89a7a", lados=24)                       # brocal
    c.cilindro(x, y, z + .8, z + .83, 3.1, "agua", None, lados=24)
    c.cilindro(x, y, z + .8, z + 1.45, .5, "piedra", "#9c7f62", lados=10, radio_arriba=.3)
    c.cilindro(x, y, z + 1.45, z + 1.75, .8, "hierro", HIERRO, lados=12, radio_arriba=.45)
    c.cilindro(x, y, z + 1.75, z + 2.7, .13, "hierro", HIERRO, lados=8)
    c.cilindro(x, y, z + 2.2, z + 2.45, .55, "hierro", HIERRO, lados=12, radio_arriba=.3)
    c.cilindro(x, y, z + 2.7, z + 2.95, .3, "hierro", HIERRO, lados=8, radio_arriba=.08)
    c.esfera(x, y, z + 3.05, .1, "metal", ORO, segmentos=6)


# --------------------------------------------------------------------------- vendedores ambulantes (R0133, R0135)
def carrito_fruta(c, x, y, z, ux, uy, color="#2f7a44"):
    """Carrito de mano de vendedor (R0133): cajón verde con bandeja de naranjas, dos ruedas de bicicleta y varas de empuje."""
    caja_local(c, x, y, z + .55, z + .95, ux, uy, 1.4, .8, "madera", color)                       # cajón
    caja_local(c, x, y, z + .95, z + 1.0, ux, uy, 1.5, .9, "madera", "#e8e2d2")                   # borde claro
    for i in range(6):                                                                            # pirámide de naranjas
        for j in range(4):
            fx, fy = -.55 + i * .22, -.3 + j * .2
            c.esfera(x + ux * fx - uy * fy, y + uy * fx + ux * fy, z + 1.08, .1, "flor", "#f08a1c", segmentos=5)
    for i in range(4):
        for j in range(2):
            fx, fy = -.3 + i * .2, -.1 + j * .2
            c.esfera(x + ux * fx - uy * fy, y + uy * fx + ux * fy, z + 1.24, .1, "flor", "#f4a020", segmentos=5)
    for s in (-.45, .45):                                                                         # ruedas
        wx, wy = x - uy * s, y + ux * s
        for k in range(10):
            a0, a1 = k * math.tau / 10, (k + 1) * math.tau / 10
            p0 = (wx + ux * .32 * math.cos(a0), wy + uy * .32 * math.cos(a0), z + .33 + .32 * math.sin(a0))
            p1 = (wx + ux * .32 * math.cos(a1), wy + uy * .32 * math.cos(a1), z + .33 + .32 * math.sin(a1))
            _barra(c, p0, p1, .025, "hierro", "#1e1f1f")
        _barra(c, (wx, wy, z + .33), (wx, wy, z + .55), .02, "hierro", HIERRO)
    _barra(c, (x - ux * .1, y - uy * .1, z + .2), (x - ux * .1, y - uy * .1, z + .55), .03, "hierro", HIERRO)   # pata
    for s in (-.3, .3):                                                                           # varas de empuje
        _barra(c, (x - ux * .7 - uy * s, y - uy * .7 + ux * s, z + .8), (x - ux * 1.3 - uy * s, y - uy * 1.3 + ux * s, z + .95),
               .025, "hierro", HIERRO)


def puesto_sombrilla(c, x, y, z, ux, uy):
    """Puesto con sombrilla roja (R0135): mostrador rojo con letrero blanco y sombrilla de 8 gajos sobre mástil."""
    caja_local(c, x, y, z, z + 1.0, ux, uy, .9, 1.5, "madera", "#c8282a")
    caja_local(c, x, y, z + 1.0, z + 1.05, ux, uy, 1.0, 1.6, "madera", "#e9e4da")
    caja_local(c, x, y, z + .25, z + .85, ux, uy, .02, 1.1, "letrero", "#f2f0ea", dx=.46)          # letrero al frente
    c.cilindro(x, y, z + 1.05, z + 2.55, .03, "hierro", "#d8d4cc", lados=6)
    n, R = 8, 1.55
    for k in range(n):
        a0, a1 = k * math.tau / n, (k + 1) * math.tau / n
        col = "#d22f2c" if k % 2 else "#e04a3a"
        c.poligono([(x, y, z + 2.75), (x + R * math.cos(a0), y + R * math.sin(a0), z + 2.25),
                    (x + R * math.cos(a1), y + R * math.sin(a1), z + 2.25)], "pintura_acento", col)
        c.poligono([(x, y, z + 2.74), (x + R * math.cos(a1), y + R * math.sin(a1), z + 2.24),
                    (x + R * math.cos(a0), y + R * math.sin(a0), z + 2.24)], "pintura_acento", "#a8231f")


# --------------------------------------------------------------------------- glorieta (R0142)
def glorieta(c, x, y, z, rumbo=0.0):
    """Glorieta junto a la fuente (R0142): plataforma octogonal de arenisca de ~1 m con gradas, baranda de hierro, ocho postes
    finos de fundición y cubierta roja de poca pendiente con borde festoneado y remate."""
    n, R = 8, 4.2

    def v(r, z_, k, off=0.0):
        a = rumbo + (k + off) * math.tau / n
        return (x + r * math.cos(a), y + r * math.sin(a), z_)
    for k in range(n):                                                     # plataforma
        j = (k + 1) % n
        c.poligono([v(R, z, k), v(R, z, j), v(R, z + 1.0, j), v(R, z + 1.0, k)], "piedra", "#a5866a")
        c.poligono([v(R + .12, z + 1.0, k), v(R + .12, z + 1.0, j), v(R + .12, z + 1.12, j), v(R + .12, z + 1.12, k)], "piedra", "#b89a7a")
    c.poligono([v(R + .12, z + 1.12, k) for k in range(n)], "piedra", "#c9b49a")
    a0 = rumbo + .5 * math.tau / n                                         # gradas en una cara
    ox, oy = math.cos(a0), math.sin(a0)
    ap = R * math.cos(math.pi / n)
    for s in range(4):
        caja_local(c, x + ox * (ap + .3 + .3 * (3 - s)), y + oy * (ap + .3 + .3 * (3 - s)), z, z + .25 * (s + 1), ox, oy, .32, 1.6,
                   "piedra", "#b89a7a")
    for k in range(n):                                                     # postes y baranda
        px, py, _ = v(R - .25, 0, k)
        zt = z + 1.12
        c.cilindro(px, py, zt, zt + 2.9, .07, "hierro", HIERRO, lados=6)
        c.cilindro(px, py, zt, zt + .18, .14, "hierro", HIERRO, lados=6)
        if k != 0:                                                          # la cara de la escalera queda abierta
            j = (k + 1) % n
            q = v(R - .25, 0, j)
            _barra(c, (px, py, zt + .95), (q[0], q[1], zt + .95), .025, "hierro", HIERRO)
            _barra(c, (px, py, zt + .15), (q[0], q[1], zt + .15), .02, "hierro", HIERRO)
            for t in (.2, .4, .6, .8):
                bx, by = px + (q[0] - px) * t, py + (q[1] - py) * t
                _barra(c, (bx, by, zt + .15), (bx, by, zt + .95), .012, "hierro", HIERRO)
    zr = z + 1.12 + 2.9
    for k in range(n):                                                     # cubierta
        j = (k + 1) % n
        # con grosor (prisma cerrado): una cara suelta queda con la normal hacia arriba y no se ve desde abajo
        c.poligono([v(R + .35, zr, k), v(R + .35, zr, j), (x, y, zr + 1.3)], "teja", "#b23a33" if k % 2 else "#a8342e",
                   grosor=.07, normal_extrusion=(0, 0, -1))
        for f in range(3):                                                 # festón
            p0 = v(R + .36, zr - .07, k, f / 3)
            p1 = v(R + .36, zr - .07, k, (f + 1) / 3)
            pm = v(R + .36, zr - .34, k, (f + .5) / 3)
            a_ = rumbo + (k + .5) * math.tau / n
            c.poligono([p0, p1, pm], "teja", "#a8342e", grosor=.03, normal_extrusion=(-math.cos(a_), -math.sin(a_), 0))
    c.cilindro(x, y, zr + 1.2, zr + 1.7, .09, "hierro", HIERRO, lados=6, radio_arriba=.03)
    c.esfera(x, y, zr + 1.75, .1, "metal", ORO, segmentos=6)
