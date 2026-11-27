"""Esquina Nicolás Ortiz × Plaza 25 de Mayo, lado SE (R0168: "la fachada de la esquina"; foto con la farmacia).

El ala de M065 (`M065_ala_plaza`, de codex) termina en un paño ciego de 6,85 m de ancho y 9,4 m de alto que mira a la
esquina del atrio de la Catedral. En la foto ese frente es la fachada principal de la esquina: planta baja con la farmacia
y portones, mirador de madera volado en la esquina del primer piso, balcones de hierro con puertas-ventana, cornisa y
pretil. No se toca la malla de codex: se coloca una piel de fachada (objeto propio, 12 cm delante del paño ciego).
"""
import math

from kit import Constructor, altura_suelo
from kit import arquitectura as A
from kit.nucleo import Fachada

A_ = (-160.61, -296.70)        # extremo norte del paño ciego
B_ = (-157.93, -302.99)        # extremo sur
MURO = "#f1ece1"
MOLDURA = "#fbf7ee"
MADERA = "#5c2f22"


def _mirador(f, s0, s1, h0, h1, vuelo=0.85):
    """Mirador de madera volado: base moldurada, montantes con vidrios, cubierta con alero."""
    f.caja(s0 - .05, s1 + .05, h0 - .45, h0, 0.0, vuelo, "moldura", MOLDURA)                  # panza inferior
    f.caja(s0 - .05, s1 + .05, h0 - .12, h0, 0.0, vuelo + .08, "moldura", MOLDURA)
    # caras: frontal y los dos laterales
    ancho = s1 - s0
    n = max(2, round(ancho / 0.62))
    for i in range(n):
        a = s0 + ancho * i / n
        b = s0 + ancho * (i + 1) / n
        f.caja(a + .05, b - .05, h0 + .1, h1 - .1, vuelo - .05, vuelo, "vidrio")
    for i in range(n + 1):
        s = s0 + ancho * i / n
        f.caja(s - .04, s + .04, h0, h1, vuelo - .08, vuelo + .03, "marco_ventana", MADERA)
    for h in (h0 + .1, h0 + (h1 - h0) * .62, h1 - .1):
        f.caja(s0, s1, h - .03, h + .03, vuelo - .08, vuelo + .03, "marco_ventana", MADERA)
    for lado in (s0, s1):
        f.caja(lado - .02, lado + .02, h0 + .1, h1 - .1, 0.0, vuelo, "vidrio")
        f.caja(lado - .05, lado + .05, h0, h1, 0.0, vuelo + .03, "marco_ventana", MADERA)
    f.caja(s0 - .12, s1 + .12, h1, h1 + .14, -.05, vuelo + .22, "moldura", MOLDURA)            # cornisa del mirador
    f.caja(s0 - .08, s1 + .08, h1 + .14, h1 + .3, 0.0, vuelo + .16, "teja")                    # cubierta


def _pano_ciego():
    """Extremos ACTUALES del paño ciego del ala de M065. Con la vuelta de la plaza 2 m más ancha (2026-11-24) el ala se
    recortó y su cabecera ciega pasó a ser el lado (-159,8, -301,6)→(-155,4, -305,7), que mira al SO, hacia la esquina
    del atrio. Con los extremos viejos la piel quedaba detrás del ala ("la fachada hundida"). El ala es una huella propia
    de codex (plaza_este.ala_baja), no del lienzo: se toma de su GLB exportado si está, si no estos valores."""
    import os
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "web", "public", "models", "ciudad",
                        "codex", "M065.glb")
    try:
        import bpy
        antes = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=ruta)
        nuevos = set(bpy.data.objects) - antes
        ala = next(o for o in nuevos if o.name.startswith("M065_ala_plaza"))
        pts = [ala.matrix_world @ v.co for v in ala.data.vertices]
        zmin = min(p.z for p in pts)
        base = {(round(p.x, 2), round(p.y, 2)) for p in pts if p.z < zmin + 0.05}
        for o in nuevos:
            bpy.data.objects.remove(o, do_unlink=True)
        # la cabecera: los puntos de la base a menos de 7 m del punto más al sur del ala, alineados
        sur = min(base, key=lambda p: p[1])
        cab = sorted((p for p in base if math.hypot(p[0] - sur[0], p[1] - sur[1]) < 7.0), key=lambda p: p[0])
        if len(cab) >= 2 and math.hypot(cab[-1][0] - cab[0][0], cab[-1][1] - cab[0][1]) > 4.0:
            return cab[0], cab[-1]
    except Exception as e:  # noqa: BLE001
        print("[M056] no se pudo leer el ala de M065:", e)
    return (-159.83, -301.62), (-155.35, -305.67)


def _zocalo_con_vanos(f, alto, huecos, color):
    """Zócalo de sillares SOLO entre vanos: delante de un portón le tapaba la mitad de abajo (revisión por MCP,
    2026-11-24: "la puerta solo se ve la mitad")."""
    s = 0.0
    for a, b in sorted(huecos) + [(f.largo, f.largo)]:
        if a - s > 0.08:
            A.zocalo(f, alto, s0=s, s1=a, color=color, desde=-0.4)
        s = max(s, b)


def esquina_farmacia(col):
    from base_suelo import ALTO_VEREDA, SOBRE_TERRENO
    a_, b_ = _pano_ciego()
    print("[M056] paño ciego de M065:", a_, b_)
    mx, my = (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2
    z = altura_suelo(mx, my) + SOBRE_TERRENO + ALTO_VEREDA      # sobre la vereda (antes en el terreno: puertas enterradas)
    dx, dy = b_[0] - a_[0], b_[1] - a_[1]
    L = math.hypot(dx, dy)
    normal = (dy / L, -dx / L)
    c = Constructor("M056_esquina_farmacia")
    # piel de 12 cm delante del paño ciego, en un solo plano limpio
    d0 = 0.12
    lado = {"a": (a_[0] + normal[0] * d0, a_[1] + normal[1] * d0), "b": (b_[0] + normal[0] * d0, b_[1] + normal[1] * d0),
            "normal": normal}
    f = Fachada(c, lado, z)
    k = f.largo / 6.85          # la composición de la foto se diseñó sobre 6,85 m: se escala al paño actual
    H = 9.3
    f.caja(0, f.largo, -0.4, H, -0.12, 0.0, "muro", MURO)
    # planta baja: portón a la izquierda (acceso a pisos), vidriera de la farmacia al centro, portón a la derecha
    p1, w1 = 0.95 * k, 1.3 * k
    v0, v1 = 1.9 * k, 5.15 * k
    p2, w2 = 5.95 * k, 1.2 * k
    _zocalo_con_vanos(f, 0.9, [(p1 - w1 / 2 - 0.22, p1 + w1 / 2 + 0.22), (v0, v1), (p2 - w2 / 2 - 0.22, p2 + w2 / 2 + 0.22)],
                      "#b99a7a")
    A.puerta(f, p1, ancho=w1, alto=2.7, arco=False, color="#4a2a1c", color_moldura=MOLDURA)
    f.caja(v0, v1, 0.0, 0.55, 0.0, 0.06, "zocalo_piedra", "#b99a7a")                          # antepecho de la vitrina
    f.caja(v0, v1, 0.55, 3.0, 0.0, 0.05, "marco_ventana", MADERA)                              # marco de la vitrina
    f.caja(v0 + .1, v1 - .1, 0.65, 2.9, 0.05, 0.07, "vidrio")
    for t in (1 / 3, 2 / 3):
        sm = v0 + (v1 - v0) * t
        f.caja(sm - .03, sm + .03, 0.65, 2.9, 0.05, 0.09, "marco_ventana", MADERA)
    f.caja(v0 - .1, v1 + .1, 3.05, 3.85, 0.0, 0.14, "madera", "#6b2a25")                      # tablero del letrero
    f.caja(v0 - .1, v1 + .1, 3.0, 3.06, 0.0, 0.18, "moldura", MOLDURA)
    A.puerta(f, p2, ancho=w2, alto=2.6, color="#4a2a1c", color_moldura=MOLDURA)
    A.imposta(f, 4.35, alto=0.28, vuelo=0.16, color=MOLDURA)
    # primer piso: mirador en la esquina norte (con el foco de la foto) y dos puertas-ventana con balcón de hierro
    _mirador(f, 0.35 * k, 2.55 * k, 4.75, 7.45)
    for s_ in (3.75 * k, 5.6 * k):
        A.ventana(f, s_, 4.9, ancho=1.05 * k, alto=2.4, balcon="hierro", color_moldura=MOLDURA, color_carpinteria=MADERA)
    # segundo nivel: ventanas altas con guardapolvo (la foto muestra un cuerpo de dos niveles sobre los balcones)
    for s_ in (3.75 * k, 5.6 * k):
        A.ventana(f, s_, 7.9, ancho=0.9 * k, alto=1.1, color_moldura=MOLDURA, color_carpinteria=MADERA)
    A.imposta(f, 7.62, alto=0.2, vuelo=0.1, color=MOLDURA)
    A.cornisa(f, 8.7, vuelo=0.32, alto=0.4, color=MOLDURA)
    f.caja(0, f.largo, 9.1, 9.3, -0.1, 0.22, "moldura", MOLDURA)
    # pilastras de esquina
    for s_ in (0.12, f.largo - 0.12):
        f.caja(s_ - .12, s_ + .12, 0.9, 8.7, -0.1, 0.1, "moldura", MOLDURA)
    c.objeto(col)


def cebra_ortiz(col, retiro=12.0, largo=3.0, medio=3.2):
    """Paso de cebra en el brazo de Nicolás Ortiz frente a la esquina del atrio (R0168: la foto lo muestra en primer
    plano). La calzada de ese brazo es de la BASE (fuera del polígono de la sección): se dibuja aquí, apoyado en el
    terreno, a `retiro` m de la esquina del muro."""
    from piezas_claude import esquina_atrio_ortiz, tramo_calle
    ort = tramo_calle("Calle Nicolás Ortiz", (-200.0, -320.0))
    t, cxy, lado = esquina_atrio_ortiz((-208.14, -335.31))
    (x0, y0), (x1, y1) = ort["eje"][-2], ort["eje"][-1]
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    # punto del eje bajo la esquina del muro (el muro está lado*ancho/2 a la izquierda del eje)
    ex = cxy[0] + uy * lado * ort["ancho"] / 2
    ey = cxy[1] - ux * lado * ort["ancho"] / 2
    px, py = ex - ux * retiro, ey - uy * retiro
    vx, vy = -uy, ux
    c = Constructor("M056_cebra_ortiz")
    k = -medio
    while k < medio:
        pts = [(px + vx * k - ux * largo / 2, py + vy * k - uy * largo / 2),
               (px + vx * (k + .5) - ux * largo / 2, py + vy * (k + .5) - uy * largo / 2),
               (px + vx * (k + .5) + ux * largo / 2, py + vy * (k + .5) + uy * largo / 2),
               (px + vx * k + ux * largo / 2, py + vy * k + uy * largo / 2)]
        c.poligono([(x, y, altura_suelo(x, y) + 0.06) for x, y in pts], "pintura_acento", "#ecebe6")
        k += 1.0
    c.objeto(col)
