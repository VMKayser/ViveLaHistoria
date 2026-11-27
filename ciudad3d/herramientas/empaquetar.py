#!/usr/bin/env python3
"""Empaquetador de la ciudad para Godot (web y app): lee DIRECTO lo que exportan los agentes, sin navegador ni Blender.

    python3 ciudad3d/herramientas/empaquetar.py          (incremental: solo relee las manzanas que cambiaron)
    python3 ciudad3d/herramientas/empaquetar.py --todo   (relee todo)

Entradas: web/public/models/ciudad/<agente>/manifiesto.json y sus GLB, web/public/mapa/raw/lienzo.glb (terreno y
volúmenes genéricos), web/public/mapa/huellas_manzanas.json, reparto/manzanas.json (zona de la BASE),
web/public/mapa/calles.json y web/public/models/fondo/cerros.json.

Reemplaza lo que hacía en el navegador el antiguo visor three.js (fusión de lotes, recorte del lienzo, cerros, faroles):
  - une la geometría por (tesela de 100 m, rol de material, origen) con el color del material en los vértices y el
    NÚMERO DE EDIFICIO (0–255, hash del objeto de Blender) en el canal alfa, para que el vidrio sea igual en todo un edificio;
  - oculta los volúmenes y árboles del lienzo que caen dentro de las huellas de lo modelado (y de toda la zona de la BASE),
    y los muros de volumen que corren pegados (< 30 cm) por fuera de una huella modelada (tapaban la fachada);
  - baja el terreno del lienzo 35 cm (el piso de la BASE va 7 cm encima y es plano entre muestras).

Salida en ciudad3d/datos/ (va dentro del APK y se copia a web/public/ciudad3d/datos/ para la web):
  ciudad.json   índice: roles, orígenes, lado, teselas {tx, tz, centro, radio, base/detalle/hojas: {archivo, origen, v}}, fondo
  t_<tx>_<tz>_b.bin / _d.bin / _h.bin   base (muros, techos, suelo, vegetación), detalle fino (rejas, carpinterías,
                flores) y racimos de hojas de las copas (solo de cerca)
  fondo.bin     cerros   ·   faroles.json   ·   calles.json   ·   pasto.json (dónde sembrar pasto y flores de cerca)
Formato de cada .bin: u32 tamaño sin comprimir + deflate de:
  u32 superficies; por superficie: u8 grupo (GRUPOS) · u8 clase de material (CLASES) · u8 origen · u8 0 · u32 vértices ·
  u32 índices; luego, por superficie: posiciones f32×3 (relativas al origen del archivo) · normales f32×3 · colores f32×4
  (RGB lineal + número de edificio / 255) · rol f32×2 (número de rol en ROLES; 1 si es la cara trasera de una copa, 0 si
  no; va al UV del vértice) · índices u32 (caras en el orden de Godot).
Las copas (roles de "doble_cara") no llevan un material de doble cara: van en la clase normal con sus caras duplicadas
(la copia, con la normal invertida y UV.y = 1). Así toda la ciudad usa un solo shader, que en WebGL se compila una sola
vez (cada shader distinto costaba ~4–5 s en la primera visita).
Una superficie junta todos los roles del mismo grupo, clase y origen: Godot la dibuja con un solo material que toma los
parámetros de cada rol de un arreglo (scripts/estilo.gd), así que una tesela son 1–4 llamadas de dibujo, no ≈20.
"""
import hashlib
import json
import os
import re
import sys
import time
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb  # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WEB = os.path.join(RAIZ, "web", "public")
SAL = os.path.join(RAIZ, "ciudad3d", "datos")
CACHE = os.path.join(RAIZ, "ciudad3d", ".cache")
AGENTES = ["claude", "codex"]
LADO = 100.0

ROLES = ["muro", "moldura", "pintura_acento", "zocalo_piedra", "piedra", "azotea", "teja", "madera", "marco_ventana",
         "vidrio", "hierro", "metal", "vereda", "calzada", "adoquin", "cesped", "follaje", "follaje_claro", "tronco",
         "flor", "agua", "letrero", "cerro", "hoja", "cantero"]
# origen de cada superficie: el taller puede ocultar un agente o los volúmenes genéricos del lienzo
ORIGENES = ["claude", "codex", "lienzo", "lienzo_volumen"]
DETALLE = {"hierro", "metal", "marco_ventana", "letrero", "flor"}       # de lejos no se dibujan
CERCA = {"hoja"}                    # solo de cerca (archivo _h aparte: se descarga a menos de ~170 m)
# grupos y clases de material (texturas/estilo.json, la misma tabla que usa Godot)
ESTILO = json.load(open(os.path.join(RAIZ, "ciudad3d", "texturas", "estilo.json")))
GRUPOS = ["suelo", "solido", "liviano"]           # suelo: sin sombra; liviano: no frena al caminante
CLASES = ["normal", "doble", "fondo", "hojas"]


def grupo_de(rol):
    return "suelo" if rol in ESTILO["suelo"] else ("liviano" if rol in ESTILO["sin_choque"] else "solido")


def clase_de(rol):
    if rol == "hoja":
        return "hojas"
    return "fondo" if rol == "cerro" else ("doble" if rol in ESTILO["doble_cara"] else "normal")
HUNDIMIENTO_TERRENO = 0.35


# ------------------------------------------------------------------------------------------------- utilidades
def lineal(hexa):
    """Color '#rrggbb' (sRGB) → lineal, como THREE.Color con la gestión de color activada."""
    c = np.array([int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def rol_de(nombre_material):
    rol = re.sub(r"\.\d+$", "", (nombre_material or "muro").split("__")[0])
    return rol if rol in ROLES else "muro"


def numero_edificio(texto):
    """FNV-1a de 32 bits módulo 256 (el mismo de FusionadorLotes.ts)."""
    h = 2166136261
    b = texto.encode("utf-16-le")
    for k in range(0, len(b), 2):              # unidades UTF-16, como charCodeAt
        h = ((h ^ (b[k] | b[k + 1] << 8)) * 16777619) & 0xFFFFFFFF
    return h % 256


def nombre_three(nombre):
    """PropertyBinding.sanitizeNodeName de three: espacios → _, sin [ ] . : /"""
    return re.sub(r"[\[\]\.:/]", "", re.sub(r"\s", "_", nombre))


# ------------------------------------------------------------------------------------------------- modelos de los agentes
def piezas_modelo(agente, ident, ruta):
    """{rol: (P, N, C(RGBA), I)} de un GLB, en coordenadas de mundo."""
    acc = {}
    for objeto, material, color, P, N, I in glb.leer(ruta):
        rol = rol_de(material)
        edif = numero_edificio(re.sub(r"_\d+$", "", f"{agente}/{ident}/{nombre_three(objeto)}"))
        C = np.empty((len(P), 4), np.float32)
        C[:, :3] = color
        C[:, 3] = edif / 255.0
        acc.setdefault(rol, []).append((P, N, C, I))
    return {rol: unir(lst) for rol, lst in acc.items()}


def unir(lst):
    """Une piezas (P, N, C, I) o (P, N, C, I, U); devuelve tantas columnas como traigan."""
    off = 0
    cols = [[] for _ in lst[0]]
    for pieza in lst:
        for j, x in enumerate(pieza):
            cols[j].append(x.astype(np.uint32) + off if j == 3 else x)
        off += len(pieza[0])
    return tuple(np.concatenate(c) for c in cols)


def cargar_modelos(todo):
    """Lee los manifiestos; usa la copia en caché de cada modelo si su marca 'actualizado' no cambió."""
    os.makedirs(CACHE, exist_ok=True)
    open(os.path.join(CACHE, ".gdignore"), "w").close()
    modelos = []
    leidos = 0
    for agente in AGENTES:
        ruta_man = os.path.join(WEB, "models", "ciudad", agente, "manifiesto.json")
        if not os.path.exists(ruta_man):
            continue
        for ident, e in json.load(open(ruta_man)).items():
            ruta = os.path.join(WEB, "models", "ciudad", agente, e["archivo"])
            if not os.path.exists(ruta):
                print(f"  falta {ruta}")
                continue
            marca = hashlib.sha1(f"{e['actualizado']}|{os.path.getsize(ruta)}|v2".encode()).hexdigest()[:12]
            cache = os.path.join(CACHE, f"{agente}__{ident}__{marca}.npz")
            if os.path.exists(cache) and not todo:
                z = np.load(cache)
                piezas = {r: (z[r + "|P"], z[r + "|N"], z[r + "|C"], z[r + "|I"]) for r in json.loads(str(z["roles"]))}
            else:
                for viejo in os.listdir(CACHE):
                    if viejo.startswith(f"{agente}__{ident}__"):
                        os.remove(os.path.join(CACHE, viejo))
                piezas = piezas_modelo(agente, ident, ruta)
                datos = {"roles": json.dumps(list(piezas))}
                for r, (P, N, C, I) in piezas.items():
                    datos.update({r + "|P": P, r + "|N": N, r + "|C": C, r + "|I": I})
                np.savez(cache, **datos)
                leidos += 1
            modelos.append((agente, ident, piezas))
    print(f"{len(modelos)} modelos ({leidos} releídos)")
    return modelos


# ------------------------------------------------------------------------------------------------- lienzo
def dentro(x, y, poli):
    """Punto en polígono (vectorizado sobre x, y)."""
    r = np.zeros(len(x), bool)
    pts = np.asarray(poli, np.float64)
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        cruza = (yi > y) != (yj > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            r ^= cruza & (x < xi + (y - yi) * (xj - xi) / (yj - yi))
        j = i
    return r


def pegado_al_borde(px, py, poli, tol):
    """True donde el punto (px, py) está a menos de 'tol' m de algún lado del polígono (vectorizado)."""
    q = np.asarray(poli, np.float64)
    a, b = q, np.roll(q, -1, axis=0)
    ab = b - a
    l2 = np.maximum((ab ** 2).sum(1), 1e-9)
    dx = px[:, None] - a[None, :, 0]
    dy = py[:, None] - a[None, :, 1]
    t = np.clip((dx * ab[None, :, 0] + dy * ab[None, :, 1]) / l2[None, :], 0, 1)
    ex = dx - t * ab[None, :, 0]
    ey = dy - t * ab[None, :, 1]
    return (ex ** 2 + ey ** 2).min(1) < tol * tol


def cargar_lienzo(modeladas):
    huellas = json.load(open(os.path.join(WEB, "mapa", "huellas_manzanas.json")))
    z = json.load(open(os.path.join(RAIZ, "reparto", "manzanas.json")))["zona"]
    zona = (z["xmin"], z["ymin"], z["xmax"], z["ymax"]) if "BASE" in modeladas else None
    polis = [p for ident in modeladas for p in huellas.get(ident, [])]
    piezas = {}   # (rol, origen) -> lista
    ocultos = 0
    for objeto, material, _, P, N, I in glb.leer(os.path.join(WEB, "mapa", "raw", "lienzo.glb")):
        nombre = objeto or material
        edificio = nombre.startswith("BUILDINGS")
        arbol = nombre == "TREES"
        if edificio:
            rol, color, origen = "muro", "#dfe3e8", "lienzo_volumen"
        elif nombre == "TERRAIN":
            rol, color, origen = "calzada", "#cbb48e", "lienzo"
        elif arbol:
            rol, color, origen = "follaje", "#5f7f3a", "lienzo"
        elif nombre == "WATER":
            rol, color, origen = "agua", "#9cc3ea", "lienzo"
        else:
            rol, color, origen = "piedra", "#c9bca6", "lienzo"
        P = P.copy()
        if nombre == "TERRAIN":
            P[:, 1] -= HUNDIMIENTO_TERRENO
        if edificio or arbol:
            c = (P[I[:, 0]] + P[I[:, 1]] + P[I[:, 2]]) / 3
            cx, cy = c[:, 0].astype(np.float64), -c[:, 2].astype(np.float64)
            tapa = np.zeros(len(I), bool)
            if zona:
                tapa |= (cx >= zona[0]) & (cx <= zona[2]) & (cy >= zona[1]) & (cy <= zona[3])
            for poli in polis:
                xs = [q[0] for q in poli]
                ys = [q[1] for q in poli]
                cerca = ~tapa & (cx >= min(xs) - 1) & (cx <= max(xs) + 1) & (cy >= min(ys) - 1) & (cy <= max(ys) + 1)
                if cerca.any():
                    k = np.flatnonzero(cerca)
                    tapa[k[dentro(cx[k], cy[k], poli)]] = True
                    if edificio:
                        # muro del volumen genérico que corre pegado a la fachada modelada (por fuera, unos cm): su centro
                        # cae en la calle y no lo quita la regla de arriba, pero tapa la fachada (franja que parpadea)
                        k = k[~tapa[k]]
                        if len(k):
                            pegado = np.ones(len(k), bool)
                            for v in range(3):
                                pv = P[I[k, v]]
                                pegado &= pegado_al_borde(pv[:, 0].astype(np.float64), -pv[:, 2].astype(np.float64), poli, 0.3)
                            tapa[k[pegado]] = True
            ocultos += int(tapa.sum())
            I = I[~tapa]
            if not len(I):
                continue
        C = np.empty((len(P), 4), np.float32)
        C[:, :3] = lineal(color)
        C[:, 3] = 0.0
        piezas.setdefault((rol, origen), []).append((P, N, C, I))
    print(f"lienzo: {ocultos} triángulos ocultos bajo lo modelado")
    return {k: unir(v) for k, v in piezas.items()}


# ------------------------------------------------------------------------------------------------- cerros del fondo
def cerros():
    d = json.load(open(os.path.join(WEB, "models", "fondo", "cerros.json")))
    n, paso, (ox, oy) = d["n"], d["paso"], d["origen"]
    z = np.array(d["z"], np.float64)
    jj, ii = np.mgrid[0:n, 0:n]
    x = ox + ii * paso
    y = oy + jj * paso
    P = np.stack([x, z, -y], -1).reshape(-1, 3)
    hx = z[:, np.minimum(n - 1, np.arange(n) + 1)] - z[:, np.maximum(0, np.arange(n) - 1)]
    hy = z[np.minimum(n - 1, np.arange(n) + 1), :] - z[np.maximum(0, np.arange(n) - 1), :]
    pend = np.hypot(hx, hy) / (2 * paso)

    def suave(v, a, b):
        t = np.clip((v - a) / (b - a), 0, 1)
        return t * t * (3 - 2 * t)

    bajo, medio, alto, roca, niebla = (lineal(c).astype(np.float64) for c in ("#b8a36a", "#8f9a5c", "#9a977f", "#a88f78", "#bcd3ea"))
    t = suave(z, -300, 500)[..., None]
    c = bajo + (medio - bajo) * np.minimum(1, t * 1.6)
    c = np.where(t > 0.6, c + (alto - c) * ((t - 0.6) / 0.4), c)
    c = c + (roca - c) * np.clip((pend - 0.25) * 2.0, 0, 0.6)[..., None]
    r = np.sin(x * 0.0021 + np.sin(y * 0.0017) * 2.0) * np.sin(y * 0.0019 - x * 0.0007)
    c = c * (1 + r * 0.07)[..., None]
    dist = np.hypot(x + 150, y + 100)
    c = c + (niebla - c) * (suave(dist, 900, 12000) * 0.62)[..., None]
    C = np.concatenate([c.reshape(-1, 3), np.zeros((n * n, 1))], 1).astype(np.float32)
    a = (jj[:-1, :-1] * n + ii[:-1, :-1]).ravel()
    I = np.stack([a, a + n, a + 1, a + 1, a + n, a + n + 1], 1).reshape(-1, 3).astype(np.uint32)
    # normales por vértice (suma de las de las caras) y la cara visible hacia arriba
    f = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]])
    if f[:, 1].mean() < 0:
        I = I[:, [0, 2, 1]]
        f = -f
    N = np.zeros_like(P)
    for k in range(3):
        np.add.at(N, I[:, k], f)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return P.astype(np.float32), N.astype(np.float32), C, I


# ------------------------------------------------------------------------------------------------- faroles
def faroles(vidrios):
    """Globos de farol: vidrio cálido y claro (las ventanas son de vidrio oscuro). Centro de cada globo, 15 cm abajo."""
    celdas = {}
    for P, _, C, _ in vidrios:
        r, g, b = C[:, 0], C[:, 1], C[:, 2]
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        sel = (lum > 0.35) & (r > b * 1.25)
        for p in P[sel]:
            k = tuple(np.round(p / 0.6).astype(int))
            c = celdas.setdefault(k, [0.0, 0.0, 0.0, 0])
            c[0] += p[0]; c[1] += p[1]; c[2] += p[2]; c[3] += 1
    puntos = sorted((c[0] / c[3], c[1] / c[3], c[2] / c[3], c[3]) for c in celdas.values())
    grupos = []
    for p in puntos:
        for g in grupos:
            if abs(g[0] - p[0]) < 0.9 and abs(g[1] - p[1]) < 0.9 and abs(g[2] - p[2]) < 0.9:
                w = g[3] + p[3]
                g[0], g[1], g[2], g[3] = [(g[i] * g[3] + p[i] * p[3]) / w for i in range(3)] + [w]
                break
        else:
            grupos.append(list(p))
    return [[round(float(g[0]), 2), round(float(g[1]) - 0.15, 2), round(float(g[2]), 2)] for g in grupos]


# ------------------------------------------------------------------------------------------------- hojas de las copas
def componentes(P, I):
    """Número de pieza conexa de cada vértice (vértices soldados por posición, al milímetro)."""
    _, soldado = np.unique(np.round(P * 1000).astype(np.int64), axis=0, return_inverse=True)
    soldado = soldado.ravel()
    e = soldado[I.reshape(-1, 3)]
    a = np.concatenate([e[:, 0], e[:, 1], e[:, 2]])
    b = np.concatenate([e[:, 1], e[:, 2], e[:, 0]])
    et = np.arange(soldado.max() + 1)
    while True:
        antes = et.copy()
        np.minimum.at(et, a, et[b])
        np.minimum.at(et, b, et[a])
        et = et[et]
        if np.array_equal(et, antes):
            break
    return et[soldado]


def tarjetas_hojas(P, N, C, I, semilla, claro=False):
    """Racimos de hojas que cubren una copa (2026-11-26, pedido del usuario: "las copas se ven mal"): cuadros con la
    textura de hojas (texturas/hojas.png) sobre la superficie de cada copa, que el shader orienta hacia la cámara y mece
    con el viento. Sus vértices llevan todos el CENTRO del cuadro; UV.y = esquina + 4·variante + 16·tamaño en cm. La
    normal es la de una esfera centrada en la copa (luz redonda, como un árbol pintado), algo mezclada con la de la cara."""
    I = I.reshape(-1, 3)
    if not len(I):
        return None
    rng = np.random.default_rng(semilla)
    comp = componentes(P, I)
    ncomp = comp.max() + 1
    lo = np.full((ncomp, 3), 1e9)
    hi = np.full((ncomp, 3), -1e9)
    np.minimum.at(lo, comp, P)
    np.maximum.at(hi, comp, P)
    centro = (lo + hi) / 2
    radio = (hi - lo).max(1) / 2
    a, b, c = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
    cruz = np.cross(b - a, c - a)
    area = np.linalg.norm(cruz, axis=1) / 2
    nf = cruz / np.maximum(area[:, None] * 2, 1e-9)
    k = comp[I[:, 0]]
    tam = np.clip(radio[k] * 0.48, 0.45, 1.6)
    cuantas = np.floor(area * 1.7 / tam ** 2 + rng.random(len(I))).astype(np.int64)
    t = np.repeat(np.arange(len(I)), cuantas)
    if not len(t):
        return None
    u, v = rng.random(len(t)), rng.random(len(t))
    fuera = u + v > 1
    u[fuera], v[fuera] = 1 - u[fuera], 1 - v[fuera]
    s = tam[t] * rng.uniform(0.8, 1.2, len(t))
    p = a[t] + (b[t] - a[t]) * u[:, None] + (c[t] - a[t]) * v[:, None] + nf[t] * (s * 0.04)[:, None]
    esf = p - centro[k[t]]
    esf /= np.maximum(np.linalg.norm(esf, axis=1, keepdims=True), 1e-6)
    n = esf * 0.65 + nf[t] * 0.35
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
    col = C[I[t, 0]].copy()          # el color de la copa (la variación por racimo la pone el shader: comprime mejor)
    col[:, :3] *= 1.08 if claro else 1.0
    col[:, 3] = 0.0
    m = len(t)
    variante = rng.integers(0, 4, m)
    tam_cm = np.round(s * 100).astype(np.int64)
    P4 = np.repeat(p, 4, axis=0).astype(np.float32)
    N4 = np.repeat(n, 4, axis=0).astype(np.float32)
    C4 = np.repeat(col, 4, axis=0).astype(np.float32)
    codigo = (np.tile(np.arange(4), m) + 4 * np.repeat(variante, 4) + 16 * np.repeat(tam_cm, 4)).astype(np.float32)
    base = np.arange(m, dtype=np.uint32)[:, None] * 4
    I2 = np.concatenate([base + [0, 1, 2], base + [2, 1, 3]], axis=1).reshape(-1, 3)
    return P4, N4, C4, I2, codigo


# ------------------------------------------------------------------------------------------------- pasto y flores
def separar_canteros(P, N, C, I):
    """Los canteros planos (triángulos de flor horizontales y grandes) pasan a tierra con un poco del color de sus flores:
    las flores las siembra Godot encima (scripts/pasto.gd). Devuelve (flor sin canteros, canteros) o None."""
    I3 = I.reshape(-1, 3)
    cr = np.cross(P[I3[:, 1]] - P[I3[:, 0]], P[I3[:, 2]] - P[I3[:, 0]])
    area = np.linalg.norm(cr, axis=1) / 2
    plano = (cr[:, 1] > 0.7 * 2 * area) & (area > 0.03)
    if not plano.any():
        return (P, N, C, I), None
    Ct = C.copy()
    Ct[:, :3] = Ct[:, :3] * 0.22 + lineal("#4e3826") * 0.78
    return (P, N, C, I3[~plano]), (P, N, Ct, I3[plano])


def suelos_vivos(modelos):
    """Dónde Godot siembra pasto y flores de cerca (scripts/pasto.gd), pedido del usuario del 2026-11-26 ("mejorar el
    pasto y las flores, algo más realista"): los triángulos horizontales de césped y los canteros (triángulos de flor
    horizontales y grandes: los chicos son pétalos de las flores ya modeladas), con su color."""
    cesped, flores = [], []
    for agente, ident, piezas in modelos:
        for rol, dest, minimo in (("cesped", cesped, 0.0), ("flor", flores, 0.03)):
            if rol not in piezas:
                continue
            P, _, C, I = piezas[rol]
            I = I.reshape(-1, 3)
            cr = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]])
            area = np.linalg.norm(cr, axis=1) / 2
            ok = (cr[:, 1] > 0.7 * 2 * area) & (area > minimo)
            for t in np.flatnonzero(ok):
                v = P[I[t]].ravel()
                c = C[I[t, 0], :3]
                dest.append([round(float(x), 2) for x in v] + [round(float(x), 3) for x in c])
    return {"_leeme": "Triángulos (9 coordenadas del mundo + color lineal) donde scripts/pasto.gd siembra pasto y flores.",
            "cesped": cesped, "flores": flores}


# ------------------------------------------------------------------------------------------------- teselas
def repartir(acc, rol, origen, P, N, C, I, U=None):
    """Reparte los triángulos por tesela (según su centro) y los acumula en acc[(tx, tz, rol, origen)]. U: UV.y por
    vértice (las hojas); si falta, 0."""
    if not len(I):
        return
    if U is None:
        U = np.zeros(len(P), np.float32)
    c = (P[I[:, 0]] + P[I[:, 1]] + P[I[:, 2]]) / 3.0
    tx = np.floor(c[:, 0] / LADO).astype(np.int64)
    tz = np.floor(c[:, 2] / LADO).astype(np.int64)
    clave = tx * 100000 + tz
    orden = np.argsort(clave, kind="stable")
    cortes = np.flatnonzero(np.diff(clave[orden])) + 1
    for grupo in np.split(orden, cortes):
        sub = I[grupo]
        usados, inv = np.unique(sub.ravel(), return_inverse=True)
        acc.setdefault((int(tx[grupo[0]]), int(tz[grupo[0]]), rol, origen), []).append(
            (P[usados], N[usados], C[usados], inv.reshape(-1, 3).astype(np.uint32), U[usados]))


def serializar(superficies):
    """[(rol, origen, P, N, C, I[, U])] → (bytes, origen del archivo, centro, radio). Junta por (grupo, clase, origen)."""
    o = np.min([s[2].min(axis=0) for s in superficies], axis=0).astype(np.float32)
    juntas = {}
    for rol, origen, P, N, C, I, *U in superficies:
        doble = clase_de(rol) == "doble"
        clave = (GRUPOS.index(grupo_de(rol)), CLASES.index("normal" if doble else clase_de(rol)), ORIGENES.index(origen))
        juntas.setdefault(clave, []).append((ROLES.index(rol), P, N, C, I, U[0] if U else 0.0))
        if doble:
            # cara trasera: los mismos vértices con la normal invertida y las caras al revés
            juntas[clave].append((ROLES.index(rol), P, -N, C, I.reshape(-1, 3)[:, ::-1], 1.0))
    cab = [np.array([len(juntas)], "<u4").tobytes()]
    cuerpo = []
    for clave in sorted(juntas):
        partes = juntas[clave]
        P = np.concatenate([q[1] for q in partes])
        N = np.concatenate([q[2] for q in partes])
        C = np.concatenate([q[3] for q in partes])
        R = np.zeros((len(P), 2), np.float32)
        idx, base = [], 0
        for rol, Pq, _, _, Iq, atras in partes:
            R[base:base + len(Pq), 0] = rol
            R[base:base + len(Pq), 1] = atras
            idx.append(Iq.reshape(-1, 3) + base)
            base += len(Pq)
        I = np.concatenate(idx)
        cab.append(np.array([*clave, 0], np.uint8).tobytes())
        cab.append(np.array([len(P), I.size], "<u4").tobytes())
        rel = (P - o).astype(np.float32)
        rel = (rel.view(np.uint32) & np.uint32(0xFFFFFF00)).view(np.float32)      # mantisa recortada: comprime mejor (≈ mm)
        cuerpo.append(rel.astype("<f4").tobytes())
        cuerpo.append((np.round(N * 127) / 127).astype("<f4").tobytes())
        cuerpo.append(np.ascontiguousarray(C).astype("<f4").tobytes())
        cuerpo.append(R.astype("<f4").tobytes())
        # three/glTF: caras antihorarias; Godot: horarias
        cuerpo.append(np.ascontiguousarray(I[:, [0, 2, 1]]).astype("<u4").tobytes())
    crudo = b"".join(cab + cuerpo)
    todo = np.concatenate([s[2] for s in superficies])
    centro = (todo.min(axis=0) + todo.max(axis=0)) / 2
    radio = float(np.linalg.norm(todo - centro, axis=1).max())
    return np.array([len(crudo)], "<u4").tobytes() + zlib.compress(crudo, 9), o, centro, radio


def escribir(nombre, datos):
    ruta = os.path.join(SAL, nombre)
    if os.path.exists(ruta) and open(ruta, "rb").read() == datos:
        return hashlib.sha1(datos).hexdigest()[:10]
    open(ruta, "wb").write(datos)
    return hashlib.sha1(datos).hexdigest()[:10]


def main():
    t0 = time.time()
    todo = "--todo" in sys.argv
    os.makedirs(SAL, exist_ok=True)
    modelos = cargar_modelos(todo)
    acc = {}
    vidrios = []
    hojas = 0
    for agente, ident, piezas in modelos:
        for rol, (P, N, C, I) in piezas.items():
            if rol == "flor":
                (P, N, C, I), cantero = separar_canteros(P, N, C, I)
                if cantero is not None:
                    repartir(acc, "cantero", agente, *cantero)
            repartir(acc, rol, agente, P, N, C, I)
            if rol == "vidrio":
                vidrios.append((P, N, C, I))
            if rol in ESTILO["doble_cara"]:
                semilla = int(hashlib.sha1(f"{agente}/{ident}/{rol}".encode()).hexdigest()[:8], 16)
                t = tarjetas_hojas(P, N, C, I, semilla, claro=rol == "follaje_claro")
                if t is not None:
                    repartir(acc, "hoja", agente, *t)
                    hojas += len(t[3]) // 2
    print(f"{hojas} racimos de hojas en las copas")
    for (rol, origen), (P, N, C, I) in cargar_lienzo([m[1] for m in modelos]).items():
        repartir(acc, rol, origen, P, N, C, I)

    por_tesela = {}
    for (tx, tz, rol, origen), lst in acc.items():
        P, N, C, I, U = unir(lst)
        por_tesela.setdefault((tx, tz), {"b": [], "d": [], "h": []})["h" if rol in CERCA else ("d" if rol in DETALLE else "b")].append(
            (rol, origen, P, N, C, I) + ((U,) if rol == "hoja" else ()))
    usados = set()
    indice = []
    total = 0
    triangulos = {}
    for (tx, tz), g in sorted(por_tesela.items()):
        e = {"tx": tx, "tz": tz}
        cajas = []
        for clave, nombre in (("b", "base"), ("d", "detalle"), ("h", "hojas")):
            if not g[clave]:
                continue
            g[clave].sort(key=lambda s: (ROLES.index(s[0]), ORIGENES.index(s[1])))
            for s in g[clave]:
                triangulos[s[0]] = triangulos.get(s[0], 0) + len(s[5])
            datos, o, centro, radio = serializar(g[clave])
            arch = f"t_{tx}_{tz}_{clave}.bin"
            usados.add(arch)
            e[nombre] = {"archivo": arch, "origen": [round(float(v), 4) for v in o], "v": escribir(arch, datos)}
            total += len(datos)
            cajas.append((centro, radio))
        c, r = cajas[0]
        e["centro"] = [round(float(v), 2) for v in c]
        e["radio"] = round(max(rr for _, rr in cajas), 2)
        indice.append(e)
    P, N, C, I = cerros()
    datos, o, _, _ = serializar([("cerro", "lienzo", P, N, C, I)])
    fondo = {"archivo": "fondo.bin", "origen": [float(v) for v in o], "v": escribir("fondo.bin", datos)}
    usados.add("fondo.bin")
    total += len(datos)
    for f in os.listdir(SAL):
        if f.endswith(".bin") and f not in usados:
            os.remove(os.path.join(SAL, f))

    vivos = suelos_vivos(modelos)
    json.dump(vivos, open(os.path.join(SAL, "pasto.json"), "w"), separators=(",", ":"))
    print(f"pasto: {len(vivos['cesped'])} triángulos de césped, {len(vivos['flores'])} de canteros")
    lista_faroles = faroles(vidrios)
    json.dump(lista_faroles, open(os.path.join(SAL, "faroles.json"), "w"), separators=(",", ":"))
    calles = json.load(open(os.path.join(WEB, "mapa", "calles.json")))
    json.dump([{"n": c["nombre"], "t": c["tipo"], "p": [[round(p[0], 1), round(p[1], 1)] for p in c["puntos"]]} for c in calles],
              open(os.path.join(SAL, "calles.json"), "w"), separators=(",", ":"), ensure_ascii=False)
    centros = {}
    for agente, ident, piezas in modelos:
        todo_p = np.concatenate([p[0] for p in piezas.values()]) if piezas else None
        if todo_p is not None and len(todo_p):
            c = (todo_p.min(0) + todo_p.max(0)) / 2
            centros[f"{agente}/{ident}"] = [round(float(v), 1) for v in c]
    version = hashlib.sha1(json.dumps(indice).encode() + fondo["v"].encode()).hexdigest()[:10]
    json.dump({"version": version, "formato": 2, "roles": ROLES, "grupos": GRUPOS, "clases": CLASES, "origenes": ORIGENES, "lado": LADO, "teselas": indice, "fondo": fondo,
               "modelos": centros}, open(os.path.join(SAL, "ciudad.json"), "w"), separators=(",", ":"))
    print(f"{len(indice)} teselas · {total / 1e6:.1f} MB comprimidos · {len(lista_faroles)} faroles · "
          f"{sum(triangulos.values()) / 1e6:.2f} M triángulos · {time.time() - t0:.0f} s")
    json.dump(triangulos, open(os.path.join(CACHE, "triangulos_por_rol.json"), "w"), indent=0)


if __name__ == "__main__":
    main()
