"""Lado SE de la Calle Batalla de Junín, desde la placita del Mercado Central (esquina con Ravelo) hasta la Av. Hernando
Siles — correcciones del usuario R0045–R0058 (2026-11-12/13). Zona comercial muy densa; vereda de 4,3 m.

El usuario aclaró (R0058) que puso las fotos "más cerca de lo que están": la secuencia real ocupa toda la cuadra.
Secuencia (s = metros sobre el eje de Junín desde el cruce con Ravelo):

  s 15–64   A  MERCADO de 2 plantas: locales abiertos con mercadería y toldo; lunetos (medio punto) arriba (R0046–R0048)
  s 64–100  B  EDIFICIO ALTO blanco de 3 plantas con "dobleces" (cuerpos salientes alternos, ventanas altas y
               angostas), remate escalonado; entrada en arco con letrero de relojeros (s≈92) y carpa naranja (R0049–R0052)
  s 100–117 C  ENTRADA CON ESCALERAS al mercado entre dos cuerpos: cuerpo bajo con gran ventanal de medio punto y una
               galería-caja amarilla en el piso alto; puestos y quitasol; pino grande en la vereda (R0053, R0054)
  s 117–134 D  MERCADO de 2 plantas: lunetos arriba y abajo, toldos, DOS ÁRBOLES grandes (pinos) en la vereda (R0055)
  s 134–fin E  EDIFICIOS MODERNOS de 4–5 plantas: bandas de ventanas, persianas metálicas abajo, letreros, volúmenes
               escalonados, antena; esquina con Hernando Siles (R0056–R0058)

Uso (desde M013): frente_junin(col, corte=(CQ, bq, DPL)) — 'corte' quita la placita de la esquina.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit import *  # noqa: E402,F403
from kit import arquitectura as A  # noqa: E402
from kit.datos import _cortar_semiplano, calles_reales, recortar_a_calles  # noqa: E402
from mercado_claude import luneto, tienda  # noqa: E402
from piezas_claude import lado_virtual, suelo_huella, techo_auto  # noqa: E402

BLANCO = "#f5f4f0"
_ej = [c for c in calles_reales() if c["nombre"] == "Calle Batalla de Junín" and c.get("peatonal")][0]
EJE = [tuple(p) for p in _ej["eje"]]
W = _ej["ancho"] / 2
VEREDA = _ej["vereda"]
_acum = [0.0]
for p, q in zip(EJE, EJE[1:]):
    _acum.append(_acum[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
LARGO = _acum[-1]
_cen = (-140.0, 100.0)          # un punto dentro de la manzana del mercado (lado SE)


def _seg(s):
    s = max(0.0, min(LARGO - 1e-6, s))
    for i in range(len(EJE) - 1):
        if _acum[i + 1] >= s:
            p, q = EJE[i], EJE[i + 1]
            L = _acum[i + 1] - _acum[i] or 1.0
            u = ((q[0] - p[0]) / L, (q[1] - p[1]) / L)
            n = (u[1], -u[0])
            if (_cen[0] - p[0]) * n[0] + (_cen[1] - p[1]) * n[1] < 0:
                n = (-n[0], -n[1])
            t = s - _acum[i]
            return (p[0] + u[0] * t, p[1] + u[1] * t), u, n
    return EJE[-1], (1.0, 0.0), (0.0, -1.0)


def P(s, d=0.0):
    """Punto sobre la línea de fachadas del lado SE (d metros hacia adentro de la manzana; negativo = vereda)."""
    p, u, n = _seg(s)
    return (p[0] + n[0] * (W + d), p[1] + n[1] * (W + d))


def N(s):
    """Normal de la fachada (hacia la calle)."""
    _, _, n = _seg(s)
    return (-n[0], -n[1])


def cuerpo(nombre, s0, s1, fondo, alto, corte=None, color=BLANCO):
    """Volumen recortado a las calles reales y su fachada a Junín (tramo recto entre s0 y s1)."""
    pts = [P(s0, 0.02)]
    k = s0
    while k < s1:
        k = min(s1, k + 3.0)
        pts.append(P(k, 0.02))
    pts += [P(s1, fondo), P(s0, fondo)]
    h = recortar_a_calles(pts, area_min=8) or pts
    if corte:
        h = _cortar_semiplano(h, corte[0][0], corte[0][1], corte[1][0], corte[1][1], corte[2]) or h
    zb, zr = suelo_huella(h)
    c = Constructor(nombre)
    c.prisma(h, zb - 0.6, zr + alto, "muro", color, tapa=False)
    techo_auto(c, h, zr + alto - 0.02, zpatio=zb, muro=("muro", color))
    f = Fachada(c, lado_virtual(P(s0), P(s1), N((s0 + s1) / 2)), altura_suelo(*P((s0 + s1) / 2)))
    return c, f, zr - f.suelo


def arbol_pino(c, x, y, z, alto=13.0, semilla=0):
    """Pino/casuarina grande de vereda (R0054, R0055): tronco alto y copa irregular en pisos de ramas oscuras."""
    rnd = random.Random(semilla)
    c.cilindro(x, y, z - 0.2, z + alto * 0.75, 0.32, "tronco", "#4a3626", lados=8, radio_arriba=0.12)
    c.cilindro(x, y, z - 0.05, z + 0.9, 0.36, "muro", "#f4f2ec", lados=8)          # pie encalado
    # copa desde los 4 m: se camina por debajo (en las fotos las ramas bajas están podadas)
    for k in range(6):
        h = z + 4.2 + (alto - 5.0) * k / 5
        r = min(alto * (0.2 - 0.022 * k), h - z - 3.2) * rnd.uniform(0.85, 1.1)
        for j in range(3):
            a = rnd.uniform(0, 6.28)
            c.esfera(x + math.cos(a) * r * 0.45, y + math.sin(a) * r * 0.45, h + r * 0.3, max(0.6, r * rnd.uniform(0.5, 0.65)),
                     "follaje", "#3f5f34" if (k + j) % 2 else "#4d6b3a", segmentos=7)


def arbol_pino_catalogo(c, x, y, z, alto=13.0, semilla=0):
    """[A prueba, no en uso: el usuario prefirió los anteriores (2026-11-23); se volverán a probar.] Pino grande de vereda (R0054, R0055): Pine de Quaternius (CC0) del catálogo elegido por el usuario, pie encalado."""
    from arboles_catalogo import poner
    poner(c, "pino_a" if semilla % 2 else "pino_b", x, y, z - 0.05, alto, semilla=semilla, encalado=0.9)


def bolardos_y_bancos(c, s0, s1, bancos=()):
    k = s0 + 1.0
    while k < s1 - 0.5:
        x, y = P(k, -(VEREDA - 0.45))
        z = altura_suelo(x, y) + 0.18
        c.cilindro(x, y, z, z + 0.75, 0.07, "hierro", "#2f2b28", lados=8)
        c.esfera(x, y, z + 0.78, 0.08, "hierro", "#2f2b28", segmentos=6)
        k += 2.6
    for sb in bancos:
        x, y = P(sb, -(VEREDA - 1.6))
        z = altura_suelo(x, y) + 0.18
        nx, ny = N(sb)
        ux, uy = -ny, nx
        c.caja_ejes((x, y, z + 0.44), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 1.8, 0.42, 0.06, "madera", "#6e4a2e")
        c.caja_ejes((x - nx * 0.2, y - ny * 0.2, z + 0.72), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 1.8, 0.05, 0.4, "madera", "#6e4a2e")
        for sg in (-0.75, 0.75):
            c.caja_ejes((x + ux * sg, y + uy * sg, z + 0.22), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 0.06, 0.42, 0.44, "hierro")


def quitasol(c, s, d, color, rnd):
    x, y = P(s, d)
    z = altura_suelo(x, y) + 0.18
    c.cilindro(x, y, z, z + 2.2, 0.03, "metal", "#9aa0a3", lados=4)
    c.cilindro(x, y, z + 2.0, z + 2.5, 1.2, "letrero", color, lados=10, radio_arriba=0.05)
    c.caja(x - 0.6, y - 0.4, z, x + 0.6, y + 0.4, z + 0.9, "letrero", rnd.choice(["#c94f4f", "#3f7fb5", "#e8c64a"]))


def mercado(nombre, s0, s1, rnd, corte=None, doble_luneto=False):
    """Tramo del mercado de 2 plantas: locales con toldo + lunetos (R0046–R0048, R0055)."""
    c, f, off = cuerpo(nombre, s0, s1, 16.0, 9.2, corte)
    A.zocalo(f, 0.4 + off, color="#b3a493", sillares=False, desde=-0.6)
    paso = 3.9
    n = max(1, int(f.largo / paso))
    paso = f.largo / n
    for k in range(n):
        sm = paso * (k + 0.5)
        tienda(f, sm - paso / 2, sm + paso / 2, off, rnd)
        luneto(f, sm, off)
        if doble_luneto:
            luneto(f, sm, off, r=0.9, h=7.4)
        if k:
            f.caja(paso * k - 0.2, paso * k + 0.2, 0.0, 8.6 + off, 0.0, 0.14, "moldura", BLANCO)
    A.imposta(f, 4.45 + off, alto=0.25, vuelo=0.14, rol="moldura", color=BLANCO)
    A.cornisa(f, 8.6 + off, vuelo=0.2, alto=0.3, rol="moldura", color=BLANCO)
    A.parapeto(f, 8.9 + off, alto=0.4, rol="muro", color=BLANCO)
    return c


def edificio_dobleces(nombre, s0, s1, rnd, s_arco, s_carpa):
    """Edificio alto blanco con cuerpos salientes alternos y remate escalonado (R0049–R0052)."""
    c, f, off = cuerpo(nombre, s0, s1, 15.0, 12.6, color="#f2f1ec")
    L = f.largo
    s_ = 0.6
    k = 0
    while s_ < L - 2.0:
        sale = 0.7 if k % 2 == 0 else 0.0
        if sale:
            f.caja(s_, s_ + 2.6, 3.6 + off, 12.6 + off, 0.0, sale, "muro", "#f2f1ec")
            # remate escalonado (los "piñones" de la azotea)
            f.caja(s_ + 0.3, s_ + 2.3, 12.6 + off, 14.0 + off, 0.0, sale, "muro", "#f2f1ec")
            f.caja(s_ + 0.8, s_ + 1.8, 14.0 + off, 14.9 + off, 0.0, sale, "muro", "#f2f1ec")
        for piso in range(2):
            for dx in (0.75, 1.85):
                ss = s_ + dx
                A.ventana(f, ss, 4.6 + piso * 3.9 + off, ancho=0.55, alto=2.4, moldura="moldura", color_moldura="#f2f1ec",
                          carpinteria="marco_ventana", color_carpinteria="#54606a")
                f.caja(ss - 0.3, ss + 0.3, 4.6 + piso * 3.9 + off, 7.0 + piso * 3.9 + off, sale, sale + 0.01, "vidrio")
        s_ += 3.1
        k += 1
    s_ = 0.4
    while s_ + 3.6 <= L:
        sm = s_ + 1.8
        if abs(s0 + sm - s_arco) < 1.8:              # entrada en arco con letrero de relojeros
            f.caja(s_ + 0.4, s_ + 3.2, 0.0, 2.8 + off, -0.02, 0.0, "madera", "#2a2420")
            f.arco(sm, 1.4, 0.3, 2.8 + off, 0.0, 0.12, "moldura", "#f2f1ec", segmentos=10)
            f.timpano_arco(sm, 1.4, 2.8 + off, 0.02, "madera", "#2a2420")
            f.caja(s_ + 0.5, s_ + 3.1, 3.3 + off, 3.9 + off, 0.12, 0.2, "letrero", "#3b5fa0")
        else:
            tienda(f, s_, s_ + 3.6, off, rnd, toldo="#e8823a" if abs(s0 + sm - s_carpa) < 1.8 else None)
        s_ += 3.6
    # carpa naranja de feria sobre la vereda
    x, y = P(s_carpa, -2.6)
    z = altura_suelo(x, y) + 0.18
    nx, ny = N(s_carpa)
    ux, uy = -ny, nx
    for dx, dy in ((-1.2, -1.0), (1.2, -1.0), (-1.2, 1.0), (1.2, 1.0)):
        c.cilindro(x + ux * dx + nx * dy, y + uy * dx + ny * dy, z, z + 2.3, 0.03, "metal", "#9aa0a3", lados=4)
    c.caja_ejes((x, y, z + 2.45), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 2.8, 2.4, 0.3, "letrero", "#e8732f")
    c.caja_ejes((x, y, z + 0.45), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 2.2, 0.8, 0.9, "letrero", "#c94f4f")
    return c


def entrada_escaleras(nombre, s0, s1, rnd):
    """Entrada al mercado con escaleras entre dos cuerpos (R0053, R0054): cuerpo bajo con gran ventanal de medio
    punto, galería-caja amarilla en la planta alta, escalinata hacia adentro, puestos y quitasol."""
    c, f, off = cuerpo(nombre, s0, s1, 16.0, 8.6)
    L = f.largo
    sm = L * 0.55
    # el vano de la entrada: hueco oscuro y escalones que suben hacia adentro
    f.caja(sm - 2.0, sm + 2.0, 0.0, 3.6 + off, -0.02, 0.0, "madera", "#3a3430")
    for k in range(6):
        f.caja(sm - 1.9, sm + 1.9, 0.0, 0.18 * (k + 1) + off, -0.4 * (k + 1), -0.4 * k, "piedra", "#c9bca6")
    f.arco(sm, 2.0, 0.25, 3.6 + off - 2.0 + 2.0, 0.0, 0.12, "moldura", BLANCO, segmentos=10)
    # gran ventanal de medio punto a la izquierda, planta alta
    luneto(f, L * 0.22, off, r=1.8, h=5.0)
    f.caja(L * 0.22 - 1.6, L * 0.22 + 1.6, 3.6 + off, 5.0 + off, 0.0, 0.02, "vidrio", "#33505a")
    # galería-caja amarilla sobre la entrada
    f.caja(sm - 2.2, sm + 2.2, 4.4 + off, 6.6 + off, 0.0, 0.9, "pintura_acento", "#e3c35a")
    for k in range(6):
        f.caja(sm - 2.0 + k * 0.8, sm - 2.0 + k * 0.8 + 0.06, 4.6 + off, 6.4 + off, 0.9, 0.95, "hierro")
    f.caja(sm - 2.2, sm + 2.2, 6.6 + off, 6.8 + off, -0.1, 1.05, "moldura", "#f2efe6")
    # puestos a los lados de la entrada
    tienda(f, 0.4, sm - 2.3, off, rnd, vuelo=2.0)
    tienda(f, sm + 2.3, L - 0.3, off, rnd, vuelo=2.0)
    A.cornisa(f, 8.3 + off, vuelo=0.2, alto=0.3, rol="moldura", color=BLANCO)
    quitasol(c, s0 + sm - 3.5, -1.8, "#d98cab", rnd)
    return c


def edificio_moderno(nombre, s0, s1, rnd, pisos=4, esquina=False):
    """Edificios modernos de 4–5 plantas (R0056–R0058): bandas de ventanas con marcos claros, persianas metálicas,
    letreros, cuerpo superior retranqueado y antena."""
    alto = pisos * 3.1 + 1.0
    c, f, off = cuerpo(nombre, s0, s1, 14.0, alto, color="#eeece6")
    L = f.largo
    for piso in range(1, pisos):
        h = piso * 3.1 + 1.0 + off
        f.caja(-0.05, L + 0.05, h - 0.2, h, 0.0, 0.35, "moldura", "#e2ded4")             # losa saliente
        k = 0.4
        while k < L - 0.8:
            w = min(2.4, L - 0.4 - k)
            f.caja(k, k + w, h + 0.7, h + 2.5, 0.0, 0.02, "vidrio")
            for j in range(4):
                f.caja(k + w * j / 3 - 0.04, k + w * j / 3 + 0.04, h + 0.7, h + 2.5, 0.0, 0.05, "marco_ventana", "#d9dde0")
            f.caja(k, k + w, h + 1.55, h + 1.6, 0.0, 0.05, "marco_ventana", "#d9dde0")
            k += w + 0.5
    # planta baja: persianas metálicas cerradas alternadas con locales abiertos
    s_ = 0.3
    j = 0
    while s_ + 3.2 <= L:
        if j % 3 == 1:
            f.caja(s_ + 0.2, s_ + 3.0, 0.0, 3.0 + off, 0.0, 0.08, "metal", "#a8aeb2")
            for hh in range(10):
                f.caja(s_ + 0.2, s_ + 3.0, 0.3 * hh + off, 0.3 * hh + 0.03 + off, 0.08, 0.1, "metal", "#8f969b")
        else:
            tienda(f, s_, s_ + 3.2, off, rnd, vuelo=1.6)
        s_ += 3.2
        j += 1
    f.caja(L * 0.3, L * 0.3 + 3.0, 1.0 + 3.1 + off, 1.0 + 3.1 + 0.7 + off, 0.36, 0.42, "letrero", "#e3c35a")  # letrero
    if pisos >= 4:   # antena en la azotea
        q = f.punto(L * 0.6, 0, -5.0)
        c.cilindro(q.x, q.y, f.suelo + alto + off, f.suelo + alto + off + 7.0, 0.05, "metal", "#9aa0a3", lados=4)
    if esquina:      # la vuelta hacia Hernando Siles: misma banda de ventanas en el costado
        pass
    return c


def frente_junin(col, corte=None):
    rnd = random.Random("junin-norte")
    S_FIN = LARGO - 5.0
    tramos = [
        mercado("JN_A_mercado", 15.0, 64.0, rnd, corte=corte),
        edificio_dobleces("JN_B_edificio_alto", 64.0, 100.0, rnd, s_arco=92.0, s_carpa=72.0),
        entrada_escaleras("JN_C_entrada_escaleras", 100.0, 117.0, rnd),
        mercado("JN_D_mercado", 117.0, 134.0, rnd, doble_luneto=True),
        edificio_moderno("JN_E1_edificio", 134.0, 146.0, rnd, pisos=4),
        edificio_moderno("JN_E2_edificio_esquina", 146.0, S_FIN, rnd, pisos=5, esquina=True),
    ]
    for c in tramos:
        c.objeto(col)
    v = Constructor("JN_vereda")
    for s_, sem in ((109.0, 1), (121.0, 2), (130.0, 3)):           # pinos grandes de la vereda
        x, y = P(s_, -(VEREDA - 0.9))
        arbol_pino(v, x, y, altura_suelo(x, y) + 0.18, alto=rnd.uniform(12.0, 15.0), semilla=sem)
    bolardos_y_bancos(v, 16.0, S_FIN, bancos=(26.0, 44.0, 58.0, 124.0, 138.0))
    v.objeto(col)


def huella_frente():
    """Polígono que ocupa todo el frente (para ocultar los volúmenes del lienzo en el visor)."""
    pts = [P(s, 0.0) for s in range(15, int(LARGO - 4), 4)]
    pts += [P(s, 16.0) for s in range(int(LARGO - 4), 14, -4)]
    return [[round(x, 2), round(y, 2)] for x, y in pts]
