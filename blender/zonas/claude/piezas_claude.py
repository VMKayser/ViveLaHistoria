"""Piezas propias de claude (complementan el kit sin modificarlo)."""

import math

from kit import arquitectura as A
from kit import datos
from kit.nucleo import Fachada


# --------------------------------------------------------------------------- huellas


def partir_huella(huella, a, u, s_corte):
    """Corta una huella con la recta perpendicular a la dirección u que pasa a s_corte de 'a'.

    Devuelve (parte con s < s_corte, parte con s >= s_corte). Las huellas del lienzo no siguen los
    límites reales de las casas: así se reparte una huella entre dos casas vistas en las fotos.
    """
    def s(p):
        return (p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1] - s_corte

    def recortar(pts, signo):
        out = []
        for p, q in zip(pts, pts[1:] + pts[:1]):
            sp, sq = signo * s(p), signo * s(q)
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq)
                out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
        return out

    pts = [tuple(p) for p in huella]
    return recortar(pts, -1), recortar(pts, 1)


def lado_virtual(a, b, normal):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return {"i": -1, "a": tuple(a), "b": tuple(b), "largo": L, "normal": tuple(normal), "a_calle": True, "calle": ""}


def adelantada(f, d=0.065):
    """Copia de la fachada f adelantada d metros (para poner portones y vanos delante de un zócalo de sillares)."""
    nx, ny = f.n.x, f.n.y
    lado = {"a": (f.a.x + nx * d, f.a.y + ny * d), "b": (f.a.x + f.u.x * f.largo + nx * d, f.a.y + f.u.y * f.largo + ny * d),
            "normal": (nx, ny)}
    return Fachada(f.c, lado, f.suelo)


def punto_en_lado(lado, s):
    L = lado["largo"]
    t = s / L
    return (lado["a"][0] + (lado["b"][0] - lado["a"][0]) * t, lado["a"][1] + (lado["b"][1] - lado["a"][1]) * t)


def fachada(c, lado):
    mx, my = (lado["a"][0] + lado["b"][0]) / 2, (lado["a"][1] + lado["b"][1]) / 2
    return Fachada(c, lado, datos.altura_suelo(mx, my))


def suelo_huella(huella):
    zs = [datos.altura_suelo(x, y) for x, y in huella]
    return min(zs), max(zs)


# --------------------------------------------------------------------------- techos


def tejado_dos_aguas(c, huella, z, pendiente=26, vuelo=0.35, teja="teja", color=None, hastial="muro", color_hastial=None,
                     alto_max=2.8, cumbrera=None):
    """Tejado de tejas a dos aguas sobre el rectángulo orientado de la huella (cumbrera según el lado más largo).
    alto_max: tope de altura de la cumbrera (los tejados de Sucre son bajos; en edificios anchos baja la pendiente).
    cumbrera: dirección (dx, dy) forzada de la cumbrera, p. ej. paralela a la calle (casas coloniales: el faldón cae
    a la calle, nunca el hastial)."""
    pts = [tuple(p) for p in huella]
    # dirección del lado más largo
    best = max(zip(pts, pts[1:] + pts[:1]), key=lambda e: math.hypot(e[1][0] - e[0][0], e[1][1] - e[0][1]))
    dx, dy = best[1][0] - best[0][0], best[1][1] - best[0][1]
    if cumbrera is not None:
        dx, dy = cumbrera
    L = math.hypot(dx, dy)
    u = (dx / L, dy / L)
    v = (-u[1], u[0])
    su = [p[0] * u[0] + p[1] * u[1] for p in pts]
    sv = [p[0] * v[0] + p[1] * v[1] for p in pts]
    u0, u1, v0, v1 = min(su) - vuelo, max(su) + vuelo, min(sv) - vuelo, max(sv) + vuelo
    vm = (v0 + v1) / 2
    alto = min(alto_max, (vm - v0) * math.tan(math.radians(pendiente)))

    def P(a, b, h):
        return (u[0] * a + v[0] * b, u[1] * a + v[1] * b, z + h)

    # dos faldones con grosor
    for vb in (v0, v1):
        c.poligono([P(u0, vb, 0), P(u1, vb, 0), P(u1, vm, alto), P(u0, vm, alto)], teja, color, grosor=0.12,
                   normal_extrusion=(0, 0, 1))
    # hastiales (triángulos de muro en los extremos, sin el vuelo)
    for ua in (u0 + vuelo, u1 - vuelo):
        c.poligono([P(ua, v0 + vuelo, 0), P(ua, v1 - vuelo, 0), P(ua, vm, alto - 0.1)], hastial, color_hastial)
    # cumbrera
    c.caja_ejes(P((u0 + u1) / 2, vm, alto + 0.08), (u[0], u[1], 0), (v[0], v[1], 0), (0, 0, 1), u1 - u0, 0.3, 0.16, teja, color)
    return alto


# --------------------------------------------------------------------------- remates y adornos


def pretil_medallones(f, h, s0, s1, pilares, alto=1.1, grosor=0.3, muro=("muro", None), acento=("pintura_acento", None),
                      bolas=True):
    """Pretil con medallones redondos entre pedestales (casa esquina Ravelo/Junín)."""
    f.caja(s0, s1, h, h + alto, -grosor, 0.0, *muro)
    f.caja(s0 - 0.05, s1 + 0.05, h + alto, h + alto + 0.12, -grosor - 0.05, 0.08, *acento)  # albardilla
    f.caja(s0, s1, h, h + 0.12, -grosor, 0.06, *acento)  # zócalo del pretil
    for s in pilares:
        f.caja(s - 0.32, s + 0.32, h, h + alto + 0.25, -grosor - 0.05, 0.12, *acento)
        if bolas:
            f.cilindro_vertical(s, h + alto + 0.25, h + alto + 0.45, 0.04, 0.12, *acento)
            f.esfera(s, h + alto + 0.62, 0.04, 0.2, *acento)
    for sa, sb in zip(pilares, pilares[1:]):
        sm = (sa + sb) / 2
        f.arco(sm, 0.28, 0.07, h + alto / 2, 0.0, 0.05, *acento, segmentos=8, medio=False)


def remate_jarron(f, s, h, d=-0.1, rol="teja", color=None):
    """Jarrón/bola de terracota sobre el pretil (casas blancas de Ravelo)."""
    f.caja(s - 0.18, s + 0.18, h, h + 0.15, d - 0.18, d + 0.18, "moldura")
    f.cilindro_vertical(s, h + 0.15, h + 0.3, d, 0.1, rol, color)
    f.esfera(s, h + 0.48, d, 0.22, rol, color)


def pilastra_capitel(f, s, h0, h1, ancho=0.5, vuelo=0.1, rol="pintura_acento", color=None):
    """Pilastra con capitel (corintio estilizado: dos bloques que se abren)."""
    f.caja(s - ancho / 2, s + ancho / 2, h0, h1 - 0.45, 0.0, vuelo, rol, color)
    f.caja(s - ancho / 2 - 0.04, s + ancho / 2 + 0.04, h1 - 0.45, h1 - 0.2, 0.0, vuelo + 0.04, rol, color)
    f.caja(s - ancho / 2 - 0.1, s + ancho / 2 + 0.1, h1 - 0.2, h1, 0.0, vuelo + 0.08, rol, color)
    f.caja(s - ancho / 2 - 0.05, s + ancho / 2 + 0.05, h0, h0 + 0.25, 0.0, vuelo + 0.03, rol, color)  # basa


def ventana_arco_archivolta(f, s, h, ancho, alto, archivolta=("pintura_acento", None), balcon=True, clave=True,
                            carpinteria=("marco_ventana", None)):
    """Ventana en arco con archivolta gruesa de color y clave, con balcón de hierro."""
    A.ventana(f, s, h, ancho=ancho, alto=alto, arco=True, balcon="hierro" if balcon else None,
              moldura=archivolta[0], color_moldura=archivolta[1], carpinteria=carpinteria[0],
              color_carpinteria=carpinteria[1])
    r = ancho / 2 + 0.14
    f.arco(s, r, 0.2, h + alto, 0.0, 0.09, *archivolta, segmentos=12)
    if clave:
        f.caja(s - 0.14, s + 0.14, h + alto + r - 0.05, h + alto + r + 0.35, 0.0, 0.13, *archivolta)


# --------------------------------------------------------------------------- neoclásico (Ravelo: CNS, Farmacia La Plata)


def fronton(f, s, h, ancho, alto, rol="moldura", color=None, d=0.04, grosor=0.12):
    """Frontón triangular sobre un vano."""
    p = [f.punto(s - ancho / 2, h, d), f.punto(s + ancho / 2, h, d), f.punto(s, h + alto, d)]
    f.c.poligono(p, rol, color, grosor=grosor, normal_extrusion=tuple(f.n))
    f.caja(s - ancho / 2 - 0.05, s + ancho / 2 + 0.05, h - 0.1, h, 0.0, d + grosor + 0.02, rol, color)


def fachada_neoclasica(f, s0, s1, n_vanos, off, alto_total=10.4, portal=None, muro=("muro", "#f4f3ef"),
                       moldura=("moldura", "#c3ccd6"), sillar="#c4a181", madera="#4a2a1e", medallon=False,
                       desde=-0.6):
    """Casona neoclásica de dos plantas: planta baja de sillería con ventanas enrejadas y portal,
    planta alta con ventanas balconeras con frontón (alternando triangular y curvo), pilastras pareadas,
    friso con tableros, cornisa y pretil con tableros. off = suelo nominal - suelo de esta fachada."""
    paso = (s1 - s0) / n_vanos
    centros = [s0 + paso * (k + 0.5) for k in range(n_vanos)]
    A.zocalo(f, 4.6 + off, s0=s0, s1=s1, color=sillar, desde=desde)
    f.caja(s0, s1, 4.6 + off, 4.85 + off, 0.0, 0.18, "piedra", sillar)
    fa = adelantada(f)
    for k, s in enumerate(centros):
        if portal is not None and k == portal:
            A.puerta(fa, s, ancho=2.2, alto=4.0 + off, color=madera, moldura="piedra", color_moldura=sillar)
            if medallon:
                fa.arco(s, 0.35, 0.12, 4.15 + off + 0.0, 0.0, 0.08, "piedra", sillar, segmentos=8, medio=False)
        else:
            A.ventana(fa, s, 1.9 + off, ancho=1.2, alto=1.5, reja=True, moldura="piedra", color_moldura=sillar,
                      carpinteria="marco_ventana", color_carpinteria=madera)
        # planta alta
        A.ventana(f, s, 5.3 + off, ancho=1.2, alto=2.6, balcon="hierro", moldura=moldura[0], color_moldura=moldura[1],
                  carpinteria="marco_ventana", color_carpinteria=madera)
        if k % 2 == 0:
            fronton(f, s, 8.15 + off, 1.9, 0.5, *moldura)
        else:
            f.arco(s, 0.85, 0.12, 8.1 + off, 0.0, 0.14, *moldura, segmentos=8)
    for k in range(n_vanos + 1):  # pilastras pareadas entre vanos
        s = s0 + paso * k
        for ds in (-0.28, 0.28):
            ss = min(max(s + ds, s0 + 0.15), s1 - 0.15)
            A.pilastra(f, ss, 4.85 + off, alto_total - 1.5 + off, ancho=0.22, vuelo=0.06, rol=moldura[0],
                       color=moldura[1], capitel=True)
    A.imposta(f, alto_total - 1.5 + off, alto=0.12, vuelo=0.08, s0=s0, s1=s1, rol=moldura[0], color=moldura[1])
    for s in centros:  # tableros del friso
        f.caja(s - 1.2, s + 1.2, alto_total - 1.3 + off, alto_total - 0.85 + off, 0.0, 0.04, *moldura)
    A.cornisa(f, alto_total - 0.8 + off, vuelo=0.35, alto=0.4, s0=s0, s1=s1, rol=moldura[0], color="#e9edf1")
    A.parapeto(f, alto_total - 0.4 + off, alto=0.6, s0=s0, s1=s1, rol=muro[0], color=muro[1], albardilla="moldura")


# --------------------------------------------------------------------------- moderno


def fachada_moderna(f, s0, s1, pisos, alto_piso, off, muro=("muro", "#f2f2ef"), banda_vidrio=True, vuelo_losas=0.0,
                    escaparate=True):
    """Edificio comercial moderno simplificado: escaparates en planta baja, bandas de ventanas, losas."""
    alto = pisos * alto_piso
    if escaparate:
        f.caja(s0 + 0.3, s1 - 0.3, 0.0, 3.3 + off, 0.0, 0.04, "vidrio")
        k = s0 + 0.3
        while k <= s1 - 0.3 + 0.01:
            f.caja(k - 0.06, k + 0.06, 0.0, 3.4 + off, 0.0, 0.07, "metal", "#3a3d40")
            k += 2.4
        f.caja(s0, s1, 3.3 + off, 3.6 + off, 0.0, 0.1, "metal", "#3a3d40")
    for p in range(1, pisos):
        h = p * alto_piso + off
        if vuelo_losas:
            f.caja(s0, s1, h - 0.25, h, 0.0, vuelo_losas, *muro)
        if banda_vidrio:
            f.caja(s0 + 0.4, s1 - 0.4, h + 0.9, h + alto_piso - 0.4, 0.0, 0.03 + vuelo_losas * 0.5, "vidrio")
            k = s0 + 0.4
            while k <= s1 - 0.4 + 0.01:
                f.caja(k - 0.04, k + 0.04, h + 0.9, h + alto_piso - 0.4, 0.0, 0.06 + vuelo_losas * 0.5, *muro)
                k += 1.2
    f.caja(s0, s1, alto + off, alto + off + 0.5, -0.2, 0.05, *muro)


# --------------------------------------------------------------------------- miradores y casas sencillas


def mirador(f, s, h, ancho=2.4, alto=2.2, vuelo=0.7, base=("muro", None), madera=("marco_ventana", "#8a5a34"),
            antepecho=None):
    """Balcón cerrado (mirador) de madera y vidrio sobre ménsula. antepecho: (rol, color) del panel bajo el vidrio."""
    s0, s1 = s - ancho / 2, s + ancho / 2
    f.caja(s0, s1, h - 0.5, h, 0.0, vuelo, *base)                 # repisa
    f.caja(s0 + 0.3, s1 - 0.3, h - 0.95, h - 0.5, 0.0, vuelo * 0.6, *base)  # ménsula
    ap = antepecho or base
    f.caja(s0, s1, h, h + 0.6, vuelo - 0.08, vuelo, *ap)          # antepecho frontal
    for sx in (s0, s1 - 0.06):
        f.caja(sx, sx + 0.06, h, h + 0.6, 0.0, vuelo, *ap)        # antepechos laterales
    f.caja(s0 + 0.04, s1 - 0.04, h + 0.6, h + alto, vuelo - 0.07, vuelo - 0.03, "vidrio")
    for sx in (s0, s1 - 0.04):
        f.caja(sx, sx + 0.04, h + 0.6, h + alto, 0.02, vuelo - 0.04, "vidrio")
    n = max(2, int(ancho / 0.6))
    for k in range(n + 1):
        sx = s0 + (ancho - 0.07) * k / n
        f.caja(sx, sx + 0.07, h + 0.6, h + alto, vuelo - 0.09, vuelo - 0.01, *madera)
    for hh in (h + 0.6, h + alto * 0.72, h + alto - 0.07):
        f.caja(s0, s1, hh, hh + 0.07, vuelo - 0.09, vuelo - 0.01, *madera)
    f.caja(s0 - 0.08, s1 + 0.08, h + alto, h + alto + 0.18, 0.0, vuelo + 0.1, *base)  # tejadillo


def guardapolvo(f, s, h, ancho, color=None, rol="moldura"):
    """Cornisita sobre la ventana (guardapolvo) con dos ménsulas pequeñas: da sombra y relieve a la fachada."""
    s0, s1 = s - ancho / 2 - 0.26, s + ancho / 2 + 0.26
    f.caja(s0, s1, h, h + 0.1, 0.0, 0.2, rol, color)
    f.caja(s0 + 0.04, s1 - 0.04, h + 0.1, h + 0.18, 0.0, 0.12, rol, color)
    for x in (s0 + 0.1, s1 - 0.1):
        f.caja(x - 0.06, x + 0.06, h - 0.22, h, 0.0, 0.13, rol, color)


def mensula(f, s, h, vuelo=0.5, color=None, rol="moldura"):
    """Ménsula escalonada bajo una losa de balcón (apoya en h, sale `vuelo` m)."""
    for k, sale in enumerate((vuelo, vuelo * 0.65, vuelo * 0.35)):
        f.caja(s - 0.06, s + 0.06, h - 0.1 * (k + 1), h - 0.1 * k, 0.0, sale, rol, color)


def cortina_metalica(f, s, ancho=2.4, alto=2.9, h0=0.0, color="#8f98a1"):
    """Cortina metálica enrollable de local (fotos de Ravelo y Junín): paño con estrías horizontales, caja de
    enrollado arriba y guías laterales."""
    s0, s1 = s - ancho / 2, s + ancho / 2
    f.caja(s0, s1, h0, h0 + alto, 0.0, 0.03, "metal", color)
    h = h0 + 0.25
    while h < h0 + alto - 0.1:
        f.caja(s0 + 0.03, s1 - 0.03, h, h + 0.035, 0.0, 0.05, "metal", "#7b848d")
        h += 0.22
    f.caja(s0 - 0.08, s1 + 0.08, h0 + alto, h0 + alto + 0.4, 0.0, 0.22, "metal", "#9aa2aa")
    for x in (s0 - 0.06, s1):
        f.caja(x, x + 0.06, h0, h0 + alto, 0.0, 0.08, "metal", "#6f777f")


def portada(f, s, ancho, alto, h0=0.0, rol="piedra", color=None, cornisa=True):
    """Marco de portada alrededor de un portón (jambas que salen 12 cm, dintel y cornisita), como en las casas de
    sillería de Ravelo y Junín. h0: altura del umbral sobre el suelo de la fachada."""
    j = 0.32
    s0, s1 = s - ancho / 2 - j, s + ancho / 2 + j
    f.caja(s0, s0 + j, h0, h0 + alto, 0.0, 0.12, rol, color)
    f.caja(s1 - j, s1, h0, h0 + alto, 0.0, 0.12, rol, color)
    f.caja(s0, s1, h0 + alto, h0 + alto + 0.38, 0.0, 0.12, rol, color)
    if cornisa:
        f.caja(s0 - 0.12, s1 + 0.12, h0 + alto + 0.38, h0 + alto + 0.5, 0.0, 0.22, rol, color)


def casa_sencilla(f, s0, s1, pisos, alto_piso, off, muro=("muro", "#f6f4ef"), zocalo_alto=1.0, zocalo_color="#b98e6e",
                  vanos=None, miradores=(), balcones=(), puertas=(), remate="cornisa", acento=None,
                  carpinteria=("marco_ventana", "#5a3422"), desde=-0.6, comercio=True):
    """Casa urbana blanca sencilla. vanos: lista de s de los vanos (por defecto 1 cada ~3.5 m).
    miradores/balcones/puertas: s de los vanos que llevan mirador (piso alto), balcón de hierro o portón (planta baja).
    remate: 'cornisa' | 'alero' | 'pinaculos' (pretil con remates del color 'acento')."""
    largo = s1 - s0
    if vanos is None:
        n = max(1, round(largo / 3.5))
        vanos = [s0 + largo * (k + 0.5) / n for k in range(n)]
    A.zocalo(f, zocalo_alto + off, s0=s0, s1=s1, color=zocalo_color, desde=desde)
    fa = adelantada(f)
    alto = pisos * alto_piso
    for s in vanos:
        if any(abs(s - p) < 0.5 for p in puertas) and comercio and (int(abs(s) * 7.3 + largo * 3.1) % 5) < 2:
            # local con cortina metálica (muy frecuentes en Ravelo y Junín)
            cortina_metalica(fa, s, ancho=min(2.4, (largo / max(1, len(vanos))) - 0.6), alto=min(2.9, alto_piso - 1.0),
                             h0=off, color=["#8f98a1", "#5f7fa6", "#9aa0a3"][int(abs(s) * 3.7) % 3])
        elif any(abs(s - p) < 0.5 for p in puertas):
            A.puerta(fa, s, ancho=1.5, alto=min(3.0, alto_piso - 0.8) + off, color=carpinteria[1], moldura="moldura",
                     color_moldura=muro[1], almohadillado=True)
            portada(fa, s, 1.5, min(3.0, alto_piso - 0.8), h0=off, rol="moldura", color=muro[1],
                    cornisa=(hash(round(s, 1)) % 2 == 0))
        else:
            A.ventana(fa, s, 1.4 + off, ancho=1.1, alto=1.7, reja=True, moldura="moldura", color_moldura=muro[1],
                      carpinteria=carpinteria[0], color_carpinteria=carpinteria[1])
        for p in range(1, pisos):
            h = p * alto_piso + off
            if any(abs(s - q) < 0.5 for q in miradores):
                mirador(f, s, h + 0.4, base=muro)
            else:
                con_balcon = any(abs(s - q) < 0.5 for q in balcones)
                A.ventana(f, s, h + 0.4, ancho=1.1, alto=2.1, balcon="hierro" if con_balcon
                          else None, moldura="moldura", color_moldura=muro[1], carpinteria=carpinteria[0],
                          color_carpinteria=carpinteria[1])
                guardapolvo(f, s, h + 0.4 + 2.1 + 0.16, 1.1, muro[1])
                if con_balcon:
                    for dm in (-0.65, 0.65):          # ménsulas bajo la losa del balcón
                        mensula(f, s + dm, h + 0.4, 0.38, muro[1])
    for p in range(1, pisos):
        A.imposta(f, p * alto_piso + off - 0.1, alto=0.14, vuelo=0.06, s0=s0, s1=s1, rol="moldura", color=muro[1])
    if remate == "alero":
        A.alero_tejas(f, alto + off - 0.1, s0=s0, s1=s1, vuelo=0.7)
    else:
        A.cornisa(f, alto + off - 0.35, vuelo=0.25, alto=0.35, s0=s0, s1=s1, rol="moldura", color=muro[1])
        A.parapeto(f, alto + off, alto=0.55, s0=s0, s1=s1, rol=muro[0], color=muro[1])
        if remate == "pinaculos":
            k = s0 + 0.4
            while k < s1:
                f.caja(k - 0.15, k + 0.15, alto + off + 0.55, alto + off + 0.75, -0.15, 0.1, "pintura_acento", acento)
                f.esfera(k, alto + off + 0.88, -0.02, 0.15, "pintura_acento", acento)
                k += 2.2


# --------------------------------------------------------------------------- arquería con enjutas lisas


def arqueria_lisa(f, s0, n, luz, h_arranque, pilar=0.6, d0=-0.5, d1=0.0, alto_total=None, muro=("muro", None),
                  moldura=("moldura", None), segmentos=14):
    """Como kit.arquitectura.arqueria, pero las enjutas son polígonos que siguen el arco (sin escalones)."""
    r = luz / 2
    alto_total = alto_total or h_arranque + r + 0.8
    s = s0
    for k in range(n + 1):
        f.caja(s, s + pilar, 0.0, h_arranque, d0, d1, *muro)
        f.caja(s, s + pilar, h_arranque, alto_total, d0, d1, *muro)       # muro sobre el pilar hasta el remate (R0227:
        #                                                                  sin él, el arco quedaba como una banda delgada)
        f.caja(s - 0.05, s + pilar + 0.05, h_arranque - 0.18, h_arranque, d0 - 0.05, d1 + 0.05, *moldura)
        if k < n:
            cs = s + pilar + r
            f.arco(cs, r, 0.2, h_arranque, d1 - 0.01, d1 + 0.04, *moldura, segmentos=segmentos)
            for lado in (-1, 1):
                pts = []
                for j in range(segmentos // 2 + 1):
                    a = math.pi / 2 * j / (segmentos // 2)  # 0 = arranque, pi/2 = clave
                    pts.append((cs + lado * r * math.cos(a), h_arranque + r * math.sin(a)))
                borde = cs + lado * r
                pts += [(cs, alto_total), (borde + lado * (pilar / 2 if 0 else 0.0), alto_total)]
                poli = [f.punto(ss, hh, d0) for ss, hh in pts]
                if lado == -1:
                    poli.reverse()
                f.c.poligono(poli, *muro, grosor=d1 - d0, normal_extrusion=tuple(f.n))
            s = cs + r
    f.caja(s0, s + pilar, alto_total, alto_total + 0.25, d0 - 0.06, d1 + 0.06, *moldura)
    return s + pilar


# --------------------------------------------------------------------------- arbolado


def arbol(c, x, y, z, alto=5.5, copa=2.4, semilla=0):
    """Árbol de vereda estilizado como en un fondo pintado: tronco que se abre en dos ramas y copa de masas de
    follaje de distinto tamaño (cuerpo oscuro, masas medias y cima clara), más ancha que alta y con el borde irregular."""
    import random
    rnd = random.Random(semilla)
    c.cilindro(x, y, z - 0.3, z + alto * 0.45, 0.17, "tronco", lados=7, radio_arriba=0.12)
    zc = z + alto * 0.66
    # dos ramas que abren la copa
    for lado in (-1, 1):
        a = rnd.uniform(0, math.pi) + (math.pi if lado < 0 else 0)
        bx, by = x + math.cos(a) * copa * 0.22, y + math.sin(a) * copa * 0.22
        c.cilindro((x + bx) / 2, (y + by) / 2, z + alto * 0.42, zc, 0.07, "tronco", lados=5)
    masas = 9
    for k in range(masas):
        a = 2 * math.pi * k / masas + rnd.uniform(-0.3, 0.3)
        rad = copa * rnd.uniform(0.18, 0.42)
        r = copa * rnd.uniform(0.30, 0.46)
        alto_k = rnd.uniform(-0.1, 0.25) * copa
        rol = "follaje_claro" if (k % 3 == 0 and alto_k > 0.05 * copa) else "follaje"
        c.esfera(x + math.cos(a) * rad, y + math.sin(a) * rad, zc + alto_k, r, rol, segmentos=9)
    c.esfera(x, y, zc + 0.38 * copa, copa * 0.4, "follaje_claro", segmentos=9)   # cima iluminada


def arbol_catalogo(c, x, y, z, alto=5.5, copa=2.4, semilla=0):
    """[A prueba, no en uso: el usuario prefirió los anteriores (2026-11-23); se volverán a probar.] Árbol de vereda: uno del catálogo elegido por el usuario (CommonTree o TwistedTree, Quaternius CC0), con la copa
    del ancho pedido (copa = diámetro en m)."""
    from arboles_catalogo import poner, radio_copa
    esp = "comun" if semilla % 3 else "retorcido"
    alto = max(alto * 1.25, 5.5)
    poner(c, esp, x, y, z - 0.05, alto, semilla=semilla, ancho=max(0.7, min(1.6, copa / 2 / radio_copa(esp, alto))))


def arbol_paraguas(c, x, y, z, alto=5.2, copa=4.2, semilla=0, encalado=True, alcorque=True, desplazar=(0.0, 0.0)):
    """Árbol de vereda podado en paraguas (Mercado Central, fotos 130206–130218): tronco con el pie encalado, tres
    ramas abiertas y copa ancha y aplanada; alcorque cuadrado con bordillo."""
    import random
    rnd = random.Random(semilla)
    zr = z + alto * 0.5
    ox, oy = desplazar           # copa corrida (podada del lado de la fachada, crece hacia la calle)
    c.cilindro(x, y, z - 0.2, zr, 0.17, "tronco", lados=7, radio_arriba=0.13)
    if encalado:
        c.cilindro(x, y, z - 0.05, z + 1.0, 0.185, "muro", "#f4f2ec", lados=7)
    ramas = []
    for k in range(3):
        a = 2 * math.pi * k / 3 + rnd.uniform(-0.4, 0.4)
        p = (x + ox + math.cos(a) * copa * 0.28, y + oy + math.sin(a) * copa * 0.28, z + alto * 0.8)
        c.cilindro(x, y, zr - 0.1, zr + 0.1, 0.12, "tronco", lados=6)
        dx, dy, dz = p[0] - x, p[1] - y, p[2] - zr
        L = math.sqrt(dx * dx + dy * dy + dz * dz)
        ex = (dx / L, dy / L, dz / L)
        ey = (-ex[1], ex[0], 0.0)
        n = math.hypot(*ey[:2]) or 1
        ey = (ey[0] / n, ey[1] / n, 0)
        ez = (ex[1] * ey[2] - ex[2] * ey[1], ex[2] * ey[0] - ex[0] * ey[2], ex[0] * ey[1] - ex[1] * ey[0])
        c.caja_ejes(((x + p[0]) / 2, (y + p[1]) / 2, (zr + p[2]) / 2), ex, ey, ez, L, 0.16, 0.16, "tronco")
        ramas.append(p)
    zc = z + alto * 0.88
    r = copa / 2
    c.esfera(x + ox, y + oy, zc + 0.25, r * 0.55, "follaje_claro", segmentos=9)
    for k in range(7):
        a = 2 * math.pi * k / 7 + rnd.uniform(-0.2, 0.2)
        c.esfera(x + ox + math.cos(a) * r * 0.62, y + oy + math.sin(a) * r * 0.62, zc + rnd.uniform(-0.15, 0.1),
                 r * rnd.uniform(0.42, 0.5), "follaje" if k % 3 else "follaje_claro", segmentos=8)
    for k in range(5):   # masas claras sobre la copa: cima con volumen, no un disco liso
        a = 2 * math.pi * k / 5 + rnd.uniform(-0.3, 0.3)
        c.esfera(x + ox + math.cos(a) * r * 0.35, y + oy + math.sin(a) * r * 0.35, zc + 0.3 + rnd.uniform(0, 0.25),
                 r * rnd.uniform(0.3, 0.4), "follaje_claro", segmentos=8)
    if alcorque:
        for dx, dy, sx, sy in ((0.6, 0, 0.12, 1.32), (-0.6, 0, 0.12, 1.32), (0, 0.6, 1.32, 0.12), (0, -0.6, 1.32, 0.12)):
            c.caja(x + dx - sx / 2, y + dy - sy / 2, z - 0.1, x + dx + sx / 2, y + dy + sy / 2, z + 0.22, "piedra", "#b8afa3")


def arbol_paraguas_catalogo(c, x, y, z, alto=5.2, copa=4.2, semilla=0, encalado=True, alcorque=True, desplazar=(0.0, 0.0)):
    """[A prueba, no en uso: el usuario prefirió los anteriores (2026-11-23); se volverán a probar.] Árbol de vereda podado (Mercado Central, fotos 130206–130218): CommonTree del catálogo (Quaternius CC0) más ancho
    que alto, con el pie encalado y alcorque cuadrado con bordillo. desplazar: la copa crece hacia la calle."""
    from arboles_catalogo import poner, radio_copa
    alto = max(alto * 1.2, 5.5)
    poner(c, "comun", x + desplazar[0] * 0.3, y + desplazar[1] * 0.3, z - 0.05, alto, semilla=semilla,
          ancho=max(0.8, min(1.8, copa / 2 / radio_copa("comun", alto))), encalado=1.0 if encalado else 0.0)
    if alcorque:
        for dx, dy, sx, sy in ((0.6, 0, 0.12, 1.32), (-0.6, 0, 0.12, 1.32), (0, 0.6, 1.32, 0.12), (0, -0.6, 1.32, 0.12)):
            c.caja(x + dx - sx / 2, y + dy - sy / 2, z - 0.1, x + dx + sx / 2, y + dy + sy / 2, z + 0.22, "piedra", "#b8afa3")


# --------------------------------------------------------------------------- calles con ancho real


def lado_lienzo(e, i, real=False):
    """Lado i de la huella ORIGINAL del lienzo (los scripts con foto se midieron sobre ella), llevado a la fachada real:
    el kit recorta las huellas al ancho real de la calle (reparto/calles_reales.json).

    real=True: si la huella recortada tiene un lado equivalente (misma orientación, ±25°, y que se superpone con éste), se usa ESE
    lado: así la fachada coincide exactamente con el volumen y no invade la calle ni la calle transversal en las
    esquinas (auditoría 2026-11-12: con el corrimiento en paralelo, en las calles oblicuas la fachada quedaba 1–2 m
    delante del volumen). Usarlo para FACHADAS; para marcos de referencia (ejes t de un script) se deja real=False,
    que corre el lado en paralelo hasta el punto más saliente de la huella."""
    from kit.datos import lados as _lados
    l = dict([x for x in _lados(e.get("huella_lienzo", e["huella"])) if x["i"] == i][0])
    nx, ny = l["normal"]
    a = l["a"]
    ux, uy = (l["b"][0] - a[0]) / l["largo"], (l["b"][1] - a[1]) / l["largo"]
    mejor = None
    for r in (_lados(e["huella"]) if real else []):
        if r["largo"] < 1.0:
            continue
        cos = r["normal"][0] * nx + r["normal"][1] * ny
        if cos < math.cos(math.radians(25)):
            continue
        sa = (r["a"][0] - a[0]) * ux + (r["a"][1] - a[1]) * uy
        sb = (r["b"][0] - a[0]) * ux + (r["b"][1] - a[1]) * uy
        solape = min(max(sa, sb), l["largo"]) - max(min(sa, sb), 0.0)
        dist = abs(((r["a"][0] + r["b"][0]) / 2 - a[0]) * nx + ((r["a"][1] + r["b"][1]) / 2 - a[1]) * ny)
        if solape > 0.4 * min(l["largo"], r["largo"]) and dist < 4.5:
            puntaje = solape - dist * 2
            if not mejor or puntaje > mejor[0]:
                mejor = (puntaje, r)
    if mejor:
        r = dict(mejor[1])
        r["i"] = i
        r["retroceso"] = round(abs(((r["a"][0] - a[0]) * nx + (r["a"][1] - a[1]) * ny)), 2)
        return r
    s = max((p[0] - a[0]) * nx + (p[1] - a[1]) * ny for p in e["huella"])
    if s < -0.02:
        l["a"] = (l["a"][0] + nx * s, l["a"][1] + ny * s)
        l["b"] = (l["b"][0] + nx * s, l["b"][1] + ny * s)
        l["retroceso"] = round(-s, 2)
    return l


# --------------------------------------------------------------------------- techo colonial con patio


def _simplificar(pts, min_lado=0.6, tol_ang=8.0):
    """Quita vértices casi alineados y lados muy cortos (las huellas del lienzo traen mucho ruido)."""
    p = [tuple(q) for q in pts]
    cambio = True
    while cambio and len(p) > 3:
        cambio = False
        for i in range(len(p)):
            a, b, c_ = p[i - 1], p[i], p[(i + 1) % len(p)]
            l1 = math.hypot(b[0] - a[0], b[1] - a[1])
            l2 = math.hypot(c_[0] - b[0], c_[1] - b[1])
            if l1 < 1e-6 or l2 < 1e-6:
                p.pop(i)
                cambio = True
                break
            cr = ((b[0] - a[0]) * (c_[1] - b[1]) - (b[1] - a[1]) * (c_[0] - b[0])) / (l1 * l2)
            if abs(math.degrees(math.asin(max(-1, min(1, cr))))) < tol_ang and \
                    ((b[0] - a[0]) * (c_[0] - b[0]) + (b[1] - a[1]) * (c_[1] - b[1])) > 0:
                p.pop(i)
                cambio = True
                break
            if l2 < min_lado and len(p) > 4:
                p.pop((i + 1) % len(p))
                cambio = True
                break
    return p


def _area_firmada(p):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(p, p[1:] + p[:1])) / 2


def desplazar_poligono(pts, d):
    """Polígono CCW desplazado d m hacia ADENTRO (d < 0: hacia afuera), con esquinas en inglete."""
    n = len(pts)
    lineas = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L          # izquierda = adentro (CCW)
        lineas.append(((a[0] + nx * d, a[1] + ny * d), (b[0] - a[0], b[1] - a[1])))
    res = []
    for i in range(n):
        (p, r), (q, s) = lineas[i - 1], lineas[i]
        den = r[0] * s[1] - r[1] * s[0]
        if abs(den) < 1e-9:
            res.append(q)
            continue
        t = ((q[0] - p[0]) * s[1] - (q[1] - p[1]) * s[0]) / den
        res.append((p[0] + r[0] * t, p[1] + r[1] * t))
    return res


def _se_cruzan(p):
    n = len(p)

    def cruza(a, b, c_, d):
        o = lambda p1, p2, p3: (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0])
        return (o(a, b, c_) > 0) != (o(a, b, d) > 0) and (o(c_, d, a) > 0) != (o(c_, d, b) > 0)

    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if cruza(p[i], p[(i + 1) % n], p[j], p[(j + 1) % n]):
                return True
    return False


def _dp(pts, tol):
    """Douglas–Peucker sobre un polígono cerrado (arranca en los dos vértices más alejados entre sí)."""
    n = len(pts)
    if n <= 4:
        return pts
    i0 = 0
    i1 = max(range(n), key=lambda i: math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]))

    def rama(a, b):
        idx = list(range(a, b + 1)) if b >= a else list(range(a, n)) + list(range(0, b + 1))
        seg = [pts[i] for i in idx]

        def rec(lo, hi):
            p, q = seg[lo], seg[hi]
            L = math.hypot(q[0] - p[0], q[1] - p[1]) or 1e-9
            mejor, k = 0.0, None
            for j in range(lo + 1, hi):
                d = abs((q[0] - p[0]) * (p[1] - seg[j][1]) - (p[0] - seg[j][0]) * (q[1] - p[1])) / L
                if d > mejor:
                    mejor, k = d, j
            if k is None or mejor <= tol:
                return [seg[lo]]
            return rec(lo, k) + rec(k, hi)
        return rec(0, len(seg) - 1)

    return rama(i0, i1) + rama(i1, i0)


def _anillos(P, d, paso=0.5):
    """Encoge el polígono CCW P paso a paso hasta d (esqueleto recto simplificado: los lados que colapsan se
    quitan). Devuelve [(t, [(id_lado, inicio, fin), ...])] o None si aparece un cruce (evento de división)."""
    n = len(P)
    lineas = []
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        lineas.append((a, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)))

    def vertices(vivos, t):
        lin = []
        for i in vivos:
            (a, u) = lineas[i]
            lin.append(((a[0] - u[1] * t, a[1] + u[0] * t), u))
        pts = []
        m = len(lin)
        for k in range(m):
            (p, r), (q, s_) = lin[k - 1], lin[k]
            den = r[0] * s_[1] - r[1] * s_[0]
            if abs(den) < 1e-9:
                pts.append(q)
                continue
            tt = ((q[0] - p[0]) * s_[1] - (q[1] - p[1]) * s_[0]) / den
            pts.append((p[0] + r[0] * tt, p[1] + r[1] * tt))
        return pts

    vivos = list(range(n))
    res = []
    pasos = max(2, int(math.ceil(d / paso)))
    for k in range(pasos + 1):
        t = d * k / pasos
        while True:
            if len(vivos) < 3:
                return None
            pts = vertices(vivos, t)
            muertos = []
            for j, i in enumerate(vivos):
                a, b = pts[j], pts[(j + 1) % len(vivos)]
                u = lineas[i][1]
                if (b[0] - a[0]) * u[0] + (b[1] - a[1]) * u[1] <= 0.02:
                    muertos.append(i)
            if not muertos:
                break
            # se quita de a uno (el más corto) para no saltear eventos encadenados
            vivos.remove(min(muertos, key=lambda i: math.hypot(
                pts[(vivos.index(i) + 1) % len(vivos)][0] - pts[vivos.index(i)][0],
                pts[(vivos.index(i) + 1) % len(vivos)][1] - pts[vivos.index(i)][1])))
        if _se_cruzan(pts):
            return None
        res.append((t, [(i, pts[j], pts[(j + 1) % len(vivos)]) for j, i in enumerate(vivos)]))
    return res


def techo_colonial(c, huella, z, zpatio, fondo=None, pendiente=24, vuelo=0.45, alto_max=2.4, teja=("teja", None),
                   muro=("muro", None), suelo_patio=("adoquin", "#c4ab90"), min_area=200, plantas=False):
    """Techo de tejas a dos aguas en ANILLO alrededor de un patio interior (casa colonial de Sucre, como se ve en
    la imagen satelital). Los entrantes cortos de la huella se resuelven como limatesas (el faldón termina en
    punta). Devuelve False si la huella no admite patio (chica o muy irregular): usar otro techo.

    fondo: ancho de la crujía techada (por defecto ~30 % del lado menor, 4,5–7 m).
    zpatio: nivel del piso del patio.
    """
    P0 = _simplificar(datos.orientar_ccw([tuple(p) for p in huella]))
    if len(P0) < 3 or _area_firmada(P0) < min_area:
        return False
    a, b = max(zip(P0, P0[1:] + P0[:1]), key=lambda e: math.hypot(e[1][0] - e[0][0], e[1][1] - e[0][1]))
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    sv = [-p[0] * u[1] + p[1] * u[0] for p in P0]
    menor = max(sv) - min(sv)
    d0 = fondo or max(4.5, min(7.0, menor * 0.3))
    anillos = None
    for tol in (0.0, 0.5, 1.2):
        P = _simplificar(_dp(P0, tol)) if tol else P0
        if len(P) < 3 or len(P) > 24:
            continue
        for d in (d0, d0 * 0.8, max(3.5, d0 * 0.65)):
            if menor < 2 * d + 3.0:
                continue
            an = _anillos(P, d)
            if an and _area_firmada([q for _, q, _ in an[-1][1]]) >= 15:
                anillos = an
                break
        if anillos:
            break
    if not anillos:
        return False
    h = min(alto_max, d / 2 * math.tan(math.radians(pendiente)))
    alto = lambda t: h * (t / (d / 2)) if t <= d / 2 else h * (d - t) / (d / 2)
    # alero: el primer anillo se corre hacia afuera `vuelo` m (con la misma pendiente)
    t0, r0 = anillos[0]
    caida = vuelo * h / (d / 2)
    if vuelo > 0:
        n0 = len(r0)
        alero = []
        for j, (i, a_, b_) in enumerate(r0):
            alero.append(i)
        E = desplazar_poligono([a_ for _, a_, _ in r0], -vuelo)
        r_e = [(i, E[j], E[(j + 1) % n0]) for j, (i, _, _) in enumerate(r0)]
        anillos = [(-vuelo, r_e)] + anillos
    alto_t = lambda t: -caida if t < 0 else alto(t)
    for (ta, ra), (tb, rb) in zip(anillos, anillos[1:]):
        za, zb_ = z + alto_t(ta), z + alto_t(tb)
        en_b = {i: (p, q) for i, p, q in rb}
        orden_b = [i for i, _, _ in rb]
        for i, pa, qa in ra:
            if i in en_b:
                pb, qb = en_b[i]
                c.poligono([(pa[0], pa[1], za), (qa[0], qa[1], za), (qb[0], qb[1], zb_), (pb[0], pb[1], zb_)],
                           teja[0], teja[1])
            else:
                # el lado murió: triángulo hasta el vértice de B donde se juntaron sus vecinos
                sig = None
                ids_a = [x for x, _, _ in ra]
                k = ids_a.index(i)
                for m in range(1, len(ids_a)):
                    cand = ids_a[(k + m) % len(ids_a)]
                    if cand in en_b:
                        sig = cand
                        break
                if sig is None:
                    continue
                v = en_b[sig][0]
                c.poligono([(pa[0], pa[1], za), (qa[0], qa[1], za), (v[0], v[1], zb_)], teja[0], teja[1])
    # cumbrera sobre el anillo de la mitad
    tm = min(anillos, key=lambda x: abs(x[0] - d / 2))
    for i, p, q in tm[1]:
        dx, dy = q[0] - p[0], q[1] - p[1]
        Lr = math.hypot(dx, dy)
        if Lr > 0.3:
            c.caja_ejes(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, z + alto(tm[0]) + 0.06), (dx / Lr, dy / Lr, 0),
                        (-dy / Lr, dx / Lr, 0), (0, 0, 1), Lr + 0.15, 0.26, 0.14, teja[0], teja[1])
    # muro del patio y piso
    Q = [p for _, p, _ in anillos[-1][1]]
    for p, q in zip(Q, Q[1:] + Q[:1]):
        c.poligono([(q[0], q[1], zpatio - 0.3), (p[0], p[1], zpatio - 0.3), (p[0], p[1], z), (q[0], q[1], z)],
                   muro[0], muro[1])
    c.tapa(Q, zpatio, *suelo_patio)
    if plantas:
        _plantas_patio(c, Q, zpatio)
    return True


def _plantas_patio(c, Q, z):
    """Patio colonial vivo (vista aérea 2026-11-13: los patios eran pisos lisos): un árbol en el centro si hay sitio,
    macetas en las esquinas y, en los patios grandes, una fuente de piedra."""
    import random
    area = abs(_area_firmada(Q))
    if area < 40:
        return
    cx = sum(p[0] for p in Q) / len(Q)
    cy = sum(p[1] for p in Q) / len(Q)
    if not datos._dentro(cx, cy, Q):
        return
    dmin = min(math.hypot(cx - (a[0] + (b[0] - a[0]) * t), cy - (a[1] + (b[1] - a[1]) * t))
               for a, b in zip(Q, Q[1:] + Q[:1]) for t in (0.0, 0.25, 0.5, 0.75))
    rnd = random.Random(int(abs(cx * 7 + cy * 13)))
    if area > 220 and dmin > 4.0:
        c.cilindro(cx, cy, z, z + 0.5, 1.2, "piedra", "#c9bba5", lados=14)
        c.cilindro(cx, cy, z + 0.38, z + 0.46, 1.0, "agua", "#6d9fb5", lados=14)
        c.cilindro(cx, cy, z + 0.5, z + 1.3, 0.15, "piedra", "#c9bba5", lados=8)
        for k in range(2):
            a = rnd.uniform(0, 6.28)
            r = min(dmin - 1.8, 3.2)
            arbol(c, cx + math.cos(a + k * 3.1) * r, cy + math.sin(a + k * 3.1) * r, z, alto=rnd.uniform(4.0, 5.5),
                  copa=rnd.uniform(1.8, 2.4), semilla=rnd.randint(0, 999))
    elif dmin > 1.8:
        arbol(c, cx, cy, z, alto=rnd.uniform(3.8, 5.2), copa=min(2.4, dmin * 1.1), semilla=rnd.randint(0, 999))
    # macetas en las esquinas del patio
    for p in Q[:4]:
        dx, dy = cx - p[0], cy - p[1]
        L = math.hypot(dx, dy) or 1
        if L < 1.5:
            continue
        x, y = p[0] + dx / L * 0.7, p[1] + dy / L * 0.7
        c.cilindro(x, y, z, z + 0.4, 0.22, "teja", "#b55a3a", lados=7, radio_arriba=0.28)
        c.esfera(x, y, z + 0.6, 0.32, "follaje", segmentos=6)


def techo_auto(c, huella, z, zpatio=None, muro=("muro", None), vuelo=0.0, **kw):
    """Techo de tejas con patio si la huella lo admite; si no, azotea plana. Sin alero por defecto: queda detrás de
    pretiles y cornisas de las fachadas neoclásicas."""
    if zpatio is None:
        zpatio = suelo_huella(huella)[0]
    if not techo_colonial(c, huella, z + 0.02, zpatio, vuelo=vuelo, muro=muro, **kw):
        A.techo_plano(c, huella, z)


def envolvente(*huellas):
    """Envolvente convexa de varias huellas: huella de un objeto que ocupa partes de más de una huella del lienzo
    (p. ej. la casa esquina de M020), para que el recorte a medianeras al exportar no le corte la fachada."""
    pts = sorted({(round(p[0], 3), round(p[1], 3)) for h in huellas for p in h})

    def cruz(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    inf, sup = [], []
    for q in pts:
        while len(inf) >= 2 and cruz(inf[-2], inf[-1], q) <= 0:
            inf.pop()
        inf.append(q)
    for q in reversed(pts):
        while len(sup) >= 2 and cruz(sup[-2], sup[-1], q) <= 0:
            sup.pop()
        sup.append(q)
    return inf[:-1] + sup[:-1]


def junto_al_bordillo(x, y, nx, ny, retiro=0.5):
    """Punto sobre la vereda a `retiro` m del bordillo, partiendo de un punto de la fachada (x, y) con su normal hacia
    la calle (nx, ny). Árboles y postes van ahí (usuario: "siempre cerca del borde de la acera")."""
    cr = datos.calle_real_cercana(x, y)
    if not cr:
        return x + nx * 1.6, y + ny * 1.6
    d_eje, ancho, vereda, _ = cr
    hasta_bordillo = d_eje - (ancho / 2 - vereda)
    d = max(0.4, hasta_bordillo - retiro)
    return x + nx * d, y + ny * d


def tramo_calle(nombre, ref):
    """Eje real (calles_reales) del tramo de `nombre` más cercano al punto `ref`: lista de puntos."""
    mejor = None
    for c in datos.calles_reales():
        if c["nombre"] != nombre:
            continue
        d = min(math.hypot(p[0] - ref[0], p[1] - ref[1]) for p in c["eje"])
        if mejor is None or d < mejor[0]:
            mejor = (d, c)
    return mejor[1]


def sobre_calle(c, t, d):
    """Punto a t m a lo largo del eje del tramo c y a d m a su IZQUIERDA (d < 0: derecha); devuelve (x, y, ux, uy)."""
    eje = c["eje"]
    for p, q in zip(eje, eje[1:]):
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if t <= L or q is eje[-1]:
            ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
            return p[0] + ux * t - uy * d, p[1] + uy * t + ux * d, ux, uy
        t -= L


def al_bordillo(nombre, x, y, retiro=0.45):
    """(x, y) llevado a `retiro` m del bordillo de la calle `nombre`, sobre la vereda del mismo lado (medido desde el eje
    real del tramo más próximo). Para postes y faroles: siguen al bordillo aunque cambie el ancho de la calle o el eje se
    quiebre cerca de una esquina."""
    mejor = None
    for c in datos.calles_reales():
        if c["nombre"] != nombre:
            continue
        for p, q in zip(c["eje"], c["eje"][1:]):
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            if L < 0.3:
                continue
            ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
            t = max(0.0, min(L, (x - p[0]) * ux + (y - p[1]) * uy))
            d = -(x - p[0]) * uy + (y - p[1]) * ux
            dist = math.hypot(x - p[0] - ux * t, y - p[1] - uy * t)
            if mejor is None or dist < mejor[0]:
                mejor = (dist, c, p, ux, uy, t, d)
    if mejor is None:
        return x, y
    _, c, p, ux, uy, t, d = mejor
    lado = 1.0 if d >= 0 else -1.0
    v = c.get("vereda_izq" if lado > 0 else "vereda_der", c["vereda"])
    dd = lado * (c["ancho"] / 2 - v + retiro)
    return p[0] + ux * t - uy * dd, p[1] + uy * t + ux * dd


def fondo_libre(x, y, nx, ny, maximo=10.0, paso=0.25):
    """Cuánto se puede ir hacia adentro (dirección nx, ny) desde (x, y) sin entrar en otra huella del lienzo."""
    hs = datos.edificios_recortados()
    d = 0.0
    while d < maximo:
        if any(datos._dentro(x + nx * d, y + ny * d, h) for h in hs):
            return max(0.0, d - 0.1)
        d += paso
    return maximo


def casas_de_frente(col, prefijo, c, lado, casas, t0, fondo_max=10.0):
    """Hilera de casas SOBRE LA LÍNEA DE FACHADA de un tramo de calle (para cerrar un frente sin huellas del
    lienzo). `casas` es la lista DISEÑADA a mano para esa cuadra: (ancho, pisos, alto_piso, muro, remate, opciones)
    con opciones de casa_sencilla. Cada casa va solo con el fondo libre hasta la huella de atrás (máx. fondo_max):
    detrás no se agrega nada. lado: +1 izquierda del eje, −1 derecha."""
    from kit.nucleo import Constructor
    objs = []
    w = c["ancho"] / 2
    t = t0
    for k, (ancho, pisos, alto_piso, muro, remate, op) in enumerate(casas):
        xa, ya, ux, uy = sobre_calle(c, t, lado * w)
        xb, yb, _, _ = sobre_calle(c, t + ancho, lado * w)
        adentro = (-uy * lado, ux * lado)                  # de la fachada hacia el interior de la cuadra
        # fondo libre medido cada metro del frente (con solo 3 muestras una casa se metía de costado en un vecino)
        muestras = [0.3] + [float(k) for k in range(1, int(ancho))] + [ancho - 0.3]
        fondo = op.get("fondo") or min(fondo_libre(xa + ux * m, ya + uy * m, *adentro, maximo=fondo_max) for m in muestras)
        if fondo < 2.5:
            t += ancho
            continue
        h = [(xa, ya), (xb, yb), (xb + adentro[0] * fondo, yb + adentro[1] * fondo),
             (xa + adentro[0] * fondo, ya + adentro[1] * fondo)]
        h = datos.orientar_ccw(h)
        cc = Constructor(f"{prefijo}_{k}")
        cc.huella = h
        zb, zr = suelo_huella(h)
        alto = pisos * alto_piso
        cc.prisma(h, zb - 0.6, zr + alto, "muro", muro, tapa=True)
        if remate == "alero":
            tejado_dos_aguas(cc, h, zr + alto, pendiente=24, cumbrera=(ux, uy))
        lado_f = lado_virtual((xa, ya), (xb, yb), (-adentro[0], -adentro[1]))
        f = fachada(cc, lado_f)
        if "a_mano" in op:      # fachada modelada a mano para esa casa (desde su foto): fn(f, ancho, alto, off, desde)
            op["a_mano"](f, ancho, alto, zr - f.suelo, zb - 0.6 - f.suelo)
        else:
            casa_sencilla(f, 0.0, ancho, pisos, alto_piso, zr - f.suelo, muro=("muro", muro), remate=remate,
                          desde=zb - 0.6 - f.suelo, **{k: v for k, v in op.items() if k not in ("fondo", "esquina")})
        esq = op.get("esquina")
        if esq in ("inicio", "fin"):
            # casa de esquina: también lleva fachada en el costado que da a la calle transversal (o a la plaza); sin
            # esto el costado quedaba como un muro liso a la vista (revisión por MCP, 2026-11-24, esquina O de la plaza)
            px, py = (xb, yb) if esq == "fin" else (xa, ya)
            q = (px + adentro[0] * fondo, py + adentro[1] * fondo)
            fuera = (ux, uy) if esq == "fin" else (-ux, -uy)
            a_, b_ = ((px, py), q) if (fuera[0] * (q[1] - py) - fuera[1] * (q[0] - px)) > 0 else (q, (px, py))
            fc = fachada(cc, lado_virtual(a_, b_, fuera))
            n_ = max(1, round(fondo / 3.4))
            vanos_c = [fondo * (i + 0.5) / n_ for i in range(n_)]
            casa_sencilla(fc, 0.0, fondo, pisos, alto_piso, zr - fc.suelo, muro=("muro", muro), remate=remate,
                          desde=zb - 0.6 - fc.suelo, vanos=vanos_c, puertas=[], balcones=vanos_c[::2])
        objs.append(cc.objeto(col))
        t += ancho
    return objs


def hilera_sobre_linea(col, prefijo, a, b, casas, fondo=9.0, libres=(), libre=3.0):
    """Hilera de casas con la fachada sobre la recta a→b mirando a su DERECHA (como los lados de una huella en sentido
    antihorario): para frentes que dan a una plaza o plazuela y no a una calle. `casas` como en casas_de_frente; el
    cuerpo tiene `fondo` m hacia la izquierda y no lleva nada más detrás."""
    from kit.nucleo import Constructor
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, ny = uy, -ux                                      # derecha = hacia la plaza
    objs, t = [], 0.0
    for k, (ancho, pisos, alto_piso, muro, remate, op) in enumerate(casas):
        if t + ancho > L + 0.01:
            break
        pa = (a[0] + ux * t, a[1] + uy * t)
        pb = (a[0] + ux * (t + ancho), a[1] + uy * (t + ancho))
        h = datos.orientar_ccw([pa, pb, (pb[0] - nx * fondo, pb[1] - ny * fondo), (pa[0] - nx * fondo, pa[1] - ny * fondo)])
        # libres: puntos que deben quedar despejados (donde camina el usuario); la casa se corta o se omite
        for cx, cy in libres:
            dfa = (cx - pa[0]) * nx + (cy - pa[1]) * ny          # > 0: delante de la fachada
            ds = (cx - pa[0]) * ux + (cy - pa[1]) * uy
            if -libre < ds < ancho + libre and dfa > -fondo - libre and dfa < libre:
                h = None
                break
        if h is not None:
            h = datos.recortar_a_calles(h, area_min=8)       # sin meterse en ninguna calle
        if h is None or len(h) < 3:
            t += ancho
            continue
        cc = Constructor(f"{prefijo}_{k}")
        cc.huella = h
        zb, zr = suelo_huella(h)
        alto = pisos * alto_piso
        cc.prisma(h, zb - 0.6, zr + alto, "muro", muro, tapa=True)
        if remate == "alero":
            tejado_dos_aguas(cc, h, zr + alto, pendiente=24, cumbrera=(ux, uy))
        f = fachada(cc, lado_virtual(pa, pb, (nx, ny)))
        if "a_mano" in op:      # fachada modelada a mano para esa casa (desde su foto): fn(f, ancho, alto, off, desde)
            op["a_mano"](f, ancho, alto, zr - f.suelo, zb - 0.6 - f.suelo)
        else:
            casa_sencilla(f, 0.0, ancho, pisos, alto_piso, zr - f.suelo, muro=("muro", muro), remate=remate,
                          desde=zb - 0.6 - f.suelo, **{k: v for k, v in op.items() if k not in ("fondo", "esquina")})
        objs.append(cc.objeto(col))
        t += ancho
    return objs


def _a_altura(f, h):
    """Copia de la fachada f con el suelo subido h m (para apoyar cada paño de un muro largo en la pendiente)."""
    return Fachada(f.c, {"a": (f.a.x, f.a.y), "b": (f.a.x + f.u.x * f.largo, f.a.y + f.u.y * f.largo),
                         "normal": (f.n.x, f.n.y)}, f.suelo + h)


def reja_hierro(f, s, ancho=3.2, alto=2.8):
    """Portón de hierro forjado en arco rebajado (atrios de la Catedral, fotos 130844–130851)."""
    n = max(6, int(ancho / 0.16))
    for k in range(n + 1):
        x = s - ancho / 2 + ancho * k / n
        cima = alto + 0.45 * math.sin(math.pi * k / n)
        f.cilindro_vertical(x, 0.0, cima, 0.02, 0.022, "hierro", "#232323", lados=6)
    for h in (0.25, 1.2, alto - 0.1):
        f.caja(s - ancho / 2, s + ancho / 2, h, h + 0.05, 0.0, 0.05, "hierro", "#232323")
    for k in range(int(ancho / 0.45)):                                   # roleos
        x = s - ancho / 2 + 0.3 + k * 0.45
        f.arco(x, 0.16, 0.03, 1.5, 0.0, 0.04, "hierro", "#232323", medio=False, segmentos=8)


def linea_muro_plaza():
    """Lado del muro del atrio de la Catedral que da a la Plaza 25 de Mayo (el mismo que usa M056): dict a/b/normal.
    Sale de la fachada lateral de la Catedral desplazada hasta el borde de la calle (recortar_a_calles)."""
    cat = datos.edificio("M055", "E03fe1d")
    fcat = Fachada(None, datos.lados(cat["huella"])[0], 0)
    a0 = fcat.punto(-14.0, 0, 22.3)
    b0 = fcat.punto(36.5, 0, 23.55)
    h = datos.recortar_a_calles([tuple(a0[:2]), tuple(b0[:2]), tuple(fcat.punto(36.5, 0)[:2]),
                                 tuple(fcat.punto(-14.0, 0)[:2])])
    ls = [ll for ll in datos.lados(h) if ll["a_calle"]]
    return max(ls, key=lambda ll: ll["normal"][0] * fcat.n.x + ll["normal"][1] * fcat.n.y)


def esquina_atrio_ortiz(cat_a):
    """Esquina del atrio de la Catedral entre el muro de Nicolás Ortiz y el de la Plaza 25 de Mayo (donde va el pilar
    con la cruz, R0169): cruce de la recta del muro de Ortiz con la del muro de la plaza (`linea_muro_plaza`).
    cat_a: un punto de la Catedral (para saber de qué lado de Ortiz está el muro). Devuelve
    (t, (x, y), lado): t = distancia sobre el eje de Ortiz hasta la esquina, lado = lado del muro (+1/-1)."""
    ortiz = tramo_calle("Calle Nicolás Ortiz", (-200.0, -320.0))
    (ox0, oy0), (ox1, oy1) = ortiz["eje"][0], ortiz["eje"][-1]
    Lo = math.hypot(ox1 - ox0, oy1 - oy0)
    uox, uoy = (ox1 - ox0) / Lo, (oy1 - oy0) / Lo
    lado = 1 if ((cat_a[0] - ox0) * -(oy1 - oy0) + (cat_a[1] - oy0) * (ox1 - ox0)) > 0 else -1
    wx0, wy0 = ox0 - uoy * lado * ortiz["ancho"] / 2, oy0 + uox * lado * ortiz["ancho"] / 2
    lp = linea_muro_plaza()
    (qx0, qy0), (qx1, qy1) = lp["a"], lp["b"]
    Lq = math.hypot(qx1 - qx0, qy1 - qy0)
    upx, upy = (qx1 - qx0) / Lq, (qy1 - qy0) / Lq
    den = uox * upy - uoy * upx
    t = ((qx0 - wx0) * upy - (qy0 - wy0) * upx) / den
    return t, (wx0 + uox * t, wy0 + uoy * t), lado


def _mezclar(c1, c2, t):
    """Mezcla dos colores #rrggbb (t = peso de c2)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def pilar_esquina_cruz(c, x, y, z, n_plaza, n_ortiz, color="#b07f66"):
    """Pilar de piedra con la cruz en la esquina del atrio (R0110, R0169): basamento escalonado, cuerpo con tableros y
    grandes volutas en cada cara, cornisa, remate abombado y cruz alta. (x, y) = vértice donde se juntan los dos muros;
    n_plaza / n_ortiz: normales hacia afuera de cada muro."""
    from mathutils import Vector
    ex = Vector((n_plaza[0], n_plaza[1], 0))
    ey = Vector((n_ortiz[0], n_ortiz[1], 0))
    ez = Vector((0, 0, 1))
    claro = _mezclar(color, "#e3cdb0", 0.45)
    oscuro = _mezclar(color, "#5a3a2c", 0.3)
    cx, cy = x - n_plaza[0] * 0.95 - n_ortiz[0] * 0.95, y - n_plaza[1] * 0.95 - n_ortiz[1] * 0.95

    def bloque(z0, z1, w, rol_c, dx=0.0, dy=0.0):
        c.caja_ejes(Vector((cx + ex.x * dx + ey.x * dy, cy + ex.y * dx + ey.y * dy, z + (z0 + z1) / 2)),
                    ex, ey, ez, w, w, z1 - z0, "piedra", rol_c)

    bloque(-0.4, 0.4, 2.3, oscuro)                      # basamento
    bloque(0.4, 0.55, 2.4, claro)                       # moldura
    bloque(0.55, 1.0, 2.0, color)                       # segundo escalón
    bloque(1.0, 3.1, 1.6, color)                        # cuerpo
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):  # pilastras de esquina más claras
        bloque(1.05, 3.05, 0.34, claro, sx * 0.72, sy * 0.72)
    c.caja_ejes(Vector((cx + ex.x * 0.83, cy + ex.y * 0.83, z + 2.0)), ex, ey, ez, 0.06, 0.9, 1.5, "piedra", oscuro)
    c.caja_ejes(Vector((cx + ey.x * 0.83, cy + ey.y * 0.83, z + 2.0)), ex, ey, ez, 0.9, 0.06, 1.5, "piedra", oscuro)
    # volutas (ménsulas enrolladas) en las caras de la plaza y de Ortiz: disco grueso + ceja
    for vx, vy in ((0.86, 0.0), (0.0, 0.86)):
        px, py = cx + ex.x * vx + ey.x * vy, cy + ex.y * vx + ey.y * vy
        c.cilindro(px, py, z + 1.25, z + 1.6, 0.26, "piedra", color, lados=10)
        c.cilindro(px, py, z + 1.28, z + 1.57, 0.14, "piedra", oscuro, lados=8)
    bloque(3.1, 3.35, 2.0, claro)                       # cornisa
    bloque(3.35, 3.55, 1.5, color)
    c.cilindro(cx, cy, z + 3.55, z + 4.4, 0.62, "piedra", color, lados=8, radio_arriba=0.4)   # remate abombado
    bloque(4.4, 4.6, 0.95, claro)
    bloque(4.6, 6.0, 0.28, claro)                       # fuste de la cruz (dos piezas, ver nota en cerramiento_atrio)
    bloque(6.0, 7.6, 0.27, claro)
    c.caja_ejes(Vector((cx, cy, z + 6.7)), ex, ey, ez, 1.2, 0.28, 0.26, "piedra", claro)      # brazos


def cerramiento_atrio(c, f, puertas=(), color="#a77b60", ancho_puerta=3.2):
    """Muro de atrio de sillería rojiza con balaustrada y pilares con urnas (Catedral, R0110, R0164–R0166 y fotos
    130844–130851), por paños de ~7 m apoyados en el terreno; portones de hierro en las posiciones `puertas`.
    Alturas (R0164: "el muro de cerca es más alto"): zócalo 0,4, sillería hasta 1,5, cornisa, balaustres hasta 2,6,
    pasamanos y pilares de 3,05 con urna."""
    z = f.suelo
    cortes = [0.0]
    while cortes[-1] + 7.0 < f.largo - 1.0:
        cortes.append(cortes[-1] + 7.0)
    cortes.append(f.largo)
    tramos = list(zip(cortes, cortes[1:]))
    for ps in puertas:
        nuevos = []
        for aa, bb in tramos:
            if aa < ps < bb:
                if ps - ancho_puerta / 2 - aa > 0.3:
                    nuevos.append((aa, ps - ancho_puerta / 2))
                if bb - ps - ancho_puerta / 2 > 0.3:
                    nuevos.append((ps + ancho_puerta / 2, bb))
            else:
                nuevos.append((aa, bb))
        tramos = nuevos
    claro = _mezclar(color, "#e3cdb0", 0.45)          # juntas y piezas de piedra más clara (arenisca)
    oscuro = _mezclar(color, "#5a3a2c", 0.3)
    for aa, bb in tramos:
        p = f.punto((aa + bb) / 2, 0)
        local_z = datos.altura_suelo(p.x, p.y) + 0.12
        ff = _a_altura(f, local_z - z)
        pa, pb = f.punto(aa, 0), f.punto(bb, 0)
        desde = min(datos.altura_suelo(pa.x, pa.y), datos.altura_suelo(pb.x, pb.y)) - 0.2 - local_z
        ff.caja(aa, bb, desde, 0.42, -0.42, 0.04, "piedra", oscuro)               # basamento saliente
        ff.caja(aa, bb, 0.42, 0.5, -0.38, 0.07, "piedra", claro)                   # moldura del basamento
        ff.caja(aa, bb, 0.5, 1.5, -0.34, 0, "piedra", color)                       # cuerpo de sillería
        # hiladas de sillería: juntas horizontales cada 0,5 m y verticales alternadas cada ~1,1 m
        for k, h in enumerate((0.95, 1.4)):
            ff.caja(aa, bb, h - 0.012, h + 0.012, -0.005, 0.012, "piedra", claro)
            ss = aa + (0.55 if k % 2 else 0.0) + 0.55
            while ss < bb - 0.2:
                ff.caja(ss - 0.012, ss + 0.012, 0.5 if k == 0 else 0.95, 0.95 if k == 0 else 1.4, -0.005, 0.012,
                        "piedra", claro)
                ss += 1.1
        ff.caja(aa, bb, 1.5, 1.66, -0.4, 0.1, "piedra", claro)                     # cornisa
        ff.caja(aa, bb, 1.66, 1.72, -0.34, 0.04, "piedra", color)
        n = max(1, round((bb - aa) / 0.46))
        for i in range(n + 1):
            ss = aa + (bb - aa) * i / n
            ff.cilindro_vertical(ss, 1.72, 2.12, -0.15, 0.13, "piedra", color, lados=6)
            ff.cilindro_vertical(ss, 2.12, 2.6, -0.15, 0.06, "piedra", color, lados=6)
        # los dos conos a la vez: base ancha abajo (balaustre de bulbo) y cuello fino arriba
        ff.caja(aa, bb, 2.58, 2.76, -0.4, 0.1, "piedra", claro)                     # pasamanos
        ff.caja(aa, bb, 2.76, 2.82, -0.36, 0.06, "piedra", color)
    for ss in sorted({x for t in tramos for x in t}):
        p = f.punto(ss, 0)
        ff = _a_altura(f, datos.altura_suelo(p.x, p.y) + 0.12 - z)
        ff.caja(ss - 0.3, ss + 0.3, -0.2, 2.55, -0.42, 0.16, "piedra", color)          # pilar (en dos piezas: calidad.py
        ff.caja(ss - 0.29, ss + 0.29, 2.55, 3.0, -0.41, 0.15, "piedra", color)         # confunde una columna alta con un poste)
        ff.caja(ss - 0.34, ss + 0.34, 0.45, 0.58, -0.46, 0.2, "piedra", claro)         # base moldurada
        ff.caja(ss - 0.2, ss + 0.2, 1.8, 2.5, 0.16, 0.2, "piedra", oscuro)            # tablero en relieve
        ff.caja(ss - 0.4, ss + 0.4, 3.0, 3.16, -0.5, 0.24, "piedra", claro)            # capitel
        q = ff.punto(ss, 3.16, -0.13)
        c.cilindro(q.x, q.y, q.z, q.z + 0.34, 0.21, "piedra", color, lados=8, radio_arriba=0.12)
        c.esfera(q.x, q.y, q.z + 0.46, 0.17, "piedra", claro, segmentos=8)
    for ps in puertas:
        p = f.punto(ps, 0)
        # entre las caras de los pilares (0,3 m de medio ancho cada uno): con 0,2 m menos asomaba por delante de ellos
        reja_hierro(_a_altura(f, datos.altura_suelo(p.x, p.y) + 0.12 - z), ps, ancho=ancho_puerta - 0.64)


# --------------------------------------------------------------------------- relieve de fachada en lados libres
# kit/medianeras.py corta cada objeto con un plano sobre cada lado convexo de su huella: a VUELO_CALLE (1 m) si el lado
# "da a la calle" y a +2 cm si no. `datos.lados` decide "da a la calle" por la distancia al eje de la calle, así que un
# frente que cae lejos del eje (la Gobernación y la Catedral sobre la plaza, las casas de la Plazuela Cochabamba) quedaba
# cortado a ras: balaustradas, pilastras, marcos y molduras aplanados (R0160: "le falta mucho detalle"). Al importar este
# módulo, los lados que no tocan a otro edificio (nada a 3 m hacia afuera) también pueden volar hasta VUELO_CALLE; los
# medianeros siguen cortados a ras. kit/ no se edita: se sustituye `medianeras.planos` en este proceso.
from kit import medianeras as _med  # noqa: E402
from mathutils import Vector as _V  # noqa: E402


def _planos_con_vuelo(huella):
    h = _med._ccw(huella)
    otros = datos.edificios_recortados()
    res = []
    for l in datos.lados(h):
        a, b, n = _V((*l["a"], 0)), _V((*l["b"], 0)), _V((*l["normal"], 0))
        if any((_V((p[0], p[1], 0)) - a).dot(n) > 0.05 for p in h):
            continue                                                     # lado cóncavo: no se corta
        libre = False
        if not l["a_calle"]:
            mx, my = (a.x + b.x) / 2 + n.x * 3.0, (a.y + b.y) / 2 + n.y * 3.0
            libre = not any(datos._dentro(mx, my, o) for o in otros)
        d = _med.VUELO_CALLE if (l["a_calle"] or libre) else _med.HOLGURA
        res.append((a + n * d, n))
    return res


_med.planos = _planos_con_vuelo
