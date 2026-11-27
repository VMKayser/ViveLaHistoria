"""M013 — lado NE de Ravelo entre la calle lateral del mercado y la Calle Aniceto Arce; Mercado Central (Junín).

Eje t sobre Ravelo: t = 0 en el extremo NO del Museo (E3785f4 lado 1, a), creciendo hacia el SE;
'prof' = metros hacia adentro (NE).

t 0–10     CASA CREMA (parte NO de E3785f4), fotos 130136 130144 130151: crema con pilastras y marcos ocre,
           2 plantas, balcones de hierro, tiendas abajo; vuelta a la calle lateral (lado 0).
t 10–43.8  MUSEO HISTÓRICO MILITAR (E3785f4), fotos 130113…130130: aire de castillo; muro gris azulado con
           llagueado horizontal, basamento de mampostería 1.6 m, 2 plantas de ventanas con marco gris oscuro,
           portal en arco de piedra entre dos torreones cilíndricos con óculo encima, torreón grande en la esquina SE,
           almenas con matacanes. ~10 m (torreones ~12.5 m).
t 44–59.5  ATRIO DE SAN FRANCISCO (no está en el lienzo), fotos 130006 130010 130101: arquería de 4 arcos sobre
           muro de piedra rojiza con rejas y jarrones verdes de cerámica sobre cada pilar.
           TEMPLO detrás (6 m): fachada a dos aguas con ventana del coro y portada con pilastras rojo anaranjado;
           torre izquierda sencilla (vanos en arco), torre derecha con campanario, campana y pináculos.
t 59.5–71  ARCO DE SAN FRANCISCO sobre la Calle Arce (gran arco de ~11.5 m de luz).
Mercado Central (E994825) frente a Junín y convento (E757802): sin foto útil → volúmenes sencillos.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from kit.arquitectura import _barrotes  # noqa: E402
from piezas_claude import (techo_auto, lado_lienzo, adelantada, arqueria_lisa, casa_sencilla, fachada, lado_virtual, partir_huella, remate_jarron,  # noqa: E402
                           suelo_huella, tejado_dos_aguas)

AGENTE = "claude"
MANZANA = "M013"
m, col = iniciar(AGENTE, MANZANA)
E = {e["id"]: e for e in m["edificios"]}

l1 = lado_lienzo(E["E3785f4"], 1)
R0 = l1["a"]
U = ((l1["b"][0] - l1["a"][0]) / l1["largo"], (l1["b"][1] - l1["a"][1]) / l1["largo"])  # hacia el SE
N = l1["normal"]                                                                          # hacia Ravelo (SO)
IN = (-N[0], -N[1])


def P(t, prof=0.0):
    return (R0[0] + U[0] * t + IN[0] * prof, R0[1] + U[1] * t + IN[1] * prof)


def rect(t0, t1, p0, p1):
    return [P(t0, p0), P(t1, p0), P(t1, p1), P(t0, p1)]


def frente(t0, t1, prof=0.0):
    return lado_virtual(P(t0, prof), P(t1, prof), N)


BLANCO = "#f6f4ef"
GRIS_MUSEO = "#cdd3d8"
GRIS_OSC = "#8b9399"
MAMPOSTERIA = "#a6806a"
CREMA = "#efe3c4"
OCRE = "#d9b25e"
NARANJA = "#c8643f"
VERDE = "#3e7a66"

# =========================================================================== casa crema + museo (E3785f4)
crema, museo = partir_huella(E["E3785f4"]["huella"], R0, U, 10.0)

c = Constructor("E3785f4_casa_crema")
zb, zr = suelo_huella(crema)
c.prisma(crema, zb - 0.6, zr + 8.6, "muro", CREMA, tapa=False)
techo_auto(c, crema, zr + 8.58)
# fachadas sobre los lados REALES de la huella recortada (corrección R0044: con la recta del lienzo la fachada
# quedaba 2 m delante del volumen, sobre la vereda de Ravelo, que ahí se curva)
for lado in [l for l in lados(crema) if l["a_calle"] and l["largo"] >= 3.0]:
    f = fachada(c, lado)
    off = zr - f.suelo
    vanos = [f.largo / 6, f.largo / 2, f.largo * 5 / 6]
    casa_sencilla(f, 0.0, f.largo, 2, 4.2, off, muro=("muro", CREMA), zocalo_alto=0.9, zocalo_color="#b98e6e",
                  vanos=vanos, puertas=[vanos[0], vanos[2]], balcones=vanos, desde=zb - 0.6 - f.suelo)
    for s in (0.25, f.largo / 3, f.largo * 2 / 3, f.largo - 0.25):
        pilastra(f, s, 0.9 + off, 8.2 + off, ancho=0.45, vuelo=0.08, rol="pintura_acento", color=OCRE)
c.objeto(col)

c = Constructor("E3785f4")
zb, zr = suelo_huella(museo)
ALTO = 10.0
c.prisma(museo, zb - 0.6, zr + ALTO, "muro", GRIS_MUSEO, tapa=False)
techo_auto(c, museo, zr + ALTO - 0.02)


def castillo(f, s0, s1, off, ventanas, portal=None):
    zocalo(f, 1.6 + off, s0=s0, s1=s1, color=MAMPOSTERIA, desde=zb - 0.6 - f.suelo)
    h = 1.9
    while h < ALTO - 1.2:  # llagueado horizontal
        f.caja(s0, s1, h + off, h + 0.06 + off, 0.0, 0.03, "moldura", "#b9c1c8")
        h += 0.55
    fa = adelantada(f, 0.04)
    for s in ventanas:
        if portal is not None and abs(s - portal) < 2.5:
            continue
        ventana(fa, s, 2.4 + off, ancho=1.0, alto=1.6, reja=True, moldura="moldura", color_moldura=GRIS_OSC,
                carpinteria="marco_ventana", color_carpinteria="#3d3a38")
        ventana(fa, s, 5.9 + off, ancho=1.1, alto=2.1, moldura="moldura", color_moldura=GRIS_OSC,
                carpinteria="marco_ventana", color_carpinteria="#3d3a38")
    k = s0 + 0.2  # matacanes bajo el almenado
    while k < s1 - 0.2:
        f.caja(k, k + 0.25, ALTO - 0.75 + off, ALTO - 0.35 + off, 0.0, 0.3, "muro", GRIS_MUSEO)
        k += 0.6
    f.caja(s0, s1, ALTO - 0.35 + off, ALTO + off, -0.3, 0.32, "muro", GRIS_MUSEO)
    almenas(f, ALTO + off, alto=0.7, ancho=0.55, paso=1.1, grosor=0.45, color=GRIS_MUSEO)


def torreon(x, y, radio, alto, z0, zr_):
    """Torreón cilíndrico EMPOTRADO en el muro (fotos 130119/130130): nace del suelo con el mismo basamento de
    mampostería, lleva la imposta gris a media altura, un anillo de matacanes bajo el almenado y saeteras."""
    c.cilindro(x, y, z0 - 0.6, zr_ + 1.6, radio + 0.08, "zocalo_piedra", MAMPOSTERIA, lados=20)
    c.cilindro(x, y, zr_ + 1.6, z0 + alto, radio, "muro", GRIS_MUSEO, lados=20)
    c.cilindro(x, y, zr_ + 5.25, zr_ + 5.55, radio + 0.1, "moldura", GRIS_OSC, lados=20)       # imposta
    c.cilindro(x, y, z0 + alto - 0.9, z0 + alto - 0.5, radio + 0.06, "muro", GRIS_MUSEO, lados=20, radio_arriba=radio + 0.3)
    c.cilindro(x, y, z0 + alto - 0.5, z0 + alto, radio + 0.3, "muro", GRIS_MUSEO, lados=20)
    n_alm = max(6, int(2 * math.pi * radio / 1.0))
    for k in range(n_alm):  # almenas del torreón
        a = 2 * math.pi * k / n_alm
        c.caja_ejes((x + math.cos(a) * (radio + 0.12), y + math.sin(a) * (radio + 0.12), z0 + alto + 0.35),
                    (math.cos(a + math.pi / 2), math.sin(a + math.pi / 2), 0), (math.cos(a), math.sin(a), 0), (0, 0, 1),
                    0.5, 0.4, 0.7, "muro", GRIS_MUSEO)
    for hh in (2.6, 6.4, 8.0):  # saeteras
        for a in (-0.55, 0.0, 0.55):
            ang = math.atan2(N[1], N[0]) + a
            c.caja_ejes((x + math.cos(ang) * (radio + 0.01), y + math.sin(ang) * (radio + 0.01), zr_ + hh),
                        (math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2), 0), (math.cos(ang), math.sin(ang), 0),
                        (0, 0, 1), 0.16, 0.04, 1.3 if hh < 7 else 0.7, "vidrio")


# fachada del museo sobre el lado REAL de su huella recortada que da a Ravelo (auditoría: con la recta del marco l1
# el basamento invadía 1,9 m la vereda)
_lr = [x for x in lados(museo) if x["a_calle"] and x["largo"] > 15]
f = fachada(c, max(_lr, key=lambda x: x["largo"] * (x["normal"][0] * N[0] + x["normal"][1] * N[1])) if _lr
            else frente(10.0, l1["largo"]))
off = zr - f.suelo
L = f.largo
PORTAL = L / 2
# ventanas: ninguna donde nacen los torreones del portal (±2,3 m, radio 1) ni junto al de la esquina
vent = [s_ for s_ in (1.8 + 3.65 * k for k in range(9)) if abs(s_ - PORTAL) > 3.9 and s_ < L - 2.6]
castillo(f, 0.0, L, off, ventanas=vent, portal=PORTAL)
f.caja(0.0, L, 5.25 + off, 5.5 + off, 0.0, 0.1, "moldura", GRIS_OSC)  # imposta gris entre plantas
fa = adelantada(f, 0.05)
puerta(fa, PORTAL, ancho=2.2, alto=3.8 + off, arco=True, color="#5a2e1e", moldura="piedra", color_moldura=MAMPOSTERIA)
f.arco(PORTAL, 0.5, 0.16, 7.0 + off, 0.0, 0.1, "moldura", GRIS_OSC, segmentos=10, medio=False)  # óculo
f.timpano_arco(PORTAL, 0.5, 7.0 + off, 0.02, "vidrio")
f.caja(PORTAL - 1.4, PORTAL + 1.4, 5.7 + off, 6.2 + off, 0.0, 0.06, "letrero")  # «Ejército Nacional»
f.caja(PORTAL - 0.5, PORTAL + 0.5, ALTO + 0.3 + off, ALTO + 1.3 + off, -0.1, 0.12, "pintura_acento", "#c9a24a")  # escudo
for ds in (-2.3, 2.3):  # torreones del portal, empotrados
    q = f.punto(PORTAL + ds, 0, -0.35)   # sobresale ~0,75 m: en la vereda de 2 m queda paso (recorrido a pie)
    torreon(q.x, q.y, 1.0, ALTO + 1.4 + off, f.suelo, zr)
q = f.punto(L - 0.9, 0, -1.0)  # torreón de la esquina SE: sobresale ~0,75 m, deja libre la vereda
torreon(q.x, q.y, 1.7, ALTO + 2.0 + off, f.suelo, zr)
l2 = lado_lienzo(E["E3785f4"], 2, real=True)
f2 = fachada(c, l2)
castillo(f2, 0.0, l2["largo"], zr - f2.suelo, ventanas=[l2["largo"] / 2])
c.objeto(col)

# =========================================================================== atrio, templo y arco de San Francisco
# Rehecho con las correcciones R0041/R0042/R0043 (fotos de referencia del usuario) y 130006/130101:
# - atrio con ARQUERÍA DE 5 ARCOS sobre Ravelo: pilares blancos con farol, pináculos verdes de cerámica sobre cada
#   pilar, muro bajo de mampostería rojiza con rejas de hierro; el arco del medio lleva el PORTÓN de hierro entre dos
#   pilares de sillería; detrás se ve el patio (piso de piedra), NO un muro;
# - la arquería dobla la esquina hacia Arce (2 arcos);
# - templo: hastial blanco con tejado, portada con pilastras salmón y ventana del coro;
# - torre izquierda (~20 m): cuerpo liso, campanario de 2 vanos por cara y remate sencillo;
# - torre derecha (~25 m), en la esquina con Arce: cuerpo con cornisa y pináculos verdes, campanario de un gran vano
#   por cara con la CAMPANA a la vista (la de la Libertad), y remate barroco escalonado con pináculos;
# - el gran ARCO DE SAN FRANCISCO cruza Arce desde el pilar de la esquina, con farol colgado en la clave.
from kit.datos import calle_real_cercana  # noqa: E402

VERDE = "#2e7a68"
SILLAR = "#b98a5c"
RUBBLE = "#9c6a55"
SALMON = "#d88a63"
BRONCE = "#5d4733"

T0, T1 = 44.2, 59.5
t_c = min((t * 0.25 for t in range(int((T1 - 5) * 4), int((T1 + 25) * 4))),
          key=lambda t: calle_real_cercana(*P(t, -0.3))[0] if calle_real_cercana(*P(t, -0.3))[3] == "Calle Aniceto Arce" else 99)
TA0 = t_c - 7.7          # línea de fachada sobre Arce (lado del templo) = cara del pilar del arco
# el pilar del otro lado de Arce no puede caer en la calzada de San Alberto (auditoría: invadía 3,4 m): se busca,
# pasando el eje de Arce, el primer punto de la línea de fachada que no esté en ninguna calzada
from kit.datos import calles_reales as _cr  # noqa: E402


def _en_calzada(x, y):
    for cc in _cr():
        cz = cc["ancho"] / 2 - cc["vereda"]
        for a_, b_ in zip(cc["eje"], cc["eje"][1:]):
            dx, dy = b_[0] - a_[0], b_[1] - a_[1]
            L2 = dx * dx + dy * dy or 1
            tt = ((x - a_[0]) * dx + (y - a_[1]) * dy) / L2
            if 0 <= tt <= 1 and math.hypot(x - a_[0] - tt * dx, y - a_[1] - tt * dy) < cz:
                return True
    return False


TA1 = t_c + 7.7
for k in range(0, 60):
    tt = t_c + 4.0 + k * 0.25
    if not any(_en_calzada(*P(tt + dd, dp)) for dd in (0.0, 0.8, 1.6) for dp in (-1.1, 0.4)):
        TA1 = tt + 1.6
        break
PF = 7.5                 # fondo del atrio
print("[M013] San Francisco: atrio t", T0, "→", round(TA0, 2), "· Arce en t =", round(t_c, 2))

c = Constructor("M013_san_francisco")
zs = [altura_suelo(*P(t)) for t in (T0, (T0 + TA0) / 2, TA0)]
zt = max(altura_suelo(*P(t, PF)) for t in (T0, TA0))
zpiso = max(zs) + 0.35


def pinaculo(f, s, h, d=-0.35, esc=1.0):
    """Pináculo de cerámica verde sobre dado blanco (sobre cada pilar de la arquería y las cornisas de las torres)."""
    f.caja(s - 0.24 * esc, s + 0.24 * esc, h, h + 0.28 * esc, d - 0.24 * esc, d + 0.24 * esc, "moldura", BLANCO)
    f.cilindro_vertical(s, h + 0.28 * esc, h + 0.45 * esc, d, 0.1 * esc, "pintura_acento", VERDE, lados=8)
    f.esfera(s, h + 0.65 * esc, d, 0.22 * esc, "pintura_acento", VERDE)
    p = f.punto(s, 0, d)
    c.cilindro(p.x, p.y, f.suelo + h + 0.78 * esc, f.suelo + h + 1.25 * esc, 0.15 * esc, "pintura_acento", VERDE, lados=8,
               radio_arriba=0.01)


def farol_pared(f, s, h, d=0.0):
    """Farol colonial de hierro con brazo, colgado del pilar."""
    f.caja(s - 0.03, s + 0.03, h + 0.55, h + 0.6, d, d + 0.55, "hierro")
    p = f.punto(s, 0, d + 0.55)
    z = f.suelo + h
    c.cilindro(p.x, p.y, z + 0.4, z + 0.55, 0.03, "hierro", lados=4)
    c.cilindro(p.x, p.y, z - 0.05, z + 0.4, 0.13, "vidrio", "#efe2b5", lados=6, radio_arriba=0.17)
    c.cilindro(p.x, p.y, z + 0.4, z + 0.55, 0.21, "hierro", lados=6, radio_arriba=0.04)
    c.cilindro(p.x, p.y, z - 0.15, z - 0.05, 0.08, "hierro", lados=6, radio_arriba=0.13)


def reja(f, s0, s1, h0, h1, d):
    """Reja de hierro con pasamanos y remate de puntas (como en R0042)."""
    _barrotes(f, s0, s1, h0, h1, d, 0.12)
    f.caja(s0, s1, h1 - 0.05, h1, d - 0.03, d + 0.03, "hierro")
    f.caja(s0, s1, h0 + 0.1, h0 + 0.15, d - 0.03, d + 0.03, "hierro")
    k = s0 + 0.3
    while k < s1 - 0.2:
        f.caja(k - 0.02, k + 0.02, h1, h1 + 0.25, d - 0.02, d + 0.02, "hierro")
        k += 0.36


def arqueria_atrio(f, n, alto_base, gate=None):
    """Arquería del atrio sobre un lado: pilares, rejas sobre el muro bajo, faroles y pináculos."""
    off = zpiso - f.suelo
    pilar = 0.75
    L = f.largo
    luz = (L - pilar * (n + 1)) / n
    h_arr = 3.3 + off
    alto_total = h_arr + luz / 2 + 0.55
    f.caja(0.0, L, -1.0, alto_base + off, -0.75, 0.0, "zocalo_piedra", RUBBLE)  # muro bajo de mampostería
    arqueria_lisa(f, 0.0, n, luz, h_arr, pilar=pilar, d0=-0.75, d1=0.05, alto_total=alto_total,
                  muro=("muro", BLANCO), moldura=("moldura", BLANCO), segmentos=16)
    s = 0.0
    for k in range(n + 1):
        sp = s + pilar / 2
        pinaculo(f, sp, alto_total + 0.25)
        if 0 < k < n or n == 2:
            farol_pared(f, sp, 2.9 + off, 0.05)
        if k < n:
            a0, a1 = s + pilar, s + pilar + luz
            if gate is not None and k == gate:
                # portón de hierro entre dos pilares de sillería con remate piramidal
                for sp2 in (a0 + 0.28, a1 - 0.28):
                    f.caja(sp2 - 0.26, sp2 + 0.26, -0.5, 3.6 + off, -0.7, -0.1, "piedra", SILLAR)
                    for hh in (0.8, 1.6, 2.4, 3.2):  # juntas de los sillares
                        f.caja(sp2 - 0.27, sp2 + 0.27, hh + off, hh + 0.04 + off, -0.71, -0.09, "moldura", "#e2cfb3")
                    q = f.punto(sp2, 0, -0.4)
                    c.cilindro(q.x, q.y, f.suelo + 3.6 + off, f.suelo + 4.3 + off, 0.38, "piedra", SILLAR, lados=4,
                               radio_arriba=0.04)
                g0, g1 = a0 + 0.54, a1 - 0.54
                _barrotes(f, g0, g1, 0.25 + off, 3.0 + off, -0.4, 0.11)
                f.caja(g0, g1, 0.25 + off, 0.75 + off, -0.42, -0.38, "hierro")                 # zócalo del portón
                f.caja(g0, g1, 3.0 + off, 3.06 + off, -0.43, -0.37, "hierro")
                f.arco((g0 + g1) / 2, (g1 - g0) / 2 - 0.05, 0.05, 3.0 + off, -0.43, -0.37, "hierro", segmentos=10)
                cm = (g0 + g1) / 2                                                               # cruz con aro
                f.caja(cm - 0.03, cm + 0.03, 3.0 + off + (g1 - g0) / 2, 4.3 + off, -0.42, -0.38, "hierro")
                f.caja(cm - 0.35, cm + 0.35, 3.95 + off, 4.0 + off, -0.42, -0.38, "hierro")
                f.arco(cm, 0.22, 0.04, 3.75 + off, -0.42, -0.38, "hierro", segmentos=8, medio=False)
                f.caja(a0, a1, -0.5, 0.25 + off, -0.75, 0.0, "piedra", "#c9b49a")                  # umbral / grada
            else:
                reja(f, a0 + 0.05, a1 - 0.05, alto_base + off, alto_base + 1.35 + off, -0.38)
            s = a1
    return luz


# --- atrio: frente a Ravelo (5 arcos, portón en el del medio) y vuelta sobre Arce (2 arcos)
fa_atrio = fachada(c, frente(T0, TA0))
arqueria_atrio(fa_atrio, 5, 1.0, gate=2)
# Arce no es perpendicular a Ravelo: la vuelta del atrio y el cuerpo lateral siguen la línea de fachada REAL de
# Arce (auditoría: con t = TA0 constante se metían 3,4 m en la calzada)
from kit.datos import recortar_a_calles as _rec  # noqa: E402
_ca = [cc for cc in _cr() if cc["nombre"] in ("Calle Aniceto Arce", "Calle Fray José Antonio de San Alberto")]
_q0 = P(TA0, 0.0)
_seg = min(((a_, b_) for cc in _ca for a_, b_ in zip(cc["eje"], cc["eje"][1:])),
           key=lambda ab: math.hypot((ab[0][0] + ab[1][0]) / 2 - _q0[0], (ab[0][1] + ab[1][1]) / 2 - _q0[1]))
_L = math.hypot(_seg[1][0] - _seg[0][0], _seg[1][1] - _seg[0][1])
DA = ((_seg[1][0] - _seg[0][0]) / _L, (_seg[1][1] - _seg[0][1]) / _L)
if DA[0] * IN[0] + DA[1] * IN[1] < 0:
    DA = (-DA[0], -DA[1])                      # a lo largo de Arce, hacia adentro de la manzana
NA = (DA[1], -DA[0]) if (DA[1] * U[0] - DA[0] * U[1]) > 0 else (-DA[1], DA[0])   # normal hacia Arce


def QA(s_, d_=0.0):
    """Punto sobre la línea de fachada de Arce: s_ hacia adentro desde la esquina, d_ hacia Arce."""
    return (_q0[0] + DA[0] * s_ + NA[0] * d_, _q0[1] + DA[1] * s_ + NA[1] * d_)


f_arce = fachada(c, lado_virtual(QA(0.0), QA(PF), NA))
arqueria_atrio(f_arce, 2, 1.0)
# piso del atrio (patio de piedra a la vista a través de las rejas)
c.prisma(rect(T0 + 0.3, TA0 - 0.3, -0.05, PF + 0.5), min(zs) - 0.6, zpiso, "adoquin", "#bfae96", tapa=True)
# muro del lado del museo (cierra el atrio)
c.prisma(rect(T0, T0 + 0.6, -0.75, PF), min(zs) - 0.6, zpiso + 3.0, "muro", BLANCO, tapa=True)

# --- templo: nave y hastial
tn0, tn1 = T0 + 6.2, TA0 - 6.0
nave = rect(tn0, tn1, PF, PF + 32.0)
c.prisma(nave, zt - 2.0, zpiso + 10.5, "muro", BLANCO, tapa=True)
tejado_dos_aguas(c, nave, zpiso + 10.5, pendiente=30, vuelo=0.35)
ff = fachada(c, frente(tn0, tn1, PF))
off = zpiso - ff.suelo
W = ff.largo
fp = adelantada(ff, 0.05)
puerta(fp, W / 2, ancho=2.4, alto=4.8 + off, arco=True, color="#5a2e1e", moldura="moldura", color_moldura=BLANCO)
for ds in (-1.75, -2.45, 1.75, 2.45):  # pilastras pareadas salmón de la portada
    pilastra(fp, W / 2 + ds, off, 6.6 + off, ancho=0.45, vuelo=0.14, rol="pintura_acento", color=SALMON)
fp.caja(W / 2 - 3.0, W / 2 + 3.0, 6.6 + off, 7.1 + off, 0.0, 0.25, "moldura", BLANCO)       # entablamento
fp.caja(W / 2 - 0.6, W / 2 + 0.6, 7.2 + off, 8.2 + off, 0.0, 0.08, "pintura_acento", SALMON)  # hornacina
ventana(fp, W / 2, 8.5 + off, ancho=1.2, alto=1.6, reja=True, moldura="moldura", color_moldura=BLANCO,
        carpinteria="marco_ventana", color_carpinteria="#3d3a38")
ff.caja(-0.2, W + 0.2, 10.3 + off, 10.6 + off, 0.0, 0.3, "moldura", BLANCO)                   # cornisa
for sp in (0.4, W - 0.4):
    pinaculo(ff, sp, 10.6 + off, d=0.1)
# cruz sobre el hastial
cumbre = zpiso + 10.5 + (W / 2) * math.tan(math.radians(30))
q = ff.punto(W / 2, 0, -0.2)
c.caja_ejes((q.x, q.y, cumbre + 0.8), (U[0], U[1], 0), (N[0], N[1], 0), (0, 0, 1), 0.08, 0.08, 1.6, "hierro")
c.caja_ejes((q.x, q.y, cumbre + 1.15), (U[0], U[1], 0), (N[0], N[1], 0), (0, 0, 1), 0.7, 0.08, 0.08, "hierro")

# --- cuerpo lateral sobre Arce detrás de la torre (muro con arcos ciegos y contrafuertes, foto R0043)
lat = _rec([QA(PF + 5.0, -0.2), QA(PF + 32.0, -0.2), QA(PF + 32.0, -6.0), QA(PF + 5.0, -6.0)]) or \
    rect(TA0 - 6.0, TA0 - 0.2, PF + 5.0, PF + 32.0)
c.prisma(lat, zt - 2.0, zpiso + 8.0, "muro", BLANCO, tapa=True)
tejado_dos_aguas(c, lat, zpiso + 8.0, pendiente=22, vuelo=0.3)
fl = fachada(c, lado_virtual(QA(PF + 5.0, -0.2), QA(PF + 32.0, -0.2), NA))
ofl = zpiso - fl.suelo
zocalo(fl, 1.4 + ofl, color=RUBBLE, desde=-1.0)
# LAS 14 HORNACINAS (foto R0043, a la derecha sobre Arce): hilera de nichos altos de medio punto sobre el zócalo de
# piedra, con moldura blanca y una crucecita encima. La leyenda del niño del caballito (encuentro nino_hornacinas)
# dice que en una falta la cruz: se la llevó él. Sin contrafuertes entre nichos (en la foto la hilera es continua).
N_HORN = 14
HORNACINA_SIN_CRUZ = 9
paso_h = (fl.largo - 2.4) / N_HORN
hn_ancho, hn_z0, hn_z1 = paso_h * 0.56, 1.9 + ofl, 4.3 + ofl
for i in range(N_HORN):
    k = 1.2 + paso_h * (i + 0.5)
    fl.caja(k - hn_ancho / 2 - 0.12, k + hn_ancho / 2 + 0.12, hn_z0 - 0.18, hn_z0, 0.0, 0.16, "moldura", BLANCO)   # repisa
    fl.caja(k - hn_ancho / 2 - 0.1, k - hn_ancho / 2, hn_z0, hn_z1, 0.0, 0.16, "moldura", BLANCO)                 # jambas
    fl.caja(k + hn_ancho / 2, k + hn_ancho / 2 + 0.1, hn_z0, hn_z1, 0.0, 0.16, "moldura", BLANCO)
    fl.arco(k, hn_ancho / 2, 0.12, hn_z1, 0.0, 0.16, "moldura", BLANCO, segmentos=10)
    # fondo en sombra (el muro es macizo: el hueco se sugiere con el fondo oscuro y el marco saliente)
    fl.caja(k - hn_ancho / 2, k + hn_ancho / 2, hn_z0, hn_z1, 0.0, 0.03, "muro", "#b7ae9f")
    fl.arco(k, 0.01, hn_ancho / 2 - 0.01, hn_z1, 0.0, 0.03, "muro", "#b7ae9f", segmentos=10)
    if i != HORNACINA_SIN_CRUZ:                                                                                # cruz
        zc_ = hn_z1 + hn_ancho / 2 + 0.25
        fl.caja(k - 0.04, k + 0.04, zc_, zc_ + 0.55, 0.0, 0.06, "hierro")
        fl.caja(k - 0.17, k + 0.17, zc_ + 0.33, zc_ + 0.4, 0.0, 0.06, "hierro")
fl.caja(0.0, fl.largo, 7.7 + ofl, 8.0 + ofl, 0.0, 0.25, "moldura", BLANCO)
_qh = QA(PF + 5.0 + 1.2 + paso_h * (HORNACINA_SIN_CRUZ + 0.5), 1.6)
print("[M013] hornacina sin cruz: mundo x=%.1f z=%.1f · mira a x=%.1f z=%.1f" % (
    _qh[0], -_qh[1], QA(PF + 5.0 + 1.2 + paso_h * (HORNACINA_SIN_CRUZ + 0.5), -0.2)[0],
    -QA(PF + 5.0 + 1.2 + paso_h * (HORNACINA_SIN_CRUZ + 0.5), -0.2)[1]))


# --- torres
def cornisa_torre(f, h, vuelo=0.3, alto=0.4):
    f.caja(-vuelo, f.largo + vuelo, h - alto, h, 0.0, vuelo, "moldura", BLANCO)


def vano_arco(f, s, h0, luz, alto, profundo=True):
    """Vano en arco del campanario (hueco oscuro con rosca y jambas)."""
    r = luz / 2
    f.caja(s - r, s + r, h0, h0 + alto - r, 0.0, 0.02, "madera", "#2b2622")    # hueco en sombra (no vidrio: no refleja)
    f.timpano_arco(s, r, h0 + alto - r, 0.02, "madera", "#2b2622")
    f.arco(s, r, 0.18, h0 + alto - r, 0.0, 0.12, "moldura", BLANCO, segmentos=10)
    f.caja(s - r - 0.18, s - r, h0, h0 + alto - r, 0.0, 0.12, "moldura", BLANCO)
    f.caja(s + r, s + r + 0.18, h0, h0 + alto - r, 0.0, 0.12, "moldura", BLANCO)
    f.caja(s - r - 0.25, s + r + 0.25, h0 - 0.2, h0, 0.0, 0.2, "moldura", BLANCO)


def campana(x, y, z, r=0.55, alto=0.9):
    c.cilindro(x, y, z + alto, z + alto + 0.25, 0.08, "hierro", lados=6)
    c.cilindro(x, y, z + alto * 0.35, z + alto, r * 0.62, "metal", BRONCE, lados=14, radio_arriba=r * 0.45)
    c.cilindro(x, y, z, z + alto * 0.35, r, "metal", BRONCE, lados=14, radio_arriba=r * 0.62)
    c.caja_ejes((x, y, z + alto + 0.3), (U[0], U[1], 0), (N[0], N[1], 0), (0, 0, 1), 2.2, 0.18, 0.2, "madera")  # yugo


def torre(t0, t1, p0, cuerpo, campanario, tipo):
    lado_t = t1 - t0
    huella = rect(t0, t1, p0, p0 + lado_t)
    z0 = min(altura_suelo(x, y) for x, y in huella) - 0.6
    ztc = zpiso + cuerpo
    c.prisma(huella, z0, ztc, "muro", BLANCO, tapa=True)
    for l in lados(huella):
        f = Fachada(c, l, zpiso)
        cornisa_torre(f, cuerpo, 0.3, 0.45)
        if tipo == "grande":
            pilastra(f, 0.35, 0.0, cuerpo - 0.45, ancho=0.5, vuelo=0.1, rol="moldura", color=BLANCO, capitel=False)
            pilastra(f, f.largo - 0.35, 0.0, cuerpo - 0.45, ancho=0.5, vuelo=0.1, rol="moldura", color=BLANCO, capitel=False)
            ventana(f, f.largo / 2, cuerpo - 4.2, ancho=0.7, alto=1.1, moldura="moldura", color_moldura=BLANCO,
                    carpinteria="marco_ventana", color_carpinteria="#3d3a38")
            for sp in (0.35, f.largo - 0.35):
                pinaculo(f, sp, cuerpo, d=0.0, esc=1.2)
        else:
            vano_arco(f, f.largo / 2, cuerpo - 4.0, 0.7, 1.6)
    # campanario
    ins = 0.35
    hc = rect(t0 + ins, t1 - ins, p0 + ins, p0 + lado_t - ins)
    c.prisma(hc, ztc, ztc + campanario, "muro", BLANCO, tapa=True)
    cx, cy = P((t0 + t1) / 2, p0 + lado_t / 2)
    for l in lados(hc):
        f = Fachada(c, l, ztc)
        if tipo == "grande":
            vano_arco(f, f.largo / 2, 0.9, 2.1, campanario - 1.6)
            for sp in (0.3, f.largo - 0.3):
                pilastra(f, sp, 0.3, campanario - 0.5, ancho=0.45, vuelo=0.12, rol="moldura", color=BLANCO)
        else:
            for sv in (f.largo * 0.3, f.largo * 0.7):
                vano_arco(f, sv, 0.9, 0.95, campanario - 1.7)
        cornisa_torre(f, campanario, 0.3, 0.4)
    if tipo == "grande":
        campana(cx + N[0] * 0.6, cy + N[1] * 0.6, ztc + 1.2, r=0.8, alto=1.45)   # la campana grande, hacia Ravelo
        campana(cx - N[0] * 0.7, cy - N[1] * 0.7, ztc + 1.4, r=0.5, alto=0.9)
        # remate barroco: cuerpo chico con vano, crestería escalonada y pináculos
        ztop = ztc + campanario
        h3 = rect(t0 + 1.0, t1 - 1.0, p0 + 1.0, p0 + lado_t - 1.0)
        c.prisma(h3, ztop, ztop + 2.4, "muro", BLANCO, tapa=True)
        for l in lados(h3):
            f = Fachada(c, l, ztop)
            vano_arco(f, f.largo / 2, 0.4, 0.8, 1.5)
            cornisa_torre(f, 2.4, 0.2, 0.3)
            f.caja(f.largo / 2 - 0.9, f.largo / 2 + 0.9, 2.4, 2.9, -0.1, 0.1, "muro", BLANCO)   # crestería escalonada
            f.caja(f.largo / 2 - 0.45, f.largo / 2 + 0.45, 2.9, 3.4, -0.1, 0.1, "muro", BLANCO)
        for x, y in hc:
            c.cilindro(x, y, ztop, ztop + 0.5, 0.25, "muro", BLANCO, lados=8)
            c.esfera(x, y, ztop + 0.75, 0.25, "muro", BLANCO)
            c.cilindro(x, y, ztop + 0.95, ztop + 1.5, 0.1, "muro", BLANCO, lados=6, radio_arriba=0.02)
        c.cilindro(cx, cy, ztop + 2.4, ztop + 3.6, 0.22, "muro", BLANCO, lados=8, radio_arriba=0.08)
        c.esfera(cx, cy, ztop + 3.8, 0.22, "muro", BLANCO)
    else:
        campana(cx, cy, ztc + 1.0, r=0.4, alto=0.7)
        ztop = ztc + campanario
        h3 = rect(t0 + 0.9, t1 - 0.9, p0 + 0.9, p0 + lado_t - 0.9)
        c.prisma(h3, ztop, ztop + 0.9, "muro", BLANCO, tapa=True)
        for x, y in hc:
            c.esfera(x, y, ztop + 0.3, 0.22, "muro", BLANCO)
        c.cilindro(cx, cy, ztop + 0.9, ztop + 1.9, 0.9, "muro", BLANCO, lados=4, radio_arriba=0.05)


torre(T0 + 0.9, T0 + 5.9, PF - 0.4, 13.5, 5.6, "sencilla")      # ~20 m
torre(TA0 - 6.0, TA0 - 0.6, PF - 0.4, 14.5, 6.4, "grande")      # ~25 m con remate

# --- Arco de San Francisco sobre la Calle Arce (pilares sobre las dos líneas de fachada)
print("[M013] arco sobre Arce:", round(TA0, 2), "→", round(TA1, 2))
# Ravelo se quiebra en el cruce (del otro lado de Arce sigue San Alberto, corrida): el pilar lejano va en la
# esquina REAL de enfrente, sobre la vereda, y el arco cruza en diagonal (auditoría: caía en la calzada).
# R0227 (2026-11-24): el pilar lejano apoya en la esquina de la Plaza San Francisco, en la línea de la arquería de la
# plaza (AMP_SAN_ALBERTO), que arranca justo donde termina el pilar; antes se buscaba "el primer punto fuera de la
# calzada" y caía 1,4 m delante de esa arquería, metido en su primer vano.
from AMP_SAN_ALBERTO import F as _F_sa, T_ARCO1 as _T_sa, D_ARCO as _D_sa  # noqa: E402
PIL_ARCO = 2.2           # pilares macizos (en la foto 115737 son tan anchos como hondos; con 1,6 × 1,3 se veía delgado)
_A = P(TA0, -0.3)
_B = _F_sa(_T_sa, _D_sa)
TA1 = TA0 + math.hypot(_B[0] - _A[0], _B[1] - _A[1])
print("[M013] pilar lejano del arco en", tuple(round(v, 1) for v in _B))
_ua = ((_B[0] - _A[0]) / (TA1 - TA0), (_B[1] - _A[1]) / (TA1 - TA0))
_na = (_ua[1], -_ua[0]) if (_ua[1] * N[0] - _ua[0] * N[1]) > 0 else (-_ua[1], _ua[0])
fa_arco = fachada(c, lado_virtual(_A, _B, _na))
off = max(zs) - fa_arco.suelo
luz_a = (TA1 - TA0) - 2 * PIL_ARCO
h_a = 6.0 + off
top_a = h_a + luz_a / 2 + 1.0
arqueria_lisa(fa_arco, 0.0, 1, luz_a, h_a, pilar=PIL_ARCO, d0=-1.0, d1=1.0, alto_total=top_a,
              muro=("muro", BLANCO), moldura=("moldura", BLANCO), segmentos=24)
for sp in (PIL_ARCO / 2, (TA1 - TA0) - PIL_ARCO / 2):
    fa_arco.caja(sp - PIL_ARCO / 2 - 0.08, sp + PIL_ARCO / 2 + 0.08, -0.6, 1.2 + off, -1.08, 1.08, "zocalo_piedra",
                 RUBBLE)                                                                       # basamento de los pilares
    for lado in (-1, 1):                                                       # tableros rehundidos en las dos caras
        fa_arco.caja(sp - PIL_ARCO / 2 + 0.3, sp + PIL_ARCO / 2 - 0.3, 1.6 + off, h_a - 0.6,
                     *((1.0, 1.06) if lado > 0 else (-1.06, -1.0)), "moldura", "#eeebe5")
    pinaculo(fa_arco, sp, top_a + 0.25, d=0.0, esc=1.2)
cm = (TA1 - TA0) / 2
fa_arco.caja(cm - 1.6, cm + 1.6, top_a + 0.25, top_a + 0.8, -0.7, 0.7, "muro", BLANCO)          # crestería central
fa_arco.caja(cm - 0.8, cm + 0.8, top_a + 0.8, top_a + 1.3, -0.55, 0.55, "muro", BLANCO)
pinaculo(fa_arco, cm, top_a + 1.3, d=0.0, esc=1.0)
# farol colgado de la clave
q = fa_arco.punto(cm, 0, 0.0)
zc = fa_arco.suelo + h_a + luz_a / 2
c.cilindro(q.x, q.y, zc - 1.6, zc, 0.02, "hierro", lados=4)
c.cilindro(q.x, q.y, zc - 2.25, zc - 1.6, 0.17, "vidrio", "#efe2b5", lados=6, radio_arriba=0.24)
c.cilindro(q.x, q.y, zc - 1.6, zc - 1.42, 0.3, "hierro", lados=6, radio_arriba=0.05)
c.objeto(col)

# =========================================================================== Mercado Central y convento (sin foto útil)
# --- Mercado Central (E994825): esquina Ravelo × Junín con PLACITA y MURO DEL MURAL, cuerpo con ventanales en arco
# Fotos 130157, 130216, 130221, 130226, 130228: en la esquina, placita elevada (bordillo amarillo) con un árbol
# grande podado en paraguas, farol y bancos; detrás, muro blanco alto con hastial, un gran mural (retrato sobre fondo
# verde) y un emblema redondo; el cuerpo del mercado sigue el orden del frente de Ravelo (M021): locales en arco
# abajo y grandes ventanales de medio punto arriba.
from kit.datos import _cortar_semiplano  # noqa: E402
from base_plazas import banco  # noqa: E402
from piezas_claude import arbol_paraguas  # noqa: E402
from adornos_claude import farol_cc0  # noqa: E402
hm = [tuple(p) for p in E["E994825"]["huella"]]
_ci = min(range(len(hm)), key=lambda i: math.hypot(hm[i][0] + 206.0, hm[i][1] - 62.0))
CQ, AQ, BQ = hm[_ci], hm[_ci - 1], hm[(_ci + 1) % len(hm)]


def _u(a, b):
    L_ = math.hypot(b[0] - a[0], b[1] - a[1])
    return ((b[0] - a[0]) / L_, (b[1] - a[1]) / L_)


uA, uB = _u(CQ, AQ), _u(CQ, BQ)
# 2026-11-13: la esquina va sobre la línea de fachada NUEVA de la peatonal (la del lienzo quedaba 1,2 m metida en la
# vereda): intersección de esa línea con el frente a Ravelo de la huella; uA = sentido de Junín, uB = de Ravelo
import peatonal_marco as _PMq  # noqa: E402
_uj = _PMq.U
if abs(uA[0] * _uj[0] + uA[1] * _uj[1]) < abs(uB[0] * _uj[0] + uB[1] * _uj[1]):
    uA, uB = uB, uA
uA = _uj
_p0 = _PMq.P("SE", 0.0, 0.0)
_den = uB[0] * uA[1] - uB[1] * uA[0]
if abs(_den) > 1e-6:
    _t = ((_p0[0] - CQ[0]) * uA[1] - (_p0[1] - CQ[1]) * uA[0]) / _den
    CQ = (CQ[0] + uB[0] * _t, CQ[1] + uB[1] * _t)
bq = _u((0.0, 0.0), (uA[0] + uB[0], uA[1] + uB[1]))
Lp = 6.0            # la placita llega hasta donde arranca el frente del mercado de PEATONAL.py (fse(6))
DPL = Lp * max(0.3, uA[0] * bq[0] + uA[1] * bq[1])
W1 = (CQ[0] + uA[0] * Lp, CQ[1] + uA[1] * Lp)
W2 = (CQ[0] + uB[0] * Lp, CQ[1] + uB[1] * Lp)
merc = _cortar_semiplano(hm, CQ[0], CQ[1], bq[0], bq[1], DPL)
# 2026-11-13 (R0087): el frente a la Peatonal de Junín lo construye PEATONAL.py; el cuerpo del mercado queda detrás de
# su franja (antes asomaba 4 m delante de la fachada nueva: "esos dos pedazos blancos sobresalen")
from peatonal_marco import cortar_franja as _cf  # noqa: E402
merc = _cf(merc, "SE") or merc
MERC_ALTO = 9.2

c = Constructor("E994825")
zb, zr = suelo_huella(merc)
c.prisma(merc, zb - 0.6, zr + MERC_ALTO, "muro", "#f5f4f0", tapa=False)
# Cubierta (vista aérea 2026-11-13: con techo_auto quedaba un anillo de tejas y un patio de 5 000 m² vacío; el
# Mercado Central es una nave cubierta): azotea perimetral detrás del pretil, gran cubierta de calamina a dos aguas
# bajas sobre el mayor rectángulo interior y un linternón vidriado a lo largo de la cumbrera.
techo_plano(c, merc, zr + MERC_ALTO - 0.02)


def _rect_interior(poly, margen):
    """Mayor rectángulo (orientado al lado más largo) centrado en el centroide que cabe a 'margen' m de los bordes."""
    from kit.datos import _dentro as _dn
    lad = max(zip(poly, poly[1:] + poly[:1]), key=lambda e: math.hypot(e[1][0] - e[0][0], e[1][1] - e[0][1]))
    ux_, uy_ = _u(lad[0], lad[1])
    vx_, vy_ = -uy_, ux_
    cx_ = sum(p[0] for p in poly) / len(poly)
    cy_ = sum(p[1] for p in poly) / len(poly)

    def dist_borde(x, y):
        d = 1e9
        for a_, b_ in zip(poly, poly[1:] + poly[:1]):
            dx_, dy_ = b_[0] - a_[0], b_[1] - a_[1]
            L2 = dx_ * dx_ + dy_ * dy_ or 1
            t = max(0, min(1, ((x - a_[0]) * dx_ + (y - a_[1]) * dy_) / L2))
            d = min(d, math.hypot(x - a_[0] - t * dx_, y - a_[1] - t * dy_))
        return d

    def cabe(hu, hv):
        for su in (-1, -0.5, 0, 0.5, 1):
            for sv in (-1, -0.5, 0, 0.5, 1):
                if abs(su) < 1 and abs(sv) < 1:
                    continue
                x = cx_ + ux_ * hu * su + vx_ * hv * sv
                y = cy_ + uy_ * hu * su + vy_ * hv * sv
                if not _dn(x, y, poly) or dist_borde(x, y) < margen:
                    return False
        return True
    mejor = None
    for hv in [k * 0.5 for k in range(4, 80)]:
        hu = 2.0
        while cabe(hu + 0.5, hv):
            hu += 0.5
        if cabe(hu, hv) and (mejor is None or hu * hv > mejor[0] * mejor[1]):
            mejor = (hu, hv)
    if not mejor:
        return None, None
    hu, hv = mejor
    P_ = lambda a_, b_: (cx_ + ux_ * a_ + vx_ * b_, cy_ + uy_ * a_ + vy_ * b_)
    return [P_(-hu, -hv), P_(hu, -hv), P_(hu, hv), P_(-hu, hv)], (ux_, uy_)


nave, eje = _rect_interior(merc, 3.0)
if nave:
    # calamina plana sobre todo el patio (techos_con_patio pone después el anillo de tejas del borde): sin ella,
    # entre el anillo y la nave quedaba el piso del patio a la vista desde el aire
    c.tapa(merc, zr + MERC_ALTO - 0.9, "metal", "#9ea5a9")
    zc = zr + MERC_ALTO - 0.05
    CALAMINA = "#a9afb2"
    alto_n = tejado_dos_aguas(c, nave, zc, pendiente=12, vuelo=0.3, teja="metal", color=CALAMINA,
                              hastial="muro", color_hastial="#f5f4f0", alto_max=2.4, cumbrera=eje)
    # linternón: franja estrecha a lo largo de la cumbrera, costados vidriados y su propio techito
    ux_, uy_ = eje
    vx_, vy_ = -uy_, ux_
    cxn = sum(p[0] for p in nave) / 4
    cyn = sum(p[1] for p in nave) / 4
    hu_n = max(abs((p[0] - cxn) * ux_ + (p[1] - cyn) * uy_) for p in nave) - 2.0
    P_ = lambda a_, b_: (cxn + ux_ * a_ + vx_ * b_, cyn + uy_ * a_ + vy_ * b_)
    lint = [P_(-hu_n, -1.6), P_(hu_n, -1.6), P_(hu_n, 1.6), P_(-hu_n, 1.6)]
    c.prisma(lint, zc + alto_n - 0.6, zc + alto_n + 1.1, "vidrio", "#3f5a63", tapa=False)
    k = -hu_n
    while k <= hu_n:                                                             # montantes del linternón
        for sv in (-1.62, 1.62):
            x_, y_ = P_(k, sv)
            c.caja(x_ - 0.05, y_ - 0.05, zc + alto_n - 0.6, x_ + 0.05, y_ + 0.05, zc + alto_n + 1.1, "metal", "#7d8488")
        k += 2.0
    tejado_dos_aguas(c, lint, zc + alto_n + 1.1, pendiente=15, vuelo=0.35, teja="metal", color=CALAMINA,
                     hastial="metal", color_hastial=CALAMINA, alto_max=0.8, cumbrera=eje)
else:
    techo_auto(c, merc, zr + MERC_ALTO - 0.02, zpatio=zb)


def fachada_mercado(f, n):
    off = zr - f.suelo
    paso = f.largo / n
    zocalo(f, 0.5 + off, color="#b3a493", sillares=False, desde=zb - 0.6 - f.suelo)
    fa = adelantada(f, 0.03)
    for k in range(n):
        s = paso * (k + 0.5)
        a = min(3.0, paso - 0.9)
        fa.caja(s - a / 2, s + a / 2, 0.0, 2.4 + off, 0.0, 0.01, "vidrio")
        fa.timpano_arco(s, a / 2, 2.4 + off, 0.01, "vidrio")
        fa.arco(s, a / 2, 0.22, 2.4 + off, 0.0, 0.08, "moldura", "#f5f4f0", segmentos=12)
        w = min(3.2, paso - 0.7)
        h0, ha = 5.4 + off, 6.0 + off
        fa.caja(s - w / 2, s + w / 2, h0, ha, 0.0, 0.01, "vidrio")
        fa.timpano_arco(s, w / 2, ha, 0.01, "vidrio")
        fa.arco(s, w / 2, 0.16, ha, 0.0, 0.07, "moldura", "#f5f4f0", segmentos=12)
        for jj in range(1, 6):
            sx = s - w / 2 + w * jj / 6
            alto_v = ha + math.sqrt(max(0.0, (w / 2) ** 2 - (sx - s) ** 2)) - 0.05
            fa.caja(sx - 0.03, sx + 0.03, h0, alto_v, 0.0, 0.04, "marco_ventana", "#e9ecef")
        fa.caja(s - w / 2 - 0.1, s + w / 2 + 0.1, h0 - 0.12, h0, 0.0, 0.12, "moldura", "#f5f4f0")
    imposta(f, 4.5 + off, alto=0.2, vuelo=0.1, color="#f5f4f0")
    cornisa(f, MERC_ALTO - 0.6 + off, vuelo=0.2, alto=0.3, color="#f5f4f0")
    parapeto(f, MERC_ALTO - 0.3 + off, alto=0.4, color="#f5f4f0")


TOLDOS = ["#f1eee6", "#f1eee6", "#efe7d6", "#e9e2d2", "#d9573a", "#e8823a"]
MERCADERIA = ["#c94f4f", "#3f7fb5", "#e8c64a", "#5a9a5a", "#d98c6a", "#8a5aa0", "#f2f0ea"]


def tienda(f, s0, s1, off, rnd_t, toldo=None):
    """Local abierto del mercado (R0046–R0049): hueco oscuro hondo, mercadería de colores colgada y apilada,
    cortina enrollada arriba y toldo de lona inclinado sobre la vereda."""
    a0, a1 = s0 + 0.25, s1 - 0.25
    f.caja(a0, a1, 0.0, 3.0 + off, 0.0, 0.02, "madera", "#2a2420")   # interior en sombra (no coplanar: parpadeaba)
    f.caja(a0, a1, 3.0 + off, 3.35 + off, 0.0, 0.12, "metal", "#9aa0a3")               # cortina enrollada
    k = a0 + 0.15
    while k < a1 - 0.3:                                                                # mercadería colgada / apilada
        hh = rnd_t.uniform(0.9, 2.4)
        f.caja(k, k + rnd_t.uniform(0.3, 0.6), 0.0, hh + off, 0.0, rnd_t.uniform(0.15, 0.5), "letrero", rnd_t.choice(MERCADERIA))
        k += rnd_t.uniform(0.4, 0.8)
    col_t = toldo or rnd_t.choice(TOLDOS)
    p0, p1 = f.punto(a0 - 0.1, 3.4 + off, 0.0), f.punto(a1 + 0.1, 3.4 + off, 0.0)
    q0, q1 = f.punto(a0 - 0.1, 2.85 + off, 1.7), f.punto(a1 + 0.1, 2.85 + off, 1.7)
    f.c.poligono([p0, p1, q1, q0], "letrero", col_t, grosor=0.04, normal_extrusion=(0, 0, 1))
    f.caja(a0 - 0.1, a1 + 0.1, 2.55 + off, 2.85 + off, 1.68, 1.72, "letrero", col_t)          # faldón


def luneto(f, s, off, r=1.35):
    """Ventanal de medio punto de la planta alta (luneto), con vidrio y radios de carpintería."""
    h = 4.75 + off
    f.timpano_arco(s, r, h, 0.02, "vidrio", "#33505a")
    f.arco(s, r, 0.16, h, 0.0, 0.08, "moldura", "#f5f4f0", segmentos=12)
    for ang in (0.5, 1.05, 1.57, 2.1, 2.65):
        f.caja(s + math.cos(ang) * r * 0.5 - 0.025, s + math.cos(ang) * r * 0.5 + 0.025, h, h + math.sin(ang) * r - 0.05,
               0.0, 0.05, "marco_ventana", "#e9ecef")
    f.caja(s - r - 0.1, s + r + 0.1, h - 0.15, h, 0.0, 0.14, "moldura", "#f5f4f0")


import random as _rt  # noqa: E402
rnd_t = _rt.Random("mercado-junin")
# Junín: TODO el lado SE de la cuadra (mercado, edificio alto, entrada con escaleras, edificios modernos hasta
# Hernando Siles) lo construye junin_norte.py sobre la línea real de la vereda (R0045–R0058)
_frentes = [l for l in lados(merc) if l["a_calle"] and l["largo"] >= 5 and "Junín" not in l["calle"]]
for l in _frentes:
    fachada_mercado(fachada(c, l), max(1, round(l["largo"] / 4.2)))
c.objeto(col)
c = Constructor("E994825_mural")   # muro del mural (el cuerpo del mercado ya se exportó arriba)
# muro del mural: más alto que el mercado, con hastial y emblema redondo; mira a la esquina
fm = fachada(c, lado_virtual(W1, W2, (-bq[0], -bq[1])))
offm = zr - fm.suelo
Lm = fm.largo
fm.caja(0.0, Lm, -0.6, 10.6 + offm, -0.5, 0.0, "muro", "#f6f5f1")
fm.caja(-0.15, Lm + 0.15, 10.4 + offm, 10.6 + offm, -0.5, 0.1, "moldura", "#f6f5f1")
# remate en HASTIAL (fotos 130221–130228), con su moldura y el emblema redondo con cruz en el centro
sm = Lm / 2
cima = 12.4 + offm
nn = (-fm.n.x * 0.5, -fm.n.y * 0.5, 0.0)
c.poligono([fm.punto(0.0, 10.6 + offm, 0.0), fm.punto(Lm, 10.6 + offm, 0.0), fm.punto(sm, cima, 0.0)], "muro",
           "#f6f5f1", grosor=0.5, normal_extrusion=nn)
fm.arco(sm, 0.75, 0.12, 10.9 + offm, 0.0, 0.1, "moldura", "#d9d4c8", segmentos=16, medio=False)
fm.timpano_arco(sm, 0.62, 10.9 + offm, 0.04, "pintura_acento", "#c9a24a")
fm.caja(sm - 0.05, sm + 0.05, cima - 0.2, cima + 0.9, 0.0, 0.1, "hierro", "#2f2b28")             # cruz
fm.caja(sm - 0.3, sm + 0.3, cima + 0.45, cima + 0.55, 0.0, 0.1, "hierro", "#2f2b28")
# el MURAL (fotos 130221–130228): paisaje de montes bajo un cielo claro y una figura con poncho rojo. Capas
# escalonadas 1 cm hacia afuera para que ninguna cara quede coplanar con otra (sin parpadeo).
mw, m0, m1 = min(7.0, Lm - 1.0), 1.4 + offm, 7.4 + offm
x0m, x1m = sm - mw / 2, sm + mw / 2
fm.caja(x0m - 0.12, x1m + 0.12, m0 - 0.12, m1 + 0.12, 0.0, 0.02, "moldura", "#e9e4da")
capas = [  # (s0, s1, h0, h1, color) en fracción del mural, de atrás hacia adelante
    (0.0, 1.0, 0.0, 1.0, "#9cc6dc"),      # cielo
    (0.0, 1.0, 0.72, 1.0, "#c6dfe8"),     # cielo claro arriba
    (0.0, 0.55, 0.30, 0.62, "#6d8fae"),   # cerros lejanos
    (0.40, 1.0, 0.28, 0.55, "#7a9bb5"),
    (0.0, 1.0, 0.0, 0.36, "#4f8a62"),     # monte verde
    (0.0, 0.35, 0.0, 0.48, "#3d6b45"),
    (0.70, 1.0, 0.0, 0.44, "#5c9a5a"),
    (0.0, 1.0, 0.0, 0.12, "#8a6a3e"),     # tierra
    (0.38, 0.62, 0.0, 0.62, "#b23a3a"),   # poncho
    (0.43, 0.57, 0.36, 0.50, "#d65a3a"),
    (0.45, 0.55, 0.62, 0.76, "#d6a985"),  # rostro
    (0.44, 0.56, 0.76, 0.84, "#2b2522"),  # cabello
    (0.82, 0.92, 0.70, 0.86, "#e9d36a"),  # sol
]
for k_, (a_, b_, h0_, h1_, col_) in enumerate(capas):
    d0_ = 0.02 + 0.01 * k_
    fm.caja(x0m + mw * a_, x0m + mw * b_, m0 + (m1 - m0) * h0_, m0 + (m1 - m0) * h1_, d0_, d0_ + 0.01, "letrero", col_)
# entrada peatonal al mercado junto al muro, con el letrero rojo
c.objeto(col)

# la placita de la esquina
c = Constructor("M013_placita_mercado")
zs_ = [altura_suelo(*p) for p in (CQ, W1, W2)]
zp = max(zs_) + 0.3
c.prisma([CQ, W1, W2], min(zs_) - 0.5, zp, "piedra", "#c9bca6", tapa=False)
c.tapa([CQ, W1, W2], zp, "adoquin", "#c8b8a4")
for a_, b_ in ((CQ, W1), (CQ, W2)):           # bordillo pintado de amarillo
    L_ = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
    ux_, uy_ = (b_[0] - a_[0]) / L_, (b_[1] - a_[1]) / L_
    c.caja_ejes(((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2, zp - 0.12), (ux_, uy_, 0), (-uy_, ux_, 0), (0, 0, 1),
                L_, 0.18, 0.3, "pintura_acento", "#e3b52f")
gx = (CQ[0] + W1[0] + W2[0]) / 3
gy = (CQ[1] + W1[1] + W2[1]) / 3
c.cilindro(gx, gy, zp - 0.05, zp + 0.45, 1.1, "piedra", "#b8afa3", lados=12)       # cantero redondo con asiento
c.cilindro(gx, gy, zp + 0.45, zp + 0.5, 0.95, "cesped", lados=12)
# la copa se corre hacia la esquina: centrada se metía en el muro del mural (calidad: SIAMESES)
arbol_paraguas(c, gx, gy, zp + 0.5, alto=6.0, copa=4.6, semilla=226, alcorque=False,
               desplazar=((CQ[0] - gx) * 0.6, (CQ[1] - gy) * 0.6))
ang = math.atan2(W2[1] - W1[1], W2[0] - W1[0])
for t in (0.25, 0.75):
    bx_ = W1[0] + (W2[0] - W1[0]) * t - bq[0] * 1.3
    by_ = W1[1] + (W2[1] - W1[1]) * t - bq[1] * 1.3
    banco(c, bx_, by_, zp, ang + math.pi)
fx_, fy_ = W1[0] + (W2[0] - W1[0]) * 0.5 - bq[0] * 2.8, W1[1] + (W2[1] - W1[1]) * 0.5 - bq[1] * 2.8
farol_cc0(c, fx_, fy_, zp, ang=ang)
c.objeto(col)
c = Constructor("E757802")
h = E["E757802"]["huella"]
zb, zt2 = suelo_huella(h)
c.prisma(h, zb - 0.6, zt2 + 8.0, "muro", "#f1ece3", tapa=False)
techo_auto(c, h, zt2 + 8.01, plantas=False)   # el claustro lleva su jardín propio
# claustro del convento (vista aérea 2026-11-13: el patio era un piso de tierra de 1 000 m²): cuatro cuarteles de
# césped con senderos en cruz, fuente de piedra en el centro, naranjos/arbolitos y bordillo de piedra
cl, eje_c = _rect_interior([tuple(p) for p in h], 9.0)
if cl:
    from piezas_claude import arbol
    ux_, uy_ = eje_c
    vx_, vy_ = -uy_, ux_
    cxc = sum(p[0] for p in cl) / 4
    cyc = sum(p[1] for p in cl) / 4
    hu = max(abs((p[0] - cxc) * ux_ + (p[1] - cyc) * uy_) for p in cl)
    hv = max(abs((p[0] - cxc) * vx_ + (p[1] - cyc) * vy_) for p in cl)
    Q = lambda a_, b_: (cxc + ux_ * a_ + vx_ * b_, cyc + uy_ * a_ + vy_ * b_)
    zc0 = altura_suelo(cxc, cyc) + 0.06
    rnd_c = _rt.Random("claustro")
    for su in (-1, 1):
        for sv in (-1, 1):
            a0, a1 = sorted((su * 1.1, su * hu))
            b0, b1 = sorted((sv * 1.1, sv * hv))
            cuartel = [Q(a0, b0), Q(a1, b0), Q(a1, b1), Q(a0, b1)]
            c.prisma(cuartel, zc0 - 0.2, zc0 + 0.18, "piedra", "#b9aa96")                  # bordillo
            ins = [Q(a0 + 0.2, b0 + 0.2), Q(a1 - 0.2, b0 + 0.2), Q(a1 - 0.2, b1 - 0.2), Q(a0 + 0.2, b1 - 0.2)]
            c.tapa(ins, zc0 + 0.2, "cesped", "#6f9a45")
            x_, y_ = Q((a0 + a1) / 2, (b0 + b1) / 2)
            arbol(c, x_, y_, zc0 + 0.2, alto=rnd_c.uniform(4.0, 5.5), copa=rnd_c.uniform(1.8, 2.4),
                  semilla=rnd_c.randint(0, 999))
    c.prisma([Q(-hu, -hv), Q(hu, -hv), Q(hu, hv), Q(-hu, hv)], zc0 - 0.3, zc0 + 0.02, "adoquin", "#cdb79c")  # senderos
    x_, y_ = Q(0, 0)
    c.cilindro(x_, y_, zc0, zc0 + 0.55, 1.3, "piedra", "#c9bba5", lados=16)               # fuente
    c.cilindro(x_, y_, zc0 + 0.4, zc0 + 0.5, 1.1, "agua", "#6d9fb5", lados=16)
    c.cilindro(x_, y_, zc0 + 0.55, zc0 + 1.5, 0.18, "piedra", "#c9bba5", lados=8)
    c.cilindro(x_, y_, zc0 + 1.5, zc0 + 1.65, 0.5, "piedra", "#c9bba5", lados=12)
c.objeto(col)

from detalles_claude import detallar, relleno_manzana, techos_con_patio  # noqa: E402
relleno_manzana(col, m)
techos_con_patio(col, excluir=())
detallar(col, m)
exportar(AGENTE, MANZANA)


def frontal(nombre, t, dist=10.0, alto_mira=6.0, prof=0.0):
    p = P(t, prof)
    z = altura_suelo(*p)
    return (nombre, (p[0] + N[0] * dist, p[1] + N[1] * dist, z + 1.7), (p[0], p[1], z + alto_mira))


import json as _json  # noqa: E402
_R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "coordinacion", "revisiones")
CAMS_R = []
for rid in ("R0039", "R0040", "R0041", "R0042", "R0043", "R0044", "R0045", "R0046", "R0047", "R0048", "R0049", "R0050", "R0051"):
    e_ = _json.load(open(os.path.join(_R, rid, "revision.json")))["escena"]
    o_, m_ = e_["camara"]["lienzo"], e_["centro"] or e_["camara"]["lienzo"]
    CAMS_R.append((rid, (o_["x"], o_["y"], o_["z"]), (m_["x"], m_["y"], m_["z"])))
solo = [a for a in sys.argv if a.startswith("--r=")]
revisar(AGENTE, MANZANA, fotos=[] if "--todas" not in sys.argv else None,
        camaras_extra=CAMS_R + [frontal("san_francisco", 52.0, 9.0, 9.0), frontal("museo_portal", 27.0, 6.5),
                                ("mercado_esquina", (CQ[0] - bq[0] * 16, CQ[1] - bq[1] * 16, altura_suelo(*CQ) + 1.7),
                                 (W1[0] / 2 + W2[0] / 2, W1[1] / 2 + W2[1] / 2, altura_suelo(*CQ) + 5.0))])
