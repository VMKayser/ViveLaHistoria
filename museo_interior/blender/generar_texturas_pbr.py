"""Genera texturas PBR 512x512 seamless (Albedo, Normal OpenGL y Roughness)
reutilizando los mapas CC0 de Poly Haven ya incluidos en web/public/texturas/.

Salida en museo_interior/texturas/pbr/:
  - <material>_albedo.jpg     (512x512 sRGB)
  - <material>_normal.jpg     (512x512 Non-Color, OpenGL +Y arriba, subsampling 4:4:4)
  - <material>_roughness.jpg  (512x512 Non-Color escala de grises)

Uso:
    python museo_interior/blender/generar_texturas_pbr.py
"""

import os
import numpy as np
from PIL import Image, ImageFile

ImageFile.MAXBLOCK = 2**20

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(HERE, ".."))
REPO_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
SRC_DIR = os.path.join(REPO_DIR, "web", "public", "texturas")
OUT_DIR = os.path.join(BASE_DIR, "texturas", "pbr")

TILE = 512


def load_tile(filename: str, col: int, row: int, cols: int, rows: int) -> np.ndarray:
    """Extrae una baldosa 512x512 normalizada [0, 1] desde un atlas detalle_*.jpg."""
    path = os.path.join(SRC_DIR, filename)
    im = Image.open(path).convert("L")
    w, h = im.size
    cw, ch = w // cols, h // rows
    crop = im.crop((col * cw, row * ch, (col + 1) * cw, (row + 1) * ch))
    if crop.size != (TILE, TILE):
        crop = crop.resize((TILE, TILE), Image.Resampling.BICUBIC)
    arr = np.asarray(crop, dtype=np.float32) / 255.0
    return arr


def load_water_tile() -> np.ndarray:
    path = os.path.join(SRC_DIR, "relieve_acuarela_agua.jpg")
    im = Image.open(path).convert("L").resize((TILE, TILE), Image.Resampling.BICUBIC)
    return np.asarray(im, dtype=np.float32) / 255.0


def height_to_normal_gl(h: np.ndarray, strength: float) -> np.ndarray:
    """Convierte mapa de altura seamless [0..1] a Normal Map OpenGL (+Y arriba) RGB uint8."""
    # Sobel 3x3 con wrap periodico para evitar cualquier costura en mosaico UV
    tl = np.roll(np.roll(h, 1, axis=0), 1, axis=1)
    tc = np.roll(h, 1, axis=0)
    tr = np.roll(np.roll(h, 1, axis=0), -1, axis=1)
    ml = np.roll(h, 1, axis=1)
    mr = np.roll(h, -1, axis=1)
    bl = np.roll(np.roll(h, -1, axis=0), 1, axis=1)
    bc = np.roll(h, -1, axis=0)
    br = np.roll(np.roll(h, -1, axis=0), -1, axis=1)

    dx = ((tr + 2.0 * mr + br) - (tl + 2.0 * ml + bl)) * 0.25
    dy_img = ((bl + 2.0 * bc + br) - (tl + 2.0 * tc + tr)) * 0.25

    nx = -dx * strength
    ny = dy_img * strength  # +Y arriba en coordenadas UV (v inverso a y_img)
    nz = np.ones_like(h)

    inv_len = 1.0 / np.sqrt(nx * nx + ny * ny + nz * nz + 1e-8)
    nx *= inv_len
    ny *= inv_len
    nz *= inv_len

    rgb = np.stack([(nx * 0.5 + 0.5), (ny * 0.5 + 0.5), (nz * 0.5 + 0.5)], axis=-1)
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)


def lerp_color(t: np.ndarray, col_low: tuple[float, float, float], col_high: tuple[float, float, float]) -> np.ndarray:
    """Interpola linealmente entre dos colores sRGB [0..1] segun mapa t [0..1]."""
    t3 = np.clip(t, 0.0, 1.0)[..., None]
    lo = np.array(col_low, dtype=np.float32)[None, None, :]
    hi = np.array(col_high, dtype=np.float32)[None, None, :]
    rgb = lo * (1.0 - t3) + hi * t3
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)


def save_pbr_set(name: str, albedo_u8: np.ndarray, normal_u8: np.ndarray, rough_f: np.ndarray):
    a_path = os.path.join(OUT_DIR, f"{name}_albedo.jpg")
    n_path = os.path.join(OUT_DIR, f"{name}_normal.jpg")
    r_path = os.path.join(OUT_DIR, f"{name}_roughness.jpg")

    Image.fromarray(albedo_u8, mode="RGB").save(a_path, "JPEG", quality=82, optimize=True)
    Image.fromarray(normal_u8, mode="RGB").save(n_path, "JPEG", quality=82, subsampling=0, optimize=True)
    r_u8 = np.clip(rough_f * 255.0, 0, 255).astype(np.uint8)
    Image.fromarray(r_u8, mode="L").save(r_path, "JPEG", quality=76, optimize=True)


def normalize_contrast(h: np.ndarray, lo_p: float = 2.0, hi_p: float = 98.0) -> np.ndarray:
    lo = float(np.percentile(h, lo_p))
    hi = float(np.percentile(h, hi_p))
    if hi - lo < 1e-4:
        return np.full_like(h, 0.5)
    return np.clip((h - lo) / (hi - lo), 0.0, 1.0)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    plaster = load_tile("detalle_muro.jpg", 1, 0, 4, 2)             # plastered_wall_02
    plaster_fine = load_tile("detalle_muro.jpg", 0, 0, 4, 2)        # plastered_wall
    sandstone = load_tile("detalle_zocalo_piedra.jpg", 0, 0, 4, 2)  # large_sandstone_blocks
    wood = load_tile("detalle_madera.jpg", 0, 0, 2, 1)              # weathered_brown_planks
    roof_tile = load_tile("detalle_teja.jpg", 0, 0, 2, 1)           # clay_roof_tiles_02
    cobble = load_tile("detalle_adoquin.jpg", 0, 0, 1, 1)           # square_cobblestone
    iron = load_tile("detalle_hierro.jpg", 1, 0, 3, 1)              # rusty_metal_02
    metal_plate = load_tile("detalle_hierro.jpg", 2, 0, 3, 1)       # metal_plate

    # 1. MURO: cal historica blanca limpia de Sucre ("Ciudad Blanca") para contrastar con piedra oscura
    h_muro = normalize_contrast(plaster_fine, 2, 98)
    albedo_muro = lerp_color(h_muro, (0.910, 0.892, 0.865), (0.985, 0.976, 0.960))
    normal_muro = height_to_normal_gl(h_muro, strength=1.8)
    rough_muro = 0.94 - 0.10 * h_muro  # cal mate artesanal
    save_pbr_set("muro", albedo_muro, normal_muro, rough_muro)

    # 2. PIEDRA: arenisca ocre-beige fina y lisa (como columnas del claustro real, sin ladrillo tosco)
    h_piedra = 0.78 * normalize_contrast(plaster_fine, 2, 98) + 0.22 * normalize_contrast(sandstone, 2, 98)
    albedo_piedra = lerp_color(h_piedra, (0.745, 0.595, 0.435), (0.895, 0.765, 0.605))
    normal_piedra = height_to_normal_gl(h_piedra, strength=1.8)
    rough_piedra = 0.86 - 0.12 * h_piedra
    save_pbr_set("piedra", albedo_piedra, normal_piedra, rough_piedra)

    # 2b. PIEDRA_FACHADA: arenisca marron-ocre oscura envejecida (#7A5C3E-#92714E) con sillares y patina exterior
    s_blk = normalize_contrast(sandstone, 1.5, 98.5)
    s_fine = normalize_contrast(plaster_fine, 3.0, 97.0)
    h_pf = np.clip(0.82 * s_blk + 0.18 * s_fine, 0.0, 1.0)
    junta_pf = np.clip((0.27 - s_blk) * 3.2, 0.0, 1.0)
    patina_pf = np.clip((0.45 - s_fine) * 1.4, 0.0, 1.0)
    albedo_pf = lerp_color(h_pf, (0.395, 0.285, 0.185), (0.595, 0.460, 0.312))
    albedo_pf = (albedo_pf.astype(np.float32) * (1.0 - 0.26 * junta_pf[..., None] - 0.12 * patina_pf[..., None])).clip(0, 255).astype(np.uint8)
    normal_pf = height_to_normal_gl(h_pf, strength=3.6)
    rough_pf = np.round((0.88 - 0.14 * h_pf + 0.06 * junta_pf) * 10.0) / 10.0
    Image.fromarray(albedo_pf, mode="RGB").save(os.path.join(OUT_DIR, "piedra_fachada_albedo.jpg"), "JPEG", quality=78, optimize=True)
    Image.fromarray(normal_pf, mode="RGB").save(os.path.join(OUT_DIR, "piedra_fachada_normal.jpg"), "JPEG", quality=78, optimize=True)
    Image.fromarray(np.clip(rough_pf * 255.0, 0, 255).astype(np.uint8), mode="L").save(os.path.join(OUT_DIR, "piedra_fachada_roughness.jpg"), "JPEG", quality=72, optimize=True)

    # 3. MADERA: cedro nativo colonial (#4a2b19) con veta y tablones nitidos
    h_madera = normalize_contrast(wood, 1.5, 98.5)
    albedo_madera = lerp_color(h_madera, (0.145, 0.078, 0.045), (0.375, 0.222, 0.130))
    normal_madera = height_to_normal_gl(h_madera, strength=4.2)
    rough_madera = 0.84 - 0.24 * h_madera  # veta pulida satinada vs grietas mates
    save_pbr_set("madera", albedo_madera, normal_madera, rough_madera)

    # 4. TEJA: teja colonial de barro cocido (#b95d37) con variación de coccion y sombra entre canales
    h_teja = normalize_contrast(roof_tile, 1, 99)
    t_warm = np.clip(0.65 * h_teja + 0.35 * plaster_fine, 0.0, 1.0)
    albedo_teja = lerp_color(t_warm, (0.435, 0.195, 0.112), (0.855, 0.455, 0.258))
    normal_teja = height_to_normal_gl(h_teja, strength=5.6)
    rough_teja = 0.90 - 0.16 * h_teja
    save_pbr_set("teja", albedo_teja, normal_teja, rough_teja)

    # 5. PISO: empedrado/ladrillo colonial (#90523b) con desgaste peatonal
    h_piso = normalize_contrast(cobble, 1, 99)
    mortar = np.clip((0.35 - h_piso) * 2.8, 0.0, 1.0)
    albedo_piso = lerp_color(h_piso, (0.340, 0.205, 0.155), (0.690, 0.415, 0.285))
    albedo_piso = (albedo_piso.astype(np.float32) * (1.0 - 0.18 * mortar[..., None])).astype(np.uint8)
    normal_piso = height_to_normal_gl(h_piso, strength=4.8)
    rough_piso = 0.62 + 0.28 * mortar
    save_pbr_set("piso", albedo_piso, normal_piso, rough_piso)

    # 6. HIERRO: hierro forjado y bronce oscuro patinado (Flechero, canon, busto de Bolivar)
    h_hierro = 0.55 * normalize_contrast(iron, 2, 98) + 0.45 * normalize_contrast(plaster_fine, 2, 98)
    albedo_hierro = lerp_color(h_hierro, (0.145, 0.125, 0.105), (0.285, 0.240, 0.195))
    normal_hierro = height_to_normal_gl(h_hierro, strength=1.8)
    rough_hierro = 0.52 - 0.14 * h_hierro
    save_pbr_set("hierro", albedo_hierro, normal_hierro, rough_hierro)

    # 7. ORO_BRONCE: bronce patinado y pan de oro fundido artesanal (sin patron diamante industrial)
    h_oro = 0.55 * normalize_contrast(plaster_fine, 2, 98) + 0.45 * normalize_contrast(iron, 2, 98)
    albedo_oro = lerp_color(h_oro, (0.280, 0.210, 0.110), (0.790, 0.595, 0.245))
    normal_oro = height_to_normal_gl(h_oro, strength=1.25)
    rough_oro = 0.50 - 0.18 * h_oro
    save_pbr_set("oro_bronce", albedo_oro, normal_oro, rough_oro)

    files = sorted(os.listdir(OUT_DIR))
    total_kb = sum(os.path.getsize(os.path.join(OUT_DIR, f)) for f in files) / 1024.0
    print(f"Generadas {len(files)} texturas PBR 512x512 en {OUT_DIR} ({total_kb:.1f} KB total):")
    for f in files:
        sz = os.path.getsize(os.path.join(OUT_DIR, f)) / 1024.0
        print(f"  - {f}: {sz:.1f} KB")


if __name__ == "__main__":
    main()
