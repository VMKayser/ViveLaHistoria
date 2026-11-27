"""Piezas de arquitectura colonial de Sucre, en el estilo del proyecto.

Todas trabajan sobre una Fachada (ver nucleo.py): s = a lo largo, h = altura, d = salida a la calle.
Las medidas por defecto son las típicas del centro histórico; ajústalas con lo que muestran las fotos.
"""

import math

from . import datos
from .nucleo import Constructor, Fachada

# --------------------------------------------------------------------------- muros y bandas


def zocalo(f, alto=1.2, s0=0.0, s1=None, rol="zocalo_piedra", color=None, sillares=True, desde=-0.6):
    """Basamento de piedra. Con sillares=True dibuja hiladas con juntas hundidas (se ven como líneas de sombra)."""
    s1 = f.largo if s1 is None else s1
    f.caja(s0, s1, desde, alto, 0.0, 0.03, rol, color)
    if not sillares:
        return
    hilada, pieza, junta = 0.42, 0.85, 0.035
    h, fila = 0.0, 0
    while h < alto - 0.05:
        h1 = min(alto, h + hilada)
        s = s0 - (pieza / 2 if fila % 2 else 0)
        while s < s1:
            a, b = max(s0, s + junta / 2), min(s1, s + pieza - junta / 2)
            if b - a > 0.05:
                f.caja(a, b, h + junta / 2, h1 - junta / 2, 0.03, 0.06, rol, color)
            s += pieza
        h, fila = h1, fila + 1
    # remate del zócalo
    f.caja(s0, s1, alto - 0.08, alto + 0.04, 0.0, 0.09, rol, color)


def imposta(f, h, alto=0.18, vuelo=0.08, s0=0.0, s1=None, rol="moldura", color=None):
    """Banda horizontal entre pisos."""
    f.caja(s0, f.largo if s1 is None else s1, h, h + alto, 0.0, vuelo, rol, color)


def cornisa(f, h, vuelo=0.35, alto=0.45, s0=0.0, s1=None, rol="moldura", color=None):
    """Cornisa escalonada de remate (3 molduras que salen cada vez más)."""
    s1 = f.largo if s1 is None else s1
    for k in range(3):
        f.caja(s0 - 0.03 * k, s1 + 0.03 * k, h + alto * k / 3, h + alto * (k + 1) / 3, 0.0, vuelo * (k + 1) / 3, rol, color)


def parapeto(f, h, alto=0.8, grosor=0.25, s0=0.0, s1=None, rol="muro", color=None, albardilla="moldura"):
    """Pretil sobre la cornisa (techo plano detrás)."""
    s1 = f.largo if s1 is None else s1
    f.caja(s0, s1, h, h + alto, -grosor, 0.0, rol, color)
    f.caja(s0 - 0.03, s1 + 0.03, h + alto, h + alto + 0.08, -grosor - 0.03, 0.05, albardilla)


def pilastra(f, s, h0, h1, ancho=0.45, vuelo=0.1, rol="moldura", color=None, capitel=True):
    f.caja(s - ancho / 2, s + ancho / 2, h0, h1, 0.0, vuelo, rol, color)
    if capitel:
        f.caja(s - ancho / 2 - 0.06, s + ancho / 2 + 0.06, h1 - 0.2, h1, 0.0, vuelo + 0.05, rol, color)


def almenas(f, h, alto=0.7, ancho=0.6, paso=1.2, grosor=0.4, rol="muro", color=None):
    """Almenas de remate (p. ej. edificios de aire militar)."""
    s = (f.largo % paso) / 2
    while s + ancho <= f.largo + 0.01:
        f.caja(s, s + ancho, h, h + alto, -grosor, 0.02, rol, color)
        s += paso


def remate_bola(f, s, h, d=0.0, radio=0.22, rol="piedra", color=None):
    """Pináculo con bola (como los de los pilares del portón de referencia)."""
    f.caja(s - radio * 1.1, s + radio * 1.1, h, h + radio * 0.8, d - radio * 1.1, d + radio * 1.1, rol, color)
    f.cilindro_vertical(s, h + radio * 0.8, h + radio * 1.2, d, radio * 0.45, rol, color)
    f.esfera(s, h + radio * 2.1, d, radio, rol, color)


# --------------------------------------------------------------------------- vanos


def ventana(f, s, h, ancho=1.1, alto=2.0, arco=False, reja=False, balcon=None, postigos=False,
            moldura="moldura", color_moldura=None, carpinteria="marco_ventana", color_carpinteria=None):
    """Ventana centrada en s con alféizar en h.

    arco: remate de medio punto. reja: barrotes de hierro delante.
    balcon: None | "hierro" (balcón volado con baranda) | "corrido" (lo mismo; usar balcon_corrido para varios vanos).
    """
    s0, s1 = s - ancho / 2, s + ancho / 2
    h1 = h + alto
    m, mc = moldura, color_moldura
    # moldura exterior (yeso o piedra)
    e = 0.14
    f.caja(s0 - e, s0, h - 0.05, h1, 0.0, 0.06, m, mc)
    f.caja(s1, s1 + e, h - 0.05, h1, 0.0, 0.06, m, mc)
    if arco:
        r = ancho / 2
        f.arco(s, r, e, h1, 0.0, 0.06, m, mc)
        f.timpano_arco(s, r, h1, 0.006, "vidrio")
        f.arco(s, r - 0.07, 0.07, h1, 0.0, 0.035, carpinteria, color_carpinteria)
    else:
        f.caja(s0 - e - 0.05, s1 + e + 0.05, h1, h1 + 0.16, 0.0, 0.09, m, mc)  # dintel
    f.caja(s0 - e - 0.04, s1 + e + 0.04, h - 0.12, h, 0.0, 0.12, m, mc)  # alféizar
    # vidrio y carpintería
    f.caja(s0, s1, h, h1, 0.0, 0.006, "vidrio")
    k = 0.07
    cc = carpinteria, color_carpinteria
    f.caja(s0, s0 + k, h, h1, 0.0, 0.035, *cc)
    f.caja(s1 - k, s1, h, h1, 0.0, 0.035, *cc)
    f.caja(s0, s1, h, h + k, 0.0, 0.035, *cc)
    f.caja(s0, s1, h1 - k, h1, 0.0, 0.035, *cc)
    f.caja(s - 0.025, s + 0.025, h, h1, 0.0, 0.03, *cc)
    for t in (0.36, 0.68):
        f.caja(s0, s1, h + alto * t - 0.02, h + alto * t + 0.02, 0.0, 0.03, *cc)
    if postigos:
        f.caja(s0 - 0.55 * ancho, s0 - e, h, h1, 0.0, 0.05, *cc)
        f.caja(s1 + e, s1 + 0.55 * ancho, h, h1, 0.0, 0.05, *cc)
    if reja:
        _barrotes(f, s0 + 0.04, s1 - 0.04, h + 0.02, h1 + (ancho / 2 if arco else 0) - 0.05, 0.1, 0.13)
    if balcon:
        balcon_hierro(f, s0 - 0.35, s1 + 0.35, h)


def puerta(f, s, ancho=1.6, alto=3.0, arco=False, rol="madera", color=None, moldura="piedra", color_moldura=None,
           almohadillado=True):
    """Portón de madera de dos hojas con marco de piedra (o yeso)."""
    s0, s1 = s - ancho / 2, s + ancho / 2
    e = 0.22
    f.caja(s0 - e, s0, 0.0, alto, 0.0, 0.1, moldura, color_moldura)
    f.caja(s1, s1 + e, 0.0, alto, 0.0, 0.1, moldura, color_moldura)
    if arco:
        f.arco(s, ancho / 2, e, alto, 0.0, 0.1, moldura, color_moldura)
        f.timpano_arco(s, ancho / 2, alto, 0.01, rol, color)
    else:
        f.caja(s0 - e - 0.08, s1 + e + 0.08, alto, alto + 0.3, 0.0, 0.14, moldura, color_moldura)
    f.caja(s0, s - 0.015, 0.0, alto, 0.0, 0.03, rol, color)
    f.caja(s + 0.015, s1, 0.0, alto, 0.0, 0.03, rol, color)
    if almohadillado:  # cuarterones en relieve
        for a, b in ((s0 + 0.12, s - 0.1), (s + 0.1, s1 - 0.12)):
            for h0 in (0.25, alto * 0.55):
                f.caja(a, b, h0, h0 + alto * 0.3, 0.03, 0.06, rol, color)


def _barrotes(f, s0, s1, h0, h1, d, paso, radio=0.012):
    n = max(2, int((s1 - s0) / paso))
    for k in range(n + 1):
        f.cilindro_vertical(s0 + (s1 - s0) * k / n, h0, h1, d, radio, "hierro", lados=4)
    for h in (h0 + 0.05, (h0 + h1) / 2, h1 - 0.05):
        f.caja(s0, s1, h - 0.015, h + 0.015, d - 0.015, d + 0.015, "hierro")


def balcon_hierro(f, s0, s1, h, vuelo=0.6, alto_baranda=1.0, losa="piedra", color_losa=None):
    """Balcón volado: losa de piedra con baranda de hierro."""
    f.caja(s0, s1, h - 0.16, h, 0.0, vuelo, losa, color_losa)
    for k in range(int((s1 - s0) / 0.9) + 1):  # ménsulas
        s = s0 + 0.15 + k * 0.9
        if s < s1 - 0.1:
            f.caja(s - 0.06, s + 0.06, h - 0.45, h - 0.16, 0.0, vuelo * 0.7, losa, color_losa)
    d = vuelo - 0.05
    _barrotes(f, s0 + 0.05, s1 - 0.05, h, h + alto_baranda, d, 0.12)
    for s in (s0 + 0.05, s1 - 0.05):  # laterales
        for k in range(1, 4):
            f.cilindro_vertical(s, h, h + alto_baranda, d * k / 4, 0.012, "hierro", lados=4)
    f.caja(s0, s1, h + alto_baranda - 0.03, h + alto_baranda + 0.03, d - 0.04, d + 0.04, "hierro")


def balcon_corrido(f, s0, s1, h, **kw):
    """Un balcón largo que une varias ventanas del piso alto."""
    balcon_hierro(f, s0, s1, h, **kw)


# --------------------------------------------------------------------------- techos


def alero_tejas(f, h, vuelo=0.85, fondo=3.0, pendiente=22, s0=0.0, s1=None, canes=True, teja="teja",
                color_teja=None, madera="madera"):
    """Tejado colonial a un agua hacia la calle, con canes (vigas) de madera vistos bajo el alero.

    h: altura del arranque en el muro. El faldón sube hacia adentro 'fondo' metros.
    """
    s1 = f.largo if s1 is None else s1
    t = math.tan(math.radians(pendiente))
    largo = (vuelo + fondo) / math.cos(math.radians(pendiente))  # largo del faldón medido en la pendiente
    sube = (-f.n + f.z * t).normalized()  # dirección de la pendiente (hacia adentro y arriba)
    perp = f.u.cross(sube).normalized()
    if perp.z < 0:
        perp = -perp
    centro = f.punto((s0 + s1) / 2, h + 0.12, vuelo) + sube * (largo / 2)
    f.c.caja_ejes(centro, f.u, sube, perp, s1 - s0 + 0.3, largo, 0.12, teja, color_teja)
    # canales de teja: listones redondeados a lo largo de la pendiente
    paso = 0.3
    n = int((s1 - s0 + 0.3) / paso)
    for k in range(n):
        s = s0 - 0.15 + paso * (k + 0.5)
        c = f.punto(s, h + 0.2, vuelo) + sube * (largo / 2) + perp * 0.03
        f.c.caja_ejes(c, f.u, sube, perp, 0.15, largo + 0.05, 0.1, teja, color_teja)
    # boca de teja en el borde
    f.caja(s0 - 0.15, s1 + 0.15, h + 0.02, h + 0.2, vuelo - 0.06, vuelo + 0.04, teja, color_teja)
    if canes:
        s = s0 + 0.3
        while s < s1 - 0.1:
            f.caja(s - 0.07, s + 0.07, h - 0.18, h + 0.02, -0.05, vuelo - 0.08, madera)
            s += 0.65
        f.caja(s0, s1, h - 0.06, h + 0.02, -0.05, vuelo - 0.05, madera)  # tablazón


def techo_plano(c, huella, z, rol="azotea", color=None):
    c.tapa(huella, z, rol, color)


# --------------------------------------------------------------------------- arcos


def arqueria(f, s0, n, luz, h_arranque, pilar=0.6, d0=0.0, d1=0.5, alto_total=None, rol="muro", color=None,
             moldura="moldura", color_moldura=None):
    """Fila de n arcos de medio punto sobre pilares, empezando en s0. Devuelve el s final.

    Sirve para arquerías y portadas (p. ej. el muro de arcos de San Francisco).
    """
    r = luz / 2
    alto_total = alto_total or h_arranque + r + 0.8
    s = s0
    for k in range(n + 1):
        f.caja(s, s + pilar, 0.0, h_arranque, d0, d1, rol, color)  # pilar
        f.caja(s - 0.05, s + pilar + 0.05, h_arranque - 0.18, h_arranque, d0 - 0.05, d1 + 0.05, moldura, color_moldura)
        if k < n:
            cs = s + pilar + r
            f.arco(cs, r, 0.18, h_arranque, d1 - 0.01, d1 + 0.03, moldura, color_moldura)
            # enjutas: relleno entre arcos hasta alto_total
            _enjuta(f, cs, r, h_arranque, alto_total, d0, d1, rol, color)
            s = cs + r
    f.caja(s0, s + pilar, alto_total, alto_total + 0.25, d0 - 0.06, d1 + 0.06, moldura, color_moldura)
    return s + pilar


def _enjuta(f, cs, r, h0, h1, d0, d1, rol, color, seg=8):
    for lado in (-1, 1):
        for k in range(seg):
            a0 = math.pi / 2 * k / seg
            a1 = math.pi / 2 * (k + 1) / seg
            x0, x1 = r * math.sin(a0), r * math.sin(a1)
            hb = h0 + r * math.cos(a1)
            sa, sb = sorted((cs + lado * x0, cs + lado * x1))
            f.caja(sa, sb, hb, h1, d0, d1, rol, color)


# --------------------------------------------------------------------------- edificio genérico


def edificio_colonial(nombre, huella, pisos=2, alto_piso=4.2, color_muro=None, zocalo_alto=1.3,
                      remate="cornisa", ventanas_por_lado=None, puerta_en=None, balcones=True,
                      arcos=False, lados_calle=None, coleccion=None, biselar=0.0):
    """Casa colonial típica a partir de una huella. Punto de partida: luego se ajusta con las fotos.

    remate: "cornisa" (cornisa + pretil, techo plano), "alero" (tejado de tejas hacia la calle) o "almenas".
    ventanas_por_lado: {indice_lado: n} para forzar cuántos vanos tiene cada fachada (por defecto 1 cada ~4 m).
    puerta_en: {indice_lado: s} posición del portón principal; por defecto el centro del lado más largo.
    lados_calle: lista de índices de lados que dan a la calle (por defecto: los detectados por datos.lados).
    Devuelve (objeto, lista_de_lados) para seguir agregando detalles.
    """
    c = Constructor(nombre)
    lados = datos.lados(huella)
    if lados_calle is not None:
        for l in lados:
            l["a_calle"] = l["i"] in lados_calle
    alturas = [datos.altura_suelo(x, y) for x, y in huella]
    z_base = min(alturas) - 0.6
    suelo_max = max(alturas)
    alto = pisos * alto_piso
    z_techo = suelo_max + alto
    c.prisma(huella, z_base, z_techo, "muro", color_muro, tapa=False)
    techo_plano(c, huella, z_techo - 0.01)

    calle = [l for l in lados if l["a_calle"]]
    if puerta_en is None and calle:
        mayor = max(calle, key=lambda l: l["largo"])
        puerta_en = {mayor["i"]: mayor["largo"] / 2}
    puerta_en = puerta_en or {}

    for l in calle:
        mx, my = (l["a"][0] + l["b"][0]) / 2, (l["a"][1] + l["b"][1]) / 2
        suelo = datos.altura_suelo(mx, my)
        f = Fachada(c, l, suelo)
        dz = z_techo - suelo  # altura de la fachada en este lado (varía con la pendiente)
        zocalo(f, zocalo_alto, desde=z_base - suelo)
        n = (ventanas_por_lado or {}).get(l["i"], max(1, int(l["largo"] / 4.0)))
        paso = l["largo"] / n
        posiciones = [paso * (k + 0.5) for k in range(n)]
        sp = puerta_en.get(l["i"])
        for p in range(pisos):
            h_piso = dz - alto + p * alto_piso
            for s in posiciones:
                if p == 0 and sp is not None and abs(s - sp) < paso / 2:
                    puerta(f, sp, alto=min(3.2, alto_piso - 0.6), arco=arcos)
                    continue
                if p == 0:
                    ventana(f, s, max(zocalo_alto + 0.2, h_piso + 1.0), alto=min(2.0, alto_piso - 1.6), reja=True, arco=arcos)
                else:
                    ventana(f, s, h_piso + 0.15, alto=alto_piso - 1.2, arco=arcos, balcon="hierro" if balcones else None)
            if p > 0:
                imposta(f, h_piso - 0.2)
        if remate == "cornisa":
            cornisa(f, dz - 0.45)
            parapeto(f, dz, alto=0.6)
        elif remate == "alero":
            alero_tejas(f, dz - 0.1)
        elif remate == "almenas":
            cornisa(f, dz - 0.45, vuelo=0.2)
            almenas(f, dz)
    ob = c.objeto(coleccion, biselar=biselar)
    return ob, lados
