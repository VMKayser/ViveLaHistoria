"""Casa de la Libertad (Sucre, 1809) — Script procedural modular para Blender 5.2.

Fase 2.6: Realismo visual optimizado para WebGL (Godot 4.7 Compatibility):
- Texturas PBR 512x512 seamless (Albedo + Normal OpenGL + Roughness) con UVs cubicas en metros
- Atlas de museo 1024x1024 con Roughness/Normal (agua con relieve y vidrio colonial oscuro)
- Material ligero vidrio_vitrina (Alpha Blend, sin Transmission) para vitrinas -> max 9 materiales
- Escultura organica de El Flechero (Skin + Subsurf + Decimate ~1,900 tris, bronce patinado)
- Arana sin discos gruesos (brazos curvos en S), crestas barrocas curvas, Shade Smooth por angulo

Presupuesto objetivo: <= 42,000 tris visibles (<= 45,000 con colisiones), <= 9 materiales.

Uso headless:
    blender -b --factory-startup --python museo_interior/blender/casa_libertad_1809.py

Uso con Blender MCP (via museo_interior/blender/mcp_cliente.py):
    python museo_interior/blender/mcp_cliente.py run museo_interior/blender/casa_libertad_1809.py --render
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

# ---------------------------------------------------------------------------
# PARAMETROS ARQUITECTONICOS MAESTROS (metros, escala humana real: ojos 1.65 m)
# ---------------------------------------------------------------------------

PHASE = 3.0  # Fase 3: Colisiones -colonly, 9 materiales PBR/Atlas, escala 1:1 y GLB 2.0

REF_LOTE = {
    "manzana": "M037",
    "edificio_id": "Ee30c62",
    "base_z_mundo": 58.05,
    "altura_lienzo": 9.0,
    "frente_total_lienzo": 45.77,
    "fondo_total_lienzo": 62.30,
    "frente_sp25_asignado": 15.76,
    "altura_sp25": 9.4,
}

# Niveles de piso
Z_ACERA = 0.0
Z_ZAGUAN = 0.12
Z_PATIO = 0.15
Z_GALERIA = 0.40
Z_SALON_PISO = 0.40
Z_PRESIDIO = 0.85
Z_PLANTA_ALTA = 4.40

# 1. Fachada exterior y crujia frontal (22.00 m alineados al claustro)
FACHADA_ANCHO = 22.00
FACHADA_FONDO = 6.20
FACHADA_ALTO = 8.60
ZOCALO_ALTO = 1.35
PORTADA_ANCHO = 5.20
PORTADA_ALTO_FRONTON = 10.15
PORTON_ANCHO = 2.80     # >= 2.20 m para collider del jugador
PORTON_ALTO = 3.80      # >= 3.00 m para collider del jugador
ZAGUAN_ANCHO = 3.20     # >= 2.20 m
ZAGUAN_ALTO = 4.10      # >= 3.00 m

# 2. Claustro principal (Patio central 14.4 x 14.4 m y 4 galerias de 3.2 m)
CLAUSTRO_Y0 = FACHADA_FONDO                      # 6.20
CLAUSTRO_ANCHO_EXT = 22.00                       # X: -11.0 -> +11.0
CLAUSTRO_FONDO_EXT = 22.00                       # Y: 6.20 -> 28.20
CLAUSTRO_MURO = 0.60
GALERIA_ANCHO = 3.20
PATIO_ANCHO = CLAUSTRO_ANCHO_EXT - 2 * (CLAUSTRO_MURO + GALERIA_ANCHO)   # 14.40
PATIO_FONDO = CLAUSTRO_FONDO_EXT - 2 * (CLAUSTRO_MURO + GALERIA_ANCHO)   # 14.40
GALERIA_ALTO_ALERO = 4.65
GALERIA_ALTO_CUMBRERA = 6.25
NUM_ARCOS_LADO = 5

# 3. Salon de la Independencia (9.2 x 24.0 m libre)
SALON_Y0 = CLAUSTRO_Y0 + CLAUSTRO_FONDO_EXT      # 28.20
SALON_MURO = 0.80
SALON_ANCHO_INT = 9.20                           # X: -4.60 -> +4.60
SALON_LARGO_INT = 24.00                          # Y: 28.80 -> 52.80
SALON_ANCHO_EXT = SALON_ANCHO_INT + 2 * SALON_MURO   # 10.80
SALON_LARGO_EXT = SALON_LARGO_INT + 2 * SALON_MURO   # 25.60
SALON_PORTON_ANCHO = 2.60                        # >= 2.20 m
SALON_PORTON_ALTO = 3.60                         # >= 3.00 m
SALON_ALTO_MURO = 6.20
SALON_ALTO_CUMBRERA = 8.60
CORO_LARGO = 4.40
CORO_ALTO = 3.45
PRESIDIO_LARGO = 4.40

# 4. Sala Museografica Lateral Navegable (basada en cuarto.jpg y cuarto2.jpg)
SALA_LAT_X0 = CLAUSTRO_ANCHO_EXT * 0.5           # 11.00 (pegada al muro Este del claustro)
SALA_LAT_ANCHO_INT = 6.20                        # X: 11.00 -> 17.20
SALA_LAT_LARGO_INT = 8.60                        # Y: 16.50 -> 25.10
SALA_LAT_MURO = 0.55
SALA_LAT_ALTO = 4.80
SALA_LAT_PUERTA_Y0 = 19.60
SALA_LAT_PUERTA_Y1 = 22.00                       # 2.40 m ancho libre (>= 2.20 m)
SALA_LAT_PUERTA_H = 3.20                         # 3.20 m alto libre (>= 3.00 m)

ROOT_COLLECTION_NAME = "CasaLibertad_1809"

# ---------------------------------------------------------------------------
# 9 MATERIALES MAXIMO PARA WEBGL (7 PBR 512px + atlas_museo + vidrio_vitrina)
# ---------------------------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEX_DIR = os.path.join(BASE_DIR, "texturas")
PBR_DIR = os.path.join(TEX_DIR, "pbr")
ATLAS_BASE_PATH = os.path.join(TEX_DIR, "atlas_museo.png")
ATLAS_EMIT_PATH = os.path.join(TEX_DIR, "atlas_museo_emit.png")
ATLAS_ROUGH_PATH = os.path.join(TEX_DIR, "atlas_museo_rough.png")
ATLAS_NORM_PATH = os.path.join(TEX_DIR, "atlas_museo_normal.png")

MATERIAL_DEFS = {
    "muro":           (0.960, 0.948, 0.930, 1.0, 0.90, 0.0),   # estuco blanco cal limpia ("Ciudad Blanca")
    "piedra":         (0.820, 0.655, 0.495, 1.0, 0.88, 0.0),   # sillar claro interior (claustro / fuente)
    "piedra_fachada": (0.520, 0.395, 0.265, 1.0, 0.86, 0.0),   # arenisca marron-ocre oscura portada / zocalo exterior
    "madera":         (0.240, 0.145, 0.090, 1.0, 0.72, 0.0),   # cedro nativo / artesonado
    "teja":           (0.740, 0.375, 0.215, 1.0, 0.84, 0.0),   # teja terracota colonial
    "piso":           (0.560, 0.300, 0.205, 1.0, 0.78, 0.0),   # baldosa barro / empedrado
    "hierro":         (0.200, 0.175, 0.165, 1.0, 0.50, 0.58),  # hierro forjado / bronce patinado
    "oro_bronce":     (0.840, 0.650, 0.250, 1.0, 0.32, 0.85),  # pan de oro coro, marcos
}

# Escala real en metros por cada baldosa UV 1x1 de textura repetible
UV_TILE_METERS = {
    "muro": 2.4,
    "piedra": 2.1,
    "piedra_fachada": 2.1,
    "madera": 1.6,
    "teja": 1.75,
    "piso": 1.8,
    "hierro": 1.0,
    "oro_bronce": 1.25,
    "vidrio_vitrina": 1.0,
}

PBR_NORMAL_STRENGTH = {
    "muro": 0.75,
    "piedra": 1.05,
    "piedra_fachada": 1.15,
    "madera": 0.95,
    "teja": 1.15,
    "piso": 1.05,
    "hierro": 0.85,
    "oro_bronce": 0.65,
}

VALID_MATERIALS = set(MATERIAL_DEFS) | {"atlas_museo", "vidrio_vitrina"}

# Regiones normalizadas (u0, v0, u1, v1) en el atlas 1024x1024 (v=1 arriba, v=0 abajo)
def _cell256(col: int, row: int, pad: float = 0.012) -> tuple[float, float, float, float]:
    return (col * 0.25 + pad, 1.0 - (row + 1) * 0.25 + pad, (col + 1) * 0.25 - pad, 1.0 - row * 0.25 - pad)


def _sub128(gx: int, gy: int, pad: float = 0.012) -> tuple[float, float, float, float]:
    # Fila 3 (y: 0.00..0.25 en UV); gy=0 arriba (v: 0.125..0.250), gy=1 abajo (v: 0.000..0.125)
    u0 = gx * 0.125 + pad
    u1 = (gx + 1) * 0.125 - pad
    v1 = 0.25 - gy * 0.125 - pad
    v0 = 0.25 - (gy + 1) * 0.125 + pad
    return (u0, v0, u1, v1)


ATLAS_REGIONS = {
    "bolivar":          _cell256(0, 0),
    "sucre":            _cell256(1, 0),
    "santacruz":        _cell256(2, 0),
    "ballivian":        _cell256(2, 0),
    "juana_grande":     _cell256(3, 0),
    "ret_sup_izq":    _cell256(0, 1),
    "ret_sup_der":    _cell256(1, 1),
    "oculo":          _cell256(2, 1, pad=0.048),
    "escudo_usfx":    _cell256(3, 1, pad=0.018),
    "guerrillera":    _cell256(0, 2),
    "batalla":        _cell256(1, 2),
    "espadas":        _cell256(2, 2),
    "acta":           _cell256(3, 2),
    "rojo":           _sub128(0, 0, pad=0.018),
    "azul_verde":     _sub128(1, 0, pad=0.018),
    "bandera":        _sub128(2, 0, pad=0.012),
    "wiphala":        _sub128(3, 0, pad=0.012),
    "verde_bar":      _sub128(4, 0, pad=0.018),
    "follaje":        _sub128(5, 0, pad=0.015),
    "vidrio":         _sub128(6, 0, pad=0.018),
    "vela":           _sub128(7, 0, pad=0.018),
    "agua":           _sub128(0, 1, pad=0.018),
    "piano_teclas":   _sub128(1, 1, pad=0.010),
    "ataud_emblema":    _sub128(2, 1, pad=0.012),
    "cuadro_pasillo":   _sub128(3, 1, pad=0.012),
    "empedrado_rombo":  _sub128(4, 1, pad=0.012),
    "bandera_belgrano": _sub128(5, 1, pad=0.012),
    "escudo_bolivia":   _sub128(6, 1, pad=0.015),
    "madera_balcon":    (7 * 0.125 + 0.010, 0.0625 + 0.008, 8 * 0.125 - 0.010, 0.125 - 0.008),
    "vereda_gris":      (7 * 0.125 + 0.010, 0.008,          8 * 0.125 - 0.010, 0.0625 - 0.008),
}


def cell_uv(cell_key: str) -> tuple[float, float, float, float]:
    return ATLAS_REGIONS[cell_key]


def _connect_image(nt, bsdf, path: str, colorspace: str, target_input: str | None = None,
                   interpolation: str = "Linear") -> bpy.types.ShaderNodeTexImage | None:
    if not os.path.exists(path):
        return None
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = colorspace
    img.reload()
    tex.image = img
    tex.interpolation = interpolation
    if target_input and target_input in bsdf.inputs:
        nt.links.new(tex.outputs["Color"], bsdf.inputs[target_input])
    return tex


def _connect_normal(nt, bsdf, path: str, strength: float = 1.0):
    tex = _connect_image(nt, bsdf, path, "Non-Color", target_input=None)
    if tex is None or "Normal" not in bsdf.inputs:
        return
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.space = "TANGENT"
    nmap.inputs["Strength"].default_value = strength
    nt.links.new(tex.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])


def get_or_create_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")

    if name == "atlas_museo":
        bsdf.inputs["Roughness"].default_value = 0.65
        bsdf.inputs["Metallic"].default_value = 0.0
        _connect_image(nt, bsdf, ATLAS_BASE_PATH, "sRGB", "Base Color")
        etex = _connect_image(nt, bsdf, ATLAS_EMIT_PATH, "sRGB", None)
        if etex is not None and "Emission Color" in bsdf.inputs:
            nt.links.new(etex.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = 2.6
        _connect_image(nt, bsdf, ATLAS_ROUGH_PATH, "Non-Color", "Roughness")
        _connect_normal(nt, bsdf, ATLAS_NORM_PATH, strength=1.0)
        mat.diffuse_color = (0.65, 0.25, 0.25, 1.0)
        return mat

    if name == "vidrio_vitrina":
        bsdf.inputs["Base Color"].default_value = (0.90, 0.96, 0.98, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.05
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Alpha"].default_value = 0.09
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.0
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.45
        if hasattr(mat, "blend_method"):
            mat.blend_method = "BLEND"
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        if hasattr(mat, "show_transparent_back"):
            mat.show_transparent_back = False
        mat.diffuse_color = (0.85, 0.94, 0.98, 0.14)
        return mat

    r, g, b, a, rough, metal = MATERIAL_DEFS[name]
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (r, g, b, a)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        _connect_image(nt, bsdf, os.path.join(PBR_DIR, f"{name}_albedo.jpg"), "sRGB", "Base Color")
        _connect_image(nt, bsdf, os.path.join(PBR_DIR, f"{name}_roughness.jpg"), "Non-Color", "Roughness")
        _connect_normal(
            nt,
            bsdf,
            os.path.join(PBR_DIR, f"{name}_normal.jpg"),
            strength=PBR_NORMAL_STRENGTH.get(name, 0.9),
        )
    mat.diffuse_color = (r, g, b, a)
    return mat


# ---------------------------------------------------------------------------
# CONSTRUCTOR DE MALLAS CON UVs POR CARA E INSTANCIACION
# ---------------------------------------------------------------------------

class MeshBuilder:
    """Acumula geometria en una sola malla Blender con slots de material y UVs cubicas en metros."""

    def __init__(self, name: str):
        self.name = name
        self.verts: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, ...]] = []
        self.face_mats: list[str] = []
        self.face_uvs: list[list[tuple[float, float]]] = []
        self.face_has_explicit_uv: list[bool] = []

    def _add_face(self, v_indices: tuple[int, ...], mat_name: str,
                  uv_coords: list[tuple[float, float]] | None = None,
                  explicit_uv: bool = False):
        self.faces.append(v_indices)
        self.face_mats.append(mat_name)
        if uv_coords is not None:
            self.face_uvs.append(uv_coords)
            self.face_has_explicit_uv.append(explicit_uv)
        else:
            self.face_uvs.append([(0.0, 0.0) for _ in v_indices])
            self.face_has_explicit_uv.append(False)

    def add_quad(self, p0, p1, p2, p3, mat_name: str, uv_box: tuple[float, float, float, float] | None = None):
        idx = len(self.verts)
        self.verts.extend([p0, p1, p2, p3])
        if uv_box:
            u0, v0, u1, v1 = uv_box
            uvs = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            self._add_face((idx, idx + 1, idx + 2, idx + 3), mat_name, uvs, explicit_uv=True)
        else:
            self._add_face((idx, idx + 1, idx + 2, idx + 3), mat_name, None, explicit_uv=False)

    def add_tri(self, p0, p1, p2, mat_name: str, uv_coords=None):
        idx = len(self.verts)
        self.verts.extend([p0, p1, p2])
        self._add_face((idx, idx + 1, idx + 2), mat_name, uv_coords, explicit_uv=uv_coords is not None)

    def add_box(self, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float,
                mat_name: str, atlas_cell: str | None = None, scale_uv: float = 1.0):
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        if z1 < z0:
            z0, z1 = z1, z0
        idx = len(self.verts)
        self.verts.extend([
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
        ])
        if atlas_cell:
            u0, v0, u1, v1 = cell_uv(atlas_cell)
            uv_quad = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            explicit = True
        else:
            uv_quad = None
            explicit = False

        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self._add_face(tuple(idx + k for k in f), mat_name, uv_quad, explicit_uv=explicit)

    def add_sloped_box(self, p00, p10, p11, p01, thick: float, mat_name: str, atlas_cell: str | None = None):
        idx = len(self.verts)
        self.verts.extend([
            p00, p10, p11, p01,
            (p00[0], p00[1], p00[2] + thick),
            (p10[0], p10[1], p10[2] + thick),
            (p11[0], p11[1], p11[2] + thick),
            (p01[0], p01[1], p01[2] + thick),
        ])
        if atlas_cell:
            u0, v0, u1, v1 = cell_uv(atlas_cell)
            uv_quad = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            explicit = True
        else:
            uv_quad = None
            explicit = False
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self._add_face(tuple(idx + k for k in f), mat_name, uv_quad, explicit_uv=explicit)

    def add_beam(self, p0: tuple[float, float, float], p1: tuple[float, float, float],
                 radius: float, segs: int, mat_name: str):
        """Crea un cilindro/barra entre dos puntos 3D arbitrarios (para arco, flecha, brazos)."""
        v0 = Vector(p0)
        v1 = Vector(p1)
        axis = v1 - v0
        length = axis.length
        if length < 1e-5:
            return
        z_dir = axis.normalized()
        up = Vector((0, 0, 1)) if abs(z_dir.z) < 0.95 else Vector((1, 0, 0))
        x_dir = up.cross(z_dir).normalized()
        y_dir = z_dir.cross(x_dir).normalized()

        idx = len(self.verts)
        for base in (v0, v1):
            for k in range(segs):
                ang = 2.0 * math.pi * k / segs
                pt = base + (x_dir * math.cos(ang) + y_dir * math.sin(ang)) * radius
                self.verts.append((pt.x, pt.y, pt.z))

        self._add_face(tuple(idx + k for k in range(segs - 1, -1, -1)), mat_name)
        self._add_face(tuple(idx + segs + k for k in range(segs)), mat_name)
        for k in range(segs):
            kn = (k + 1) % segs
            self._add_face((idx + k, idx + kn, idx + segs + kn, idx + segs + k), mat_name)

    def add_cylinder(self, x: float, y: float, z0: float, z1: float, r_bot: float, r_top: float,
                     segs: int, mat_name: str, atlas_cell: str | None = None, cap_top: bool = True, cap_bot: bool = True):
        idx = len(self.verts)
        for k in range(segs):
            ang = 2.0 * math.pi * k / segs
            self.verts.append((x + math.cos(ang) * r_bot, y + math.sin(ang) * r_bot, z0))
        for k in range(segs):
            ang = 2.0 * math.pi * k / segs
            self.verts.append((x + math.cos(ang) * r_top, y + math.sin(ang) * r_top, z1))

        uv_atlas = None
        if atlas_cell:
            u0, v0, u1, v1 = cell_uv(atlas_cell)
            uv_atlas = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

        if cap_bot:
            bot_f = tuple(idx + k for k in range(segs - 1, -1, -1))
            self._add_face(bot_f, mat_name, [uv_atlas[0]] * segs if uv_atlas else None, explicit_uv=bool(uv_atlas))
        if cap_top:
            top_f = tuple(idx + segs + k for k in range(segs))
            self._add_face(top_f, mat_name, [uv_atlas[2]] * segs if uv_atlas else None, explicit_uv=bool(uv_atlas))

        tile = UV_TILE_METERS.get(mat_name, 1.8)
        circ = math.pi * max(r_bot + r_top, 0.05)
        v_bot, v_top = z0 / tile, z1 / tile
        for k in range(segs):
            kn = (k + 1) % segs
            if uv_atlas:
                uvs = uv_atlas
            else:
                u_a = (k / segs) * (circ / tile)
                u_b = ((k + 1) / segs) * (circ / tile)
                uvs = [(u_a, v_bot), (u_b, v_bot), (u_b, v_top), (u_a, v_top)]
            self._add_face((idx + k, idx + kn, idx + segs + kn, idx + segs + k), mat_name, uvs, explicit_uv=True)

    def add_disc_y(self, cx: float, cy: float, cz: float, radius: float, depth: float, segs: int,
                   mat_name: str, atlas_cell: str | None = None, facing_neg_y: bool = True,
                   rim_mat: str | None = None):
        """Disco o medallon vertical mirando a -Y o +Y, con UVs circulares centradas si usa atlas."""
        y_front = cy if facing_neg_y else cy - depth
        y_back = cy + depth if facing_neg_y else cy
        c_idx = len(self.verts)
        self.verts.append((cx, y_front, cz))
        for k in range(segs):
            ang = 2.0 * math.pi * k / segs
            self.verts.append((cx + math.cos(ang) * radius, y_front, cz + math.sin(ang) * radius))
        for k in range(segs):
            ang = 2.0 * math.pi * k / segs
            self.verts.append((cx + math.cos(ang) * radius, y_back, cz + math.sin(ang) * radius))

        has_atlas = atlas_cell is not None
        u0, v0, u1, v1 = cell_uv(atlas_cell) if has_atlas else (0.0, 0.0, 1.0, 1.0)
        um, vm = (u0 + u1) * 0.5, (v0 + v1) * 0.5
        ur, vr = (u1 - u0) * 0.48, (v1 - v0) * 0.48

        for k in range(segs):
            kn = (k + 1) % segs
            a0 = 2.0 * math.pi * k / segs
            a1 = 2.0 * math.pi * kn / segs
            if facing_neg_y:
                # normal mirando hacia -Y (al espectador en frente de la fachada)
                uvs = [
                    (um, vm),
                    (um + math.cos(a0) * ur, vm + math.sin(a0) * vr),
                    (um + math.cos(a1) * ur, vm + math.sin(a1) * vr),
                ] if has_atlas else None
                self._add_face((c_idx, c_idx + 1 + k, c_idx + 1 + kn), mat_name, uvs, explicit_uv=has_atlas)
            else:
                uvs = [
                    (um, vm),
                    (um - math.cos(a1) * ur, vm + math.sin(a1) * vr),
                    (um - math.cos(a0) * ur, vm + math.sin(a0) * vr),
                ] if has_atlas else None
                self._add_face((c_idx, c_idx + 1 + kn, c_idx + 1 + k), mat_name, uvs, explicit_uv=has_atlas)
            self._add_face(
                (c_idx + 1 + k, c_idx + 1 + kn, c_idx + 1 + segs + kn, c_idx + 1 + segs + k),
                rim_mat if rim_mat else ("piedra" if has_atlas else mat_name),
            )

    def add_sphere_octa(self, cx: float, cy: float, cz: float, rx: float, ry: float, rz: float,
                        mat_name: str, atlas_cell: str | None = None):
        idx = len(self.verts)
        self.verts.extend([
            (cx, cy, cz + rz), (cx, cy, cz - rz),
            (cx + rx, cy, cz), (cx - rx, cy, cz),
            (cx, cy + ry, cz), (cx, cy - ry, cz),
        ])
        uvs = None
        if atlas_cell:
            u0, v0, u1, v1 = cell_uv(atlas_cell)
            um, vm = (u0 + u1) * 0.5, (v0 + v1) * 0.5
            uvs = [(u0, v0), (u1, v0), (um, v1)]
        for f in (
            (0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2),
            (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5),
        ):
            self._add_face(tuple(idx + k for k in f), mat_name, uvs, explicit_uv=bool(atlas_cell))

    def add_arch_spandrel(self, x_center: float, span: float, y0: float, y1: float,
                          z_spring: float, z_top: float, arch_h: float, segs: int, mat_name: str,
                          ring_mat: str | None = None, ring_thick: float = 0.0, ring_out: float = 0.0):
        half = span * 0.5
        arch_pts = []
        for k in range(segs + 1):
            ang = math.pi * (1.0 - k / segs)
            arch_pts.append((x_center + math.cos(ang) * half, z_spring + math.sin(ang) * arch_h))

        idx = len(self.verts)
        for ax, az in arch_pts:
            self.verts.append((ax, y0, az))
        for ax, _ in arch_pts:
            self.verts.append((ax, y0, z_top))
        for ax, az in arch_pts:
            self.verts.append((ax, y1, az))
        for ax, _ in arch_pts:
            self.verts.append((ax, y1, z_top))

        n = segs + 1
        for k in range(segs):
            self._add_face((idx + k, idx + k + 1, idx + n + k + 1, idx + n + k), mat_name)
            self._add_face((idx + 2 * n + k + 1, idx + 2 * n + k, idx + 3 * n + k, idx + 3 * n + k + 1), mat_name)
            self._add_face((idx + k + 1, idx + k, idx + 2 * n + k, idx + 2 * n + k + 1), mat_name)
            self._add_face((idx + n + k, idx + n + k + 1, idx + 3 * n + k + 1, idx + 3 * n + k), mat_name)
        self._add_face((idx, idx + n, idx + 3 * n, idx + 2 * n), mat_name)
        self._add_face((idx + segs, idx + 2 * n + segs, idx + 3 * n + segs, idx + n + segs), mat_name)

        if ring_mat and ring_thick > 0.0:
            self.add_arch_ring(x_center, half, ring_thick, y0 - ring_out, y1 + ring_out, z_spring, arch_h, segs, ring_mat)

    def add_arch_ring(self, x_center: float, r_in: float, thick: float, y0: float, y1: float,
                      z_spring: float, arch_h: float, segs: int, mat_name: str):
        r_out = r_in + thick
        h_out = arch_h + thick
        in_pts, out_pts = [], []
        for k in range(segs + 1):
            ang = math.pi * (1.0 - k / segs)
            in_pts.append((x_center + math.cos(ang) * r_in, z_spring + math.sin(ang) * arch_h))
            out_pts.append((x_center + math.cos(ang) * r_out, z_spring + math.sin(ang) * h_out))

        idx = len(self.verts)
        n = segs + 1
        for ax, az in in_pts:
            self.verts.append((ax, y0, az))
        for ax, az in out_pts:
            self.verts.append((ax, y0, az))
        for ax, az in in_pts:
            self.verts.append((ax, y1, az))
        for ax, az in out_pts:
            self.verts.append((ax, y1, az))

        for k in range(segs):
            self._add_face((idx + k, idx + k + 1, idx + n + k + 1, idx + n + k), mat_name)
            self._add_face((idx + 2 * n + k + 1, idx + 2 * n + k, idx + 3 * n + k, idx + 3 * n + k + 1), mat_name)
            self._add_face((idx + k + 1, idx + k, idx + 2 * n + k, idx + 2 * n + k + 1), mat_name)
            self._add_face((idx + n + k, idx + n + k + 1, idx + 3 * n + k + 1, idx + 3 * n + k), mat_name)
        self._add_face((idx, idx + n, idx + 3 * n, idx + 2 * n), mat_name)
        self._add_face((idx + segs, idx + 2 * n + segs, idx + 3 * n + segs, idx + n + segs), mat_name)

    def build_mesh(self, smooth_angle_deg: float = 48.0) -> bpy.types.Mesh:
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.verts, [], self.faces)

        mat_index = {}
        for m_name in self.face_mats:
            if m_name not in mat_index:
                mat_index[m_name] = len(mesh.materials)
                mesh.materials.append(get_or_create_material(m_name))

        for i, poly in enumerate(mesh.polygons):
            poly.material_index = mat_index[self.face_mats[i]]
            poly.use_smooth = False

        uv_layer = mesh.uv_layers.new(name="UVMap")
        verts_co = mesh.vertices
        loops = mesh.loops
        for i, poly in enumerate(mesh.polygons):
            m_name = self.face_mats[i]
            if self.face_has_explicit_uv[i] or m_name == "atlas_museo":
                uvs = self.face_uvs[i]
                for li, loop_idx in enumerate(poly.loop_indices):
                    uv_layer.data[loop_idx].uv = uvs[li % len(uvs)]
            else:
                tile = UV_TILE_METERS.get(m_name, 1.8)
                n = poly.normal
                ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
                for loop_idx in poly.loop_indices:
                    co = verts_co[loops[loop_idx].vertex_index].co
                    if ax >= ay and ax >= az:
                        u, v = co.y / tile, co.z / tile
                    elif ay >= ax and ay >= az:
                        u, v = co.x / tile, co.z / tile
                    elif m_name == "teja" and ax > ay + 0.05:
                        u, v = co.y / tile, co.x / tile
                    else:
                        u, v = co.x / tile, co.y / tile
                    uv_layer.data[loop_idx].uv = (u, v)

        # Soldado ligero y Shade Smooth por angulo (suaviza columnas, arcos, fuente y pinaculos
        # sin difuminar aristas arquitectonicas >= smooth_angle_deg)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bm.normal_update()
        max_ang = math.radians(smooth_angle_deg)
        sharp_edges = []
        for e in bm.edges:
            if len(e.link_faces) == 2:
                f0, f1 = e.link_faces[0], e.link_faces[1]
                if f0.material_index != f1.material_index or e.calc_face_angle(0.0) > max_ang:
                    sharp_edges.append(e)
            else:
                sharp_edges.append(e)
        for f in bm.faces:
            f.smooth = True
        if sharp_edges:
            bmesh.ops.split_edges(bm, edges=sharp_edges)
        bm.to_mesh(mesh)
        bm.free()

        mesh.update()
        return mesh

    def to_object(self, col, obj_name: str | None = None,
                  loc: tuple[float, float, float] = (0.0, 0.0, 0.0),
                  rot_z_deg: float = 0.0) -> bpy.types.Object:
        mesh = self.build_mesh()
        obj = bpy.data.objects.new(obj_name or self.name, mesh)
        obj.location = loc
        obj.rotation_euler = (0.0, 0.0, math.radians(rot_z_deg))
        col.objects.link(obj)
        return obj


def spawn_instance(col, name: str, shared_mesh: bpy.types.Mesh,
                   loc: tuple[float, float, float], rot_z_deg: float = 0.0,
                   scale: tuple[float, float, float] = (1.0, 1.0, 1.0)) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, shared_mesh)
    obj.location = loc
    obj.rotation_euler = (0.0, 0.0, math.radians(rot_z_deg))
    obj.scale = scale
    col.objects.link(obj)
    return obj


# ---------------------------------------------------------------------------
# LIMPIEZA Y COLECCIONES
# ---------------------------------------------------------------------------

def reset_scene_clean():
    existing = bpy.data.collections.get(ROOT_COLLECTION_NAME)
    if existing:
        for obj in list(existing.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for child in list(existing.children):
            bpy.data.collections.remove(child)
        bpy.data.collections.remove(existing)

    for obj in list(bpy.data.objects):
        if obj.name in ("Cube",) or obj.name.startswith(("CL_", "POI_", "LUZ_", "CAM_", "_Flechero")):
            bpy.data.objects.remove(obj, do_unlink=True)

    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        if mat.users == 0 or mat.name in VALID_MATERIALS:
            bpy.data.materials.remove(mat)
    for img in list(bpy.data.images):
        if img.users == 0:
            bpy.data.images.remove(img)


def get_collection(name: str, parent=None) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        if parent is None:
            bpy.context.scene.collection.children.link(col)
        else:
            parent.children.link(col)
    return col


def add_empty(col, name: str, loc: tuple[float, float, float], display_type: str = "PLAIN_AXES", size: float = 0.45):
    emp = bpy.data.objects.new(name, None)
    emp.empty_display_type = display_type
    emp.empty_display_size = size
    emp.location = loc
    col.objects.link(emp)
    return emp


# ---------------------------------------------------------------------------
# HELPERS REUTILIZABLES DE DETALLE COLONIAL (SIN DUPLICACION)
# ---------------------------------------------------------------------------

def add_curved_baroque_crest(mb: MeshBuilder, y0: float, y1: float, z_base: float,
                             half_w: float, height: float, mat_name: str, segs: int = 6):
    """Cresta barroca continua y curva (sin escalones en bloque) con remate central tallado."""
    pts_top = []
    for k in range(segs + 1):
        t = k / segs
        x = -half_w + 2.0 * half_w * t
        profile = 0.22 + 0.78 * (math.sin(math.pi * t) ** 1.35)
        pts_top.append((x, z_base + height * profile))

    for k in range(segs):
        x0_p, z0_p = pts_top[k]
        x1_p, z1_p = pts_top[k + 1]
        mb.add_quad((x0_p, y0, z_base), (x1_p, y0, z_base), (x1_p, y0, z1_p), (x0_p, y0, z0_p), mat_name)
        mb.add_quad((x1_p, y1, z_base), (x0_p, y1, z_base), (x0_p, y1, z0_p), (x1_p, y1, z1_p), mat_name)
        mb.add_quad((x0_p, y0, z0_p), (x1_p, y0, z1_p), (x1_p, y1, z1_p), (x0_p, y1, z0_p), mat_name)
        mb.add_quad((x1_p, y0, z_base), (x0_p, y0, z_base), (x0_p, y1, z_base), (x1_p, y1, z_base), mat_name)
    mb.add_quad((pts_top[0][0], y1, z_base), (pts_top[0][0], y0, z_base), (pts_top[0][0], y0, pts_top[0][1]), (pts_top[0][0], y1, pts_top[0][1]), mat_name)
    mb.add_quad((pts_top[-1][0], y0, z_base), (pts_top[-1][0], y1, z_base), (pts_top[-1][0], y1, pts_top[-1][1]), (pts_top[-1][0], y0, pts_top[-1][1]), mat_name)
    mb.add_cylinder(0.0, (y0 + y1) * 0.5, z_base + height * 0.88, z_base + height + 0.08, 0.052, 0.018, 6, mat_name, cap_bot=False)


def add_curved_s_arm(mb: MeshBuilder, p_hub: tuple[float, float, float], ang: float,
                     r_mid: float, z_mid: float, r_tip: float, z_tip: float,
                     radius: float = 0.013, segs: int = 4):
    """Brazo curvo en S para arana colonial (3 tramos delgados + platillo bobeche + vela)."""
    ca, sa = math.cos(ang), math.sin(ang)
    p1 = (ca * r_mid * 0.52, sa * r_mid * 0.52, (p_hub[2] + z_mid) * 0.5 - 0.03)
    p2 = (ca * r_mid, sa * r_mid, z_mid)
    p3 = (ca * r_tip, sa * r_tip, z_tip)
    mb.add_beam(p_hub, p1, radius, segs, "oro_bronce")
    mb.add_beam(p1, p2, radius * 0.92, segs, "oro_bronce")
    mb.add_beam(p2, p3, radius * 0.85, segs, "oro_bronce")
    # Platillo bobeche dorado + vela + llama emisiva
    mb.add_cylinder(p3[0], p3[1], z_tip, z_tip + 0.022, 0.052, 0.036, 6, "oro_bronce", cap_bot=False)
    mb.add_cylinder(p3[0], p3[1], z_tip + 0.022, z_tip + 0.145, 0.017, 0.015, 4, "muro", cap_bot=False, cap_top=False)
    mb.add_cylinder(p3[0], p3[1], z_tip + 0.145, z_tip + 0.215, 0.022, 0.004, 4, "atlas_museo", "vela", cap_bot=False)


def add_beveled_frame_painting(mb: MeshBuilder, cx: float, cy: float, cz: float,
                               width: float, height: float, facing: str,
                               cell_key: str, frame_w: float = 0.075, depth: float = 0.055):
    """Cuadro con marco moldurado perimetral de 4 listones en oro_bronce y lienzo en relieve."""
    hw, hh = width * 0.5, height * 0.5
    u0, v0, u1, v1 = cell_uv(cell_key)
    d_in = depth * 0.55

    if facing in ("-Y", "+Y"):
        sgn = -1.0 if facing == "-Y" else 1.0
        y_wall = cy
        y_outer = cy + sgn * depth
        y_y0, y_y1 = sorted((y_wall, y_outer))
        # Listones del marco dorado (top, bottom, left, right) + moldura escalonada
        mb.add_box(cx - hw - frame_w, cx + hw + frame_w, y_y0, y_y1, cz + hh, cz + hh + frame_w, "oro_bronce")
        mb.add_box(cx - hw - frame_w, cx + hw + frame_w, y_y0, y_y1, cz - hh - frame_w, cz - hh, "oro_bronce")
        mb.add_box(cx - hw - frame_w, cx - hw, y_y0, y_y1, cz - hh, cz + hh, "oro_bronce")
        mb.add_box(cx + hw, cx + hw + frame_w, y_y0, y_y1, cz - hh, cz + hh, "oro_bronce")
        # Reborde interior oscuro en cedro
        y_f0, y_f1 = sorted((y_wall, cy + sgn * (depth * 0.72)))
        mb.add_box(cx - hw, cx + hw, y_f0, y_f1, cz - hh, cz + hh, "madera")
        yq = cy + sgn * (depth * 0.78)
        if facing == "-Y":
            mb.add_quad((cx - hw, yq, cz - hh), (cx + hw, yq, cz - hh), (cx + hw, yq, cz + hh), (cx - hw, yq, cz + hh), "atlas_museo", (u0, v0, u1, v1))
        else:
            mb.add_quad((cx + hw, yq, cz - hh), (cx - hw, yq, cz - hh), (cx - hw, yq, cz + hh), (cx + hw, yq, cz + hh), "atlas_museo", (u0, v0, u1, v1))
    else:
        sgn = -1.0 if facing == "-X" else 1.0
        x_wall = cx
        x_outer = cx + sgn * depth
        x_x0, x_x1 = sorted((x_wall, x_outer))
        mb.add_box(x_x0, x_x1, cy - hw - frame_w, cy + hw + frame_w, cz + hh, cz + hh + frame_w, "oro_bronce")
        mb.add_box(x_x0, x_x1, cy - hw - frame_w, cy + hw + frame_w, cz - hh - frame_w, cz - hh, "oro_bronce")
        mb.add_box(x_x0, x_x1, cy - hw - frame_w, cy - hw, cz - hh, cz + hh, "oro_bronce")
        mb.add_box(x_x0, x_x1, cy + hw, cy + hw + frame_w, cz - hh, cz + hh, "oro_bronce")
        x_f0, x_f1 = sorted((x_wall, cx + sgn * (depth * 0.72)))
        mb.add_box(x_f0, x_f1, cy - hw, cy + hw, cz - hh, cz + hh, "madera")
        xq = cx + sgn * (depth * 0.78)
        if facing == "-X":
            mb.add_quad((xq, cy + hw, cz - hh), (xq, cy - hw, cz - hh), (xq, cy - hw, cz + hh), (xq, cy + hw, cz + hh), "atlas_museo", (u0, v0, u1, v1))
        else:
            mb.add_quad((xq, cy - hw, cz - hh), (xq, cy + hw, cz - hh), (xq, cy + hw, cz + hh), (xq, cy - hw, cz + hh), "atlas_museo", (u0, v0, u1, v1))


def add_vitrine_glass_box(mb: MeshBuilder, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float):
    """Paneles delgados de vidrio ligero (Alpha Blend, sin Transmission) para vitrinas."""
    t = 0.006
    mb.add_box(x0, x1, y0, y0 + t, z0, z1, "vidrio_vitrina")  # frente
    mb.add_box(x0, x1, y1 - t, y1, z0, z1, "vidrio_vitrina")  # fondo
    mb.add_box(x0, x0 + t, y0 + t, y1 - t, z0, z1, "vidrio_vitrina")  # izq
    mb.add_box(x1 - t, x1, y0 + t, y1 - t, z0, z1, "vidrio_vitrina")  # der
    mb.add_box(x0, x1, y0, y1, z1 - t, z1, "vidrio_vitrina")  # tapa superior


# ---------------------------------------------------------------------------
# KIT MODULAR REUTILIZABLE (MALLAS COMPARTIDAS)
# ---------------------------------------------------------------------------

def build_modular_kit() -> dict[str, bpy.types.Mesh]:
    kit = {}

    # 1. Ventana colonial planta baja (relieve de madera + vidrio oscuro + reja cilindrica)
    mb = MeshBuilder("M_Ventana_Baja")
    h_v = 2.15
    mb.add_box(-0.78, -0.62, -0.09, 0.14, -0.05, h_v, "piedra")
    mb.add_box(0.62, 0.78, -0.09, 0.14, -0.05, h_v, "piedra")
    mb.add_box(-0.88, 0.88, -0.14, 0.14, -0.11, 0.0, "piedra")     # alfeizar saliente
    mb.add_box(-0.76, 0.76, -0.08, 0.12, -0.22, -0.11, "piedra")   # sobremarco inferior
    mb.add_arch_ring(0.0, 0.62, 0.16, -0.09, 0.14, h_v, 0.24, 12, "piedra")
    mb.add_box(-0.08, 0.08, -0.11, 0.14, h_v + 0.22, h_v + 0.44, "piedra")  # clave del arco
    # Vidrio oscuro en el fondo del vano + bastidor y tableros bajos de madera en relieve
    mb.add_box(-0.60, 0.60, 0.10, 0.14, 0.56, h_v + 0.18, "atlas_museo", "vidrio")
    mb.add_box(-0.62, 0.62, 0.04, 0.11, 0.0, 0.56, "madera")  # antepecho interior madera
    for sx in (-0.31, 0.31):
        mb.add_box(sx - 0.23, sx + 0.23, 0.02, 0.05, 0.07, 0.49, "madera")  # tablero en relieve
    for x in (-0.62, -0.03, 0.56):
        mb.add_box(x, x + 0.06, 0.03, 0.12, 0.0, h_v + 0.16, "madera")
    for z in (0.0, 0.56, 1.12, 1.68, h_v):
        mb.add_box(-0.62, 0.62, 0.03, 0.12, z, z + 0.05, "madera")
    for k in range(6):
        rx = -0.50 + k * 0.20
        mb.add_cylinder(rx, -0.025, 0.0, h_v + 0.18, 0.015, 0.015, 6, "hierro")
    for rz in (0.28, 0.88, 1.48, 2.04):
        mb.add_box(-0.62, 0.62, -0.04, -0.01, rz - 0.016, rz + 0.016, "hierro")
    kit["ventana_baja"] = mb.build_mesh()

    # 1b. Ventana exterior fachada (piedra_fachada oscura + vidrio profundo por delante del muro Y=0)
    mb = MeshBuilder("M_Ventana_Fachada")
    mb.add_box(-0.78, -0.62, -0.10, 0.04, -0.05, h_v, "piedra_fachada")
    mb.add_box(0.62, 0.78, -0.10, 0.04, -0.05, h_v, "piedra_fachada")
    mb.add_box(-0.88, 0.88, -0.14, 0.04, -0.11, 0.0, "piedra_fachada")
    mb.add_box(-0.76, 0.76, -0.09, 0.04, -0.22, -0.11, "piedra_fachada")
    mb.add_arch_ring(0.0, 0.62, 0.16, -0.10, 0.04, h_v, 0.24, 12, "piedra_fachada")
    mb.add_box(-0.08, 0.08, -0.12, 0.04, h_v + 0.22, h_v + 0.44, "piedra_fachada")
    # Vidrio oscuro profundo y respaldo en cedro delante de Y=0 (spawn en -0.02 -> cara visible en Y=-0.03)
    mb.add_box(-0.62, 0.62, -0.010, 0.015, 0.0, h_v + 0.20, "atlas_museo", "vidrio")
    mb.add_box(-0.62, 0.62, -0.016, 0.010, 0.0, 0.56, "madera")
    for sx in (-0.31, 0.31):
        mb.add_box(sx - 0.23, sx + 0.23, -0.024, -0.014, 0.07, 0.49, "madera")
    for x in (-0.62, -0.03, 0.56):
        mb.add_box(x, x + 0.06, -0.024, -0.008, 0.0, h_v + 0.16, "madera")
    for z in (0.0, 0.56, 1.12, 1.68, h_v):
        mb.add_box(-0.62, 0.62, -0.024, -0.008, z, z + 0.05, "madera")
    for k in range(6):
        rx = -0.50 + k * 0.20
        mb.add_cylinder(rx, -0.052, 0.0, h_v + 0.18, 0.015, 0.015, 6, "hierro")
    for rz in (0.28, 0.88, 1.48, 2.04):
        mb.add_box(-0.62, 0.62, -0.066, -0.038, rz - 0.016, rz + 0.016, "hierro")
    kit["ventana_fachada"] = mb.build_mesh()

    # 2. Balcon colonial corrido de madera (mensulas oscuras + balaustrada calida + puertas oscuras)
    mb = MeshBuilder("M_Balcon_Colonial")
    bw, hw, vuelo = 6.20, 3.10, 1.05
    mb.add_box(-hw, hw, -vuelo, 0.02, -0.18, 0.0, "madera")
    for k in range(5):
        mx = -hw + 0.35 + k * (bw - 0.70) / 4.0
        mb.add_box(mx - 0.08, mx + 0.08, -vuelo + 0.08, 0.0, -0.34, -0.18, "madera")
        mb.add_box(mx - 0.08, mx + 0.08, -vuelo * 0.62, 0.0, -0.52, -0.34, "madera")
        mb.add_box(mx - 0.08, mx + 0.08, -vuelo * 0.32, 0.0, -0.70, -0.52, "madera")
    # Antepecho con moldura y tableros calidos en madera_balcon (contraste legible con vigas oscuras)
    mb.add_box(-hw + 0.04, hw - 0.04, -vuelo, -vuelo + 0.08, 0.0, 0.38, "atlas_museo", "madera_balcon")
    mb.add_box(-hw - 0.02, hw + 0.02, -vuelo - 0.03, -vuelo + 0.08, 0.34, 0.40, "atlas_museo", "madera_balcon")
    for tp in range(8):
        tx = -hw + 0.44 + tp * 0.76
        mb.add_box(tx - 0.28, tx + 0.28, -vuelo - 0.025, -vuelo, 0.06, 0.32, "atlas_museo", "madera_balcon")
    mb.add_box(-hw + 0.04, -hw + 0.12, -vuelo, 0.0, 0.0, 0.38, "atlas_museo", "madera_balcon")
    mb.add_box(hw - 0.12, hw - 0.04, -vuelo, 0.0, 0.0, 0.38, "atlas_museo", "madera_balcon")
    mb.add_box(-hw, hw, -vuelo - 0.02, -vuelo + 0.10, 0.96, 1.06, "atlas_museo", "madera_balcon")
    mb.add_box(-hw, -hw + 0.10, -vuelo, 0.0, 0.96, 1.04, "atlas_museo", "madera_balcon")
    mb.add_box(hw - 0.10, hw, -vuelo, 0.0, 0.96, 1.04, "atlas_museo", "madera_balcon")
    bx = -hw + 0.26
    while bx < hw - 0.22:
        mb.add_cylinder(bx, -vuelo + 0.04, 0.38, 0.96, 0.030, 0.022, 6, "atlas_museo", "madera_balcon", cap_top=False, cap_bot=False)
        bx += 0.29
    for k in range(4):
        px = -hw + 0.14 + k * (bw - 0.28) / 3.0
        mb.add_box(px - 0.07, px + 0.07, -vuelo, -vuelo + 0.12, 0.0, 1.15, "atlas_museo", "madera_balcon")
        mb.add_cylinder(px, -vuelo + 0.06, 1.15, 3.12, 0.062, 0.048, 8, "atlas_museo", "madera_balcon", cap_top=False, cap_bot=False)
        mb.add_cylinder(px, -vuelo + 0.06, 3.12, 3.22, 0.048, 0.078, 8, "atlas_museo", "madera_balcon", cap_top=False, cap_bot=False)
        mb.add_box(px - 0.075, px + 0.075, -vuelo - 0.24, 0.0, 3.22, 3.36, "madera")
    mb.add_sloped_box(
        (-hw - 0.20, -vuelo - 0.35, 3.22), (hw + 0.20, -vuelo - 0.35, 3.22),
        (hw + 0.20, 0.0, 3.72), (-hw - 0.20, 0.0, 3.72), 0.14, "teja",
    )
    for vx in (-1.60, 1.60):
        # Vidrio y carpinteria oscura por delante del muro blanco Y=0 (y_local <= 0.01)
        mb.add_box(vx - 0.60, vx + 0.60, -0.012, 0.015, 0.0, 2.40, "atlas_museo", "vidrio")
        mb.add_box(vx - 0.60, vx + 0.60, -0.020, 0.010, 0.0, 0.72, "madera")
        for sx in (vx - 0.30, vx + 0.30):
            mb.add_box(sx - 0.22, sx + 0.22, -0.030, -0.018, 0.10, 0.62, "madera")
        for x in (vx - 0.60, vx - 0.03, vx + 0.54):
            mb.add_box(x, x + 0.06, -0.028, -0.008, 0.0, 2.42, "madera")
        for z in (0.0, 0.72, 1.32, 1.88, 2.36):
            mb.add_box(vx - 0.60, vx + 0.60, -0.028, -0.008, z, z + 0.055, "madera")
        mb.add_box(vx - 0.74, vx + 0.74, -0.07, 0.04, 2.40, 2.56, "piedra_fachada")
    kit["balcon_colonial"] = mb.build_mesh()

    # 3. Columna de piedra del Claustro (12 segs suavizados + tapas ocultas omitidas)
    mb = MeshBuilder("M_Columna_Claustro")
    mb.add_box(-0.30, 0.30, -0.30, 0.30, -0.25, 0.52, "piedra")
    mb.add_cylinder(0.0, 0.0, 0.52, 0.68, 0.275, 0.22, 12, "piedra", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, 0.0, 0.68, 2.42, 0.21, 0.185, 12, "piedra", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, 0.0, 2.42, 2.48, 0.21, 0.21, 12, "piedra", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, 0.0, 2.48, 2.58, 0.20, 0.275, 12, "piedra", cap_top=False, cap_bot=False)
    mb.add_box(-0.31, 0.31, -0.31, 0.31, 2.58, 2.72, "piedra")
    kit["columna_claustro"] = mb.build_mesh()

    # 4. Modulo de arco de medio punto del claustro (5 arcos por lado -> bay=2.88m, 10 segs)
    mb = MeshBuilder("M_Arco_Claustro")
    mb.add_arch_spandrel(
        x_center=0.0, span=2.46, y0=-0.22, y1=0.22,
        z_spring=2.72, z_top=4.25, arch_h=1.05, segs=10,
        mat_name="muro", ring_mat="muro", ring_thick=0.14, ring_out=0.045,
    )
    mb.add_box(-1.44, -1.23, -0.23, 0.23, 2.72, 4.25, "muro")
    mb.add_box(1.23, 1.44, -0.23, 0.23, 2.72, 4.25, "muro")
    mb.add_box(-1.44, 1.44, -0.29, 0.29, 4.18, 4.26, "muro")
    kit["arco_claustro"] = mb.build_mesh()

    # 5. Puerta colonial cerrada DETALLADA (marco piedra + dintel madera + tableros + aldabas bronce)
    mb = MeshBuilder("M_Puerta_Cerrada")
    mb.add_box(-0.78, -0.62, -0.12, 0.14, 0.0, 2.48, "piedra")
    mb.add_box(0.62, 0.78, -0.12, 0.14, 0.0, 2.48, "piedra")
    mb.add_box(-0.92, 0.92, -0.16, 0.14, 2.48, 2.70, "madera")
    mb.add_box(-0.62, 0.62, 0.02, 0.12, 0.0, 2.48, "madera")
    mb.add_box(-0.03, 0.03, -0.02, 0.02, 0.04, 2.46, "madera")
    for sx in (-0.33, 0.33):
        for sz in (0.45, 1.25, 2.02):
            mb.add_box(sx - 0.21, sx + 0.21, -0.03, 0.02, sz - 0.27, sz + 0.27, "madera")
            mb.add_box(sx - 0.14, sx + 0.14, -0.05, -0.03, sz - 0.18, sz + 0.18, "madera")
        mb.add_cylinder(sx * 0.45, -0.055, 1.13, 1.22, 0.032, 0.038, 8, "oro_bronce", cap_bot=False)
    kit["puerta_cerrada"] = mb.build_mesh()

    # 6. Banca colonial de madera del claustro
    mb = MeshBuilder("M_Banca_Patio")
    mb.add_box(-0.85, 0.85, -0.24, 0.24, 0.42, 0.48, "madera")
    mb.add_box(-0.85, 0.85, 0.18, 0.24, 0.48, 1.02, "madera")
    for lx in (-0.82, 0.82):
        mb.add_box(lx - 0.04, lx + 0.04, -0.24, 0.24, 0.0, 0.42, "hierro")
        mb.add_box(lx - 0.03, lx + 0.03, -0.24, 0.22, 0.48, 0.68, "madera")
    kit["banca_patio"] = mb.build_mesh()

    # 7. Farol colonial colgante
    mb = MeshBuilder("M_Farol_Colonial")
    mb.add_cylinder(0.0, 0.0, 0.28, 0.62, 0.018, 0.018, 5, "hierro", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, 0.0, 0.20, 0.28, 0.14, 0.03, 6, "hierro", cap_top=False)
    mb.add_cylinder(0.0, 0.0, -0.08, 0.0, 0.03, 0.10, 6, "hierro", cap_bot=False)
    mb.add_cylinder(0.0, 0.0, 0.0, 0.20, 0.08, 0.11, 6, "atlas_museo", "vela", cap_top=False, cap_bot=False)
    for k in range(4):
        ang = k * math.pi * 0.5 + math.pi * 0.25
        px, py = math.cos(ang) * 0.10, math.sin(ang) * 0.10
        mb.add_box(px - 0.012, px + 0.012, py - 0.012, py + 0.012, -0.01, 0.21, "hierro")
    kit["farol_colonial"] = mb.build_mesh()

    # 8. Maceta colonial de terracota con vegetacion (10 segs suavizados)
    mb = MeshBuilder("M_Maceta_Patio")
    mb.add_cylinder(0.0, 0.0, 0.0, 0.10, 0.24, 0.24, 6, "hierro", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, 0.0, 0.08, 0.46, 0.16, 0.25, 10, "teja", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, 0.0, 0.46, 0.52, 0.27, 0.27, 10, "teja")
    mb.add_sphere_octa(0.0, 0.0, 0.72, 0.28, 0.28, 0.26, "atlas_museo", "follaje")
    mb.add_sphere_octa(0.14, 0.10, 0.88, 0.18, 0.18, 0.18, "atlas_museo", "follaje")
    mb.add_sphere_octa(-0.12, -0.10, 0.85, 0.17, 0.17, 0.17, "atlas_museo", "follaje")
    kit["maceta_patio"] = mb.build_mesh()

    # 9. Sitial superior de silleria del Salon (cresta barroca curva, sin bloques cuadrados)
    mb = MeshBuilder("M_Sitial_Sup")
    mb.add_box(-0.44, 0.44, -0.28, 0.28, 0.42, 0.48, "madera")
    mb.add_box(-0.44, 0.44, 0.20, 0.28, 0.48, 1.50, "madera")
    mb.add_box(-0.32, 0.32, 0.16, 0.20, 0.68, 1.38, "oro_bronce")
    mb.add_box(-0.46, 0.46, 0.14, 0.30, 1.48, 1.54, "oro_bronce")
    add_curved_baroque_crest(mb, 0.17, 0.27, 1.54, 0.41, 0.26, "oro_bronce", segs=6)
    for ax in (-0.43, 0.37):
        mb.add_box(ax, ax + 0.06, -0.26, 0.24, 0.0, 0.70, "madera")
    kit["sitial_sup"] = mb.build_mesh()

    # 10. Escano inferior azul-verde del Salon (cresta barroca curva suavizada)
    mb = MeshBuilder("M_Escano_Inf")
    mb.add_box(-0.44, 0.44, -0.26, 0.24, 0.38, 0.44, "atlas_museo", "azul_verde")
    mb.add_box(-0.44, 0.44, 0.18, 0.24, 0.44, 0.94, "atlas_museo", "azul_verde")
    mb.add_box(-0.42, 0.42, 0.15, 0.25, 0.94, 0.98, "oro_bronce")
    add_curved_baroque_crest(mb, 0.16, 0.24, 0.98, 0.38, 0.18, "oro_bronce", segs=5)
    for px in (-0.40, 0.36):
        mb.add_box(px, px + 0.05, -0.24, 0.22, 0.0, 0.38, "oro_bronce")
    kit["escano_inf"] = mb.build_mesh()

    # 11. Silla de diputado / presidio
    mb = MeshBuilder("M_Silla_Presidio")
    mb.add_box(-0.27, 0.27, -0.26, 0.26, 0.42, 0.48, "atlas_museo", "rojo")
    mb.add_box(-0.25, 0.25, 0.20, 0.26, 0.48, 1.16, "atlas_museo", "rojo")
    mb.add_box(-0.28, -0.23, 0.19, 0.27, 0.45, 1.18, "oro_bronce")
    mb.add_box(0.23, 0.28, 0.19, 0.27, 0.45, 1.18, "oro_bronce")
    add_curved_baroque_crest(mb, 0.19, 0.27, 1.16, 0.20, 0.14, "oro_bronce", segs=4)
    for lx in (-0.25, 0.20):
        for ly in (-0.24, 0.19):
            mb.add_box(lx, lx + 0.05, ly, ly + 0.05, 0.0, 0.42, "madera")
        mb.add_box(lx, lx + 0.05, -0.22, 0.22, 0.62, 0.67, "madera")
    kit["silla_presidio"] = mb.build_mesh()

    # 12. Ataud ceremonial universitario sobre andas
    mb = MeshBuilder("M_Ataud_Universitario")
    for vx in (-0.36, 0.36):
        mb.add_box(vx - 0.04, vx + 0.04, -1.25, 1.25, 0.46, 0.54, "madera")
        for ly in (-0.82, 0.74):
            mb.add_box(vx - 0.04, vx + 0.04, ly, ly + 0.08, 0.0, 0.46, "madera")
            mb.add_cylinder(vx, ly + 0.04, 0.54, 0.96, 0.045, 0.038, 8, "madera", cap_top=False, cap_bot=False)
            mb.add_box(vx - 0.06, vx + 0.06, ly - 0.02, ly + 0.10, 0.96, 1.04, "madera")
    mb.add_box(-0.34, 0.34, -0.80, 0.80, 0.54, 0.88, "madera")
    mb.add_box(-0.36, 0.36, -0.82, 0.82, 0.88, 0.96, "oro_bronce")
    mb.add_box(-0.28, 0.28, -0.76, 0.76, 0.96, 1.12, "madera")
    mb.add_box(-0.22, 0.22, -0.82, -0.78, 0.96, 1.26, "madera")
    mb.add_box(-0.22, 0.22, 0.78, 0.82, 0.96, 1.26, "madera")
    u0, v0, u1, v1 = cell_uv("ataud_emblema")
    mb.add_quad((-0.18, -0.825, 0.62), (0.18, -0.825, 0.62), (0.18, -0.825, 0.92), (-0.18, -0.825, 0.92), "atlas_museo", (u0, v0, u1, v1))
    kit["ataud_universitario"] = mb.build_mesh()

    # 13. Arana de cristal colonial con brazos curvos en S (sin discos gruesos!)
    mb = MeshBuilder("M_Arana_Cristal")
    mb.add_cylinder(0.0, 0.0, 0.0, 2.15, 0.016, 0.016, 6, "oro_bronce", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, 0.0, -0.92, -0.78, 0.015, 0.085, 8, "oro_bronce", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, 0.0, -0.78, -0.58, 0.085, 0.042, 8, "oro_bronce", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, 0.0, -0.58, -0.25, 0.042, 0.072, 8, "oro_bronce", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, 0.0, -0.25, 0.0, 0.072, 0.025, 8, "oro_bronce", cap_top=False, cap_bot=False)
    for k in range(8):
        ang = 2.0 * math.pi * k / 8.0
        add_curved_s_arm(mb, (math.cos(ang) * 0.075, math.sin(ang) * 0.075, -0.75), ang, 0.34, -0.83, 0.56, -0.68, radius=0.012, segs=4)
    for k in range(4):
        ang = 2.0 * math.pi * k / 4.0 + math.pi * 0.25
        add_curved_s_arm(mb, (math.cos(ang) * 0.055, math.sin(ang) * 0.055, -0.40), ang, 0.21, -0.46, 0.35, -0.35, radius=0.011, segs=4)
    kit["arana_cristal"] = mb.build_mesh()

    return kit


def add_pinaculo_jarron(mb: MeshBuilder, x: float, y: float, z0: float, scale: float = 1.0, mat_name: str = "piedra_fachada"):
    """Pinaculo barroco suavizado en forma de jarron (foto 03_00m59s)."""
    s = scale
    mb.add_box(x - 0.16 * s, x + 0.16 * s, y - 0.16 * s, y + 0.16 * s, z0, z0 + 0.14 * s, mat_name)
    mb.add_cylinder(x, y, z0 + 0.14 * s, z0 + 0.28 * s, 0.12 * s, 0.07 * s, 12, mat_name)
    mb.add_cylinder(x, y, z0 + 0.28 * s, z0 + 0.56 * s, 0.08 * s, 0.18 * s, 12, mat_name)
    mb.add_cylinder(x, y, z0 + 0.56 * s, z0 + 0.78 * s, 0.18 * s, 0.08 * s, 12, mat_name)
    mb.add_cylinder(x, y, z0 + 0.78 * s, z0 + 0.98 * s, 0.09 * s, 0.02 * s, 12, mat_name)
    mb.add_cylinder(x, y, z0 + 0.98 * s, z0 + 1.08 * s, 0.045 * s, 0.008 * s, 12, mat_name)


# ---------------------------------------------------------------------------
# 1. FACHADA BARROCA Y ZAGUAN
# ---------------------------------------------------------------------------

def build_fachada_y_zaguan(col, kit: dict[str, bpy.types.Mesh]):
    hx = FACHADA_ANCHO * 0.5
    hz_zag = ZAGUAN_ANCHO * 0.5
    pw = PORTON_ANCHO * 0.5

    mb = MeshBuilder("CL_Fachada_Crujia")
    mb.add_box(-13.0, 13.0, -4.50, 0.0, -0.18, Z_ACERA, "atlas_museo", "vereda_gris")

    # Muro frontal con vano libre del porton (2.80 x 3.80 m)
    mb.add_box(-hx, -pw, 0.0, 0.80, 0.0, FACHADA_ALTO, "muro")
    mb.add_box(pw, hx, 0.0, 0.80, 0.0, FACHADA_ALTO, "muro")
    mb.add_box(-pw, pw, 0.0, 0.80, PORTON_ALTO, FACHADA_ALTO, "muro")

    mb.add_box(-hx, -2.55, -0.06, 0.02, 0.0, ZOCALO_ALTO, "piedra_fachada")
    mb.add_box(2.55, hx, -0.06, 0.02, 0.0, ZOCALO_ALTO, "piedra_fachada")
    mb.add_box(-hx - 0.15, -2.65, -0.24, 0.02, FACHADA_ALTO - 0.25, FACHADA_ALTO, "muro")
    mb.add_box(2.65, hx + 0.15, -0.24, 0.02, FACHADA_ALTO - 0.25, FACHADA_ALTO, "muro")

    # --- PORTADA BARROCA DE PIEDRA OSCURA (piedra_fachada: columnas, entablamento, escudo, roleos, pinaculos) ---
    for sgn in (-1.0, 1.0):
        px_in = sgn * 1.72
        px_out = sgn * 2.26
        x_lo, x_hi = sorted((sgn * 1.40, sgn * 2.62))
        mb.add_box(x_lo, x_hi, -0.46, 0.02, 0.0, ZOCALO_ALTO + 0.15, "piedra_fachada")
        for cx in (px_in, px_out):
            mb.add_cylinder(cx, -0.28, ZOCALO_ALTO + 0.15, 4.15, 0.18, 0.16, 14, "piedra_fachada")
            mb.add_box(cx - 0.22, cx + 0.22, -0.48, -0.04, 4.15, 4.35, "piedra_fachada")
        mb.add_box(x_lo - 0.06, x_hi + 0.06, -0.54, 0.02, 4.35, 4.78, "piedra_fachada")
        for cx in (px_in, px_out):
            mb.add_box(cx - 0.14, cx + 0.14, -0.38, 0.02, 4.78, 7.25, "piedra_fachada")
        # Entablamento curvo lateral + 4 pinaculos en forma de jarron
        mb.add_box(x_lo - 0.04, x_hi + 0.04, -0.48, 0.02, 7.25, 7.55, "piedra_fachada")
        add_pinaculo_jarron(mb, px_out, -0.30, 7.55, scale=1.05, mat_name="piedra_fachada")
        add_pinaculo_jarron(mb, px_in, -0.30, 7.55, scale=0.85, mat_name="piedra_fachada")
        # Roleos / volutas laterales barrocas flanqueando el cuerpo superior
        mb.add_box(sgn * 1.35 - 0.35, sgn * 1.35 + 0.35, -0.42, 0.02, 7.55, 8.20, "piedra_fachada")
        mb.add_disc_y(sgn * 1.55, -0.46, 7.95, 0.26, 0.10, 12, "piedra_fachada")

    mb.add_arch_spandrel(0.0, PORTON_ANCHO, -0.42, 0.02, 3.25, 4.78, 0.65, 14, "piedra_fachada", ring_mat="piedra_fachada", ring_thick=0.22, ring_out=0.06)
    mb.add_box(-2.60, 2.60, -0.48, 0.02, 4.65, 4.92, "piedra_fachada")
    mb.add_box(-1.50, 1.50, -0.18, 0.02, 4.92, 7.45, "piedra_fachada")

    # Ventana alta de portada con reja ornamental y fondo oscuro profundo
    mb.add_box(-0.54, 0.54, -0.25, -0.19, 5.10, 6.72, "atlas_museo", "vidrio")
    mb.add_box(-0.64, -0.54, -0.28, -0.17, 5.06, 6.76, "madera")
    mb.add_box(0.54, 0.64, -0.28, -0.17, 5.06, 6.76, "madera")
    mb.add_arch_ring(0.0, 0.54, 0.14, -0.28, -0.17, 6.72, 0.22, 12, "piedra_fachada")
    for rx in (-0.36, -0.12, 0.12, 0.36):
        mb.add_box(rx - 0.015, rx + 0.015, -0.32, -0.28, 5.12, 6.84, "hierro")
    for rz in (5.55, 6.08, 6.56):
        mb.add_box(-0.54, 0.54, -0.32, -0.28, rz - 0.015, rz + 0.015, "hierro")

    # Cuerpo superior barroco: medallon IHS + arco central con Escudo USFX + remate curvo-quebrado
    mb.add_box(-1.55, 1.55, -0.46, 0.02, 7.25, 8.65, "piedra_fachada")
    mb.add_arch_ring(0.0, 0.68, 0.18, -0.54, -0.40, 8.05, 0.68, 14, "piedra_fachada")
    # Medallon inferior IHS (entre ventana y escudo)
    mb.add_disc_y(0.0, -0.50, 7.22, 0.32, 0.08, 14, "piedra_fachada")
    # Gran Escudo circular de la Universidad de San Francisco Xavier (mirando a -Y)
    mb.add_disc_y(0.0, -0.56, 8.15, 0.60, 0.11, 16, "atlas_museo", "escudo_usfx", rim_mat="piedra_fachada")

    # Alero central mas estrecho (-1.95..+1.95) para dejar los 4 pinaculos en jarron libres contra el cielo!
    mb.add_sloped_box((-2.05, -0.70, 8.48), (0.0, -0.70, PORTADA_ALTO_FRONTON), (0.0, 0.85, PORTADA_ALTO_FRONTON), (-2.05, 0.85, 8.48), 0.18, "teja")
    mb.add_sloped_box((0.0, -0.70, PORTADA_ALTO_FRONTON), (2.05, -0.70, 8.48), (2.05, 0.85, 8.48), (0.0, 0.85, PORTADA_ALTO_FRONTON), 0.18, "teja")
    mb.add_box(-0.14, 0.14, -0.72, 0.88, PORTADA_ALTO_FRONTON + 0.12, PORTADA_ALTO_FRONTON + 0.28, "teja")
    # Timpano triangular cerrado en piedra
    mb.add_tri((-1.95, -0.46, 8.48), (1.95, -0.46, 8.48), (0.0, -0.46, PORTADA_ALTO_FRONTON), "piedra_fachada")
    mb.add_tri((1.95, -0.46, 8.48), (1.95, 0.02, 8.48), (0.0, -0.46, PORTADA_ALTO_FRONTON), "piedra_fachada")
    mb.add_tri((-1.95, 0.02, 8.48), (-1.95, -0.46, 8.48), (0.0, -0.46, PORTADA_ALTO_FRONTON), "piedra_fachada")

    # Porton de cedro nativo abierto con clavos de bronce y 2 aldabones (foto 05_01m31s)
    for sgn in (-1.0, 1.0):
        hx_door = sgn * (pw - 0.08)
        mb.add_box(hx_door - 0.06, hx_door + 0.06, 0.15, 1.50, Z_ZAGUAN, PORTON_ALTO - 0.15, "madera")
        for dy in (0.30, 0.58, 0.86, 1.14, 1.40):
            for dz in (0.55, 1.15, 1.75, 2.35, 2.95, 3.45):
                mb.add_sphere_octa(hx_door - sgn * 0.08, dy, dz, 0.042, 0.042, 0.042, "oro_bronce")
        # Aldabon de bronce (placa y anillo en cada hoja)
        mb.add_box(hx_door - sgn * 0.095, hx_door - sgn * 0.06, 1.02, 1.16, 2.52, 2.74, "oro_bronce")
        mb.add_sphere_octa(hx_door - sgn * 0.11, 1.09, 2.48, 0.055, 0.055, 0.075, "oro_bronce")

    # Crujia frontal y Zaguan
    mb.add_box(-hx, -hz_zag, 0.80, CLAUSTRO_Y0, 0.0, FACHADA_ALTO, "muro")
    mb.add_box(hz_zag, hx, 0.80, CLAUSTRO_Y0, 0.0, FACHADA_ALTO, "muro")
    mb.add_box(-hz_zag, hz_zag, 0.0, CLAUSTRO_Y0, 0.0, Z_ZAGUAN, "piso")
    mb.add_box(-hz_zag, hz_zag, 0.80, CLAUSTRO_Y0, Z_ZAGUAN + ZAGUAN_ALTO, FACHADA_ALTO, "muro")
    mb.add_box(-hz_zag, -hz_zag + 0.03, 0.80, CLAUSTRO_Y0, Z_ZAGUAN, ZOCALO_ALTO, "piedra")
    mb.add_box(hz_zag - 0.03, hz_zag, 0.80, CLAUSTRO_Y0, Z_ZAGUAN, ZOCALO_ALTO, "piedra")
    for vy in (1.4, 2.4, 3.4, 4.4, 5.4):
        mb.add_box(-hz_zag, hz_zag, vy - 0.10, vy + 0.10, Z_ZAGUAN + ZAGUAN_ALTO - 0.18, Z_ZAGUAN + ZAGUAN_ALTO, "madera")

    # Cubierta a dos aguas de la crujia frontal + liston de cumbrera + canes
    mb.add_sloped_box(
        (-hx - 0.25, -0.75, FACHADA_ALTO - 0.15), (hx + 0.25, -0.75, FACHADA_ALTO - 0.15),
        (hx + 0.25, CLAUSTRO_Y0 * 0.5, 10.20), (-hx - 0.25, CLAUSTRO_Y0 * 0.5, 10.20), 0.18, "teja",
    )
    mb.add_sloped_box(
        (-hx - 0.25, CLAUSTRO_Y0 * 0.5, 10.20), (hx + 0.25, CLAUSTRO_Y0 * 0.5, 10.20),
        (hx + 0.25, CLAUSTRO_Y0 + 0.35, FACHADA_ALTO - 0.15), (-hx - 0.25, CLAUSTRO_Y0 + 0.35, FACHADA_ALTO - 0.15), 0.18, "teja",
    )
    mb.add_box(-hx - 0.28, hx + 0.28, CLAUSTRO_Y0 * 0.5 - 0.14, CLAUSTRO_Y0 * 0.5 + 0.14, 10.30, 10.48, "teja")
    kx = -hx + 0.5
    while kx <= hx - 0.5:
        if abs(kx) > 2.8:
            mb.add_box(kx - 0.06, kx + 0.06, -0.65, 0.0, FACHADA_ALTO - 0.22, FACHADA_ALTO - 0.04, "madera")
        kx += 0.80

    mb.to_object(col, "CL_Fachada_Crujia")

    for i, vx in enumerate((-8.20, -4.90, 4.90, 8.20)):
        spawn_instance(col, f"CL_Ventana_Baja_{i+1:02d}", kit["ventana_fachada"], (vx, -0.02, 1.50))
    spawn_instance(col, "CL_Balcon_Izq", kit["balcon_colonial"], (-6.55, -0.02, Z_PLANTA_ALTA))
    spawn_instance(col, "CL_Balcon_Der", kit["balcon_colonial"], (6.55, -0.02, Z_PLANTA_ALTA))
    spawn_instance(col, "CL_Farol_Zaguan", kit["farol_colonial"], (0.0, 3.20, Z_ZAGUAN + ZAGUAN_ALTO - 0.62))


# ---------------------------------------------------------------------------
# 2. CLAUSTRO PRINCIPAL, CORREDORES DETALLADOS, ESTATUA FLECHERO Y FUENTE
# ---------------------------------------------------------------------------

def _bm_add_tube(bm: bmesh.types.BMesh, p0: Vector, p1: Vector, r0: float, r1: float, segs: int = 6):
    axis = p1 - p0
    if axis.length < 1e-5:
        return
    z_dir = axis.normalized()
    up = Vector((0.0, 0.0, 1.0)) if abs(z_dir.z) < 0.95 else Vector((1.0, 0.0, 0.0))
    x_dir = up.cross(z_dir).normalized()
    y_dir = z_dir.cross(x_dir).normalized()
    ring0, ring1 = [], []
    for k in range(segs):
        ang = 2.0 * math.pi * k / segs
        d = x_dir * math.cos(ang) + y_dir * math.sin(ang)
        ring0.append(bm.verts.new(p0 + d * r0))
        ring1.append(bm.verts.new(p1 + d * r1))
    bm.faces.new(list(reversed(ring0)))
    bm.faces.new(ring1)
    for k in range(segs):
        kn = (k + 1) % segs
        bm.faces.new((ring0[k], ring0[kn], ring1[kn], ring1[k]))


def build_flechero_statue(col, loc: tuple[float, float, float], rot_z_deg: float = 45.0):
    """Escultura organica de El Flechero (~1,950 tris, Skin + Subsurf + Decimate + bronce patinado)."""
    # Arbol esqueletico musculoso (torax en V, cuello firme y cabeza integrada sin separaciones)
    nodes = [
        # 0: pelvis (raiz)
        ((0.0, 0.0, 1.72), (0.148, 0.118), -1),
        # Pierna izquierda adelantada sobre peldano alto (z=0.98)
        ((-0.098, 0.08, 1.56), (0.106, 0.108), 0),    # 1 thigh L
        ((-0.082, 0.31, 1.32), (0.078, 0.082), 1),    # 2 knee/calf L
        ((-0.062, 0.36, 1.00), (0.052, 0.054), 2),    # 3 ankle L
        ((-0.060, 0.49, 0.99), (0.054, 0.032), 3),    # 4 foot L
        # Pierna derecha atrasada de apoyo (z=0.74)
        ((0.098, -0.06, 1.56), (0.106, 0.108), 0),    # 5 thigh R
        ((0.082, -0.23, 1.18), (0.076, 0.080), 5),    # 6 knee/calf R
        ((0.062, -0.38, 0.77), (0.050, 0.052), 6),    # 7 ankle R
        ((0.060, -0.26, 0.76), (0.054, 0.032), 7),    # 8 foot R
        # Torax heroico en V + cuello continuo
        ((0.0, 0.03, 1.92), (0.128, 0.105), 0),       # 9 waist (estrecho)
        ((0.0, 0.07, 2.18), (0.208, 0.138), 9),       # 10 chest (ancho pectoral)
        ((0.0, 0.08, 2.34), (0.125, 0.095), 10),      # 11 clavicle
        ((0.0, 0.09, 2.50), (0.078, 0.078), 11),      # 12 neck
        # Brazo izquierdo extendido en diagonal sosteniendo el arco
        ((-0.24, 0.10, 2.33), (0.078, 0.078), 11),    # 13 shoulder L
        ((-0.18, 0.45, 2.58), (0.060, 0.060), 13),    # 14 elbow L
        ((-0.08, 0.78, 2.84), (0.048, 0.048), 14),    # 15 bow hand L
        # Brazo derecho tensando la cuerda hacia la mejilla
        ((0.24, 0.02, 2.32), (0.078, 0.078), 11),     # 16 shoulder R
        ((0.35, -0.14, 2.48), (0.058, 0.058), 16),    # 17 elbow R
        ((0.10, 0.15, 2.54), (0.046, 0.046), 17),     # 18 draw hand R
    ]
    skel_verts = [n[0] for n in nodes]
    skel_edges = [(n[2], i) for i, n in enumerate(nodes) if n[2] >= 0]

    skel_mesh = bpy.data.meshes.new("_Flechero_Skel")
    skel_mesh.from_pydata(skel_verts, skel_edges, [])
    skel_obj = bpy.data.objects.new("_Flechero_Skel", skel_mesh)
    col.objects.link(skel_obj)

    sk_mod = skel_obj.modifiers.new("Skin", "SKIN")
    sk_mod.use_smooth_shade = True
    sk_mod.branch_smoothing = 0.25
    sv_data = skel_mesh.skin_vertices[0].data
    for i, (_, rad, _) in enumerate(nodes):
        sv_data[i].radius = rad
        sv_data[i].use_root = (i == 0)

    sub_mod = skel_obj.modifiers.new("Subsurf", "SUBSURF")
    sub_mod.levels = 2
    sub_mod.render_levels = 2

    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    raw_tris = len(skel_obj.evaluated_get(deps).data.loop_triangles)
    if raw_tris > 1680:
        dec_mod = skel_obj.modifiers.new("Decimate", "DECIMATE")
        dec_mod.ratio = max(0.18, min(1.0, 1660.0 / float(raw_tris)))
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()

    baked_mesh = bpy.data.meshes.new_from_object(skel_obj.evaluated_get(deps), preserve_all_data_layers=False, depsgraph=deps)
    bpy.data.objects.remove(skel_obj, do_unlink=True)
    bpy.data.meshes.remove(skel_mesh)

    bm = bmesh.new()
    bm.from_mesh(baked_mesh)
    bpy.data.meshes.remove(baked_mesh)

    # Cuello continuo, cabeza anatomica esculpida y yelmo de puma encajado sobre el craneo
    _bm_add_tube(bm, Vector((0.0, 0.07, 2.28)), Vector((0.0, 0.10, 2.57)), 0.088, 0.068, segs=8)
    head_ret = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.108)
    for v in head_ret["verts"]:
        v.co.x = v.co.x * 0.90
        v.co.y = v.co.y * 1.08 + 0.105
        v.co.z = v.co.z * 1.18 + 2.595
    # Taparrabo ceremonial
    _bm_add_tube(bm, Vector((0.0, 0.01, 1.54)), Vector((0.0, 0.01, 1.82)), 0.182, 0.156, segs=10)
    # Yelmo/tocado de puma asentado directamente sobre la cabeza (2.66..2.82, cero flotacion)
    _bm_add_tube(bm, Vector((0.0, 0.01, 2.66)), Vector((0.0, 0.19, 2.69)), 0.074, 0.082, segs=8)
    _bm_add_tube(bm, Vector((0.0, 0.02, 2.71)), Vector((0.0, 0.15, 2.81)), 0.044, 0.020, segs=6)
    _bm_add_tube(bm, Vector((-0.065, 0.10, 2.69)), Vector((-0.095, 0.09, 2.79)), 0.024, 0.008, segs=5)
    _bm_add_tube(bm, Vector((0.065, 0.10, 2.69)), Vector((0.095, 0.09, 2.79)), 0.024, 0.008, segs=5)

    p_grip = Vector(nodes[15][0])
    p_draw = Vector(nodes[18][0])
    aim = (p_grip - p_draw).normalized()
    up_hint = Vector((-0.15, -0.30, 0.94)).normalized()
    up_bow = (up_hint - aim * up_hint.dot(aim)).normalized()

    bow_curve = []
    for k in range(9):
        t = -1.0 + 2.0 * k / 8.0
        bend = -0.19 * (t * t) + 0.03 * (t ** 4)
        pt = p_grip + up_bow * (t * 0.64) + aim * bend
        bow_curve.append(pt)
    for b0, b1 in zip(bow_curve, bow_curve[1:]):
        _bm_add_tube(bm, b0, b1, 0.015, 0.014, segs=6)

    _bm_add_tube(bm, bow_curve[0], p_draw, 0.006, 0.006, segs=4)
    _bm_add_tube(bm, bow_curve[-1], p_draw, 0.006, 0.006, segs=4)

    p_arrow_tail = p_draw - aim * 0.08
    p_arrow_neck = p_grip + aim * 0.38
    p_arrow_tip = p_arrow_neck + aim * 0.11
    _bm_add_tube(bm, p_arrow_tail, p_arrow_neck, 0.011, 0.011, segs=5)
    _bm_add_tube(bm, p_arrow_neck, p_arrow_tip, 0.026, 0.002, segs=5)

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.normal_update()
    uv_layer = bm.loops.layers.uv.verify()
    tile = UV_TILE_METERS["oro_bronce"]
    for f in bm.faces:
        f.smooth = True
        n = f.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for loop in f.loops:
            co = loop.vert.co
            if ax >= ay and ax >= az:
                loop[uv_layer].uv = (co.y / tile, co.z / tile)
            elif ay >= ax and ay >= az:
                loop[uv_layer].uv = (co.x / tile, co.z / tile)
            else:
                loop[uv_layer].uv = (co.x / tile, co.y / tile)

    max_ang = math.radians(48.0)
    sharp_edges = [e for e in bm.edges if len(e.link_faces) != 2 or e.calc_face_angle(0.0) > max_ang]
    if sharp_edges:
        bmesh.ops.split_edges(bm, edges=sharp_edges)

    mesh = bpy.data.meshes.new("CL_Estatua_Flechero")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(get_or_create_material("hierro"))
    mesh.update()

    stat_obj = bpy.data.objects.new("CL_Estatua_Flechero", mesh)
    stat_obj.location = loc
    stat_obj.rotation_euler = (0.0, 0.0, math.radians(rot_z_deg))
    col.objects.link(stat_obj)
    return stat_obj


def build_claustro(col, kit: dict[str, bpy.types.Mesh]):
    cx_half = CLAUSTRO_ANCHO_EXT * 0.5            # 11.00
    px_half = PATIO_ANCHO * 0.5                   # 7.20
    y_cl0 = CLAUSTRO_Y0                           # 6.20
    y_cl1 = CLAUSTRO_Y0 + CLAUSTRO_FONDO_EXT      # 28.20
    y_p0 = y_cl0 + CLAUSTRO_MURO + GALERIA_ANCHO  # 10.00
    y_p1 = y_cl1 - CLAUSTRO_MURO - GALERIA_ANCHO  # 24.40
    fy = (y_p0 + y_p1) * 0.5                      # 17.20
    bay = PATIO_ANCHO / NUM_ARCOS_LADO            # 3.60 m

    mb = MeshBuilder("CL_Claustro_Estructura")

    # Pisos del patio (empedrado en rombos 8x8 tiles de 1.8m) y galerias (ladrillo rojo)
    u0_r, v0_r, u1_r, v1_r = cell_uv("empedrado_rombo")
    nx_t, ny_t = 8, 8
    dx_t = (2.0 * px_half) / nx_t
    dy_t = (y_p1 - y_p0) / ny_t
    for ix in range(nx_t):
        for iy in range(ny_t):
            tx0 = -px_half + ix * dx_t
            ty0 = y_p0 + iy * dy_t
            mb.add_quad((tx0, ty0, Z_PATIO), (tx0 + dx_t, ty0, Z_PATIO), (tx0 + dx_t, ty0 + dy_t, Z_PATIO), (tx0, ty0 + dy_t, Z_PATIO), "atlas_museo", (u0_r, v0_r, u1_r, v1_r))
    mb.add_box(-cx_half, cx_half, y_cl0, y_p0, 0.0, Z_GALERIA, "piso")
    mb.add_box(-cx_half, cx_half, y_p1, y_cl1, 0.0, Z_GALERIA, "piso")
    mb.add_box(-cx_half, -px_half, y_p0, y_p1, 0.0, Z_GALERIA, "piso")
    mb.add_box(px_half, cx_half, y_p0, y_p1, 0.0, Z_GALERIA, "piso")

    # Pretil bajo de piedra entre columnas (abierto frente a zaguan y frente a Salon)
    for y_wall in (y_p0, y_p1):
        mb.add_box(-px_half, -1.45, y_wall - 0.16, y_wall + 0.16, Z_PATIO, Z_GALERIA + 0.22, "piedra")
        mb.add_box(1.45, px_half, y_wall - 0.16, y_wall + 0.16, Z_PATIO, Z_GALERIA + 0.22, "piedra")
    mb.add_box(-px_half - 0.16, -px_half + 0.16, y_p0, y_p1, Z_PATIO, Z_GALERIA + 0.22, "piedra")
    mb.add_box(px_half - 0.16, px_half + 0.16, y_p0, y_p1, Z_PATIO, Z_GALERIA + 0.22, "piedra")

    # Muro Oeste (abierto en Y=19.46..22.14 sin solapamiento con jambas/dintel),
    # Muro Este continuo y Muro Norte (abierto en X=7.00..9.60 sin solapamiento)
    sx_out_cl = SALON_ANCHO_EXT * 0.5
    mb.add_box(-cx_half, -cx_half + CLAUSTRO_MURO, y_cl0, SALA_LAT_PUERTA_Y0 - 0.14, 0.0, GALERIA_ALTO_CUMBRERA, "muro")
    mb.add_box(-cx_half, -cx_half + CLAUSTRO_MURO, SALA_LAT_PUERTA_Y1 + 0.14, y_cl1, 0.0, GALERIA_ALTO_CUMBRERA, "muro")
    mb.add_box(-cx_half, -cx_half + CLAUSTRO_MURO, SALA_LAT_PUERTA_Y0 - 0.14, SALA_LAT_PUERTA_Y1 + 0.14, Z_GALERIA + SALA_LAT_PUERTA_H + 0.22, GALERIA_ALTO_CUMBRERA, "muro")
    mb.add_box(cx_half - CLAUSTRO_MURO, cx_half, y_cl0, y_cl1, 0.0, GALERIA_ALTO_CUMBRERA, "muro")

    mb.add_box(-cx_half, -sx_out_cl, y_cl1 - CLAUSTRO_MURO, y_cl1, 0.0, GALERIA_ALTO_CUMBRERA, "muro")
    mb.add_box(sx_out_cl, 7.00, y_cl1 - CLAUSTRO_MURO, y_cl1, 0.0, GALERIA_ALTO_CUMBRERA, "muro")
    mb.add_box(9.60, cx_half, y_cl1 - CLAUSTRO_MURO, y_cl1, 0.0, GALERIA_ALTO_CUMBRERA, "muro")
    mb.add_box(7.00, 9.60, y_cl1 - CLAUSTRO_MURO, y_cl1, Z_GALERIA + 3.22, GALERIA_ALTO_CUMBRERA, "muro")

    # Portada abierta Oeste hacia Salon del Antiguo Senado / Galeria de los Presidentes (-X)
    mb.add_box(-cx_half - 0.04, -cx_half + CLAUSTRO_MURO + 0.08, SALA_LAT_PUERTA_Y0 - 0.14, SALA_LAT_PUERTA_Y0, 0.0, Z_GALERIA + SALA_LAT_PUERTA_H, "piedra")
    mb.add_box(-cx_half - 0.04, -cx_half + CLAUSTRO_MURO + 0.08, SALA_LAT_PUERTA_Y1, SALA_LAT_PUERTA_Y1 + 0.14, 0.0, Z_GALERIA + SALA_LAT_PUERTA_H, "piedra")
    mb.add_box(-cx_half - 0.06, -cx_half + CLAUSTRO_MURO + 0.10, SALA_LAT_PUERTA_Y0 - 0.14, SALA_LAT_PUERTA_Y1 + 0.14, Z_GALERIA + SALA_LAT_PUERTA_H, Z_GALERIA + SALA_LAT_PUERTA_H + 0.22, "madera")
    mb.add_box(-cx_half - 1.15, -cx_half - 0.05, SALA_LAT_PUERTA_Y0 - 0.08, SALA_LAT_PUERTA_Y0 + 0.02, Z_GALERIA, Z_GALERIA + SALA_LAT_PUERTA_H - 0.05, "madera")
    mb.add_box(-cx_half - 1.15, -cx_half - 0.05, SALA_LAT_PUERTA_Y1 - 0.02, SALA_LAT_PUERTA_Y1 + 0.08, Z_GALERIA, Z_GALERIA + SALA_LAT_PUERTA_H - 0.05, "madera")

    # Portada abierta Norte-Este hacia Sala de los Guerrilleros (+Y, piedra limpia sin caras coplanares)
    mb.add_box(7.00, 7.10, y_cl1 - CLAUSTRO_MURO - 0.02, y_cl1 + 0.02, 0.0, Z_GALERIA + 3.05, "piedra")
    mb.add_box(9.50, 9.60, y_cl1 - CLAUSTRO_MURO - 0.02, y_cl1 + 0.02, 0.0, Z_GALERIA + 3.05, "piedra")
    mb.add_box(7.00, 9.60, y_cl1 - CLAUSTRO_MURO - 0.03, y_cl1 + 0.03, Z_GALERIA + 3.05, Z_GALERIA + 3.22, "piedra")
    mb.add_box(7.04, 7.14, y_cl1 + 0.05, y_cl1 + 1.12, Z_GALERIA, Z_GALERIA + 3.00, "madera")
    mb.add_box(9.46, 9.56, y_cl1 + 0.05, y_cl1 + 1.12, Z_GALERIA, Z_GALERIA + 3.00, "madera")

    # Zocalo bajo de piedra en las paredes interiores de los corredores
    mb.add_box(-cx_half + CLAUSTRO_MURO, -cx_half + CLAUSTRO_MURO + 0.03, y_cl0, SALA_LAT_PUERTA_Y0 - 0.14, Z_GALERIA, Z_GALERIA + 0.34, "piedra")
    mb.add_box(-cx_half + CLAUSTRO_MURO, -cx_half + CLAUSTRO_MURO + 0.03, SALA_LAT_PUERTA_Y1 + 0.14, y_cl1, Z_GALERIA, Z_GALERIA + 0.34, "piedra")
    mb.add_box(cx_half - CLAUSTRO_MURO - 0.03, cx_half - CLAUSTRO_MURO, y_cl0, y_cl1, Z_GALERIA, Z_GALERIA + 0.34, "piedra")
    hz_zag_cl = ZAGUAN_ANCHO * 0.5
    mb.add_box(-cx_half + CLAUSTRO_MURO, -hz_zag_cl, y_cl0, y_cl0 + 0.03, Z_GALERIA, Z_GALERIA + 0.34, "piedra")
    mb.add_box(hz_zag_cl, cx_half - CLAUSTRO_MURO, y_cl0, y_cl0 + 0.03, Z_GALERIA, Z_GALERIA + 0.34, "piedra")

    # Cuadros / placas historicas en los muros de los corredores (mapeados al atlas)
    # Corredor Oeste (+X mirando al patio)
    for qy, ckey in ((17.20, "cuadro_pasillo"), (24.50, "guerrillera")):
        mb.add_box(-cx_half + CLAUSTRO_MURO, -cx_half + CLAUSTRO_MURO + 0.04, qy - 0.52, qy + 0.52, 1.55, 2.75, "oro_bronce")
        u0, v0, u1, v1 = cell_uv(ckey)
        mb.add_quad((-cx_half + CLAUSTRO_MURO + 0.05, qy - 0.45, 1.62), (-cx_half + CLAUSTRO_MURO + 0.05, qy + 0.45, 1.62), (-cx_half + CLAUSTRO_MURO + 0.05, qy + 0.45, 2.68), (-cx_half + CLAUSTRO_MURO + 0.05, qy - 0.45, 2.68), "atlas_museo", (u0, v0, u1, v1))
    # Corredor Este (-X mirando al patio)
    for qy, ckey in ((17.20, "batalla"), (24.50, "cuadro_pasillo")):
        wx = cx_half - CLAUSTRO_MURO
        mb.add_box(wx - 0.04, wx, qy - 0.52, qy + 0.52, 1.55, 2.75, "oro_bronce")
        u0, v0, u1, v1 = cell_uv(ckey)
        mb.add_quad((wx - 0.05, qy + 0.45, 1.62), (wx - 0.05, qy - 0.45, 1.62), (wx - 0.05, qy - 0.45, 2.68), (wx - 0.05, qy + 0.45, 2.68), "atlas_museo", (u0, v0, u1, v1))

    # Cubiertas de teja inclinadas de las 4 galerias (+0.07 m sobre arcos para evitar rozamiento)
    z_al_cl = GALERIA_ALTO_ALERO + 0.07
    z_cu_cl = GALERIA_ALTO_CUMBRERA + 0.07
    mb.add_sloped_box(
        (-cx_half, y_cl0, z_cu_cl), (cx_half, y_cl0, z_cu_cl),
        (px_half + 0.45, y_p0 - 0.45, z_al_cl), (-px_half - 0.45, y_p0 - 0.45, z_al_cl), 0.18, "teja",
    )
    mb.add_sloped_box(
        (-px_half - 0.45, y_p1 + 0.45, z_al_cl), (px_half + 0.45, y_p1 + 0.45, z_al_cl),
        (cx_half, y_cl1, z_cu_cl), (-cx_half, y_cl1, z_cu_cl), 0.18, "teja",
    )
    mb.add_sloped_box(
        (-cx_half, y_cl0, z_cu_cl), (-px_half + 0.45, y_p0 - 0.45, z_al_cl),
        (-px_half + 0.45, y_p1 + 0.45, z_al_cl), (-cx_half, y_cl1, z_cu_cl), 0.18, "teja",
    )
    mb.add_sloped_box(
        (px_half - 0.45, y_p0 - 0.45, z_al_cl), (cx_half, y_cl0, z_cu_cl),
        (cx_half, y_cl1, z_cu_cl), (px_half - 0.45, y_p1 + 0.45, z_al_cl), 0.18, "teja",
    )
    # Listones de cumbrera en el claustro
    mb.add_box(-cx_half - 0.05, -cx_half + 0.25, y_cl0, y_cl1, z_cu_cl + 0.12, z_cu_cl + 0.26, "teja")
    mb.add_box(cx_half - 0.25, cx_half + 0.05, y_cl0, y_cl1, z_cu_cl + 0.12, z_cu_cl + 0.26, "teja")
    mb.add_box(-cx_half, cx_half, y_cl1 - 0.25, y_cl1 + 0.05, z_cu_cl + 0.12, z_cu_cl + 0.26, "teja")

    # Vigas de madera densas bajo el techo de las 4 galerias (fotos 10_09m14s, 11_09m18s)
    for k in range(9):
        x_b = -9.6 + k * 2.4
        mb.add_sloped_box(
            (x_b - 0.07, y_cl0 + CLAUSTRO_MURO, GALERIA_ALTO_CUMBRERA - 0.28),
            (x_b + 0.07, y_cl0 + CLAUSTRO_MURO, GALERIA_ALTO_CUMBRERA - 0.28),
            (x_b + 0.07, y_p0 - 0.30, GALERIA_ALTO_ALERO - 0.14),
            (x_b - 0.07, y_p0 - 0.30, GALERIA_ALTO_ALERO - 0.14), 0.14, "madera",
        )
        mb.add_sloped_box(
            (x_b - 0.07, y_p1 + 0.30, GALERIA_ALTO_ALERO - 0.14),
            (x_b + 0.07, y_p1 + 0.30, GALERIA_ALTO_ALERO - 0.14),
            (x_b + 0.07, y_cl1 - CLAUSTRO_MURO, GALERIA_ALTO_CUMBRERA - 0.28),
            (x_b - 0.07, y_cl1 - CLAUSTRO_MURO, GALERIA_ALTO_CUMBRERA - 0.28), 0.14, "madera",
        )
    for k in range(7):
        y_b = 10.6 + k * 2.2
        mb.add_sloped_box(
            (-cx_half + CLAUSTRO_MURO, y_b - 0.07, GALERIA_ALTO_CUMBRERA - 0.28),
            (-px_half + 0.30, y_b - 0.07, GALERIA_ALTO_ALERO - 0.14),
            (-px_half + 0.30, y_b + 0.07, GALERIA_ALTO_ALERO - 0.14),
            (-cx_half + CLAUSTRO_MURO, y_b + 0.07, GALERIA_ALTO_CUMBRERA - 0.28), 0.14, "madera",
        )
        mb.add_sloped_box(
            (px_half - 0.30, y_b - 0.07, GALERIA_ALTO_ALERO - 0.14),
            (cx_half - CLAUSTRO_MURO, y_b - 0.07, GALERIA_ALTO_CUMBRERA - 0.28),
            (cx_half - CLAUSTRO_MURO, y_b + 0.07, GALERIA_ALTO_CUMBRERA - 0.28),
            (px_half - 0.30, y_b + 0.07, GALERIA_ALTO_ALERO - 0.14), 0.14, "madera",
        )

    # --- FUENTE CENTRAL DE PIEDRA (16 segs suavizados + agua con relieve normal/roughness) ---
    mb.add_cylinder(0.0, fy, Z_PATIO, Z_PATIO + 0.22, 1.78, 1.72, 16, "piedra", cap_bot=False)
    mb.add_cylinder(0.0, fy, Z_PATIO + 0.22, Z_PATIO + 0.84, 1.32, 1.40, 16, "piedra", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, fy, Z_PATIO + 0.84, Z_PATIO + 0.94, 1.48, 1.48, 16, "piedra", cap_bot=False)
    mb.add_cylinder(0.0, fy, Z_PATIO + 0.72, Z_PATIO + 0.76, 1.26, 1.26, 16, "atlas_museo", "agua", cap_bot=False)
    mb.add_cylinder(0.0, fy, Z_PATIO + 0.22, Z_PATIO + 1.65, 0.28, 0.22, 12, "piedra", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, fy, Z_PATIO + 1.55, Z_PATIO + 1.88, 0.38, 0.78, 14, "piedra")
    mb.add_cylinder(0.0, fy, Z_PATIO + 1.88, Z_PATIO + 2.38, 0.16, 0.22, 12, "piedra", cap_top=False, cap_bot=False)
    mb.add_cylinder(0.0, fy, Z_PATIO + 2.32, Z_PATIO + 2.58, 0.24, 0.44, 12, "piedra")

    # --- PEDESTAL DE ARENISCA PARA EL FLECHERO (roca escalonada con placa) ---
    ex, ey = 4.55, 13.90
    mb.add_cylinder(ex, ey, Z_PATIO, Z_PATIO + 0.22, 0.92, 0.86, 10, "piedra", cap_bot=False)
    mb.add_cylinder(ex + 0.04, ey - 0.04, Z_PATIO + 0.22, Z_PATIO + 0.74, 0.74, 0.64, 10, "piedra", cap_bot=False)
    mb.add_cylinder(ex - 0.22, ey + 0.22, Z_PATIO + 0.70, Z_PATIO + 0.98, 0.42, 0.34, 10, "piedra", cap_bot=False)
    # Placa conmemorativa de bronce con moldura en cara patio (-X)
    mb.add_box(ex - 0.72, ex - 0.65, ey - 0.30, ey + 0.30, Z_PATIO + 0.28, Z_PATIO + 0.62, "piedra")
    mb.add_box(ex - 0.74, ex - 0.70, ey - 0.26, ey + 0.26, Z_PATIO + 0.32, Z_PATIO + 0.58, "oro_bronce")

    mb.to_object(col, "CL_Claustro_Estructura")
    build_flechero_statue(col, (ex, ey, Z_PATIO - 0.02), rot_z_deg=45.0)

    # --- INSTANCIAS MODULARES DEL CLAUSTRO ---
    col_coords = set()
    for i in range(NUM_ARCOS_LADO + 1):
        xv = round(-px_half + i * bay, 3)
        yv = round(y_p0 + i * bay, 3)
        col_coords.add((xv, round(y_p0, 3)))
        col_coords.add((xv, round(y_p1, 3)))
        col_coords.add((round(-px_half, 3), yv))
        col_coords.add((round(px_half, 3), yv))
    for idx, (cx_p, cy_p) in enumerate(sorted(col_coords)):
        spawn_instance(col, f"CL_Columna_Claustro_{idx+1:02d}", kit["columna_claustro"], (cx_p, cy_p, Z_GALERIA))

    for i in range(NUM_ARCOS_LADO):
        mx = -px_half + (i + 0.5) * bay
        my = y_p0 + (i + 0.5) * bay
        spawn_instance(col, f"CL_Arco_Sur_{i+1:02d}", kit["arco_claustro"], (mx, y_p0, Z_GALERIA), 0.0)
        spawn_instance(col, f"CL_Arco_Norte_{i+1:02d}", kit["arco_claustro"], (mx, y_p1, Z_GALERIA), 180.0)
        spawn_instance(col, f"CL_Arco_Oeste_{i+1:02d}", kit["arco_claustro"], (-px_half, my, Z_GALERIA), 90.0)
        spawn_instance(col, f"CL_Arco_Este_{i+1:02d}", kit["arco_claustro"], (px_half, my, Z_GALERIA), -90.0)

    # Puertas cerradas detalladas (Oeste Y=20.80 abierta a Galeria de Presidentes; Norte-Este X=8.30 abierta a Guerrilleros)
    spawn_instance(col, "CL_Puerta_Oeste_01", kit["puerta_cerrada"], (-cx_half + CLAUSTRO_MURO, 13.6, Z_GALERIA), -90.0)
    spawn_instance(col, "CL_Puerta_Este_01", kit["puerta_cerrada"], (cx_half - CLAUSTRO_MURO, 13.6, Z_GALERIA), 90.0)
    spawn_instance(col, "CL_Puerta_Este_02", kit["puerta_cerrada"], (cx_half - CLAUSTRO_MURO, 20.8, Z_GALERIA), 90.0)
    spawn_instance(col, "CL_Puerta_Norte_Izq", kit["puerta_cerrada"], (-8.2, y_cl1 - CLAUSTRO_MURO - 0.13, Z_GALERIA), 0.0)

    # Ventana con reja a la izquierda de la portada del Salon + ventanas galeria sur + faroles centrales
    spawn_instance(col, "CL_Ventana_Entrada_Salon", kit["ventana_baja"], (-3.6, y_cl1 - 0.02, 1.35), 0.0)
    spawn_instance(col, "CL_Farol_Arco_Salon_Izq", kit["farol_colonial"], (-1.44, y_p1 - 0.18, 3.65))
    spawn_instance(col, "CL_Farol_Arco_Salon_Der", kit["farol_colonial"], (1.44, y_p1 - 0.18, 3.65))
    spawn_instance(col, "CL_Ventana_Galeria_Sur_Izq", kit["ventana_baja"], (-5.4, y_cl0 + 0.02, 1.30), 180.0)
    spawn_instance(col, "CL_Ventana_Galeria_Sur_Der", kit["ventana_baja"], (5.4, y_cl0 + 0.02, 1.30), 180.0)

    # Bancas de madera y 6 Macetas coloniales con vegetacion junto a columnas del patio
    spawn_instance(col, "CL_Banca_Norte_Izq", kit["banca_patio"], (-3.8, y_cl1 - 0.35, Z_GALERIA), 180.0)
    spawn_instance(col, "CL_Banca_Norte_Der", kit["banca_patio"], (3.8, y_cl1 - 0.35, Z_GALERIA), 180.0)
    spawn_instance(col, "CL_Banca_Oeste", kit["banca_patio"], (-cx_half + CLAUSTRO_MURO + 0.35, 17.2, Z_GALERIA), -90.0)
    spawn_instance(col, "CL_Banca_Este", kit["banca_patio"], (cx_half - CLAUSTRO_MURO - 0.35, 17.2, Z_GALERIA), 90.0)

    maceta_locs = [
        (-6.5, 10.6, Z_PATIO), (-6.5, 17.2, Z_PATIO), (-6.5, 23.8, Z_PATIO),
        (6.5, 23.8, Z_PATIO), (3.6, 23.8, Z_PATIO), (-3.6, 23.8, Z_PATIO),
    ]
    for i, ml in enumerate(maceta_locs):
        spawn_instance(col, f"CL_Maceta_Patio_{i+1:02d}", kit["maceta_patio"], ml)

    # 8 Faroles colgantes emisivos en arcadas
    farol_locs = [
        (-1.8, y_p1 + 0.35, 3.65), (1.8, y_p1 + 0.35, 3.65),
        (-5.4, y_p1 + 0.35, 3.65), (5.4, y_p1 + 0.35, 3.65),
        (-px_half - 0.35, 17.2, 3.65), (px_half + 0.35, 17.2, 3.65),
        (-1.8, y_p0 - 0.35, 3.65), (1.8, y_p0 - 0.35, 3.65),
    ]
    for i, fl in enumerate(farol_locs):
        spawn_instance(col, f"CL_Farol_Galeria_{i+1:02d}", kit["farol_colonial"], fl)


# ---------------------------------------------------------------------------
# 3. SALON DE LA INDEPENDENCIA (CON PIANO S. XIX Y ATAUD CEREMONIAL)
# ---------------------------------------------------------------------------

def build_salon_independencia(col, kit: dict[str, bpy.types.Mesh]):
    sx_in = SALON_ANCHO_INT * 0.5   # 4.60
    sx_out = SALON_ANCHO_EXT * 0.5  # 5.40
    sy0 = SALON_Y0                  # 28.20
    sy_in0 = sy0 + 0.60             # 28.80
    sy_in1 = sy_in0 + SALON_LARGO_INT  # 52.80
    sy1 = sy_in1 + SALON_MURO       # 53.60

    mb = MeshBuilder("CL_Salon_Arquitectura")

    # Piso de baldosa + alfombra roja
    mb.add_box(-sx_in, sx_in, sy_in0, sy_in1, 0.0, Z_SALON_PISO, "piso")
    mb.add_box(-1.05, 1.05, sy0 - 1.40, sy_in1 - PRESIDIO_LARGO + 0.6, Z_SALON_PISO, Z_SALON_PISO + 0.02, "atlas_museo", "rojo")

    # Portada interior del Salon (paso libre 2.60 x 3.60 m)
    spw = SALON_PORTON_ANCHO * 0.5
    mb.add_box(-sx_out, -spw, sy0, sy_in0, 0.0, SALON_ALTO_MURO, "muro")
    mb.add_box(spw, sx_out, sy0, sy_in0, 0.0, SALON_ALTO_MURO, "muro")
    mb.add_arch_spandrel(0.0, SALON_PORTON_ANCHO, sy0, sy_in0, Z_SALON_PISO + 3.05, SALON_ALTO_MURO, 0.55, 10, "muro", ring_mat="piedra", ring_thick=0.18, ring_out=0.05)
    for sgn in (-1.0, 1.0):
        mb.add_box(sgn * 1.45 - 0.25, sgn * 1.45 + 0.25, sy0 - 0.14, sy0 + 0.02, Z_SALON_PISO, Z_SALON_PISO + 3.85, "muro")
        mb.add_box(sgn * 1.95 - 0.18, sgn * 1.95 + 0.18, sy0 - 0.10, sy0 + 0.02, Z_SALON_PISO, Z_SALON_PISO + 3.85, "muro")
    mb.add_box(-2.25, 2.25, sy0 - 0.18, sy0 + 0.02, Z_SALON_PISO + 3.85, Z_SALON_PISO + 4.25, "muro")
    for sgn in (-1.0, 1.0):
        dx = sgn * (spw - 0.06)
        mb.add_box(dx - 0.05, dx + 0.05, sy_in0 + 0.08, sy_in0 + 1.25, Z_SALON_PISO, Z_SALON_PISO + 3.05, "madera")
        for dy in (sy_in0 + 0.28, sy_in0 + 0.62, sy_in0 + 0.98):
            for dz in (0.75, 1.35, 1.95, 2.55, 3.10):
                mb.add_sphere_octa(dx - sgn * 0.07, dy, dz, 0.032, 0.032, 0.032, "oro_bronce")

    # Hastial norte visible sobre el patio + ventana alta
    mb.add_quad((-sx_out, sy0, SALON_ALTO_MURO), (sx_out, sy0, SALON_ALTO_MURO), (0.0, sy0, SALON_ALTO_CUMBRERA), (0.0, sy0, SALON_ALTO_CUMBRERA), "muro")
    mb.add_box(-0.55, 0.55, sy0 - 0.06, sy0 + 0.02, 6.25, 7.35, "madera")
    mb.add_box(-0.42, 0.42, sy0 - 0.08, sy0 - 0.04, 6.32, 7.28, "atlas_museo", "vidrio")
    mb.add_box(-0.72, 0.72, sy0 - 0.35, sy0, 7.35, 7.46, "teja")

    # Muros laterales con 3 ventanas altas abocinadas por lado + puerta cerrada Guerrilleros
    win_ys = [33.50, 39.20, 44.90]
    win_hw = 0.70
    win_z0, win_z1 = 3.90, 5.55

    mb.add_box(-sx_out, -sx_in, sy_in0, sy_in1, 0.0, win_z0, "muro")
    mb.add_box(-sx_out, -sx_in, sy_in0, sy_in1, win_z1, SALON_ALTO_MURO, "muro")
    y_cursor = sy_in0
    for wy in win_ys:
        mb.add_box(-sx_out, -sx_in, y_cursor, wy - win_hw, win_z0, win_z1, "muro")
        mb.add_box(-sx_out, -sx_out + 0.06, wy - win_hw, wy + win_hw, win_z0, win_z1, "atlas_museo", "vidrio")
        mb.add_box(-sx_out + 0.06, -sx_out + 0.14, wy - 0.03, wy + 0.03, win_z0, win_z1, "madera")
        mb.add_box(-sx_out + 0.04, -sx_in + 0.04, wy - win_hw, wy + win_hw, win_z0 - 0.04, win_z0 + 0.04, "madera")
        y_cursor = wy + win_hw
    mb.add_box(-sx_out, -sx_in, y_cursor, sy_in1, win_z0, win_z1, "muro")

    # Paso abierto en arco limpio (2.40 x 3.05 m) hacia Sala de los Guerrilleros con hojas verdes abiertas
    mb.add_box(sx_in, sx_out, sy_in0, 43.80, 0.0, win_z0, "muro")
    mb.add_box(sx_in, sx_out, 46.20, sy_in1, 0.0, win_z0, "muro")
    mb.add_box(sx_in, sx_out, 43.80, 46.20, Z_SALON_PISO + 3.05, win_z0, "muro")
    # Marco completo verde colonial + dintel corrido sin barrotes sueltos + 2 hojas abiertas hacia Guerrilleros
    mb.add_box(sx_in - 0.01, sx_out + 0.01, 43.80, 43.92, Z_SALON_PISO, Z_SALON_PISO + 3.05, "atlas_museo", "verde_bar")
    mb.add_box(sx_in - 0.01, sx_out + 0.01, 46.08, 46.20, Z_SALON_PISO, Z_SALON_PISO + 3.05, "atlas_museo", "verde_bar")
    mb.add_box(sx_in - 0.01, sx_out + 0.01, 43.80, 46.20, Z_SALON_PISO + 2.86, Z_SALON_PISO + 3.06, "atlas_museo", "verde_bar")
    mb.add_box(sx_in - 0.02, sx_out + 0.02, 43.86, 46.14, Z_SALON_PISO + 2.82, Z_SALON_PISO + 2.87, "oro_bronce")
    mb.add_box(sx_out + 0.04, sx_out + 1.05, 43.92, 44.02, Z_SALON_PISO, Z_SALON_PISO + 2.80, "atlas_museo", "verde_bar")
    mb.add_box(sx_out + 0.04, sx_out + 1.05, 45.98, 46.08, Z_SALON_PISO, Z_SALON_PISO + 2.80, "atlas_museo", "verde_bar")
    mb.add_box(sx_in, sx_out, sy_in0, sy_in1, win_z1, SALON_ALTO_MURO, "muro")
    y_cursor = sy_in0
    for wy in [33.50, 39.20]:
        mb.add_box(sx_in, sx_out, y_cursor, wy - win_hw, win_z0, win_z1, "muro")
        mb.add_box(sx_out - 0.06, sx_out, wy - win_hw, wy + win_hw, win_z0, win_z1, "atlas_museo", "vidrio")
        mb.add_box(sx_out - 0.14, sx_out - 0.06, wy - 0.03, wy + 0.03, win_z0, win_z1, "madera")
        mb.add_box(sx_in - 0.04, sx_out - 0.04, wy - win_hw, wy + win_hw, win_z0 - 0.04, win_z0 + 0.04, "madera")
        y_cursor = wy + win_hw
    mb.add_box(sx_in, sx_out, y_cursor, sy_in1, win_z0, win_z1, "muro")

    # Muro Testero + cubierta a dos aguas + liston de cumbrera
    mb.add_box(-sx_out, sx_out, sy_in1, sy1, 0.0, SALON_ALTO_MURO, "muro")
    mb.add_quad((sx_in, sy_in1, SALON_ALTO_MURO), (-sx_in, sy_in1, SALON_ALTO_MURO), (0.0, sy_in1, SALON_ALTO_CUMBRERA - 0.15), (0.0, sy_in1, SALON_ALTO_CUMBRERA - 0.15), "muro")
    mb.add_quad((-sx_out, sy1, SALON_ALTO_MURO), (sx_out, sy1, SALON_ALTO_MURO), (0.0, sy1, SALON_ALTO_CUMBRERA), (0.0, sy1, SALON_ALTO_CUMBRERA), "muro")
    mb.add_sloped_box((-sx_out - 0.25, sy0 - 0.15, SALON_ALTO_MURO - 0.05), (0.0, sy0 - 0.15, SALON_ALTO_CUMBRERA), (0.0, sy1 + 0.25, SALON_ALTO_CUMBRERA), (-sx_out - 0.25, sy1 + 0.25, SALON_ALTO_MURO - 0.05), 0.18, "teja")
    mb.add_sloped_box((0.0, sy0 - 0.15, SALON_ALTO_CUMBRERA), (sx_out + 0.25, sy0 - 0.15, SALON_ALTO_MURO - 0.05), (sx_out + 0.25, sy1 + 0.25, SALON_ALTO_MURO - 0.05), (0.0, sy1 + 0.25, SALON_ALTO_CUMBRERA), 0.18, "teja")
    mb.add_box(-0.14, 0.14, sy0 - 0.18, sy1 + 0.28, SALON_ALTO_CUMBRERA + 0.12, SALON_ALTO_CUMBRERA + 0.28, "teja")

    # Artesonado mudejar oscuro en artesa + 5 vigas tirantes
    z_eave_int = SALON_ALTO_MURO - 0.08
    z_nud = 7.82
    x_nud = 1.65
    mb.add_sloped_box((-sx_in, sy_in0, z_eave_int), (-x_nud, sy_in0, z_nud), (-x_nud, sy_in1, z_nud), (-sx_in, sy_in1, z_eave_int), 0.08, "madera")
    mb.add_sloped_box((x_nud, sy_in0, z_nud), (sx_in, sy_in0, z_eave_int), (sx_in, sy_in1, z_eave_int), (x_nud, sy_in1, z_nud), 0.08, "madera")
    mb.add_box(-x_nud, x_nud, sy_in0, sy_in1, z_nud, z_nud + 0.10, "atlas_museo", "azul_verde")
    # Acentos mudejares rojo y verde en el almizate del artesonado
    mb.add_box(-x_nud + 0.12, -x_nud + 0.28, sy_in0, sy_in1, z_nud - 0.02, z_nud + 0.02, "atlas_museo", "rojo")
    mb.add_box(x_nud - 0.28, x_nud - 0.12, sy_in0, sy_in1, z_nud - 0.02, z_nud + 0.02, "atlas_museo", "rojo")
    mb.add_box(-0.14, 0.14, sy_in0, sy_in1, z_nud - 0.02, z_nud + 0.02, "atlas_museo", "verde_bar")
    for k in range(5):
        ty = sy_in0 + 3.0 + k * 3.55
        mb.add_box(-sx_in, sx_in, ty - 0.12, ty + 0.12, z_eave_int - 0.24, z_eave_int, "madera")
        mb.add_box(-sx_in, -sx_in + 0.55, ty - 0.10, ty + 0.10, z_eave_int - 0.48, z_eave_int - 0.24, "madera")
        mb.add_box(sx_in - 0.55, sx_in, ty - 0.10, ty + 0.10, z_eave_int - 0.48, z_eave_int - 0.24, "madera")
    for k in range(18):
        cy = sy_in0 + 0.65 + k * 1.32
        mb.add_sloped_box((-sx_in, cy - 0.04, z_eave_int - 0.06), (-x_nud, cy - 0.04, z_nud - 0.06), (-x_nud, cy + 0.04, z_nud - 0.06), (-sx_in, cy + 0.04, z_eave_int - 0.06), 0.08, "madera")
        mb.add_sloped_box((x_nud, cy - 0.04, z_nud - 0.06), (sx_in, cy - 0.04, z_eave_int - 0.06), (sx_in, cy + 0.04, z_eave_int - 0.06), (x_nud, cy + 0.04, z_nud - 0.06), 0.08, "madera")

    # Coro / Tribuna dorada en U
    coro_y1 = sy_in0 + CORO_LARGO
    mb.add_box(-sx_in, -2.0, sy_in0, coro_y1, CORO_ALTO - 0.22, CORO_ALTO, "madera")
    mb.add_box(2.0, sx_in, sy_in0, coro_y1, CORO_ALTO - 0.22, CORO_ALTO, "madera")
    mb.add_box(-2.0, 2.0, sy_in0, sy_in0 + 2.2, CORO_ALTO - 0.22, CORO_ALTO, "madera")
    mb.add_box(-sx_in, sx_in, sy_in0 + 2.1, sy_in0 + 2.32, CORO_ALTO - 0.44, CORO_ALTO - 0.22, "madera")
    for cx_c in (-2.0, 2.0):
        mb.add_cylinder(cx_c, sy_in0 + 2.2, Z_SALON_PISO, CORO_ALTO - 0.22, 0.14, 0.12, 8, "madera")
    y_cf = sy_in0 + 2.20
    mb.add_box(-2.0, 2.0, y_cf - 0.08, y_cf + 0.08, CORO_ALTO, CORO_ALTO + 0.38, "oro_bronce")
    mb.add_box(-2.0, 2.0, y_cf - 0.08, y_cf + 0.08, CORO_ALTO + 0.88, CORO_ALTO + 1.06, "oro_bronce")
    for k in range(9):
        bx = -1.80 + k * 0.45
        mb.add_box(bx - 0.05, bx + 0.05, y_cf - 0.05, y_cf + 0.05, CORO_ALTO + 0.38, CORO_ALTO + 0.88, "oro_bronce")
    for sx_b in (-2.04, 2.04):
        mb.add_box(sx_b - 0.08, sx_b + 0.08, y_cf, coro_y1, CORO_ALTO, CORO_ALTO + 0.38, "oro_bronce")
        mb.add_box(sx_b - 0.08, sx_b + 0.08, y_cf, coro_y1, CORO_ALTO + 0.88, CORO_ALTO + 1.06, "oro_bronce")
        for k in range(5):
            by = y_cf + 0.15 + k * 0.48
            mb.add_box(sx_b - 0.05, sx_b + 0.05, by - 0.05, by + 0.05, CORO_ALTO + 0.38, CORO_ALTO + 0.88, "oro_bronce")
    for x0_b, x1_b in ((-sx_in, -2.0), (2.0, sx_in)):
        mb.add_box(x0_b, x1_b, coro_y1 - 0.14, coro_y1, CORO_ALTO, CORO_ALTO + 0.38, "oro_bronce")
        mb.add_box(x0_b, x1_b, coro_y1 - 0.14, coro_y1, CORO_ALTO + 0.88, CORO_ALTO + 1.06, "oro_bronce")
        for k in range(5):
            bx = x0_b + 0.25 + k * 0.52
            mb.add_box(bx - 0.05, bx + 0.05, coro_y1 - 0.12, coro_y1 - 0.02, CORO_ALTO + 0.38, CORO_ALTO + 0.88, "oro_bronce")

    # Gradas laterales y baranda verde divisoria
    mb.add_box(-sx_in, -2.45, coro_y1, 47.40, Z_SALON_PISO, Z_SALON_PISO + 0.22, "piso")
    mb.add_box(-sx_in, -3.55, coro_y1, 47.40, Z_SALON_PISO + 0.22, Z_SALON_PISO + 0.44, "piso")
    mb.add_box(2.45, sx_in, coro_y1, 44.00, Z_SALON_PISO, Z_SALON_PISO + 0.22, "piso")
    mb.add_box(3.55, sx_in, coro_y1, 44.00, Z_SALON_PISO + 0.22, Z_SALON_PISO + 0.44, "piso")
    for bx, y_end in ((-2.42, 47.20), (2.42, 43.80)):
        mb.add_box(bx - 0.05, bx + 0.05, coro_y1 + 0.2, y_end, Z_SALON_PISO + 0.22, Z_SALON_PISO + 0.30, "atlas_museo", "verde_bar")
        mb.add_box(bx - 0.06, bx + 0.06, coro_y1 + 0.2, y_end, Z_SALON_PISO + 1.08, Z_SALON_PISO + 1.16, "atlas_museo", "verde_bar")
        by = coro_y1 + 0.40
        while by < y_end - 0.15:
            mb.add_box(bx - 0.02, bx + 0.02, by - 0.02, by + 0.02, Z_SALON_PISO + 0.30, Z_SALON_PISO + 1.08, "atlas_museo", "verde_bar")
            by += 0.42
        for py in (coro_y1 + 0.25, (coro_y1 + y_end) * 0.5, y_end):
            mb.add_box(bx - 0.07, bx + 0.07, py - 0.07, py + 0.07, Z_SALON_PISO + 0.22, Z_SALON_PISO + 1.24, "atlas_museo", "verde_bar")
            mb.add_sphere_octa(bx, py, Z_SALON_PISO + 1.32, 0.07, 0.07, 0.07, "atlas_museo", "verde_bar")

    # Pedestal y Urna del Acta de la Independencia (con vidrio ligero de proteccion)
    ay = 47.00
    mb.add_box(-0.56, 0.56, ay - 0.56, ay + 0.56, Z_SALON_PISO, Z_SALON_PISO + 0.16, "piedra")
    mb.add_box(-0.42, 0.42, ay - 0.42, ay + 0.42, Z_SALON_PISO + 0.16, Z_SALON_PISO + 1.18, "piedra")
    mb.add_box(-0.52, 0.52, ay - 0.52, ay + 0.52, Z_SALON_PISO + 1.18, Z_SALON_PISO + 1.32, "piedra")
    mb.add_box(-0.38, 0.38, ay - 0.34, ay + 0.34, Z_SALON_PISO + 1.32, Z_SALON_PISO + 1.44, "oro_bronce")
    mb.add_sloped_box((-0.34, ay - 0.30, Z_SALON_PISO + 1.44), (0.34, ay - 0.30, Z_SALON_PISO + 1.44), (0.34, ay + 0.30, Z_SALON_PISO + 1.62), (-0.34, ay + 0.30, Z_SALON_PISO + 1.62), 0.03, "oro_bronce")
    u0, v0, u1, v1 = cell_uv("acta")
    mb.add_quad((-0.26, ay - 0.22, Z_SALON_PISO + 1.48), (0.26, ay - 0.22, Z_SALON_PISO + 1.48), (0.26, ay + 0.22, Z_SALON_PISO + 1.66), (-0.26, ay + 0.22, Z_SALON_PISO + 1.66), "atlas_museo", (u0, v0, u1, v1))
    add_vitrine_glass_box(mb, -0.35, 0.35, ay - 0.31, ay + 0.31, Z_SALON_PISO + 1.44, Z_SALON_PISO + 1.72)

    # --- PIANO DE MESA DEL SIGLO XIX (angulo SO del presidio, X=-3.95, Y=47.85) ---
    px_pi, py_pi = -3.90, 47.85
    mb.add_box(px_pi - 0.45, px_pi + 0.45, py_pi - 0.85, py_pi + 0.85, Z_SALON_PISO + 0.72, Z_SALON_PISO + 0.94, "madera")
    for lx in (px_pi - 0.38, px_pi + 0.36):
        for ly in (py_pi - 0.78, py_pi + 0.74):
            mb.add_cylinder(lx, ly, Z_SALON_PISO, Z_SALON_PISO + 0.72, 0.045, 0.06, 8, "madera")
    # Teclado saliente mirando hacia +X (al centro del salon) + tapa inclinada
    mb.add_box(px_pi + 0.45, px_pi + 0.62, py_pi - 0.62, py_pi + 0.62, Z_SALON_PISO + 0.72, Z_SALON_PISO + 0.78, "madera")
    u0, v0, u1, v1 = cell_uv("piano_teclas")
    mb.add_quad((px_pi + 0.45, py_pi - 0.58, Z_SALON_PISO + 0.785), (px_pi + 0.45, py_pi + 0.58, Z_SALON_PISO + 0.785), (px_pi + 0.60, py_pi + 0.58, Z_SALON_PISO + 0.785), (px_pi + 0.60, py_pi - 0.58, Z_SALON_PISO + 0.785), "atlas_museo", (u0, v0, u1, v1))
    mb.add_sloped_box((px_pi - 0.44, py_pi - 0.82, Z_SALON_PISO + 0.94), (px_pi + 0.38, py_pi - 0.82, Z_SALON_PISO + 1.24), (px_pi + 0.38, py_pi + 0.82, Z_SALON_PISO + 1.24), (px_pi - 0.44, py_pi + 0.82, Z_SALON_PISO + 0.94), 0.03, "madera")

    # Presidio elevado + Testero
    yp0 = sy_in1 - PRESIDIO_LARGO  # 48.40
    mb.add_box(-sx_in, sx_in, yp0 - 0.45, yp0, Z_SALON_PISO, Z_SALON_PISO + 0.22, "atlas_museo", "rojo")
    mb.add_box(-sx_in, sx_in, yp0, sy_in1, Z_SALON_PISO, Z_PRESIDIO, "piso")
    mb.add_box(-2.8, 2.8, yp0, yp0 + 2.2, Z_PRESIDIO, Z_PRESIDIO + 0.02, "atlas_museo", "rojo")

    mb.add_box(-1.55, 1.55, yp0 + 0.90, yp0 + 1.85, Z_PRESIDIO, Z_PRESIDIO + 0.84, "atlas_museo", "rojo")
    for cx_cand in (-0.85, 0.85):
        mb.add_cylinder(cx_cand, yp0 + 1.35, Z_PRESIDIO + 0.84, Z_PRESIDIO + 1.32, 0.08, 0.03, 10, "oro_bronce")
        mb.add_sphere_octa(cx_cand, yp0 + 1.35, Z_PRESIDIO + 1.38, 0.05, 0.05, 0.07, "atlas_museo", "vela")

    mb.add_box(-0.36, 0.36, yp0 + 2.05, yp0 + 2.60, Z_PRESIDIO, Z_PRESIDIO + 0.50, "atlas_museo", "rojo")
    mb.add_box(-0.36, 0.36, yp0 + 2.52, yp0 + 2.62, Z_PRESIDIO + 0.50, Z_PRESIDIO + 1.48, "atlas_museo", "rojo")
    mb.add_box(-0.40, 0.40, yp0 + 2.50, yp0 + 2.64, Z_PRESIDIO + 1.48, Z_PRESIDIO + 1.86, "oro_bronce")

    wall_y = sy_in1 - 0.04
    portraits = [
        (0.0,   2.85, 1.65, 2.25, "bolivar"),
        (-2.25, 2.70, 1.30, 1.78, "sucre"),
        (2.25,  2.70, 1.25, 1.75, "ballivian"),
        (-1.28, 3.05, 0.38, 0.88, "espadas"),
        (1.28,  3.05, 0.38, 0.88, "espadas"),
        (-1.85, 4.75, 0.95, 1.25, "ret_sup_izq"),
        (1.85,  4.75, 0.95, 1.25, "ret_sup_der"),
    ]
    for px_c, pz_b, pw_c, ph_c, ckey in portraits:
        add_beveled_frame_painting(mb, px_c, wall_y, pz_b + ph_c * 0.5, pw_c, ph_c, "-Y", ckey, frame_w=0.07, depth=0.065)

    u0, v0, u1, v1 = cell_uv("oculo")
    mb.add_box(-0.72, 0.72, wall_y - 0.05, wall_y + 0.04, 6.28, 7.22, "muro")
    mb.add_quad((-0.58, wall_y - 0.08, 6.35), (0.58, wall_y - 0.08, 6.35), (0.58, wall_y - 0.08, 7.15), (-0.58, wall_y - 0.08, 7.15), "atlas_museo", (u0, v0, u1, v1))

    for bx, dir_x, ckey in ((-3.85, 1.0, "bandera"), (3.85, -1.0, "wiphala")):
        mb.add_cylinder(bx, sy_in1 - 0.45, Z_PRESIDIO, Z_PRESIDIO + 2.85, 0.025, 0.02, 6, "madera")
        u0, v0, u1, v1 = cell_uv(ckey)
        x_edge = bx + dir_x * 0.84
        x0_f, x1_f = sorted((bx, x_edge))
        mb.add_quad((x0_f, sy_in1 - 0.45, Z_PRESIDIO + 1.05), (x1_f, sy_in1 - 0.45, Z_PRESIDIO + 1.05), (x1_f, sy_in1 - 0.45, Z_PRESIDIO + 2.55), (x0_f, sy_in1 - 0.45, Z_PRESIDIO + 2.55), "atlas_museo", (u0, v0, u1, v1))

    mb.to_object(col, "CL_Salon_Arquitectura")

    # Instancias modulares del Salon
    for k in range(10):
        yy = coro_y1 + 0.65 + k * 0.96
        spawn_instance(col, f"CL_Sitial_Izq_{k+1:02d}", kit["sitial_sup"], (-sx_in + 0.36, yy, Z_SALON_PISO + 0.44), -90.0)
        spawn_instance(col, f"CL_Escano_Izq_{k+1:02d}", kit["escano_inf"], (-sx_in + 1.48, yy, Z_SALON_PISO + 0.22), -90.0)
    for k in range(7):
        yy = coro_y1 + 0.65 + k * 0.96
        spawn_instance(col, f"CL_Sitial_Der_{k+1:02d}", kit["sitial_sup"], (sx_in - 0.36, yy, Z_SALON_PISO + 0.44), 90.0)
        spawn_instance(col, f"CL_Escano_Der_{k+1:02d}", kit["escano_inf"], (sx_in - 1.48, yy, Z_SALON_PISO + 0.22), 90.0)

    for k in range(4):
        yy = 43.80 + k * 0.92
        spawn_instance(col, f"CL_Silla_Dip_Izq_{k+1:02d}", kit["silla_presidio"], (-1.85, yy, Z_SALON_PISO), -75.0)
        if k < 3:
            spawn_instance(col, f"CL_Silla_Dip_Der_{k+1:02d}", kit["silla_presidio"], (1.85, yy, Z_SALON_PISO), 75.0)

    pres_chairs = [
        (-3.6, yp0 + 2.4, -20.0), (-2.7, yp0 + 2.6, -10.0), (-1.8, yp0 + 2.7, -5.0), (-0.95, yp0 + 2.75, 0.0),
        (0.95, yp0 + 2.75, 0.0), (1.8, yp0 + 2.7, 5.0), (2.7, yp0 + 2.6, 10.0), (3.6, yp0 + 2.4, 20.0),
    ]
    for i, (cx_p, cy_p, rot_p) in enumerate(pres_chairs):
        spawn_instance(col, f"CL_Silla_Presidio_{i+1:02d}", kit["silla_presidio"], (cx_p, cy_p, Z_PRESIDIO), rot_p)

    spawn_instance(col, "CL_Arana_Cristal_01", kit["arana_cristal"], (0.0, 38.2, z_nud - 2.15))
    spawn_instance(col, "CL_Arana_Cristal_02", kit["arana_cristal"], (0.0, 45.6, z_nud - 2.15))


# ---------------------------------------------------------------------------
# 4. NUEVA SALA MUSEOGRAFICA LATERAL NAVEGABLE (SALA GUERRILLEROS / VIRREINAL)
# ---------------------------------------------------------------------------

def _add_eagle_pedestal(mb: MeshBuilder, ax: float, ay: float, z0: float, face_east: bool = False):
    """Pedestal del Aguila tallada en madera con alas curvas y perfil de plumas (~420 tris)."""
    def _pt(dx: float, dy: float, dz: float) -> tuple[float, float, float]:
        # Por defecto mira hacia -Y; face_east=True lo rota +90 deg para mirar al Claustro (+X)
        return (ax - dy, ay + dx, z0 + dz) if face_east else (ax + dx, ay + dy, z0 + dz)

    # Base escalonada octagonal tallada
    mb.add_cylinder(ax, ay, z0, z0 + 0.08, 0.38, 0.34, 8, "madera", cap_bot=False)
    mb.add_cylinder(ax, ay, z0 + 0.08, z0 + 0.22, 0.32, 0.22, 8, "madera", cap_top=False, cap_bot=False)
    # Penacho / roca base + cuerpo musculoso del aguila
    mb.add_cylinder(ax, ay, z0 + 0.22, z0 + 0.56, 0.16, 0.19, 10, "madera", cap_top=False, cap_bot=False)
    mb.add_cylinder(ax, ay, z0 + 0.56, z0 + 0.88, 0.19, 0.13, 10, "madera", cap_top=False, cap_bot=False)
    # Cuello y cabeza esculpida con pico curvo hacia el frente
    cx_h, cy_h, _ = _pt(0.0, -0.02, 0.0)
    mb.add_cylinder(cx_h, cy_h, z0 + 0.88, z0 + 1.00, 0.09, 0.075, 8, "madera", cap_top=False, cap_bot=False)
    mb.add_beam(_pt(0.0, -0.04, 0.99), _pt(0.0, -0.19, 0.94), 0.042, 6, "madera")
    # Alas desplegadas y curvadas hacia abajo (5 plumas escalonadas en arco por ala)
    for sgn in (-1.0, 1.0):
        wing_pts = [
            (0.08, 0.86, 0.06),
            (0.20, 0.94, 0.055),
            (0.34, 0.88, 0.048),
            (0.45, 0.72, 0.040),
            (0.48, 0.50, 0.032),
            (0.36, 0.32, 0.024),
        ]
        for (px0, pz0, r0), (px1, pz1, r1) in zip(wing_pts, wing_pts[1:]):
            mb.add_beam(_pt(sgn * px0, 0.02, pz0), _pt(sgn * px1, 0.04, pz1), (r0 + r1) * 0.5, 5, "madera")
        for fx, fz_top, fz_bot in ((0.22, 0.86, 0.48), (0.31, 0.80, 0.42), (0.40, 0.68, 0.34)):
            mb.add_beam(_pt(sgn * fx, 0.03, fz_top), _pt(sgn * (fx + 0.03), 0.05, fz_bot), 0.026, 4, "madera")
    # Bandeja y cofre historico encima
    hx, hy = (0.25, 0.38) if face_east else (0.38, 0.25)
    chx, chy = (0.18, 0.28) if face_east else (0.28, 0.18)
    ochx, ochy = (0.19, 0.30) if face_east else (0.30, 0.19)
    mb.add_box(ax - hx, ax + hx, ay - hy, ay + hy, z0 + 0.96, z0 + 1.02, "madera")
    mb.add_box(ax - chx, ax + chx, ay - chy, ay + chy, z0 + 1.02, z0 + 1.24, "madera")
    mb.add_box(ax - ochx, ax + ochx, ay - ochy, ay + ochy, z0 + 1.24, z0 + 1.30, "oro_bronce")


def _build_bolivar_bust_mesh() -> bpy.types.Mesh:
    """Esculpe el busto de Simon Bolivar sobre pedestal de piedra y detalles dorados (~1035 tris)."""
    bm = bmesh.new()
    mat_slots = ["hierro", "piedra", "oro_bronce"]  # 0: bronce oscuro, 1: piedra pedestal, 2: dorado militar
    flat_faces = set()

    def _add_loft(rings, mat_idx: int, cap_bot: bool = False, cap_top: bool = False, smooth: bool = True):
        prev = None
        for rz, coords in rings:
            ring = [bm.verts.new((cx, cy, rz)) for cx, cy in coords]
            n = len(ring)
            if prev is not None:
                for k in range(n):
                    kn = (k + 1) % n
                    f = bm.faces.new((prev[k], prev[kn], ring[kn], ring[k]))
                    f.material_index = mat_idx
                    if not smooth:
                        flat_faces.add(f)
            elif cap_bot:
                f = bm.faces.new(list(reversed(ring)))
                f.material_index = mat_idx
                if not smooth:
                    flat_faces.add(f)
            prev = ring
        if prev is not None and cap_top:
            f = bm.faces.new(prev)
            f.material_index = mat_idx
            if not smooth:
                flat_faces.add(f)

    def _sq(hw: float, hd: float):
        return [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]

    def _oct(r: float, n: int = 8):
        return [(math.cos(2.0 * math.pi * k / n) * r, math.sin(2.0 * math.pi * k / n) * r) for k in range(n)]

    def _ell(rx: float, ry: float, n: int = 12):
        return [(math.cos(2.0 * math.pi * k / n) * rx, math.sin(2.0 * math.pi * k / n) * ry) for k in range(n)]

    # 1. Pedestal arquitectonico en piedra clara (0.00 .. 1.12 m) — base solida para busto monumental
    _add_loft([(0.00, _sq(0.42, 0.42)), (0.16, _sq(0.42, 0.42)), (0.26, _sq(0.30, 0.30))],
              mat_idx=1, cap_bot=True, cap_top=True, smooth=False)
    _add_loft([(0.24, _oct(0.275)), (0.98, _oct(0.235)), (1.05, _oct(0.295))],
              mat_idx=1, cap_bot=False, cap_top=True, smooth=False)
    _add_loft([(1.05, _sq(0.335, 0.335)), (1.12, _sq(0.335, 0.335))],
              mat_idx=1, cap_bot=True, cap_top=True, smooth=False)

    # 2. Socle circular torneado en bronce oscuro (1.12 .. 1.32 m)
    _add_loft([(1.12, _ell(0.260, 0.245)), (1.18, _ell(0.200, 0.188)), (1.25, _ell(0.158, 0.148)), (1.32, _ell(0.182, 0.168))],
              mat_idx=0, cap_bot=True, cap_top=False, smooth=True)

    # 3. Torso heroico monumental con casaca militar 1825, cuello alto en V y hombros anchos (1.32 .. 1.86 m)
    chest_rings = [
        (1.32, 0.195, 0.165),
        (1.46, 0.445, 0.250),
        (1.63, 0.560, 0.265),
        (1.74, 0.320, 0.215),
        (1.86, 0.175, 0.162),
    ]
    prev_ring = None
    for rz, rx, ry in chest_rings:
        ring = []
        for k in range(14):
            ang = 2.0 * math.pi * k / 14.0
            ca, sa = math.cos(ang), math.sin(ang)
            dip = -0.075 * max(0.0, -sa) if rz >= 1.72 else 0.0
            if rz <= 1.48 and sa < -0.35:
                ry_cur = ry * 1.07
            else:
                ry_cur = ry
            ring.append(bm.verts.new((ca * rx, sa * ry_cur, rz + dip)))
        if prev_ring is not None:
            for k in range(14):
                kn = (k + 1) % 14
                f = bm.faces.new((prev_ring[k], prev_ring[kn], ring[kn], ring[k]))
                f.material_index = 0
        else:
            f = bm.faces.new(list(reversed(ring)))
            f.material_index = 0
        prev_ring = ring
    f_cap = bm.faces.new(prev_ring)
    f_cap.material_index = 0

    # 4. Charreteras, solapas en V y medalla pectoral en oro_bronce (escala monumental)
    before_gold = set(bm.faces)
    for sgn in (-1.0, 1.0):
        _bm_add_tube(bm, Vector((sgn * 0.275, 0.0, 1.69)), Vector((sgn * 0.555, 0.0, 1.59)), 0.064, 0.094, segs=8)
        _bm_add_tube(bm, Vector((sgn * 0.130, -0.162, 1.74)), Vector((sgn * 0.025, -0.255, 1.48)), 0.019, 0.017, segs=5)
    _bm_add_tube(bm, Vector((-0.180, -0.244, 1.57)), Vector((-0.194, -0.280, 1.57)), 0.052, 0.044, segs=6)
    for f in bm.faces:
        if f not in before_gold:
            f.material_index = 2

    # 5. Cuello anatomico (1.78 .. 2.06 m)
    before_neck = set(bm.faces)
    _bm_add_tube(bm, Vector((0.0, -0.020, 1.78)), Vector((0.0, -0.032, 2.06)), 0.128, 0.108, segs=10)
    for f in bm.faces:
        if f not in before_neck:
            f.material_index = 0

    # 6. Cabeza clasica monumental proporcionada (22x15 ~ 616 tris)
    uv_ret = bmesh.ops.create_uvsphere(bm, u_segments=22, v_segments=15, radius=0.238)
    for v in uv_ret["verts"]:
        p = v.co
        nx, ny, nz = p.x / 0.238, p.y / 0.238, p.z / 0.238
        jaw_taper = 0.72 + 0.28 * max(0.0, min(1.0, (nz + 0.58) / 0.88))
        sx = p.x * 0.80 * jaw_taper
        sy = p.y * 0.98
        sz = p.z * 1.18

        if ny < -0.10:
            sy -= 0.017 * math.exp(-((nz - 0.44) / 0.22) ** 2) * max(0.0, 1.0 - (nx / 0.75) ** 2)
            sy -= 0.034 * math.exp(-((nz - 0.18) / 0.10) ** 2) * max(0.0, 1.0 - (nx / 0.68) ** 2)
            for ex in (-0.28, 0.28):
                eye_d = ((nx - ex) / 0.15) ** 2 + ((nz - 0.05) / 0.11) ** 2
                sy += 0.038 * math.exp(-eye_d)
            if -0.24 < nz < 0.22:
                nose_w = math.exp(-((nx / 0.105) ** 2))
                nose_p = max(0.0, 1.0 - ((nz + 0.02) / 0.22) ** 2)
                sy -= 0.082 * nose_w * (nose_p ** 0.70)
            for cx_p in (-0.40, 0.40):
                sy -= 0.024 * math.exp(-(((nx - cx_p) / 0.17) ** 2 + ((nz + 0.04) / 0.14) ** 2))
                sy += 0.020 * math.exp(-(((nx - cx_p * 0.85) / 0.18) ** 2 + ((nz + 0.24) / 0.14) ** 2))
            sy -= 0.017 * math.exp(-(((nx / 0.16) ** 2 + ((nz + 0.28) / 0.06) ** 2)))
            sy += 0.022 * math.exp(-(((nx / 0.18) ** 2 + ((nz + 0.40) / 0.07) ** 2)))
            sy -= 0.038 * math.exp(-(((nx / 0.20) ** 2 + ((nz + 0.58) / 0.15) ** 2)))

        if abs(nx) > 0.76 and -0.22 < nz < 0.14 and -0.14 < ny < 0.24:
            ear_f = math.exp(-(((nz + 0.04) / 0.14) ** 2 + ((ny - 0.04) / 0.14) ** 2))
            sx += math.copysign(0.030, nx) * ear_f

        if nz > 0.34 or ny > 0.02 or (abs(nx) > 0.62 and nz > -0.34):
            curl = 0.022 * (math.sin(nx * 14.0) * math.cos(nz * 10.0) + 0.65 * math.cos(ny * 12.0))
            sx += nx * (0.032 + curl)
            sy += ny * (0.030 + curl)
            sz += max(0.0, nz) * (0.034 + curl * 0.9)

        v.co = Vector((sx, sy - 0.030, sz + 2.24))

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    uv_layer = bm.loops.layers.uv.verify()
    for f in bm.faces:
        f.smooth = f not in flat_faces
        m_name = mat_slots[f.material_index] if f.material_index < len(mat_slots) else "hierro"
        tile = UV_TILE_METERS.get(m_name, 1.0)
        nz_f = abs(f.normal.z)
        for loop in f.loops:
            co = loop.vert.co
            if nz_f > 0.7:
                loop[uv_layer].uv = (co.x / tile, co.y / tile)
            else:
                loop[uv_layer].uv = ((co.x + co.y) / tile, co.z / tile)

    mesh = bpy.data.meshes.new("CL_Busto_Bolivar")
    bm.to_mesh(mesh)
    bm.free()
    for m_name in mat_slots:
        mesh.materials.append(get_or_create_material(m_name))
    mesh.update()
    return mesh


def build_sala_lateral_museo(col, kit: dict[str, bpy.types.Mesh]):
    """Sala de los Guerrilleros cerrada (6.20 x 19.60 m) con acceso directo desde Claustro y Salon."""
    x0 = SALON_ANCHO_EXT * 0.5                # 5.40 (pegada al muro Este del Salon)
    x1 = x0 + 6.20                            # 11.60
    x_out = x1 + 0.50                         # 12.10
    y0 = CLAUSTRO_Y0 + CLAUSTRO_FONDO_EXT     # 28.20 (acceso directo desde galeria Norte-Este X=7.10..9.50)
    y1 = 47.80
    y_out1 = y1 + 0.50                        # 48.30
    z_top = 4.80
    z_ridge = 6.30

    mb = MeshBuilder("CL_Sala_Guerrilleros")
    mb.add_box(x0, x1, y0, y1, 0.0, Z_SALON_PISO, "piso")
    # Zocalos piedra Norte, Sur (flanqueando puerta del claustro) y Este
    mb.add_box(x0, x1, y1 - 0.05, y1, Z_SALON_PISO, Z_SALON_PISO + 0.30, "piedra")
    mb.add_box(x0, 7.00, y0, y0 + 0.05, Z_SALON_PISO, Z_SALON_PISO + 0.30, "piedra")
    mb.add_box(9.60, x1, y0, y0 + 0.05, Z_SALON_PISO, Z_SALON_PISO + 0.30, "piedra")
    mb.add_box(x1 - 0.05, x1, y0, y1, Z_SALON_PISO, Z_SALON_PISO + 0.30, "piedra")

    # Muros exteriores completamente cerrados: Norte, Este continuo y remate Sur-Este (X=11.00..12.10)
    mb.add_box(x0, x_out, y1, y_out1, 0.0, z_top, "muro")
    mb.add_box(x1, x_out, y0, y1, 0.0, z_top, "muro")
    mb.add_box(CLAUSTRO_ANCHO_EXT * 0.5, x_out, y0 - 0.60, y0, 0.0, z_top, "muro")

    # Techo de teja exterior (sin invadir el muro del claustro ni el del Salon) + artesonado verde azulado interior
    xm = (x0 + x_out) * 0.5
    mb.add_sloped_box((x0, y0, z_top), (xm, y0, z_ridge), (xm, y_out1 + 0.25, z_ridge), (x0, y_out1 + 0.25, z_top), 0.18, "teja")
    mb.add_sloped_box((xm, y0, z_ridge), (x_out + 0.15, y0, z_top), (x_out + 0.15, y_out1 + 0.25, z_top), (xm, y_out1 + 0.25, z_ridge), 0.18, "teja")
    mb.add_box(x0, x1, y0, y1, z_top - 0.14, z_top, "atlas_museo", "azul_verde")
    for k in range(14):
        vy = y0 + 0.75 + k * 1.38
        mb.add_box(x0, x1, vy - 0.08, vy + 0.08, z_top - 0.30, z_top - 0.14, "madera")
    for vx in (x0 + 1.5, x0 + 3.1, x0 + 4.7):
        mb.add_box(vx - 0.06, vx + 0.06, y0, y1, z_top - 0.22, z_top - 0.14, "madera")

    # Muro Norte (Juana Azurduy grande + altar con cofre cubierto con banderas Bolivia y Argentina + vitrina roja)
    add_beveled_frame_painting(mb, x0 + 3.10, y1, 2.75, 2.15, 1.85, "-Y", "juana_grande", frame_w=0.085, depth=0.065)
    mx_c, my_c = x0 + 3.10, y1 - 0.45
    mb.add_box(mx_c - 0.72, mx_c + 0.72, my_c - 0.34, my_c + 0.34, Z_SALON_PISO + 0.72, Z_SALON_PISO + 0.80, "madera")
    for lx in (mx_c - 0.65, mx_c + 0.61):
        for ly in (my_c - 0.28, my_c + 0.24):
            mb.add_box(lx, lx + 0.05, ly, ly + 0.05, Z_SALON_PISO, Z_SALON_PISO + 0.72, "madera")
    mb.add_box(mx_c - 0.44, mx_c + 0.44, my_c - 0.24, my_c + 0.24, Z_SALON_PISO + 0.80, Z_SALON_PISO + 1.18, "madera")
    mb.add_box(mx_c - 0.45, mx_c, my_c - 0.25, my_c + 0.25, Z_SALON_PISO + 0.82, Z_SALON_PISO + 1.22, "atlas_museo", "bandera")
    mb.add_box(mx_c, mx_c + 0.45, my_c - 0.25, my_c + 0.25, Z_SALON_PISO + 0.82, Z_SALON_PISO + 1.22, "atlas_museo", "bandera_belgrano")
    mb.add_box(mx_c - 0.62, mx_c + 0.62, my_c - 0.92, my_c - 0.38, Z_SALON_PISO, Z_SALON_PISO + 0.36, "atlas_museo", "rojo")
    mb.add_box(mx_c - 0.24, mx_c + 0.24, my_c - 0.82, my_c - 0.44, Z_SALON_PISO + 0.36, Z_SALON_PISO + 0.56, "atlas_museo", "rojo")
    add_vitrine_glass_box(mb, mx_c - 0.58, mx_c + 0.58, my_c - 0.88, my_c - 0.42, Z_SALON_PISO + 0.36, Z_SALON_PISO + 0.84)

    # Muro Oeste (Sur a Norte antes de la cancela verde Y=43.8..46.2): Padilla, Casimiro Olaneta y consola con 4 patas
    add_beveled_frame_painting(mb, x0, 32.00, 2.52, 1.25, 1.55, "+X", "guerrillera", frame_w=0.06, depth=0.06)
    add_beveled_frame_painting(mb, x0, 35.40, 2.52, 1.10, 1.42, "+X", "cuadro_pasillo", frame_w=0.06, depth=0.06)
    mb.add_box(x0, x0 + 0.03, 35.22, 35.58, 1.62, 1.72, "oro_bronce")
    add_beveled_frame_painting(mb, x0, 39.60, 2.52, 1.15, 1.48, "+X", "guerrillera", frame_w=0.06, depth=0.06)
    add_beveled_frame_painting(mb, x0, 41.35, 2.52, 1.40, 1.12, "+X", "batalla", frame_w=0.06, depth=0.06)

    # Consola de madera apoyada firmemente en 4 patas hasta el piso + cofre tallado encima
    cs_y0, cs_y1 = 40.30, 41.60
    mb.add_box(x0 + 0.04, x0 + 0.56, cs_y0, cs_y1, Z_SALON_PISO + 0.72, Z_SALON_PISO + 0.78, "madera")
    for lx in (x0 + 0.07, x0 + 0.48):
        for ly in (cs_y0 + 0.04, cs_y1 - 0.09):
            mb.add_box(lx, lx + 0.05, ly, ly + 0.05, Z_SALON_PISO, Z_SALON_PISO + 0.72, "madera")
    mb.add_box(x0 + 0.08, x0 + 0.50, cs_y0 + 0.06, cs_y1 - 0.06, Z_SALON_PISO + 0.16, Z_SALON_PISO + 0.20, "madera")
    mb.add_box(x0 + 0.14, x0 + 0.46, 40.70, 41.20, Z_SALON_PISO + 0.78, Z_SALON_PISO + 1.04, "madera")

    # Muro Este: Templete de la Bandera de Macha (Belgrano) + cuadros historicos
    by_t = 33.40
    mb.add_box(x1 - 0.54, x1, by_t - 0.96, by_t + 0.96, Z_SALON_PISO, Z_SALON_PISO + 0.86, "piso")
    mb.add_box(x1 - 0.50, x1 - 0.04, by_t - 0.88, by_t + 0.88, Z_SALON_PISO + 0.86, Z_SALON_PISO + 0.92, "madera")
    u0, v0, u1, v1 = cell_uv("bandera_belgrano")
    mb.add_quad((x1 - 0.44, by_t - 0.74, Z_SALON_PISO + 0.94), (x1 - 0.44, by_t + 0.74, Z_SALON_PISO + 0.94),
                (x1 - 0.12, by_t + 0.74, Z_SALON_PISO + 0.94), (x1 - 0.12, by_t - 0.74, Z_SALON_PISO + 0.94),
                "atlas_museo", (u0, v0, u1, v1))
    add_vitrine_glass_box(mb, x1 - 0.48, x1 - 0.08, by_t - 0.82, by_t + 0.82, Z_SALON_PISO + 0.92, Z_SALON_PISO + 1.24)
    add_beveled_frame_painting(mb, x1, by_t, 2.55, 1.35, 1.10, "-X", "batalla", frame_w=0.06, depth=0.06)
    add_beveled_frame_painting(mb, x1, 38.80, 2.55, 1.15, 1.45, "-X", "ret_sup_izq", frame_w=0.06, depth=0.06)
    add_beveled_frame_painting(mb, x1, 43.00, 2.55, 0.95, 1.40, "-X", "espadas", frame_w=0.06, depth=0.06)
    add_beveled_frame_painting(mb, x1, 46.20, 2.55, 1.10, 1.38, "-X", "cuadro_pasillo", frame_w=0.06, depth=0.06)

    # Canon de montana al centro sobre pedestal de madera + 4 vidrios bajos sin tapa (tubo sobresale arriba)
    cx_c, cy_c = x0 + 3.10, 42.40
    mb.add_box(cx_c - 0.82, cx_c + 0.82, cy_c - 0.46, cy_c + 0.46, Z_SALON_PISO, Z_SALON_PISO + 0.56, "madera")
    mb.add_box(cx_c - 0.56, cx_c + 0.56, cy_c - 0.22, cy_c + 0.22, Z_SALON_PISO + 0.56, Z_SALON_PISO + 0.82, "madera")
    mb.add_beam((cx_c - 0.82, cy_c, Z_SALON_PISO + 1.08), (cx_c + 0.74, cy_c, Z_SALON_PISO + 0.86), 0.115, 10, "hierro")
    mb.add_cylinder(cx_c + 0.78, cy_c, Z_SALON_PISO + 0.80, Z_SALON_PISO + 0.94, 0.055, 0.045, 8, "hierro")
    t_v = 0.008
    mb.add_box(cx_c - 0.80, cx_c + 0.80, cy_c - 0.44, cy_c - 0.44 + t_v, Z_SALON_PISO + 0.56, Z_SALON_PISO + 0.88, "vidrio_vitrina")
    mb.add_box(cx_c - 0.80, cx_c + 0.80, cy_c + 0.44 - t_v, cy_c + 0.44, Z_SALON_PISO + 0.56, Z_SALON_PISO + 0.88, "vidrio_vitrina")
    mb.add_box(cx_c - 0.80, cx_c - 0.80 + t_v, cy_c - 0.44, cy_c + 0.44, Z_SALON_PISO + 0.56, Z_SALON_PISO + 0.88, "vidrio_vitrina")
    mb.add_box(cx_c + 0.80 - t_v, cx_c + 0.80, cy_c - 0.44, cy_c + 0.44, Z_SALON_PISO + 0.56, Z_SALON_PISO + 0.88, "vidrio_vitrina")

    mb.to_object(col, "CL_Sala_Guerrilleros")
    spawn_instance(col, "CL_Silla_Guerrilleros_01", kit["silla_presidio"], (x0 + 1.15, y1 - 0.55, Z_SALON_PISO), 180.0)
    spawn_instance(col, "CL_Silla_Guerrilleros_02", kit["silla_presidio"], (x0 + 5.05, y1 - 0.55, Z_SALON_PISO), 180.0)
    spawn_instance(col, "CL_Arana_Guerrilleros", kit["arana_cristal"], (x0 + 3.10, 42.40, z_top - 1.35), 0.0)


def build_sala_bolivar(col, kit: dict[str, bpy.types.Mesh]):
    """Salon del Antiguo Senado / Galeria de los Presidentes (6.20 x 14.40 m, ala Oeste desde el patio)."""
    x0 = -CLAUSTRO_ANCHO_EXT * 0.5 - 6.20     # -17.20
    x1 = -CLAUSTRO_ANCHO_EXT * 0.5            # -11.00 (pegada al muro Oeste del claustro)
    x_out = x0 - 0.45                         # -17.65
    xm = (x0 + x1) * 0.5                      # -14.10
    y0 = 18.80
    y1 = 33.20
    y_out0 = y0 - 0.45                        # 18.35
    y_out1 = y1 + 0.45                        # 33.65
    y_cl_n = CLAUSTRO_Y0 + CLAUSTRO_FONDO_EXT # 28.20
    z_top = 5.40
    z_ridge = 6.80

    mb = MeshBuilder("CL_Sala_Bolivar")
    mb.add_box(x0, x1, y0, y1, 0.0, Z_SALON_PISO, "piso")

    # Muros perimetrales (Oeste, Sur, Norte y tramo Este mas alla del claustro en Y=28.20..33.65)
    mb.add_box(x_out, x0, y_out0, y_out1, 0.0, z_top, "muro")
    mb.add_box(x0, x1, y_out0, y0, 0.0, z_top, "muro")
    mb.add_box(x0, x1, y1, y_out1, 0.0, z_top, "muro")
    mb.add_box(x1, x1 + 0.45, y_cl_n, y_out1, 0.0, z_top, "muro")

    # Zocalos interiores de piedra
    mb.add_box(x0, x0 + 0.04, y0, y1, Z_SALON_PISO, Z_SALON_PISO + 0.30, "piedra")
    mb.add_box(x0, x1, y0, y0 + 0.04, Z_SALON_PISO, Z_SALON_PISO + 0.30, "piedra")
    mb.add_box(x1 - 0.04, x1, y_cl_n, y1, Z_SALON_PISO, Z_SALON_PISO + 0.30, "piedra")

    # Cubierta exterior de teja (enrasada en X=-11.00 sin entrar al claustro) + cielorraso con vigas oscuras
    mb.add_sloped_box((x_out - 0.15, y_out0 - 0.25, z_top), (xm, y_out0 - 0.25, z_ridge), (xm, y_out1 + 0.25, z_ridge), (x_out - 0.15, y_out1 + 0.25, z_top), 0.18, "teja")
    mb.add_sloped_box((xm, y_out0 - 0.25, z_ridge), (x1, y_out0 - 0.25, z_top), (x1, y_out1 + 0.25, z_top), (xm, y_out1 + 0.25, z_ridge), 0.18, "teja")
    mb.add_box(x0, x1, y0, y1, z_top - 0.12, z_top, "madera")
    for vy in (20.10, 21.80, 23.50, 25.20, 26.90, 28.60, 30.30, 32.00):
        mb.add_box(x0, x1, vy - 0.07, vy + 0.07, z_top - 0.26, z_top - 0.12, "madera")

    # Antesala directa del patio: Pedestal del Aguila tallada mirando hacia el Claustro (+X)
    _add_eagle_pedestal(mb, xm, 20.80, Z_SALON_PISO, face_east=True)

    # Piano antiguo pegado al muro izquierdo (Oeste, Y=25.00..26.80, mirando +X) con 4 patas solidas
    mb.add_box(x0 + 0.06, x0 + 0.72, 25.00, 26.80, Z_SALON_PISO + 0.72, Z_SALON_PISO + 1.08, "madera")
    mb.add_box(x0 + 0.64, x0 + 0.92, 25.02, 26.78, Z_SALON_PISO + 0.70, Z_SALON_PISO + 0.79, "madera")
    u0, v0, u1, v1 = cell_uv("piano_teclas")
    mb.add_quad((x0 + 0.93, 25.08, Z_SALON_PISO + 0.76), (x0 + 0.93, 26.72, Z_SALON_PISO + 0.76),
                (x0 + 0.72, 26.72, Z_SALON_PISO + 0.80), (x0 + 0.72, 25.08, Z_SALON_PISO + 0.80),
                "atlas_museo", (u0, v0, u1, v1))
    mb.add_box(x0 + 0.08, x0 + 0.42, 25.40, 26.40, Z_SALON_PISO + 1.08, Z_SALON_PISO + 1.32, "madera")
    for lx in (x0 + 0.12, x0 + 0.82):
        for ly in (25.08, 26.64):
            mb.add_box(lx, lx + 0.06, ly, ly + 0.06, Z_SALON_PISO, Z_SALON_PISO + 0.72, "madera")
    mb.add_box(x0 + 0.18, x0 + 0.42, 25.75, 26.05, Z_SALON_PISO + 0.04, Z_SALON_PISO + 0.10, "oro_bronce")

    # 2 Vitrinas de bastones presidenciales junto al muro Este (dejan > 4 m de paso central libre)
    v1_x0, v1_x1, v1_y0, v1_y1 = x1 - 0.88, x1 - 0.04, 24.40, 25.55
    mb.add_box(v1_x0, v1_x1, v1_y0, v1_y1, Z_SALON_PISO, Z_SALON_PISO + 0.76, "madera")
    for bk in range(4):
        by_b = v1_y0 + 0.22 + bk * 0.23
        mb.add_cylinder(x1 - 0.46, by_b, Z_SALON_PISO + 0.82, Z_SALON_PISO + 1.50, 0.016, 0.013, 6, "madera")
        mb.add_cylinder(x1 - 0.46, by_b, Z_SALON_PISO + 1.50, Z_SALON_PISO + 1.57, 0.022, 0.018, 6, "oro_bronce")
    add_vitrine_glass_box(mb, v1_x0 + 0.03, v1_x1 - 0.03, v1_y0 + 0.03, v1_y1 - 0.03, Z_SALON_PISO + 0.76, Z_SALON_PISO + 1.66)

    v2_x0, v2_x1, v2_y0, v2_y1 = x1 - 0.88, x1 - 0.04, 27.95, 29.20
    mb.add_box(v2_x0, v2_x1, v2_y0, v2_y1, Z_SALON_PISO, Z_SALON_PISO + 0.78, "madera")
    mb.add_box(v2_x0 + 0.08, v2_x1 - 0.08, v2_y0 + 0.08, v2_y1 - 0.08, Z_SALON_PISO + 0.78, Z_SALON_PISO + 0.82, "atlas_museo", "rojo")
    mb.add_beam((x1 - 0.46, v2_y0 + 0.22, Z_SALON_PISO + 0.86), (x1 - 0.46, v2_y1 - 0.22, Z_SALON_PISO + 0.86), 0.018, 6, "madera")
    mb.add_beam((x1 - 0.46, v2_y1 - 0.22, Z_SALON_PISO + 0.86), (x1 - 0.46, v2_y1 - 0.14, Z_SALON_PISO + 0.86), 0.024, 6, "oro_bronce")
    add_vitrine_glass_box(mb, v2_x0 + 0.03, v2_x1 - 0.03, v2_y0 + 0.03, v2_y1 - 0.03, Z_SALON_PISO + 0.82, Z_SALON_PISO + 1.18)

    # 10 Retratos presidenciales enmarcados + placa dorada (sin solaparse con puerta Oeste, piano ni tarima)
    west_portraits = (
        (20.40, "bolivar"),
        (22.10, "sucre"),
        (23.80, "santacruz"),
        (27.90, "cuadro_pasillo"),
        (29.55, "ret_sup_izq"),
    )
    east_portraits = (
        (23.20, "ret_sup_der"),
        (24.85, "ballivian"),
        (26.45, "bolivar"),
        (28.05, "sucre"),
        (29.55, "santacruz"),
    )
    for py_p, ckey in west_portraits:
        add_beveled_frame_painting(mb, x0, py_p, 2.58, 1.00, 1.32, "+X", ckey, frame_w=0.055, depth=0.05)
        mb.add_box(x0, x0 + 0.03, py_p - 0.15, py_p + 0.15, 1.70, 1.79, "oro_bronce")
    for py_p, ckey in east_portraits:
        add_beveled_frame_painting(mb, x1, py_p, 2.58, 1.00, 1.32, "-X", ckey, frame_w=0.055, depth=0.05)
        mb.add_box(x1 - 0.03, x1, py_p - 0.15, py_p + 0.15, 1.70, 1.79, "oro_bronce")

    # Tarima escalonada de ladrillo con bordes blancos al fondo Norte (cuarto2.jpg / 28m13s)
    mb.add_box(x0, x1, 30.40, y1, Z_SALON_PISO, Z_SALON_PISO + 0.18, "piso")
    mb.add_box(x0, x1, 30.36, 30.44, Z_SALON_PISO, Z_SALON_PISO + 0.19, "muro")
    mb.add_box(x0, x1, 31.20, y1, Z_SALON_PISO + 0.18, Z_SALON_PISO + 0.36, "piso")
    mb.add_box(x0, x1, 31.16, 31.24, Z_SALON_PISO + 0.18, Z_SALON_PISO + 0.37, "muro")
    z_dais = Z_SALON_PISO + 0.36

    # Puerta doble verde con molduras en X al fondo derecha (Y=33.12..33.20)
    mb.add_box(x1 - 1.45, x1 - 0.18, y1 - 0.08, y1, z_dais, z_dais + 2.55, "atlas_museo", "verde_bar")
    mb.add_box(x1 - 1.49, x1 - 0.14, y1 - 0.10, y1 - 0.06, z_dais + 2.52, z_dais + 2.60, "madera")
    mb.add_box(x1 - 1.49, x1 - 1.43, y1 - 0.10, y1 - 0.06, z_dais, z_dais + 2.54, "madera")
    mb.add_box(x1 - 0.20, x1 - 0.14, y1 - 0.10, y1 - 0.06, z_dais, z_dais + 2.54, "madera")
    mb.add_box(x1 - 0.84, x1 - 0.79, y1 - 0.10, y1 - 0.06, z_dais, z_dais + 2.54, "madera")
    mb.add_box(x1 - 1.44, x1 - 0.19, y1 - 0.10, y1 - 0.06, z_dais + 1.12, z_dais + 1.18, "madera")
    # Manijas de bronce
    mb.add_box(x1 - 0.90, x1 - 0.86, y1 - 0.12, y1 - 0.08, z_dais + 1.00, z_dais + 1.10, "oro_bronce")
    mb.add_box(x1 - 0.77, x1 - 0.73, y1 - 0.12, y1 - 0.08, z_dais + 1.00, z_dais + 1.10, "oro_bronce")

    # Escudo Nacional de Bolivia en medallon limpio sobre el busto de Bolivar
    mb.add_disc_y(xm, y1 - 0.02, 3.92, 0.48, 0.025, 16, "atlas_museo", "escudo_bolivia", facing_neg_y=True, rim_mat="muro")

    # 4 Banderas historicas diferenciadas flanqueando el busto monumental (sin invadir la puerta verde)
    for bx, ckey in ((xm - 1.90, "wiphala"), (xm - 1.22, "bandera"), (xm + 0.90, "bandera_belgrano"), (xm + 1.48, "rojo")):
        mb.add_cylinder(bx, 32.00, z_dais, z_dais + 2.65, 0.025, 0.020, 6, "oro_bronce")
        u0, v0, u1, v1 = cell_uv(ckey)
        mb.add_quad((bx - 0.30, 31.98, z_dais + 0.90), (bx + 0.30, 31.98, z_dais + 0.90),
                    (bx + 0.30, 31.98, z_dais + 2.40), (bx - 0.30, 31.98, z_dais + 2.40),
                    "atlas_museo", (u0, v0, u1, v1))

    mb.to_object(col, "CL_Sala_Bolivar")

    bust_mesh = _build_bolivar_bust_mesh()
    b_obj = bpy.data.objects.new("CL_Busto_Bolivar", bust_mesh)
    b_obj.location = (xm, 31.90, z_dais)
    col.objects.link(b_obj)

    spawn_instance(col, "CL_Arana_Sala_Bolivar", kit["arana_cristal"], (xm, 26.80, z_top - 1.25), 0.0)


# ---------------------------------------------------------------------------
# 5. MARCADORES POI_* Y LUZ_* + COLISIONES (-colonly) + EXPORTADOR GLB
# ---------------------------------------------------------------------------

def build_markers(col):
    add_empty(col, "POI_ENTRADA_PORTON", (0.0, 0.35, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_PATIO_FUENTE", (0.0, 14.80, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_ESTATUA", (3.05, 13.90, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_PORTADA_SALON", (0.0, 27.6, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_ACTA_INDEPENDENCIA", (0.0, 45.8, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_PRESIDIO_BOLIVAR", (0.0, 48.2, 1.85), "SPHERE", 0.40)
    add_empty(col, "POI_BANDERA_BELGRANO", (9.80, 33.40, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_CANON", (8.50, 41.20, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_SALA_MUSEO", (8.50, 45.80, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_PASILLO_AGUILA", (-12.80, 20.80, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_SALA_BOLIVAR", (-14.10, 29.20, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_SALA_VIRREINAL", (-10.20, 13.60, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_SALA_HONOR", (10.20, 13.60, 1.65), "SPHERE", 0.40)
    add_empty(col, "POI_BIBLIOTECA", (-8.20, 27.40, 1.65), "SPHERE", 0.40)

    luces = [
        ("LUZ_ZAGUAN_01", (0.0, 3.20, 3.65)),
        ("LUZ_SALON_ARANA_01", (0.0, 38.20, 5.20)),
        ("LUZ_SALON_ARANA_02", (0.0, 45.60, 5.20)),
        ("LUZ_SALA_GUERRILLEROS", (8.50, 40.20, 3.85)),
        ("LUZ_SALA_BOLIVAR", (-14.10, 26.80, 4.20)),
    ]
    for name, loc in luces:
        add_empty(col, name, loc, "SINGLE_ARROW", 0.45)


class _ColliderBoxes:
    """Constructor minimalista de cajas -colonly (sin materiales, normales salientes)."""

    def __init__(self, name: str):
        self.name = name
        self.verts: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, int, int, int]] = []

    def add_box(self, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float):
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        if z1 < z0:
            z0, z1 = z1, z0
        idx = len(self.verts)
        self.verts.extend([
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
        ])
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.faces.append(tuple(idx + k for k in f))

    def to_object(self, col) -> bpy.types.Object:
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.verts, [], self.faces)
        me.update()
        obj = bpy.data.objects.new(self.name, me)
        obj.display_type = "WIRE"
        obj.hide_render = True
        col.objects.link(obj)
        return obj


def build_collisions(col) -> list[bpy.types.Object]:
    """Colisiones simplificadas -colonly manteniendo todos los pasos libres (>= 2.2 x 2.8 m)."""
    cb_pisos = _ColliderBoxes("CL_Col_Pisos-colonly")
    # Acera, Zaguan, Patio, Galerias, Salon, Presidio, Guerrilleros (Este) y Senado/Bolivar (Oeste + tarimas)
    cb_pisos.add_box(-13.0, 13.0, -4.50, 0.0, -0.18, Z_ACERA)
    cb_pisos.add_box(-1.60, 1.60, 0.0, 6.20, 0.0, Z_ZAGUAN)
    cb_pisos.add_box(-7.20, 7.20, 10.00, 24.40, 0.0, Z_PATIO)
    cb_pisos.add_box(-11.00, 11.00, 6.20, 10.00, 0.0, Z_GALERIA)
    cb_pisos.add_box(-11.00, 11.00, 24.40, 28.20, 0.0, Z_GALERIA)
    cb_pisos.add_box(-11.00, -7.20, 10.00, 24.40, 0.0, Z_GALERIA)
    cb_pisos.add_box(7.20, 11.00, 10.00, 24.40, 0.0, Z_GALERIA)
    cb_pisos.add_box(-4.60, 4.60, 28.20, 52.80, 0.0, Z_SALON_PISO)
    cb_pisos.add_box(-4.60, 4.60, 47.95, 48.40, Z_SALON_PISO, Z_SALON_PISO + 0.22)
    cb_pisos.add_box(-4.60, 4.60, 48.40, 52.80, Z_SALON_PISO, Z_PRESIDIO)
    cb_pisos.add_box(4.60, 11.60, 28.20, 47.80, 0.0, Z_SALON_PISO)
    cb_pisos.add_box(-17.20, -10.40, 18.80, 33.20, 0.0, Z_SALON_PISO)
    cb_pisos.add_box(-17.20, -11.00, 30.40, 33.20, Z_SALON_PISO, Z_SALON_PISO + 0.18)
    cb_pisos.add_box(-17.20, -11.00, 31.20, 33.20, Z_SALON_PISO + 0.18, Z_SALON_PISO + 0.36)

    cb_muros = _ColliderBoxes("CL_Col_Muros-colonly")
    pw = PORTON_ANCHO * 0.5
    hz_zag = ZAGUAN_ANCHO * 0.5
    # Fachada y zaguan (porton 2.8x3.8m libre)
    cb_muros.add_box(-11.0, -pw, 0.0, 0.80, 0.0, FACHADA_ALTO)
    cb_muros.add_box(pw, 11.0, 0.0, 0.80, 0.0, FACHADA_ALTO)
    cb_muros.add_box(-11.0, -hz_zag, 0.80, 6.20, 0.0, FACHADA_ALTO)
    cb_muros.add_box(hz_zag, 11.0, 0.80, 6.20, 0.0, FACHADA_ALTO)
    # Claustro muros (Oeste abierto en Y=19.6..22.0, Norte-Este abierto en X=7.1..9.5) y columnas
    cb_muros.add_box(-11.0, -10.4, 6.20, SALA_LAT_PUERTA_Y0, 0.0, GALERIA_ALTO_CUMBRERA)
    cb_muros.add_box(-11.0, -10.4, SALA_LAT_PUERTA_Y1, 28.20, 0.0, GALERIA_ALTO_CUMBRERA)
    cb_muros.add_box(10.4, 11.0, 6.20, 28.20, 0.0, GALERIA_ALTO_CUMBRERA)
    cb_muros.add_box(-11.0, -5.4, 27.60, 28.20, 0.0, GALERIA_ALTO_CUMBRERA)
    cb_muros.add_box(5.4, 7.10, 27.60, 28.20, 0.0, GALERIA_ALTO_CUMBRERA)
    cb_muros.add_box(9.50, 11.0, 27.60, 28.20, 0.0, GALERIA_ALTO_CUMBRERA)
    for yw in (10.0, 24.4):
        cb_muros.add_box(-7.2, -1.45, yw - 0.16, yw + 0.16, Z_PATIO, Z_GALERIA + 0.22)
        cb_muros.add_box(1.45, 7.2, yw - 0.16, yw + 0.16, Z_PATIO, Z_GALERIA + 0.22)
    cb_muros.add_box(-7.36, -7.04, 10.0, 24.4, Z_PATIO, Z_GALERIA + 0.22)
    cb_muros.add_box(7.04, 7.36, 10.0, 24.4, Z_PATIO, Z_GALERIA + 0.22)
    bay = PATIO_ANCHO / NUM_ARCOS_LADO
    col_coords = set()
    for i in range(NUM_ARCOS_LADO + 1):
        xv = round(-7.20 + i * bay, 3)
        yv = round(10.00 + i * bay, 3)
        col_coords.update({(xv, 10.0), (xv, 24.4), (-7.20, yv), (7.20, yv)})
    for cx_p, cy_p in sorted(col_coords):
        cb_muros.add_box(cx_p - 0.30, cx_p + 0.30, cy_p - 0.30, cy_p + 0.30, Z_GALERIA, Z_GALERIA + 3.0)
    # Salon muros (porton 2.6x3.6 y puerta verde 2.4x3.05 libres)
    cb_muros.add_box(-5.40, -1.30, 28.20, 28.80, 0.0, SALON_ALTO_MURO)
    cb_muros.add_box(1.30, 5.40, 28.20, 28.80, 0.0, SALON_ALTO_MURO)
    cb_muros.add_box(-5.40, -4.60, 28.80, 52.80, 0.0, SALON_ALTO_MURO)
    cb_muros.add_box(4.60, 5.40, 28.80, 43.80, 0.0, SALON_ALTO_MURO)
    cb_muros.add_box(4.60, 5.40, 46.20, 52.80, 0.0, SALON_ALTO_MURO)
    cb_muros.add_box(-5.40, 5.40, 52.80, 53.60, 0.0, SALON_ALTO_MURO)
    # Sala de Guerrilleros cerrada (Este) y Galeria Presidentes / Bolivar (Oeste)
    cb_muros.add_box(11.00, 12.10, 27.60, 28.20, 0.0, 4.80)
    cb_muros.add_box(11.60, 12.10, 28.20, 47.80, 0.0, 4.80)
    cb_muros.add_box(5.40, 12.10, 47.80, 48.30, 0.0, 4.80)
    cb_muros.add_box(-17.65, -17.20, 18.35, 33.65, 0.0, 5.40)
    cb_muros.add_box(-17.20, -11.00, 18.35, 18.80, 0.0, 5.40)
    cb_muros.add_box(-17.20, -10.55, 33.20, 33.65, 0.0, 5.40)
    cb_muros.add_box(-11.00, -10.55, 28.20, 33.20, 0.0, 5.40)

    cb_props = _ColliderBoxes("CL_Col_Mobiliario-colonly")
    # Fuente, Flechero, Silleria Salon, Acta, Presidio, Piano Salon
    cb_props.add_box(-1.78, 1.78, 15.42, 18.98, Z_PATIO, 2.75)
    cb_props.add_box(3.65, 5.45, 13.00, 14.80, Z_PATIO, 3.20)
    cb_props.add_box(-4.60, -2.35, 33.20, 47.40, Z_SALON_PISO, Z_SALON_PISO + 1.80)
    cb_props.add_box(2.35, 4.60, 33.20, 44.00, Z_SALON_PISO, Z_SALON_PISO + 1.80)
    cb_props.add_box(-0.56, 0.56, 46.44, 47.56, Z_SALON_PISO, Z_SALON_PISO + 1.75)
    cb_props.add_box(-1.60, 1.60, 49.25, 50.30, Z_PRESIDIO, Z_PRESIDIO + 1.45)
    cb_props.add_box(-4.35, -3.28, 47.00, 48.70, Z_SALON_PISO, Z_SALON_PISO + 1.30)
    # Sala Guerrilleros (Este): canon, cofre Juana, templete Belgrano, consola Oeste
    cb_props.add_box(7.68, 9.32, 41.94, 42.86, Z_SALON_PISO, Z_SALON_PISO + 1.25)
    cb_props.add_box(7.78, 9.22, 46.40, 47.70, Z_SALON_PISO, Z_SALON_PISO + 1.25)
    cb_props.add_box(11.06, 11.60, 32.44, 34.36, Z_SALON_PISO, Z_SALON_PISO + 1.25)
    cb_props.add_box(5.44, 5.96, 40.30, 41.60, Z_SALON_PISO, Z_SALON_PISO + 1.05)
    # Galeria Presidentes / Bolivar (Oeste): pedestal Aguila, piano, 2 vitrinas bastones, busto Bolivar
    cb_props.add_box(-14.60, -13.60, 20.38, 21.22, Z_SALON_PISO, Z_SALON_PISO + 1.35)
    cb_props.add_box(-17.16, -16.24, 25.00, 26.80, Z_SALON_PISO, Z_SALON_PISO + 1.32)
    cb_props.add_box(-11.90, -11.00, 24.40, 25.55, Z_SALON_PISO, Z_SALON_PISO + 1.66)
    cb_props.add_box(-11.90, -11.00, 27.95, 29.20, Z_SALON_PISO, Z_SALON_PISO + 1.18)
    cb_props.add_box(-14.70, -13.50, 31.32, 32.42, Z_SALON_PISO + 0.36, 3.40)

    return [cb_pisos.to_object(col), cb_muros.to_object(col), cb_props.to_object(col)]


def export_glb(out_path: str) -> int:
    """Exporta CasaLibertad_1809 (sin camaras/luces de revision) a glTF 2.0 binario Y-Up."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    root_col = bpy.data.collections.get(ROOT_COLLECTION_NAME)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in root_col.all_objects:
        # Excluir la coleccion de camaras y luces de preview (solo exportar POI_*, LUZ_*, mallas y -colonly)
        if obj.name.startswith(("CAM_", "CL_Sol_", "CL_Luz_")):
            continue
        obj.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_extras=False,
        export_cameras=False,
        export_lights=False,
    )
    bpy.ops.object.select_all(action="DESELECT")
    return os.path.getsize(out_path)


def setup_preview_lighting_and_cameras(col_cam):
    sc = bpy.context.scene

    sun_data = bpy.data.lights.new("CL_Sol_Revision", type="SUN")
    sun_data.energy = 3.1
    sun_data.angle = math.radians(3.5)
    sun_obj = bpy.data.objects.new("CL_Sol_Revision", sun_data)
    sun_obj.rotation_euler = (math.radians(48), math.radians(12), math.radians(-32))
    col_cam.objects.link(sun_obj)

    for idx, (lx, ly, lz, en) in enumerate((
        (0.0, 3.20, 3.40, 220.0),
        (0.0, 38.20, 4.90, 680.0),
        (0.0, 45.60, 4.90, 680.0),
        (8.50, 40.20, 3.65, 620.0),
        (-14.10, 26.80, 3.85, 760.0),
    )):
        pt_data = bpy.data.lights.new(f"CL_Luz_Int_{idx+1}", type="POINT")
        pt_data.energy = en
        pt_data.color = (1.0, 0.88, 0.68)
        pt_data.shadow_soft_size = 0.45
        pt_obj = bpy.data.objects.new(f"CL_Luz_Int_{idx+1}", pt_data)
        pt_obj.location = (lx, ly, lz)
        col_cam.objects.link(pt_obj)

    world = sc.world or bpy.data.worlds.new("CL_World")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.56, 0.74, 0.92, 1.0)
        bg.inputs["Strength"].default_value = 0.85

    eevee = getattr(sc, "eevee", None)
    if eevee:
        for attr, val in (
            ("use_gtao", True),
            ("gtao_distance", 1.2),
            ("gtao_factor", 1.0),
            ("use_raytracing", True),
            ("use_fast_gi", True),
        ):
            if hasattr(eevee, attr):
                try:
                    setattr(eevee, attr, val)
                except Exception:
                    pass

    cams = [
        ("CAM_Entrada_Salon", (0.0, 19.8, 1.75), (0.0, 31.0, 2.20), 22),
        ("CAM_Guerrilleros_Canon", (10.6, 38.4, 1.85), (6.0, 45.8, 1.80), 20),
        ("CAM_Pasillo_Aguila", (-9.4, 20.8, 1.85), (-15.0, 21.2, 1.85), 21),
        ("CAM_Sala_Bolivar", (-14.1, 21.6, 1.85), (-14.1, 32.8, 2.35), 20),
    ]
    created = []
    for name, pos, target, lens in cams:
        cam_data = bpy.data.cameras.new(name)
        cam_data.lens = lens
        cam_data.clip_end = 500.0
        cam_obj = bpy.data.objects.new(name, cam_data)
        cam_obj.location = Vector(pos)
        direction = Vector(target) - Vector(pos)
        cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        col_cam.objects.link(cam_obj)
        created.append(cam_obj)
    return created


def render_views(cams, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x = 1280
    sc.render.resolution_y = 720
    sc.render.image_settings.file_format = "PNG"

    rendered = []
    for cam in cams:
        sc.camera = cam
        out_path = os.path.join(out_dir, f"fase27_{cam.name.replace('CAM_', '').lower()}.png")
        sc.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        rendered.append(out_path)
    return rendered


# ---------------------------------------------------------------------------
# ORQUESTACION PRINCIPAL
# ---------------------------------------------------------------------------

def build_all(render_previews: bool = False, do_export: bool = False):
    reset_scene_clean()
    root_col = get_collection(ROOT_COLLECTION_NAME)
    col_fachada = get_collection("01_Fachada_Zaguan", root_col)
    col_claustro = get_collection("02_Claustro_Patio", root_col)
    col_salon = get_collection("03_Salon_Independencia", root_col)
    col_sala_lat = get_collection("04_Sala_Guerrilleros", root_col)
    col_bolivar = get_collection("04b_Galeria_Presidentes_Bolivar", root_col)
    col_marcadores = get_collection("05_Marcadores_POI_LUZ", root_col)
    col_cam = get_collection("06_Camaras_Revision", root_col)
    col_col = get_collection("07_Colisiones", root_col)

    kit = build_modular_kit()
    build_fachada_y_zaguan(col_fachada, kit)
    build_claustro(col_claustro, kit)
    build_salon_independencia(col_salon, kit)
    build_sala_lateral_museo(col_sala_lat, kit)
    build_sala_bolivar(col_bolivar, kit)
    build_markers(col_marcadores)
    build_collisions(col_col)
    cams = setup_preview_lighting_and_cameras(col_cam)

    deps = bpy.context.evaluated_depsgraph_get()
    vis_tris = sum(
        len(o.evaluated_get(deps).data.loop_triangles)
        for o in root_col.all_objects
        if o.type == "MESH" and not o.name.endswith("-colonly")
    )
    col_tris = sum(
        len(o.evaluated_get(deps).data.loop_triangles)
        for o in root_col.all_objects
        if o.type == "MESH" and o.name.endswith("-colonly")
    )
    bust_obj = bpy.data.objects.get("CL_Busto_Bolivar")
    bust_tris = len(bust_obj.evaluated_get(deps).data.loop_triangles) if bust_obj else 0
    stat_obj = bpy.data.objects.get("CL_Estatua_Flechero")
    stat_tris = len(stat_obj.evaluated_get(deps).data.loop_triangles) if stat_obj else 0
    mats = len(bpy.data.materials)
    unique_meshes = len({o.data for o in root_col.all_objects if o.type == "MESH"})
    has_trans = any(
        n.type == "BSDF_PRINCIPLED" and "Transmission Weight" in n.inputs and n.inputs["Transmission Weight"].default_value > 0.0
        for m in bpy.data.materials if m.use_nodes and m.node_tree
        for n in m.node_tree.nodes
    )
    max_scale_err = 0.0
    for o in root_col.all_objects:
        if not o.name.startswith(("CAM_", "CL_Sol_", "CL_Luz_")):
            err = max(abs(s - 1.0) for s in o.scale)
            if err > max_scale_err:
                max_scale_err = err
            if err > 1e-4:
                raise RuntimeError(f"Escala != 1 en objeto exportable {o.name}: {tuple(o.scale)}")
    print(
        f"[CasaLibertad_1809] Fase 3 listo: {len(root_col.all_objects)} objetos ({unique_meshes} mallas), "
        f"{vis_tris} tris visibles + {col_tris} tris -colonly = {vis_tris + col_tris} tris totales "
        f"(Flechero: {stat_tris}, Bolivar: {bust_tris}), {mats} materiales (Transmission={has_trans}, scale_err={max_scale_err:.4f})."
    )

    if not bpy.app.background and bpy.context.screen:
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"
                        space.clip_end = 500.0

    if render_previews:
        out_dir = os.path.join(BASE_DIR, "renders")
        for p in render_views(cams, out_dir):
            print(f"[CasaLibertad_1809] Render guardado: {p}")

    if do_export:
        glb_path = os.path.join(BASE_DIR, "exports", "casa_libertad.glb")
        sz = export_glb(glb_path)
        print(f"[CasaLibertad_1809] GLB exportado: {glb_path} ({sz / (1024.0 * 1024.0):.2f} MB)")


if __name__ == "__main__":
    do_render = "--render" in sys.argv
    do_export = "--export" in sys.argv
    build_all(render_previews=do_render, do_export=do_export)
