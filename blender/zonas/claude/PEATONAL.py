"""PEATONAL de Junín — Calle Batalla de Junín entre Ravelo y la Av. Hernando Siles, los DOS frentes (pedido del
usuario 2026-11-13: "encárgate tú por completo de esta calle"; R0087 y R0045–R0079).

Fuentes cotejadas: las fotos de fachada de cada lado (referencia de R0045–R0062 para el lado SE, R0063–R0079 para el
NO) y el recorrido de la carpeta Peatonal/ (17 vistas cada ~10 m, de Ravelo a Hernando Siles), que fija el orden y el
largo de cada edificio. Sección: vereda NO 3,5 m, calzada de ASFALTO 5 m sin marcas (R0132), vereda SE 6 m.

LADO SE (Mercado Central), de Ravelo a Hernando Siles (s ≈ metros desde Ravelo):
  placita de la esquina (M013) · MERCADO de 2 plantas: pilares blancos, locales con toldos blancos, gran imposta y
  LUNETOS de vidrio de colores arriba; entrada en arco al centro (R0046–R0048) · BLOQUE ALTO blanco de 3–4 plantas
  con "dobleces" (cuerpos salientes alternos de distinta altura, ventanas altas y angostas), entrada en arco de los
  relojeros y carpa naranja (R0049–R0052) · ENTRADA con escalinata, cuerpo bajo con luneto y galería amarilla
  (R0053–R0054) · MERCADO bajo con dos filas de arcos y DOS PINOS grandes en la vereda (R0055) · EDIFICIOS MODERNOS
  de 4–5 plantas: vidriado (R0056), SIMA C&N con tejadito rojo (R0057), CORAG en la esquina con banda azul (R0058–59).
LADO NO, de Ravelo a Hernando Siles:
  CASONA DE LA ESQUINA (Feria de Libros) con gran mirador de madera, alero de tejas, balcones de hierro, VIVA, Las
  Esquinas (R0076–R0079) · casa colonial angosta · SHOPPING FLORENCIA (R0074–75) · edificio moderno de bandas, Farmacia
  San Agustín (R0072–73) · casita de tejas · edificio angosto San Valentín (R0071) · SHOPPING Ma. CLOTILDE (R0070) ·
  casas de tejas: Librería Torre, casita del balcón, La Comelona (R0068–69) · casa larga de 2 plantas, Memphis y Bata
  (R0066–67) · GALERÍA GUADALUPE (R0066) · Antonio's y GALERÍA HUICI con balcones (R0064–65) · Samsung y la esquina
  moderna ZTE (R0063).
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from kit import arquitectura as A_  # noqa: E402
from kit.datos import lados, recortar_a_calles  # noqa: E402
from mercado_claude import tienda, toldo  # noqa: E402
from piezas_claude import (adelantada, cortina_metalica, lado_virtual, mirador, suelo_huella, techo_auto,  # noqa: E402
                           tejado_dos_aguas)
import peatonal_marco as PM  # noqa: E402
from peatonal_marco import P, NOUT  # noqa: E402

AGENTE, MID = "claude", "PEATONAL"
m, col = iniciar(AGENTE, MID)
BL = "#f5f4f0"
CREMA = "#efe6d2"
MADERA = "#5a3a26"
VIDRIOS = ["#3f6f8f", "#4f8a6a", "#8a4f4f", "#3f5f8f", "#6f8a4f", "#2f5a7a"]
S0 = {l: PM.limites(l)[0] for l in ("NO", "SE")}
S1 = {l: PM.limites(l)[1] for l in ("NO", "SE")}
print("[PEATONAL] límites", {l: (round(S0[l], 1), round(S1[l], 1)) for l in S0})
RND = random.Random("peatonal")


# =============================================================================== volúmenes y fachadas
def cuerpo(lado, nombre, s0, s1, alto, fondo=None, color=BL, techo="plano", retiro=0.0):
    """Volumen entre s0 y s1 del lado, recortado a las calles (las esquinas quedan con su ochava real) y su fachada a
    la peatonal. retiro: la fachada queda d metros adentro (entradas retiradas)."""
    fondo = fondo or PM.FONDO[lado]
    a0 = s0 - (12 if s0 <= S0[lado] + 0.5 else 0)
    a1 = s1 + (12 if s1 >= S1[lado] - 0.5 else 0)
    pts = [P(lado, a0, retiro), P(lado, a1, retiro), P(lado, a1, fondo), P(lado, a0, fondo)]
    h = recortar_a_calles(pts, area_min=4) or pts
    zb, zr = suelo_huella(h)
    c = Constructor(nombre)
    c.huella = h                                           # al exportar se recorta a sus medianeras
    c.prisma(h, zb - 0.6, zr + alto, "muro", color, tapa=False)
    if techo == "tejas":
        c.tapa(h, zr + alto - 0.02, "muro", color)
        tejado_dos_aguas(c, h, zr + alto, pendiente=22, vuelo=0.25, hastial="muro", color_hastial=color, alto_max=1.8,
                         cumbrera=PM.U)
    else:
        # azotea plana (como en las fotos): el techo de tejas con patio dejaba hastiales blancos asomando sobre los
        # pretiles (glitch visto a pie, 2026-11-13)
        A_.techo_plano(c, h, zr + alto - 0.02, rol="azotea", color="#e9e6df")
    sa, sb = max(s0, S0[lado]), min(s1, S1[lado])
    pa, pb = P(lado, sa, retiro), P(lado, sb, retiro)
    if lado == "NO":
        pa, pb = pb, pa                      # el sentido de s de la fachada: de izquierda a derecha visto desde la calle
    f = Fachada(c, lado_virtual(pa, pb, NOUT(lado)), altura_suelo(*P(lado, (sa + sb) / 2, retiro)))
    # fachadas laterales a otra calle (esquinas)
    otras = []
    for l in lados(h):
        if not l["a_calle"] or l["largo"] < 2.5 or "Junín" in l["calle"]:
            continue
        mx, my = (l["a"][0] + l["b"][0]) / 2, (l["a"][1] + l["b"][1]) / 2
        if abs(PM.sd(mx, my)[1]) < PM.W + 0.6:
            continue
        otras.append(Fachada(c, l, altura_suelo(mx, my)))
    return c, f, zr - f.suelo, otras, zb, zr


def S(f, lado, s):
    """s de la calle → s local de la fachada f."""
    p = P(lado, s)
    return (p[0] - f.a.x) * f.u.x + (p[1] - f.a.y) * f.u.y


def letrero(f, s0, s1, h0, h1, color, d=0.12, borde="#f2efe6"):
    f.caja(s0, s1, h0, h1, 0.04, d, "letrero", color)
    f.caja(s0 + 0.12, s1 - 0.12, h0 + 0.1, h1 - 0.1, d, d + 0.01, "letrero", borde)        # campo con "texto"
    k = s0 + 0.35
    while k < s1 - 0.5:
        f.caja(k, k + RND.uniform(0.15, 0.4), h0 + 0.2, h1 - 0.2, d + 0.01, d + 0.02, "letrero", color)
        k += RND.uniform(0.3, 0.6)


def local_abierto(f, s0, s1, off, alto=2.9, letrero_col=None):
    """Local abierto (la mayoría en las fotos): hueco con interior claro, mercadería colgada y apilada en las paredes,
    un exhibidor en la puerta y letrero arriba. El hueco se simula con jambas y dintel que salen 0,5 m del muro."""
    f.caja(s0, s1, 0.0, alto + off, 0.0, 0.02, "letrero", RND.choice(["#d9cfbd", "#e2d8c4", "#cfc4b0"]))  # fondo
    f.caja(s0 - 0.12, s0 + 0.05, 0.0, alto + 0.12 + off, 0.0, 0.5, "muro", "#f2f0ea")
    f.caja(s1 - 0.05, s1 + 0.12, 0.0, alto + 0.12 + off, 0.0, 0.5, "muro", "#f2f0ea")
    f.caja(s0 - 0.12, s1 + 0.12, alto + off, alto + 0.14 + off, 0.0, 0.5, "muro", "#f2f0ea")
    k = s0 + 0.2
    while k < s1 - 0.3:                                                                        # mercadería colgada
        w = RND.uniform(0.2, 0.45)
        h1 = alto + off - RND.uniform(0.1, 0.4)
        f.caja(k, k + w, h1 - RND.uniform(0.6, 1.4), h1, 0.03, 0.2, "letrero",
               RND.choice(["#c94f4f", "#3f7fb5", "#e8c64a", "#5a9a5a", "#d98c6a", "#8a5aa0", "#f2f0ea", "#e07ab0"]))
        k += w + 0.08
    for x in (s0 + 0.08, s1 - 0.53):                                                           # estantes laterales
        for hh in (0.3, 0.8, 1.3):
            f.caja(x, x + 0.45, hh + off, hh + 0.3 + off, 0.03, 0.42, "letrero",
                   RND.choice(["#c94f4f", "#3f7fb5", "#e8c64a", "#5a9a5a", "#f2f0ea", "#d98c6a"]))
    sm = (s0 + s1) / 2                                                                         # exhibidor en la puerta
    f.caja(sm - 0.45, sm + 0.45, 0.0, 1.5 + off, 0.55, 0.9, "marco_ventana", "#8a8f93")
    for hh in (0.35, 0.75, 1.15):
        f.caja(sm - 0.42, sm + 0.42, hh + off, hh + 0.28 + off, 0.58, 0.88, "letrero",
               RND.choice(["#c94f4f", "#3f7fb5", "#e8c64a", "#f2f0ea", "#5a9a5a"]))
    if letrero_col:
        letrero(f, s0 + 0.1, s1 - 0.1, alto + 0.15 + off, alto + 0.75 + off, letrero_col, d=0.6)


def vidriera(f, s0, s1, off, alto=2.9, marco="#3b3f42", letrero_col=None, puerta=True):
    """Local con vidriera: marco oscuro, vidrio, puerta vidriada y letrero sobre el vano. La mitad de las veces, un
    local abierto (como la mayoría en las fotos)."""
    if RND.random() < 0.55:
        local_abierto(f, s0, s1, off, alto, letrero_col)
        return
    f.caja(s0, s1, 0.0, alto + off, 0.0, 0.02, "letrero", "#e2d8c4")                         # interior iluminado
    f.caja(s0, s1, 0.0, alto + off, 0.0, 0.08, "marco_ventana", marco)
    f.caja(s0 + 0.08, s1 - 0.08, 0.35, alto - 0.1 + off, 0.08, 0.09, "vidrio")
    if puerta and s1 - s0 > 2.2:
        sm = (s0 + s1) / 2
        for x in (sm - 0.55, sm + 0.5):
            f.caja(x, x + 0.06, 0.0, alto - 0.3 + off, 0.08, 0.13, "marco_ventana", marco)
    # mercadería detrás del vidrio (estantes de colores)
    k = s0 + 0.3
    while k < s1 - 0.5:
        f.caja(k, k + 0.4, 0.4, RND.uniform(1.2, 2.2) + off, 0.02, 0.07, "letrero",
               RND.choice(["#c94f4f", "#3f7fb5", "#e8c64a", "#5a9a5a", "#d98c6a", "#f2f0ea", "#8a5aa0"]))
        k += RND.uniform(0.5, 0.9)
    if letrero_col:
        letrero(f, s0 + 0.1, s1 - 0.1, alto + 0.1 + off, alto + 0.75 + off, letrero_col)


def vitrinas_vereda(c, lado, s0, s1, d=-0.7, paso=2.6):
    """Vitrinas de vidrio y exhibidores sobre la vereda delante de los locales (todas las fotos)."""
    nx, ny = NOUT(lado)
    tx, ty = -ny, nx
    k = s0 + 0.6
    while k < s1 - 0.6:
        if RND.random() < 0.45:
            x, y = P(lado, k, d)
            z = altura_suelo(x, y) + 0.18
            alto = RND.uniform(1.3, 1.7)
            c.caja_ejes((x, y, z + 0.1), (tx, ty, 0), (nx, ny, 0), (0, 0, 1), 0.7, 0.4, 0.2, "marco_ventana", "#6f767b")
            for a_ in (-0.33, 0.33):
                c.caja_ejes((x + tx * a_, y + ty * a_, z + alto / 2), (tx, ty, 0), (nx, ny, 0), (0, 0, 1), 0.04, 0.4, alto,
                            "marco_ventana", "#6f767b")
            c.caja_ejes((x, y, z + alto), (tx, ty, 0), (nx, ny, 0), (0, 0, 1), 0.7, 0.4, 0.04, "marco_ventana", "#6f767b")
            for hh in (0.5, 0.95, 1.4):
                if hh < alto - 0.2:
                    c.caja_ejes((x, y, z + hh), (tx, ty, 0), (nx, ny, 0), (0, 0, 1), 0.75, 0.38, 0.12, "letrero",
                                RND.choice(["#c94f4f", "#3f7fb5", "#e8c64a", "#5a9a5a", "#f2f0ea", "#d98c6a"]))
        k += paso * RND.uniform(0.8, 1.3)


def puesto(c, lado, s, d, largo=2.0, prof=1.2, lona=None):
    """Puesto callejero: mesa con mercadería y lona tendida sobre parantes (R0053–R0057, Peatonal/)."""
    nx, ny = NOUT(lado)
    tx, ty = -ny, nx
    x, y = P(lado, s, d)
    z = altura_suelo(x, y) + 0.18
    c.caja_ejes((x, y, z + 0.8), (tx, ty, 0), (nx, ny, 0), (0, 0, 1), largo, prof, 0.08, "madera", "#7a5e4a")
    for a in (-1, 1):
        for b in (-1, 1):
            c.cilindro(x + tx * a * (largo / 2 - 0.1) + nx * b * (prof / 2 - 0.1),
                       y + ty * a * (largo / 2 - 0.1) + ny * b * (prof / 2 - 0.1), z, z + 2.3, 0.03, "metal", "#8a8f93", lados=5)
    k = -largo / 2 + 0.15
    while k < largo / 2 - 0.2:
        w = RND.uniform(0.15, 0.4)
        c.caja_ejes((x + tx * (k + w / 2), y + ty * (k + w / 2), z + 0.84 + 0.12), (tx, ty, 0), (nx, ny, 0), (0, 0, 1),
                    w, prof * 0.8, RND.uniform(0.1, 0.35), "letrero",
                    RND.choice(["#c94f4f", "#3f7fb5", "#e8c64a", "#5a9a5a", "#d98c6a", "#8a5aa0", "#f2f0ea"]))
        k += w + 0.05
    lona = lona or RND.choice(["#f1eee6", "#3f6fb0", "#f1eee6", "#2f5fa8", "#e9e2d2"])
    c.caja_ejes((x, y, z + 2.32), (tx, ty, 0), (nx, ny, 0), (0, 0, 1), largo + 0.4, prof + 0.5, 0.04, "letrero", lona)


def quitasol(c, lado, s, d, color):
    x, y = P(lado, s, d)
    z = altura_suelo(x, y) + 0.18
    c.cilindro(x, y, z, z + 2.4, 0.03, "metal", "#8a8f93", lados=5)
    c.cilindro(x, y, z + 2.1, z + 2.55, 1.2, "letrero", color, lados=10, radio_arriba=0.05)


# =============================================================================== LADO SE
def mercado_lunetos(s0, s1, entrada=None, mayorista=()):
    """Mercado de 2 plantas (R0046–R0048): pilares blancos cada ~5,6 m, locales abiertos con toldo blanco, imposta
    gruesa, lunetos de vidrio de colores (algunos tapiados) y cornisa con pretil."""
    c, f, off, otras, zb, zr = cuerpo("SE", f"SE_mercado_{int(s0)}", s0, s1, 8.6)
    a, b = sorted((S(f, "SE", s0), S(f, "SE", s1)))
    n = max(1, round((b - a) / 5.6))
    paso = (b - a) / n
    A_.zocalo(f, 0.35 + off, s0=a, s1=b, color="#d9d4ca", sillares=False, desde=zb - 0.6 - f.suelo)
    for k in range(n + 1):
        sp = a + k * paso
        f.caja(sp - 0.35, sp + 0.35, 0.0, 4.2 + off, 0.0, 0.75, "muro", BL)            # pilares: los locales quedan hundidos
    for k in range(n):
        sm = a + (k + 0.5) * paso
        if entrada and abs(sm - S(f, "SE", entrada)) < paso / 2:
            # entrada central en arco (R0048): vano alto con rosca y letrero
            f.caja(sm - 1.7, sm + 1.7, 0.0, 3.6 + off, -0.6, 0.0, "madera", "#2a2420")
            f.timpano_arco(sm, 1.7, 3.6 + off, -0.02, "madera", "#2a2420")
            f.arco(sm, 1.7, 0.3, 3.6 + off, 0.0, 0.32, "moldura", BL, segmentos=12)
            f.caja(sm - 1.4, sm + 1.4, 4.1 + off, 4.6 + off, 0.3, 0.36, "letrero", "#2f4f8f")
            continue
        tienda(f, sm - paso / 2 + 0.35, sm + paso / 2 - 0.35, off, RND,
               toldo=RND.choice(["#f1eee6", "#f1eee6", "#efe7d6", "#e9a0a0", "#f1eee6"]), vuelo=2.0)
    f.caja(a, b, 3.75 + off, 4.2 + off, 0.0, 0.75, "muro", BL)                            # dintel de los locales
    f.caja(a, b, 4.2 + off, 4.75 + off, 0.0, 0.8, "moldura", BL)                           # imposta corrida
    for k in range(n):
        sm = a + (k + 0.5) * paso
        r = min(2.1, paso / 2 - 0.5)
        h = 5.3 + off
        tapiado = RND.random() < 0.2
        f.timpano_arco(sm, r, h, 0.02, "muro" if tapiado else "vidrio", "#ece9e2" if tapiado else RND.choice(VIDRIOS))
        f.arco(sm, r, 0.18, h, 0.0, 0.1, "moldura", BL, segmentos=14)
        if not tapiado:
            for ang in (0.45, 0.9, 1.35, 1.8, 2.25, 2.7):
                f.caja(sm + math.cos(ang) * r * 0.5 - 0.03, sm + math.cos(ang) * r * 0.5 + 0.03, h,
                       h + math.sin(ang) * r - 0.05, 0.0, 0.05, "marco_ventana", "#e9ecef")
            f.caja(sm - r, sm + r, h + r * 0.45, h + r * 0.45 + 0.06, 0.0, 0.05, "marco_ventana", "#e9ecef")
    A_.cornisa(f, 8.0 + off, vuelo=0.25, alto=0.3, s0=a, s1=b, color=BL)
    A_.parapeto(f, 8.3 + off, alto=0.5, s0=a, s1=b, color=BL)
    for sm in mayorista:                                                                 # "MAYORISTA CENTRAL"
        x = S(f, "SE", sm)
        letrero(f, x - 1.6, x + 1.6, 7.2 + off, 7.95 + off, "#2f4f8f")
    c.objeto(col)


def bloque_dobleces(s0, s1, entrada):
    """Bloque alto del Mercado (R0049–R0052): cuerpos alternos que salen 0,6 m y suben a distinta altura (11–14,5 m),
    ventanas altas y angostas en pares, remate escalonado; abajo locales y la entrada en arco de los relojeros."""
    c, f, off, otras, zb, zr = cuerpo("SE", "SE_bloque_alto", s0, s1, 11.0)
    a, b = sorted((S(f, "SE", s0), S(f, "SE", s1)))
    alturas = [12.5, 14.5, 11.5, 13.5, 12.0, 14.0, 11.0]
    n = max(3, round((b - a) / 5.5))
    paso = (b - a) / n
    for k in range(n):
        x0, x1 = a + k * paso, a + (k + 1) * paso
        ht = alturas[k % len(alturas)]
        sale = 0.6 if k % 2 == 0 else 0.0
        f.caja(x0, x1, 3.6 + off, ht + off, 0.0, sale + 0.02, "muro", BL)                 # cuerpo
        f.caja(x0, x1, ht + off, ht + 0.25 + off, 0.0, sale + 0.08, "moldura", BL)              # remate (sin vuelo lateral)
        # ventanas altas y angostas en pares, dos o tres pisos
        for pz in range(3 if ht > 12.5 else 2):
            h0 = 5.0 + pz * 3.0 + off
            if h0 + 2.2 > ht + off - 0.6:
                continue
            for dx in ((-0.55, 0.55) if paso > 3.5 else (0.0,)):
                sm = (x0 + x1) / 2 + dx
                f.caja(sm - 0.33, sm + 0.33, h0, h0 + 2.3, sale + 0.02, sale + 0.03, "vidrio")
                f.caja(sm - 0.4, sm + 0.4, h0 - 0.08, h0, sale, sale + 0.1, "moldura", BL)
                f.caja(sm - 0.03, sm + 0.03, h0, h0 + 2.3, sale + 0.02, sale + 0.06, "marco_ventana", "#d8dadc")
    # planta baja: locales y puestos, entrada en arco "Relojeros" (R0051–R0052)
    se = S(f, "SE", entrada)
    k = a + 0.3
    while k < b - 2.0:
        e = min(b - 0.3, k + 3.4)
        if abs((k + e) / 2 - se) < 2.6:
            k = e + 0.4
            continue
        tienda(f, k, e, off, RND, toldo=RND.choice(["#e9e2d2", "#f1eee6", "#c9b9a0"]), vuelo=1.9)
        for x in (k - 0.2, e + 0.2):
            f.caja(x - 0.25, x + 0.25, 0.0, 3.6 + off, 0.0, 0.7, "muro", BL)
        k = e + 0.4
    f.caja(a, b, 3.3 + off, 3.65 + off, 0.0, 0.7, "muro", BL)                              # dintel de la planta baja
    f.caja(se - 1.6, se + 1.6, 0.0, 3.2 + off, -0.8, 0.0, "madera", "#241f1b")
    f.timpano_arco(se, 1.6, 3.2 + off, -0.02, "madera", "#241f1b")
    f.arco(se, 1.6, 0.35, 3.2 + off, 0.0, 0.25, "moldura", BL, segmentos=12)
    f.timpano_arco(se, 1.25, 3.25 + off, 0.27, "letrero", "#3a3f8f", segmentos=10)       # letrero en el arco
    f.caja(se - 1.0, se + 1.0, 3.5 + off, 3.9 + off, 0.27, 0.29, "letrero", "#e9d9a0")
    c.objeto(col)


def entrada_escalinata(s0, s1):
    """Entrada retirada con escalinata (R0053–R0054): gradas hacia un portal en arco, cuerpo bajo con un gran luneto y
    una galería-caja amarilla arriba; a un lado la pared alta del bloque."""
    c, f, off, otras, zb, zr = cuerpo("SE", "SE_entrada_escalinata", s0, s1, 9.5, retiro=3.0)
    a, b = sorted((S(f, "SE", s0), S(f, "SE", s1)))
    sm = (a + b) / 2
    for k in range(6):                                                                  # gradas sobre la vereda
        f.caja(a + 0.4, b - 0.4, 0.0, 0.17 * (k + 1) + off, 3.0 - k * 0.5, 3.0 - (k + 1) * 0.5, "piedra", "#b8b0a3")
    f.caja(sm - 1.5, sm + 1.5, 1.0, 4.2 + off, -0.4, 0.0, "madera", "#2a2420")
    f.timpano_arco(sm, 1.5, 4.2 + off, -0.02, "madera", "#2a2420")
    f.arco(sm, 1.5, 0.3, 4.2 + off, 0.0, 0.25, "moldura", BL, segmentos=12)
    f.timpano_arco(sm, 1.8, 6.2 + off, 0.02, "vidrio", "#4f6f7f")                        # luneto alto
    f.arco(sm, 1.8, 0.2, 6.2 + off, 0.0, 0.12, "moldura", BL, segmentos=12)
    f.caja(b - 3.4, b - 0.3, 6.0 + off, 8.4 + off, 0.0, 0.9, "muro", "#e8c64a")           # galería amarilla
    f.caja(b - 3.3, b - 0.4, 6.4 + off, 8.0 + off, 0.9, 0.92, "vidrio")
    # muros laterales de la entrada hasta la línea de fachada
    for x in (a, b):
        f.caja(x - 0.2, x + 0.2, 0.0, 9.5 + off, 0.0, 3.0, "muro", BL)
    c.objeto(col)


def mercado_dos_filas(s0, s1):
    """Mercado bajo (R0055): fila de lunetos arriba y fila de arcos más chicos a media altura, locales con toldos."""
    c, f, off, otras, zb, zr = cuerpo("SE", "SE_mercado_arcos", s0, s1, 8.4)
    a, b = sorted((S(f, "SE", s0), S(f, "SE", s1)))
    n = max(1, round((b - a) / 3.8))
    paso = (b - a) / n
    for k in range(n):
        sm = a + (k + 0.5) * paso
        tienda(f, sm - paso / 2 + 0.25, sm + paso / 2 - 0.25, off, RND,
               toldo=RND.choice(["#f1eee6", "#3f6fb0", "#e9e2d2"]), vuelo=1.4)
        f.timpano_arco(sm, 1.0, 3.6 + off, 0.02, "vidrio", "#3f5a63")                      # arcos bajos
        f.arco(sm, 1.0, 0.14, 3.6 + off, 0.0, 0.08, "moldura", BL, segmentos=10)
        f.timpano_arco(sm, min(1.6, paso / 2 - 0.25), 5.6 + off, 0.02, "vidrio", RND.choice(VIDRIOS))
        f.arco(sm, min(1.6, paso / 2 - 0.25), 0.16, 5.6 + off, 0.0, 0.09, "moldura", BL, segmentos=12)
    f.caja(a, b, 3.35 + off, 3.6 + off, 0.0, 0.25, "moldura", BL)
    A_.cornisa(f, 7.9 + off, vuelo=0.22, alto=0.28, s0=a, s1=b, color=BL)
    A_.parapeto(f, 8.15 + off, alto=0.45, s0=a, s1=b, color=BL)
    c.objeto(col)


def moderno(lado, nombre, s0, s1, pisos, color=BL, bandas=True, balcones=False, tejadito=False, banda_color=None,
            letreros=(), alto_pb=3.6, vidriado=False, cortinas=True, retiro_ultimo=False):
    """Edificio moderno de 3–5 plantas (R0056–R0059, R0063, R0072–73): ventanas corridas o vidriado, antepechos,
    cortinas metálicas o vidrieras abajo."""
    alto = alto_pb + 3.0 * (pisos - 1)
    c, f, off, otras, zb, zr = cuerpo(lado, nombre, s0, s1, alto, color=color)
    a, b = sorted((S(f, lado, s0), S(f, lado, s1)))
    for fa in [f] + otras:
        aa, bb = (a, b) if fa is f else (0.2, fa.largo - 0.2)
        if bb - aa < 1.5:
            continue
        ofa = zr - fa.suelo
        for p in range(1, pisos):
            h = alto_pb + 3.0 * (p - 1) + ofa
            if retiro_ultimo and p == pisos - 1:
                fa.caja(aa, bb, h, h + 1.0, -1.4, -1.3, "vidrio")                          # baranda de vidrio
                fa.caja(aa + 0.3, bb - 0.3, h, h + 2.6, -1.6, -1.5, "vidrio")
                continue
            fa.caja(aa - 0.05, bb + 0.05, h - 0.12, h + 0.95, 0.0, 0.45 if balcones else 0.12, "muro", color)
            if vidriado or bandas:
                fa.caja(aa + 0.15, bb - 0.15, h + 0.95, h + 2.75, 0.0, 0.03, "vidrio")
                k = aa + 0.15
                while k <= bb - 0.1:
                    fa.caja(k - 0.035, k + 0.035, h + 0.95, h + 2.75, 0.0, 0.07, "marco_ventana", "#e6e8ea")
                    k += 0.95 if vidriado else 1.25
            else:
                nv = max(1, round((bb - aa) / 2.4))
                for j in range(nv):
                    sm = aa + (bb - aa) * (j + 0.5) / nv
                    fa.caja(sm - 0.8, sm + 0.8, h + 1.0, h + 2.6, 0.0, 0.03, "vidrio")
                    fa.caja(sm - 0.88, sm + 0.88, h + 0.92, h + 1.0, 0.0, 0.12, "moldura", "#e6e2d8")
        fa.caja(aa - 0.05, bb + 0.05, alto + ofa, alto + 0.6 + ofa, 0.0, 0.1, "muro", color)   # pretil
        if banda_color:
            fa.caja(aa, bb, alto_pb + 3.0 + ofa - 0.12, alto_pb + 3.0 + 0.95 + ofa, 0.13, 0.16, "letrero", banda_color)
        # planta baja: cortinas metálicas y vidrieras
        k = aa + 0.2
        while k < bb - 1.4:
            e = min(bb - 0.2, k + RND.uniform(2.8, 3.8))
            if cortinas and RND.random() < 0.45:
                cortina_metalica(fa, (k + e) / 2, ancho=e - k - 0.2, alto=2.9 + ofa, h0=0.0)
            else:
                vidriera(fa, k + 0.1, e - 0.1, ofa, letrero_col=RND.choice(
                    ["#2f5fa8", "#c9302c", "#f5f2ea", "#1e1e22", "#3a8a4a", "#e8b23a"]))
            k = e
        fa.caja(aa - 0.1, bb + 0.1, alto_pb - 0.25 + ofa, alto_pb + ofa, 0.0, 0.6, "muro", color)   # marquesina
    for sl, col_l in letreros:
        x = S(f, lado, sl)
        letrero(f, x - 1.4, x + 1.4, alto_pb + 0.15 + off, alto_pb + 0.85 + off, col_l, d=0.62)
    if tejadito:                                                    # tejadito rojo a cuatro aguas en la azotea (R0057)
        sm = (a + b) / 2
        p = f.punto(sm, alto + off, -3.0)
        c.cilindro(p.x, p.y, p.z, p.z + 2.6, 2.2, "teja", "#b5563a", lados=4, radio_arriba=0.05)
        c.cilindro(p.x, p.y, p.z - 0.01, p.z + 0.6, 2.0, "muro", color, lados=4)
    c.objeto(col)
    return f, off


# =============================================================================== LADO NO
def colonial(nombre, s0, s1, pisos=2, color=BL, balcones=True, alero=True, mirador_s=None, locales=None,
             zocalo="#b9a48a", alto_piso=4.2, ventanas=None, cornisas_vent=True):
    """Casa colonial de 1–2 plantas: alero de tejas con canes, ventanas de madera con balcón de hierro y guardapolvo,
    locales abajo (R0067–R0079)."""
    alto = pisos * alto_piso
    c, f, off, otras, zb, zr = cuerpo("NO", nombre, s0, s1, alto, color=color, techo="plano")
    a, b = sorted((S(f, "NO", s0), S(f, "NO", s1)))
    for fa in [f] + otras:
        aa, bb = (a, b) if fa is f else (0.3, fa.largo - 0.3)
        if bb - aa < 1.5:
            continue
        ofa = zr - fa.suelo
        A_.zocalo(fa, 0.6 + ofa, s0=aa, s1=bb, color=zocalo, sillares=False, desde=zb - 0.6 - fa.suelo)
        nv = ventanas or max(1, round((bb - aa) / 3.4))
        vs = [aa + (bb - aa) * (j + 0.5) / nv for j in range(nv)] if fa is f else \
            [aa + (bb - aa) * (j + 0.5) / max(1, round((bb - aa) / 3.4)) for j in range(max(1, round((bb - aa) / 3.4)))]
        if pisos >= 2:
            for v in vs:
                if mirador_s is not None and fa is f and abs(v - S(f, "NO", mirador_s)) < 2.6:
                    continue
                A_.ventana(fa, v, alto_piso + 0.35 + ofa, ancho=1.15, alto=2.1, moldura="moldura", color_moldura=color,
                           carpinteria="madera", color_carpinteria=MADERA)
                if balcones:
                    A_.balcon_hierro(fa, v - 0.85, v + 0.85, alto_piso + 0.35 + ofa, vuelo=0.55)
                if cornisas_vent:
                    fa.caja(v - 0.85, v + 0.85, alto_piso + 2.6 + ofa, alto_piso + 2.8 + ofa, 0.0, 0.16, "moldura", color)
                    fa.caja(v - 0.35, v + 0.35, alto_piso + 2.8 + ofa, alto_piso + 3.1 + ofa, 0.0, 0.1, "moldura", color)
            fa.caja(aa, bb, alto_piso - 0.05 + ofa, alto_piso + 0.15 + ofa, 0.0, 0.12, "moldura", color)
        if alero:
            A_.alero_tejas(fa, alto + ofa, vuelo=0.9, fondo=2.5, s0=aa - 0.05, s1=bb + 0.05)
        else:
            A_.cornisa(fa, alto - 0.3 + ofa, vuelo=0.25, alto=0.3, s0=aa, s1=bb, color=color)
            A_.parapeto(fa, alto + ofa, alto=0.5, s0=aa, s1=bb, color=color)
        # planta baja: locales
        cols = locales or ["#2f5fa8", "#1e1e22", "#c9302c", "#f5f2ea", "#3a8a4a"]
        for j, v in enumerate(vs):
            w = min(2.8, (bb - aa) / len(vs) - 0.5)
            if j % 3 == 1 and fa is f:
                A_.puerta(fa, v, ancho=1.5, alto=2.8 + ofa, color=MADERA, moldura="moldura", color_moldura=color)
            else:
                w = min(w, 2.2)                                    # vanos separados en muro blanco (casonas)
                vidriera(fa, v - w / 2, v + w / 2, ofa, alto=2.7, letrero_col=cols[j % len(cols)])
                if fa is f and RND.random() < 0.5:
                    toldo(fa, v - w / 2, v + w / 2, ofa, RND, toldo=RND.choice(["#f1eee6", "#e9e2d2", "#2f5fa8"]), vuelo=1.0)
    if mirador_s is not None:
        x = S(f, "NO", mirador_s)
        mirador(f, x, alto_piso - 0.2 + off, ancho=5.2, alto=3.4, vuelo=1.25, base=("madera", "#4a2a1a"),
                madera=("marco_ventana", "#4a2a1a"), antepecho=("madera", "#5a3020"))
        f.caja(x - 2.75, x + 2.75, alto_piso + 3.2 + off, alto_piso + 3.45 + off, 0.0, 1.45, "madera", "#3a2216")  # cornisa
        for dx in (-2.0, -0.7, 0.7, 2.0):                                                   # ménsulas talladas
            f.caja(x + dx - 0.12, x + dx + 0.12, alto_piso - 0.9 + off, alto_piso - 0.2 + off, 0.0, 1.0, "madera", "#3a2216")
    c.objeto(col)
    return c, f, off


def casa_tejas(nombre, s0, s1, pisos=1, color=BL, letrero_col="#c9302c", balcon=False, ladrillo_atras=False):
    """Casa baja de tejas (R0068–R0072): alero grande, un local abajo; a veces un piso alto angosto con balcón."""
    alto = 3.9 if pisos == 1 else 7.6
    c, f, off, otras, zb, zr = cuerpo("NO", nombre, s0, s1, alto, color=color, techo="plano")
    a, b = sorted((S(f, "NO", s0), S(f, "NO", s1)))
    A_.zocalo(f, 0.8 + off, s0=a, s1=b, color="#a8987f", sillares=False, desde=zb - 0.6 - f.suelo)
    sm = (a + b) / 2
    if pisos == 2:
        A_.ventana(f, sm, 4.2 + off, ancho=1.1, alto=2.2, moldura="moldura", color_moldura=color,
                   carpinteria="madera", color_carpinteria=MADERA)
        if balcon:
            A_.balcon_hierro(f, sm - 0.85, sm + 0.85, 4.2 + off, vuelo=0.5)
    vidriera(f, a + 0.4, b - 0.4, off, alto=2.6, letrero_col=letrero_col, marco="#5a4a3a")
    A_.alero_tejas(f, alto + off, vuelo=1.1, fondo=3.0, s0=a - 0.1, s1=b + 0.1)
    if ladrillo_atras:
        p = [P("NO", s0, 6.0), P("NO", s1, 6.0), P("NO", s1, 12.0), P("NO", s0, 12.0)]
        c.prisma(p, zr, zr + 9.5, "muro", "#b0604a")
    c.objeto(col)


def florencia(s0, s1):
    """SHOPPING FLORENCIA (R0074–R0075): angosto de 4 plantas, remate en punta (marco triangular blanco), dos calles de
    ventanales verticales de madera que suben tres plantas, balcón central con balaustrada y el letrero."""
    c, f, off, otras, zb, zr = cuerpo("NO", "NO_shopping_florencia", s0, s1, 14.6, color="#f3f0e8")
    a, b = sorted((S(f, "NO", s0), S(f, "NO", s1)))
    L = b - a
    MAR = "#6b4430"
    for x0 in (a + 0.4, a + 2.6, b - 4.6, b - 2.4):
        f.caja(x0, x0 + 2.0, 4.4 + off, 13.4 + off, 0.0, 0.35, "marco_ventana", MAR)
        f.caja(x0 + 0.12, x0 + 1.88, 4.6 + off, 13.2 + off, 0.36, 0.37, "vidrio")
        for h in (6.0, 7.6, 9.2, 10.8, 12.4):
            f.caja(x0, x0 + 2.0, h + off, h + 0.08 + off, 0.3, 0.42, "marco_ventana", MAR)
        f.caja(x0 - 0.15, x0 + 2.15, 13.4 + off, 13.75 + off, -0.1, 0.55, "teja", "#8a4a32")
    sm = (a + b) / 2
    for hb in (4.4, 7.4):                                                                # balcones de balaustrada
        f.caja(sm - 1.5, sm + 1.5, hb + off, hb + 0.2 + off, 0.0, 0.8, "piedra", "#f3f0e8")
        k = sm - 1.4
        while k < sm + 1.4:
            f.cilindro_vertical(k, hb + 0.2 + off, hb + 1.0 + off, 0.65, 0.05, "moldura", "#f6f4ef", lados=6)
            k += 0.22
        f.caja(sm - 1.5, sm + 1.5, hb + 1.0 + off, hb + 1.1 + off, 0.0, 0.8, "moldura", "#f6f4ef")
        A_.ventana(f, sm, hb + 0.3 + off, ancho=1.6, alto=2.2, moldura="moldura", color_moldura="#f6f4ef",
                   carpinteria="marco_ventana", color_carpinteria=MAR)
    letrero(f, sm - 1.6, sm + 1.6, 3.6 + off, 4.3 + off, "#5a2a1a", borde="#e9d9b0")          # SHOPPING FLORENCIA
    # remate en punta
    # marco triangular (contorno, no un triángulo macizo: de abajo se leía como una astilla blanca)
    for (x0, h0, x1, h1) in ((sm - 2.6, 14.6, sm, 17.0), (sm, 17.0, sm + 2.6, 14.6)):
        L_ = math.hypot(x1 - x0, h1 - h0)
        p_ = f.punto((x0 + x1) / 2, (h0 + h1) / 2 + off, 0.3)
        ang = math.atan2(h1 - h0, x1 - x0)
        ex = (f.u.x * math.cos(ang), f.u.y * math.cos(ang), math.sin(ang))
        c.caja_ejes((p_.x, p_.y, p_.z), ex, (f.n.x, f.n.y, 0), (-f.u.x * math.sin(ang), -f.u.y * math.sin(ang), math.cos(ang)),
                    L_ + 0.3, 0.3, 0.35, "moldura", "#f6f4ef")
    f.caja(sm - 2.7, sm + 2.7, 14.45 + off, 14.75 + off, 0.15, 0.45, "moldura", "#f6f4ef")
    tri = [f.punto(sm - 2.3, 14.75 + off, 0.2), f.punto(sm + 2.3, 14.75 + off, 0.2), f.punto(sm, 16.7 + off, 0.2)]
    c.poligono(tri, "teja", "#8a4a32", grosor=0.1, normal_extrusion=tuple(f.n))             # tímpano oscuro
    f.arco(sm, 0.5, 0.12, 15.0 + off, 0.25, 0.32, "moldura", "#c9a24a", segmentos=8, medio=False)
    vidriera(f, a + 0.3, sm - 1.2, off, letrero_col="#2f5fa8")
    vidriera(f, sm + 1.2, b - 0.3, off, letrero_col="#3a8a4a")
    f.caja(sm - 0.9, sm + 0.9, 0.0, 3.0 + off, -0.3, 0.0, "madera", "#2a2420")            # pasillo de la galería
    c.objeto(col)


def angosto_san_valentin(s0, s1):
    """Edificio angosto de 5 plantas con la gran banda de letrero (R0071)."""
    c, f, off, otras, zb, zr = cuerpo("NO", "NO_san_valentin", s0, s1, 15.0)
    a, b = sorted((S(f, "NO", s0), S(f, "NO", s1)))
    sm = (a + b) / 2
    letrero(f, a + 0.1, b - 0.1, 4.2 + off, 6.6 + off, "#2f8a8a", borde="#e9f2f2")
    for h in (7.2, 10.2):
        A_.ventana(f, sm - 0.9, h + off, ancho=1.0, alto=2.0, carpinteria="madera", color_carpinteria=MADERA)
        A_.ventana(f, sm + 0.9, h + off, ancho=1.0, alto=2.0, carpinteria="madera", color_carpinteria=MADERA)
    A_.balcon_hierro(f, sm - 1.6, sm + 1.6, 10.2 + off, vuelo=0.5)
    f.caja(a + 0.3, b - 0.3, 13.0 + off, 15.0 + off, -1.2, -1.0, "muro", BL)
    vidriera(f, a + 0.2, b - 0.2, off, letrero_col="#c9302c")
    toldo(f, a + 0.2, b - 0.2, off, RND, toldo="#e9e2d2", vuelo=1.0)
    c.objeto(col)


def clotilde(s0, s1):
    """SHOPPING Ma. CLOTILDE (R0070–R0071): 2 plantas altas, pilastras planas, tres grandes paneles de publicidad
    enmarcados, cornisa y pretil; abajo locales (Apple Store, Chalita) y vitrinas."""
    c, f, off, otras, zb, zr = cuerpo("NO", "NO_shopping_clotilde", s0, s1, 10.5)
    a, b = sorted((S(f, "NO", s0), S(f, "NO", s1)))
    n = max(2, round((b - a) / 4.2))
    paso = (b - a) / n
    for k in range(n + 1):
        A_.pilastra(f, a + k * paso, 0.0, 9.6 + off, ancho=0.55, vuelo=0.12, color=BL)
    for k in range(n):
        sm = a + (k + 0.5) * paso
        f.caja(sm - 1.2, sm + 1.2, 5.0 + off, 9.0 + off, 0.0, 0.14, "moldura", BL)          # marco del panel
        f.caja(sm - 1.05, sm + 1.05, 5.15 + off, 8.85 + off, 0.14, 0.15, "letrero",
               RND.choice(["#7fb03a", "#3a7fb0", "#2f2f3a", "#c9a24a"]))
        vidriera(f, sm - paso / 2 + 0.4, sm + paso / 2 - 0.4, off, alto=3.2,
                 letrero_col=RND.choice(["#1e1e22", "#2f5fa8", "#c9302c"]))
    letrero(f, (a + b) / 2 - 1.8, (a + b) / 2 + 1.8, 3.9 + off, 4.7 + off, "#5a3a2a", borde="#f2ead8")
    A_.cornisa(f, 9.6 + off, vuelo=0.3, alto=0.35, s0=a, s1=b, color=BL)
    A_.parapeto(f, 9.95 + off, alto=0.55, s0=a, s1=b, color=BL)
    c.objeto(col)


def largo_memphis(s0, s1):
    """Casa larga de 2 plantas (R0066–R0067): ventanas de madera de 3 hojas, un balcón, cornisa recta con pretil,
    abajo locales con toldo (Memphis), y Bata (letrero rojo) en el extremo."""
    c, f, off, otras, zb, zr = cuerpo("NO", "NO_memphis_bata", s0, s1, 8.6)
    a, b = sorted((S(f, "NO", s0), S(f, "NO", s1)))
    n = max(2, round((b - a) / 3.3))
    vs = [a + (b - a) * (j + 0.5) / n for j in range(n)]
    for j, v in enumerate(vs):
        A_.ventana(f, v, 5.0 + off, ancho=1.5, alto=1.8, carpinteria="madera", color_carpinteria=MADERA,
                   moldura="moldura", color_moldura=BL)
        if j == len(vs) // 2:
            A_.balcon_hierro(f, v - 1.0, v + 1.0, 5.0 + off, vuelo=0.5)
    A_.cornisa(f, 7.9 + off, vuelo=0.2, alto=0.25, s0=a, s1=b, color=BL)
    A_.parapeto(f, 8.15 + off, alto=0.45, s0=a, s1=b, color=BL)
    f.caja(a, b, 3.8 + off, 4.05 + off, 0.0, 0.1, "moldura", "#5a4a3a")                      # cableado/viga
    for j, v in enumerate(vs):
        w = (b - a) / n - 0.5
        bata = j >= n - 2
        vidriera(f, v - w / 2, v + w / 2, off, alto=3.0, letrero_col="#d0202a" if bata else None, marco="#c8c8c8" if bata else "#3b3f42")
    toldo(f, a + 0.3, (a + b) / 2, off, RND, toldo="#e9e2d2", vuelo=1.2)
    letrero(f, a + 1.5, a + 3.8, 5.0 + off, 5.8 + off, "#e8a020", borde="#2a2a2a")          # Memphis
    c.objeto(col)


def guadalupe(s0, s1):
    """GALERÍA GUADALUPE (R0064–R0066): cuerpo angosto de 4 plantas con remate de volutas escalonado y óculo, dos
    balcones de hierro con ménsulas, pilastras con filete ocre; el pasillo de la galería abajo."""
    c, f, off, otras, zb, zr = cuerpo("NO", "NO_galeria_guadalupe", s0, s1, 12.6)
    a, b = sorted((S(f, "NO", s0), S(f, "NO", s1)))
    sm = (a + b) / 2
    OCRE = "#b5794a"
    for x in (a + 0.25, b - 0.25):
        f.caja(x - 0.25, x + 0.25, 0.0, 12.6 + off, 0.0, 0.15, "moldura", BL)
        f.caja(x - 0.06, x + 0.06, 3.5 + off, 12.6 + off, 0.15, 0.17, "pintura_acento", OCRE)
    for h in (4.4, 7.5, 10.2):
        A_.ventana(f, sm, h + off, ancho=1.2, alto=2.2, carpinteria="madera", color_carpinteria=MADERA, moldura="moldura",
                   color_moldura=BL)
        if h < 10:
            A_.balcon_hierro(f, sm - 1.0, sm + 1.0, h + off, vuelo=0.6)
    # remate escalonado con volutas
    f.caja(a, b, 12.6 + off, 13.2 + off, 0.0, 0.2, "moldura", BL)
    f.caja(sm - 1.4, sm + 1.4, 13.2 + off, 14.4 + off, 0.0, 0.2, "muro", BL)
    f.caja(sm - 0.8, sm + 0.8, 14.4 + off, 15.2 + off, 0.0, 0.2, "muro", BL)
    f.arco(sm - 1.4, 0.35, 0.12, 13.2 + off, 0.15, 0.25, "pintura_acento", OCRE, segmentos=6)
    f.arco(sm + 1.4, 0.35, 0.12, 13.2 + off, 0.15, 0.25, "pintura_acento", OCRE, segmentos=6)
    f.arco(sm, 0.35, 0.1, 13.6 + off, 0.2, 0.26, "pintura_acento", OCRE, segmentos=8, medio=False)
    letrero(f, sm - 1.0, sm + 1.0, 6.3 + off, 7.1 + off, "#7a5a2a", borde="#e9d29a")            # GALERÍA GUADALUPE
    f.caja(sm - 1.0, sm + 1.0, 0.0, 3.2 + off, -0.4, 0.0, "madera", "#2a2420")                # pasillo
    f.caja(a + 0.5, sm - 1.2, 0.0, 3.0 + off, 0.0, 0.06, "marco_ventana", "#3b3f42")
    c.objeto(col)


def balcones_huici(nombre, s0, s1, pisos=3, color=BL, banda=None, letreros=()):
    """Edificios de 3 plantas con muchos balcones sobre ménsulas y puertas-ventana de madera (Antonio's, GALERÍA HUICI,
    Samsung — R0063–R0065): secuencia de vanos D-V-D-V… según la foto, pretil con cornisa."""
    alto = 3.8 + 3.2 * (pisos - 1)
    c, f, off, otras, zb, zr = cuerpo("NO", nombre, s0, s1, alto, color=color)
    a, b = sorted((S(f, "NO", s0), S(f, "NO", s1)))
    n = max(2, round((b - a) / 2.3))
    vs = [a + (b - a) * (j + 0.5) / n for j in range(n)]
    for p in range(1, pisos):
        h = 3.8 + 3.2 * (p - 1) + 0.3 + off
        for j, v in enumerate(vs):
            puerta_v = j % 2 == 0
            A_.ventana(f, v, h, ancho=1.15, alto=2.4 if puerta_v else 1.6, carpinteria="madera", color_carpinteria="#4a2a1a",
                       moldura="moldura", color_moldura="#e6e2d8")
            f.caja(v - 0.5, v + 0.5, h + 0.1, h + (2.3 if puerta_v else 1.5), 0.0, 0.06, "madera", "#5a3020")   # hojas
            if puerta_v:
                f.caja(v - 0.75, v + 0.75, h - 0.15, h, 0.0, 0.65, "moldura", "#ece8df")      # losa del balcón
                for sx in (-0.5, 0.0, 0.5):                                                    # ménsulas
                    f.caja(v + sx - 0.07, v + sx + 0.07, h - 0.55, h - 0.15, 0.0, 0.55, "moldura", "#ece8df")
                k_ = v - 0.7
                while k_ <= v + 0.71:                                                           # baranda negra
                    f.caja(k_ - 0.025, k_ + 0.025, h, h + 1.0, 0.58, 0.63, "hierro", "#1f1c1a")
                    k_ += 0.14
                for dd_ in (0.0, 0.6):
                    f.caja(v - 0.72 if dd_ else v - 0.72, v + 0.72, h + 0.95, h + 1.04, dd_, 0.65, "hierro", "#1f1c1a")
                f.caja(v - 0.72, v + 0.72, h + 0.3, h + 0.34, 0.58, 0.63, "hierro", "#1f1c1a")
    if banda:
        f.caja(a, b, 3.5 + off, 3.8 + off, 0.0, 0.08, "pintura_acento", banda)
    A_.cornisa(f, alto - 0.2 + off, vuelo=0.25, alto=0.25, s0=a, s1=b, color=color)
    A_.parapeto(f, alto + 0.05 + off, alto=0.5, s0=a, s1=b, color=color)
    k = a + 0.2
    j = 0
    while k < b - 1.4:
        e = min(b - 0.2, k + 3.2)
        cols = [x[1] for x in letreros] or ["#1e1e22", "#f5f2ea", "#c9302c", "#2f5fa8"]
        vidriera(f, k + 0.1, e - 0.1, off, alto=3.0, letrero_col=cols[j % len(cols)])
        k = e
        j += 1
    c.objeto(col)


# =============================================================================== mobiliario de la peatonal
# tramos con bolardos (metros desde el bordillo de Ravelo), por vereda, según las fotos de Peatonal/
BOLARDOS = {"NO": [(8.0, 27.0), (64.0, 95.0), (117.0, 138.0)], "SE": [(8.0, 19.0), (64.0, 95.0), (117.0, 138.0)]}


def mobiliario():
    c = Constructor("PEATONAL_vereda")
    for lado in ("NO", "SE"):
        v = PM.VEREDA[lado]
        # bolardos negros junto al bordillo SOLO en los tramos donde salen en el recorrido Peatonal/ (usuario R0132:
        # "solo hay palos en algunos tramos"); metros desde Ravelo, una vista cada ~10 m:
        #   09-04-09/09-04-22 (≈10–25 m), 09-05-17…09-05-40 (≈65–95 m), 09-06-04/09-06-13 (≈118–138 m)
        for t0, t1 in BOLARDOS[lado]:
            k = S0[lado] + t0
            while k < min(S0[lado] + t1, S1[lado] - 1.0):
                x, y = P(lado, k, -(v - 0.35))
                z = altura_suelo(x, y) + 0.18
                c.cilindro(x, y, z, z + 0.85, 0.075, "hierro", "#232020", lados=8)
                c.esfera(x, y, z + 0.87, 0.085, "hierro", "#232020", segmentos=6)
                k += 2.2
    # faroles ornamentales de globo junto al bordillo SE (R0047, R0049, R0051, R0053–56, R0058)
    for s in range(int(S0["SE"] + 14), int(S1["SE"] - 4), 17):
        x, y = P("SE", s, -(PM.VEREDA["SE"] - 0.9))
        z = altura_suelo(x, y) + 0.18
        c.cilindro(x, y, z, z + 0.5, 0.16, "hierro", "#2a3a30", lados=8)
        c.cilindro(x, y, z + 0.5, z + 3.9, 0.07, "hierro", "#2a3a30", lados=8)
        c.cilindro(x, y, z + 3.9, z + 4.1, 0.2, "hierro", "#2a3a30", lados=8)
        c.esfera(x, y, z + 4.45, 0.34, "vidrio", "#f2e6b8", segmentos=8)
        c.cilindro(x, y, z + 4.7, z + 4.85, 0.25, "hierro", "#2a3a30", lados=8, radio_arriba=0.06)
    # bancos de madera de espaldas a la calle, frente al mercado (R0047–R0049)
    nx, ny = NOUT("SE")
    tx, ty = -ny, nx
    for s in (S0["SE"] + 22, S0["SE"] + 31, S0["SE"] + 40):
        x, y = P("SE", s, -(PM.VEREDA["SE"] - 1.3))
        z = altura_suelo(x, y) + 0.18
        c.caja_ejes((x, y, z + 0.44), (tx, ty, 0), (nx, ny, 0), (0, 0, 1), 1.9, 0.45, 0.06, "madera", "#6e4a2e")
        c.caja_ejes((x + nx * 0.22, y + ny * 0.22, z + 0.74), (tx, ty, 0), (nx, ny, 0), (0, 0, 1), 1.9, 0.05, 0.42, "madera", "#6e4a2e")
        for sg in (-0.8, 0.8):
            c.caja_ejes((x + tx * sg, y + ty * sg, z + 0.22), (tx, ty, 0), (nx, ny, 0), (0, 0, 1), 0.06, 0.45, 0.44, "hierro")
    c.objeto(col)


def pino(s, d, alto=15.0, semilla=0):
    """Pino grande de vereda (R0053–R0055, Peatonal/ 09-04-58 a 09-05-32): tronco alto, copa en pisos irregulares de
    ramas oscuras desde los 4 m (se camina por debajo)."""
    c = Constructor(f"PEATONAL_pino_{int(s)}")
    rnd = random.Random(semilla)
    x, y = P("SE", s, d)
    z = altura_suelo(x, y) + 0.18
    c.cilindro(x, y, z - 0.2, z + alto * 0.85, 0.34, "tronco", "#4a3626", lados=8, radio_arriba=0.12)
    c.cilindro(x, y, z - 0.05, z + 0.9, 0.38, "muro", "#f4f2ec", lados=8)
    c.cilindro(x, y, z - 0.1, z + 0.2, 0.75, "piedra", "#b8afa3", lados=8)                  # alcorque
    # copa rala y alta (casuarina/pino de las fotos): ramas sueltas con mechones colgantes, se ve el cielo entre ellas
    for k in range(9):
        h = z + 6.0 + (alto - 6.5) * k / 8
        r = max(0.8, (alto - (h - z)) * 0.38) * rnd.uniform(0.8, 1.2)
        for j in range(3):
            a = rnd.uniform(0, 6.28)
            px, py = x + math.cos(a) * r, y + math.sin(a) * r
            dx_, dy_ = px - x, py - y
            c.caja_ejes(((x + px) / 2, (y + py) / 2, h - 0.2), (dx_ / (r or 1), dy_ / (r or 1), 0), (-dy_ / (r or 1), dx_ / (r or 1), 0),
                        (0, 0, 1), r, 0.08, 0.08, "tronco", "#4a3626")
            for q in range(4):
                t = 0.3 + 0.24 * q
                c.esfera(x + dx_ * t, y + dy_ * t, h - 0.1 - q * 0.18, rnd.uniform(0.55, 0.85), "follaje",
                         "#3a5a30" if (k + j + q) % 2 else "#4a6a38", segmentos=6)
    c.objeto(col)


def carpa_naranja(s):
    """Carpa naranja sobre la vereda del Mercado (R0049–R0050)."""
    c = Constructor("PEATONAL_carpa")
    nx, ny = NOUT("SE")
    tx, ty = -ny, nx
    x, y = P("SE", s, -2.2)
    z = altura_suelo(x, y) + 0.18
    for a in (-1, 1):
        for b in (-1, 1):
            c.cilindro(x + tx * a * 1.4 + nx * b * 1.1, y + ty * a * 1.4 + ny * b * 1.1, z, z + 2.4, 0.035, "metal", "#8a8f93", lados=5)
    c.poligono([(x + tx * -1.7 + nx * -1.4, y + ty * -1.7 + ny * -1.4, z + 2.4), (x + tx * 1.7 + nx * -1.4, y + ty * 1.7 + ny * -1.4, z + 2.4),
                (x + tx * 1.7 + nx * 1.4, y + ty * 1.7 + ny * 1.4, z + 2.4), (x + tx * -1.7 + nx * 1.4, y + ty * -1.7 + ny * 1.4, z + 2.4)],
               "letrero", "#e8823a", grosor=0.05, normal_extrusion=(0, 0, 1))
    c.cilindro(x, y, z + 2.4, z + 2.9, 1.9, "letrero", "#e8823a", lados=4, radio_arriba=0.1)
    c.objeto(col)


# =============================================================================== secuencia (s desde el eje en Ravelo)
s0se, s1se = S0["SE"], S1["SE"]
s0no, s1no = S0["NO"], S1["NO"]
L_SE = s1se - s0se
L_NO = s1no - s0no
print("[PEATONAL] largo SE", round(L_SE, 1), "NO", round(L_NO, 1))


def fse(x):
    return s0se + x


def fno(x):
    return s0no + x


# ---- LADO SE (s desde el bordillo de Ravelo; la placita de la esquina es de M013 y ocupa ~6 m)
mercado_lunetos(fse(6.0), fse(46.0), entrada=fse(40.0), mayorista=(fse(14.0), fse(31.0)))
bloque_dobleces(fse(46.0), fse(84.0), entrada=fse(72.0))
entrada_escalinata(fse(84.0), fse(92.0))
mercado_dos_filas(fse(92.0), fse(106.0))
moderno("SE", "SE_vidriado_irom", fse(106.0), fse(114.0), 5, vidriado=True, balcones=True,
        letreros=((fse(110.0), "#e8c64a"),))
moderno("SE", "SE_sima", fse(114.0), fse(123.5), 5, bandas=False, balcones=True, tejadito=True,
        letreros=((fse(118.0), "#e8c64a"),))
moderno("SE", "SE_edificio_cn", fse(123.5), fse(131.0), 4, bandas=True, color="#f1efe8")
moderno("SE", "SE_corag", fse(131.0), s1se, 4, bandas=True, banda_color="#2a6fa8", retiro_ultimo=True)

# ---- LADO NO
colonial("NO_casona_esquina_feria", s0no, fno(24.0), mirador_s=s0no + 2.6, locales=["#2f6fd0", "#1e1e22", "#c9302c"],
         ventanas=5)
colonial("NO_casa_angosta", fno(24.0), fno(29.0), ventanas=1, locales=["#2f5fa8"])
florencia(fno(29.0), fno(38.0))
moderno("NO", "NO_moderno_san_agustin", fno(38.0), fno(52.0), 5, bandas=True, color="#efece4", retiro_ultimo=True,
        cortinas=False, letreros=((fno(48.0), "#c9302c"), (fno(41.0), "#e9a0c0")))
casa_tejas("NO_ferreteria", fno(52.0), fno(58.0), ladrillo_atras=True)
angosto_san_valentin(fno(58.0), fno(63.0))
clotilde(fno(63.0), fno(80.0))
casa_tejas("NO_libreria_torre", fno(80.0), fno(85.0), pisos=2, letrero_col="#e86a2a")
casa_tejas("NO_coca_cola", fno(85.0), fno(90.0), letrero_col="#c9202a")
casa_tejas("NO_casita_balcon", fno(90.0), fno(94.5), pisos=2, balcon=True, letrero_col="#c9302c")
casa_tejas("NO_la_comelona", fno(94.5), fno(99.0), letrero_col="#f5f2ea", ladrillo_atras=True)
largo_memphis(fno(99.0), fno(114.0))
guadalupe(fno(114.0), fno(118.5))
balcones_huici("NO_antonios", fno(118.5), fno(124.0), pisos=3, letreros=((0, "#f5f2ea"),))
balcones_huici("NO_galeria_huici", fno(124.0), fno(133.0), pisos=3, banda="#c9a24a")
balcones_huici("NO_samsung", fno(133.0), fno(138.0), pisos=4, color="#efe2c4", letreros=((0, "#1e1e22"),))
moderno("NO", "NO_esquina_zte", fno(138.0), s1no, 3, bandas=False, color="#f4f3ef", cortinas=True,
        letreros=((s1no - 3.0, "#e9e6e0"),))

# ---- vereda: bolardos, faroles, bancos, pinos, puestos, carpa
mobiliario()
for s, dd, h in ((fse(88.0), -3.4, 16.0), (fse(95.0), -4.5, 17.0), (fse(102.0), -4.4, 15.5)):
    pino(s, dd, alto=h, semilla=int(s))
carpa_naranja(fse(52.0))
pz = Constructor("PEATONAL_puestos")
# puestos con lona a lo largo de todo el frente del Mercado (Peatonal/: la vereda SE está cubierta de puestos)
for s in range(int(fse(8)), int(fse(128)), 3):
    if RND.random() < 0.7:
        puesto(pz, "SE", s + RND.uniform(0, 1.0), -1.5, lona=RND.choice(["#2f5fa8", "#f1eee6", "#3f6fb0", "#e9e2d2"]))
for s in (fse(90.0), fse(97.0), fse(108.0)):
    quitasol(pz, "SE", s, -2.6, RND.choice(["#3f6fb0", "#e9a0c0", "#c9302c"]))
vitrinas_vereda(pz, "NO", s0no + 2, s1no - 2, d=-0.6)
vitrinas_vereda(pz, "SE", fse(106.0), s1se - 2, d=-0.7)
# letreros salientes (bandera) sobre las veredas, como en todas las vistas de Peatonal/: cajas de luz a 3–4,5 m que
# vuelan 0,9 m sobre la vereda (dentro del vuelo permitido)
for lado in ("NO", "SE"):
    nx, ny = NOUT(lado)
    tx, ty = -ny, nx
    k = (S0[lado] + 6) if lado == "NO" else fse(100)
    while k < S1[lado] - 3:
        if RND.random() < 0.55:
            x, y = P(lado, k, -0.5)
            z = altura_suelo(*P(lado, k, 0)) + RND.uniform(3.2, 4.6)
            alto = RND.uniform(0.5, 0.9)
            col_l = RND.choice(["#c9302c", "#2f5fa8", "#f5f2ea", "#e8b23a", "#3a8a4a", "#1e1e22", "#e86a2a"])
            pz2 = pz if False else None
            sl = Constructor(f"PEATONAL_letrero_{lado}_{int(k)}")
            sl.caja_ejes((x, y, z), (nx, ny, 0), (tx, ty, 0), (0, 0, 1), 0.8, 0.12, alto, "letrero", col_l)
            sl.caja_ejes((x - nx * 0.05, y - ny * 0.05, z), (nx, ny, 0), (tx, ty, 0), (0, 0, 1), 0.66, 0.14, alto - 0.14,
                         "letrero", "#f2efe6")
            sl.caja_ejes((x + nx * 0.42, y + ny * 0.42, z + alto / 2 - 0.05), (nx, ny, 0), (tx, ty, 0), (0, 0, 1), 0.12, 0.05, 0.05,
                         "hierro", "#2f2b28")
            sl.objeto(col)
        k += RND.uniform(3.0, 6.0)

# postes de concreto junto al bordillo NO, cables de poste a poste y acometidas a ménsulas de las dos fachadas
# (Peatonal/: maraña de cables cruzando la calle). Coherencia: los cables solo van poste–poste o poste–ménsula.
from base_mobiliario import cable  # noqa: E402
cc = Constructor("PEATONAL_cables")
postes = []
for s in range(int(S0["NO"] + 12), int(S1["NO"] - 4), 26):
    x, y = P("NO", s, -(PM.VEREDA["NO"] - 0.4))
    z = altura_suelo(x, y) + 0.18
    cc.cilindro(x, y, z - 0.3, z + 9.0, 0.16, "piedra", "#a9a59c", lados=8, radio_arriba=0.1)
    nx, ny = NOUT("NO")
    tx, ty = -ny, nx
    cc.caja_ejes((x, y, z + 8.4), (nx, ny, 0), (tx, ty, 0), (0, 0, 1), 1.4, 0.1, 0.1, "madera", "#5a4a3a")   # cruceta
    postes.append((s, x, y, z))
for (s0_, x0, y0, z0), (s1_, x1, y1, z1) in zip(postes, postes[1:]):
    for k in range(5):
        h = 7.2 + k * 0.3
        cable(cc, (x0, y0, z0 + h), (x1, y1, z1 + h), RND.uniform(0.4, 0.9))
for s_, x, y, z in postes:
    for k in range(4):                                   # acometidas a la fachada de enfrente (SE)
        sf = s_ + RND.uniform(-6, 6)
        fx, fy = P("SE", sf, -0.25)
        fz = altura_suelo(fx, fy) + RND.uniform(5.5, 7.0)
        cable(cc, (x, y, z + 7.0 + k * 0.25), (fx, fy, fz), RND.uniform(0.3, 0.7), radio=0.014)
        cc.caja(fx - 0.06, fy - 0.06, fz - 0.15, fx + 0.06, fy + 0.06, fz + 0.05, "hierro", "#2f2b28")       # ménsula
    for k in range(2):                                   # y a la propia
        sf = s_ + RND.uniform(-5, 5)
        fx, fy = P("NO", sf, -0.25)
        fz = altura_suelo(fx, fy) + RND.uniform(5.0, 6.0)
        cable(cc, (x, y, z + 7.4 + k * 0.25), (fx, fy, fz), RND.uniform(0.2, 0.5), radio=0.014)
        cc.caja(fx - 0.06, fy - 0.06, fz - 0.15, fx + 0.06, fy + 0.06, fz + 0.05, "hierro", "#2f2b28")
cc.objeto(col)

exportar(AGENTE, MID)

# cámaras: las de las correcciones de la calle
import json  # noqa: E402
CAMS = []
_R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "coordinacion", "revisiones")
for k in list(range(45, 80)) + [87]:
    rid = f"R{k:04d}"
    p = os.path.join(_R, rid, "revision.json")
    if not os.path.exists(p):
        continue
    e = json.load(open(p))["escena"]
    o = e["camara"]["lienzo"]
    rb = math.radians(e["camara"]["rumbo_grados"])
    CAMS.append((rid, (o["x"], o["y"], o["z"]), (o["x"] + math.sin(rb) * 15, o["y"] + math.cos(rb) * 15, o["z"] + 3)))
if "--sin-render" not in sys.argv:
    revisar(AGENTE, MID, fotos=[], camaras_extra=CAMS)
