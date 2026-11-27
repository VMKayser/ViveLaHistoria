"""Frente de San Felipe Neri sobre la Calle Nicolás Ortiz (R0099–R0102, R0179), rehecho desde cero el 2026-11-24.

Fachada local del lado de OSM más cercano al cruce: s = 0 en la esquina de Colón, s = L (12,3 m) contra el convento;
h sobre el suelo de la fachada; d hacia la calle.

Inventario (fotos del usuario a resolución completa):
- Cuerpo de piedra de 16 m: sillares grandes beige con muchos bloques rojos alternados (no franjas), esquinas romas.
- Calle central (5,2 m) metida 0,3 m: puerta en arco de medio punto (3 m de luz, clave a 4,7 m) de madera verde con
  archivolta moldurada; encima una cartela con volutas en C y medallón; la ventana del coro (1,4 × 1,9 m, marco de
  piedra, vidrio azul en cuadros); todo bajo un gran arco de piedra almohadillada (clave a ~13 m).
- A cada lado un pilar macizo que sale 0,5 m, con dos fajas de molduras abultadas (a 6,3 m y a 10,2 m) y basa.
- Cornisa a 15,6 m que sube en curva al centro; pináculos chicos en las esquinas.
- Encima, retirado 1,2 m: cuerpo blanco con el vano en arco de la campana y balcón de hierro delante, remate de
  volutas; a los lados las dos torres blancas: base cuadrada de esquinas achaflanadas hasta 21,5 m, cuerpo octogonal
  con vanos en arco y campana hasta 25 m, cupulín octogonal con borde de tejas y cruz de hierro.
- Base de la torre sobre Colón (R0179): bloque de piedra liso más alto que la nave, con la esquina en cuarto bocel.
"""
import math

from piezas_claude import adelantada
from san_felipe_costado import sillares, _tramos_libres

HF = 15.6
PIEDRA = ("#c4946f", "#b98663", "#cc9f7c", "#ad7a5e", "#94523f")
CLARA = "#cfa483"
MOLDURA = "#c99b78"
VERDE = "#24372f"
BL = "#f3f0ea"
BL2 = "#e7e2d8"
TEJA = "#a8543a"
HIERRO = "#26292b"


def _anillo(c, x, y, z0, z1, r, rol, color, lados=8, rot=math.pi / 8):
    """Prisma de n lados (para las torres octogonales)."""
    pts = [(x + r * math.cos(rot + 2 * math.pi * k / lados), y + r * math.sin(rot + 2 * math.pi * k / lados))
           for k in range(lados)]
    c.prisma(pts, z0, z1, rol, color, tapa=True)


# ---------------------------------------------------------------------------------------------- cuerpo de piedra
def cuerpo(c, f, off, L):
    sm = L / 2
    W = 2.6                                                                      # media calle central
    P0, P1 = W, W + 1.8                                                          # pilares (desde el centro)
    f.caja(0.0, L, -0.6, HF + off, 0.0, 0.3, "zocalo_piedra", "#a97c62")       # macizo
    # paños laterales y calle central
    for a, b in ((0.25, sm - P1), (sm + P1, L - 0.25)):
        sillares(adelantada(f, 0.3), a, b, -0.4, HF + off - 0.2, 0.0, alto=0.5, largo=(0.6, 1.2), colores=PIEDRA,
                 rojo=0.24, semilla=int(a * 7) + 3)
    for k, s0 in enumerate((0.0, L - 0.25)):                                       # esquinas romas
        f.caja(s0, s0 + 0.25, -0.6, HF + off, 0.0, 0.22, "zocalo_piedra", CLARA)
    fc = adelantada(f, 0.0)
    huecos = [(sm - 1.75, sm + 1.75)]
    for a, b in _tramos_libres(sm - W, sm + W, huecos):
        sillares(adelantada(f, 0.3), a, b, -0.4, 5.1 + off, 0.0, alto=0.5, colores=PIEDRA, rojo=0.24, semilla=40 + int(a))
    sillares(adelantada(f, 0.3), sm - W, sm + W, 5.1 + off, HF + off - 0.2, 0.0, alto=0.5, colores=PIEDRA, rojo=0.24,
             semilla=47)
    # pilares
    for k in (-1, 1):
        a, b = sorted((sm + k * P0, sm + k * P1))
        fp = adelantada(f, 0.3)
        fp.caja(a, b, -0.6, HF + off - 0.3, 0.0, 0.5, "zocalo_piedra", "#c09a80")
        sillares(adelantada(f, 0.8), a, b, -0.4, HF + off - 0.3, 0.0, alto=0.45, largo=(0.5, 0.9), colores=PIEDRA,
                 rojo=0.3, semilla=60 + k)
        fp.caja(a - 0.12, b + 0.12, -0.6, 0.9 + off, 0.0, 0.65, "piedra", "#b48a72")       # basa
        for h0, n in ((6.3, 5), (10.2, 4)):                                               # fajas abultadas
            for j in range(n):
                hh = h0 + j * 0.28
                sal = 0.62 + 0.22 * math.sin(math.pi * (j + 0.5) / n)
                fp.caja(a - 0.1 - 0.1 * (j % 2), b + 0.1 + 0.1 * (j % 2), hh + off, hh + 0.26 + off, 0.0, sal,
                        "piedra", MOLDURA if j % 2 else "#c39a7f")
    # puerta en arco
    fd = adelantada(f, 0.31)
    r, hs = 1.5, 3.2 + off
    fd.caja(sm - r, sm + r, -0.3, hs, -0.02, 0.0, "madera", VERDE)
    fd.timpano_arco(sm, r, hs, 0.0, "madera", VERDE)
    fd.caja(sm - 0.03, sm + 0.03, 0.0, hs + r, 0.0, 0.03, "madera", "#16211c")
    for kk in (-1, 1):
        for hh in (0.4, 1.7):
            fd.caja(sm + kk * 0.75 - 0.5, sm + kk * 0.75 + 0.5, hh + off, hh + 1.0 + off, 0.0, 0.03, "madera", "#2d453a")
    fd.arco(sm, r, 0.35, hs, 0.0, 0.18, "piedra", CLARA, segmentos=14)
    fd.arco(sm, r + 0.35, 0.15, hs, 0.0, 0.26, "piedra", MOLDURA, segmentos=14)
    for kk in (-1, 1):
        fd.caja(sm + kk * (r + 0.17) - 0.18, sm + kk * (r + 0.17) + 0.18, -0.3, hs, 0.0, 0.18, "piedra", CLARA)
        fd.caja(sm + kk * (r + 0.17) - 0.26, sm + kk * (r + 0.17) + 0.26, hs - 0.22, hs, 0.0, 0.28, "piedra", MOLDURA)
    # cartela con volutas en C y medallón
    h0 = 5.4 + off
    fd.caja(sm - 1.3, sm + 1.3, h0, h0 + 0.18, 0.0, 0.3, "piedra", MOLDURA)
    for j in range(8):
        t = (j + 0.5) / 8
        w = 0.75 + 0.45 * math.sin(math.pi * t)
        fd.caja(sm - w, sm + w, h0 + 0.18 + 0.22 * j, h0 + 0.4 + 0.22 * j, 0.0, 0.2, "piedra", CLARA if j % 2 else "#cba287")
    fd.esfera(sm, h0 + 1.05, 0.25, 0.35, "piedra", "#d8b79d")
    for kk in (-1, 1):
        fd.arco(sm + kk * 1.05, 0.3, 0.12, h0 + 0.55, 0.15, 0.34, "piedra", MOLDURA, segmentos=8, medio=False)
        fd.arco(sm + kk * 0.95, 0.22, 0.1, h0 + 1.45, 0.15, 0.34, "piedra", MOLDURA, segmentos=8, medio=False)
    fd.caja(sm - 1.35, sm + 1.35, h0 + 1.95, h0 + 2.2, 0.0, 0.38, "piedra", MOLDURA)
    # ventana del coro
    w0, w1 = 8.1 + off, 10.0 + off
    fd.caja(sm - 0.95, sm + 0.95, w0 - 0.25, w1 + 0.4, 0.0, 0.16, "piedra", CLARA)
    fd.caja(sm - 0.7, sm + 0.7, w0, w1, 0.16, 0.17, "vidrio", "#203a5c")
    for kk in (-0.35, 0.35):
        fd.caja(sm + kk - 0.025, sm + kk + 0.025, w0, w1, 0.17, 0.2, "marco_ventana", "#3a3f44")
    for hh in (w0 + 0.63, w0 + 1.26):
        fd.caja(sm - 0.7, sm + 0.7, hh - 0.025, hh + 0.025, 0.17, 0.2, "marco_ventana", "#3a3f44")
    fd.arco(sm, 0.95, 0.2, w1 - 0.6, 0.0, 0.2, "piedra", MOLDURA, segmentos=8)
    # gran arco almohadillado que enmarca la calle central
    R = W - 0.35
    for j in range(13):
        am = math.pi * (j + 0.5) / 13
        s_ = sm - math.cos(am) * (R + 0.3)
        h_ = 10.9 + off + math.sin(am) * (R + 0.3)
        fd.caja(s_ - 0.3, s_ + 0.3, h_ - 0.3, h_ + 0.3, 0.0, 0.22, "piedra", CLARA if j % 2 else "#b47f68")
    fd.arco(sm, R + 0.6, 0.18, 10.9 + off, 0.0, 0.3, "piedra", MOLDURA, segmentos=13)
    fd.caja(sm - 0.45, sm + 0.45, 12.6 + off, 13.4 + off, 0.0, 0.3, "piedra", "#d4b196")             # clave
    # cornisa que sube en curva al centro y pináculos de las esquinas
    for j in range(16):
        s0, s1 = L * j / 16, L * (j + 1) / 16
        x = ((s0 + s1) / 2 - sm) / (L / 2)
        sube = 1.1 * max(0.0, math.cos(x * math.pi / 1.3)) ** 1.5
        h = HF + sube + off
        f.caja(s0 - 0.01, s1 + 0.01, h - 0.55, h - 0.25, 0.0, 0.62, "piedra", MOLDURA)
        f.caja(s0 - 0.01, s1 + 0.01, h - 0.25, h, 0.0, 0.85, "piedra", "#d7b59a")
        if sube > 0.02:
            sillares(adelantada(f, 0.3), s0, s1, HF + off - 0.2, h - 0.55, 0.0, alto=0.4, colores=PIEDRA, rojo=0.24,
                     semilla=90 + j)
            f.caja(s0, s1, HF - 0.6 + off, h - 0.5, -1.2, 0.3, "zocalo_piedra", "#b58a72")
    for s_ in (0.35, L - 0.35):
        q = f.punto(s_, HF + off, 0.4)
        c.caja(q.x - 0.25, q.y - 0.25, q.z, q.x + 0.25, q.y + 0.25, q.z + 0.4, "piedra", MOLDURA)
        c.cilindro(q.x, q.y, q.z + 0.4, q.z + 0.75, 0.18, "piedra", CLARA, lados=8, radio_arriba=0.1)
        c.esfera(q.x, q.y, q.z + 0.9, 0.15, "piedra", MOLDURA, segmentos=8)


# ---------------------------------------------------------------------------------------------- remate blanco
def campanario(c, f, off, L, st):
    """Cuerpo blanco con la campana entre las dos torres (st: centros de las torres en s)."""
    sm = L / 2
    d0, d1 = -3.0, -0.9
    h0 = HF + off
    f.caja(st[0], st[1], h0 - 0.3, h0 + 3.6, d0, d1, "muro", BL)
    for j in range(9):                                                                   # remate de volutas
        t = (j + 0.5) / 9
        x0 = st[0] + (st[1] - st[0]) * j / 9
        hh = h0 + 3.6 + 1.3 * math.sin(math.pi * t) ** 0.7
        f.caja(x0, x0 + (st[1] - st[0]) / 9 + 0.01, h0 + 3.5, hh, d0 + 0.2, d1, "muro", BL)
        f.caja(x0, x0 + (st[1] - st[0]) / 9 + 0.01, hh, hh + 0.15, d0 + 0.1, d1 + 0.1, "moldura", BL2)
    f.caja(sm - 0.7, sm + 0.7, h0 + 0.5, h0 + 2.6, d1, d1 + 0.01, "madera", "#2a2622")      # vano de la campana
    f.timpano_arco(sm, 0.7, h0 + 2.6, d1 + 0.01, "madera", "#2a2622")
    f.arco(sm, 0.7, 0.18, h0 + 2.6, d1, d1 + 0.12, "moldura", BL2, segmentos=10)
    q = f.punto(sm, h0 + 2.5, d1 - 0.4)
    c.cilindro(q.x, q.y, q.z - 0.75, q.z - 0.1, 0.42, "metal", "#5e5236", lados=10, radio_arriba=0.2)
    c.caja(q.x - 0.06, q.y - 0.06, q.z - 0.1, q.x + 0.06, q.y + 0.06, q.z + 0.25, "hierro", HIERRO)
    # balcón de hierro sobre la cornisa
    a, b = sm - 1.6, sm + 1.6
    for hh in (h0 + 1.05 + 0.0, h0 + 0.1):
        f.caja(a, b, hh, hh + 0.05, -0.1, 0.0, "hierro", HIERRO)
    k = a
    while k <= b + 0.01:
        f.caja(k - 0.015, k + 0.015, h0 + 0.1, h0 + 1.05, -0.08, -0.05, "hierro", HIERRO)
        k += 0.12
    for kk in (a, b):
        f.caja(kk - 0.02, kk + 0.02, h0 + 0.1, h0 + 1.05, -0.9, 0.0, "hierro", HIERRO)
        f.caja(kk - 0.02, kk + 0.02, h0 + 1.05, h0 + 1.1, -0.9, 0.0, "hierro", HIERRO)
    f.caja(a, b, h0 - 0.05, h0 + 0.1, -0.95, 0.05, "piedra", MOLDURA)                     # piso del balcón


def torre(c, f, off, s, d=-2.0):
    """Torre blanca: base de esquinas achaflanadas, cuerpo octogonal con vanos en arco, cupulín de tejas y cruz."""
    p = f.punto(s, HF + off, d)
    z0 = p.z - 0.4
    rot = math.atan2(f.u.y, f.u.x) + math.pi / 8
    _anillo(c, p.x, p.y, z0, z0 + 6.0, 2.1, "muro", BL, rot=rot)                     # base
    _anillo(c, p.x, p.y, z0 + 5.6, z0 + 6.0, 2.3, "moldura", BL2, rot=rot)
    _anillo(c, p.x, p.y, z0 + 6.0, z0 + 6.5, 1.85, "muro", BL, rot=rot)
    _anillo(c, p.x, p.y, z0 + 6.5, z0 + 9.4, 1.6, "muro", BL, rot=rot)               # cuerpo de campanas
    _anillo(c, p.x, p.y, z0 + 9.4, z0 + 9.75, 1.85, "moldura", BL2, rot=rot)
    for k in (1, 3, 5, 7):                                                            # un vano en arco por cara
        a = rot + 2 * math.pi * (k + 0.5) / 8
        ap = 1.6 * math.cos(math.pi / 8) + 0.01
        cx, cy = p.x + ap * math.cos(a), p.y + ap * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a)
        c.caja_ejes((cx, cy, z0 + 7.6), (tx, ty, 0), (math.cos(a), math.sin(a), 0), (0, 0, 1), 0.7, 0.02, 1.5,
                    "madera", "#2a2622")
        for j in range(5):
            t = math.pi * (j + 0.5) / 5
            c.caja_ejes((cx - tx * 0.35 * math.cos(t), cy - ty * 0.35 * math.cos(t), z0 + 8.35 + 0.17 * math.sin(t)),
                        (tx, ty, 0), (math.cos(a), math.sin(a), 0), (0, 0, 1), 0.18, 0.02, 0.34 * math.sin(t) + 0.02,
                        "madera", "#2a2622")
    for k in range(4):                                                                # base: vano ciego en cada cara
        a = math.atan2(f.n.y, f.n.x) + math.pi / 2 * k
        ap = 2.1 * math.cos(math.pi / 8) + 0.01
        cx, cy = p.x + ap * math.cos(a), p.y + ap * math.sin(a)
        c.caja_ejes((cx, cy, z0 + 3.4), (-math.sin(a), math.cos(a), 0), (math.cos(a), math.sin(a), 0), (0, 0, 1),
                    1.1, 0.03, 2.8, "moldura", BL2)
    # cupulín octogonal con borde de tejas
    zc = z0 + 9.75
    _anillo(c, p.x, p.y, zc, zc + 0.3, 1.95, "teja", TEJA, rot=rot)
    for j in range(5):
        t0, t1 = j / 5, (j + 1) / 5
        r0 = 1.7 * math.cos(t0 * math.pi / 2) + 0.06
        r1 = 1.7 * math.cos(t1 * math.pi / 2) + 0.06
        c.cilindro(p.x, p.y, zc + 0.3 + 1.6 * math.sin(t0 * math.pi / 2), zc + 0.3 + 1.6 * math.sin(t1 * math.pi / 2),
                   r0, "muro", BL, lados=8, radio_arriba=r1)
    c.cilindro(p.x, p.y, zc + 1.9, zc + 2.3, 0.2, "muro", BL, lados=8)
    c.esfera(p.x, p.y, zc + 2.45, 0.18, "muro", BL, segmentos=8)
    c.caja(p.x - 0.035, p.y - 0.035, zc + 2.55, p.x + 0.035, p.y + 0.035, zc + 3.5, "hierro", HIERRO)
    c.caja_ejes((p.x, p.y, zc + 3.15), (f.u.x, f.u.y, 0), (f.n.x, f.n.y, 0), (0, 0, 1), 0.55, 0.05, 0.05,
                "hierro", HIERRO)


def base_torre_colon(c, f_costado, off, desde, s0, s1, alto):
    """Bloque liso de la base de la torre sobre Colón (R0179), con faja e imposta, esquina en cuarto bocel."""
    fa = adelantada(f_costado, 0.01)
    f_costado.caja(s0, s1, desde, alto + off, 0.0, 0.3, "zocalo_piedra", "#b07d68")
    sillares(adelantada(f_costado, 0.3), s0, s1, 0.0, 4.2 + off, 0.0, semilla=301)
    from san_felipe_costado import piedra_chica
    piedra_chica(adelantada(f_costado, 0.3), s0, s1, 4.3 + off, alto + off - 0.4, 0.0, semilla=302)
    f_costado.caja(s0, s1, 4.15 + off, 4.35 + off, 0.0, 0.42, "piedra", "#c09a80")
    f_costado.caja(s0 - 0.05, s1 + 0.05, alto - 0.4 + off, alto + off, 0.0, 0.55, "moldura", "#c9a58c")
    f_costado.caja(s1 - 0.5, s1, desde, alto + off, 0.0, 0.5, "zocalo_piedra", "#c5a088")   # cuarto bocel


def frente(c, f, off, L):
    st = (2.75, L - 2.75)
    cuerpo(c, f, off, L)
    campanario(c, f, off, L, st)
    for s in st:
        torre(c, f, off, s)


def muro_atrio(c, tramos, z_vereda, interior, alto=2.3):
    """Muro del atrio (R0099, R0100, R0102, R0179): sillares de arenisca hasta `alto` sobre la vereda, cornisa, balaustrada
    de balaustres cortos y pedestales con pináculo de bulbo cada ~2,4 m. tramos: [((x, y), (x, y)), ...] en planta;
    z_vereda(x, y) da el suelo exterior; interior: un punto dentro del atrio (la cara de sillares mira al otro lado)."""
    from kit.nucleo import Fachada
    for a, b in tramos:
        Lt = math.hypot(b[0] - a[0], b[1] - a[1])
        if Lt < 0.3:
            continue
        ux, uy = (b[0] - a[0]) / Lt, (b[1] - a[1]) / Lt
        if -uy * (interior[0] - a[0]) + ux * (interior[1] - a[1]) > 0:
            a, b = b, a
            ux, uy = -ux, -uy
        zs = max(z_vereda(a[0], a[1]), z_vereda(b[0], b[1]))
        z0 = min(z_vereda(a[0], a[1]), z_vereda(b[0], b[1])) - 0.5
        lado = {"a": (a[0] - uy * 0.35, a[1] + ux * 0.35), "b": (b[0] - uy * 0.35, b[1] + ux * 0.35), "normal": (-uy, ux)}
        f = Fachada(c, lado, zs)
        f.caja(0.0, Lt, z0 - zs, alto, -0.7, 0.0, "zocalo_piedra", "#a97c62")
        sillares(adelantada(f, 0.0), 0.0, Lt, z0 - zs + 0.4, alto - 0.05, 0.0, alto=0.48, largo=(0.6, 1.1), colores=PIEDRA,
                 rojo=0.26, semilla=int(abs(a[0]) * 3))
        f.caja(-0.05, Lt + 0.05, alto, alto + 0.18, -0.8, 0.12, "piedra", MOLDURA)
        f.caja(-0.05, Lt + 0.05, alto + 0.98, alto + 1.13, -0.78, 0.1, "piedra", MOLDURA)
        n = max(1, round(Lt / 2.4))
        paso = Lt / n
        for j in range(n + 1):
            s = j * paso
            f.caja(s - 0.3, s + 0.3, alto + 0.18, alto + 0.98, -0.7, 0.05, "piedra", "#bb8c6c")
            q = f.punto(s, alto + 1.13, -0.33)
            c.caja(q.x - 0.24, q.y - 0.24, q.z, q.x + 0.24, q.y + 0.24, q.z + 0.35, "piedra", CLARA)
            c.cilindro(q.x, q.y, q.z + 0.35, q.z + 0.55, 0.13, "piedra", MOLDURA, lados=8)
            c.esfera(q.x, q.y, q.z + 0.72, 0.2, "piedra", CLARA, segmentos=8)
            c.cilindro(q.x, q.y, q.z + 0.88, q.z + 1.15, 0.08, "piedra", MOLDURA, lados=6, radio_arriba=0.02)
            if j < n:
                k = s + 0.5
                while k < s + paso - 0.4:
                    f.cilindro_vertical(k, alto + 0.18, alto + 0.42, -0.35, 0.1, "piedra", CLARA, lados=8)
                    f.cilindro_vertical(k, alto + 0.42, alto + 0.68, -0.35, 0.14, "piedra", CLARA, lados=8)
                    f.cilindro_vertical(k, alto + 0.68, alto + 0.98, -0.35, 0.08, "piedra", CLARA, lados=8)
                    k += 0.36
