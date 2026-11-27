"""AMP_O — ampliación oeste: lado NO de la Calle Batalla de Junín, desde la esquina con Estudiantes (correcciones del
usuario R0026–R0033, 2026-11-12). Fuera de la zona original; reparto: espacio AMP_O, dueño claude.

Eje t a lo largo de la fachada sobre Junín, t = 0 en la esquina con Estudiantes, creciendo hacia el NE; 'prof' hacia
adentro (NO).

t 0–27   AIT (Autoridad de Impugnación Tributaria), fotos R0026–R0029: edificio blanco moderno de 4 plantas + ático,
         ventanas en bandas con marcos azul oscuro, galerías con balaustrada blanca en la parte izquierda, arcos en la
         última planta; terraza elevada al frente con ESCALINATA de ladrillo, canteros con palmera, buganvilla y
         arbustos; cuerpo vertical de vidrio oscuro (escalera) con el logo redondo arriba.
t 27–fin EDIFICIO COLONIAL LARGO, fotos R0029–R0033: blanco, 2 plantas, zócalo de piedra rojiza que se escalona con
         la pendiente, ventanas rectas con reja abajo y en arco rebajado arriba, imposta, alero de tejas con canes;
         puerta de hierro en arco (R0031) y PORTADA central (R0033): marco de piedra, puerta de hierro, losa y gran
         VITRAL encima entre pilastras; adorno de ladrillo a la izquierda de la portada; faroles de pared.
Resto (cuadra norte y casa sobre Estudiantes): versión sencilla.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from kit import arquitectura as A  # noqa: E402
from kit.datos import RAIZ, lados, recortar_a_calles  # noqa: E402
from base_plazas import palmera  # noqa: E402
from piezas_claude import (arbol, casa_sencilla, fachada, guardapolvo, lado_virtual, partir_huella,  # noqa: E402
                           suelo_huella, techo_auto)

AGENTE, MID = "claude", "AMP_O"
m, col = iniciar(AGENTE, MID)
P8, P1, P0 = m["huellas_lienzo"]
H8 = recortar_a_calles(P8)
BLANCO = "#f5f4ef"
AZUL = "#34435c"
LADRILLO = "#b5634a"
ZOC = "#a65a48"

# --- marco: línea real de fachadas del lado NO de Junín (eje de la calle corrido medio ancho), t desde el inicio del
# eje. Las huellas del lienzo aquí empiezan ~15 m después de la esquina real: se usan huellas propias recortadas.
from kit.datos import calles_reales  # noqa: E402
_cj = [cc for cc in calles_reales() if cc["nombre"] == "Calle Batalla de Junín" and abs(cc["eje"][0][0] + 370.49) < 2][0]
_a, _b = _cj["eje"][0], _cj["eje"][-1]
_Lj = math.hypot(_b[0] - _a[0], _b[1] - _a[1])
U = ((_b[0] - _a[0]) / _Lj, (_b[1] - _a[1]) / _Lj)
N = (U[1], -U[0])                      # normal hacia la calle desde el lado NO (el NO queda a la izquierda de U)
if N[0] * (-0.77) + N[1] * 0.64 > 0:  # N debe apuntar al SE (hacia el eje), no al NO
    N = (-N[0], -N[1])
IN = (-N[0], -N[1])
A0 = (_a[0] + IN[0] * _cj["ancho"] / 2, _a[1] + IN[1] * _cj["ancho"] / 2)
LARGO = 84.0


def P(t, prof=0.0):
    return (A0[0] + U[0] * t + IN[0] * prof, A0[1] + U[1] * t + IN[1] * prof)


def rect(t0, t1, p0, p1):
    return [P(t0, p0), P(t1, p0), P(t1, p1), P(t0, p1)]


def lado_frente(h):
    """Lado de la huella recortada que da a Junín, orientado con t creciente."""
    cand = [l for l in lados(h) if l["normal"][0] * N[0] + l["normal"][1] * N[1] > 0.9 and l["largo"] > 2]
    l = max(cand, key=lambda l: l["largo"])
    if (l["b"][0] - l["a"][0]) * U[0] + (l["b"][1] - l["a"][1]) * U[1] < 0:
        l = lado_virtual(l["b"], l["a"], N)
    return l


def frente(t0, t1, prof=0.0):
    return lado_virtual(P(t0, prof), P(t1, prof), N)


T_INI, T_AIT = -6.0, 31.0
# termina donde empieza la M027 de codex (su mensaje: Eaeb297 arranca en (-326.907, -63.302))
_lim = (-326.907, -63.302)
T_FIN = (_lim[0] - A0[0]) * U[0] + (_lim[1] - A0[1]) * U[1] - 0.2
ait_parte = recortar_a_calles(rect(T_INI, T_AIT, 0.0, 22.0))
colonial_parte = recortar_a_calles(rect(T_AIT, T_FIN, 0.0, 22.0))
T0_REAL = min((x - A0[0]) * U[0] + (y - A0[1]) * U[1] for x, y in ait_parte)
print(f"[AMP_O] la AIT empieza en t = {T0_REAL:.1f} (esquina con Estudiantes); el colonial termina en t = {T_FIN:.1f}")

# =========================================================================== AIT
c = Constructor("AMP_O_AIT")
TERR = 1.8                       # terraza elevada sobre la vereda
FR = 4.5                         # el edificio retrocede: terraza al frente
cuerpo = partir_huella(ait_parte, A0, IN, FR)[1]
fondo_ait = None
zb, zr = suelo_huella(cuerpo)
ALTO_AIT = 3.4 * 4
c.prisma(cuerpo, zb - 0.6, zr + TERR + ALTO_AIT, "muro", BLANCO, tapa=True)
# ático retirado con galería en arcos
atico = recortar_a_calles(rect(T0_REAL + 1.5, T_AIT - 6.0, FR + 1.5, FR + 14.0)) or rect(T0_REAL + 1.5, T_AIT - 6.0, FR + 1.5, FR + 14.0)
c.prisma(atico, zr + TERR + ALTO_AIT, zr + TERR + ALTO_AIT + 3.0, "muro", BLANCO, tapa=True)
f = fachada(c, frente(T0_REAL + 0.3, T_AIT - 5.5, FR))
off = zr + TERR - f.suelo
L = f.largo
for piso in range(4):
    h = piso * 3.4 + off
    n = max(3, round(L / 2.6))
    for k in range(n):
        s = L * (k + 0.5) / n
        if piso == 3:
            A.ventana(f, s, h + 0.7, ancho=1.2, alto=2.0, arco=True, moldura="moldura", color_moldura=BLANCO,
                      carpinteria="marco_ventana", color_carpinteria=AZUL)
        else:
            A.ventana(f, s, h + 0.8, ancho=1.3, alto=1.9, moldura="moldura", color_moldura=BLANCO,
                      carpinteria="marco_ventana", color_carpinteria=AZUL)
    if piso >= 1:   # losa de piso volada y galería con balaustrada en la mitad izquierda
        f.caja(-0.1, L + 0.1, h - 0.1, h + 0.12, 0.0, 0.35, "moldura", BLANCO)
        s0, s1 = 0.0, L * 0.55
        f.caja(s0, s1, h, h + 0.15, 0.0, 1.1, "piedra", BLANCO)
        k = s0 + 0.2
        while k < s1 - 0.1:
            f.cilindro_vertical(k, h + 0.15, h + 0.9, 1.0, 0.06, "moldura", BLANCO, lados=6)
            k += 0.26
        f.caja(s0, s1, h + 0.9, h + 1.02, 0.85, 1.12, "moldura", BLANCO)
A.cornisa(f, ALTO_AIT + off - 0.3, vuelo=0.35, alto=0.3, rol="moldura", color=BLANCO)
# balaustrada del ático
fa = fachada(c, frente(T0_REAL + 1.5, T_AIT - 6.0, FR + 1.5))
for k in range(int(fa.largo / 3.0)):
    s = 1.5 + k * 3.0
    fa.arco(s, 1.0, 0.25, ALTO_AIT + off + 0.0 + 0.6, 0.0, 0.1, "moldura", BLANCO, segmentos=8)
k = 0.2
while k < fa.largo:
    fa.cilindro_vertical(k, ALTO_AIT + off, ALTO_AIT + off + 0.85, 0.15, 0.06, "moldura", BLANCO, lados=6)
    k += 0.26
fa.caja(0.0, fa.largo, ALTO_AIT + off + 0.85, ALTO_AIT + off + 0.97, 0.0, 0.3, "moldura", BLANCO)
# fachada lateral hacia Estudiantes (la esquina)
for l in lados(cuerpo):
    if l["normal"][0] * N[0] + l["normal"][1] * N[1] < 0.5 and l["normal"][0] * IN[0] + l["normal"][1] * IN[1] < 0.5 \
            and l["largo"] > 5 and l["a_calle"]:
        fl = fachada(c, l)
        offl = zr + TERR - fl.suelo
        for piso in range(4):
            n = max(2, round(l["largo"] / 2.8))
            for k in range(n):
                A.ventana(fl, l["largo"] * (k + 0.5) / n, piso * 3.4 + offl + 0.8, ancho=1.2, alto=1.8,
                          moldura="moldura", color_moldura=BLANCO, carpinteria="marco_ventana", color_carpinteria=AZUL)
        A.zocalo(fl, offl + 0.2, color=LADRILLO, desde=zb - 0.6 - fl.suelo)
# cuerpo de vidrio (escalera) con el logo
vid = recortar_a_calles(rect(T_AIT - 5.5, T_AIT - 0.3, FR - 0.6, FR + 7.0)) or rect(T_AIT - 5.5, T_AIT - 0.3, FR - 0.6, FR + 7.0)
c.prisma(vid, zb - 0.6, zr + TERR + ALTO_AIT + 2.6, "vidrio", "#2c3a4a", tapa=True)
fv = fachada(c, frente(T_AIT - 5.5, T_AIT - 0.3, FR - 0.6))
offv = zr + TERR - fv.suelo
for k in range(6):
    fv.caja(fv.largo * k / 5 - 0.06, fv.largo * k / 5 + 0.06, -0.5, ALTO_AIT + offv + 2.6, 0.0, 0.08, "metal", "#9aa2a8")
for k in range(10):
    fv.caja(0.0, fv.largo, offv + k * 1.7, offv + k * 1.7 + 0.08, 0.0, 0.08, "metal", "#9aa2a8")
fv.caja(0.0, fv.largo, ALTO_AIT + offv + 2.6, ALTO_AIT + offv + 3.0, -0.1, 0.25, "moldura", BLANCO)
q = fv.punto(fv.largo / 2, ALTO_AIT + offv - 0.5, 0.12)
c.caja_ejes((q.x, q.y, q.z), (U[0], U[1], 0), (N[0], N[1], 0), (0, 0, 1), 1.8, 0.08, 1.8, "letrero", "#efe2c4")  # logo
# terraza al frente con escalinata de ladrillo, canteros y vegetación
ft_lado = frente(T0_REAL + 0.2, T_AIT - 5.5, 0.0)
E0, E1 = 12.0, 18.5                                  # escalinata (s sobre el frente de la terraza)
PE = 2.8                                             # la escalinata entra 2,8 m en la terraza
tA = T0_REAL + 0.2
for (t0_, t1_, p0_) in ((tA, tA + E0 - 0.3, 0.0), (tA + E0 - 0.3, tA + E1 + 0.3, PE), (tA + E1 + 0.3, T_AIT - 5.5, 0.0)):
    tr = recortar_a_calles(rect(t0_, t1_, p0_, FR)) or rect(t0_, t1_, p0_, FR)
    zb3, zr3 = suelo_huella(tr)
    c.prisma(tr, zb3 - 0.6, zr + TERR, "zocalo_piedra", LADRILLO, tapa=False)
    c.tapa(tr, zr + TERR, "adoquin", "#c9a089")
ft = fachada(c, ft_lado)
import random as _r  # noqa: E402
from adornos_claude import planta  # noqa: E402
rnd_p = _r.Random("canteros-ait")
offt = zr - ft.suelo
for k in range(9):                                   # escalones de ladrillo, subiendo hacia adentro
    h = offt + TERR * (k + 1) / 9
    ft.caja(E0, E1, -0.6, h, -PE * (k + 1) / 9 - 0.02, -PE * k / 9, "zocalo_piedra", LADRILLO)
for sb in (E0 - 0.15, E1 + 0.15):                    # muretes laterales de la escalinata
    ft.caja(sb - 0.15, sb + 0.15, -0.6, offt + TERR + 0.9, -PE, 0.0, "zocalo_piedra", LADRILLO)
for (s0, s1) in ((0.6, E0 - 0.6), (E1 + 0.6, ft.largo - 0.4)):   # canteros con plantas, sobre la terraza
    ft.caja(s0, s1, offt + TERR, offt + TERR + 0.6, -1.5, -0.25, "zocalo_piedra", LADRILLO)
    ft.caja(s0 + 0.1, s1 - 0.1, offt + TERR + 0.55, offt + TERR + 0.62, -1.4, -0.35, "cesped")
    kk = s0 + 0.7                                      # buganvillas, arbustos floridos y plantas (Quaternius, CC0)
    while kk < s1 - 0.5:
        q = ft.punto(kk, offt + TERR + 0.62, -0.85)
        planta(c, rnd_p.choice(["Bush_Common_Flowers", "Flower_4_Group", "Plant_1_Big", "Flower_3_Group"]), q.x, q.y, q.z,
               ang=rnd_p.uniform(0, 6.28), escala=rnd_p.uniform(0.4, 0.55), semilla=int(kk * 10))
        kk += 1.3
k = 0.3                                               # baranda blanca de la terraza
while k < ft.largo - 0.2:
    if not (E0 - 0.3 < k < E1 + 0.3):
        ft.cilindro_vertical(k, offt + TERR, offt + TERR + 1.0, -0.1, 0.03, "metal", "#e8e8e4", lados=4)
    k += 0.5
ft.caja(0.3, E0 - 0.3, offt + TERR + 0.95, offt + TERR + 1.02, -0.15, -0.05, "metal", "#e8e8e4")
ft.caja(E1 + 0.3, ft.largo - 0.2, offt + TERR + 0.95, offt + TERR + 1.02, -0.15, -0.05, "metal", "#e8e8e4")
import random  # noqa: E402
rnd = random.Random("ait")
for t in (T0_REAL + 3.0, T0_REAL + 7.0, T0_REAL + 21.0):
    x, y = P(t, FR - 2.0)
    palmera(c, x, y, zr + TERR, 7.5 if t != T0_REAL + 7.0 else 5.5, rnd)
x, y = P(T0_REAL + 22.0, 2.2)
arbol(c, x, y, zr + TERR, alto=4.2, copa=3.2, semilla=7)   # buganvilla/arbusto grande
c.objeto(col)

# fondo de la AIT y del colonial: cuerpos bajos con patio
for nombre, h in (("AMP_O_fondo_ait", fondo_ait),):
    if h and len(h) >= 3:
        cc = Constructor(nombre)
        zb2, zr2 = suelo_huella(h)
        cc.prisma(h, zb2 - 0.6, zr2 + 7.5, "muro", "#f1ede4", tapa=False)
        techo_auto(cc, h, zr2 + 7.5, zpatio=zb2)
        cc.objeto(col)

# =========================================================================== EDIFICIO COLONIAL LARGO
c = Constructor("AMP_O_colonial")
frente_col = colonial_parte
fondo_col = None
zb, zr = suelo_huella(frente_col)
ALTO = 9.2
c.prisma(frente_col, zb - 0.6, zr + ALTO, "muro", BLANCO, tapa=False)
techo_auto(c, frente_col, zr + ALTO - 0.02, zpatio=zb)
f = fachada(c, lado_frente(frente_col))
T_C0 = (f.a.x - A0[0]) * U[0] + (f.a.y - A0[1]) * U[1]
off = zr - f.suelo
L = f.largo
PORTAL = 67.5 - T_C0
PUERTA = 54.0 - T_C0
# zócalo de piedra rojiza que se escalona con la pendiente (tramos de 6 m)
s = 0.0
while s < L:
    s1 = min(L, s + 6.0)
    zl = altura_suelo(*P(T_C0 + (s + s1) / 2)) - f.suelo
    f.caja(s, s1, -0.8, zl + 1.3, 0.0, 0.1, "zocalo_piedra", ZOC)
    s = s1
vanos = []
k = 1.8
while k < L - 1.0:
    if abs(k - PORTAL) > 3.0:
        vanos.append(k)
    k += 3.5
for s in vanos:
    zl = altura_suelo(*P(T_C0 + s)) - f.suelo
    if abs(s - PUERTA) < 1.75:   # puerta de hierro en arco
        A.puerta(f, s, ancho=1.4, alto=2.9 + zl, arco=True, rol="hierro", color="#2f2b28", moldura="moldura",
                 color_moldura=BLANCO, almohadillado=False)
        A._barrotes(f, s - 0.6, s + 0.6, zl + 0.2, zl + 3.4, 0.06, 0.12)
    else:
        A.ventana(f, s, zl + 1.6, ancho=1.1, alto=2.0, reja=True, moldura="moldura", color_moldura=BLANCO,
                  carpinteria="marco_ventana", color_carpinteria="#3a2a22")
    # planta alta: ventana en arco rebajado con postigos
    A.ventana(f, s, 5.5 + off, ancho=1.05, alto=1.75, moldura="moldura", color_moldura=BLANCO,
              carpinteria="marco_ventana", color_carpinteria="#3a2a22")
    f.arco(s, 0.62, 0.16, 5.5 + off + 1.75 - 0.25, 0.0, 0.08, "moldura", BLANCO, segmentos=6)
A.imposta(f, 4.7 + off, alto=0.22, vuelo=0.12, rol="moldura", color=BLANCO)
A.alero_tejas(f, ALTO + off - 0.05, vuelo=0.95)
# portada con vitral (R0033)
pp = PORTAL
f.caja(pp - 2.6, pp + 2.6, -0.6, ALTO + off - 0.2, 0.0, 0.18, "muro", BLANCO)            # cuerpo central adelantado
for ds in (-2.45, 2.45):
    A.pilastra(f, pp + ds, 0.0, ALTO + off - 0.4, ancho=0.45, vuelo=0.28, rol="moldura", color=BLANCO)
A.puerta(f, pp, ancho=2.2, alto=3.6 + off, arco=False, rol="hierro", color="#2b2522", moldura="piedra",
         color_moldura="#ece4d4", almohadillado=False)
A._barrotes(f, pp - 1.05, pp + 1.05, off + 0.3, off + 3.5, 0.22, 0.14)
f.caja(pp - 2.0, pp + 2.0, 4.2 + off, 4.45 + off, 0.0, 0.75, "piedra", "#ece4d4")         # losa / cornisa
# vitral: marco de piedra y paños de colores
f.caja(pp - 1.75, pp + 1.75, 4.9 + off, 8.2 + off, 0.18, 0.26, "moldura", "#ece4d4")
cols = ["#7a2f3a", "#2f4f7a", "#c9a24a", "#3f6b4a", "#8a5a9a", "#b6463a"]
for i in range(6):
    for j in range(5):
        s0 = pp - 1.55 + i * 0.52
        h0 = 5.05 + off + j * 0.6
        f.caja(s0 + 0.03, s0 + 0.49, h0 + 0.03, h0 + 0.57, 0.26, 0.27, "vidrio", cols[(i * 2 + j * 3) % 6])
for i in range(7):
    f.caja(pp - 1.55 + i * 0.52 - 0.02, pp - 1.55 + i * 0.52 + 0.02, 5.05 + off, 8.05 + off, 0.26, 0.29, "hierro")
# adorno de ladrillo a la izquierda de la portada (R0033)
f.caja(pp - 5.2, pp - 3.6, 2.0 + off, 2.35 + off, 0.0, 0.06, "zocalo_piedra", LADRILLO)
f.caja(pp - 4.8, pp - 4.0, 2.35 + off, 2.7 + off, 0.0, 0.06, "zocalo_piedra", LADRILLO)
# faroles de pared
for s in (PUERTA + 4.0, PORTAL - 4.2, 8.0):
    q = f.punto(s, 5.0 + off, 0.0)
    f.caja(s - 0.03, s + 0.03, 5.6 + off, 5.65 + off, 0.0, 0.55, "hierro")
    p2 = f.punto(s, 0, 0.55)
    zf = f.suelo + 5.3 + off
    c.cilindro(p2.x, p2.y, zf - 0.35, zf + 0.1, 0.13, "vidrio", "#efe2b5", lados=6, radio_arriba=0.17)
    c.cilindro(p2.x, p2.y, zf + 0.1, zf + 0.28, 0.22, "hierro", lados=6, radio_arriba=0.03)
c.objeto(col)
if fondo_col and len(fondo_col) >= 3:
    cc = Constructor("AMP_O_fondo_colonial")
    zb2, zr2 = suelo_huella(fondo_col)
    cc.prisma(fondo_col, zb2 - 0.6, zr2 + 7.0, "muro", "#f1ede4", tapa=False)
    techo_auto(cc, fondo_col, zr2 + 7.0, zpatio=zb2)
    cc.objeto(col)

# =========================================================================== interior y vecinos sin foto
from kit.datos import _cortar_semiplano  # noqa: E402
interior = partir_huella(H8, A0, IN, 22.5)[1] if H8 else None
if interior and len(interior) >= 3:
    cc = Constructor("AMP_O_interior")
    zb2, zr2 = suelo_huella(interior)
    cc.prisma(interior, zb2 - 0.6, zr2 + 7.0, "muro", "#f1ede4", tapa=False)
    techo_auto(cc, interior, zr2 + 7.0, zpatio=zb2)
    cc.objeto(col)
# la casa sobre Estudiantes no puede invadir la esquina de la AIT
P0 = _cortar_semiplano([tuple(p) for p in P0], A0[0], A0[1], -U[0], -U[1], -(T0_REAL - 0.3))
# (la cuadra norte P1 cae en la M027 de codex: no se modela aquí)
for nombre, Pn in (("AMP_O_estudiantes", P0),):
    h = recortar_a_calles(Pn) if len(Pn) >= 3 else None
    if not h:
        continue
    cc = Constructor(nombre)
    zb2, zr2 = suelo_huella(h)
    cc.prisma(h, zb2 - 0.6, zr2 + 8.6, "muro", "#f3eee4", tapa=False)
    techo_auto(cc, h, zr2 + 8.58, zpatio=zb2)
    for l in lados(h):
        if l["a_calle"] and l["largo"] >= 4:
            fl = fachada(cc, l)
            n = max(1, round(l["largo"] / 3.6))
            v = [l["largo"] * (k + 0.5) / n for k in range(n)]
            casa_sencilla(fl, 0.0, l["largo"], 2, 4.3, zr2 - fl.suelo, muro=("muro", "#f3eee4"), zocalo_alto=1.1,
                          zocalo_color=ZOC, vanos=v, balcones=v[1::2], puertas=v[::3], remate="alero",
                          desde=zb2 - 0.6 - fl.suelo)
    cc.objeto(col)

exportar(AGENTE, MID)

import json  # noqa: E402
CAMS = []
for i in range(26, 34):
    e = json.load(open(os.path.join(RAIZ, "coordinacion", "revisiones", f"R00{i}", "revision.json")))["escena"]
    o = e["camara"]["lienzo"]
    rb = math.radians(e["camara"]["rumbo_grados"])
    CAMS.append((f"R00{i}", (o["x"], o["y"], o["z"]), (o["x"] + math.sin(rb) * 15, o["y"] + math.cos(rb) * 15, o["z"] + 3.5)))
revisar(AGENTE, MID, fotos=[], camaras_extra=CAMS)
