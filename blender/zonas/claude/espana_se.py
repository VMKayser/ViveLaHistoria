"""Calle España, vereda SE, primera cuadra desde la Plaza 25 de Mayo (R0206–R0210), rehecha desde cero el 2026-11-24
con las fotos del usuario. Lo llama la sección S_PLAZA25 (blender/secciones/plaza_25_mayo.py).

`t` = distancia a lo largo del eje de la Calle España desde la plaza; la fachada va a ancho/2 a la derecha del eje.
Las fotos están tomadas desde la vereda NO mirando al SE: lo de la IZQUIERDA tiene `t` mayor.

1. Casona de la esquina España × Daniel Calvo y del Banco Ecofuturo (t ≈ 4–48,5), dos plantas republicanas:
   - cuerpo de la esquina (R0206, R0207): planta baja almohadillada con ventana y puertas de arco, zócalo de sillares
     pardos, gran balcón de hierro con volutas sobre vigas de madera que dobla la esquina, puertas-ventana de arco,
     ático más alto con frontón curvo sobre la ochava;
   - el resto (R0207–R0209): ventanas de vidrios geométricos con marco moldurado y relieve encima, balcones de
     balaustres sobre ménsulas en los vanos 1, 2, 4, 6 y 7, pilastras con capitel a los lados del eje (portón tallado
     con montante de reja), vanos de marco gris abajo (METRO, tienda, banco, cajero, Ópticas Gala), entablamento de
     ménsulas y dentículos, pretil de tableros rosados con discos;
2. Casa de molduras grises (R0210, t 48,5–70): pilastras pareadas, faja con ménsulas colgantes, ventanas con frontón
   triangular gris y balcones de hierro, cornisa de dentículos, pretil con pedestales, medallones y bolas.
"""
import copy
import math

import colon_cuadra as cc_
from kit import Constructor, Fachada, altura_suelo
from kit import datos
from ortiz_se import marco_gris, puerta, tienda, zocalo_sillares, cuarterones
from piezas_claude import sobre_calle, suelo_huella, tramo_calle
from SAN_MIGUEL import farol_brazo as farol_verde
from base_suelo import ALTO_VEREDA, SOBRE_TERRENO

MURO = "#f2f0ea"
BLANCO = "#ecebe6"
RELIEVE = "#e4e1d8"
ROSA = "#e6cdc6"
GRIS = "#8e9192"
GRIS2 = "#7a7f80"
MADERA = "#4e2a1c"
HIERRO = "#1d1d1d"
PARDO = ("#9c8468", "#8a7258", "#a88f72", "#7f6a52", "#94795e")

# casona 1 (t sobre España)
T_FIN_1 = 48.5
T_TORRE = 10.0                 # fin del cuerpo de la esquina sobre España (casona() lo recalcula desde la esquina real)
LARGO_TORRE = 5.5             # largo del cuerpo de la esquina en cada cara (como en la cara a Daniel Calvo)
VENTANAS = [15.2 + 4.6 * k for k in range(7)]          # vanos de la planta alta
BALCONES = {0, 1, 3, 5, 6}
EJE = 3                                                # vano central, entre pilastras
BAJOS = {0: "metro", 1: "tienda", 3: "porton", 4: "banco", 5: "cajero", 6: "gala"}
H1, H_COR, H_TOPE = 5.0, 9.6, 10.4                    # faja, cornisa y tope del entablamento (sobre la vereda alta)
FONDO = 12.0
LARGO_DC = 15.0                                        # cara a Daniel Calvo
OCHAVA = 1.6


def _tramos():
    return tramo_calle("Calle España", (-60.0, -165.0)), tramo_calle("Calle Daniel Calvo", (-80.0, -210.0))


def _t_de(tramo, x, y):
    """t (m a lo largo del eje) del punto del eje más cercano a (x, y), en TODO el tramo. Antes se buscaba solo en los
    primeros 150 m: con las calles regeneradas el tramo de Daniel Calvo mide ~600 m y la casona, al final, prolongaba la
    línea de fachada recta desde lejos hasta meterla en media calzada (R0228)."""
    mejor, s0 = None, 0.0
    eje = tramo["eje"]
    for p, q in zip(eje, eje[1:]):
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if L < 1e-9:
            continue
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        t = max(0.0, min(L, (x - p[0]) * ux + (y - p[1]) * uy))
        d = math.hypot(x - p[0] - ux * t, y - p[1] - uy * t)
        if mejor is None or d < mejor[0]:
            mejor = (d, s0 + t)
        s0 += L
    return mejor[1]


def _linea_fachada(tramo, t, lado_lote):
    """Punto y dirección de la línea de fachada del tramo en t, del lado del lote."""
    w = tramo["ancho"] / 2
    for sgn in (-1, 1):
        x, y, ux, uy = sobre_calle(tramo, t, sgn * w)
        x2, y2, _, _ = sobre_calle(tramo, t, sgn * (w + 3))
        if math.dist((x2, y2), lado_lote) < math.dist((x, y), lado_lote):
            return (x, y), (ux, uy)
    raise ValueError


# ------------------------------------------------------------------------------------------------ piezas
def ventana_geometrica(f, s, h, w=1.3, alto=2.25, relieve=True):
    """Ventana de vidrios geométricos (rombos arriba), marco blanco moldurado con orejas y relieve de roleos encima."""
    a = w / 2
    f.caja(s - a, s + a, h, h + alto, -0.14, -0.12, "vidrio", "#2c3034")
    for x in (s - a, s - 0.03, s + a - 0.06):
        f.caja(x, x + 0.06, h, h + alto, -0.12, -0.07, "marco_ventana", BLANCO)
    for hh in (h, h + alto * 0.62, h + alto - 0.06):
        f.caja(s - a, s + a, hh, hh + 0.06, -0.12, -0.07, "marco_ventana", BLANCO)
    for x in (s - a / 2, s + a / 2):
        f.caja(x - 0.015, x + 0.015, h, h + alto * 0.62, -0.12, -0.09, "marco_ventana", BLANCO)
    for k in range(4):                                                          # rombos del montante
        x = s - a + w * (k + 0.5) / 4
        f.caja(x - 0.1, x + 0.1, h + alto * 0.78 - 0.015, h + alto * 0.78 + 0.015, -0.12, -0.09, "marco_ventana", BLANCO)
        f.caja(x - 0.015, x + 0.015, h + alto * 0.66, h + alto * 0.9, -0.12, -0.09, "marco_ventana", BLANCO)
    f.caja(s - a - 0.2, s - a, h - 0.05, h + alto + 0.2, 0.0, 0.08, "moldura", RELIEVE)
    f.caja(s + a, s + a + 0.2, h - 0.05, h + alto + 0.2, 0.0, 0.08, "moldura", RELIEVE)
    f.caja(s - a - 0.32, s + a + 0.32, h + alto + 0.05, h + alto + 0.22, 0.0, 0.1, "moldura", RELIEVE)
    for dx in (-a - 0.26, a + 0.26):                                            # orejas
        f.caja(s + dx - 0.08, s + dx + 0.08, h + alto - 0.25, h + alto + 0.05, 0.0, 0.1, "moldura", RELIEVE)
    if relieve:
        f.caja(s - a - 0.15, s + a + 0.15, h + alto + 0.22, h + alto + 0.62, 0.0, 0.05, "moldura", RELIEVE)
        for dx in (-0.35, 0.0, 0.35):                                           # roleos
            q = f.punto(s + dx, h + alto + 0.42, 0.06)
            f.c.esfera(q.x, q.y, q.z, 0.11, "moldura", "#dcd8ce", segmentos=6)
        f.caja(s - a - 0.38, s + a + 0.38, h + alto + 0.62, h + alto + 0.76, 0.0, 0.2, "moldura", RELIEVE)


def balcon_balaustres(f, s, h, ancho=1.75, vuelo=0.55):
    """Balcón de piedra blanca: losa moldurada sobre tres ménsulas grandes y baranda de balaustres."""
    s0, s1 = s - ancho / 2, s + ancho / 2
    f.caja(s0, s1, h - 0.2, h, 0.0, vuelo, "moldura", BLANCO)
    f.caja(s0 + 0.06, s1 - 0.06, h - 0.32, h - 0.2, 0.0, vuelo - 0.08, "moldura", RELIEVE)
    for k in range(3):
        x = s0 + 0.25 + (ancho - 0.5) * k / 2
        f.caja(x - 0.11, x + 0.11, h - 0.75, h - 0.32, 0.0, vuelo * 0.75, "moldura", BLANCO)
    d = vuelo - 0.08
    f.caja(s0, s1, h, h + 0.1, d - 0.06, d + 0.06, "moldura", BLANCO)
    f.caja(s0, s1, h + 0.85, h + 0.95, d - 0.07, d + 0.07, "moldura", BLANCO)
    for lado in (s0 + 0.06, s1 - 0.06):
        f.caja(lado - 0.06, lado + 0.06, h, h + 0.95, 0.0, d + 0.06, "moldura", BLANCO)
    k = s0 + 0.2
    while k < s1 - 0.15:
        q = f.punto(k, h + 0.1, d)
        f.c.cilindro(q.x, q.y, q.z, q.z + 0.75, 0.04, "moldura", BLANCO, lados=6, radio_arriba=0.03)
        k += 0.14


def balcon_volutas(f, s0, s1, h, vuelo=0.9, vigas=True):
    """Balcón grande de hierro con volutas sobre vigas de madera a la vista (R0206)."""
    if vigas:
        k = s0 + 0.15
        while k < s1 - 0.1:
            f.caja(k - 0.07, k + 0.07, h - 0.42, h - 0.18, 0.0, vuelo + 0.08, "madera", "#8a6a4a")
            k += 0.42
    f.caja(s0, s1, h - 0.18, h, 0.0, vuelo, "madera", "#7a5a3c")
    d = vuelo - 0.05
    f.caja(s0, s1, h + 1.0, h + 1.06, d - 0.03, d + 0.03, "hierro", HIERRO)
    f.caja(s0, s1, h + 0.05, h + 0.09, d - 0.02, d + 0.02, "hierro", HIERRO)
    f.caja(s0, s1, h + 0.8, h + 0.83, d - 0.02, d + 0.02, "hierro", HIERRO)
    k = s0 + 0.1
    while k < s1 - 0.05:
        f.caja(k - 0.012, k + 0.012, h, h + 1.0, d - 0.015, d + 0.015, "hierro", HIERRO)
        k += 0.12
    k = s0 + 0.3
    while k < s1 - 0.25:                                                        # volutas y abanicos
        cc_._anillo(f, k, h + 0.42, d, 0.18, n=10)
        cc_._anillo(f, k + 0.3, h + 0.62, d, 0.11, n=8)
        k += 0.6


def ventana_arco(f, s, h, w, alto, marco=MADERA, reja=False):
    """Vano de arco de medio punto con carpintería de madera y abanico en el montante."""
    a = w / 2
    f.caja(s - a, s + a, h, h + alto, -0.14, -0.12, "vidrio", "#2a2c2e")
    f.timpano_arco(s, a, h + alto, -0.12, "vidrio", "#2a2c2e")
    f.arco(s, a, 0.1, h + alto, -0.12, -0.05, "marco_ventana", marco, segmentos=10)
    for x in (s - a, s - 0.04, s + a - 0.08):
        f.caja(x, x + 0.08, h, h + alto, -0.12, -0.05, "marco_ventana", marco)
    f.caja(s - a, s + a, h + alto - 0.08, h + alto, -0.12, -0.05, "marco_ventana", marco)
    for k in range(5):                                                          # rayos del abanico
        ang = math.pi * (k + 1) / 6
        x = s + math.cos(ang) * a * 0.5
        f.caja(x - 0.02, x + 0.02, h + alto, h + alto + math.sin(ang) * a * 0.9, -0.12, -0.08, "marco_ventana", marco)
    if reja:
        k = s - a + 0.1
        while k < s + a - 0.05:
            f.caja(k - 0.012, k + 0.012, h, h + alto, -0.05, -0.03, "hierro", HIERRO)
            k += 0.13
    f.arco(s, a + 0.04, 0.22, h + alto, 0.0, 0.08, "moldura", RELIEVE, segmentos=12)    # rosca


def almohadillado(f, s0, s1, h0, h1, huecos=()):
    """Planta baja almohadillada: bandas lisas con junta hundida; huecos: (s0, s1, h_tope) de los vanos."""
    s0, s1 = min(s0, s1), max(s0, s1)
    hh = h0
    while hh < h1 - 0.1:
        a, b = hh + 0.04, min(hh + 0.44, h1)
        cortes = sorted((max(s0, x0), min(s1, x1)) for x0, x1, ht in huecos if a < ht)
        x = s0
        for c0, c1 in cortes + [(s1, s1)]:
            if c0 - x > 0.05:
                f.caja(x, c0, a, b, 0.0, 0.05, "muro", MURO)
            x = max(x, c1)
        hh += 0.48


def pilastra_capitel(f, s, h0, h1, ancho=0.5, vuelo=0.12):
    f.caja(s - ancho / 2 - 0.05, s + ancho / 2 + 0.05, h0, h0 + 0.3, 0.0, vuelo + 0.04, "moldura", RELIEVE)
    f.caja(s - ancho / 2, s + ancho / 2, h0 + 0.3, h1 - 0.4, 0.0, vuelo, "moldura", MURO)
    f.caja(s - ancho / 2 + 0.08, s + ancho / 2 - 0.08, h0 + 0.5, h1 - 0.6, vuelo, vuelo + 0.02, "moldura", RELIEVE)
    f.caja(s - ancho / 2 - 0.06, s + ancho / 2 + 0.06, h1 - 0.4, h1, 0.0, vuelo + 0.08, "moldura", RELIEVE)
    for dx in (-ancho / 3, 0.0, ancho / 3):                                     # hojas del capitel
        q = f.punto(s + dx, h1 - 0.22, vuelo + 0.1)
        f.c.esfera(q.x, q.y, q.z, 0.08, "moldura", "#dcd8ce", segmentos=6)


def entablamento(f, s0, s1, h, tope):
    """Arquitrabe, friso con ménsulas pareadas, dentículos y cornisa (R0207–R0209)."""
    f.caja(s0, s1, h, h + 0.18, 0.0, 0.1, "moldura", RELIEVE)
    f.caja(s0, s1, h + 0.18, tope - 0.35, 0.0, 0.04, "moldura", MURO)
    k = s0 + 0.4
    while k < s1 - 0.3:
        for dx in (-0.1, 0.1):
            f.caja(k + dx - 0.05, k + dx + 0.05, h + 0.2, tope - 0.35, 0.0, 0.16, "moldura", RELIEVE)
        k += 1.15
    k = s0 + 0.05
    while k < s1 - 0.1:
        f.caja(k, k + 0.08, tope - 0.35, tope - 0.24, 0.0, 0.22, "moldura", RELIEVE)
        k += 0.15
    f.caja(s0, s1, tope - 0.24, tope, 0.0, 0.42, "moldura", BLANCO)


def pretil_tableros(f, s0, s1, h, alto=0.95, paso=2.3):
    """Pretil de tableros rosados con un disco al centro, entre pedestales blancos."""
    f.caja(s0, s1, h, h + alto, 0.0, 0.04, "muro", MURO)
    n = max(1, round((s1 - s0) / paso))
    for k in range(n):
        a = s0 + (s1 - s0) * k / n + 0.3
        b = s0 + (s1 - s0) * (k + 1) / n - 0.3
        f.caja(a + 0.08, b - 0.08, h + 0.2, h + alto - 0.2, 0.04, 0.05, "pintura_acento", ROSA)
        q = f.punto((a + b) / 2, h + alto / 2, 0.06)
        f.c.cilindro(q.x, q.y, q.z - 0.2, q.z + 0.2, 0.025, "moldura", BLANCO, lados=10)
    for k in range(n + 1):
        s = min(max(s0 + (s1 - s0) * k / n, s0 + 0.3), s1 - 0.3)
        f.caja(s - 0.3, s + 0.3, h, h + alto + 0.1, 0.0, 0.12, "moldura", BLANCO)
    f.caja(s0, s1, h + alto, h + alto + 0.08, 0.0, 0.14, "moldura", BLANCO)


# ------------------------------------------------------------------------------------------------ casona 1
def a_la_vereda(f, s):
    """La misma fachada con h = 0 en la vereda que está delante de s (las caras largas bajan con la calle: una puerta
    con el pie en el suelo del centro de la cara quedaría enterrada en un extremo y colgada en el otro).
    Devuelve (fachada, dz): lo que estaba a la altura h queda en h - dz."""
    base = f.f if isinstance(f, cc_._Frente) else f
    q = base.punto(s, 0.0)
    dz = altura_suelo(q.x, q.y) + SOBRE_TERRENO + ALTO_VEREDA - base.suelo
    g = copy.copy(base)
    g.suelo = base.suelo + dz
    return (cc_._Frente(g) if isinstance(f, cc_._Frente) else g), dz


SEMIANCHO_BAJO = {"metro": 0.9, "tienda": 2.55, "porton": 1.15, "banco": 1.25, "cajero": 0.95, "gala": 1.3}


def zocalo_cortado(f, L, vanos, h, desde, semilla):
    """Zócalo de sillares a lo largo de la cara, interrumpido en los vanos que bajan al piso [(s, semiancho)]."""
    cortes = [0.0]
    for s, a in sorted(vanos):
        cortes += [max(s - a, 0.0), min(s + a, L)]
    cortes.append(L)
    for k in range(0, len(cortes), 2):
        if cortes[k + 1] - cortes[k] > 0.05:
            zocalo_sillares(f, cortes[k], cortes[k + 1], h, desde, colores=PARDO, semilla=semilla + k)


def _vano_bajo(f, tipo, s, off):
    f, dz = a_la_vereda(f, s)
    off -= dz
    if tipo == "metro":
        puerta(f, s, 1.2, 2.6 + off, color="#3a2a20")
        cc_.ventana_recta(f, s, 0.3 + off, 1.1, 2.2, carpinteria="#2a2220", reja=True)
        marco_gris(f, s, 0.0, 1.25, 2.75 + off, w=0.24)
        f.caja(s - 0.8, s + 0.8, 3.2 + off, 3.6 + off, 0.04, 0.08, "letrero", "#1f2326")
    elif tipo == "tienda":
        tienda(f, s, 4.4, 3.2 + off)
        marco_gris(f, s, 0.0, 4.4, 3.2 + off, w=0.3)
    elif tipo == "porton":
        puerta(f, s, 1.9, 3.0 + off, color="#e2dfd8", tableros=False)
        for dx in (-0.48, 0.48):
            for hh in (0.4, 1.3, 2.2):
                f.caja(s + dx - 0.3, s + dx + 0.3, hh + off, hh + 0.65 + off, -0.08, -0.05, "madera", "#d4d0c6")
        cc_.ventana_recta(f, s, 3.1 + off, 1.9, 0.75, carpinteria="#d4d0c6", reja=True)
        f.caja(s - 1.1, s + 1.1, 3.0 + off, 3.1 + off, 0.0, 0.06, "moldura", RELIEVE)
        f.caja(s - 1.3, s + 1.3, -0.35, 0.0, 0.0, 0.35, "piedra", "#9a9286")             # grada
    elif tipo == "banco":
        tienda(f, s, 1.9, 3.0 + off)
        rejilla(f, s, 1.9, 3.0 + off)
        marco_gris(f, s, 0.0, 1.9, 3.0 + off, w=0.26)
        f.caja(s - 1.6, s + 1.6, 3.45 + off, 4.25 + off, 0.04, 0.1, "letrero", "#6f7376")
        f.caja(s - 1.2, s + 1.2, 3.7 + off, 4.0 + off, 0.1, 0.11, "letrero", "#e8e8e8")
    elif tipo == "cajero":
        tienda(f, s, 1.4, 2.8 + off)
        rejilla(f, s, 1.4, 2.8 + off)
        marco_gris(f, s, 0.0, 1.4, 2.8 + off, w=0.22)
        f.caja(s - 0.8, s + 0.8, 2.85 + off, 3.2 + off, 0.04, 0.08, "letrero", "#e2542c")
    elif tipo == "gala":
        tienda(f, s, 2.0, 3.0 + off)
        marco_gris(f, s, 0.0, 2.0, 3.0 + off, w=0.26)
        f.caja(s - 1.6, s + 1.6, 3.6 + off, 3.95 + off, 0.06, 0.1, "letrero", "#c9ccce")
        q = f.punto(s - 2.4, 3.1 + off, 0.55)
        f.c.cilindro(q.x, q.y, q.z - 0.4, q.z + 0.4, 0.05, "letrero", "#2a8aa8", lados=12)
        f.caja(s - 2.43, s - 2.37, 3.55 + off, 3.65 + off, 0.0, 0.55, "hierro", HIERRO)


def rejilla(f, s, ancho, alto):
    """Reja plegable de rombos (banco, cajero)."""
    a = ancho / 2
    k = s - a + 0.1
    while k < s + a - 0.05:
        f.caja(k - 0.012, k + 0.012, 0.0, alto, -0.06, -0.04, "metal", "#b8bcbd")
        k += 0.16
    for hh in (0.1, alto * 0.5, alto - 0.1):
        f.caja(s - a, s + a, hh - 0.02, hh + 0.02, -0.06, -0.04, "metal", "#b8bcbd")


def cara_espana(f0, off, S, desde):
    """Cara a España: cuerpo de la esquina hasta T_TORRE y luego la casona. S(t) → s sobre esta cara."""
    f = cc_._Frente(f0)
    L = f.largo
    s_torre = S(T_TORRE)
    lo, hi = (0.0, s_torre) if s_torre < L / 2 else (s_torre, L)
    # zócalo de sillares pardos, cortado en los vanos que bajan a la vereda
    vanos = []
    for k, t in enumerate(VENTANAS):
        if k in BAJOS:
            sv = S(t) + (0.4 if BAJOS[k] == "tienda" else 0.0)
            vanos.append((sv, SEMIANCHO_BAJO[BAJOS[k]]))
    zocalo_cortado(f, L, vanos, 1.15 + off, desde, 17)
    # cuerpo de la esquina
    sm = (lo + hi) / 2
    almohadillado(f, lo, hi, 1.25 + off, H1 - 0.1 + off, huecos=[(sm - 1.0, sm + 1.0, 1.4 + off + 3.1)])
    ventana_arco(f, sm, 1.4 + off, 1.6, 2.2)
    ventana_arco(f, sm, H1 + 0.35 + off, 1.3, 2.1)
    balcon_volutas(f0, lo if lo == 0.0 else lo + 0.3, hi if hi == L else hi - 0.3, H1 + 0.25 + off)
    atico(f, lo, hi, off)
    for x in (lo + 0.3, hi - 0.3):
        if 0.3 < x < L - 0.3:
            pilastra_capitel(f, x, 1.25 + off, H_COR + off, ancho=0.55)
    f.caja(lo, hi, H1 - 0.15 + off, H1 + 0.05 + off, 0.0, 0.15, "moldura", RELIEVE)
    # casona
    a, b = (s_torre, L) if lo == 0.0 else (0.0, s_torre)
    f.caja(a, b, H1 - 0.15 + off, H1 + 0.02 + off, 0.0, 0.1, "moldura", RELIEVE)            # faja
    for k, t in enumerate(VENTANAS):
        s = S(t)
        if not (min(a, b) + 0.8 < s < max(a, b) - 0.8):
            continue
        ventana_geometrica(f, s, H1 + 0.55 + off, relieve=(k % 2 == 0 or k == EJE))
        if k in BALCONES:
            balcon_balaustres(f0, s, H1 + 0.5 + off)
        if k in BAJOS:
            _vano_bajo(f, BAJOS[k], s + (0.4 if BAJOS[k] == "tienda" else 0.0), off)
        if k == EJE:
            for dx in (-1.45, 1.45):
                pilastra_capitel(f, s + dx, 1.25 + off, H_COR + off, ancho=0.42)
    for t, h in ((26.5, H1 + 1.3), (T_FIN_1 - 1.6, H1 + 1.3)):                   # faroles de brazo (R0207, R0209)
        s = S(t)
        if 0.4 < s < L - 0.4:
            cc_.farol_brazo(f, s, h + off)
    entablamento(f, 0.0, L, H_COR + off, H_TOPE + off)
    pretil_tableros(f, min(a, b), max(a, b), H_TOPE + off)


def cara_ochava(f0, off, desde):
    f = cc_._Frente(f0)
    L = f.largo
    w = min(1.2, L - 0.5)
    zocalo_cortado(f, L, [(L / 2, w / 2 + 0.06)], 1.15 + off, desde, 19)
    almohadillado(f, 0.0, L, 1.25 + off, H1 - 0.1 + off, huecos=[(L / 2 - w / 2 - 0.25, L / 2 + w / 2 + 0.25, 3.3 + off)])
    fv, dz = a_la_vereda(f, L / 2)
    ventana_arco(fv, L / 2, 0.0, w, 2.4 + off - dz)
    f.caja(L / 2 - 0.55, L / 2 + 0.55, 2.55 + off, 2.85 + off, -0.11, -0.1, "letrero", "#1f2326")
    ventana_arco(f, L / 2, H1 + 0.35 + off, min(1.0, L - 0.7), 2.1)
    balcon_volutas(f0, -0.6, L + 0.6, H1 + 0.25 + off)
    cc_.farol_brazo(f, L - 0.2, H1 + 2.6 + off)
    entablamento(f, 0.0, L, H_COR + off, H_TOPE + off)
    atico(f, 0.0, L, off, frontón=True)


def atico(f, s0, s1, off, frontón=False):
    """Ático del cuerpo de la esquina, más alto que el pretil, con pilastras y frontón curvo (R0206)."""
    h = H_TOPE + off
    f.caja(s0, s1, h, h + 1.7, 0.0, 0.05, "muro", MURO)
    f.caja(s0, s1, h + 1.7, h + 1.95, 0.0, 0.3, "moldura", BLANCO)
    for x in (s0 + 0.25, s1 - 0.25):
        f.caja(x - 0.25, x + 0.25, h, h + 1.7, 0.0, 0.12, "moldura", RELIEVE)
    if frontón:
        sm = (s0 + s1) / 2
        r = (s1 - s0) / 2 - 0.1
        f.timpano_arco(sm, r, h + 1.95, 0.02, "muro", MURO)
        f.arco(sm, r, 0.2, h + 1.95, 0.0, 0.25, "moldura", BLANCO, segmentos=12)
        q = f.punto(sm, h + 2.3, 0.08)
        f.c.esfera(q.x, q.y, q.z, 0.28, "moldura", RELIEVE, segmentos=8)


def cara_calvo(f0, off, desde, desde_esquina):
    """Cara a Daniel Calvo: cuerpo de la esquina los primeros 5,5 m y luego la casona (dos vanos)."""
    f = cc_._Frente(f0)
    L = f.largo
    S = (lambda d: d) if desde_esquina else (lambda d: L - d)
    a, b = sorted((S(0.0), S(5.5)))
    zocalo_sillares(f, 0.0, L, 1.15 + off, desde, colores=PARDO, semilla=23)
    almohadillado(f, a, b, 1.25 + off, H1 - 0.1 + off, huecos=[(S(3.0) - 0.95, S(3.0) + 0.95, 4.5 + off)])
    ventana_arco(f, S(3.0), 1.4 + off, 1.4, 2.2, reja=True)
    ventana_arco(f, S(2.6), H1 + 0.35 + off, 1.2, 2.1)
    balcon_volutas(f0, min(S(0.0), S(4.2)), max(S(0.0), S(4.2)), H1 + 0.25 + off)
    pilastra_capitel(f, S(5.3), 1.25 + off, H_COR + off, ancho=0.55)
    f.caja(0.0, L, H1 - 0.15 + off, H1 + 0.02 + off, 0.0, 0.1, "moldura", RELIEVE)
    for d in (8.4, 12.6):
        if d < L - 0.9:
            ventana_geometrica(f, S(d), H1 + 0.55 + off, relieve=True)
            balcon_balaustres(f0, S(d), H1 + 0.5 + off)
            cc_.ventana_recta(f, S(d), 1.5 + off, 1.1, 2.0, marco=RELIEVE, carpinteria=MADERA, reja=True)
    entablamento(f, 0.0, L, H_COR + off, H_TOPE + off)
    c0, c1 = sorted((S(5.5), S(L)))
    pretil_tableros(f, c0, c1, H_TOPE + off)
    atico(f, a, b, off)


def casona(col):
    esp, dc = _tramos()
    lote = sobre_calle(esp, 12.0, -esp["ancho"] / 2 - 8.0)[:2]          # un punto dentro de la cuadra
    pe, ue = _linea_fachada(esp, 10.0, lote)
    pd, ud = _linea_fachada(dc, _t_de(dc, *pe), lote)
    den = ue[0] * ud[1] - ue[1] * ud[0]
    t = ((pd[0] - pe[0]) * ud[1] - (pd[1] - pe[1]) * ud[0]) / den
    C = (pe[0] + ue[0] * t, pe[1] + ue[1] * t)
    # direcciones desde la esquina hacia adentro de la cuadra
    if (lote[0] - C[0]) * ue[0] + (lote[1] - C[1]) * ue[1] < 0:
        ue = (-ue[0], -ue[1])
    if (lote[0] - C[0]) * ud[0] + (lote[1] - C[1]) * ud[1] < 0:
        ud = (-ud[0], -ud[1])
    fin = _linea_fachada(esp, T_FIN_1, lote)[0]
    global T_TORRE
    T_TORRE = _t_de(esp, *C) + LARGO_TORRE                              # con la esquina bien ubicada (R0228)
    lt = LARGO_TORRE                                                    # largo del cuerpo de la esquina sobre España
    print("[espana_se] esquina en", tuple(round(v, 1) for v in C), "cuerpo de esquina", round(lt, 1), "m")
    adentro = (ud[0], ud[1])
    huella = [(C[0] + ue[0] * OCHAVA, C[1] + ue[1] * OCHAVA), fin,
              (fin[0] + adentro[0] * FONDO, fin[1] + adentro[1] * FONDO),
              (C[0] + ud[0] * LARGO_DC, C[1] + ud[1] * LARGO_DC),
              (C[0] + ud[0] * OCHAVA, C[1] + ud[1] * OCHAVA)]
    huella = datos.orientar_ccw(huella)
    c = Constructor("SP25_esquina_E")
    c.huella = huella
    zb, zt = suelo_huella(huella)
    c.prisma(huella, zb - 0.6, zt + H_TOPE, "muro", MURO, tapa=True)
    # ático del cuerpo de la esquina (sobre la azotea, retirado 0,0 de las caras)
    at = [C, (C[0] + ue[0] * lt, C[1] + ue[1] * lt), (C[0] + ue[0] * lt + ud[0] * 5.5, C[1] + ue[1] * lt + ud[1] * 5.5),
          (C[0] + ud[0] * 5.5, C[1] + ud[1] * 5.5)]
    at = [(C[0] + ue[0] * OCHAVA, C[1] + ue[1] * OCHAVA)] + at[1:] + [(C[0] + ud[0] * OCHAVA, C[1] + ud[1] * OCHAVA)]
    c.prisma(datos.orientar_ccw(at), zt + H_TOPE - 0.05, zt + H_TOPE + 1.95, "muro", MURO, tapa=True)
    for p, q in zip(huella, huella[1:] + huella[:1]):
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        dirx, diry = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        f = Fachada(c, {"a": p, "b": q, "normal": (diry, -dirx)}, altura_suelo(mx, my))
        off = zt - f.suelo
        desde = zb - 0.6 - f.suelo
        if L < 3.0 and math.dist((mx, my), C) < 3:
            cara_ochava(f, off, desde)
        elif abs(dirx * ue[0] + diry * ue[1]) > 0.95 and math.dist((mx, my), C) < 40:
            ta, tb = _t_de(esp, *p), _t_de(esp, *q)
            cara_espana(f, off, lambda t, ta=ta, tb=tb, L=L: (t - ta) / (tb - ta) * L, desde)
        elif abs(dirx * ud[0] + diry * ud[1]) > 0.95 and math.dist(p, C) < LARGO_DC + 2 and math.dist(q, C) < LARGO_DC + 2:
            cara_calvo(f, off, desde, math.dist(p, C) < math.dist(q, C))
    c.objeto(col)
    return huella


# ------------------------------------------------------------------------------------------------ casa gris
# R0210 + R0211 (2026-11-24): la casa tiene CUATRO vanos (no tres). De t menor a mayor (en las fotos, de derecha a
# izquierda): puerta con reja ornamental, vitrina del local con franja amarilla, entrada con montante de vitrales y
# zaguán de arco, puerta de madera de dos hojas con montante; letrero de casita «La Primera» entre los dos últimos,
# cruz verde junto a la entrada; macetas en los balcones de los vanos 3 y 4; farol verde de brazo en el extremo NE.
GRIS_ANCHO = 18.5
GRIS_VANOS = [2.8, 7.1, 11.4, 15.7]
GRIS_PILASTRAS = [0.65, 4.95, 9.25, 13.55, 17.85]


def _bajo_gris(f, j, s, off):
    """Vano j de la planta baja de la casa gris; devuelve el ancho del hueco (para cortar el zócalo)."""
    f, dz = a_la_vereda(f, s)
    off -= dz
    if j == 0:                                                                  # puerta con reja ornamental
        a = 0.85
        f.caja(s - a, s + a, -0.05, 3.0 + off, -0.14, -0.12, "madera", "#3a1f16")
        for k in range(7):
            x = s - a + 0.12 + (2 * a - 0.24) * k / 6
            f.caja(x - 0.012, x + 0.012, 0.1, 2.95 + off, -0.12, -0.1, "hierro", HIERRO)
        for hh in (0.9, 1.9, 2.5 + off):
            f.caja(s - a, s + a, hh, hh + 0.03, -0.12, -0.1, "hierro", HIERRO)
        for k in range(3):                                                      # volutas
            cc_._anillo(f, s - 0.5 + 0.5 * k, 2.2 + off, -0.11, 0.18)
        marco_gris(f, s, 0.0, 2 * a, 3.0 + off, w=0.22)
    elif j == 1:                                                                # vitrina del local
        a = 0.9
        f.caja(s - a, s + a, -0.05, 3.0 + off, -0.16, -0.14, "vidrio", "#2b3034")
        for x in (s - a, s - 0.03, s + a - 0.06):
            f.caja(x, x + 0.06, 0.0, 3.0 + off, -0.14, -0.1, "marco_ventana", "#3a3a38")
        f.caja(s - a, s + a, 2.35 + off, 2.41 + off, -0.14, -0.1, "marco_ventana", "#3a3a38")
        f.caja(s - a + 0.05, s + a - 0.05, 1.05, 1.25, -0.1, -0.09, "letrero", "#e6c43a")       # franja amarilla
        for k in range(4):                                                      # montante de reja
            cc_._anillo(f, s - 0.6 + 0.4 * k, 2.68 + off, -0.12, 0.13)
        marco_gris(f, s, 0.0, 2 * a, 3.0 + off, w=0.24)
    elif j == 2:                                                                # entrada con montante de vitrales
        a = 0.95
        f.caja(s - a, s + a, -0.05, 2.6 + off, -0.3, -0.28, "vidrio", "#1d1a18")
        for x0, x1 in ((s - 0.72, s - 0.55), (s + 0.55, s + 0.72)):                    # arco del zaguán (al fondo)
            f.caja(x0, x1, -0.05, 2.2 + off, -0.26, -0.24, "muro", "#b9b3a8")
        f.arco(s, 0.55, 0.07, 2.2 + off, -0.26, -0.22, "moldura", "#c9c3b8", segmentos=8)
        f.caja(s - a, s + a, 2.6 + off, 3.25 + off, -0.14, -0.12, "madera", "#4a2618")
        for x in (s - 0.45, s + 0.45):                                          # vitrales
            f.caja(x - 0.36, x + 0.36, 2.7 + off, 3.15 + off, -0.12, -0.1, "vidrio", "#6a4a3a")
            cc_._anillo(f, x, 2.92 + off, -0.09, 0.16, n=8)
        for x in (s - a - 0.05, s + a - 0.1):                                   # hojas abiertas
            f.caja(x, x + 0.15, 0.0, 2.6 + off, -0.12, 0.0, "madera", "#4a2618")
        marco_gris(f, s, 0.0, 2 * a, 3.25 + off, w=0.24)
    else:                                                                       # puerta de madera con montante
        a = 0.85
        puerta(f, s, 2 * a, 2.6 + off, color="#4a2a1c")
        f.caja(s - a, s + a, 2.6 + off, 3.25 + off, -0.14, -0.12, "vidrio", "#3a3e40")
        for x in (s - a, s - 0.03, s + a - 0.06):
            f.caja(x, x + 0.06, 2.6 + off, 3.25 + off, -0.12, -0.08, "madera", "#4a2a1c")
        f.caja(s - a, s + a, 2.6 + off, 2.68 + off, -0.12, -0.08, "madera", "#4a2a1c")
        marco_gris(f, s, 0.0, 2 * a, 3.25 + off, w=0.22)
    return a + 0.24


def casa_gris(f0, L, alto, off, desde):
    f = cc_._Frente(f0)
    vanos, pil = GRIS_VANOS, GRIS_PILASTRAS
    h1 = 4.6 + off
    h_cor = alto - 1.2 + off
    # planta baja; zócalo de sillares pardos (1,3 m) cortado en sus vanos
    cortes = [0.0]
    for j, s in enumerate(vanos):
        a = _bajo_gris(f, j, s, off)
        cortes += [s - a, s + a]
    cortes.append(L)
    for k in range(0, len(cortes), 2):
        zocalo_sillares(f, cortes[k], cortes[k + 1], 1.3 + off, desde, semilla=17 + k)
    # pilastras pareadas
    for sp in pil:
        for dx in (-0.35, 0.35):
            x = min(max(sp + dx, 0.25), L - 0.25)
            f.caja(x - 0.2, x + 0.2, 1.38 + off, h_cor, 0.0, 0.1, "moldura", MURO)
    f.caja(0.0, L, h1 - 0.15, h1 + 0.05, 0.0, 0.14, "moldura", GRIS)                        # faja gris
    for sp in pil:                                                                           # ménsulas colgantes
        for dx in (-0.35, 0.35):
            x = min(max(sp + dx, 0.25), L - 0.25)
            f.caja(x - 0.09, x + 0.09, h1 - 0.85, h1 - 0.15, 0.0, 0.16, "moldura", GRIS)
            q = f.punto(x, h1 - 0.95, 0.1)
            f.c.cilindro(q.x, q.y, q.z - 0.15, q.z + 0.1, 0.06, "moldura", GRIS, lados=6, radio_arriba=0.02)
    for j, s in enumerate(vanos):
        # planta alta: puerta-ventana con marco gris, frontón triangular y balcón de hierro
        h2 = h1 + 0.45
        cuarterones(f, s, h2, ancho=1.15, alto=2.3, color="#3a2016")
        marco_gris(f, s, h2, 1.15, 2.3, w=0.18)
        hp = h2 + 2.6
        for k in range(6):                                                                   # frontón escalonado
            w = 1.95 - k * 0.32
            f.caja(s - w / 2, s + w / 2, hp + k * 0.09, hp + (k + 1) * 0.09, 0.0, 0.16 - k * 0.01, "moldura", GRIS)
        for dx in (-0.95, 0.95):
            f.caja(s + dx - 0.08, s + dx + 0.08, hp - 0.35, hp, 0.0, 0.16, "moldura", GRIS)
        cc_.balcon_forjado(f, s, h2, ancho=1.8, vuelo=0.45, losa=GRIS, menulas=2)
        if j >= 2:                                                                           # macetas con flores
            for k in range(4):
                q = f.punto(s - 0.6 + 0.4 * k, h2, 0.22)
                f.c.cilindro(q.x, q.y, q.z, q.z + 0.24, 0.1, "piedra", "#b0603e", lados=8, radio_arriba=0.13)
                f.c.esfera(q.x, q.y, q.z + 0.36, 0.15, "follaje" if k % 2 else "follaje_claro", None, segmentos=6)
                if k % 2 == 0:
                    f.c.esfera(q.x, q.y, q.z + 0.48, 0.07, "flor", "#d8433a", segmentos=6)
    # letreros: casita «La Primera», cruz verde y placa de bronce
    sl = 13.3
    f.caja(sl - 0.5, sl + 0.5, 2.55 + off, 3.3 + off, 0.02, 0.05, "letrero", "#2a2622")
    for k in range(5):
        w = 1.1 - k * 0.22
        f.caja(sl - w / 2, sl + w / 2, 3.3 + off + k * 0.08, 3.38 + off + k * 0.08, 0.02, 0.05, "letrero", "#2a2622")
    q = f.punto(sl, 2.92 + off, 0.06)
    f.c.cilindro(q.x, q.y, q.z - 0.25, q.z + 0.25, 0.25, "letrero", "#c9a54a", lados=12)
    f.caja(9.45, 9.75, 2.95 + off, 3.25 + off, 0.02, 0.04, "letrero", "#3aa060")
    f.caja(17.25, 17.95, 2.0 + off, 2.45 + off, 0.02, 0.04, "letrero", "#8a6a3a")
    farol_verde(f, 18.0, 6.9 + off)
    # cornisa de dentículos grises y ménsulas
    f.caja(0.0, L, h_cor, h_cor + 0.15, 0.0, 0.12, "moldura", GRIS)
    k = 0.1
    while k < L - 0.1:
        f.caja(k, k + 0.12, h_cor + 0.15, h_cor + 0.35, 0.0, 0.2, "moldura", GRIS2 if int(k / 0.25) % 2 else MURO)
        k += 0.25
    f.caja(0.0, L, h_cor + 0.35, h_cor + 0.55, 0.0, 0.38, "moldura", GRIS)
    for sp in pil:
        for dx in (-0.35, 0.35):
            x = min(max(sp + dx, 0.2), L - 0.2)
            f.caja(x - 0.1, x + 0.1, h_cor - 0.6, h_cor, 0.0, 0.2, "moldura", GRIS)
    # pretil con pedestales, medallón gris y bola (uno sobre cada par de pilastras)
    zp = h_cor + 0.55
    f.caja(0.0, L, zp, zp + 0.85, 0.0, 0.04, "muro", MURO)
    f.caja(0.0, L, zp + 0.85, zp + 0.92, 0.0, 0.1, "moldura", GRIS)
    for sp in pil:
        x = min(max(sp, 0.5), L - 0.5)
        f.caja(x - 0.45, x + 0.45, zp, zp + 1.2, 0.0, 0.16, "moldura", MURO)
        for dx in (-0.36, 0.36):
            f.caja(x + dx - 0.06, x + dx + 0.06, zp + 0.1, zp + 1.1, 0.16, 0.18, "moldura", GRIS)
        q = f.punto(x, zp + 0.6, 0.18)
        f.c.cilindro(q.x, q.y, q.z - 0.14, q.z + 0.14, 0.03, "moldura", GRIS, lados=10)
        f.caja(x - 0.5, x + 0.5, zp + 1.2, zp + 1.3, 0.0, 0.2, "moldura", GRIS)
        q = f.punto(x, zp + 1.55, 0.08)
        f.c.esfera(q.x, q.y, q.z, 0.22, "moldura", BLANCO, segmentos=8)


def construir(col):
    """Casona de la esquina y casa gris; devuelve el t donde sigue la hilera genérica de la cuadra."""
    from piezas_claude import casas_de_frente
    casona(col)
    esp, _ = _tramos()
    casas_de_frente(col, "SP25_espana_gris", esp, -1,
                    [(GRIS_ANCHO, 2, 4.65, MURO, "plano", dict(a_mano=casa_gris))], t0=T_FIN_1, fondo_max=11.0)
    return T_FIN_1 + GRIS_ANCHO
