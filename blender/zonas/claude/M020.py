"""M020 — esquina Calle Capitán Agustín Ravelo × Calle Batalla de Junín (lado SO de Ravelo).

Fotos (ficha): #1 125818, #2 125821 (casa esquina); #3–#8 125825…125842 (casa blanca y vista de la calle).
Las #9–#13 (125849…125909) muestran Farmacia La Plata y la CNS: están en el hueco del lienzo entre M020 y
M030 → se usan al modelar M030. #14 (130234) mira hacia M009 (Chocolatería Taboada).

Las huellas del lienzo no siguen los límites reales de las casas. Sobre Ravelo hay dos casas:

CASA ESQUINA (obj E238eeb = huella E238eeb + parte NO de Ef32a68), fotos #1 #2
  - frente a Ravelo ~16.8 m (4 crujías de ~4.2 m) + vuelta a Junín (lado 1 de E238eeb, 10.4 m, sin foto: igual)
  - planta baja: toda de sillería de arenisca (#c9a27e) hasta 5.0 m, con banda de piedra; un portón bajo cada
    ventana (Kodak en la esquina, Aleydi, tienda, puerta)
  - planta alta: muro crema #f1e6cf; 4 ventanas en arco (1.2 × 2.6 m + arco) con archivolta ocre #e3c27a,
    clave y balcón de hierro sobre losa de piedra; pilastras ocres con capitel entre crujías y en la esquina
  - entablamento: friso + cornisa ocre con dentículos (9.6–10.6 m)
  - pretil de 1.1 m con medallones redondos y pedestales con bola sobre cada pilastra
CASA BLANCA (obj Ef32a68 = parte SE de Ef32a68, s 0–16 del lado 5), fotos #2 #6 #7 #8
  - muro blanco #f3f1ec; molduras gris azulado #c6d0da (marcos de ventana y fajas verticales)
  - zócalo de piedra 1.8 m; planta baja con portones y vanos de tienda
  - planta alta: 4 ventanas en arco con balcón de hierro
  - cornisa sencilla + pretil con jarrones de terracota (#7)
Interior (E79c305, E4bccaf, Eaa8541, E943591): sin foto; volúmenes con tejado de tejas a dos aguas.
E08268d (frente a Junín, lado 1): sin foto; casa colonial blanca sencilla de 2 pisos.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from piezas_claude import (techo_auto, portada, mensula, lado_lienzo, adelantada, fachada, lado_virtual, partir_huella, pilastra_capitel, pretil_medallones,  # noqa: E402
                           punto_en_lado, remate_jarron, envolvente, suelo_huella, tejado_dos_aguas, ventana_arco_archivolta)

AGENTE = "claude"
MANZANA = "M020"

m, col = iniciar(AGENTE, MANZANA)

# colores reales
CREMA = "#f1e6cf"
OCRE = "#e3c27a"
SILLAR = "#c9a27e"
BLANCO = "#f3f1ec"
GRIS_AZUL = "#c6d0da"
MADERA_OSC = "#4a2a1e"

E = {e["id"]: e for e in m["edificios"]}
l5 = lado_lienzo(E["Ef32a68"], 5)      # Ef32a68 sobre Ravelo (a=SE, b=NO)
le0 = lado_lienzo(E["E238eeb"], 0, real=True)     # E238eeb sobre Ravelo (b = esquina)
le1 = lado_lienzo(E["E238eeb"], 1, real=True)   # E238eeb sobre Junín (a = esquina)

S_CORTE = 15.97  # límite entre casa blanca y casa esquina, medido sobre el lado 5 desde 'a'
u5 = ((l5["b"][0] - l5["a"][0]) / l5["largo"], (l5["b"][1] - l5["a"][1]) / l5["largo"])
parte_blanca, parte_esquina = partir_huella(E["Ef32a68"]["huella"], l5["a"], u5, S_CORTE)

# =========================================================================== CASA ESQUINA
c = Constructor("E238eeb")
huellas_esq = [E["E238eeb"]["huella"], parte_esquina]
# ocupa E238eeb + la parte NO de Ef32a68: sin esto el recorte a medianeras le borraba la mitad del frente (R0131)
c.huella = envolvente(*huellas_esq)
zmin = min(suelo_huella(h)[0] for h in huellas_esq)
zref = max(suelo_huella(h)[1] for h in huellas_esq)  # suelo nominal: alturas de diseño se miden desde aquí
Z_TOP = zref + 10.6
for h in huellas_esq:
    c.prisma(h, zmin - 0.6, Z_TOP, "muro", CREMA, tapa=False)
    techo_auto(c, h, Z_TOP - 0.02)

esquina = le0["b"]
frente = lado_virtual(punto_en_lado(l5, S_CORTE), esquina, l5["normal"])  # Ravelo, de SE a la esquina
L = frente["largo"]


def crujias_esquina(f, desde_esquina, largo, ventanas_S, pilastras_S, portones):
    """Fachada de la casa esquina. Posiciones S medidas desde la esquina."""
    off = zref - f.suelo  # sube las alturas de diseño al suelo nominal
    S = (lambda x: largo - x) if desde_esquina == "b" else (lambda x: x)
    # planta baja de sillería hasta 5.0 m
    zocalo(f, 4.9 + off, color=SILLAR, desde=zmin - 0.6 - f.suelo)
    f.caja(-0.05, largo + 0.05, 4.9 + off, 5.15 + off, 0.0, 0.2, "piedra", SILLAR)
    fa = adelantada(f)
    for sw in portones:
        puerta(fa, S(sw), ancho=1.6, alto=3.3 + off, color=MADERA_OSC, moldura="piedra", color_moldura=SILLAR)
        portada(fa, S(sw), 1.6, 3.3, h0=off, rol="piedra", color="#d2ad86")
    # pilastras de sillería en la planta baja, bajo las de la planta alta (foto 125818)
    for sp in pilastras_S:
        f.caja(S(sp) - 0.3, S(sp) + 0.3, off - 0.3, 4.9 + off, 0.0, 0.1, "piedra", "#d2ad86")
    # ménsulas de piedra bajo las losas de los balcones
    for sv in ventanas_S:
        for dm in (-0.8, 0.8):
            mensula(f, S(sv) + dm, 5.35 + off, 0.55, "#d2ad86", rol="piedra")
    # planta alta
    for sp in pilastras_S:
        pilastra_capitel(f, S(sp), 5.15 + off, 9.6 + off, ancho=0.42, color=OCRE)
    for sv in ventanas_S:
        ventana_arco_archivolta(f, S(sv), 5.35 + off, 1.2, 2.5, archivolta=("pintura_acento", OCRE),
                                carpinteria=("marco_ventana", MADERA_OSC))
    # entablamento: friso, dentículos y cornisa
    imposta(f, 9.6 + off, alto=0.15, vuelo=0.12, rol="pintura_acento", color=OCRE)
    k = 0.15
    while k < largo - 0.1:
        f.caja(k, k + 0.12, 10.0 + off, 10.18 + off, 0.0, 0.16, "pintura_acento", OCRE)
        k += 0.26
    cornisa(f, 10.18 + off, vuelo=0.4, alto=0.42, rol="pintura_acento", color=OCRE)
    pretil_medallones(f, 10.6 + off, 0.0, largo, [S(p) for p in pilastras_S], muro=("muro", CREMA),
                      acento=("pintura_acento", OCRE))


# Ravelo: 4 crujías
f_rav = fachada(c, frente)
crujias_esquina(f_rav, "b", L, ventanas_S=[2.1, 6.3, 10.5, 14.7], pilastras_S=[0.3, 4.2, 8.4, 12.6, L - 0.3],
                portones=[2.1, 6.3, 10.5, 14.7])
# Junín: 2 crujías y media (sin foto de esta cara: se repite el orden de Ravelo)
f_jun = fachada(c, le1)
crujias_esquina(f_jun, "a", le1["largo"], ventanas_S=[2.1, 6.3], pilastras_S=[0.3, 4.2, 8.4, le1["largo"] - 0.3],
                portones=[2.1, 6.3])
c.objeto(col)

# =========================================================================== CASA BLANCA
c = Constructor("Ef32a68")
zmin_b, zref_b = suelo_huella(parte_blanca)
Z_TOP_B = zref_b + 9.5
c.prisma(parte_blanca, zmin_b - 0.6, Z_TOP_B, "muro", BLANCO, tapa=False)
techo_auto(c, parte_blanca, Z_TOP_B - 0.02)
lb = lado_virtual(l5["a"], punto_en_lado(l5, S_CORTE), l5["normal"])
f = fachada(c, lb)
off = zref_b - f.suelo
zocalo(f, 1.8 + off, color=SILLAR, desde=zmin_b - 0.6 - f.suelo)
xs = [2.0, 6.0, 10.0, 14.0]
for k, s in enumerate(xs):
    # planta baja: portón en arco, vano de tienda, portón, ventana con reja
    if k in (0, 2):
        puerta(adelantada(f), s, ancho=1.7, alto=3.4 + off, arco=(k == 2), color=MADERA_OSC, moldura="moldura", color_moldura=GRIS_AZUL)
    elif k == 1:
        puerta(adelantada(f), s, ancho=2.2, alto=3.0 + off, color="#3d4a5c", moldura="moldura", color_moldura=GRIS_AZUL,
               almohadillado=False)  # cortina de tienda (azul oscuro en #7)
    else:
        ventana(f, s, 2.0 + off, ancho=1.1, alto=1.8, reja=True, moldura="moldura", color_moldura=GRIS_AZUL,
                carpinteria="marco_ventana", color_carpinteria=MADERA_OSC)
    # planta alta: ventana en arco con balcón y marco gris azulado
    ventana(f, s, 5.2 + off, ancho=1.15, alto=2.4, arco=True, balcon="hierro", moldura="moldura",
            color_moldura=GRIS_AZUL, carpinteria="marco_ventana", color_carpinteria=MADERA_OSC)
for s in (0.25, 4.0, 8.0, 12.0, 15.75):  # fajas verticales
    pilastra(f, s, 1.8 + off, 8.6 + off, ancho=0.4, vuelo=0.05, rol="moldura", color=GRIS_AZUL, capitel=False)
imposta(f, 4.9 + off, alto=0.16, rol="moldura", color=GRIS_AZUL)
cornisa(f, 8.6 + off, vuelo=0.3, alto=0.4, rol="moldura", color=BLANCO)
parapeto(f, 9.0 + off, alto=0.5, rol="muro", color=BLANCO)
for s in (0.4, 8.0, 15.6):
    remate_jarron(f, s, 9.58 + off)
c.objeto(col)

# =========================================================================== E08268d (Junín, sin foto)
ob, _ = edificio_colonial("E08268d", E["E08268d"]["huella"], pisos=2, alto_piso=4.4, color_muro="#f4efe4",
                          zocalo_alto=1.4, remate="cornisa", coleccion=col)

# =========================================================================== interiores (sin foto)
for eid, alto in (("E79c305", 7.0), ("E4bccaf", 6.0), ("Eaa8541", 6.0), ("E943591", 5.5)):
    c = Constructor(eid)
    h = E[eid]["huella"]
    zb, zt = suelo_huella(h)
    c.prisma(h, zb - 0.6, zt + alto, "muro", "#efe8dc", tapa=True)
    tejado_dos_aguas(c, h, zt + alto, pendiente=24)
    c.objeto(col)


# =========================================================================== lote sobre Ravelo junto a E943591
# (sección Ravelo, R0128: "no hay ningún callejón en esta zona"): el frente SO de Ravelo seguía abierto 8 m en el
# quiebre de la calle (antes lo tapaba el relleno con un pasaje inventado). Se cierra con dos casas de la cuadra.
from piezas_claude import casas_de_frente, tramo_calle  # noqa: E402
casas_de_frente(col, "M020_ravelo_a", tramo_calle("Calle Capitán Agustín Ravelo", (-190.0, 47.0)), -1, [
    (7.8, 2, 4.2, "#f3f1ec", "cornisa", dict(vanos=[1.5, 3.9, 6.3], puertas=[3.9], balcones=[1.5, 6.3])),
], t0=51.6)
casas_de_frente(col, "M020_ravelo_b", tramo_calle("Calle Capitán Agustín Ravelo", (-150.0, 10.0)), -1, [
    (4.85, 2, 4.2, "#f1e6cf", "alero", dict(vanos=[1.3, 3.65], puertas=[1.3], balcones=[3.65])),
], t0=0.0)   # 4,85 m: con 5,6 la casa se metía 0,2–0,7 m en el arranque del CNS de M030 (SIAMESES con E530f95)

from detalles_claude import detallar, relleno_manzana, techos_con_patio  # noqa: E402
relleno_manzana(col, m)
techos_con_patio(col, excluir=())
detallar(col, m)
from vecinos_claude import preparar  # noqa: E402
preparar(None, MANZANA, vecinas=("M030",))   # recorte contra el muro del vecino (SIAMESES)
exportar(AGENTE, MANZANA)
FOTOS = ["IMG_20261105_125818.jpg", "IMG_20261105_125821.jpg", "IMG_20261105_125834.jpg", "IMG_20261105_125838.jpg"]
cx, cy = m["centro"]
cz = altura_suelo(cx, cy)
revisar(AGENTE, MANZANA, fotos=FOTOS if "--todas" not in sys.argv else None,
        camaras_extra=[("aerea_ne", (cx + 45, cy + 55, cz + 55), (cx, cy, cz)),
                       ("aerea_so", (cx - 50, cy - 45, cz + 50), (cx, cy, cz))])
