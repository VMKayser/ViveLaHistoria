"""Piezas de las fachadas de Colón (balcón forjado, puerta-ventana, puerta de madera, ventana recta, farol de brazo,
cornisa de modillones, urna) que usan colon_ne.py y otras partes de AMP_S. Las fachadas viejas de esta cuadra se
quitaron el 2026-11-23 (rehechas en colon_ne.py). Notas originales:

Calle Colón, frente NE entre la esquina de la plazuela y el costado de San Felipe Neri (R0172–R0175, fotos del
usuario, estudiadas a resolución completa el 2026-11-23). Cuatro fachadas, de NO a SE (en las fotos, de izquierda a
derecha):

A. R0172 izquierda — dos plantas de cal con PILASTRAS planas color beige que marcan módulos de ~5,1 m, faja beige entre
   plantas con ménsulas bajo los balcones, cornisa beige con friso de modillones y pretil con urnas sobre las pilastras;
   arriba puertas-ventana de madera con marco beige y guardapolvo con dentículos y balcón forjado con volutas; abajo una
   puerta con marco y dintel con dentículos, un portón de garaje de tablas y ventanas; zócalo de sillares pardos.
B. R0172 derecha + R0173 izquierda — misma altura, cal blanca SIN pilastras, cornisa blanca con modillones, faja blanca,
   dos puertas-ventana con marco y guardapolvo blancos y balcón forjado; abajo una puerta vidriera de dos hojas, una
   vidriera oscura de local y una puerta de madera de dos hojas; zócalo pardo bajo.
C. R0173 centro — casa de alero de TEJA, cal con grietas; arriba dos ventanas rectangulares sin moldura con baranda de
   barrotes a ras; abajo dos vanos con marco ancho de piedra ocre (entrada de tienda y vitrina) con persiana roja
   enrollada; zócalo alto de sillería ocre anaranjada.
D. R0174 — casa antigua de alero de teja, cal gastada con desconchados; arriba tres ventanas de arco rebajado con
   carpintería rojiza de cuarterones; abajo portón de arco de tableros rojizos, una puerta abierta y una ventana con
   reja; zócalo de CANTO RODADO con filete blanco; llega hasta el contrafuerte de esquina de San Felipe (R0175).

Cada función recibe la fachada (s a lo largo, h altura sobre la vereda, d hacia la calle), el ancho, el alto, el
desnivel `off` y `desde` (base enterrada). Las posiciones salen de las fotos (píxeles → metros con la altura del piso).
"""
import math

from kit.arquitectura import alero_tejas, cornisa, zocalo

CAL = "#f6f4ef"
BEIGE = "#dcc9a3"
MADERA = "#5c3322"
HIERRO = "#1f1f1f"


# ----------------------------------------------------------------------------------------------- piezas
class _Frente:
    """La fachada con los vanos "hundidos" (d < 0) llevados justo delante del muro: el volumen de la casa no tiene
    huecos, así que lo que queda detrás de su cara (d < 0) no se vería. Conserva el orden vidrio < carpintería < marco."""

    def __init__(self, f):
        self.f = f
        self.c = f.c
        self.n = f.n
        self.largo = f.largo

    @staticmethod
    def _d(d):
        return 0.022 + (max(d, -0.3) + 0.3) * 0.06 if d < 0 else d      # −0,3 … 0 → 0,022 … 0,040

    def caja(self, s0, s1, h0, h1, d0, d1, rol, color=None):
        self.f.caja(s0, s1, h0, h1, self._d(d0), self._d(d1), rol, color)

    def arco(self, s, r, ancho, h, d0, d1, rol, color=None, **kw):
        self.f.arco(s, r, ancho, h, self._d(d0), self._d(d1), rol, color, **kw)

    def timpano_arco(self, s, r, h, d, rol, color=None, **kw):
        self.f.timpano_arco(s, r, h, self._d(d), rol, color, **kw)

    def punto(self, s, h, d=0.0):
        return self.f.punto(s, h, self._d(d))

    def __getattr__(self, k):
        return getattr(self.f, k)


def _envolver(fn):
    def g(f, ancho, alto, off, desde):
        return fn(_Frente(f), ancho, alto, off, desde)
    g.__name__ = fn.__name__
    g.__doc__ = fn.__doc__
    return g

def _anillo(f, s, h, d, r, n=10, grosor=0.018):
    """Voluta de hierro: aro de barras finas en el plano de la fachada."""
    pts = [(s + r * math.cos(k * math.tau / n), h + r * math.sin(k * math.tau / n)) for k in range(n + 1)]
    for (s0, h0), (s1, h1) in zip(pts, pts[1:]):
        f.caja(min(s0, s1) - grosor / 2, max(s0, s1) + grosor / 2, min(h0, h1) - grosor / 2, max(h0, h1) + grosor / 2,
               d - grosor / 2, d + grosor / 2, "hierro", HIERRO)


def balcon_forjado(f, s, h, ancho=1.75, vuelo=0.5, losa=CAL, menulas=3):
    """Balcón de las fotos: losa moldurada sobre ménsulas y baranda de hierro con barrotes y volutas."""
    s0, s1 = s - ancho / 2, s + ancho / 2
    f.caja(s0, s1, h - 0.18, h, 0.0, vuelo, "moldura", losa)
    f.caja(s0 + 0.05, s1 - 0.05, h - 0.26, h - 0.18, 0.0, vuelo - 0.06, "moldura", losa)
    for k in range(menulas):
        sm = s0 + 0.25 + (ancho - 0.5) * k / max(1, menulas - 1)
        f.caja(sm - 0.1, sm + 0.1, h - 0.6, h - 0.26, 0.0, vuelo * 0.7, "moldura", losa)
    d = vuelo - 0.05
    f.caja(s0 + 0.03, s1 - 0.03, h + 0.95, h + 1.0, d - 0.025, d + 0.025, "hierro", HIERRO)   # pasamanos
    f.caja(s0 + 0.03, s1 - 0.03, h + 0.05, h + 0.09, d - 0.02, d + 0.02, "hierro", HIERRO)
    for lado in (s0 + 0.05, s1 - 0.05):                                                       # costados
        f.caja(lado - 0.015, lado + 0.015, h, h + 1.0, 0.0, d, "hierro", HIERRO)
    n = int(ancho / 0.12)
    for k in range(n + 1):
        sb = s0 + 0.06 + (ancho - 0.12) * k / n
        f.caja(sb - 0.01, sb + 0.01, h + 0.09, h + 0.95, d - 0.01, d + 0.01, "hierro", HIERRO)
    k = s0 + 0.25
    while k < s1 - 0.2:
        _anillo(f, k, h + 0.72, d + 0.02, 0.12)
        k += 0.3


def puerta_ventana(f, s, h, ancho=1.2, alto=2.4, marco=BEIGE, carpinteria=MADERA, guardapolvo=True, denticulos=True):
    """Puerta-ventana de dos hojas con montantes y travesaño, marco moldurado y guardapolvo encima."""
    a = ancho / 2
    f.caja(s - a, s + a, h, h + alto, -0.18, -0.16, "vidrio", "#2b3236")
    for k in (-1, 0, 1):                                                                       # montantes
        f.caja(s + k * (a - 0.04) - 0.045, s + k * (a - 0.04) + 0.045, h, h + alto, -0.16, -0.1, "marco_ventana", carpinteria)
    for hh in (h, h + alto * 0.42, h + alto - 0.42, h + alto - 0.06):                          # travesaños
        f.caja(s - a, s + a, hh, hh + 0.06, -0.16, -0.1, "marco_ventana", carpinteria)
    f.caja(s - a - 0.17, s - a, h - 0.05, h + alto + 0.17, 0.0, 0.07, "moldura", marco)        # marco
    f.caja(s + a, s + a + 0.17, h - 0.05, h + alto + 0.17, 0.0, 0.07, "moldura", marco)
    f.caja(s - a - 0.17, s + a + 0.17, h + alto, h + alto + 0.17, 0.0, 0.07, "moldura", marco)
    if guardapolvo:
        f.caja(s - a - 0.32, s + a + 0.32, h + alto + 0.3, h + alto + 0.46, 0.0, 0.2, "moldura", marco)
        f.caja(s - a - 0.22, s + a + 0.22, h + alto + 0.17, h + alto + 0.3, 0.0, 0.1, "moldura", marco)
        if denticulos:
            k = s - a - 0.15
            while k < s + a + 0.15:
                f.caja(k, k + 0.07, h + alto + 0.2, h + alto + 0.3, 0.0, 0.15, "moldura", marco)
                k += 0.14


def puerta_madera(f, s, ancho, alto, color=MADERA, marco=None, dintel=False, reja=False, hojas=2):
    """Puerta de madera de tableros (dos hojas) con marco moldurado opcional y dintel con dentículos."""
    a = ancho / 2
    f.caja(s - a, s + a, -0.05, alto, -0.12, -0.04, "madera", color)
    for k in range(1, hojas):
        f.caja(s - a + ancho * k / hojas - 0.02, s - a + ancho * k / hojas + 0.02, 0.0, alto, -0.04, -0.02, "madera", "#3a2016")
    for hh in (0.35, alto * 0.45, alto * 0.8):                                                 # tableros
        for k in range(hojas):
            x0 = s - a + ancho * k / hojas
            f.caja(x0 + 0.12, x0 + ancho / hojas - 0.12, hh, hh + 0.5, -0.04, -0.02, "madera", "#7a4630")
    if reja:
        k = s - a + 0.1
        while k < s + a - 0.05:
            f.caja(k - 0.012, k + 0.012, 0.3, alto - 0.2, -0.02, 0.0, "hierro", HIERRO)
            k += 0.16
    if marco:
        f.caja(s - a - 0.2, s - a, 0.0, alto + 0.2, 0.0, 0.08, "moldura", marco)
        f.caja(s + a, s + a + 0.2, 0.0, alto + 0.2, 0.0, 0.08, "moldura", marco)
        f.caja(s - a - 0.2, s + a + 0.2, alto, alto + 0.2, 0.0, 0.08, "moldura", marco)
        if dintel:
            f.caja(s - a - 0.4, s + a + 0.4, alto + 0.35, alto + 0.52, 0.0, 0.2, "moldura", marco)
            k = s - a - 0.3
            while k < s + a + 0.3:
                f.caja(k, k + 0.08, alto + 0.22, alto + 0.35, 0.0, 0.14, "moldura", marco)
                k += 0.16


def ventana_recta(f, s, h, ancho, alto, marco=None, carpinteria=MADERA, reja=False, vidrio="#2b3236"):
    a = ancho / 2
    f.caja(s - a, s + a, h, h + alto, -0.2, -0.18, "vidrio", vidrio)
    f.caja(s - 0.03, s + 0.03, h, h + alto, -0.18, -0.12, "marco_ventana", carpinteria)
    f.caja(s - a, s + a, h + alto * 0.62, h + alto * 0.62 + 0.05, -0.18, -0.12, "marco_ventana", carpinteria)
    f.caja(s - a, s + a, h - 0.08, h, 0.0, 0.08, "moldura", marco or CAL)                     # alféizar
    if marco:
        f.caja(s - a - 0.15, s - a, h, h + alto + 0.15, 0.0, 0.06, "moldura", marco)
        f.caja(s + a, s + a + 0.15, h, h + alto + 0.15, 0.0, 0.06, "moldura", marco)
        f.caja(s - a - 0.15, s + a + 0.15, h + alto, h + alto + 0.15, 0.0, 0.06, "moldura", marco)
    if reja:
        k = s - a + 0.08
        while k < s + a - 0.04:
            f.caja(k - 0.012, k + 0.012, h, h + alto, -0.06, -0.035, "hierro", HIERRO)
            k += 0.12
        for hh in (h + 0.1, h + alto - 0.1):
            f.caja(s - a, s + a, hh, hh + 0.025, -0.06, -0.035, "hierro", HIERRO)


def farol_brazo(f, s, h):
    """Farol de brazo de hierro con globo, como en las fotos de Colón."""
    f.caja(s - 0.04, s + 0.04, h - 0.4, h + 0.1, 0.0, 0.08, "hierro", HIERRO)
    f.caja(s - 0.025, s + 0.025, h, h + 0.05, 0.0, 0.85, "hierro", HIERRO)
    f.caja(s - 0.025, s + 0.025, h - 0.35, h, 0.6, 0.65, "hierro", HIERRO)
    q = f.punto(s, h - 0.45, 0.85)
    f.c.cilindro(q.x, q.y, q.z, q.z + 0.15, 0.2, "hierro", HIERRO, lados=8, radio_arriba=0.05)
    f.c.esfera(q.x, q.y, q.z - 0.1, 0.17, "letrero", "#ecebdc", segmentos=8)


def cornisa_modillones(f, s0, s1, h, color):
    """Cornisa de las fotos: filete, friso con modillones (bloques) cada 0,36 m y vuelo moldurado."""
    f.caja(s0, s1, h, h + 0.12, 0.0, 0.1, "moldura", color)
    k = s0 + 0.12
    while k < s1 - 0.15:
        f.caja(k, k + 0.14, h + 0.12, h + 0.42, 0.0, 0.2, "moldura", color)
        k += 0.36
    f.caja(s0, s1, h + 0.42, h + 0.56, 0.0, 0.32, "moldura", color)
    f.caja(s0, s1, h + 0.56, h + 0.68, 0.0, 0.42, "moldura", color)


def urna(f, s, h, d=0.1, color=CAL):
    q = f.punto(s, h, d)
    f.c.caja(q.x - 0.18, q.y - 0.18, q.z, q.x + 0.18, q.y + 0.18, q.z + 0.25, "moldura", color)
    f.c.cilindro(q.x, q.y, q.z + 0.25, q.z + 0.55, 0.13, "moldura", color, lados=8, radio_arriba=0.2)
    f.c.esfera(q.x, q.y, q.z + 0.68, 0.14, "moldura", color, segmentos=8)
