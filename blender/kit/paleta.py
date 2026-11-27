"""Paleta del estilo (ver estilo/GUIA_ESTILO.md). Colores ALBEDO (color propio del material, sin luz).

Contrato con el visor web: el nombre del material es el ROL, y opcionalmente el color propio:
    "muro"              -> color por defecto del rol
    "muro__f1e3c8"      -> rol muro con color propio (para respetar el color real de cada fachada)
El visor aplica el sombreado del estilo según el rol (prefijo antes de "__").
No inventes roles nuevos: si falta uno, pídelo en coordinacion/estado_<agente>.md.
"""

import bpy

PALETA = {
    # muros y piedra
    "muro": "#f3e6d3",            # cal blanca cálida (al sol se ve crema #fae6d5)
    "zocalo_piedra": "#c9935f",   # zócalo de sillares de arenisca
    "piedra": "#e8c39a",          # sillares, pilares, remates, molduras de piedra
    "moldura": "#f7efe3",         # cornisas, marcos y pilastras de yeso (algo más claros que el muro)
    "pintura_acento": "#e7c46a",  # molduras pintadas de color (amarillo ocre típico de Sucre)
    "azotea": "#d8c3a5",          # techo plano
    # techos y madera
    "teja": "#c0643a",            # teja colonial de terracota
    "madera": "#5a3422",          # vigas, canes, aleros, portones
    "marco_ventana": "#6a3622",   # carpintería de ventanas (marrón rojizo)
    "vidrio": "#3a4550",          # vidrio oscuro (sin reflejos realistas)
    "hierro": "#2b2522",          # rejas, balcones, faroles (negro cálido, nunca negro puro)
    "metal": "#8f8a7e",           # campanas, metal claro
    # suelo
    "vereda": "#d9a77c",          # aceras de piedra/losa
    "calzada": "#8b7a6d",         # calzada empedrada/asfalto viejo
    "adoquin": "#b98b69",         # plazas y patios
    "cesped": "#7fa046",
    # vegetación
    "follaje": "#4d6b2a",
    "follaje_claro": "#8fae45",
    "tronco": "#4a3626",
    "flor": "#e8742c",            # buganvillas/flores naranjas
    "agua": "#6fa8c9",
    # otros
    "letrero": "#efe2c4",         # placas y letreros simplificados (sin texto legible)
}

ROLES = set(PALETA)


def hex_a_rgba(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    # sRGB -> lineal (Blender trabaja en lineal)
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, 1.0)


def nombre_material(rol, color=None):
    if rol not in ROLES:
        raise ValueError(f"Rol de material desconocido: {rol!r}. Roles válidos: {sorted(ROLES)}")
    return rol if not color else f"{rol}__{color.lstrip('#').lower()}"


def material(rol, color=None):
    """Devuelve (o crea) el material del rol; color opcional '#rrggbb' para el color real de la fachada."""
    nombre = nombre_material(rol, color)
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_a_rgba(color or PALETA[rol])
    bsdf.inputs["Roughness"].default_value = 0.35 if rol in ("vidrio", "agua") else 0.9
    bsdf.inputs["Metallic"].default_value = 0.0
    m.diffuse_color = hex_a_rgba(color or PALETA[rol])
    return m
