"""Calle Colón, frente NE, desde la esquina de Rafael Bustillo hasta el contrafuerte de esquina de San Felipe Neri.
Rehecho desde cero el 2026-11-23 (pedido del usuario: "deshacer toda esa parte" y hacerlo "muy estricto"), con las
fotos R0170–R0174 estudiadas a resolución completa.

Medidas: t = metros a lo largo del eje de Colón desde su cruce con Bustillo (-441,1, -415,3), hacia el SE. La línea de
fachada NE está a 7,5 m del eje (calle de 15 m). Bustillo es perpendicular y mide 11,5 m: la esquina queda en t = 5,75.
San Felipe empieza en t = 67,7 (huella OSM corregida). Los anchos salen de las fotos (alto de piso o de puerta como
escala): A 22,9 + B 12,5 + C 11,1 + D 15,5 = 62 m, justo lo que hay entre la esquina y San Felipe.

A. CASONA DE ESQUINA (R0170, R0171, R0172 a la izquierda), t 5,75–28,6. Dos plantas de cal blanca. Pilastras beige
   (#d8c29a) que parten el frente en cuatro módulos de 5,6 m; cadena de sillares beige en la esquina; faja beige entre
   plantas; cornisa beige con friso de modillones y pretil rosado con urnas sobre las pilastras; zócalo de sillares
   pardos de 1,4 m. Módulo 1 (esquina): MIRADOR de madera rojo oscuro que arranca en la esquina, de 4,2 m, con tres
   paños de 4×3 vidrios, antepecho de tableros, cinco canes curvos y tejadillo de tejas; abajo ventana alta con reja y
   marco beige con cornisita de dentículos. Módulo 2: igual abajo, arriba puerta-ventana con balcón forjado. Módulo 3:
   portón de garaje de tablas rojizas, balcón arriba. Módulo 4: puerta de madera con reja y marco beige, balcón arriba.
   Farol de brazo sobre la pilastra entre los módulos 3 y 4. Sobre Bustillo la casona sigue con el mismo orden (sin
   foto de ese lado: dos módulos iguales al 2).
B. CASA DE MODILLONES BLANCOS (R0172 derecha, R0173 izquierda), t 28,6–41,1. Misma altura, cal blanca SIN pilastras;
   cornisa blanca de modillones y pretil con una urna; faja blanca. Arriba dos puertas-ventana con marco y cornisita
   blancos y balcón forjado (a 3,0 y 9,3 m). Abajo, bajo el primer balcón, puerta vidriera de dos hojas; bajo el
   segundo, vitrina de local con cartel blanco y, a su derecha, puerta de madera de dos hojas (n.º 65). Zócalo pardo.
C. CASA DE TIENDAS (R0173), t 41,1–52,2. Alero de teja sin canes; cal blanca con grietas; arriba dos ventanas
   rectangulares sin moldura con baranda de barrotes a ras; abajo la entrada de la tienda (marco ancho de piedra ocre,
   persiana roja enrollada, puerta de vidrio) y una vitrina con el mismo marco, persiana roja y reja; zócalo alto de
   sillería ocre anaranjada. Farol de brazo a la derecha.
D. CASA ANTIGUA (R0174), t 52,2–67,7, pegada al contrafuerte de San Felipe. Alero de teja, cal gastada con
   desconchados que dejan ver el adobe; arriba tres ventanas de arco rebajado con carpintería roja de cuarterones,
   visillos y antepecho oscuro; abajo portón de arco de tableros rojizos (izquierda), puerta abierta de la librería,
   ventana con reja y postigos oscuros; zócalo de canto rodado con filete blanco; letreros "fotocopias" y "librería".

Detrás de las fachadas no hay nada: cada casa es un volumen con su techo (azotea tras el pretil o tejado de dos aguas).
"""
import math

import colon_cuadra as P
from kit import Constructor, altura_suelo
from kit.arquitectura import alero_tejas
from piezas_claude import lado_virtual, sobre_calle, tejado_dos_aguas, tramo_calle

CAL = "#f4f2ec"
BEIGE = "#d8c29a"
ROSADO = "#efe2dc"          # pretil de la casona (algo rosado en las fotos)
PARDO = "#8c7260"           # zócalo de sillares
MADERA_R = "#5c2c20"        # carpintería y mirador rojo oscuro
TABLAS = "#7a3a24"          # portón de garaje
HIERRO = P.HIERRO

LINEA = 8.0                 # línea de fachada (m al NE del eje); 7,5 antes del ensanche de Colón (2026-11-24)
T_ESQUINA = 6.75           # media calle de Bustillo (5,75 antes del ensanche)
T_SAN_FELIPE = 67.7
CORTES = [T_ESQUINA, 28.6, 41.1, 52.2, T_SAN_FELIPE]


def _colon():
    return tramo_calle("Calle Colón", (-420.0, -430.0))


def _cuerpo(col_, nombre, t0, t1, fondo, alto, techo):
    """Volumen de una casa sobre la línea de fachada entre t0 y t1, con su fachada (Fachada local: s desde t0)."""
    c = _colon()
    xa, ya, ux, uy = sobre_calle(c, t0, LINEA)
    xb, yb, _, _ = sobre_calle(c, t1, LINEA)
    nx, ny = -uy, ux                                    # hacia el interior de la cuadra (NE)
    h = [(xa, ya), (xb, yb), (xb + nx * fondo, yb + ny * fondo), (xa + nx * fondo, ya + ny * fondo)]
    h = list(reversed(h))                               # antihorario
    zs = [altura_suelo(x, y) for x, y in h]
    zb, zr = min(zs), max(zs)
    cc = Constructor(nombre)
    cc.huella = h
    from kit.nucleo import Fachada
    suelo = altura_suelo((xa + xb) / 2, (ya + yb) / 2)
    f = Fachada(cc, lado_virtual((xa, ya), (xb, yb), (-nx, -ny)), suelo)
    cc.prisma(h, zb - 0.6, suelo + alto, "muro", CAL, tapa=(techo == "azotea"))
    if techo == "tejado":
        tejado_dos_aguas(cc, h, suelo + alto, pendiente=24, cumbrera=(ux, uy))
    return cc, P._Frente(f), zb - 0.6 - suelo, (ux, uy), (nx, ny)


# ---------------------------------------------------------------------------------------------- piezas propias
def cadena_esquina(f, s, h0, h1, hacia, color=BEIGE):
    """Sillares alternados (largo/corto) de una esquina; `hacia` = +1 si la fachada sigue hacia s creciente."""
    h, k = h0, 0
    while h < h1 - 0.1:
        largo = 0.75 if k % 2 == 0 else 0.45
        a, b = (s, s + largo * hacia) if hacia > 0 else (s + largo * hacia, s)
        f.caja(a, b, h, min(h1, h + 0.5), 0.0, 0.07, "piedra", color)
        h += 0.55
        k += 1


def zocalo_tramos(f, L, alto, desde, huecos, color=PARDO, junta="#6f5848", paso=0.38, d1=0.09):
    """Zócalo de sillares en tramos entre los vanos que bajan hasta la vereda (huecos: [(s0, s1)])."""
    cortes, s0 = [], 0.0
    for a, b in sorted(huecos):
        if a > s0:
            cortes.append((s0, a))
        s0 = max(s0, b)
    if s0 < L:
        cortes.append((s0, L))
    for a, b in cortes:
        f.caja(a, b, desde, alto, 0.02, d1, "zocalo_piedra", color)
        hz = 0.35
        while hz < alto - 0.1:
            f.caja(a, b, hz, hz + 0.03, d1, d1 + 0.01, "zocalo_piedra", junta)
            hz += paso


def pilastra_beige(f, s, h0, h_faja, h1, ancho=0.45):
    f.caja(s - ancho / 2, s + ancho / 2, h0, h1, 0.0, 0.09, "moldura", BEIGE)
    f.caja(s - ancho / 2 - 0.06, s + ancho / 2 + 0.06, h_faja - 0.3, h_faja - 0.1, 0.0, 0.14, "moldura", BEIGE)  # capitel


def ventana_reja_baja(f, s, ancho=1.4, h0=0.7, h1=3.3, marco=BEIGE, denticulos=True):
    """Ventana alta de planta baja con reja tupida de barrotes y bandas, marco moldurado y cornisita."""
    a = ancho / 2
    f.caja(s - a, s + a, h0, h1, -0.2, -0.18, "vidrio", "#2a3034")
    k = s - a + 0.08
    while k < s + a - 0.04:                                                  # barrotes
        f.caja(k - 0.014, k + 0.014, h0 + 0.03, h1 - 0.03, -0.05, -0.02, "hierro", HIERRO)
        k += 0.11
    hh = h0 + 0.25
    while hh < h1 - 0.1:                                                     # pletinas
        f.caja(s - a, s + a, hh, hh + 0.04, -0.05, -0.01, "hierro", HIERRO)
        hh += 0.42
    f.caja(s - a - 0.22, s - a, h0 - 0.08, h1 + 0.22, 0.0, 0.08, "moldura", marco)
    f.caja(s + a, s + a + 0.22, h0 - 0.08, h1 + 0.22, 0.0, 0.08, "moldura", marco)
    f.caja(s - a - 0.22, s + a + 0.22, h1, h1 + 0.22, 0.0, 0.08, "moldura", marco)
    f.caja(s - a - 0.28, s + a + 0.28, h0 - 0.16, h0 - 0.04, 0.0, 0.12, "moldura", marco)       # alféizar
    _cornisita(f, s, a + 0.36, h1 + 0.22, marco, denticulos)


def _cornisita(f, s, a, h, color, denticulos=True):
    f.caja(s - a + 0.06, s + a - 0.06, h, h + 0.12, 0.0, 0.1, "moldura", color)
    if denticulos:
        k = s - a + 0.12
        while k < s + a - 0.15:
            f.caja(k, k + 0.07, h + 0.12, h + 0.24, 0.0, 0.14, "moldura", color)
            k += 0.15
    f.caja(s - a, s + a, h + 0.24, h + 0.36, 0.0, 0.22, "moldura", color)


def mirador_esquina(f, s0, s1, h, alto=2.6, vuelo=1.0):
    """Mirador de madera de la esquina (R0170): base con cinco canes curvos, antepecho de tableros, tres paños de vidrio
    de 4×3 con su costado y tejadillo de tejas."""
    L = s1 - s0
    f.caja(s0, s1, h - 0.3, h, 0.0, vuelo, "madera", MADERA_R)                              # piso
    for k in range(5):                                                                       # canes curvos
        sc = s0 + 0.35 + (L - 0.7) * k / 4
        for j in range(4):
            f.caja(sc - 0.09, sc + 0.09, h - 0.3 - 0.18 * (j + 1), h - 0.3 - 0.18 * j, 0.0, vuelo * (0.95 - 0.22 * j),
                   "madera", MADERA_R)
    ap = 1.05                                                                                # antepecho
    f.caja(s0, s1, h, h + ap, vuelo - 0.08, vuelo, "madera", MADERA_R)
    for sx in (s0, s1 - 0.08):
        f.caja(sx, sx + 0.08, h, h + ap, 0.0, vuelo, "madera", MADERA_R)
    for k in range(6):                                                                       # tableros
        a = s0 + 0.1 + (L - 0.2) * k / 6
        f.caja(a + 0.06, a + (L - 0.2) / 6 - 0.06, h + 0.18, h + ap - 0.15, vuelo, vuelo + 0.03, "madera", "#6e3628")
    g0, g1 = h + ap, h + alto
    f.caja(s0 + 0.05, s1 - 0.05, g0, g1, vuelo - 0.07, vuelo - 0.05, "vidrio", "#3b4650")
    for sx in (s0 + 0.02, s1 - 0.06):                                                       # costados de vidrio
        f.caja(sx, sx + 0.04, g0, g1, 0.04, vuelo - 0.06, "vidrio", "#3b4650")
    n = 12                                                                                   # parteluces (3 paños × 4)
    for k in range(n + 1):
        sx = s0 + (L - 0.06) * k / n
        grueso = 0.1 if k % 4 == 0 else 0.045
        f.caja(sx, sx + grueso, g0, g1, vuelo - 0.09, vuelo - 0.01, "marco_ventana", MADERA_R)
    for j in range(4):
        hh = g0 + (g1 - g0 - 0.06) * j / 3
        f.caja(s0, s1, hh, hh + (0.09 if j in (0, 3) else 0.04), vuelo - 0.09, vuelo - 0.01, "marco_ventana", MADERA_R)
    for sx in (s0, s1 - 0.04):                                                               # parteluces del costado
        for j in range(1, 3):
            f.caja(sx, sx + 0.05, g0, g1, vuelo * j / 3 - 0.03, vuelo * j / 3 + 0.03, "marco_ventana", MADERA_R)
    f.caja(s0 - 0.1, s1 + 0.1, g1, g1 + 0.22, 0.0, vuelo + 0.12, "madera", MADERA_R)        # friso
    for j in range(4):                                                                       # tejadillo
        f.caja(s0 - 0.15, s1 + 0.15, g1 + 0.22 + j * 0.1, g1 + 0.32 + j * 0.1, 0.0, vuelo + 0.3 - j * 0.3, "teja")


def porton_tablas(f, s, ancho=3.0, alto=3.2):
    a = ancho / 2
    for sx in (s - a - 0.1, s + a):                                                          # derrame
        f.caja(sx, sx + 0.1, -0.05, alto + 0.1, -0.12, 0.0, "muro", "#e6e2da")
    f.caja(s - a - 0.1, s + a + 0.1, alto, alto + 0.1, -0.12, 0.0, "muro", "#e6e2da")
    f.caja(s - a, s + a, -0.05, alto, -0.12, -0.06, "madera", TABLAS)
    k = s - a + 0.16
    while k < s + a - 0.05:                                                                  # tablas verticales
        f.caja(k - 0.012, k + 0.012, 0.0, alto, -0.06, -0.05, "madera", "#4e2216")
        k += 0.16
    f.caja(s - 0.02, s + 0.02, 0.0, alto, -0.06, -0.04, "madera", "#3a1810")


def medidor(f, s, h):
    f.caja(s - 0.26, s + 0.26, h, h + 0.36, 0.0, 0.14, "metal", "#cfcfc8")
    for k in (-0.12, 0.12):
        f.caja(s + k - 0.07, s + k + 0.07, h + 0.12, h + 0.26, 0.14, 0.16, "pintura_acento", "#b03a2e")


# ---------------------------------------------------------------------------------------------- A: casona
ALTO_A = 8.4               # hasta el arranque de la cornisa
FAJA_A = 4.4


def casona(col_):
    t0, t1 = CORTES[0], CORTES[1]
    L = t1 - t0
    c, f, desde, u, n = _cuerpo(col_, "AMP_S_colon_casona", t0, t1, 14.0, ALTO_A + 0.7, "azotea")
    _fachada_casona(f, L, desde, modulos=[("mirador", 3.4), ("ventana", 9.0), ("porton", 14.6), ("puerta", 20.2)],
                    pilastras=[6.2, 11.8, 17.4, L - 0.25], esquina_s=0.0)
    P.farol_brazo(f, 17.4, 7.9)
    medidor(f, 16.6, 1.6)
    # lado de Bustillo (sin foto): la casona dobla la esquina con el mismo orden
    cb = _colon()
    xa, ya, ux, uy = sobre_calle(cb, t0, LINEA + 14.0)
    xb, yb, _, _ = sobre_calle(cb, t0, LINEA)
    from kit.nucleo import Fachada
    fb = P._Frente(Fachada(c, lado_virtual((xa, ya), (xb, yb), (-ux, -uy)), altura_suelo((xa + xb) / 2, (ya + yb) / 2)))
    dz = fb.suelo - f.suelo
    _fachada_casona(fb, 14.0, desde - dz, modulos=[("ventana", 3.6), ("ventana", 9.4)], pilastras=[0.25, 6.5],
                    esquina_s=14.0, alto=ALTO_A - dz)
    return c.objeto(col_)


def _fachada_casona(f, L, desde, modulos, pilastras, esquina_s, alto=ALTO_A):
    faja = FAJA_A + (alto - ALTO_A)
    f.caja(0, L, desde, alto + 0.7, 0.0, 0.02, "muro", CAL)
    huecos = [(s - (1.5 if t == "porton" else 0.95), s + (1.5 if t == "porton" else 0.95)) for t, s in modulos]
    zocalo_tramos(f, L, 1.4 + (alto - ALTO_A), desde, huecos)
    f.caja(0, L, faja - 0.12, faja + 0.12, 0.0, 0.12, "moldura", BEIGE)                     # faja
    for s in pilastras:
        pilastra_beige(f, s, 1.4 + (alto - ALTO_A), faja + 0.1, alto)
    hacia = 1 if esquina_s == 0.0 else -1
    cadena_esquina(f, esquina_s, 1.4 + (alto - ALTO_A), alto, hacia)
    P.cornisa_modillones(f, 0.0, L, alto, BEIGE)
    f.caja(0, L, alto + 0.68, alto + 1.5, -0.25, 0.0, "muro", ROSADO)                        # pretil
    f.caja(0, L, alto + 1.5, alto + 1.6, -0.3, 0.06, "moldura", BEIGE)
    for s in pilastras:
        P.urna(f, min(max(s, 0.3), L - 0.3), alto + 1.6, d=-0.1, color="#efe7d8")
    for tipo, s in modulos:
        b = alto - ALTO_A
        if tipo in ("mirador", "ventana"):
            ventana_reja_baja(f, s, ancho=1.55, h0=0.6 + b, h1=3.4 + b)
        elif tipo == "porton":
            porton_tablas(f, s, 3.0, 3.2 + b)
        elif tipo == "puerta":
            P.puerta_madera(f, s, 1.3, 3.0 + b, color="#4a2a1e", reja=True)
            for sx in (s - 0.65 - 0.22, s + 0.65):
                f.caja(sx, sx + 0.22, -0.05, 3.22 + b, 0.0, 0.08, "moldura", BEIGE)
            _cornisita(f, s, 1.05, 3.22 + b, BEIGE)
        if tipo == "mirador":
            mirador_esquina(f, 0.0 if esquina_s == 0.0 else L - 4.2, 4.2 if esquina_s == 0.0 else L, faja + 0.35)
        else:
            P.puerta_ventana(f, s, faja + 0.4, ancho=1.4, alto=2.8, marco=BEIGE, carpinteria=MADERA_R)
            P.balcon_forjado(f, s, faja + 0.4, ancho=2.2, vuelo=0.5, losa=BEIGE, menulas=3)


# ---------------------------------------------------------------------------------------------- B
def casa_b(col_):
    t0, t1 = CORTES[1], CORTES[2]
    L = t1 - t0
    c, f, desde, u, n = _cuerpo(col_, "AMP_S_colon_b", t0, t1, 10.0, ALTO_A + 0.7, "azotea")
    BL = "#f6f5f1"
    f.caja(0, L, desde, ALTO_A + 0.7, 0.0, 0.02, "muro", CAL)
    zocalo_tramos(f, L, 1.15, desde, [(2.2, 3.8), (8.1, 10.1), (10.5, 12.0)], paso=0.4, d1=0.08)
    f.caja(0, L, FAJA_A - 0.1, FAJA_A + 0.1, 0.0, 0.1, "moldura", BL)
    P.cornisa_modillones(f, 0.0, L, ALTO_A, BL)
    f.caja(0, L, ALTO_A + 0.68, ALTO_A + 1.35, -0.25, 0.0, "muro", BL)
    f.caja(0, L, ALTO_A + 1.35, ALTO_A + 1.45, -0.3, 0.05, "moldura", BL)
    P.urna(f, 9.3, ALTO_A + 1.45, d=-0.1, color=BL)
    for s in (3.0, 9.3):
        P.puerta_ventana(f, s, FAJA_A + 0.4, ancho=1.35, alto=2.8, marco=BL, carpinteria=MADERA_R, denticulos=False)
        P.balcon_forjado(f, s, FAJA_A + 0.4, ancho=2.0, vuelo=0.5, losa=BL, menulas=3)
    # puerta vidriera bajo el primer balcón
    s = 3.0
    f.caja(s - 0.7, s + 0.7, 0.0, 2.75, -0.2, -0.18, "vidrio", "#30383c")
    for k in (-0.66, 0.0, 0.66):
        f.caja(s + k - 0.05, s + k + 0.05, 0.0, 2.75, -0.18, -0.1, "marco_ventana", MADERA_R)
    for hh in (0.0, 2.68):
        f.caja(s - 0.7, s + 0.7, hh, hh + 0.07, -0.18, -0.1, "marco_ventana", MADERA_R)
    f.caja(s - 0.85, s + 0.85, 2.75, 2.85, 0.0, 0.05, "moldura", BL)
    # vitrina del local con cartel y puerta de madera n.º 65
    s = 9.1
    f.caja(s - 0.85, s + 0.85, 0.25, 2.6, -0.2, -0.18, "vidrio", "#22282b")
    f.caja(s - 0.6, s + 0.6, 1.45, 2.1, -0.18, -0.17, "letrero", "#f2f2f2")
    for sx, w in ((s - 1.0, 0.15), (s + 0.85, 0.15)):
        f.caja(sx, sx + w, 0.0, 2.75, 0.0, 0.05, "moldura", BL)
    f.caja(s - 1.0, s + 1.0, 2.6, 2.75, 0.0, 0.05, "moldura", BL)
    P.puerta_madera(f, 11.25, 1.3, 2.6, color="#4a2318")
    f.caja(10.45, 12.05, 2.6, 2.72, 0.0, 0.04, "moldura", BL)
    return c.objeto(col_)


# ---------------------------------------------------------------------------------------------- C
ALTO_C = 8.6


def casa_c(col_):
    t0, t1 = CORTES[2], CORTES[3]
    L = t1 - t0
    c, f, desde, u, n = _cuerpo(col_, "AMP_S_colon_c", t0, t1, 10.0, ALTO_C, "tejado")
    OCRE = "#c7894f"
    MARCO = "#b07a4c"
    f.caja(0, L, desde, ALTO_C, 0.0, 0.02, "muro", "#f2f0ea")
    zocalo_tramos(f, L, 1.65, desde, [(1.25, 4.3)], color=OCRE, junta="#9c6638", paso=0.33, d1=0.1)
    f.caja(0, L, 4.15, 4.25, 0.0, 0.05, "moldura", "#ecebe5")                                # línea entre plantas
    for s0, s1, hb in ((1.25, 4.3, 0.0), (6.3, 8.6, 0.95)):                                 # marcos de piedra ocre
        f.caja(s0, s0 + 0.32, hb - 0.05, 3.75, 0.0, 0.12, "piedra", MARCO)
        f.caja(s1 - 0.32, s1, hb - 0.05, 3.75, 0.0, 0.12, "piedra", MARCO)
        f.caja(s0, s1, 3.43, 3.75, 0.0, 0.12, "piedra", MARCO)
        if hb > 0:
            f.caja(s0, s1, hb - 0.12, hb + 0.05, 0.0, 0.14, "piedra", MARCO)
        a, b = s0 + 0.32, s1 - 0.32
        f.caja(a, b, 2.4 + hb * 0.4, 3.43, 0.0, 0.16, "pintura_acento", "#b5281f")           # persiana roja enrollada
        k = 2.45 + hb * 0.4
        while k < 3.4:
            f.caja(a, b, k, k + 0.03, 0.16, 0.17, "pintura_acento", "#8e1e18")
            k += 0.09
        f.caja(a, b, hb, 2.4 + hb * 0.4, -0.2, -0.18, "vidrio", "#1d2124")
    # entrada de la tienda: puerta de vidrio con marco metálico
    for sx in (1.6, 2.8, 3.95):
        f.caja(sx - 0.03, sx + 0.03, 0.0, 2.4, -0.18, -0.15, "metal", "#9a9a94")
    # vitrina: reja de barrotes
    k = 6.7
    while k < 8.25:
        f.caja(k - 0.012, k + 0.012, 0.95, 2.78, -0.04, -0.02, "hierro", HIERRO)
        k += 0.13
    # piso alto: dos ventanas sin moldura con baranda a ras
    for s in (2.9, 7.2):
        a = 0.85
        f.caja(s - a, s + a, 4.3, 6.75, -0.22, -0.2, "vidrio", "#2c3236")
        f.caja(s - a + 0.1, s + a - 0.1, 4.6, 6.65, -0.2, -0.19, "letrero", "#e9e4da")        # visillos
        for k_ in (-a, -0.03, a - 0.07):
            f.caja(s + k_, s + k_ + 0.07, 4.3, 6.75, -0.19, -0.13, "marco_ventana", "#2a2a2a")
        for hh in (4.3, 5.55, 6.68):
            f.caja(s - a, s + a, hh, hh + 0.07, -0.19, -0.13, "marco_ventana", "#2a2a2a")
        f.caja(s - a, s + a, 5.22, 5.27, -0.05, 0.0, "hierro", HIERRO)                        # baranda a ras
        k_ = s - a + 0.06
        while k_ < s + a:
            f.caja(k_ - 0.012, k_ + 0.012, 4.3, 5.25, -0.04, -0.01, "hierro", HIERRO)
            k_ += 0.12
        for sx in (s - a - 0.04, s + a):                                                      # derrame
            f.caja(sx, sx + 0.04, 4.3, 6.75, -0.2, 0.0, "muro", "#e4e1da")
    for (s, h, w, hh) in ((5.3, 7.1, 0.03, 1.4), (9.8, 5.2, 0.03, 1.1), (0.7, 6.2, 0.03, 0.9)):   # grietas
        f.caja(s, s + w, h, h + hh, 0.02, 0.03, "muro", "#cfc9bd")
    P.farol_brazo(f, L - 0.6, 7.3)
    alero_tejas(f, ALTO_C, vuelo=0.55, canes=False)
    return c.objeto(col_)


# ---------------------------------------------------------------------------------------------- D
ALTO_D = 8.1


def casa_d(col_):
    t0, t1 = CORTES[3], CORTES[4]
    L = t1 - t0
    c, f, desde, u, n = _cuerpo(col_, "AMP_S_colon_d", t0, t1, 10.0, ALTO_D, "tejado")
    CAL_V = "#eeebe3"
    ROJ = "#8a2a20"
    f.caja(0, L, desde, ALTO_D, 0.0, 0.02, "muro", CAL_V)
    # zócalo de canto rodado con filete blanco (salvo bajo el portón)
    HUECOS_D = [(-1.0, 2.75), (4.9, 6.3), (9.7, 11.3)]
    zocalo_tramos(f, L, 1.25, desde, HUECOS_D, color="#7d6b5d", junta="#7d6b5d", paso=9.0, d1=0.1)
    k, j = 2.9, 0
    while k < L - 0.15:                                                                      # cantos
        if any(a - 0.1 < k < b + 0.1 for a, b in HUECOS_D):
            k += 0.24
            continue
        for hh in (0.12, 0.36, 0.6, 0.84, 1.06):
            dh = 0.05 * math.sin(k * 3.1 + hh * 7)
            sk = k + 0.07 * math.sin(hh * 9 + j)
            w, hgt = 0.1 + 0.03 * math.sin(j + hh * 5), 0.07 + 0.02 * math.cos(j * 1.3 + hh)
            f.caja(sk - w, sk + w, hh + dh - hgt, hh + dh + hgt, 0.1, 0.13, "zocalo_piedra",
                   ["#8d7a6a", "#6a5a4f", "#a08d7b"][(j + int(hh * 10)) % 3])
        k += 0.24
        j += 1
    for a, b in ((2.75, 4.9), (6.3, 9.7), (11.3, L)):                                       # filete blanco
        f.caja(a, b, 1.25, 1.33, 0.0, 0.12, "moldura", "#f4f1ea")
    f.caja(0, L, 3.9, 3.98, 0.0, 0.07, "moldura", "#f4f1ea")                                 # línea entre plantas
    # portón de arco (izquierda)
    sp, wp = 1.4, 2.5
    f.caja(sp - wp / 2, sp + wp / 2, -0.05, 2.0, -0.14, -0.06, "madera", "#7b3a24")
    f.timpano_arco(sp, wp / 2, 2.0, -0.06, "madera", "#7b3a24")
    for jj in range(3):
        for kk in (-1, 1):
            f.caja(sp + kk * 0.6 - 0.45, sp + kk * 0.6 + 0.45, 0.25 + jj * 0.62, 0.75 + jj * 0.62, -0.06, -0.03,
                   "madera", "#93492e")
    f.caja(sp - 0.03, sp + 0.03, 0.0, 3.2, -0.06, -0.03, "madera", "#4a2015")
    f.arco(sp, wp / 2, 0.3, 2.0, 0.0, 0.06, "moldura", CAL_V, segmentos=12)
    f.caja(sp - wp / 2 - 0.3, sp - wp / 2, -0.05, 2.0, 0.0, 0.06, "moldura", CAL_V)
    f.caja(sp + wp / 2, sp + wp / 2 + 0.3, -0.05, 2.0, 0.0, 0.06, "moldura", CAL_V)
    # puerta abierta de la librería
    s = 5.6
    f.caja(s - 0.6, s + 0.6, 0.0, 2.7, -0.4, -0.38, "vidrio", "#15120f")
    f.caja(s - 0.6, s + 0.6, 0.0, 0.05, -0.4, 0.0, "piedra", "#9b9186")
    for sx in (s - 0.66, s + 0.6):
        f.caja(sx, sx + 0.06, 0.0, 2.7, -0.38, 0.0, "muro", "#e3dfd6")
    # ventana con reja y postigos oscuros
    s = 10.5
    f.caja(s - 0.68, s + 0.68, 0.55, 2.75, -0.18, -0.12, "madera", "#3e2318")
    k = s - 0.6
    while k < s + 0.66:
        f.caja(k - 0.013, k + 0.013, 0.55, 2.75, -0.06, -0.04, "hierro", HIERRO)
        k += 0.13
    for hh in (1.1, 1.9):
        f.caja(s - 0.68, s + 0.68, hh, hh + 0.04, -0.06, -0.03, "hierro", HIERRO)
    f.caja(s - 0.8, s + 0.8, 0.45, 0.55, 0.0, 0.08, "moldura", "#f4f1ea")
    # piso alto: tres ventanas de arco rebajado con carpintería roja de cuarterones
    for s, a in ((1.9, 0.62), (5.9, 0.64), (8.9, 0.72)):
        h0, h1 = 4.05, 6.15
        f.caja(s - a, s + a, h0, h1, -0.24, -0.22, "letrero", "#e2ddd2")                      # visillos
        f.caja(s - a, s + a, h0, h0 + 0.62, -0.22, -0.14, "madera", "#2b1a14" if s < 7 else ROJ)  # antepecho
        for kk in (-a, -0.04, a - 0.08):
            f.caja(s + kk, s + kk + 0.08, h0, h1 + 0.2, -0.22, -0.15, "marco_ventana", ROJ)
        for jj in range(5):
            hh = h0 + 0.62 + jj * 0.36
            f.caja(s - a, s + a, hh, hh + 0.045, -0.22, -0.16, "marco_ventana", ROJ)
        for kk in (-a / 2, a / 2):
            f.caja(s + kk - 0.02, s + kk + 0.02, h0 + 0.62, h1, -0.22, -0.16, "marco_ventana", ROJ)
        for jj in range(7):                                                                   # arco rebajado
            t_ = jj / 7
            x0 = s - a + 2 * a * t_
            hh = h1 + 0.3 * math.sin(math.pi * (t_ + 0.5 / 7))
            f.caja(x0, x0 + 2 * a / 7, h1, hh, -0.22, -0.15, "marco_ventana", ROJ)
            f.caja(x0 - 0.06, x0 + 2 * a / 7 + 0.06, hh, hh + 0.12, -0.22, 0.0, "muro", "#e6e2da")  # derrame del arco
        k = s - a + 0.06
        while k < s + a and s < 7:                                                            # baranda baja
            f.caja(k - 0.012, k + 0.012, h0, h0 + 0.62, -0.13, -0.11, "hierro", HIERRO)
            k += 0.11
        for sx in (s - a - 0.08, s + a):
            f.caja(sx, sx + 0.08, h0, h1 + 0.2, -0.22, 0.0, "muro", "#e6e2da")
        f.caja(s - a - 0.05, s + a + 0.05, h0 - 0.08, h0, 0.0, 0.06, "moldura", "#f4f1ea")
    # desconchados (dónde se ven en la foto)
    for s, h, w, hh, col_d in ((2.4, 4.0, 0.45, 0.75, "#b07a5a"), (13.1, 6.6, 0.7, 0.55, "#a8805f"),
                               (12.4, 6.9, 0.25, 0.3, "#a8805f"), (11.1, 3.15, 0.6, 0.3, "#b07a5a"),
                               (9.3, 1.35, 0.95, 0.45, "#a2553c"), (8.0, 1.5, 0.35, 0.2, "#a2553c"),
                               (14.0, 1.4, 0.45, 0.3, "#a8805f"), (6.3, 3.2, 0.3, 0.25, "#b07a5a")):
        f.caja(s - w / 2, s + w / 2, h, h + hh, 0.02, 0.03, "muro", col_d)
    # letreros verticales
    f.caja(4.05, 4.45, 1.15, 2.55, 0.05, 0.12, "pintura_acento", "#c8392b")
    f.caja(4.1, 4.4, 1.3, 2.4, 0.12, 0.13, "letrero", "#f1d36b")
    f.caja(7.0, 7.3, 1.1, 2.3, 0.05, 0.12, "pintura_acento", "#2d6fa8")
    f.caja(7.04, 7.26, 1.25, 2.15, 0.12, 0.13, "letrero", "#f0d040")
    alero_tejas(f, ALTO_D, vuelo=0.55, canes=False)
    return c.objeto(col_)


def construir(col_):
    """Las cuatro casas del frente NE de Colón."""
    return [casona(col_), casa_b(col_), casa_c(col_), casa_d(col_)]
