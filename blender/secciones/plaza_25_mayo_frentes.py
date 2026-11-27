"""Frentes de la Plaza 25 de Mayo rehechos en la sección piloto (refactor 2026-11-14).

FRENTE NO — Casa de la Libertad y vecinos (foto 130638, mirando al SO desde la esquina con Arenales; 130624–130635
desde la plaza). En el lienzo esta cuadra quedaba 9 m retirada de la calle y la fachada de codex (Ee30c62) se había
quedado sin ventanas. Va sobre la línea real de la calle, con vereda normal:
  s 0–17    casa blanca de 2 plantas con cornisa, ventanas rectas con reja abajo y balcón de hierro arriba
  s 17–30   edificio de bandas rojizas: pilastras y fajas color ladrillo, medallones en el friso
  s 30–fin  CASA DE LA LIBERTAD: muro blanco, zócalo alto de sillería rojiza, ventanas de la planta baja con marco de
            piedra rosada en arco rebajado y reja, BALCÓN CORRIDO DE MADERA en el piso alto con balaustres torneados y
            ménsulas, alero de tejas con canes de madera.
"""

import math

from kit import Constructor, altura_suelo
from kit import arquitectura as A
from kit.nucleo import Fachada

BLANCO = "#f3f1ec"
SILLAR = "#a8735f"
PIEDRA_ROSA = "#c39a84"
LADRILLO = "#b77861"
MADERA = "#6e4a2e"
MADERA_OSC = "#4a2f1e"


def _linea_fachada(nombre_calle, a, b, eje):
    """Proyecta los extremos a, b (de la huella vieja) sobre la línea de fachada de la calle (a ancho/2 del eje)."""
    (x0, y0), (x1, y1) = eje
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if (mx - x0) * nx + (my - y0) * ny < 0:
        nx, ny = -nx, -ny
    return ux, uy, nx, ny


def frente_libertad(col, calles, a=(-263.1, -192.3), b=(-234.1, -156.9)):
    """calles: lista (nombre, eje, medio_calzada) del trazado; a→b: lado de la plaza de la huella vieja (Ee30c62)."""
    import json
    import os
    from kit.datos import RAIZ
    cr = json.load(open(os.path.join(RAIZ, "reparto", "calles_reales.json")))["calles"]
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2

    def dist(c):
        best = 1e9
        for p, q in zip(c["eje"], c["eje"][1:]):
            dx, dy = q[0] - p[0], q[1] - p[1]
            t = max(0, min(1, ((mx - p[0]) * dx + (my - p[1]) * dy) / (dx * dx + dy * dy)))
            best = min(best, math.hypot(mx - p[0] - t * dx, my - p[1] - t * dy))
        return best
    calle = min((c for c in cr if c["nombre"] == "Plaza 25 de Mayo"), key=dist)
    eje = calle["eje"]
    p, q = min(zip(eje, eje[1:]), key=lambda s: math.hypot((s[0][0] + s[1][0]) / 2 - mx, (s[0][1] + s[1][1]) / 2 - my))
    ux, uy, nx, ny = _linea_fachada(calle["nombre"], a, b, (p, q))
    w = calle["ancho"] / 2

    def sobre_linea(pt):
        t = (pt[0] - p[0]) * ux + (pt[1] - p[1]) * uy
        return (p[0] + ux * t + nx * w, p[1] + uy * t + ny * w)
    fa, fb = sobre_linea(a), sobre_linea(b)
    # huella: de la línea de la calle hasta la fachada vieja (lo de atrás ya existe)
    huella = [fa, fb, b, a]
    area = sum(p_[0] * q_[1] - q_[0] * p_[1] for p_, q_ in zip(huella, huella[1:] + huella[:1]))
    if area < 0:
        huella.reverse()
    c = Constructor("SP25_casa_libertad")
    c.huella = huella
    zs = [altura_suelo(*pt) for pt in huella]
    zb, zt = min(zs), max(zs)
    ALTO = 9.4
    c.prisma(huella, zb - 0.6, zt + ALTO, "muro", BLANCO, tapa=True)
    # fachada hacia la calle: de fa a fb, normal hacia la calle (−n)
    lado = {"a": fa, "b": fb, "normal": (-nx, -ny)}
    if (fb[0] - fa[0]) * (-ny) - (fb[1] - fa[1]) * (-nx) > 0:     # la normal tiene que quedar a la derecha de a→b
        lado = {"a": fb, "b": fa, "normal": (-nx, -ny)}
    f = Fachada(c, lado, altura_suelo((fa[0] + fb[0]) / 2, (fa[1] + fb[1]) / 2))
    off = zt - f.suelo
    L = f.largo
    # s se mide desde el extremo SO (el de a): si la fachada quedó al revés, se invierte
    inv = math.hypot(lado["a"][0] - fa[0], lado["a"][1] - fa[1]) > 1.0
    S = (lambda s: L - s) if inv else (lambda s: s)

    def tramo(s0, s1):
        return (min(S(s0), S(s1)), max(S(s0), S(s1)))

    # ---- s 0–17: casa blanca
    t0, t1 = tramo(0.0, 17.0)
    A.zocalo(f, 1.1 + off, s0=t0, s1=t1, color="#b9a48c", desde=zb - 0.6 - f.suelo)
    for s in (2.2, 5.6, 9.0, 12.4, 15.2):
        A.ventana(f, S(s), 1.5 + off, ancho=1.2, alto=2.0, reja=True, color_moldura="#e3dccd",
                  color_carpinteria="#5a3422")
        A.ventana(f, S(s), 5.4 + off, ancho=1.2, alto=2.3, balcon="hierro", color_moldura="#e3dccd",
                  color_carpinteria="#5a3422")
    A.imposta(f, 4.6 + off, s0=t0, s1=t1, color="#e3dccd")
    A.cornisa(f, 8.7 + off, s0=t0, s1=t1, color="#e3dccd")
    A.parapeto(f, 9.1 + off, alto=0.5, s0=t0, s1=t1, color=BLANCO)
    # ---- s 17–30: bandas rojizas
    t0, t1 = tramo(17.0, 30.0)
    f.caja(t0, t1, 1.3 + off, 8.3 + off, 0.0, 0.02, "muro", "#ddc9b0")
    A.zocalo(f, 1.3 + off, s0=t0, s1=t1, color=SILLAR, desde=zb - 0.6 - f.suelo)
    for s in (17.4, 23.5, 29.6):
        A.pilastra(f, S(s), 1.3 + off, 8.4 + off, ancho=0.5, vuelo=0.14, rol="pintura_acento", color=LADRILLO)
    for hh in (1.4, 4.3, 8.3):
        A.cornisa(f, hh + off, s0=t0, s1=t1, alto=0.18, vuelo=0.17, rol="pintura_acento", color=LADRILLO)
    for s in (19.0, 22.0, 25.0, 28.0):
        A.ventana(f, S(s), 1.8 + off, ancho=1.15, alto=2.1, reja=True, color_moldura=LADRILLO,
                  color_carpinteria="#5a3422")
        A.ventana(f, S(s), 5.1 + off, ancho=1.15, alto=2.3, color_moldura=LADRILLO, color_carpinteria="#714b30")
    for s in (20.5, 23.5, 26.5):
        f.arco(S(s), 0.14, 0.05, 7.7 + off, 0.06, 0.16, "pintura_acento", LADRILLO, medio=False, segmentos=8)
    A.parapeto(f, 8.7 + off, alto=0.5, s0=t0, s1=t1, color="#ddc9b0")
    # ---- s 30–fin: Casa de la Libertad
    t0, t1 = tramo(30.0, L)
    A.zocalo(f, 1.5 + off, s0=t0, s1=t1, color=SILLAR, desde=zb - 0.6 - f.suelo)
    k = 31.6
    vanos = []
    while k < L - 1.0:
        vanos.append(k)
        k += 3.4
    for s in vanos:
        sm = S(s)
        # ventana baja con marco ancho de piedra rosada en arco rebajado y reja
        f.caja(sm - 0.95, sm + 0.95, 1.5 + off, 4.0 + off, 0.0, 0.1, "piedra", PIEDRA_ROSA)
        f.arco(sm, 0.95, 0.35, 4.0 + off, 0.0, 0.1, "piedra", PIEDRA_ROSA, segmentos=10)
        A.ventana(f, sm, 1.75 + off, ancho=1.05, alto=2.25, arco=True, reja=True, moldura="piedra",
                  color_moldura=PIEDRA_ROSA, carpinteria="madera", color_carpinteria=MADERA_OSC)
        # puerta-ventana del piso alto que sale al balcón
        f.caja(sm - 0.6, sm + 0.6, 5.0 + off, 7.5 + off, 0.0, 0.03, "madera", MADERA_OSC)
        f.caja(sm - 0.75, sm + 0.75, 7.5 + off, 7.7 + off, 0.0, 0.1, "moldura", "#e3dccd")
    # balcón corrido de madera: piso sobre ménsulas, balaustres torneados, pasamanos y pies derechos con alero
    b0, b1 = t0 + 0.6, t1 - 0.4
    f.caja(b0, b1, 4.7 + off, 4.92 + off, 0.0, 1.05, "madera", MADERA)
    s = b0 + 0.3
    while s < b1:
        f.caja(s - 0.07, s + 0.07, 4.52 + off, 4.7 + off, 0.0, 0.95, "madera", MADERA_OSC)     # ménsula escalonada
        f.caja(s - 0.07, s + 0.07, 4.32 + off, 4.52 + off, 0.0, 0.6, "madera", MADERA_OSC)
        f.caja(s - 0.07, s + 0.07, 4.15 + off, 4.32 + off, 0.0, 0.3, "madera", MADERA_OSC)
        s += 1.15
    s = b0 + 0.1
    while s < b1:
        f.cilindro_vertical(s, 4.92 + off, 5.82 + off, 0.95, 0.045, "madera", MADERA, lados=6)
        s += 0.32
    f.caja(b0, b1, 5.82 + off, 5.95 + off, 0.88, 1.03, "madera", MADERA)                    # pasamanos
    f.caja(b0, b1, 5.0 + off, 5.08 + off, 0.88, 1.03, "madera", MADERA)
    s = b0 + 0.05
    while s < b1:
        f.caja(s - 0.07, s + 0.07, 4.92 + off, 8.1 + off, 0.92, 1.06, "madera", MADERA)       # pies derechos
        s += 3.4
    A.alero_tejas(f, 8.2 + off, vuelo=1.35, fondo=2.0, s0=t0, s1=t1, madera="madera")
    # los dos extremos (9 m) quedan a la vista en las esquinas: la casa dobla la esquina con el mismo orden
    for extremo, interior in ((lado["b"], b if math.dist(lado["b"], fb) < 1 else a),
                              (lado["a"], a if math.dist(lado["a"], fa) < 1 else b)):
        ex = {"a": extremo, "b": interior}
        dx, dy = ex["b"][0] - ex["a"][0], ex["b"][1] - ex["a"][1]
        Le = math.hypot(dx, dy)
        nrm = (dy / Le, -dx / Le)
        cx_, cy_ = sum(p_[0] for p_ in huella) / 4, sum(p_[1] for p_ in huella) / 4
        if (ex["a"][0] - cx_) * nrm[0] + (ex["a"][1] - cy_) * nrm[1] < 0:      # normal hacia afuera
            ex = {"a": interior, "b": extremo}
            nrm = (-nrm[0], -nrm[1])
        ex["normal"] = nrm
        fe = Fachada(c, ex, altura_suelo((extremo[0] + interior[0]) / 2, (extremo[1] + interior[1]) / 2))
        oe = zt - fe.suelo
        es_libertad = math.dist(extremo, fb) < 1.0 if not inv else math.dist(extremo, fa) < 1.0
        A.zocalo(fe, (1.5 if es_libertad else 1.1) + oe, color=SILLAR if es_libertad else "#b9a48c",
                 desde=zb - 0.6 - fe.suelo)
        for sv in (Le * 0.3, Le * 0.72):
            A.ventana(fe, sv, 1.75 + oe, ancho=1.05, alto=2.2, reja=True, moldura="piedra",
                      color_moldura=PIEDRA_ROSA if es_libertad else "#e3dccd", color_carpinteria=MADERA_OSC)
            A.ventana(fe, sv, 5.3 + oe, ancho=1.05, alto=2.2, color_moldura="#e3dccd", color_carpinteria=MADERA_OSC)
        if es_libertad:
            A.alero_tejas(fe, 8.2 + oe, vuelo=1.0, fondo=2.0, madera="madera")
        else:
            A.cornisa(fe, 8.7 + oe, color="#e3dccd")
    c.objeto(col)
    return huella


# ================================================================================================ ESQUINA N
def _eje_calle(nombre, cerca):
    import json
    import os
    from kit.datos import RAIZ
    cr = json.load(open(os.path.join(RAIZ, "reparto", "calles_reales.json")))["calles"]
    best = None
    for c in cr:
        if c["nombre"] != nombre:
            continue
        for p, q in zip(c["eje"], c["eje"][1:]):
            d = math.hypot((p[0] + q[0]) / 2 - cerca[0], (p[1] + q[1]) / 2 - cerca[1])
            if best is None or d < best[0]:
                best = (d, p, q, c["ancho"])
    return best[1], best[2], best[3]


def _linea(p, q, w, hacia):
    """Línea de fachada paralela al eje p→q a w m, del lado del punto `hacia`: (punto, dirección unitaria)."""
    ux, uy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    nx, ny = -uy, ux
    if (hacia[0] - p[0]) * nx + (hacia[1] - p[1]) * ny < 0:
        nx, ny = -nx, -ny
    return (p[0] + nx * w, p[1] + ny * w), (ux, uy), (nx, ny)


def esquina_alcaldia(col, lote=(-188.0, -100.0), largo_a=20.0, largo_b=18.0, radio=4.5):
    """Esquina Arenales × Arce, lado de la plaza (fotos 130532, 130535): edificio blanco de 3 plantas con la ESQUINA
    REDONDEADA; planta baja almohadillada con vanos en arco, pisos altos con ventanas de marco gris y balcones de
    hierro (también curvos en la esquina), cornisa y balaustrada."""
    from shapely.geometry import Point as P_, Polygon as Pg
    pa, qa, wa = _eje_calle("Calle José Álvarez de Arenales", (-200.0, -105.0))
    pb, qb, wb = _eje_calle("Calle Aniceto Arce", (-180.0, -108.0))
    oa, ua, na = _linea(pa, qa, wa / 2, lote)
    ob, ub, nb = _linea(pb, qb, wb / 2, lote)
    # esquina = cruce de las dos líneas de fachada
    den = ua[0] * ub[1] - ua[1] * ub[0]
    t = ((ob[0] - oa[0]) * ub[1] - (ob[1] - oa[1]) * ub[0]) / den
    C = (oa[0] + ua[0] * t, oa[1] + ua[1] * t)
    # direcciones a lo largo de cada calle alejándose del cruce, hacia el lote
    da = ua if (lote[0] - C[0]) * ua[0] + (lote[1] - C[1]) * ua[1] > 0 else (-ua[0], -ua[1])
    db = ub if (lote[0] - C[0]) * ub[0] + (lote[1] - C[1]) * ub[1] > 0 else (-ub[0], -ub[1])
    A_ = (C[0] + da[0] * largo_a, C[1] + da[1] * largo_a)
    B_ = (C[0] + db[0] * largo_b, C[1] + db[1] * largo_b)
    D_ = (A_[0] + db[0] * largo_b, A_[1] + db[1] * largo_b)
    pol = Pg([C, A_, D_, B_])
    # sólo la esquina de la calle se redondea
    redondo = pol.buffer(-radio, join_style="round").buffer(radio, join_style="round")
    pol = redondo.union(pol.difference(P_(C).buffer(radio * 2.2)))
    pol = pol.simplify(0.05)
    huella = list(pol.exterior.coords)[:-1]
    if not pol.exterior.is_ccw:
        huella.reverse()
    c = Constructor("SP25_esquina_alcaldia")
    c.huella = huella
    zs = [altura_suelo(*p) for p in huella]
    zb, zt = min(zs), max(zs)
    PISOS = (4.6, 4.1, 4.1)
    ALTO = sum(PISOS)
    GRIS = "#9aa3a8"
    c.prisma(huella, zb - 0.6, zt + ALTO, "muro", "#f2f0eb", tapa=True)
    for p, q in zip(huella, huella[1:] + huella[:1]):
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if L < 0.3:
            continue
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        # solo las caras a la calle (sobre una de las dos líneas o en la curva de la esquina)
        da_ = abs((mx - oa[0]) * na[0] + (my - oa[1]) * na[1])
        db_ = abs((mx - ob[0]) * nb[0] + (my - ob[1]) * nb[1])
        en_curva = math.hypot(mx - C[0], my - C[1]) < radio * 2.3
        if da_ > 0.3 and db_ > 0.3 and not en_curva:
            continue
        nrm = ((q[1] - p[1]) / L, -(q[0] - p[0]) / L)          # derecha de p→q = afuera (huella antihoraria)
        f = Fachada(c, {"a": p, "b": q, "normal": nrm}, altura_suelo(mx, my))
        off = zt - f.suelo
        # planta baja almohadillada (bandas grises)
        A.zocalo(f, 0.9 + off, color="#8f969a", desde=zb - 0.6 - f.suelo)
        h = 1.2
        while h < PISOS[0] - 0.2:
            f.caja(0.0, L, h + off, h + 0.06 + off, 0.0, 0.05, "moldura", "#d9dcdc")
            h += 0.55
        A.imposta(f, PISOS[0] + off, alto=0.25, vuelo=0.14, color="#e6e4df")
        A.imposta(f, PISOS[0] + PISOS[1] + off, alto=0.2, vuelo=0.1, color="#e6e4df")
        A.cornisa(f, ALTO - 0.3 + off, vuelo=0.4, alto=0.45, color="#e6e4df")
        A.parapeto(f, ALTO + 0.15 + off, alto=0.8, color="#f2f0eb")
        if L < 2.0:                                            # tramos de la curva: balcones corridos curvos
            for hp in (PISOS[0], PISOS[0] + PISOS[1]):
                f.caja(-0.02, L + 0.02, hp + off, hp + 0.12 + off, 0.0, 0.85, "moldura", "#e6e4df")
                f.caja(-0.02, L + 0.02, hp + 1.0 + off, hp + 1.05 + off, 0.8, 0.85, "hierro", "#2b2b2b")
                k = 0.0
                while k <= L:
                    f.caja(k - 0.015, k + 0.015, hp + 0.12 + off, hp + 1.0 + off, 0.8, 0.83, "hierro", "#2b2b2b")
                    k += 0.14
            continue
        n = max(1, round(L / 3.4))
        for j in range(n):
            s = L * (j + 0.5) / n
            if j % 3 == 1:
                A.puerta(f, s, ancho=1.5, alto=3.3 + off, arco=True, color="#5a3a26", moldura="moldura",
                         color_moldura="#d9dcdc")
            else:
                A.ventana(f, s, 1.1 + off, ancho=1.15, alto=2.4, arco=True, reja=True, color_moldura="#d9dcdc",
                          color_carpinteria="#5a3422")
            for k_, hp in enumerate((PISOS[0], PISOS[0] + PISOS[1])):
                A.ventana(f, s, hp + 0.45 + off, ancho=1.15, alto=2.4, balcon="hierro" if k_ == 0 or j % 2 == 0 else None,
                          moldura="moldura", color_moldura=GRIS, color_carpinteria="#5a3422")
                f.caja(s - 0.85, s + 0.85, hp + 2.95 + off, hp + 3.1 + off, 0.0, 0.16, "moldura", GRIS)
        for j in range(n + 1):
            A.pilastra(f, L * j / n if 0 < j < n else (0.25 if j == 0 else L - 0.25), PISOS[0] + off,
                       ALTO - 0.3 + off, ancho=0.4, vuelo=0.08, color="#e6e4df", capitel=False)
    c.objeto(col)
    return huella


def esquina_colonial(col, nombre, calle_a, cerca_a, calle_b, cerca_b, lote, largo_a=16.0, largo_b=16.0,
                     ochava=3.0, pisos=(4.4, 4.0), muro="#f4f1ea", zocalo="#b9a48c", remate="cornisa",
                     balcon_esquina=True):
    """Edificio de esquina de la plaza (sin foto propia): planta baja con portones y vanos con reja, piso(s) alto(s)
    con balcones de hierro, OCHAVA con balcón corrido en la esquina, cornisa y pretil (o alero de tejas). Su huella se
    recorta contra los edificios que ya existen (no se mete en ningún vecino)."""
    from shapely.geometry import Point as P_, Polygon as Pg
    from shapely.ops import unary_union
    from kit.datos import edificios_recortados
    pa, qa, wa = _eje_calle(calle_a, cerca_a)
    pb, qb, wb = _eje_calle(calle_b, cerca_b)
    oa, ua, na = _linea(pa, qa, wa / 2, lote)
    ob, ub, nb = _linea(pb, qb, wb / 2, lote)
    den = ua[0] * ub[1] - ua[1] * ub[0]
    t = ((ob[0] - oa[0]) * ub[1] - (ob[1] - oa[1]) * ub[0]) / den
    C = (oa[0] + ua[0] * t, oa[1] + ua[1] * t)
    da = ua if (lote[0] - C[0]) * ua[0] + (lote[1] - C[1]) * ua[1] > 0 else (-ua[0], -ua[1])
    db = ub if (lote[0] - C[0]) * ub[0] + (lote[1] - C[1]) * ub[1] > 0 else (-ub[0], -ub[1])
    A_ = (C[0] + da[0] * largo_a, C[1] + da[1] * largo_a)
    B_ = (C[0] + db[0] * largo_b, C[1] + db[1] * largo_b)
    D_ = (A_[0] + db[0] * largo_b, A_[1] + db[1] * largo_b)
    pol = Pg([C, A_, D_, B_])
    pol = pol.difference(P_(C).buffer(ochava, resolution=1))      # ochava recta
    vecinos = [Pg(h).buffer(0.05) for h in edificios_recortados() if Pg(h).intersects(pol)]
    if vecinos:
        pol = pol.difference(unary_union(vecinos))
    if pol.geom_type != "Polygon":
        pol = max(pol.geoms, key=lambda g_: g_.area)
    pol = pol.simplify(0.05)
    huella = list(pol.exterior.coords)[:-1]
    if not pol.exterior.is_ccw:
        huella.reverse()
    c = Constructor(nombre)
    c.huella = huella
    zs = [altura_suelo(*p) for p in huella]
    zb, zt = min(zs), max(zs)
    ALTO = sum(pisos)
    c.prisma(huella, zb - 0.6, zt + ALTO, "muro", muro, tapa=True)
    for p, q in zip(huella, huella[1:] + huella[:1]):
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if L < 1.2:
            continue
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        da_ = abs((mx - oa[0]) * na[0] + (my - oa[1]) * na[1])
        db_ = abs((mx - ob[0]) * nb[0] + (my - ob[1]) * nb[1])
        en_ochava = math.hypot(mx - C[0], my - C[1]) < ochava * 1.3
        if da_ > 0.3 and db_ > 0.3 and not en_ochava:
            continue
        nrm = ((q[1] - p[1]) / L, -(q[0] - p[0]) / L)
        f = Fachada(c, {"a": p, "b": q, "normal": nrm}, altura_suelo(mx, my))
        off = zt - f.suelo
        A.zocalo(f, 1.0 + off, color=zocalo, desde=zb - 0.6 - f.suelo)
        A.imposta(f, pisos[0] + off, alto=0.2, vuelo=0.1, color="#e6e1d6")
        if remate == "alero":
            A.alero_tejas(f, ALTO + off, vuelo=0.9, fondo=2.0)
        else:
            A.cornisa(f, ALTO - 0.3 + off, vuelo=0.35, alto=0.4, color="#e6e1d6")
            A.parapeto(f, ALTO + 0.1 + off, alto=0.6, color=muro)
        if en_ochava:
            A.puerta(f, L / 2, ancho=min(1.6, L - 0.6), alto=3.0 + off, color="#5a3a26", moldura="moldura",
                     color_moldura="#e6e1d6")
            if balcon_esquina:
                for k in range(1, len(pisos)):
                    hp = sum(pisos[:k])
                    A.ventana(f, L / 2, hp + 0.4 + off, ancho=min(1.2, L - 0.8), alto=2.3, balcon="hierro",
                              color_moldura="#e6e1d6", color_carpinteria="#5a3422")
            continue
        n = max(1, round(L / 3.5))
        for j in range(n):
            s = L * (j + 0.5) / n
            if j % 3 == 1:
                A.puerta(f, s, ancho=1.5, alto=3.0 + off, color="#5a3a26", moldura="moldura", color_moldura="#e6e1d6")
            else:
                A.ventana(f, s, 1.2 + off, ancho=1.1, alto=2.0, reja=True, color_moldura="#e6e1d6",
                          color_carpinteria="#5a3422")
            for k in range(1, len(pisos)):
                hp = sum(pisos[:k])
                A.ventana(f, s, hp + 0.4 + off, ancho=1.15, alto=2.3, balcon="hierro" if (j + k) % 2 == 0 else None,
                          color_moldura="#e6e1d6", color_carpinteria="#5a3422")
    c.objeto(col)
    return huella


# ================================================================================================ PRIMERA CUADRA
# Las calles que salen de la plaza tenían su primera cuadra sin edificios (el relleno genérico los tapaba). Sin fotos
# propias: hileras de casas del centro diseñadas para cada cuadra. Tipos (pisos, alto de piso, muro, remate):
TIPOS = {
    "Ba": (2, 4.2, "#f6f4ef", "alero"),      # blanca, alero de tejas
    "Bc": (2, 4.3, "#f6f4ef", "cornisa"),    # blanca, cornisa y pretil
    "Ca": (2, 4.0, "#f1e6cf", "alero"),      # crema, alero
    "Oc": (2, 4.2, "#efe3c4", "cornisa"),    # ocre claro, cornisa
    "B3": (3, 3.8, "#f4f1ea", "cornisa"),    # blanca de 3 plantas
    "Bp": (2, 4.4, "#f6f4ef", "pinaculos"),  # blanca republicana con remates
    "Gc": (2, 4.2, "#eef0f1", "cornisa"),    # gris muy claro
}


def _casa(tipo, ancho):
    esquina = None
    if tipo.endswith(">"):          # "Bc>": casa de esquina al final de la hilera (fachada también en el costado)
        tipo, esquina = tipo[:-1], "fin"
    pisos, alto, muro, remate = TIPOS[tipo]
    n = max(1, round(ancho / 3.4))
    vanos = [ancho * (k + 0.5) / n for k in range(n)]
    puertas = [vanos[n // 2]]
    balcones = [v for k, v in enumerate(vanos) if k % 2 == 0 and v not in puertas] or vanos[:1]
    op = dict(vanos=vanos, puertas=puertas, balcones=balcones)
    if esquina:
        op["esquina"] = esquina
    return (ancho, pisos, alto, muro, remate, op)


# (calle, punto de referencia del tramo, lado: +1 izquierda del eje / −1 derecha, t inicial, casas [(tipo, ancho)])
HILERAS = [
    # vereda SE de España: casona de la esquina y casa gris (espana_se.py, R0206–R0211) hasta t = 67 y desde ahí la
    # casa de piedra, el Mercantil Santa Cruz y la Fiscalía (zonas/claude/AMP_ESPANA.py, R0211–R0215)
    ("Calle España", (-40.0, -140.0), +1, 77.5, [("Ba", 7.5), ("Oc", 7.8)]),
    ("Calle Daniel Calvo", (-60.0, -225.0), -1, 431.6,
     # termina donde empieza la cara a Daniel Calvo de la casona de la esquina (espana_se.py); de dos plantas: la de
     # tres metía su cornisa en la vecina (SIAMESES)
     [("Ba", 8.0), ("Bc", 9.0), ("Ca", 7.0), ("Bc", 10.5), ("Ba", 7.0), ("Oc", 8.0), ("Bp", 9.0)]),
    ("Calle Daniel Calvo", (-60.0, -225.0), +1, 431.6,
     [("Bc", 8.5), ("Ba", 7.0), (None, 15.5), ("Bp", 9.0), ("Ba", 6.5)]),   # None: ahí ya está E0b406f (M059)
    ("Calle Estudiantes", (-300.0, -190.0), +1, 53.8,
     [("Ba", 8.0), ("Oc", 7.5), ("Bc", 9.0), ("Ca", 7.0), ("B3", 10.0), ("Ba", 7.5), ("Bp", 9.0), ("Gc", 5.5),
      ("Bc>", 8.6)]),   # la última da a la esquina O de la plaza: fachada también hacia la plaza
    ("Calle Argentina", (-290.0, -240.0), +1, 24.5, [("Ba", 8.0), ("Bc", 9.0), ("Ca", 7.5), ("Oc", 8.5)]),
]


def primeras_cuadras(col):
    import sys as _s
    import os as _o
    _s.path.insert(1, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "zonas", "claude"))
    from piezas_claude import casas_de_frente, tramo_calle
    n = 0
    for k, (calle, ref, lado, t0, casas) in enumerate(HILERAS):
        tramo = tramo_calle(calle, ref)
        # cada tramo continuo de casas por separado; (None, ancho) deja el hueco a un edificio que ya existe
        t, grupo, g_ = t0, [], 0
        for tipo, ancho in casas + [(None, 0.0)]:
            if tipo is None:
                if grupo:
                    n += len(casas_de_frente(col, f"SP25_cuadra_{k}_{g_}", tramo, lado, grupo,
                                             t0=t - sum(c_[0] for c_ in grupo), fondo_max=10.0))
                    g_ += 1
                grupo = []
                t += ancho
                continue
            grupo.append(_casa(tipo, ancho))
            t += ancho
    return n
