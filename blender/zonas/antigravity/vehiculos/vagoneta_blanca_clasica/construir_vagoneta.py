"""Construcción 3D orgánica en Blender de la Vagoneta Blanca Clásica (`01_vagoneta_blanca_clasica`).

Versión esculpida con volúmenes continuos 3D tipo años 90 (sin cubos apilados ni cortes diagonales):
- Monocasco en barril continuo: zócalo recogido (rocker roll-under), moldura lateral integrada,
  hombro de cintura redondeado, invernadero curvado (tumblehome) y techo abovedado amplio.
- Aletas estampadas con abombamiento (fender flare) y labio de chapa volteado hacia adentro.
- Morro bullnose progresivo con capó abovedado, faros redondeados de lente convexa y parrilla curva.
- Parachoques 3D reales con repisa superior, cojín sobresaliente y faldón inferior recogido.
- Portón trasero abombado en alzado y planta, pilares curvados y espejos/manillas con subdivisión.

Ejecución:
  blender -b -t 2 -P blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/construir_vagoneta.py -- [--sin-render] [--vistas=perspectiva,lateral]
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

DIRECTORIO = Path(__file__).resolve().parent
RAIZ = DIRECTORIO.parents[4]
SKILL_SCRIPTS = RAIZ / ".agents" / "skills" / "vehiculo-3d-desde-diseno" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
sys.path.insert(0, str(RAIZ / "blender" / "kit"))

from paleta import material as material_rol  # noqa: E402
from kit_vehiculo_bpy import (  # noqa: E402
    configurar_estudio_y_renderizar,
    configurar_normal_goma,
    consolidar_lotes,
    construir_ruedas_volumetricas,
    contorno_redondeado,
    crear_caja,
    crear_cilindro,
    crear_malla,
    crear_panel,
    crear_superficie_grid,
    crear_tubo,
    exportar_glb_vehiculo,
    inicializar_jerarquia,
    interpolar_hermite,
    preparar_rig_y_clips,
    suavizar_subsurf,
    validar_geometria_vehiculo,
)

D = json.loads((DIRECTORIO / "vagoneta_blanca_clasica.json").read_text())
SALIDA = RAIZ / "web" / "public" / "models" / "ciudad" / "antigravity" / "vehiculos" / D["id"]
REVISION = RAIZ / "revisiones" / "antigravity" / D["id"]
SALIDA.mkdir(parents=True, exist_ok=True)
REVISION.mkdir(parents=True, exist_ok=True)

M = {}
GRUPOS = {}

# Perfiles longitudinales suaves medidos de la lámina 01_vagoneta_blanca_clasica_diseno_miciudad.png
PERFIL_CINTURA = [
    (-2.02, 0.945),
    (-1.60, 0.955),
    (-0.90, 0.952),
    (-0.10, 0.946),
    (0.86, 0.940),
    (1.35, 0.902),
    (1.70, 0.855),
    (1.90, 0.808),
    (2.06, 0.736),
]

PERFIL_CAPO_CENTRO = [
    (0.86, 0.972),
    (1.18, 0.952),
    (1.52, 0.914),
    (1.80, 0.868),
    (1.96, 0.818),
    (2.05, 0.768),
    (2.092, 0.734),
]

# Techo con caída suave y redondeada en parabrisas y portón (sin esquinas angulosas)
PERFIL_TECHO_CIMA = [
    (-1.74, 1.422),
    (-1.62, 1.482),
    (-1.42, 1.518),
    (-1.05, 1.528),
    (-0.55, 1.530),
    (-0.05, 1.522),
    (0.18, 1.496),
    (0.33, 1.438),
]

PERFIL_RIEL_TECHO = [
    (-1.72, 1.402),
    (-1.55, 1.426),
    (-1.10, 1.438),
    (-0.45, 1.440),
    (0.08, 1.432),
    (0.31, 1.408),
]


def sstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def z_cintura(x):
    return interpolar_hermite(PERFIL_CINTURA, x)


def z_riel_techo(x):
    return interpolar_hermite(PERFIL_RIEL_TECHO, x)


def estrechamiento_planta(x):
    """ Forma suavemente ahusada (en huso / barril en planta) típica de los años 90. """
    if x >= 0.0:
        t = min(1.0, x / 2.05)
        return 1.0 - 0.082 * (t ** 2.1)
    t = min(1.0, (-x) / 2.05)
    return 1.0 - 0.062 * (t ** 2.2)


def relieve_aleta_y_moldura(x, z):
    """Volumen muscular suave en ambos pasos de rueda + moldura lateral integrada a media puerta."""
    zc = D["centro_rueda_z"]
    flare = 0.0
    for eje in D["ejes"]:
        dx = x - eje
        dz = max(-0.06, z - zc) * 1.05
        dist = math.hypot(dx, dz)
        # Abombamiento ancho de aleta estampada (r = 0.372..0.525 m)
        if 0.368 <= dist <= 0.525:
            u = (dist - 0.368) / (0.525 - 0.368)
            flare = max(flare, 0.021 * (math.sin(math.pi * u) ** 1.15))

    # Moldura horizontal abombada entre ruedas (z ~ 0.49..0.535 m, alineada con el parachoques)
    moldura = 0.0
    if -0.78 <= x <= 0.74 and 0.472 <= z <= 0.536:
        ux = sstep((x + 0.78) / 0.08) * sstep((0.74 - x) / 0.08)
        uz = math.sin(math.pi * (z - 0.472) / (0.536 - 0.472))
        moldura = 0.010 * ux * (uz ** 0.85)

    return flare + moldura


def semiancho_barril(x, z):
    """Sección transversal continua en C (zócalo recogido -> panza -> hombro redondeado -> invernadero curvo)."""
    zc = z_cintura(x)
    zr = z_riel_techo(x)
    esc = estrechamiento_planta(x)
    if z <= zc:
        u = max(0.0, min(1.0, (z - 0.215) / max(0.12, zc - 0.215)))
        perfil_u = [
            (0.00, 0.708),  # zócalo inferior profundamente recogido hacia el bastidor
            (0.11, 0.806),  # curva baja de estribo
            (0.32, 0.848),  # tercio inferior de puerta
            (0.52, 0.862),  # panza máxima a media altura
            (0.78, 0.854),  # volumen alto de puerta
            (0.91, 0.838),  # inicio del hombro redondeado de cintura
            (1.00, 0.808),  # apoyo redondeado de ventanilla
        ]
        return interpolar_hermite(perfil_u, u) * esc + relieve_aleta_y_moldura(x, z)

    # Invernadero con curvatura convexa suave (no una recta rígida) hasta el riel del techo
    v = max(0.0, min(1.0, (z - zc) / max(0.10, zr - zc)))
    perfil_inv = [
        (0.00, 0.808),
        (0.30, 0.764),
        (0.65, 0.698),
        (1.00, 0.618),
    ]
    return interpolar_hermite(perfil_inv, v) * esc


def x_nariz_frontal(y_abs):
    """Curva orgánica en planta del frente (centro convexo y esquinas ampliamente redondeadas)."""
    perfil = [
        (0.00, 2.092),
        (0.36, 2.074),
        (0.62, 2.032),
        (0.73, 1.982),
        (0.785, 1.920),
        (0.808, 1.850),
    ]
    return interpolar_hermite(perfil, y_abs)


def x_perfil_porton(z):
    """Curva lateral continua de la trasera: sin escalón recto entre chapa y luneta."""
    perfil = [
        (0.540, -2.032),
        (0.680, -2.054),
        (0.855, -2.062),  # volumen abombado suave del portón bajo la luneta
        (0.960, -2.036),  # transición redondeada hacia el cristal trasero
        (1.120, -1.938),
        (1.290, -1.824),
        (1.425, -1.718),
        (1.475, -1.665),
    ]
    return interpolar_hermite(perfil, z)


def z_borde_inferior_chapa(x):
    """Borde inferior continuo de la piel blanca con arcos elípticos desde el zócalo z=0.218 sin saltos."""
    z_base = 0.218
    z = z_base
    if x < -1.505:
        t = sstep((-1.505 - x) / 0.045)
        z = z_base * (1.0 - t) + 0.542 * t
    elif x > 1.475:
        t = sstep((x - 1.475) / 0.045)
        z = z_base * (1.0 - t) + 0.550 * t

    rx_arco = 0.386
    rz_arco = 0.480  # z_base (0.218) + 0.480 = 0.698 m en la cima del paso de rueda
    for eje in D["ejes"]:
        dx = abs(x - eje)
        if dx < rx_arco:
            u = dx / rx_arco
            z = max(z, z_base + rz_arco * math.sqrt(max(0.0, 1.0 - u * u)))
    return z


def solidificar(obj, espesor=0.015, offset=-1.0):
    mod = obj.modifiers.new("Chapa", "SOLIDIFY")
    mod.thickness = espesor
    mod.offset = offset
    mod.use_even_offset = True
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def crear_materiales():
    c = D["colores"]
    M["carroceria"] = material_rol("muro", c["carroceria"])
    M["carroceria"]["pintura_vehiculo"] = "principal"
    M["parachoques"] = material_rol("hierro", c["parachoques"])
    M["goma"] = material_rol("hierro", c["goma"])
    M["oscuro"] = material_rol("hierro", c["oscuro"])
    M["interior"] = material_rol("hierro", c["interior"])
    M["tapizado"] = material_rol("hierro", c["tapizado"])
    M["llanta"] = material_rol("metal", c["llanta"])
    M["cromo"] = material_rol("metal", c["cromo"])
    M["faro"] = material_rol("metal", c["faro"])
    M["ambar"] = material_rol("pintura_acento", c["ambar"])
    M["rojo"] = material_rol("pintura_acento", c["rojo"])
    M["placa"] = material_rol("letrero", c["placa"])

    M["carroceria"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.42
    M["parachoques"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.68
    M["llanta"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.58
    M["llanta"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.34
    M["cromo"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.80
    M["cromo"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.20
    M["faro"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.14
    M["ambar"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.22
    M["rojo"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.22

    M["vidrio"] = material_rol("vidrio", c["vidrio"])
    bs_v = M["vidrio"].node_tree.nodes["Principled BSDF"]
    bs_v.inputs["Alpha"].default_value = 0.34
    bs_v.inputs["Roughness"].default_value = 0.16
    M["vidrio"].diffuse_color = (*M["vidrio"].diffuse_color[:3], 0.34)
    M["vidrio"].surface_render_method = "DITHERED"
    M["vidrio"].use_transparent_shadow = True

    M["lente_claro"] = material_rol("vidrio", "#dce4f0")
    bs_l = M["lente_claro"].node_tree.nodes["Principled BSDF"]
    bs_l.inputs["Alpha"].default_value = 0.46
    bs_l.inputs["Roughness"].default_value = 0.10
    M["lente_claro"].diffuse_color = (*M["lente_claro"].diffuse_color[:3], 0.46)
    M["lente_claro"].surface_render_method = "DITHERED"

    M["neumatico"] = material_rol("hierro", "#29282c")
    ruta_normal = DIRECTORIO / D["acabados"]["textura_goma"]
    configurar_normal_goma(M["neumatico"], ruta_normal, D["acabados"]["normal_goma_intensidad"])


def construir_flancos_organicos():
    """Flancos continuos en barril con moldura integrada, hombro de cintura y labio interior volteado."""
    xs_brutos = sorted(
        {-1.900 + (1.850 - (-1.900)) * i / 48 for i in range(49)}
        | {eje - 0.41 + 0.82 * i / 28 for eje in D["ejes"] for i in range(29)}
    )
    xs = []
    for x in xs_brutos:
        if -1.901 <= x <= 1.851 and (not xs or x - xs[-1] >= 0.014):
            xs.append(round(x, 5))
    if xs[-1] < 1.849:
        xs.append(1.850)

    # Fracciones verticales densas en zócalo, moldura central y hombro de cintura
    us_z = [0.0, 0.04, 0.10, 0.20, 0.32, 0.40, 0.44, 0.48, 0.53, 0.64, 0.76, 0.86, 0.93, 0.97, 1.0]

    for signo in (-1, 1):
        filas = []
        for x in xs:
            zb = z_borde_inferior_chapa(x)
            zt = z_cintura(x)
            ya_borde = semiancho_barril(x, zb)
            # 3 anillos interiores volteados hacia adentro (labio redondeado de guardabarros y estribo)
            fila = [
                (x, signo * (ya_borde - 0.036), zb + 0.008),
                (x, signo * (ya_borde - 0.015), zb + 0.001),
                (x, signo * (ya_borde - 0.003), zb - 0.002),
            ]
            for u in us_z:
                z = zb + (zt - zb) * u
                y = semiancho_barril(x, z)
                fila.append((x, signo * y, z))
            # Vuelta superior suave hacia el apoyo del cristal
            y_top = semiancho_barril(x, zt)
            fila.append((x, signo * (y_top - 0.012), zt + 0.006))
            fila.append((x, signo * (y_top - 0.026), zt + 0.003))
            filas.append(fila)

        crear_superficie_grid(
            f"Flanco monocasco {'izq' if signo > 0 else 'der'}",
            filas,
            M["carroceria"],
            GRUPOS["carroceria"],
            invertir=(signo > 0),
        )

        # Líneas finas de cierre de puertas siguiendo exactamente la curvatura del barril
        for nombre_j, xj, z_ini in [
            ("Junta puerta delantera", 0.845, 0.32),
            ("Junta central puertas", -0.125, 0.24),
            ("Junta puerta trasera", -0.895, 0.58),
        ]:
            zt = z_cintura(xj) - 0.006
            pts_j = [
                (xj, signo * (semiancho_barril(xj, z) + 0.0018), z)
                for z in [z_ini + (zt - z_ini) * s / 10 for s in range(11)]
            ]
            crear_tubo(nombre_j, pts_j, 0.0026, M["oscuro"], GRUPOS["decoracion"], resolucion=1)

        # Manillas ovaladas orgánicas (cuenco cóncavo suave + tirador redondeado con SUBSURF)
        for nombre_m, xm, zm in [("Manilla delantera", 0.02, 0.865), ("Manilla trasera", -0.745, 0.872)]:
            ym = signo * semiancho_barril(xm, zm)
            cuenco = crear_caja(
                nombre_m + " cuenco",
                (xm, ym + signo * 0.003, zm),
                (0.145, 0.018, 0.058),
                M["oscuro"],
                GRUPOS["decoracion"],
            )
            cuenco.rotation_euler.x = signo * 0.16
            suavizar_subsurf(cuenco, niveles=2)

            tirador = crear_caja(
                nombre_m + " tirador",
                (xm, ym + signo * 0.010, zm + 0.005),
                (0.118, 0.018, 0.032),
                M["goma"],
                GRUPOS["decoracion"],
            )
            tirador.rotation_euler.x = signo * 0.16
            suavizar_subsurf(tirador, niveles=2)

        # Bóveda interior cerrada en los cuatro pasos de rueda
        for eje in D["ejes"]:
            arco_int = [
                (eje + 0.388 * math.cos(math.pi * s / 24), D["centro_rueda_z"] + 0.388 * math.sin(math.pi * s / 24))
                for s in range(25)
            ]
            y_ext = signo * 0.785
            y_int = signo * 0.585
            filas_bov = [[(xx, y_int, zz), (xx, y_ext, zz)] for xx, zz in arco_int]
            bov = crear_superficie_grid("Boveda guardabarros", filas_bov, M["oscuro"], GRUPOS["interior"], invertir=(signo < 0))
            solidificar(bov, espesor=0.012)
            crear_panel(
                "Fondo paso rueda",
                [(xx, y_int, zz) for xx, zz in arco_int] + [(eje - 0.388, y_int, 0.22), (eje + 0.388, y_int, 0.22)],
                M["oscuro"],
                GRUPOS["interior"],
                espesor=0.012,
            )

    crear_caja("Bandeja inferior chasis", (-0.02, 0.0, 0.235), (3.72, 1.34, 0.055), M["oscuro"], GRUPOS["interior"], bisel=0.018)
    for x_eje in D["ejes"]:
        crear_cilindro("Puente eje", (x_eje, 0.0, D["centro_rueda_z"]), 0.034, 1.36, M["oscuro"], GRUPOS["interior"], eje="Y", lados=16)


def construir_techo_e_invernadero_curvo():
    """Techo abovedado amplio y pilares A/B/C/D curvados sobre la superficie en barril."""
    # 1. Bóveda continua del techo (de X = -1.73 a X = +0.33, con hombros anchos y suaves)
    xs_t = [-1.73 + (0.33 - (-1.73)) * i / 28 for i in range(29)]
    us_y = [-1.0 + 2.0 * j / 24 for j in range(25)]
    filas_techo = []
    for x in xs_t:
        z_cima = interpolar_hermite(PERFIL_TECHO_CIMA, x)
        z_riel = z_riel_techo(x)
        ancho_r = semiancho_barril(x, z_riel)
        # Redondeo en planta de las esquinas delantera y trasera del techo
        encoge = 0.0
        curva_x = 0.0
        if x > 0.10:
            w = sstep((x - 0.10) / 0.23)
            encoge = 0.036 * w
            curva_x = -0.052 * w
        elif x < -1.48:
            w = sstep((-1.48 - x) / 0.25)
            encoge = 0.042 * w
            curva_x = 0.058 * w

        fila = []
        for u in us_y:
            ua = abs(u)
            y = u * (ancho_r - encoge + 0.004)
            # Domo elíptico continuo de centro a hombro, solapando 6 mm sobre el larguero lateral
            caida = 0.28 * (ua ** 2) + 0.72 * (1.0 - math.sqrt(max(0.0, 1.0 - (ua ** 2.4) * 0.96)))
            z = z_cima - caida * (z_cima - (z_riel - 0.006))
            xx = x + curva_x * (ua ** 2.2)
            fila.append((xx, y, z))
        filas_techo.append(fila)

    crear_superficie_grid("Boveda techo vagoneta", filas_techo, M["carroceria"], GRUPOS["carroceria"], invertir=False)
    # Cielo interior contenido bajo la bóveda para que nunca asome por los hombros del techo
    crear_caja("Tapizado cielo interior", (-0.68, 0.0, 1.395), (1.72, 1.00, 0.018), M["interior"], GRUPOS["interior"], bisel=0.006)

    # 2. Pilares curvados y ventanillas redondeadas sobre el barril
    def punto_barril(x, z, signo, desp_normal=0.0):
        return (x, signo * (semiancho_barril(x, z) + desp_normal), z)

    def crear_pilar_curvo(nombre, func_x_izq, func_x_der, z0, z1, signo, abombamiento=0.006, n_z=12):
        filas_p = []
        for i in range(n_z + 1):
            tz = i / n_z
            z = z0 + (z1 - z0) * tz
            xa = func_x_izq(tz)
            xb = func_x_der(tz)
            # Sección transversal curva del pilar con bordes vueltos hacia el cristal (-10 mm)
            fila = []
            for su, desp in [
                (0.00, -0.012),
                (0.08, 0.001),
                (0.32, abombamiento * 0.85),
                (0.50, abombamiento),
                (0.68, abombamiento * 0.85),
                (0.92, 0.001),
                (1.00, -0.012),
            ]:
                xx = xa + (xb - xa) * su
                fila.append(punto_barril(xx, z, signo, desp))
            filas_p.append(fila)
        return crear_superficie_grid(nombre, filas_p, M["carroceria"], GRUPOS["carroceria"], invertir=(signo < 0))

    for signo in (-1, 1):
        # Larguero curvo del techo (cantrail) enlazando suavemente A hasta D
        filas_cant = []
        xs_cant = [-1.70 + (0.31 - (-1.70)) * i / 24 for i in range(25)]
        for x in xs_cant:
            zr = z_riel_techo(x)
            zb = zr - 0.028
            filas_cant.append([
                punto_barril(x, zb, signo, -0.012),
                punto_barril(x, zb + 0.006, signo, 0.002),
                punto_barril(x, zr - 0.006, signo, 0.005),
                punto_barril(x, zr + 0.008, signo, -0.004),
            ])
        crear_superficie_grid("Larguero curvo techo", filas_cant, M["carroceria"], GRUPOS["carroceria"], invertir=(signo > 0))

        # Pilar D curvo (envuelve desde la cintura trasera hasta el hombro curvo del techo y esquina del portón)
        def x_d_tras(t):
            return -2.015 * (1 - t) + (-1.715) * t + 0.028 * math.sin(math.pi * t)

        def x_d_del(t):
            return -1.825 * (1 - t) + (-1.585) * t + 0.032 * math.sin(math.pi * t)

        crear_pilar_curvo("Pilar D envolvente", x_d_tras, x_d_del, 0.938, 1.422, signo, abombamiento=0.007, n_z=14)

        # Pilar C esbelto ligeramente inclinado
        crear_pilar_curvo(
            "Pilar C",
            lambda t: -0.955 - 0.032 * t,
            lambda t: -0.880 - 0.032 * t,
            0.942,
            1.434,
            signo,
            abombamiento=0.005,
        )

        # Pilar B
        crear_pilar_curvo(
            "Pilar B",
            lambda t: -0.160 - 0.028 * t,
            lambda t: -0.072 - 0.028 * t,
            0.940,
            1.436,
            signo,
            abombamiento=0.005,
        )

        # Pilar A suavemente arqueado (típico parabrisas envolvente de los 90)
        def x_a_int(t):
            return 0.815 * (1 - t) + 0.225 * t + 0.026 * math.sin(math.pi * t)

        def x_a_ext(t):
            return 0.905 * (1 - t) + 0.315 * t + 0.026 * math.sin(math.pi * t)

        crear_pilar_curvo("Pilar A arqueado", x_a_int, x_a_ext, 0.932, 1.418, signo, abombamiento=0.007, n_z=14)

        # Tres ventanillas laterales curvas con esquinas generosamente redondeadas y burlete perimetral
        vanos_xz = [
            ("Ventanilla carga trasera", [(-1.835, 0.952), (-0.950, 0.952), (-0.982, 1.418), (-1.592, 1.412)], 0.055),
            ("Ventanilla puerta trasera", [(-0.884, 0.952), (-0.156, 0.952), (-0.184, 1.420), (-0.914, 1.420)], 0.038),
            ("Ventanilla puerta delantera", [(-0.076, 0.950), (0.825, 0.944), (0.245, 1.414), (-0.104, 1.420)], 0.052),
        ]
        for nombre_v, poli_xz, rad_v in vanos_xz:
            suave_xz = contorno_redondeado(poli_xz, radio=rad_v, pasos=4)
            pts_burlete = [punto_barril(x, z, signo, -0.002) for x, z in suave_xz]
            # Superficie curva limpia (10 x 6) para el cristal siguiendo la curvatura del barril
            p0, p1, p2, p3 = poli_xz
            filas_vid = []
            for iv in range(7):
                tv = iv / 6
                xa = p0[0] * (1 - tv) + p3[0] * tv
                xb = p1[0] * (1 - tv) + p2[0] * tv
                za = p0[1] * (1 - tv) + p3[1] * tv
                zb_v = p1[1] * (1 - tv) + p2[1] * tv
                fila_v = []
                for iu in range(9):
                    tu = iu / 8
                    xx = xa * (1 - tu) + xb * tu
                    zz = za * (1 - tu) + zb_v * tu
                    fila_v.append(punto_barril(xx, zz, signo, -0.011))
                filas_vid.append(fila_v)
            crear_superficie_grid(nombre_v, filas_vid, M["vidrio"], GRUPOS["cristales"], invertir=(signo > 0))
            crear_tubo(nombre_v + " burlete", pts_burlete, 0.013, M["goma"], GRUPOS["carroceria"], cerrado=True)

        # Divisor vertical de la ventanilla trasera
        pts_div = [
            punto_barril(-0.705 - 0.022 * (s / 6), 0.955 + (1.416 - 0.955) * (s / 6), signo, -0.003)
            for s in range(7)
        ]
        crear_tubo("Divisor ventanilla trasera", pts_div, 0.010, M["goma"], GRUPOS["carroceria"])

        # Base triangular curva y espejo retrovisor aerodinámico en gota (con SUBSURF)
        tri_esp = contorno_redondeado([(0.64, 0.946), (0.84, 0.942), (0.71, 1.115)], radio=0.022, pasos=3)
        crear_panel(
            "Base espejo delantero",
            [punto_barril(x, z, signo, 0.002) for x, z in tri_esp],
            M["oscuro"],
            GRUPOS["carroceria"],
            espesor=0.016,
        )
        yb_esp = signo * semiancho_barril(0.73, 1.02)
        brazo_e = crear_caja("Brazo espejo", (0.735, yb_esp + signo * 0.036, 1.022), (0.068, 0.075, 0.034), M["oscuro"], GRUPOS["carroceria"])
        suavizar_subsurf(brazo_e, niveles=1)

        # Carcasa de espejo esculpida redondeada años 90 (compensando encogimiento de SUBSURF)
        carcasa = crear_caja("Carcasa retrovisor", (0.705, yb_esp + signo * 0.105, 1.048), (0.128, 0.172, 0.138), M["oscuro"], GRUPOS["carroceria"])
        bm = bmesh.new()
        bm.from_mesh(carcasa.data)
        for v in bm.verts:
            es_ext = (v.co.y * signo) > 0
            if es_ext:
                v.co.z *= 0.86
                v.co.x -= 0.020
            if v.co.x > 0:
                v.co.z *= 0.90
                v.co.y -= signo * 0.008
        bm.to_mesh(carcasa.data)
        bm.free()
        suavizar_subsurf(carcasa, niveles=2)

        cristal_e = crear_caja("Cristal retrovisor", (0.648, yb_esp + signo * 0.104, 1.048), (0.010, 0.124, 0.082), M["cromo"], GRUPOS["decoracion"], bisel=0.008)
        cristal_e.rotation_euler.z = signo * -0.14

    # 3. Parabrisas delantero curvado en alzado y planta + encuentro suave con techo
    filas_pb = []
    for i in range(13):
        v = i / 12
        z = 0.946 + (1.426 - 0.946) * v
        x_lat = 0.865 * (1 - v) + 0.275 * v + 0.024 * math.sin(math.pi * v)
        ancho = semiancho_barril(x_lat, z) - 0.026
        bombeo_x = 0.068 * (1.0 - 0.22 * v)
        fila = []
        for j in range(21):
            u = -1.0 + 2.0 * j / 20
            # Redondear suavemente las esquinas superiores del parabrisas
            recorte_z = -0.016 * (u ** 6) if v > 0.85 else (0.012 * (u ** 6) if v < 0.12 else 0.0)
            y = u * ancho
            x = x_lat + bombeo_x * (1.0 - u * u)
            fila.append((x, y, z + recorte_z))
        filas_pb.append(fila)

    pb = crear_superficie_grid("Parabrisas curvo", filas_pb, M["vidrio"], GRUPOS["cristales"])
    solidificar(pb, espesor=0.006)

    perim_pb = (
        filas_pb[0]
        + [filas_pb[i][-1] for i in range(1, 13)]
        + list(reversed(filas_pb[-1][:-1]))
        + [filas_pb[i][0] for i in range(11, 0, -1)]
    )
    crear_tubo(
        "Burlete parabrisas",
        [(x + 0.004, y, z) for x, y, z in perim_pb],
        0.014,
        M["goma"],
        GRUPOS["carroceria"],
        cerrado=True,
    )

    # Cintillo blanco curvo que enlaza sin escalón el borde superior del parabrisas con la bóveda del techo
    filas_cint = [
        [(x - 0.002, y * 1.01, z - 0.004) for x, y, z in filas_pb[-1]],
        [(x - 0.025, y * 1.005, z + 0.010) for x, y, z in filas_pb[-1]],
        [(x - 0.055, y * 0.995, z + 0.018) for x, y, z in filas_pb[-1]],
    ]
    cint = crear_superficie_grid("Cintillo curvo techo parabrisas", filas_cint, M["carroceria"], GRUPOS["carroceria"])
    solidificar(cint, espesor=0.014)


def construir_capo_y_frente_organico():
    """Capó bullnose enrasado exactamente con el borde superior de las aletas delanteras."""
    n_u, n_v = 26, 26
    filas_capo = []
    for j in range(n_v + 1):
        u = -1.0 + 2.0 * j / n_v
        ua = abs(u)
        fila = []
        for i in range(n_u + 1):
            t = i / n_u
            x_cen = 0.86 + (2.092 - 0.86) * t
            x_ext = 0.86 + (1.850 - 0.86) * min(1.0, t / 0.84) if t <= 0.84 else 1.850 + (x_nariz_frontal(0.806) - 1.850) * ((t - 0.84) / 0.16)
            # Interpolar X entre el centro adelantado y el borde exterior curvo
            x = x_cen * (1.0 - ua ** 2.2) + x_ext * (ua ** 2.2)

            # En el borde exterior (ua=1), coincidir EXACTAMENTE con la cima del flanco monocasco z_cintura(x)
            if x <= 1.850:
                z_borde = z_cintura(x)
                y_max = semiancho_barril(x, z_borde)
            else:
                w = sstep((x - 1.850) / max(0.05, x_nariz_frontal(0.72) - 1.850))
                z_borde = z_cintura(1.850) * (1.0 - w) + 0.734 * w
                y_max = semiancho_barril(1.850, z_cintura(1.850)) * (1.0 - 0.03 * w)

            # En el frente (t -> 1), el borde frontal sigue la curva x_nariz_frontal(y)
            y = u * y_max
            if t > 0.82:
                wt = sstep((t - 0.82) / 0.18)
                y_nariz = u * 0.806
                y = y * (1.0 - wt) + y_nariz * wt
                x = x * (1.0 - wt) + x_nariz_frontal(abs(y_nariz)) * wt
                z_borde = z_borde * (1.0 - wt) + 0.734 * wt

            z_cen = interpolar_hermite(PERFIL_CAPO_CENTRO, x)
            domo = 1.0 - (ua ** 2.0)
            nervio = 0.004 * math.exp(-(((ua - 0.48) / 0.14) ** 2)) * sstep(t * 1.4)
            z = z_borde + max(0.0, z_cen - z_borde) * domo + nervio
            if t > 0.93:
                wb = (t - 0.93) / 0.07
                z -= 0.010 * (wb * wb) * (1.0 - 0.5 * ua)
            fila.append((x, y, z))
        filas_capo.append(fila)

    crear_superficie_grid("Capo delantero abovedado", filas_capo, M["carroceria"], GRUPOS["carroceria"], invertir=True)

    # Cierre inferior suave entre la aleta (X=1.85) y el borde bajo del piloto de esquina ámbar (Z=0.550..0.635)
    for signo in (-1, 1):
        filas_inf_m = []
        for s in range(7):
            w = s / 6
            xx = 1.848 + (1.965 - 1.848) * w
            z_top_i = 0.638 - 0.042 * sstep(w)
            yy = semiancho_barril(1.850, 0.58) * (1.0 - 0.052 * (w ** 1.5))
            filas_inf_m.append([(xx, signo * yy, 0.548), (xx, signo * yy, z_top_i)])
        inf_m = crear_superficie_grid("Faldon punta aleta", filas_inf_m, M["carroceria"], GRUPOS["carroceria"], invertir=(signo > 0))
        solidificar(inf_m, espesor=0.014)
        # Pequeño triángulo superior entre X=1.85 (z=0.81) y el esquinero (z=0.69..0.734)
        pts_sup_e = [
            (1.848, signo * semiancho_barril(1.850, 0.688), 0.686),
            (1.955, signo * 0.796, 0.724),
            (1.955, signo * 0.792, 0.752),
            (1.848, signo * semiancho_barril(1.850, z_cintura(1.850)), z_cintura(1.850)),
        ]
        crear_panel("Enlace superior aleta faro", pts_sup_e, M["carroceria"], GRUPOS["carroceria"], espesor=0.014)

        zc_s = interpolar_hermite(PERFIL_CAPO_CENTRO, 1.32) - 0.003
        dif = crear_caja("Difusor lavaparabrisas", (1.32, signo * 0.30, zc_s + 0.005), (0.026, 0.016, 0.012), M["oscuro"], GRUPOS["decoracion"])
        suavizar_subsurf(dif, niveles=1)

    # Rejilla torpedo curva y limpiaparabrisas
    crear_caja("Torpedo parabrisas", (0.88, 0.0, 0.948), (0.09, 1.48, 0.026), M["oscuro"], GRUPOS["carroceria"], bisel=0.008)
    for y_piv, largo_esc in [(-0.10, 0.42), (0.36, 0.44)]:
        xb = 0.885 + 0.045 * (1.0 - (y_piv / 0.72) ** 2)
        crear_tubo("Brazo limpiaparabrisas", [(xb + 0.015, y_piv, 0.968), (xb - 0.015, y_piv - 0.22, 1.006)], 0.0065, M["oscuro"], GRUPOS["decoracion"])
        crear_tubo("Escobilla limpiaparabrisas", [(xb - 0.008, y_piv - 0.05, 0.988), (xb - 0.024, y_piv - largo_esc, 1.022)], 0.0085, M["goma"], GRUPOS["decoracion"])

    # 2. Bigote / moldura blanca curva continua bajo faros y parrilla (Z = 0.548..0.594)
    ys_big = [-0.805 + 1.610 * i / 32 for i in range(33)]
    filas_big = []
    for yy in ys_big:
        xb = x_nariz_frontal(abs(yy))
        filas_big.append([
            (xb - 0.012, yy, 0.548),
            (xb + 0.005, yy, 0.572),
            (xb - 0.004, yy, 0.594),
        ])
    big = crear_superficie_grid("Moldura curva bajo opticas", filas_big, M["carroceria"], GRUPOS["carroceria"])
    solidificar(big, espesor=0.020, offset=-1.0)

    # Fondo interior oscuro continuo del frente
    filas_resp = [[(x_nariz_frontal(abs(yy)) - 0.026, yy, 0.550), (x_nariz_frontal(abs(yy)) - 0.026, yy, 0.742)] for yy in ys_big]
    resp = crear_superficie_grid("Respaldo oscuro frente", filas_resp, M["oscuro"], GRUPOS["carroceria"])
    solidificar(resp, espesor=0.016)

    # 3. Parrilla central curva con marco redondeado, 3 lamas esculpidas y emblema abombado
    ys_par = [-0.380 + 0.760 * i / 16 for i in range(17)]
    for z_lama in (0.624, 0.664, 0.704):
        pts_lama = [(x_nariz_frontal(abs(yy)) + 0.003, yy, z_lama) for yy in ys_par]
        crear_tubo("Lama curva parrilla", pts_lama, 0.0085, M["parachoques"], GRUPOS["decoracion"], resolucion=2)

    contorno_par = contorno_redondeado([(-0.386, 0.594), (0.386, 0.594), (0.372, 0.732), (-0.372, 0.732)], radio=0.024, pasos=4)
    crear_tubo(
        "Cerco parrilla central",
        [(x_nariz_frontal(abs(y)) + 0.002, y, z) for y, z in contorno_par],
        0.009,
        M["oscuro"],
        GRUPOS["carroceria"],
        cerrado=True,
    )
    pts_emb = [(2.100, 0.042 * math.cos(math.tau * i / 32), 0.664 + 0.032 * math.sin(math.tau * i / 32)) for i in range(32)]
    crear_tubo("Emblema frontal aro", pts_emb, 0.0055, M["cromo"], GRUPOS["decoracion"], cerrado=True)
    crear_tubo("Emblema frontal barra", [(2.102, -0.040, 0.664), (2.102, 0.040, 0.664)], 0.005, M["cromo"], GRUPOS["decoracion"])

    # 4. Faros principales redondeados con cuencos reflectores y lente abombada + esquinero envolvente orgánico
    for signo in (-1, 1):
        # Faro principal (|y| = 0.392..0.718, z = 0.594..0.734) con esquinas redondeadas y lente abombada 3D
        n_fy, n_fz = 12, 8
        filas_refl = []
        filas_lente = []
        for i in range(n_fy + 1):
            u = i / n_fy
            yy = 0.394 + (0.718 - 0.394) * u
            # Ligero ahusamiento vertical junto a la parrilla (u -> 0) como en los Corolla E100 reales
            z_inf_f = 0.596 + 0.006 * ((1.0 - u) ** 2)
            z_sup_f = 0.734 - 0.005 * ((1.0 - u) ** 2)
            xf = x_nariz_frontal(yy)
            fila_r, fila_l = [], []
            for k in range(n_fz + 1):
                v = k / n_fz
                # Redondeo de esquinas en los extremos
                enc_z = 0.010 * math.sin(math.pi * v) if (u < 0.08 or u > 0.92) else 0.0
                zz = (z_inf_f + enc_z * 0.3) * (1 - v) + (z_sup_f - enc_z * 0.3) * v
                # Lente con abombamiento almohadillado 3D (+13 mm) y reflector cóncavo doble detrás
                domo_l = 0.013 * math.sin(math.pi * u) * math.sin(math.pi * v)
                concavo_r = -0.014 * abs(math.sin(2.0 * math.pi * u)) * math.sin(math.pi * v)
                fila_r.append((xf - 0.004 + concavo_r, signo * yy, zz))
                fila_l.append((xf + 0.005 + domo_l, signo * yy, zz))
            filas_refl.append(fila_r)
            filas_lente.append(fila_l)

        refl = crear_superficie_grid("Reflector doble faro", filas_refl, M["cromo"], GRUPOS["decoracion"], invertir=(signo < 0))
        solidificar(refl, espesor=0.006)
        lente = crear_superficie_grid("Lente abombado faro", filas_lente, M["lente_claro"], GRUPOS["cristales"], invertir=(signo < 0))
        solidificar(lente, espesor=0.004)

        # Burlete redondeado alrededor del faro
        cont_faro = contorno_redondeado([(0.394, 0.602), (0.718, 0.596), (0.718, 0.734), (0.394, 0.729)], radio=0.024, pasos=4)
        crear_tubo(
            "Cerco suave faro",
            [(x_nariz_frontal(y) + 0.003, signo * y, z) for y, z in cont_faro],
            0.0075,
            M["oscuro"],
            GRUPOS["carroceria"],
            cerrado=True,
        )

        # Esquinero envolvente curvo (|y| = 0.718 -> 0.826, x = 1.99 -> 1.846) cerrando limpio con la aleta
        estaciones_esq = [
            (x_nariz_frontal(0.718) + 0.004, 0.718, 0.596, 0.734),
            (x_nariz_frontal(0.758) + 0.006, 0.758, 0.596, 0.731),
            (1.948, 0.800, 0.600, 0.722),
            (1.892, 0.820, 0.608, 0.710),
            (1.846, 0.827, 0.622, 0.696),
        ]
        filas_esq = []
        for ie, (xx, yy, z0, z1) in enumerate(estaciones_esq):
            ue = ie / (len(estaciones_esq) - 1)
            fila_e = []
            for k in range(7):
                ve = k / 6
                zz = z0 * (1 - ve) + z1 * ve
                bombeo = 0.008 * math.sin(math.pi * ve) * math.sin(math.pi * (1.0 - 0.5 * ue))
                fila_e.append((xx + bombeo * 0.6, signo * (yy + bombeo * 0.5), zz))
            filas_esq.append(fila_e)
        esq = crear_superficie_grid("Piloto esquina curvo", filas_esq, M["ambar"], GRUPOS["decoracion"], invertir=(signo < 0))
        solidificar(esq, espesor=0.010, offset=-1.0)


def construir_parachoques_3d(nombre, es_delantero):
    """Parachoques volumétrico 3D: repisa superior entrante, barra/cojín sobresaliente y faldón inferior recogido."""
    x_arco = 1.482 if es_delantero else -1.522
    x_punta = 2.165 if es_delantero else -2.165
    rad_plan = 0.255 if es_delantero else 0.225
    ancho_punta = 0.838
    ancho_arco = semiancho_barril(x_arco, 0.50) + 0.008

    # Barrido suave de 45 estaciones alrededor del frente o la cola
    ruta_xy = []
    x_ini_curva = x_punta - rad_plan if es_delantero else x_punta + rad_plan
    for s in range(8):
        t = s / 7
        xx = x_arco + (x_ini_curva - x_arco) * t
        yy = -(ancho_arco * (1 - t) + ancho_punta * t)
        ruta_xy.append((xx, yy))
    for s in range(1, 12):
        ang = -math.pi / 2 + (math.pi / 2) * (s / 11)
        xx = x_ini_curva + (rad_plan if es_delantero else -rad_plan) * math.cos(ang)
        yy = -(ancho_punta - rad_plan) + rad_plan * math.sin(ang)
        ruta_xy.append((xx, yy))
    y_recto = ancho_punta - rad_plan
    for s in range(1, 14):
        u = -1.0 + 2.0 * (s / 14)
        yy = u * y_recto
        bombeo = 0.038 * (1.0 - u * u)
        xx = x_punta + (bombeo if es_delantero else -bombeo)
        ruta_xy.append((xx, yy))
    for s in range(12):
        ang = (math.pi / 2) * (s / 11)
        xx = x_ini_curva + (rad_plan if es_delantero else -rad_plan) * math.cos(ang)
        yy = (ancho_punta - rad_plan) + rad_plan * math.sin(ang)
        ruta_xy.append((xx, yy))
    for s in range(1, 8):
        t = s / 7
        xx = x_ini_curva + (x_arco - x_ini_curva) * t
        yy = ancho_punta * (1 - t) + ancho_arco * t
        ruta_xy.append((xx, yy))

    # Sección vertical esculpida con volumen 3D real:
    # repisa interior -> labio superior curvo -> cojín sobresaliente -> hendidura -> faldón inferior recogido (-9.5 cm)
    if es_delantero:
        perfil_sz = [
            (0.242, -0.098),  # retorno inferior bajo el radiador
            (0.268, -0.056),  # faldón bajo recogido (tuck-under)
            (0.325, -0.024),
            (0.395, -0.002),  # plano inclinado de intermitentes y matrícula
            (0.458, +0.010),
            (0.474, +0.003),  # hendidura horizontal característica de moldura
            (0.488, +0.016),
            (0.516, +0.022),  # máxima proyección del cojín del parachoques
            (0.542, +0.010),  # hombro superior redondeado
            (0.554, -0.018),  # repisa horizontal superior bajo faros/aletas
            (0.550, -0.052),  # cierre interior
        ]
    else:
        perfil_sz = [
            (0.252, -0.095),  # retorno inferior hacia escape/rueda de auxilio
            (0.280, -0.052),  # faldón trasero recogido
            (0.350, -0.018),
            (0.425, +0.005),
            (0.472, +0.004),  # hendidura horizontal
            (0.488, +0.018),
            (0.518, +0.024),  # cojín trasero sobresaliente
            (0.542, +0.010),  # hombro redondeado de carga
            (0.552, -0.022),  # repisa bajo portón y pilotos
            (0.546, -0.055),
        ]

    filas_b = []
    for idx, (px, py) in enumerate(ruta_xy):
        p_ant = ruta_xy[max(0, idx - 1)]
        p_sig = ruta_xy[min(len(ruta_xy) - 1, idx + 1)]
        tx, ty = p_sig[0] - p_ant[0], p_sig[1] - p_ant[1]
        tl = max(1e-6, math.hypot(tx, ty))
        nx, ny = (ty / tl, -tx / tl) if es_delantero else (-ty / tl, tx / tl)

        # En los costados hacia el paso de rueda, el saliente del cojín se funde suavemente con la aleta
        dist_frente = abs(px - x_arco) / max(0.2, abs(x_punta - x_arco))
        escala_sal = 0.35 + 0.65 * sstep(dist_frente * 1.25)
        # Ligera subida del borde inferior en las esquinas para dejar lucir la banda de los neumáticos en vista frontal/trasera
        subida_esq = 0.024 * math.exp(-(((abs(py) - 0.72) / 0.16) ** 2))

        fila = []
        for z_base, sal in perfil_sz:
            zz = z_base
            if z_base < 0.36:
                zz += subida_esq * (1.0 - (z_base - 0.24) / 0.12)
            if not es_delantero and z_base > 0.49 and abs(py) < 0.56:
                zz -= 0.018 * (1.0 - (abs(py) / 0.56) ** 4)
            s_eff = sal * (escala_sal if sal > 0 else 1.0)
            fila.append((px + nx * s_eff, py + ny * s_eff, zz))
        filas_b.append(fila)

    # El perfil_sz ya incluye retorno superior e inferior completo: no duplicar caras internas ocultas
    crear_superficie_grid(nombre, filas_b, M["parachoques"], GRUPOS["carroceria"], invertir=(not es_delantero))
    return ruta_xy


def construir_detalles_parachoques_delantero(ruta_del):
    frente_pts = sorted([(abs(py), px) for px, py in ruta_del if px > 1.90 and py >= 0], key=lambda t: t[0])
    dedup = []
    for yy, xx in frente_pts:
        if not dedup or yy - dedup[-1][0] > 0.015:
            dedup.append((yy, xx))

    def x_cara_bumper(y_abs):
        return interpolar_hermite(dedup, y_abs)

    # Intermitentes horizontales redondeados empotrados bajo la moldura del parachoques
    for signo in (-1, 1):
        ys_i = [0.495 + (0.735 - 0.495) * i / 8 for i in range(9)]
        filas_marco, filas_ambar = [], []
        for i, yy in enumerate(ys_i):
            ui = i / 8
            xp = x_cara_bumper(yy)
            rec = 0.008 * (1.0 - math.sin(math.pi * ui))
            z0 = 0.408 + rec
            z1 = 0.456 - rec
            zm = 0.5 * (z0 + z1)
            abomb = 0.007 * math.sin(math.pi * ui)
            filas_marco.append([(xp + 0.004, signo * yy, z0 - 0.005), (xp + 0.004, signo * yy, z1 + 0.005)])
            filas_ambar.append([
                (xp + 0.008, signo * yy, z0),
                (xp + 0.013 + abomb, signo * yy, zm),
                (xp + 0.008, signo * yy, z1),
            ])
        mc = crear_superficie_grid("Cuenco intermitente parachoques", filas_marco, M["oscuro"], GRUPOS["carroceria"], invertir=(signo < 0))
        solidificar(mc, espesor=0.008)
        la = crear_superficie_grid("Lente ambar parachoques", filas_ambar, M["ambar"], GRUPOS["decoracion"], invertir=(signo < 0))
        solidificar(la, espesor=0.006)

        # Tomas laterales bajas redondeadas en el faldón recogido
        xp_t = x_cara_bumper(0.56) - 0.022
        toma_l = crear_caja("Boca lateral faldon", (xp_t, signo * 0.56, 0.322), (0.028, 0.175, 0.056), M["oscuro"], GRUPOS["carroceria"])
        toma_l.rotation_euler.z = signo * -0.18
        suavizar_subsurf(toma_l, niveles=2)

    # Toma de aire central inferior con esquinas redondeadas + travesaño curvo + matrícula
    boca_c = crear_caja("Toma aire central faldon", (2.152, 0.0, 0.338), (0.036, 0.88, 0.098), M["oscuro"], GRUPOS["carroceria"])
    suavizar_subsurf(boca_c, niveles=2)
    ys_trav = [-0.42 + 0.84 * i / 12 for i in range(13)]
    crear_tubo(
        "Lama toma inferior",
        [(x_cara_bumper(abs(y)) - 0.012, y, 0.340) for y in ys_trav],
        0.009,
        M["parachoques"],
        GRUPOS["carroceria"],
    )
    portaplaca = crear_caja("Portaplaca delantero", (2.192, 0.0, 0.365), (0.026, 0.345, 0.162), M["oscuro"], GRUPOS["decoracion"], bisel=0.014)
    crear_caja("Matricula delantera", (2.206, 0.0, 0.365), (0.009, 0.315, 0.138), M["placa"], GRUPOS["decoracion"], bisel=0.008)


def construir_trasera_organica():
    """Portón trasero abombado en 3D continuo, luneta redondeada y pilotos envolventes abombados."""
    construir_parachoques_3d("Parachoques trasero 3D", es_delantero=False)

    # 1. Chapa inferior abombada del portón trasero (Z = 0.542..0.962, curvada en alzado y en planta, con cuenco suave de matrícula)
    zs_p = [0.542 + (0.962 - 0.542) * i / 16 for i in range(17)]
    us_p = [-1.0 + 2.0 * j / 24 for j in range(25)]
    filas_porton = []
    for z in zs_p:
        x_base = x_perfil_porton(z)
        ancho = 0.656
        fila = []
        for u in us_p:
            y = u * ancho
            # Curvatura horizontal en barril (+4.2 cm en el centro respecto a los costados)
            bombeo_planta = -0.042 * (1.0 - u * u)
            # Cuenco trapezoidal suavemente rehundido para la matrícula (|y| < 0.27, z in 0.65..0.84)
            wy = sstep((0.275 - abs(y)) / 0.045)
            wz = sstep((z - 0.645) / 0.035) * sstep((0.842 - z) / 0.035)
            hundimiento = 0.026 * wy * wz
            fila.append((x_base + bombeo_planta + hundimiento, y, z))
        filas_porton.append(fila)

    crear_superficie_grid("Porton trasero abombado", filas_porton, M["carroceria"], GRUPOS["carroceria"], invertir=False)

    # Moldura visera redondeada sobre la matrícula + placa + emblema y cerradura
    ys_vis = [-0.26 + 0.52 * i / 12 for i in range(13)]
    crear_tubo(
        "Visera cuenco matricula",
        [(x_perfil_porton(0.842) - 0.042 * (1.0 - (y / 0.68) ** 2) - 0.008, y, 0.842) for y in ys_vis],
        0.013,
        M["carroceria"],
        GRUPOS["carroceria"],
    )
    x_pl = x_perfil_porton(0.742) - 0.042 + 0.022
    crear_caja("Marco matricula trasera", (x_pl - 0.004, 0.0, 0.740), (0.014, 0.335, 0.150), M["oscuro"], GRUPOS["decoracion"], bisel=0.010)
    crear_caja("Matricula trasera", (x_pl - 0.011, 0.0, 0.740), (0.009, 0.310, 0.132), M["placa"], GRUPOS["decoracion"], bisel=0.006)
    crear_cilindro("Bombin porton", (x_perfil_porton(0.600) - 0.044, 0.0, 0.600), 0.009, 0.012, M["oscuro"], GRUPOS["decoracion"], eje="X", lados=14)

    x_emb_t = x_perfil_porton(0.905) - 0.045
    pts_emb_t = [(x_emb_t, 0.038 * math.cos(math.tau * i / 28), 0.905 + 0.030 * math.sin(math.tau * i / 28)) for i in range(28)]
    crear_tubo("Emblema trasero aro", pts_emb_t, 0.005, M["cromo"], GRUPOS["decoracion"], cerrado=True)
    crear_tubo("Emblema trasero barra", [(x_emb_t - 0.002, -0.036, 0.905), (x_emb_t - 0.002, 0.036, 0.905)], 0.0045, M["cromo"], GRUPOS["decoracion"])

    # 2. Luneta trasera curvada en 3D siguiendo exactamente `x_perfil_porton(z)` con esquinas redondeadas
    filas_lt = []
    for i in range(13):
        v = i / 12
        z = 0.965 + (1.422 - 0.965) * v
        x_lat = x_perfil_porton(z) + 0.028
        ancho = semiancho_barril(-1.85, z) - 0.048
        bombeo_x = -0.048 * (1.0 - 0.20 * v)
        fila = []
        for j in range(21):
            u = -1.0 + 2.0 * j / 20
            rec_z = -0.020 * (u ** 6) if v > 0.82 else (0.012 * (u ** 6) if v < 0.12 else 0.0)
            y = u * ancho
            x = x_lat + bombeo_x * (1.0 - u * u)
            fila.append((x, y, z + rec_z))
        filas_lt.append(fila)

    lt = crear_superficie_grid("Luneta trasera curva", filas_lt, M["vidrio"], GRUPOS["cristales"], invertir=True)
    solidificar(lt, espesor=0.006)

    perim_lt = (
        filas_lt[0]
        + [filas_lt[i][-1] for i in range(1, 13)]
        + list(reversed(filas_lt[-1][:-1]))
        + [filas_lt[i][0] for i in range(11, 0, -1)]
    )
    crear_tubo(
        "Burlete luneta trasera",
        [(x - 0.004, y, z) for x, y, z in perim_lt],
        0.015,
        M["goma"],
        GRUPOS["carroceria"],
        cerrado=True,
    )

    # Corona superior curva del portón enlazando con la bóveda del techo sin arista dura
    filas_cor = [
        [(x + 0.002, y * 1.02, z - 0.004) for x, y, z in filas_lt[-1]],
        [(x + 0.032, y * 1.01, z + 0.018) for x, y, z in filas_lt[-1]],
        [(x + 0.072, y * 0.99, z + 0.028) for x, y, z in filas_lt[-1]],
    ]
    cor = crear_superficie_grid("Corona superior porton", filas_cor, M["carroceria"], GRUPOS["carroceria"], invertir=True)
    solidificar(cor, espesor=0.016)

    # Limpiaparabrisas trasero apoyado sobre la curva de la luneta
    xb_l = x_perfil_porton(0.975) - 0.022
    crear_tubo("Brazo limpialuneta", [(xb_l - 0.008, 0.02, 0.968), (xb_l + 0.006, -0.22, 0.998)], 0.0065, M["oscuro"], GRUPOS["decoracion"])
    crear_tubo("Escobilla limpialuneta", [(xb_l + 0.002, -0.06, 0.995), (xb_l + 0.014, -0.38, 1.002)], 0.008, M["goma"], GRUPOS["decoracion"])

    # 3. Montantes curvos de esquina trasera y pilotos verticales abombados de 3 colores
    for signo in (-1, 1):
        # Montante curvo que abraza desde el pilar D hasta el borde lateral de la luneta
        filas_m = []
        for i in range(11):
            v = i / 10
            z = 0.945 + (1.422 - 0.945) * v
            x_int = x_perfil_porton(z) + 0.024
            y_int = semiancho_barril(-1.85, z) - 0.048
            x_ext = -2.005 * (1 - v) + (-1.705) * v + 0.028 * math.sin(math.pi * v)
            y_ext = semiancho_barril(x_ext, z)
            filas_m.append([
                (x_int, signo * y_int, z),
                (0.5 * (x_int + x_ext) - 0.008, signo * (0.5 * (y_int + y_ext) + 0.006), z),
                (x_ext, signo * y_ext, z),
            ])
        mont = crear_superficie_grid("Montante curvo esquina trasera", filas_m, M["carroceria"], GRUPOS["carroceria"], invertir=(signo < 0))
        solidificar(mont, espesor=0.016)

        # Faja blanca suave sobre el piloto trasero (Z = 0.926..0.952) cerrando con el pilar D
        pts_faja = [
            (-1.900, signo * semiancho_barril(-1.90, 0.926), 0.926),
            (-2.012, signo * 0.785, 0.926),
            (-2.036, signo * 0.655, 0.928),
            (-2.030, signo * 0.655, 0.956),
            (-2.005, signo * 0.782, 0.954),
            (-1.900, signo * semiancho_barril(-1.90, 0.952), 0.952),
        ]
        crear_panel("Faja curva sobre piloto", pts_faja, M["carroceria"], GRUPOS["carroceria"], espesor=0.016)

        # Curva envolvente del piloto trasero con lente convexa almohadillada
        estaciones_pil = [
            (-2.040, 0.652),
            (-2.036, 0.710),
            (-2.022, 0.768),
            (-1.985, 0.808),
            (-1.938, 0.822),
            (-1.900, 0.826),
        ]

        def bloque_piloto(nombre_b, z0, z1, mat_b, i0=0, i1=5, abomb=0.009):
            tramo = estaciones_pil[i0 : i1 + 1]
            filas_pl = []
            for idx, (xx, yy) in enumerate(tramo):
                u = idx / max(1, len(tramo) - 1)
                # Seguir la ligera inclinación de x_perfil_porton(z)
                dx_z0 = (x_perfil_porton(z0) - x_perfil_porton(0.75)) * (1.0 - 0.6 * u)
                dx_z1 = (x_perfil_porton(z1) - x_perfil_porton(0.75)) * (1.0 - 0.6 * u)
                fila = []
                for k in range(5):
                    v = k / 4
                    zz = z0 * (1 - v) + z1 * v
                    dxx = dx_z0 * (1 - v) + dx_z1 * v
                    almohada = abomb * math.sin(math.pi * v) * (0.4 + 0.6 * math.sin(math.pi * (idx + 0.5) / len(tramo)))
                    fila.append((xx + dxx - almohada * 0.75, signo * (yy + almohada * 0.55), zz))
                filas_pl.append(fila)
            padre_dest = GRUPOS["carroceria"] if mat_b == M["oscuro"] else GRUPOS["decoracion"]
            m = crear_superficie_grid(nombre_b, filas_pl, mat_b, padre_dest, invertir=(signo > 0))
            solidificar(m, espesor=0.012, offset=-1.0)

        bloque_piloto("Carcasa piloto trasero", 0.548, 0.930, M["oscuro"], 0, 5, abomb=0.002)
        bloque_piloto("Piloto ambar superior", 0.822, 0.922, M["ambar"], 0, 5, abomb=0.010)
        bloque_piloto("Piloto rojo central", 0.668, 0.816, M["rojo"], 0, 5, abomb=0.011)
        bloque_piloto("Luz blanca reversa", 0.556, 0.662, M["faro"], 0, 2, abomb=0.009)
        bloque_piloto("Piloto rojo inferior esquina", 0.556, 0.662, M["rojo"], 2, 5, abomb=0.010)

    # Escape trasero derecho
    crear_cilindro("Silenciador oculto", (-1.76, -0.44, 0.305), 0.045, 0.24, M["oscuro"], GRUPOS["interior"], eje="X", lados=14)
    crear_tubo("Cola escape", [(-1.88, -0.44, 0.265), (-2.11, -0.44, 0.222)], 0.020, M["llanta"], GRUPOS["interior"])


def construir_interior_organico():
    """Interior sobrio con asientos y salpicadero suavizados por subdivisión."""
    crear_caja("Piso habitaculo", (0.05, 0.0, 0.295), (1.88, 1.32, 0.045), M["interior"], GRUPOS["interior"], bisel=0.01)
    crear_caja("Piso maletero", (-1.30, 0.0, 0.535), (1.28, 1.22, 0.05), M["interior"], GRUPOS["interior"], bisel=0.01)

    salp = crear_caja("Salpicadero curvo", (0.72, 0.0, 0.855), (0.36, 1.38, 0.19), M["interior"], GRUPOS["interior"])
    suavizar_subsurf(salp, niveles=2)
    capilla = crear_caja("Capilla instrumentos", (0.67, 0.34, 0.960), (0.20, 0.36, 0.095), M["oscuro"], GRUPOS["interior"])
    suavizar_subsurf(capilla, niveles=2)

    crear_tubo("Columna direccion", [(0.65, 0.34, 0.84), (0.44, 0.34, 0.945)], 0.023, M["oscuro"], GRUPOS["interior"])
    centro_vol = Vector((0.43, 0.34, 0.95))
    u_v, v_v = Vector((0.062, 0.0, 0.150)), Vector((0.0, 0.168, 0.0))
    aro = [tuple(centro_vol + u_v * math.cos(math.tau * i / 28) + v_v * math.sin(math.tau * i / 28)) for i in range(28)]
    crear_tubo("Aro volante", aro, 0.015, M["goma"], GRUPOS["interior"], cerrado=True)
    for ang in (0.0, math.pi * 0.82, -math.pi * 0.82):
        crear_tubo("Radio volante", [tuple(centro_vol), tuple(centro_vol + u_v * math.cos(ang) + v_v * math.sin(ang))], 0.011, M["oscuro"], GRUPOS["interior"])

    crear_tubo("Soporte espejo interior", [(0.33, 0.0, 1.435), (0.36, 0.0, 1.365)], 0.0065, M["oscuro"], GRUPOS["interior"])
    esp_i = crear_caja("Espejo interior cabina", (0.36, 0.0, 1.355), (0.022, 0.180, 0.046), M["oscuro"], GRUPOS["interior"])
    suavizar_subsurf(esp_i, niveles=1)

    for nombre_as, y_as in [("Asiento conductor", 0.34), ("Asiento acompanante", -0.34)]:
        coj = crear_caja(nombre_as + " cojin", (0.14, y_as, 0.49), (0.46, 0.45, 0.12), M["tapizado"], GRUPOS["interior"])
        suavizar_subsurf(coj, niveles=1)
        resp = crear_caja(nombre_as + " respaldo", (-0.06, y_as, 0.80), (0.12, 0.43, 0.53), M["tapizado"], GRUPOS["interior"])
        resp.rotation_euler.y = -0.18
        suavizar_subsurf(resp, niveles=1)
        cab = crear_caja(nombre_as + " apoyacabezas", (-0.12, y_as, 1.125), (0.085, 0.21, 0.14), M["interior"], GRUPOS["interior"])
        cab.rotation_euler.y = -0.12
        suavizar_subsurf(cab, niveles=2)

    b_coj = crear_caja("Banqueta trasera cojin", (-0.56, 0.0, 0.52), (0.44, 1.18, 0.12), M["tapizado"], GRUPOS["interior"])
    suavizar_subsurf(b_coj, niveles=1)
    b_resp = crear_caja("Banqueta trasera respaldo", (-0.77, 0.0, 0.82), (0.12, 1.16, 0.49), M["tapizado"], GRUPOS["interior"])
    b_resp.rotation_euler.y = -0.16
    suavizar_subsurf(b_resp, niveles=1)
    for y_cab in (-0.34, 0.34):
        cab_t = crear_caja("Apoyacabezas trasero", (-0.82, y_cab, 1.115), (0.080, 0.21, 0.13), M["interior"], GRUPOS["interior"])
        suavizar_subsurf(cab_t, niveles=2)


def construir_ruedas():
    medio_neumatico = [
        (0.190, -0.078),
        (0.208, -0.092),
        (0.246, -0.098),  # flanco bien abombado de neumático radial clásico
        (0.284, -0.091),
        (0.307, -0.076),
        (0.317, -0.058),
        (0.320, -0.044),
        (0.314, -0.038),
        (0.320, -0.031),
        (0.320, -0.011),
        (0.314, -0.005),
        (0.320, -0.001),
    ]
    perfil_neumatico = medio_neumatico + [(r, -d) for r, d in reversed(medio_neumatico)]

    perfil_llanta = [
        (0.042, 0.066),
        (0.074, 0.068),
        (0.096, 0.054),
        (0.122, 0.048),
        (0.152, 0.050),
        (0.174, 0.070),
        (0.188, 0.082),
        (0.197, 0.084),
        (0.200, 0.074),
        (0.200, 0.044),
        (0.186, 0.038),
        (0.170, 0.054),
        (0.150, 0.036),
        (0.120, 0.034),
        (0.094, 0.040),
        (0.072, 0.054),
        (0.042, 0.052),
    ]

    construir_ruedas_volumetricas(
        datos=D,
        materiales=M,
        grupos=GRUPOS,
        perfil_neumatico=perfil_neumatico,
        perfil_llanta=perfil_llanta,
        segmentos_neumatico=40,
        segmentos_llanta=40,
        dibujo_banda=(0.312, 0.064, 0.0022),
        n_ventilaciones=9,
        radio_ventilaciones=0.136,
        radio_agujero=0.0165,
        desp_agujero=0.050,
        n_tuercas=4,
        radio_tuercas=0.055,
        radio_buje=0.034,
        desp_buje=0.068,
    )


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    crear_materiales()
    GRUPOS.update(inicializar_jerarquia(D["id"]))

    construir_flancos_organicos()
    construir_techo_e_invernadero_curvo()
    construir_capo_y_frente_organico()
    ruta_del = construir_parachoques_3d("Parachoques delantero 3D", es_delantero=True)
    construir_detalles_parachoques_delantero(ruta_del)
    construir_trasera_organica()
    construir_interior_organico()
    construir_ruedas()

    bpy.context.view_layer.update()
    consolidar_lotes(
        raiz=GRUPOS["raiz"],
        nombres_mat_con_uv=(M["neumatico"].name,),
        nombre_mat_llanta=M["llanta"].name,
    )
    bpy.context.view_layer.update()

    reporte = validar_geometria_vehiculo(
        raiz=GRUPOS["raiz"],
        datos=D,
        ruta_ficha=SALIDA / f"{D['id']}.ficha.json",
        info_extra={
            "acabados": D["acabados"],
            "normal_goma": {
                "archivo": D["acabados"]["textura_goma"],
                "fuente": "https://ambientcg.com/view?id=Rubber004",
                "licencia": "CC0 1.0",
            },
        },
    )
    print("VAGONETA_VALIDACION", json.dumps(reporte, ensure_ascii=False), flush=True)

    preparar_rig_y_clips(D, GRUPOS)
    exportar_glb_vehiculo(GRUPOS["raiz"], SALIDA / f"{D['id']}.glb")

    sin_render = "--sin-render" in sys.argv
    vistas_arg = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--vistas=")), None)
    configurar_estudio_y_renderizar(
        raiz=GRUPOS["raiz"],
        datos=D,
        ruta_blend=SALIDA / f"{D['id']}.blend",
        carpeta_renders=REVISION,
        vistas_pedidas=vistas_arg,
        ruta_referencia=DIRECTORIO / D["referencia"],
        sin_render=sin_render,
    )


if __name__ == "__main__":
    main()
