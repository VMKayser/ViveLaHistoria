"""Manzanas SIN FOTO de claude: versión sencilla y coherente con las calles del centro.

Cada edificio: muro con el color de una paleta de fachadas típicas de Sucre (mayoría blancas), fachadas solo en los
lados que dan a la calle (casa_sencilla: zócalo, vanos, balcones, portones, cornisa o alero), techo de tejas a dos
aguas en los volúmenes chicos e interiores, azotea en los grandes. Todo es determinista (semilla = id del edificio):
volver a correr da el mismo resultado.

Uso desde un script de manzana:
    from generica import construir
    construir("claude", "M041")
"""

import hashlib
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Constructor, altura_suelo, exportar, iniciar, lados, revisar, techo_plano  # noqa: E402
from piezas_claude import (casa_sencilla, fachada, pilastra_capitel, suelo_huella, techo_colonial,  # noqa: E402
                           tejado_dos_aguas)
from adornos_claude import planta  # noqa: E402

FACHADAS = ["#f6f4ef", "#f6f4ef", "#f6f4ef", "#f4efe4", "#f3e6d3", "#f1e6cf", "#efe3c4", "#eef0f1"]
ZOCALOS = ["#b98e6e", "#c4a181", "#a6806a"]
CARPINTERIAS = ["#5a3422", "#6a3622", "#4a2a1e", "#3f4d3a"]
ACENTOS = ["#e7c46a", "#d4ab5c", "#b9c4cc", "#d98c6a", "#c0533a"]
# carácter de cada casa (afinado 2026-11-12: "falta detalle, relieves"): colonial con alero y canes, neoclásica con
# pilastras y guardapolvos, republicana con pretil y remates, con mirador de madera, o local comercial
TIPOS = ["colonial", "colonial", "neoclasica", "republicana", "mirador", "comercial"]


def rectangularidad(huella):
    """Área de la huella / área de su rectángulo orientado según el lado más largo (1 = rectángulo)."""
    import math
    pts = [tuple(p) for p in huella]
    a, b = max(zip(pts, pts[1:] + pts[:1]), key=lambda e: math.hypot(e[1][0] - e[0][0], e[1][1] - e[0][1]))
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    su = [p[0] * u[0] + p[1] * u[1] for p in pts]
    sv = [-p[0] * u[1] + p[1] * u[0] for p in pts]
    caja = (max(su) - min(su)) * (max(sv) - min(sv))
    area = abs(sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1]))) / 2
    return area / caja if caja else 0


_OTROS = []


def _dir_frente(a_calle):
    """Dirección del frente a la calle más largo: la cumbrera va paralela (el faldón cae a la calle)."""
    if not a_calle:
        return None
    l = max(a_calle, key=lambda x: x["largo"])
    return (l["b"][0] - l["a"][0], l["b"][1] - l["a"][1])


from kit.datos import _dentro  # noqa: E402


def _otros():
    if not _OTROS:
        from kit.datos import edificios_recortados
        _OTROS.extend(edificios_recortados())
    return _OTROS


def construir(agente, mid, revisar_render=True, extra=None, filtro_huella=None, camaras=(), forzar=None, vecinas=()):
    """extra(m, col): función opcional para agregar detalles vistos en alguna foto antes de exportar.
    filtro_huella(e) -> huella nueva o None: recorta o quita huellas del lienzo que reemplaza un script con foto.
    camaras: cámaras extra para revisar() (p. ej. las de las correcciones del usuario).
    vecinas: IDs de manzanas vecinas ya exportadas contra las que se recortan los tejados que se meten en ellas.
    forzar: {id_edificio: {"tipo": ..., "muro": ..., "pisos": ...}} para casas vistas en fotos."""
    forzar = forzar or {}
    m, col = iniciar(agente, mid)
    if filtro_huella:
        eds = []
        for e in m["edificios"]:
            h = filtro_huella(e)
            if h:
                e["huella"] = h
                eds.append(e)
        m["edificios"] = eds
    for e in m["edificios"]:
        rnd = random.Random(int(hashlib.md5(e["id"].encode()).hexdigest()[:8], 16))
        h = e["huella"]
        zb, zr = suelo_huella(h)
        a_calle = [l for l in lados(h) if l["a_calle"] and l["largo"] >= 4.0]
        area = e["area_m2"]
        if a_calle:
            pisos = 3 if (area > 500 and rnd.random() < 0.35) else 2
            alto_piso = rnd.choice([4.0, 4.2, 4.4])
        else:
            pisos, alto_piso = 1, (6.0 if area > 60 else 4.5)
        alto = pisos * alto_piso
        muro = rnd.choice(FACHADAS)
        fz = forzar.get(e["id"], {})
        muro = fz.get("muro", muro)
        if "pisos" in fz:
            pisos = fz["pisos"]
            alto = pisos * alto_piso
        c = Constructor(e["id"])
        c.prisma(h, zb - 0.6, zr + alto, "muro", muro, tapa=False)
        con_tejado = (area < 350 or not a_calle) and rectangularidad(h) > 0.85
        if con_tejado:
            c.tapa(h, zr + alto - 0.02, "muro", muro)
            tejado_dos_aguas(c, h, zr + alto, pendiente=rnd.choice([22, 25, 28]),
                             cumbrera=_dir_frente(a_calle))
        elif not techo_colonial(c, h, zr + alto, zb, pendiente=rnd.choice([22, 25]), muro=("muro", muro)):
            techo_plano(c, h, zr + alto - 0.02)
        tipo = fz.get("tipo", rnd.choice(TIPOS))
        if tipo == "colonial" and not con_tejado and "tipo" not in fz:
            tipo = "neoclasica"
        remate = {"colonial": "alero", "republicana": "pinaculos"}.get(tipo, "cornisa")
        acento = rnd.choice(ACENTOS)
        carp = rnd.choice(CARPINTERIAS)
        for l in a_calle:
            f = fachada(c, l)
            off = zr - f.suelo
            n = max(1, round(l["largo"] / rnd.uniform(3.4, 4.2)))
            vanos = [l["largo"] * (k + 0.5) / n for k in range(n)]
            puertas = [v for k, v in enumerate(vanos) if k % 3 == 1 or n == 1]
            balcones = [v for v in vanos if rnd.random() < (0.6 if tipo in ("neoclasica", "republicana") else 0.4)]
            miradores = [vanos[len(vanos) // 2]] if tipo == "mirador" and pisos > 1 and n >= 2 else []
            casa_sencilla(f, 0.0, l["largo"], pisos, alto_piso, off, muro=("muro", muro),
                          zocalo_alto=rnd.choice([0.8, 1.0, 1.3]), zocalo_color=rnd.choice(ZOCALOS), vanos=vanos,
                          balcones=balcones, puertas=puertas, miradores=miradores,
                          remate=remate if pisos > 1 or remate == "cornisa" else "cornisa", acento=acento,
                          carpinteria=("marco_ventana", carp), desde=zb - 0.6 - f.suelo,
                          comercio=(tipo == "comercial" or rnd.random() < 0.3))
            alto_f = pisos * alto_piso
            if tipo == "neoclasica" and l["largo"] > 5:
                # pilastras con capitel en los extremos y entre vanos alternos (color de acento o del muro)
                col_p = acento if muro in ("#f3e6d3", "#f1e6cf", "#efe3c4") else muro
                for k in range(n + 1):
                    if k in (0, n) or k % 2 == 0:
                        sp = 0.3 if k == 0 else (l["largo"] - 0.3 if k == n else l["largo"] * k / n)
                        pilastra_capitel(f, sp, 0.9 + off, alto_f - 0.4 + off, ancho=0.42, vuelo=0.08,
                                         rol="pintura_acento" if col_p == acento else "moldura", color=col_p)
            if tipo == "republicana" and pisos > 1:
                for k in range(n - 1):                       # medallones entre los vanos del piso alto
                    sm = (vanos[k] + vanos[k + 1]) / 2
                    f.arco(sm, 0.2, 0.08, alto_piso * 1.6 + off, 0.0, 0.06, "pintura_acento", acento, segmentos=8, medio=False)
        c.objeto(col)
    if extra:
        extra(m, col)
    from detalles_claude import detallar, relleno_manzana, techos_con_patio
    relleno_manzana(col, m)
    techos_con_patio(col)
    detallar(col, m)
    from vecinos_claude import preparar
    preparar(col, mid, vecinas)        # recorte contra el muro del vecino (control de calidad: SIAMESES)
    exportar(agente, mid)
    if revisar_render and "--sin-render" not in sys.argv:
        cx, cy = m["centro"]
        z = altura_suelo(cx, cy)
        revisar(agente, mid, fotos=[], camaras_extra=list(camaras) + [("aerea", (cx + 45, cy - 50, z + 50), (cx, cy, z))])
