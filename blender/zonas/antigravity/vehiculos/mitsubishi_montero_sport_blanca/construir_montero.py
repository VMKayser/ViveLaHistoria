"""Construcción 3D orgánica en Blender de la Mitsubishi Montero Sport Blanca (`02_mitsubishi_montero_sport_blanca`).

Usa la skill `vehiculo-3d-desde-diseno` (`kit_vehiculo_bpy.py`) con superficies curvas continuas 3D:
- Frente Dynamic Shield esculpido: capó alto abovedado, parrilla negra superior con emblema 3D de tres diamantes,
  faros superiores afilados, perfiles cromados envolventes en boomerang, nichos verticales inferiores de 3 ópticas
  y protector inferior plateado (skid plate) con ángulo de ataque todoterreno.
- Cuerpo SUV monocasco en barril: pasos de rueda musculosos blancos con labio interior, estribos laterales plateados,
  cintura ascendente con tercer cristal en punta y listón cromado, techo bicolor con barras negras, espejos cromados
  subdivididos y alerón trasero integrado.
- Trasera esculpida: pilotos verticales tipo lágrima, portón abombado con moldura cromada, difusor plateado con
  reflectores rojos y diferencial/puente trasero visible bajo el chasis.
- Ruedas todoterreno con llantas oscuras de aleación de 6 radios dobles (12 ventanas abiertas reales) y 6 tuercas.
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

D = json.loads((DIRECTORIO / "mitsubishi_montero_sport_blanca.json").read_text())
SALIDA = RAIZ / "web" / "public" / "models" / "ciudad" / "antigravity" / "vehiculos" / D["id"]
REVISION = RAIZ / "revisiones" / "antigravity" / D["id"]
SALIDA.mkdir(parents=True, exist_ok=True)
REVISION.mkdir(parents=True, exist_ok=True)

M = {}
GRUPOS = {}

# Cintura ascendente característica de la Montero Sport (sube hacia el pilar D)
PERFIL_CINTURA = [
    (-2.22, 1.385),
    (-1.92, 1.375),
    (-1.45, 1.275),
    (-0.85, 1.235),
    (-0.10, 1.205),
    (0.88, 1.180),
    (1.42, 1.195),
    (1.88, 1.172),
    (2.26, 1.115),
]

PERFIL_CAPO_CENTRO = [
    (0.88, 1.245),
    (1.25, 1.258),
    (1.65, 1.246),
    (2.02, 1.218),
    (2.22, 1.186),
    (2.30, 1.155),
]

PERFIL_TECHO_CIMA = [
    (-1.92, 1.775),
    (-1.68, 1.812),
    (-1.20, 1.826),
    (-0.55, 1.828),
    (0.05, 1.815),
    (0.38, 1.775),
    (0.55, 1.725),
]

PERFIL_RIEL_TECHO = [
    (-1.90, 1.715),
    (-1.55, 1.745),
    (-0.90, 1.758),
    (-0.20, 1.755),
    (0.28, 1.728),
    (0.52, 1.688),
]


def sstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def z_cintura(x):
    return interpolar_hermite(PERFIL_CINTURA, x)


def z_riel_techo(x):
    return interpolar_hermite(PERFIL_RIEL_TECHO, x)


def estrechamiento_planta(x):
    if x >= 0.0:
        t = min(1.0, x / 2.30)
        return 1.0 - 0.072 * (t ** 2.2)
    t = min(1.0, (-x) / 2.28)
    return 1.0 - 0.065 * (t ** 2.1)


def relieve_suv_lateral(x, z):
    """Aletas musculosas tipo Montero Sport + concavidad inferior de puertas sobre el estribo."""
    zc = D["centro_rueda_z"]
    flare = 0.0
    for eje in D["ejes"]:
        dx = x - eje
        dz = max(-0.08, z - zc) * 0.96
        dist = math.hypot(dx, dz)
        # Corona ancha musculosa alrededor de cada rueda (r = 0.49..0.67 m)
        if 0.485 <= dist <= 0.675:
            u = (dist - 0.485) / (0.675 - 0.485)
            # Meseta suave tipo SUV moderno
            pulso = math.sin(math.pi * u) ** 0.85
            flare = max(flare, 0.032 * pulso)

    # Entalle esculpido en el tercio bajo de las puertas (entre arcos) y nervio ascendente superior
    entalle = 0.0
    if -0.72 <= x <= 0.92 and 0.44 <= z <= 0.68:
        ux = sstep((x + 0.72) / 0.12) * sstep((0.92 - x) / 0.12)
        uz = math.sin(math.pi * (z - 0.44) / 0.24)
        entalle = -0.012 * ux * uz

    nervio_sup = 0.0
    z_nerv = 1.04 + 0.06 * ((0.90 - x) / 2.8)
    if -1.95 <= x <= 1.55 and abs(z - z_nerv) < 0.065:
        ux = sstep((x + 1.95) / 0.15) * sstep((1.55 - x) / 0.18)
        uz = math.cos(0.5 * math.pi * (z - z_nerv) / 0.065) ** 2
        nervio_sup = 0.009 * ux * uz

    return flare + entalle + nervio_sup


def semiancho_barril(x, z):
    zc = z_cintura(x)
    zr = z_riel_techo(x)
    esc = estrechamiento_planta(x)
    if z <= zc:
        u = max(0.0, min(1.0, (z - 0.34) / max(0.15, zc - 0.34)))
        perfil_u = [
            (0.00, 0.815),  # zócalo alto recogido sobre el estribo
            (0.12, 0.888),
            (0.38, 0.920),
            (0.65, 0.926),  # hombro ancho de SUV
            (0.88, 0.912),
            (1.00, 0.878),  # hombro redondeado hacia la ventanilla
        ]
        return interpolar_hermite(perfil_u, u) * esc + relieve_suv_lateral(x, z)

    v = max(0.0, min(1.0, (z - zc) / max(0.10, zr - zc)))
    perfil_inv = [
        (0.00, 0.878),
        (0.32, 0.832),
        (0.68, 0.768),
        (1.00, 0.690),
    ]
    return interpolar_hermite(perfil_inv, v) * esc


def x_frente_escudo(y_abs):
    """Planta curva del frente Dynamic Shield."""
    perfil = [
        (0.00, 2.335),
        (0.42, 2.312),
        (0.68, 2.248),
        (0.82, 2.155),
        (0.88, 2.015),
    ]
    return interpolar_hermite(perfil, y_abs)


def x_perfil_porton(z):
    """Alzado continuo del portón trasero SUV."""
    perfil = [
        (0.740, -2.265),
        (0.920, -2.288),
        (1.105, -2.292),  # cresta suave bajo el emblema trasero
        (1.235, -2.258),  # base de la luneta trasera
        (1.450, -2.135),
        (1.650, -2.010),
        (1.755, -1.935),
    ]
    return interpolar_hermite(perfil, z)


def z_borde_inferior_chapa(x):
    """Recorte continuo de estribo alto (z=0.345) y pasos de rueda todoterreno amplios."""
    z_base = 0.345
    z = z_base
    if x < -1.78:
        t = sstep((-1.78 - x) / 0.06)
        z = z_base * (1.0 - t) + 0.685 * t
    elif x > 1.98:
        t = sstep((x - 1.98) / 0.05)
        z = z_base * (1.0 - t) + 0.665 * t

    rx_arco = 0.505
    rz_arco = 0.585  # 0.345 + 0.585 = 0.930 m en la cima del paso de rueda
    for eje in D["ejes"]:
        dx = abs(x - eje)
        if dx < rx_arco:
            u = dx / rx_arco
            # Arco ligeramente trapezoidal suavizado propio de SUV Mitsubishi
            forma = (1.0 - (u ** 2.35)) ** 0.52
            z = max(z, z_base + rz_arco * forma)
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
    M["techo_oscuro"] = material_rol("hierro", c["techo_oscuro"])
    M["parrilla"] = material_rol("hierro", c["parrilla"])
    M["goma"] = material_rol("hierro", c["goma"])
    M["oscuro"] = material_rol("hierro", c["oscuro"])
    M["interior"] = material_rol("hierro", c["interior"])
    M["tapizado"] = material_rol("hierro", c["tapizado"])
    M["llanta"] = material_rol("metal", c["llanta"])
    M["plata"] = material_rol("metal", c["plata"])
    M["cromo"] = material_rol("metal", c["cromo"])
    M["faro"] = material_rol("metal", c["faro"])
    M["ambar"] = material_rol("pintura_acento", c["ambar"])
    M["rojo"] = material_rol("pintura_acento", c["rojo"])
    M["placa"] = material_rol("letrero", c["placa"])

    M["carroceria"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.38
    M["techo_oscuro"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.30
    M["parrilla"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.34
    M["llanta"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.68
    M["llanta"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.32
    M["plata"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.52
    M["plata"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.36
    M["cromo"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.86
    M["cromo"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.16
    M["faro"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.14
    M["rojo"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.20

    M["vidrio"] = material_rol("vidrio", c["vidrio"])
    bs_v = M["vidrio"].node_tree.nodes["Principled BSDF"]
    bs_v.inputs["Alpha"].default_value = 0.38
    bs_v.inputs["Roughness"].default_value = 0.14
    M["vidrio"].diffuse_color = (*M["vidrio"].diffuse_color[:3], 0.38)
    M["vidrio"].surface_render_method = "DITHERED"
    M["vidrio"].use_transparent_shadow = True

    M["lente_claro"] = material_rol("vidrio", "#dfe7f2")
    bs_l = M["lente_claro"].node_tree.nodes["Principled BSDF"]
    bs_l.inputs["Alpha"].default_value = 0.44
    bs_l.inputs["Roughness"].default_value = 0.10
    M["lente_claro"].diffuse_color = (*M["lente_claro"].diffuse_color[:3], 0.44)
    M["lente_claro"].surface_render_method = "DITHERED"

    M["neumatico"] = material_rol("hierro", "#27262a")
    configurar_normal_goma(M["neumatico"], DIRECTORIO / D["acabados"]["textura_goma"], D["acabados"]["normal_goma_intensidad"])


def construir_emblema_tres_diamantes(x_pos, z_centro, escala, hacia_frente=True):
    """Construye en geometría real los 3 rombos Mitsubishi a 120°."""
    signo_x = 1.0 if hacia_frente else -1.0
    largo_d = 0.048 * escala
    ancho_d = 0.024 * escala
    for ang_grados in (90.0, 210.0, 330.0):
        ang = math.radians(ang_grados)
        uy, uz = math.cos(ang), math.sin(ang)
        ny, nz = -uz, uy
        p0 = (x_pos, 0.0, z_centro)
        p1 = (x_pos + signo_x * 0.003, 0.5 * largo_d * uy + 0.5 * ancho_d * ny, z_centro + 0.5 * largo_d * uz + 0.5 * ancho_d * nz)
        p2 = (x_pos + signo_x * 0.002, largo_d * uy, z_centro + largo_d * uz)
        p3 = (x_pos + signo_x * 0.003, 0.5 * largo_d * uy - 0.5 * ancho_d * ny, z_centro + 0.5 * largo_d * uz - 0.5 * ancho_d * nz)
        crear_panel("Rombo emblema", [p0, p1, p2, p3], M["cromo"], GRUPOS["decoracion"], espesor=0.006)


def construir_flancos_y_estribos():
    xs_brutos = sorted(
        {-2.10 + (2.00 - (-2.10)) * i / 48 for i in range(49)}
        | {eje - 0.52 + 1.04 * i / 28 for eje in D["ejes"] for i in range(29)}
    )
    xs = []
    for x in xs_brutos:
        if -2.101 <= x <= 2.001 and (not xs or x - xs[-1] >= 0.015):
            xs.append(round(x, 5))
    if xs[-1] < 1.999:
        xs.append(2.000)

    us_z = [0.0, 0.05, 0.14, 0.26, 0.38, 0.52, 0.66, 0.78, 0.88, 0.95, 1.0]

    for signo in (-1, 1):
        filas = []
        for x in xs:
            zb = z_borde_inferior_chapa(x)
            zt = z_cintura(x)
            yb = semiancho_barril(x, zb)
            fila = [
                (x, signo * (yb - 0.042), zb + 0.010),
                (x, signo * (yb - 0.016), zb + 0.001),
                (x, signo * (yb - 0.003), zb - 0.002),
            ]
            for u in us_z:
                z = zb + (zt - zb) * u
                fila.append((x, signo * semiancho_barril(x, z), z))
            yt = semiancho_barril(x, zt)
            fila.append((x, signo * (yt - 0.014), zt + 0.006))
            fila.append((x, signo * (yt - 0.030), zt + 0.003))
            filas.append(fila)

        crear_superficie_grid(
            f"Flanco SUV {'izq' if signo > 0 else 'der'}",
            filas,
            M["carroceria"],
            GRUPOS["carroceria"],
            invertir=(signo > 0),
        )

        # Estribos laterales integrados (puntas blancas moldeadas + plataforma plateada con goma antideslizante)
        crear_caja(
            "Plataforma estribo plateado",
            (0.11, signo * 0.885, 0.308),
            (1.66, 0.115, 0.042),
            M["plata"],
            GRUPOS["carroceria"],
            bisel=0.012,
        )
        crear_caja(
            "Pisadera negra estribo",
            (0.11, signo * 0.902, 0.331),
            (1.48, 0.072, 0.010),
            M["goma"],
            GRUPOS["decoracion"],
            bisel=0.004,
        )
        for x_punta in (-0.71, 0.93):
            punta = crear_caja(
                "Puntera blanca estribo",
                (x_punta, signo * 0.892, 0.322),
                (0.16, 0.118, 0.068),
                M["carroceria"],
                GRUPOS["carroceria"],
            )
            suavizar_subsurf(punta, niveles=2)

        # Líneas de cierre de puertas laterales
        for nombre_j, xj, z_ini in [
            ("Junta puerta delantera", 0.94, 0.38),
            ("Junta pilar B", -0.06, 0.36),
            ("Junta puerta trasera", -0.82, 0.72),
        ]:
            zt = z_cintura(xj) - 0.008
            pts_j = [(xj, signo * (semiancho_barril(xj, z) + 0.002), z) for z in [z_ini + (zt - z_ini) * s / 8 for s in range(9)]]
            crear_tubo(nombre_j, pts_j, 0.0028, M["oscuro"], GRUPOS["decoracion"], resolucion=1)

        # Manillas horizontales cromadas con cuenco suave (4 puertas)
        for nombre_m, xm, zm in [("Manilla delantera", 0.10, 1.105), ("Manilla trasera", -0.68, 1.135)]:
            ym = signo * semiancho_barril(xm, zm)
            cuenco = crear_caja(nombre_m + " cuenco", (xm, ym + signo * 0.002, zm), (0.155, 0.016, 0.056), M["oscuro"], GRUPOS["decoracion"])
            suavizar_subsurf(cuenco, niveles=2)
            tirador = crear_caja(nombre_m + " tirador", (xm, ym + signo * 0.012, zm + 0.004), (0.145, 0.022, 0.034), M["cromo"], GRUPOS["decoracion"])
            suavizar_subsurf(tirador, niveles=2)

        # Bóveda interior oscura de pasos de rueda + faldillas guardabarros traseras
        for ie, eje in enumerate(D["ejes"]):
            arco_int = [
                (eje + 0.495 * math.cos(math.pi * s / 24), D["centro_rueda_z"] + 0.495 * math.sin(math.pi * s / 24))
                for s in range(25)
            ]
            y_ext = signo * 0.855
            y_int = signo * 0.625
            filas_bov = [[(xx, y_int, zz), (xx, y_ext, zz)] for xx, zz in arco_int]
            bov = crear_superficie_grid("Boveda paso rueda", filas_bov, M["oscuro"], GRUPOS["interior"], invertir=(signo < 0))
            solidificar(bov, espesor=0.014)
            crear_panel(
                "Fondo paso rueda",
                [(xx, y_int, zz) for xx, zz in arco_int] + [(eje - 0.495, y_int, 0.34), (eje + 0.495, y_int, 0.34)],
                M["oscuro"],
                GRUPOS["interior"],
                espesor=0.012,
            )
            if ie == 0:
                faldilla = crear_caja("Faldilla trasera", (eje - 0.485, signo * 0.845, 0.365), (0.035, 0.16, 0.16), M["goma"], GRUPOS["carroceria"])
                suavizar_subsurf(faldilla, niveles=1)

    # Chasis largueros + puente trasero y diferencial visible en vista trasera (fiel a la lámina)
    crear_caja("Bastidor largueros SUV", (0.10, 0.0, 0.375), (3.85, 1.24, 0.085), M["oscuro"], GRUPOS["interior"], bisel=0.02)
    crear_cilindro("Eje delantero", (D["ejes"][1], 0.0, D["centro_rueda_z"]), 0.042, 1.48, M["oscuro"], GRUPOS["interior"], eje="Y", lados=16)
    crear_cilindro("Puente rigido trasero", (D["ejes"][0], 0.0, 0.365), 0.046, 1.48, M["oscuro"], GRUPOS["interior"], eje="Y", lados=18)
    bocha = crear_caja("Diferencial trasero", (D["ejes"][0] - 0.04, 0.0, 0.345), (0.24, 0.25, 0.21), M["oscuro"], GRUPOS["interior"])
    suavizar_subsurf(bocha, niveles=2)
    for signo in (-1, 1):
        crear_tubo(
            "Brazo suspension trasera",
            [(D["ejes"][0] - 0.02, signo * 0.52, 0.35), (D["ejes"][0] + 0.42, signo * 0.46, 0.39)],
            0.022,
            M["oscuro"],
            GRUPOS["interior"],
        )


def construir_invernadero_techo_y_barras():
    """Techo bicolor abovedado, barras negras, alerón trasero y ventanillas con 3er cristal ascendente."""
    # 1. Bóveda central oscura del techo (|y| <= 0.58 m) + hombros laterales blancos (cantrails)
    xs_t = [-1.92 + (0.54 - (-1.92)) * i / 28 for i in range(29)]
    us_cen = [-0.78 + 1.56 * j / 16 for j in range(17)]
    filas_techo_osc = []
    for x in xs_t:
        z_cima = interpolar_hermite(PERFIL_TECHO_CIMA, x)
        z_riel = z_riel_techo(x)
        ancho_r = semiancho_barril(x, z_riel)
        fila = []
        for u in us_cen:
            ua = abs(u)
            y = u * ancho_r
            caida = 0.32 * (ua ** 2) + 0.68 * (1.0 - math.sqrt(max(0.0, 1.0 - (ua ** 2.2) * 0.92)))
            z = z_cima - caida * (z_cima - z_riel)
            xx = x - (0.045 * sstep((x - 0.32) / 0.22) * (ua ** 2) if x > 0.32 else 0.0)
            fila.append((xx, y, z))
        filas_techo_osc.append(fila)

    crear_superficie_grid("Techo central bicolor oscuro", filas_techo_osc, M["techo_oscuro"], GRUPOS["carroceria"], invertir=False)
    crear_caja("Tapizado cielo interior", (-0.65, 0.0, 1.695), (2.10, 1.12, 0.018), M["interior"], GRUPOS["interior"], bisel=0.006)

    def punto_barril(x, z, signo, desp=0.0):
        return (x, signo * (semiancho_barril(x, z) + desp), z)

    for signo in (-1, 1):
        # Hombro blanco del techo (entre u=0.76 y u=1.02) que abraza el techo oscuro
        filas_hombro = []
        for x in xs_t:
            z_cima = interpolar_hermite(PERFIL_TECHO_CIMA, x)
            z_riel = z_riel_techo(x)
            ancho_r = semiancho_barril(x, z_riel)
            fila_h = []
            for ua in (0.75, 0.86, 0.95, 1.01):
                y = signo * ua * ancho_r
                caida = 0.32 * (ua ** 2) + 0.68 * (1.0 - math.sqrt(max(0.0, 1.0 - min(0.98, (ua ** 2.2) * 0.92))))
                z = z_cima - caida * (z_cima - (z_riel - 0.008))
                fila_h.append((x, y, z))
            filas_hombro.append(fila_h)
        crear_superficie_grid("Hombro blanco techo", filas_hombro, M["carroceria"], GRUPOS["carroceria"], invertir=(signo < 0))

        # Barras portaequipajes negras longitudinales integradas sobre el techo (z hasta 1.88 m)
        xs_barra = [-1.76 + (0.26 - (-1.76)) * i / 20 for i in range(21)]
        pts_barra = []
        for i, xb in enumerate(xs_barra):
            tb = i / 20
            arco_b = math.sin(math.pi * tb) ** 0.45
            zb_base = interpolar_hermite(PERFIL_TECHO_CIMA, xb) - 0.032
            zb = zb_base + 0.052 * arco_b
            yb = signo * (semiancho_barril(xb, z_riel_techo(xb)) * 0.80)
            pts_barra.append((xb, yb, zb))
        crear_tubo("Barra longitudinal techo", pts_barra, 0.020, M["oscuro"], GRUPOS["decoracion"], resolucion=3)
        for xb_pie in (-1.70, -0.75, 0.18):
            yb_p = signo * (semiancho_barril(xb_pie, z_riel_techo(xb_pie)) * 0.80)
            zb_p = interpolar_hermite(PERFIL_TECHO_CIMA, xb_pie) - 0.015
            pie = crear_caja("Apoyo barra techo", (xb_pie, yb_p, zb_p), (0.14, 0.042, 0.042), M["oscuro"], GRUPOS["decoracion"])
            suavizar_subsurf(pie, niveles=1)

        # Pilar A blanco arqueado y Pilar D blanco musculoso con quiebre ascendente
        def crear_pilar(nombre_p, f_xa, f_xb, z0, z1, mat_p, abomb=0.006, nz=12):
            filas_p = []
            for i in range(nz + 1):
                t = i / nz
                z = z0 + (z1 - z0) * t
                xa, xb = f_xa(t), f_xb(t)
                filas_p.append([
                    punto_barril(xa, z, signo, -0.010),
                    punto_barril(xa + 0.15 * (xb - xa), z, signo, 0.002),
                    punto_barril(0.5 * (xa + xb), z, signo, abomb),
                    punto_barril(xa + 0.85 * (xb - xa), z, signo, 0.002),
                    punto_barril(xb, z, signo, -0.010),
                ])
            return crear_superficie_grid(nombre_p, filas_p, mat_p, GRUPOS["carroceria"], invertir=(signo < 0))

        crear_pilar(
            "Pilar A blanco",
            lambda t: 0.88 * (1 - t) + 0.42 * t + 0.028 * math.sin(math.pi * t),
            lambda t: 0.98 * (1 - t) + 0.52 * t + 0.028 * math.sin(math.pi * t),
            1.175,
            1.705,
            M["carroceria"],
            abomb=0.007,
        )
        crear_pilar(
            "Pilar D blanco SUV",
            lambda t: -2.22 * (1 - t) + (-1.92) * t + 0.024 * math.sin(math.pi * t),
            lambda t: -1.90 * (1 - t) + (-1.68) * t + 0.035 * math.sin(math.pi * t),
            1.365,
            1.725,
            M["carroceria"],
            abomb=0.008,
        )
        # Pilares B y C en negro brillante enrasados con los cristales
        crear_pilar("Pilar B negro", lambda t: -0.10 - 0.03 * t, lambda t: -0.01 - 0.03 * t, 1.205, 1.745, M["parrilla"], abomb=0.002)
        crear_pilar("Pilar C negro", lambda t: -0.88 - 0.04 * t, lambda t: -0.79 - 0.04 * t, 1.235, 1.742, M["parrilla"], abomb=0.002)

        # Tres cristales laterales oscuros (el trasero sube en cuña hacia el pilar D)
        vanos = [
            ("Cristal custodia SUV", [(-1.89, 1.375), (-0.88, 1.240), (-0.92, 1.728), (-1.69, 1.712)], 0.045),
            ("Cristal puerta trasera", [(-0.79, 1.232), (-0.10, 1.205), (-0.13, 1.735), (-0.83, 1.732)], 0.032),
            ("Cristal puerta delantera", [(-0.01, 1.202), (0.88, 1.182), (0.43, 1.698), (-0.04, 1.734)], 0.045),
        ]
        for nombre_v, poli_xz, rad_v in vanos:
            suave_xz = contorno_redondeado(poli_xz, radio=rad_v, pasos=4)
            crear_tubo(
                nombre_v + " marco negro",
                [punto_barril(x, z, signo, -0.002) for x, z in suave_xz],
                0.013,
                M["goma"],
                GRUPOS["carroceria"],
                cerrado=True,
            )
            p0, p1, p2, p3 = poli_xz
            filas_v = []
            for iv in range(7):
                tv = iv / 6
                xa, xb = p0[0] * (1 - tv) + p3[0] * tv, p1[0] * (1 - tv) + p2[0] * tv
                za, zb_v = p0[1] * (1 - tv) + p3[1] * tv, p1[1] * (1 - tv) + p2[1] * tv
                filas_v.append([punto_barril(xa * (1 - iu / 8) + xb * (iu / 8), za * (1 - iu / 8) + zb_v * (iu / 8), signo, -0.009) for iu in range(9)])
            crear_superficie_grid(nombre_v, filas_v, M["vidrio"], GRUPOS["cristales"], invertir=(signo > 0))

        # Listón cromado continuo en la base de las ventanillas que sube y remata la punta del 3er cristal
        pts_cromo_vent = [
            punto_barril(0.84, 1.182, signo, 0.004),
            punto_barril(0.20, 1.196, signo, 0.004),
            punto_barril(-0.45, 1.218, signo, 0.004),
            punto_barril(-0.92, 1.242, signo, 0.004),
            punto_barril(-1.45, 1.305, signo, 0.004),
            punto_barril(-1.91, 1.382, signo, 0.004),
            punto_barril(-1.70, 1.708, signo, 0.003),
        ]
        crear_tubo("Moldura cromada ventanillas", pts_cromo_vent, 0.0085, M["cromo"], GRUPOS["decoracion"])

        # Retrovisor exterior bicolor (base negra + carcasa superior cromada/plata con intermitente)
        tri_esp = contorno_redondeado([(0.70, 1.182), (0.90, 1.180), (0.78, 1.355)], radio=0.022, pasos=3)
        crear_panel("Base espejo SUV", [punto_barril(x, z, signo, 0.002) for x, z in tri_esp], M["oscuro"], GRUPOS["carroceria"], espesor=0.016)
        yb_e = signo * semiancho_barril(0.79, 1.25)
        brazo_e = crear_caja("Brazo espejo", (0.78, yb_e + signo * 0.038, 1.255), (0.075, 0.080, 0.038), M["oscuro"], GRUPOS["carroceria"])
        suavizar_subsurf(brazo_e, niveles=1)

        carcasa = crear_caja("Carcasa cromada espejo", (0.745, yb_e + signo * 0.112, 1.285), (0.135, 0.178, 0.142), M["cromo"], GRUPOS["decoracion"])
        bm = bmesh.new()
        bm.from_mesh(carcasa.data)
        for v in bm.verts:
            if (v.co.y * signo) > 0:
                v.co.z *= 0.86
                v.co.x -= 0.022
            if v.co.x > 0:
                v.co.z *= 0.90
        bm.to_mesh(carcasa.data)
        bm.free()
        suavizar_subsurf(carcasa, niveles=2)

        base_inf_e = crear_caja("Base oscura espejo", (0.745, yb_e + signo * 0.108, 1.242), (0.118, 0.158, 0.048), M["oscuro"], GRUPOS["carroceria"])
        suavizar_subsurf(base_inf_e, niveles=2)
        cristal_e = crear_caja("Cristal retrovisor", (0.688, yb_e + signo * 0.112, 1.282), (0.010, 0.135, 0.095), M["plata"], GRUPOS["decoracion"], bisel=0.008)
        cristal_e.rotation_euler.z = signo * -0.14

    # 2. Parabrisas delantero curvo + limpiaparabrisas
    filas_pb = []
    for i in range(13):
        v = i / 12
        z = 1.195 + (1.708 - 1.195) * v
        x_lat = 0.935 * (1 - v) + 0.475 * v + 0.026 * math.sin(math.pi * v)
        ancho = semiancho_barril(x_lat, z) - 0.032
        bombeo_x = 0.072 * (1.0 - 0.22 * v)
        filas_pb.append([(x_lat + bombeo_x * (1.0 - (j / 10 - 1) ** 2), (-1 + j / 10) * ancho, z) for j in range(21)])
    pb = crear_superficie_grid("Parabrisas SUV", filas_pb, M["vidrio"], GRUPOS["cristales"])
    solidificar(pb, espesor=0.006)
    perim_pb = filas_pb[0] + [filas_pb[i][-1] for i in range(1, 13)] + list(reversed(filas_pb[-1][:-1])) + [filas_pb[i][0] for i in range(11, 0, -1)]
    crear_tubo("Burlete parabrisas", [(x + 0.004, y, z) for x, y, z in perim_pb], 0.015, M["goma"], GRUPOS["carroceria"], cerrado=True)

    # 3. Alerón trasero aerodinámico sobre la luneta con tercera luz de freno roja y aletas negras
    us_al = [-1.0 + 2.0 * j / 20 for j in range(21)]
    filas_aleron = []
    for xs_a, dz_a in [(-1.82, -0.008), (-1.96, 0.012), (-2.11, 0.006), (-2.08, -0.022)]:
        fila_a = []
        for u in us_al:
            ancho_a = 0.705
            y = u * ancho_a
            curva_x = -0.038 * (1.0 - u * u)
            caida_z = -0.026 * (u * u)
            fila_a.append((xs_a + curva_x, y, 1.792 + dz_a + caida_z))
        filas_aleron.append(fila_a)
    aleron = crear_superficie_grid("Aleron trasero techo", filas_aleron, M["carroceria"], GRUPOS["carroceria"], invertir=False)
    solidificar(aleron, espesor=0.018)
    crear_caja("Tercera luz freno LED", (-2.125, 0.0, 1.776), (0.016, 0.34, 0.016), M["rojo"], GRUPOS["decoracion"], bisel=0.004)


def construir_frente_dynamic_shield():
    """Capó alto musculoso, Dynamic Shield cromado en boomerang, ópticas divididas y skid plate plateado."""
    # 1. Capó alto esculpido con canal central y hombros marcados
    n_u, n_v = 24, 24
    filas_capo = []
    for j in range(n_v + 1):
        u = -1.0 + 2.0 * j / n_v
        ua = abs(u)
        fila = []
        for i in range(n_u + 1):
            t = i / n_u
            x_cen = 0.90 + (2.315 - 0.90) * t
            x_ext = 0.90 + (2.000 - 0.90) * min(1.0, t / 0.84) if t <= 0.84 else 2.000 + (x_frente_escudo(0.86) - 2.000) * ((t - 0.84) / 0.16)
            x = x_cen * (1.0 - ua ** 2.2) + x_ext * (ua ** 2.2)

            if x <= 2.000:
                z_borde = z_cintura(x)
                y_max = semiancho_barril(x, z_borde)
            else:
                w = sstep((x - 2.000) / max(0.06, x_frente_escudo(0.78) - 2.000))
                z_borde = z_cintura(2.000) * (1.0 - w) + 1.148 * w
                y_max = semiancho_barril(2.000, z_cintura(2.000)) * (1.0 - 0.03 * w)

            y = u * y_max
            if t > 0.82:
                wt = sstep((t - 0.82) / 0.18)
                yn = u * 0.865
                y = y * (1.0 - wt) + yn * wt
                x = x * (1.0 - wt) + x_frente_escudo(abs(yn)) * wt
                z_borde = z_borde * (1.0 - wt) + 1.152 * wt

            z_cen = interpolar_hermite(PERFIL_CAPO_CENTRO, x)
            domo = 1.0 - (ua ** 2.3)
            # Dos nervios musculosos del capó Mitsubishi en |u| ~ 0.56
            cresta = 0.012 * math.exp(-(((ua - 0.56) / 0.16) ** 2)) * sstep(t * 1.2)
            z = z_borde + max(0.0, z_cen - z_borde) * domo + cresta
            if t > 0.92:
                wb = (t - 0.92) / 0.08
                z -= 0.016 * (wb * wb)
            fila.append((x, y, z))
        filas_capo.append(fila)

    crear_superficie_grid("Capo alto SUV", filas_capo, M["carroceria"], GRUPOS["carroceria"], invertir=True)
    crear_caja("Torpedo base parabrisas", (0.92, 0.0, 1.192), (0.09, 1.62, 0.028), M["oscuro"], GRUPOS["carroceria"], bisel=0.006)
    for y_piv, largo_esc in [(-0.12, 0.46), (0.40, 0.48)]:
        crear_tubo("Brazo limpiaparabrisas", [(0.94, y_piv, 1.210), (0.90, y_piv - 0.24, 1.248)], 0.007, M["oscuro"], GRUPOS["decoracion"])
        crear_tubo("Escobilla limpiaparabrisas", [(0.91, y_piv - 0.06, 1.230), (0.89, y_piv - largo_esc, 1.264)], 0.009, M["goma"], GRUPOS["decoracion"])

    # 2. Escudo central oscuro (parrilla superior + boca hexagonal inferior)
    ys_esc = [-0.86 + 1.72 * i / 32 for i in range(33)]
    filas_fondo_esc = [
        [(x_frente_escudo(abs(yy)) - 0.032, yy, 0.62), (x_frente_escudo(abs(yy)) - 0.025, yy, 1.165)]
        for yy in ys_esc
    ]
    f_esc = crear_superficie_grid("Fondo oscuro Dynamic Shield", filas_fondo_esc, M["oscuro"], GRUPOS["carroceria"])
    solidificar(f_esc, espesor=0.018)

    # Lamas horizontales negras brillantes de la parrilla superior + emblema 3 diamantes
    ys_sup = [-0.46 + 0.92 * i / 16 for i in range(17)]
    for z_l, grosor in [(1.142, 0.016), (1.095, 0.018), (1.046, 0.014)]:
        pts_l = [(x_frente_escudo(abs(y)) + 0.004 - (0.012 if abs(y) < 0.09 else 0.0), y, z_l) for y in ys_sup]
        crear_tubo("Barra parrilla superior", pts_l, grosor, M["parrilla"], GRUPOS["decoracion"], resolucion=2)

    construir_emblema_tres_diamantes(x_frente_escudo(0.0) + 0.016, 1.088, escala=1.18, hacia_frente=True)

    # Rejilla inferior trapezoidal con entramado oscuro y portaplaca delantero neutro
    ys_rej = [-0.43 + 0.86 * i / 14 for i in range(15)]
    for z_r in (0.68, 0.73, 0.78, 0.92, 0.96):
        crear_tubo(
            "Travesano malla inferior",
            [(x_frente_escudo(abs(y)) - 0.006, y, z_r) for y in ys_rej],
            0.006,
            M["parrilla"],
            GRUPOS["decoracion"],
            resolucion=1,
        )
    crear_caja("Portaplaca delantero", (2.345, 0.0, 0.855), (0.024, 0.365, 0.155), M["oscuro"], GRUPOS["decoracion"], bisel=0.012)
    crear_caja("Matricula delantera", (2.358, 0.0, 0.855), (0.009, 0.335, 0.132), M["placa"], GRUPOS["decoracion"], bisel=0.006)

    # 3. Parachoques delantero esculpido blanco + boomerang cromado Dynamic Shield + ópticas dobles
    # Faldón y mejillas blancas envolventes desde el paso de rueda (X=1.985) hasta el frente (X=2.36)
    ruta_b = []
    rad_b = 0.24
    x_arco_d = 1.985
    x_punta_d = 2.365
    x_ic = x_punta_d - rad_b
    ancho_a = semiancho_barril(x_arco_d, 0.66)
    ancho_p = 0.885
    for s in range(6):
        t = s / 5
        ruta_b.append((x_arco_d + (x_ic - x_arco_d) * t, -(ancho_a * (1 - t) + ancho_p * t)))
    for s in range(1, 10):
        ang = -math.pi / 2 + (math.pi / 2) * (s / 9)
        ruta_b.append((x_ic + rad_b * math.cos(ang), -(ancho_p - rad_b) + rad_b * math.sin(ang)))
    for s in range(1, 14):
        u = -1.0 + 2.0 * (s / 14)
        ruta_b.append((x_punta_d + 0.032 * (1 - u * u), u * (ancho_p - rad_b)))
    for s in range(10):
        ang = (math.pi / 2) * (s / 9)
        ruta_b.append((x_ic + rad_b * math.cos(ang), (ancho_p - rad_b) + rad_b * math.sin(ang)))
    for s in range(1, 6):
        t = s / 5
        ruta_b.append((x_ic + (x_arco_d - x_ic) * t, ancho_p * (1 - t) + ancho_a * t))

    # Labio inferior blanco del parachoques con ángulo de ataque todoterreno (Z = 0.42..0.64)
    perfil_b_inf = [
        (0.395, -0.115),
        (0.435, -0.055),
        (0.515, +0.008),
        (0.585, +0.018),
        (0.635, -0.006),
        (0.642, -0.042),
    ]
    filas_b_inf = []
    for idx, (px, py) in enumerate(ruta_b):
        p0 = ruta_b[max(0, idx - 1)]
        p1 = ruta_b[min(len(ruta_b) - 1, idx + 1)]
        tx, ty = p1[0] - p0[0], p1[1] - p0[1]
        tl = max(1e-6, math.hypot(tx, ty))
        nx, ny = ty / tl, -tx / tl
        fila = [(px + nx * sal, py + ny * sal, zz) for zz, sal in perfil_b_inf]
        filas_b_inf.append(fila)
    crear_superficie_grid("Faldon blanco parachoques delantero", filas_b_inf, M["carroceria"], GRUPOS["carroceria"], invertir=False)

    # Protector inferior todoterreno plateado (Skid Plate frontal característico)
    ys_skid = [-0.56 + 1.12 * i / 18 for i in range(19)]
    filas_skid = []
    for yy in ys_skid:
        ua = abs(yy) / 0.56
        xs = 2.382 - 0.045 * (ua ** 2)
        filas_skid.append([
            (xs - 0.14, yy * 0.92, 0.375),
            (xs - 0.05, yy * 0.96, 0.435),
            (xs + 0.012, yy, 0.525),
            (xs + 0.005, yy * 0.98, 0.568),
            (xs - 0.022, yy * 0.96, 0.575),
        ])
    crear_superficie_grid("Protector inferior plateado delantero", filas_skid, M["plata"], GRUPOS["decoracion"], invertir=False)
    crear_caja("Boca central skid plate", (2.375, 0.0, 0.525), (0.032, 0.62, 0.042), M["oscuro"], GRUPOS["decoracion"], bisel=0.008)

    for signo in (-1, 1):
        # Mejilla lateral blanca envolvente del parachoques (alrededor del grupo óptico vertical, Z = 0.62..1.08)
        filas_mej = []
        for s in range(9):
            w = s / 8
            xx = 1.985 + (2.215 - 1.985) * w
            yy_ext = semiancho_barril(1.985, 0.85) * (1.0 - 0.045 * (w ** 1.6))
            z_top_m = 1.155 - 0.095 * sstep(w)
            filas_mej.append([
                (xx, signo * (yy_ext - 0.035 * w), 0.625),
                (xx + 0.014 * math.sin(math.pi * w), signo * (yy_ext + 0.008), 0.84),
                (xx, signo * (yy_ext - 0.025 * w), z_top_m),
            ])
        mej = crear_superficie_grid("Mejilla lateral parachoques", filas_mej, M["carroceria"], GRUPOS["carroceria"], invertir=(signo > 0))
        solidificar(mej, espesor=0.018)

        # Boomerang cromado Dynamic Shield (perfil 3D brillante en C que abraza las ópticas inferiores)
        pts_boom = [
            (x_frente_escudo(0.84) + 0.008, signo * 0.84, 1.055),
            (x_frente_escudo(0.62) + 0.016, signo * 0.62, 1.015),
            (x_frente_escudo(0.42) + 0.020, signo * 0.42, 0.955),
            (x_frente_escudo(0.45) + 0.022, signo * 0.45, 0.805),
            (x_frente_escudo(0.50) + 0.022, signo * 0.50, 0.648),
            (x_frente_escudo(0.70) + 0.018, signo * 0.70, 0.642),
            (x_frente_escudo(0.84) + 0.010, signo * 0.84, 0.648),
        ]
        crear_tubo("Boomerang cromado Dynamic Shield", pts_boom, 0.024, M["cromo"], GRUPOS["decoracion"], resolucion=3)

        # Panel plateado satinado interior del boomerang junto al nicho vertical
        pts_pl_boom = [
            (x_frente_escudo(0.45) + 0.012, signo * 0.45, 0.95),
            (x_frente_escudo(0.63) + 0.010, signo * 0.63, 0.98),
            (x_frente_escudo(0.63) + 0.012, signo * 0.63, 0.66),
            (x_frente_escudo(0.50) + 0.014, signo * 0.50, 0.66),
        ]
        crear_panel("Escudo satinado boomerang", pts_pl_boom, M["plata"], GRUPOS["decoracion"], espesor=0.014)

        # Faro superior rasgado afilado (|y| = 0.44..0.87, barriendo hacia X = 1.94 en la aleta)
        est_faro = [
            (x_frente_escudo(0.44) + 0.006, 0.44, 1.062, 1.150),
            (x_frente_escudo(0.64) + 0.008, 0.64, 1.058, 1.154),
            (x_frente_escudo(0.80) + 0.008, 0.80, 1.072, 1.158),
            (2.06, 0.868, 1.098, 1.166),
            (1.94, 0.888, 1.128, 1.174),
        ]
        filas_f_sup = []
        for xx, yy, z0, z1 in est_faro:
            zm = 0.5 * (z0 + z1)
            filas_f_sup.append([(xx, signo * yy, z0), (xx + 0.010, signo * (yy + 0.004), zm), (xx, signo * yy, z1)])
        lente_s = crear_superficie_grid("Faro superior rasgado", filas_f_sup, M["lente_claro"], GRUPOS["cristales"], invertir=(signo < 0))
        solidificar(lente_s, espesor=0.005)
        # Ceja LED diurna blanca brillante en la base del faro superior
        crear_tubo(
            "Ceja LED diurna",
            [(xx + 0.004, signo * yy, z0 + 0.010) for xx, yy, z0, _ in est_faro],
            0.008,
            M["faro"],
            GRUPOS["decoracion"],
        )

        # Grupo óptico vertical inferior de 3 cámaras (|y| = 0.65..0.83, z = 0.68..0.97)
        x_pod = x_frente_escudo(0.74) - 0.004
        marco_pod = crear_caja("Nicho optico vertical", (x_pod, signo * 0.745, 0.825), (0.045, 0.185, 0.285), M["oscuro"], GRUPOS["carroceria"])
        marco_pod.rotation_euler.z = signo * -0.26
        suavizar_subsurf(marco_pod, niveles=1)
        for z_cam, col_cam in [(0.912, "ambar"), (0.825, "faro"), (0.738, "faro")]:
            cam = crear_caja(
                "Camara optica vertical",
                (x_pod + 0.016, signo * 0.745, z_cam),
                (0.024, 0.145, 0.068),
                M[col_cam],
                GRUPOS["decoracion"],
                bisel=0.010,
            )
            cam.rotation_euler.z = signo * -0.26


def construir_trasera_montero():
    """Portón abombado, pilotos verticales largos tipo lágrima y difusor plateado trasero."""
    # 1. Portón trasero abombado en 3D (Z = 0.74..1.24) con cuenco trapezoidal de matrícula
    zs_p = [0.740 + (1.240 - 0.740) * i / 16 for i in range(17)]
    us_p = [-1.0 + 2.0 * j / 22 for j in range(23)]
    filas_porton = []
    for z in zs_p:
        xb = x_perfil_porton(z)
        ancho = 0.755
        fila = []
        for u in us_p:
            y = u * ancho
            bombeo = -0.048 * (1.0 - u * u)
            wy = sstep((0.30 - abs(y)) / 0.05)
            wz = sstep((z - 0.86) / 0.04) * sstep((1.065 - z) / 0.04)
            cuenco = 0.028 * wy * wz
            fila.append((xb + bombeo + cuenco, y, z))
        filas_porton.append(fila)
    crear_superficie_grid("Porton trasero SUV", filas_porton, M["carroceria"], GRUPOS["carroceria"], invertir=False)

    # Moldura cromada horizontal ancha sobre matrícula + emblema 3 diamantes + placa neutra
    ys_mc = [-0.42 + 0.84 * i / 14 for i in range(15)]
    crear_tubo(
        "Moldura cromada porton",
        [(x_perfil_porton(1.072) - 0.048 * (1.0 - (y / 0.75) ** 2) - 0.008, y, 1.072) for y in ys_mc],
        0.015,
        M["cromo"],
        GRUPOS["decoracion"],
    )
    construir_emblema_tres_diamantes(x_perfil_porton(1.145) - 0.052, 1.145, escala=0.92, hacia_frente=False)
    x_plt = x_perfil_porton(0.955) - 0.048 + 0.024
    crear_caja("Marco matricula trasera", (x_plt - 0.004, 0.0, 0.955), (0.014, 0.345, 0.152), M["oscuro"], GRUPOS["decoracion"], bisel=0.010)
    crear_caja("Matricula trasera", (x_plt - 0.011, 0.0, 0.955), (0.009, 0.320, 0.134), M["placa"], GRUPOS["decoracion"], bisel=0.006)

    # 2. Luneta trasera curvada + aletas negras laterales bajo el alerón + limpialuneta
    filas_lt = []
    for i in range(13):
        v = i / 12
        z = 1.240 + (1.745 - 1.240) * v
        xl = x_perfil_porton(z) + 0.022
        ancho = semiancho_barril(-1.95, z) - 0.042
        bombeo = -0.052 * (1.0 - 0.22 * v)
        filas_lt.append([(xl + bombeo * (1.0 - (-1 + j / 10) ** 2), (-1 + j / 10) * ancho, z) for j in range(21)])
    lt = crear_superficie_grid("Luneta trasera SUV", filas_lt, M["vidrio"], GRUPOS["cristales"], invertir=True)
    solidificar(lt, espesor=0.006)
    perim_lt = filas_lt[0] + [filas_lt[i][-1] for i in range(1, 13)] + list(reversed(filas_lt[-1][:-1])) + [filas_lt[i][0] for i in range(11, 0, -1)]
    crear_tubo("Burlete luneta", [(x - 0.004, y, z) for x, y, z in perim_lt], 0.015, M["goma"], GRUPOS["carroceria"], cerrado=True)
    crear_tubo("Brazo limpialuneta", [(-2.30, 0.02, 1.248), (-2.29, -0.26, 1.272)], 0.007, M["oscuro"], GRUPOS["decoracion"])
    crear_tubo("Escobilla limpialuneta", [(-2.295, -0.08, 1.268), (-2.285, -0.42, 1.272)], 0.0085, M["goma"], GRUPOS["decoracion"])

    # 3. Parachoques trasero envolvente blanco + difusor plateado con reflectores rojos
    ruta_bt = []
    rad_t = 0.22
    x_at = -1.78
    x_pt = -2.355
    x_ict = x_pt + rad_t
    ancho_at = semiancho_barril(x_at, 0.65)
    ancho_pt = 0.885
    for s in range(6):
        t = s / 5
        ruta_bt.append((x_at + (x_ict - x_at) * t, -(ancho_at * (1 - t) + ancho_pt * t)))
    for s in range(1, 10):
        ang = -math.pi / 2 + (math.pi / 2) * (s / 9)
        ruta_bt.append((x_ict - rad_t * math.cos(ang), -(ancho_pt - rad_t) + rad_t * math.sin(ang)))
    for s in range(1, 14):
        u = -1.0 + 2.0 * (s / 14)
        ruta_bt.append((x_pt - 0.036 * (1 - u * u), u * (ancho_pt - rad_t)))
    for s in range(10):
        ang = (math.pi / 2) * (s / 9)
        ruta_bt.append((x_ict - rad_t * math.cos(ang), (ancho_pt - rad_t) + rad_t * math.sin(ang)))
    for s in range(1, 6):
        t = s / 5
        ruta_bt.append((x_ict + (x_at - x_ict) * t, ancho_pt * (1 - t) + ancho_at * t))

    perfil_bt = [
        (0.415, -0.105),
        (0.455, -0.048),
        (0.545, +0.012),
        (0.655, +0.024),
        (0.725, +0.008),
        (0.742, -0.032),
        (0.735, -0.068),
    ]
    filas_bt = []
    for idx, (px, py) in enumerate(ruta_bt):
        p0 = ruta_bt[max(0, idx - 1)]
        p1 = ruta_bt[min(len(ruta_bt) - 1, idx + 1)]
        tx, ty = p1[0] - p0[0], p1[1] - p0[1]
        tl = max(1e-6, math.hypot(tx, ty))
        nx, ny = -ty / tl, tx / tl
        filas_bt.append([(px + nx * sal, py + ny * sal, zz) for zz, sal in perfil_bt])
    crear_superficie_grid("Parachoques trasero blanco SUV", filas_bt, M["carroceria"], GRUPOS["carroceria"], invertir=True)

    # Difusor protector plateado trasero + dos reflectores rojos empotrados
    ys_dif = [-0.68 + 1.36 * i / 20 for i in range(21)]
    filas_dif = []
    for yy in ys_dif:
        ua = abs(yy) / 0.68
        xd = -2.378 + 0.040 * (ua ** 2)
        filas_dif.append([
            (xd + 0.11, yy * 0.94, 0.405),
            (xd + 0.03, yy * 0.97, 0.455),
            (xd - 0.012, yy, 0.535),
            (xd - 0.004, yy * 0.98, 0.578),
            (xd + 0.020, yy * 0.96, 0.584),
        ])
    crear_superficie_grid("Difusor plateado trasero", filas_dif, M["plata"], GRUPOS["decoracion"], invertir=True)

    for signo in (-1, 1):
        refl_r = crear_caja("Reflector rojo parachoques", (-2.382, signo * 0.54, 0.525), (0.018, 0.185, 0.034), M["rojo"], GRUPOS["decoracion"], bisel=0.008)
        refl_r.rotation_euler.z = signo * 0.12

        # Montante trasero blanco + aleta negra junto a luneta
        filas_m = []
        for i in range(9):
            v = i / 8
            z = 1.24 + (1.745 - 1.24) * v
            xi = x_perfil_porton(z) + 0.018
            yi = semiancho_barril(-1.95, z) - 0.042
            xe = -2.21 * (1 - v) + (-1.91) * v
            ye = semiancho_barril(xe, z)
            filas_m.append([(xi, signo * yi, z), (0.5 * (xi + xe) - 0.008, signo * (0.5 * (yi + ye) + 0.005), z), (xe, signo * ye, z)])
        mont = crear_superficie_grid("Montante esquina trasera", filas_m, M["oscuro"], GRUPOS["carroceria"], invertir=(signo < 0))
        solidificar(mont, espesor=0.014)

        # Pilotos verticales largos tipo lágrima Mitsubishi Montero Sport (Z = 0.76..1.38)
        # Ala superior envolvente hacia el costado (X = -1.98..-2.28, Z = 1.18..1.38) + hoja vertical (Z = 0.76..1.22)
        est_ala = [
            (-2.275, 0.755, 1.16, 1.33),
            (-2.255, 0.825, 1.18, 1.36),
            (-2.165, 0.875, 1.21, 1.37),
            (-2.055, 0.892, 1.25, 1.36),
            (-1.975, 0.896, 1.29, 1.34),
        ]
        filas_ala = []
        for xx, yy, z0, z1 in est_ala:
            zm = 0.5 * (z0 + z1)
            filas_ala.append([(xx, signo * yy, z0), (xx - 0.012, signo * (yy + 0.008), zm), (xx, signo * yy, z1)])
        ala_pil = crear_superficie_grid("Ala superior piloto trasero", filas_ala, M["rojo"], GRUPOS["decoracion"], invertir=(signo > 0))
        solidificar(ala_pil, espesor=0.014, offset=-1.0)

        # Caída vertical característica ("lágrima" roja exterior + franja blanca interior de reversa)
        zs_lag = [0.755 + (1.205 - 0.755) * i / 10 for i in range(11)]
        filas_lag_roja, filas_lag_blanca = [], []
        for zz in zs_lag:
            xl = x_perfil_porton(zz) - 0.008
            filas_lag_roja.append([
                (xl - 0.006, signo * 0.795, zz),
                (xl - 0.018, signo * 0.835, zz),
                (xl + 0.025, signo * 0.868, zz),
            ])
            filas_lag_blanca.append([
                (xl - 0.004, signo * 0.756, zz),
                (xl - 0.010, signo * 0.795, zz),
            ])
        lag_r = crear_superficie_grid("Lagrima vertical piloto rojo", filas_lag_roja, M["rojo"], GRUPOS["decoracion"], invertir=(signo < 0))
        solidificar(lag_r, espesor=0.014, offset=-1.0)
        lag_b = crear_superficie_grid("Franja vertical reversa", filas_lag_blanca, M["faro"], GRUPOS["decoracion"], invertir=(signo < 0))
        solidificar(lag_b, espesor=0.012, offset=-1.0)

        # Cierre blanco de aleta trasera entre X=-2.10 y el piloto vertical (Z=0.68..1.28)
        filas_cie_t = []
        for zz in [0.68, 0.88, 1.08, 1.28]:
            filas_cie_t.append([
                (-2.10, signo * semiancho_barril(-2.10, zz), zz),
                (-2.23, signo * 0.865, zz),
            ])
        cie_t = crear_superficie_grid("Cierre esquina trasera blanca", filas_cie_t, M["carroceria"], GRUPOS["carroceria"], invertir=(signo > 0))
        solidificar(cie_t, espesor=0.016)

    crear_tubo("Cola escape trasera", [(-2.05, -0.52, 0.37), (-2.28, -0.52, 0.35)], 0.024, M["llanta"], GRUPOS["interior"])


def construir_interior_suv():
    crear_caja("Piso cabina SUV", (0.05, 0.0, 0.44), (2.10, 1.48, 0.05), M["interior"], GRUPOS["interior"], bisel=0.01)
    crear_caja("Piso maletero SUV", (-1.45, 0.0, 0.72), (1.35, 1.36, 0.06), M["interior"], GRUPOS["interior"], bisel=0.01)

    salp = crear_caja("Salpicadero SUV", (0.82, 0.0, 1.08), (0.38, 1.52, 0.22), M["interior"], GRUPOS["interior"])
    suavizar_subsurf(salp, niveles=2)
    capilla = crear_caja("Capilla instrumentos", (0.76, 0.38, 1.20), (0.22, 0.38, 0.10), M["oscuro"], GRUPOS["interior"])
    suavizar_subsurf(capilla, niveles=2)

    crear_tubo("Columna direccion", [(0.74, 0.38, 1.06), (0.52, 0.38, 1.18)], 0.025, M["oscuro"], GRUPOS["interior"])
    cv = Vector((0.50, 0.38, 1.185))
    uv, vv = Vector((0.065, 0.0, 0.165)), Vector((0.0, 0.180, 0.0))
    crear_tubo("Aro volante", [tuple(cv + uv * math.cos(math.tau * i / 28) + vv * math.sin(math.tau * i / 28)) for i in range(28)], 0.016, M["goma"], GRUPOS["interior"], cerrado=True)
    for ang in (0.0, math.pi * 0.80, -math.pi * 0.80):
        crear_tubo("Radio volante", [tuple(cv), tuple(cv + uv * math.cos(ang) + vv * math.sin(ang))], 0.012, M["plata"], GRUPOS["interior"])

    crear_tubo("Soporte espejo interior", [(0.45, 0.0, 1.695), (0.48, 0.0, 1.615)], 0.007, M["oscuro"], GRUPOS["interior"])
    esp_i = crear_caja("Espejo interior cabina", (0.48, 0.0, 1.605), (0.024, 0.195, 0.050), M["oscuro"], GRUPOS["interior"])
    suavizar_subsurf(esp_i, niveles=1)

    for nombre_as, y_as in [("Asiento conductor", 0.38), ("Asiento acompanante", -0.38)]:
        coj = crear_caja(nombre_as + " cojin", (0.18, y_as, 0.72), (0.50, 0.48, 0.13), M["tapizado"], GRUPOS["interior"])
        suavizar_subsurf(coj, niveles=1)
        resp = crear_caja(nombre_as + " respaldo", (-0.04, y_as, 1.06), (0.13, 0.46, 0.58), M["tapizado"], GRUPOS["interior"])
        resp.rotation_euler.y = -0.17
        suavizar_subsurf(resp, niveles=1)
        cab = crear_caja(nombre_as + " apoyacabezas", (-0.11, y_as, 1.41), (0.09, 0.22, 0.15), M["interior"], GRUPOS["interior"])
        suavizar_subsurf(cab, niveles=2)

    b_coj = crear_caja("Banqueta trasera cojin", (-0.58, 0.0, 0.75), (0.48, 1.32, 0.13), M["tapizado"], GRUPOS["interior"])
    suavizar_subsurf(b_coj, niveles=1)
    b_resp = crear_caja("Banqueta trasera respaldo", (-0.80, 0.0, 1.08), (0.13, 1.30, 0.54), M["tapizado"], GRUPOS["interior"])
    b_resp.rotation_euler.y = -0.15
    suavizar_subsurf(b_resp, niveles=1)
    for y_cab in (-0.38, 0.38):
        cab_t = crear_caja("Apoyacabezas trasero", (-0.86, y_cab, 1.40), (0.085, 0.22, 0.14), M["interior"], GRUPOS["interior"])
        suavizar_subsurf(cab_t, niveles=2)


def construir_ruedas_aleacion():
    # Neumático todoterreno SUV 265/60R18 (R = 0.425 m, ancho ~0.255 m)
    medio_neum = [
        (0.252, -0.108),
        (0.278, -0.124),
        (0.328, -0.130),
        (0.378, -0.120),
        (0.408, -0.098),
        (0.421, -0.074),
        (0.425, -0.056),
        (0.417, -0.048),
        (0.425, -0.039),
        (0.425, -0.015),
        (0.417, -0.007),
        (0.425, -0.001),
    ]
    perfil_neumatico = medio_neum + [(r, -d) for r, d in reversed(medio_neum)]

    # Llanta de aleación 18" gris antracita oscuro: plato exterior esculpido para 6 radios dobles
    perfil_llanta = [
        (0.052, 0.086),
        (0.088, 0.088),
        (0.118, 0.094),
        (0.175, 0.102),
        (0.228, 0.108),
        (0.248, 0.112),
        (0.258, 0.114),
        (0.262, 0.102),
        (0.262, 0.064),
        (0.242, 0.060),
        (0.222, 0.082),
        (0.172, 0.076),
        (0.118, 0.068),
        (0.086, 0.064),
        (0.052, 0.064),
    ]

    # 6 pares de radios dobles = 6 ventanas anchas entre pares + 6 ranuras estrechas dentro de cada par
    ventanas = []
    paso = math.tau / 6.0
    for k in range(6):
        base = k * paso
        # Ranura estrecha dentro del radio doble
        ventanas.append((base + 0.085, base + 0.235, 0.112, 0.228))
        # Ventana trapezoidal amplia entre pares de radios dobles
        ventanas.append((base + 0.365, base + paso - 0.085, 0.098, 0.232))

    construir_ruedas_volumetricas(
        datos=D,
        materiales=M,
        grupos=GRUPOS,
        perfil_neumatico=perfil_neumatico,
        perfil_llanta=perfil_llanta,
        segmentos_neumatico=42,
        segmentos_llanta=48,
        dibujo_banda=(0.415, 0.085, 0.0032),
        n_ventilaciones=0,
        ventanas_aleacion=ventanas,
        desp_agujero=0.088,
        n_tuercas=6,
        radio_tuercas=0.068,
        radio_buje=0.042,
        desp_buje=0.092,
    )


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    crear_materiales()
    GRUPOS.update(inicializar_jerarquia(D["id"]))

    construir_flancos_y_estribos()
    construir_invernadero_techo_y_barras()
    construir_frente_dynamic_shield()
    construir_trasera_montero()
    construir_interior_suv()
    construir_ruedas_aleacion()

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
    print("MONTERO_VALIDACION", json.dumps(reporte, ensure_ascii=False), flush=True)

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
