"""Genera el Texture Atlas 1024x1024 (Base Color + Emissive) para Casa de la Libertad.

Fase 2.5: Consolida todos los retratos, escudo USFX, cuadros de la Sala de los Guerrilleros,
vitral, piano, ataúd, follaje de macetas y acabados en 1 solo material PBR ('atlas_museo').
"""

import os
from PIL import Image, ImageDraw, ImageEnhance

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REF_IMG_DIR = os.path.join(BASE_DIR, "referencias", "imagenes")
REF_CASA_DIR = os.path.join(BASE_DIR, "referencias", "casa_libertad")
OUT_DIR = os.path.join(BASE_DIR, "texturas")

CELL = 256
SUB = 128
SIZE = CELL * 4  # 1024 x 1024


def crop_norm(img: Image.Image, x0: float, y0: float, x1: float, y1: float, size=(CELL, CELL)) -> Image.Image:
    w, h = img.size
    box = (int(w * x0), int(h * y0), int(w * x1), int(h * y1))
    return img.crop(box).resize(size, Image.Resampling.LANCZOS)


def solid_cell(rgb: tuple[int, int, int], size=(SUB, SUB)) -> Image.Image:
    return Image.new("RGB", size, rgb)


def make_flag_tricolor(size=(SUB, SUB)) -> Image.Image:
    w, h = size
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    h3 = h // 3
    d.rectangle([0, 0, w, h3], fill=(210, 38, 32))
    d.rectangle([0, h3, w, 2 * h3], fill=(242, 208, 36))
    d.rectangle([0, 2 * h3, w, h], fill=(32, 132, 54))
    return im


def make_wiphala(size=(SUB, SUB)) -> Image.Image:
    colors = [
        (214, 34, 34), (238, 122, 28), (242, 212, 34),
        (244, 244, 240), (36, 146, 56), (34, 86, 178), (118, 44, 148),
    ]
    w, h = size
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    n = 7
    step_x, step_y = w / n, h / n
    for r in range(n):
        for c in range(n):
            col = colors[(r + c) % 7]
            d.rectangle([int(c * step_x), int(r * step_y), int((c + 1) * step_x) + 1, int((r + 1) * step_y) + 1], fill=col)
    return im


def make_acta_parchment() -> Image.Image:
    im = solid_cell((236, 224, 194), (CELL, CELL))
    d = ImageDraw.Draw(im)
    d.rectangle([10, 10, CELL - 10, CELL - 10], outline=(168, 142, 102), width=3)
    d.rectangle([42, 26, CELL - 42, 46], fill=(115, 76, 48))
    for y in range(64, CELL - 34, 14):
        w_line = CELL - 32 if y < CELL - 60 else CELL - 90
        d.line([(28, y), (w_line, y)], fill=(96, 76, 58), width=3)
    d.ellipse([CELL - 72, CELL - 68, CELL - 38, CELL - 34], fill=(172, 46, 38))
    return im


def make_velvet(rgb: tuple[int, int, int], size=(SUB, SUB)) -> Image.Image:
    im = solid_cell(rgb, size)
    d = ImageDraw.Draw(im)
    w, h = size
    r, g, b = rgb
    darker = (max(0, r - 14), max(0, g - 10), max(0, b - 10))
    for y in range(0, h, 6):
        d.line([(0, y), (w, y)], fill=darker, width=1)
    for x in range(0, w, 6):
        d.line([(x, 0), (x, h)], fill=darker, width=1)
    return im


def make_foliage_flowers() -> Image.Image:
    im = solid_cell((62, 106, 42), (SUB, SUB))
    d = ImageDraw.Draw(im)
    for cx, cy in ((20, 25), (65, 18), (102, 32), (38, 72), (88, 68), (22, 104), (72, 106), (110, 96)):
        d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(44, 82, 30))
    for fx, fy, col in ((30, 32, (226, 66, 82)), (84, 42, (238, 126, 152)), (52, 84, (226, 66, 82)), (98, 86, (240, 178, 62))):
        d.ellipse([fx - 7, fy - 7, fx + 7, fy + 7], fill=col)
    return im


def make_piano_keys() -> Image.Image:
    im = solid_cell((242, 238, 226), (SUB, SUB))
    d = ImageDraw.Draw(im)
    n_keys = 14
    kw = SUB / n_keys
    for k in range(n_keys):
        x = int(k * kw)
        d.line([(x, 0), (x, SUB)], fill=(120, 114, 104), width=1)
        if k % 7 in (0, 1, 3, 4, 5) and k < n_keys - 1:
            bx = int((k + 0.65) * kw)
            d.rectangle([bx, 0, bx + max(4, int(kw * 0.55)), int(SUB * 0.62)], fill=(28, 24, 22))
    return im


def make_ataud_emblem() -> Image.Image:
    im = solid_cell((42, 36, 34), (SUB, SUB))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, SUB - 6, SUB - 6], outline=(196, 158, 76), width=4)
    # Emblema universitario estilizado dorado
    d.ellipse([44, 28, 84, 68], fill=(196, 158, 76))
    d.line([(32, 92), (96, 72)], fill=(196, 158, 76), width=5)
    d.line([(32, 72), (96, 92)], fill=(196, 158, 76), width=5)
    return im


def paste_cell(atlas: Image.Image, cell_img: Image.Image, col: int, row: int):
    atlas.paste(cell_img, (col * CELL, row * CELL))


def paste_sub(atlas: Image.Image, sub_img: Image.Image, gx: int, gy: int):
    # gx: 0..7, gy: 0..1 dentro de la fila inferior (y: 768..1024)
    atlas.paste(sub_img, (gx * SUB, 3 * CELL + gy * SUB))


def make_dark_window_glass() -> Image.Image:
    """Vidrio colonial profundo (marron-obsidiana oscuro) para contraste nitido detras de rejas."""
    im = Image.new("RGB", (SUB, SUB), (14, 11, 10))
    d = ImageDraw.Draw(im)
    for y in range(SUB):
        t = y / max(1, SUB - 1)
        r = int(14 + 12 * (1.0 - t))
        g = int(11 + 10 * (1.0 - t))
        b = int(10 + 11 * (1.0 - t))
        d.line([(0, y), (SUB, y)], fill=(r, g, b))
    # Sutil reflejo diagonal de vidrio antiguo
    d.polygon([(16, 18), (40, 18), (88, SUB - 16), (64, SUB - 16)], fill=(30, 26, 25))
    return im


def make_balcon_y_vereda() -> Image.Image:
    """Subcelda (7,1): mitad superior madera calida de balcon colonial; mitad inferior piedra gris acera."""
    im = Image.new("RGB", (SUB, SUB), (88, 90, 96))
    d = ImageDraw.Draw(im)
    half = SUB // 2
    # Mitad superior (gy top -> UV v superior): madera calida miel-roble (#966436..#b8824a)
    d.rectangle([0, 0, SUB, half], fill=(166, 114, 62))
    for y in range(0, half, 4):
        shade = 148 + ((y * 17) % 34)
        g_col = (shade, int(shade * 0.68), int(shade * 0.37))
        d.line([(0, y), (SUB, y)], fill=g_col, width=2)
    for x in range(8, SUB, 24):
        d.line([(x, 0), (x, half - 1)], fill=(128, 84, 42), width=1)
    # Mitad inferior (gy bottom -> UV v inferior): piedra gris pizarra para vereda exterior (#52545a..#64676e)
    d.rectangle([0, half, SUB, SUB], fill=(88, 90, 96))
    for y in range(half, SUB, 8):
        for x in range(0, SUB, 12):
            v = 80 + ((x * 13 + y * 29) % 24)
            d.rectangle([x, y, x + 10, min(SUB - 1, y + 6)], fill=(v, v + 2, v + 5))
    return im


def make_water_tiles() -> tuple[Image.Image, Image.Image]:
    """Genera albedo de agua y su tile de altura [L] usando relieve_acuarela_agua.jpg."""
    water_rel = os.path.join(os.path.dirname(REF_CASA_DIR), "..", "..", "web", "public", "texturas", "relieve_acuarela_agua.jpg")
    # REF_CASA_DIR = museo_interior/referencias/casa_libertad -> subimos 3 niveles a repo root
    water_rel = os.path.abspath(os.path.join(REF_CASA_DIR, "..", "..", "..", "web", "public", "texturas", "relieve_acuarela_agua.jpg"))
    if os.path.exists(water_rel):
        im_w = Image.open(water_rel).convert("L").resize((SUB, SUB), Image.Resampling.BICUBIC)
    else:
        im_w = Image.new("L", (SUB, SUB), 128)
    # Albedo azul verdoso colonial de pila de piedra con sutil caustica
    px = im_w.load()
    alb = Image.new("RGB", (SUB, SUB))
    apx = alb.load()
    for y in range(SUB):
        for x in range(SUB):
            v = px[x, y] / 255.0
            apx[x, y] = (
                int(32 + 34 * v),
                int(86 + 52 * v),
                int(106 + 56 * v),
            )
    return alb, im_w


def make_atlas_normal_and_rough(water_height: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Genera mapas 512x512 Roughness (L) y Normal OpenGL (RGB) para atlas_museo."""
    S = 512
    C = 128
    SB = 64

    rough = Image.new("L", (S, S), 170)
    rd = ImageDraw.Draw(rough)

    def r_cell(col: int, row: int, val: int):
        rd.rectangle([col * C, row * C, (col + 1) * C - 1, (row + 1) * C - 1], fill=val)

    def r_sub(gx: int, gy: int, val: int):
        rd.rectangle([gx * SB, 3 * C + gy * SB, (gx + 1) * SB - 1, 3 * C + (gy + 1) * SB - 1], fill=val)

    # Cuadros al oleo (barniz satinado)
    for col, row in [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (0, 2), (1, 2)]:
        r_cell(col, row, 148)
    r_cell(2, 1, 32)   # oculo vitral brillante
    r_cell(3, 1, 215)  # escudo piedra
    r_cell(2, 2, 52)   # vitrina espadas (vidrio/acero)
    r_cell(3, 2, 195)  # acta pergamino

    # Subceldas fila inferior
    r_sub(0, 0, 228)   # rojo terciopelo mate
    r_sub(1, 0, 224)   # azul_verde
    r_sub(2, 0, 218)   # bandera tela
    r_sub(3, 0, 218)   # wiphala tela
    r_sub(4, 0, 224)   # verde_bar
    r_sub(5, 0, 210)   # follaje
    r_sub(6, 0, 18)    # vidrio oscuro reflectante (roughness ~0.07)
    r_sub(7, 0, 120)   # vela cera
    r_sub(0, 1, 14)    # agua fuente (roughness ~0.055!)
    r_sub(1, 1, 95)    # piano teclas marfil/ebano
    r_sub(2, 1, 165)   # ataud emblema
    r_sub(3, 1, 152)   # cuadro pasillo
    r_sub(4, 1, 205)   # empedrado rombos patio
    r_sub(5, 1, 215)   # bandera belgrano
    r_sub(6, 1, 160)   # escudo bolivia
    r_sub(7, 1, 198)   # madera balcon / vereda gris

    # Normal map 512x512 neutro (128, 128, 255) salvo ondas en subcelda de agua
    norm = Image.new("RGB", (S, S), (128, 128, 255))
    wh = water_height.resize((SB, SB), Image.Resampling.BICUBIC)
    wpx = wh.load()
    npx = norm.load()
    ox, oy = 0 * SB, 3 * C + 1 * SB
    for y in range(SB):
        yp = (y - 1) % SB
        yn = (y + 1) % SB
        for x in range(SB):
            xp = (x - 1) % SB
            xn = (x + 1) % SB
            dx = (wpx[xn, y] - wpx[xp, y]) / 255.0
            dy_img = (wpx[x, yn] - wpx[x, yp]) / 255.0
            nx = -dx * 2.8
            ny = dy_img * 2.8
            nz = 1.0
            inv = 1.0 / ((nx * nx + ny * ny + nz * nz) ** 0.5)
            npx[ox + x, oy + y] = (
                int(max(0, min(255, (nx * inv * 0.5 + 0.5) * 255))),
                int(max(0, min(255, (ny * inv * 0.5 + 0.5) * 255))),
                int(max(0, min(255, (nz * inv * 0.5 + 0.5) * 255))),
            )

    return rough, norm


def make_empedrado_rombo() -> Image.Image:
    """Empedrado colonial de laja en rombos (entrada_salon.jpg) para el patio abierto."""
    im = Image.new("RGB", (SUB, SUB), (138, 128, 114))
    d = ImageDraw.Draw(im)
    step = 32
    tones = [(146, 134, 118), (128, 118, 106), (156, 144, 126), (118, 110, 98)]
    idx = 0
    for gy in range(-1, SUB // step + 2):
        for gx in range(-1, SUB // step + 2):
            cx = gx * step + (step // 2 if gy % 2 else 0)
            cy = gy * (step // 2)
            col = tones[(idx + gx + gy) % len(tones)]
            pts = [(cx, cy - step // 2 + 2), (cx + step // 2 - 2, cy), (cx, cy + step // 2 - 2), (cx - step // 2 + 2, cy)]
            d.polygon(pts, fill=col, outline=(88, 82, 74))
            idx += 1
    return im


def make_bandera_belgrano() -> Image.Image:
    im = Image.new("RGB", (SUB, SUB))
    d = ImageDraw.Draw(im)
    h3 = SUB // 3
    d.rectangle([0, 0, SUB, h3], fill=(92, 164, 214))
    d.rectangle([0, h3, SUB, 2 * h3], fill=(238, 236, 228))
    d.rectangle([0, 2 * h3, SUB, SUB], fill=(92, 164, 214))
    return im


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    im_fondo = Image.open(os.path.join(REF_CASA_DIR, "salon_fondo.jpg")).convert("RGB")
    im_salon = Image.open(os.path.join(REF_CASA_DIR, "salon.jpg")).convert("RGB")
    im_cuarto = Image.open(os.path.join(REF_CASA_DIR, "cuarto.jpg")).convert("RGB")
    im_cuarto2 = Image.open(os.path.join(REF_CASA_DIR, "cuarto2.jpg")).convert("RGB")
    im_pasillo = Image.open(os.path.join(REF_CASA_DIR, "pasillo1.jpg")).convert("RGB")
    im_fronton = Image.open(os.path.join(REF_IMG_DIR, "03_00m59s_fronton_portada.png")).convert("RGB")

    atlas = Image.new("RGB", (SIZE, SIZE), (24, 24, 24))
    emit = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))

    # Row 0 (256x256): retratos mayores
    paste_cell(atlas, crop_norm(im_fondo, 0.375, 0.04, 0.625, 0.56), 0, 0)    # Bolivar
    paste_cell(atlas, crop_norm(im_fondo, 0.080, 0.20, 0.305, 0.65), 1, 0)    # Sucre
    paste_cell(atlas, crop_norm(im_fondo, 0.720, 0.24, 0.900, 0.645), 2, 0)   # Santa Cruz
    paste_cell(atlas, crop_norm(im_cuarto, 0.740, 0.27, 0.890, 0.57), 3, 0)   # Juana Azurduy (sala lateral)

    # Row 1 (256x256): retratos sup + oculo + escudo USFX
    paste_cell(atlas, crop_norm(im_salon, 0.380, 0.14, 0.435, 0.26), 0, 1)    # Retrato sup izq
    paste_cell(atlas, crop_norm(im_salon, 0.575, 0.14, 0.625, 0.27), 1, 1)    # Retrato sup der
    oculo = crop_norm(im_salon, 0.460, 0.06, 0.540, 0.15)
    paste_cell(atlas, oculo, 2, 1)                                            # Oculo vitral
    paste_cell(emit, oculo.point(lambda p: int(p * 0.75)), 2, 1)
    escudo = crop_norm(im_fronton, 0.400, 0.305, 0.560, 0.465)
    escudo = ImageEnhance.Contrast(escudo).enhance(1.55)
    escudo = ImageEnhance.Sharpness(escudo).enhance(1.35)
    # Tinte suave arenisca envejecida para armonizar con piedra_fachada
    er, eg, eb = escudo.split()
    escudo = Image.merge("RGB", (er.point(lambda p: int(p * 0.88)), eg.point(lambda p: int(p * 0.78)), eb.point(lambda p: int(p * 0.62))))
    paste_cell(atlas, escudo, 3, 1)  # Escudo USFX portada

    # Row 2 (256x256): cuadros sala lateral + espadas + acta
    paste_cell(atlas, crop_norm(im_cuarto, 0.388, 0.325, 0.475, 0.515), 0, 2) # Retrato guerrillera sala
    paste_cell(atlas, crop_norm(im_cuarto, 0.495, 0.390, 0.585, 0.505), 1, 2) # Batalla sala
    paste_cell(atlas, crop_norm(im_fondo, 0.645, 0.430, 0.700, 0.645), 2, 2)  # Vitrina espadas
    paste_cell(atlas, make_acta_parchment(), 3, 2)                            # Acta independencia

    # Row 3 (subceldas 128x128: gx=0..7, gy=0..1)
    paste_sub(atlas, make_velvet((138, 22, 28)), 0, 0)                        # rojo (alfombra/presidio)
    paste_sub(atlas, make_velvet((32, 78, 86)), 1, 0)                         # azul_verde (escanos/techo)
    paste_sub(atlas, make_flag_tricolor(), 2, 0)                              # bandera
    paste_sub(atlas, make_wiphala(), 3, 0)                                    # wiphala
    paste_sub(atlas, make_velvet((36, 78, 54)), 4, 0)                         # verde_bar (vigas pasillo/barandas)
    paste_sub(atlas, make_foliage_flowers(), 5, 0)                            # follaje (macetas)
    paste_sub(atlas, make_dark_window_glass(), 6, 0)                          # vidrio oscuro bajo rejas
    vela = solid_cell((255, 224, 152))
    paste_sub(atlas, vela, 7, 0)                                              # vela (emisivo)
    paste_sub(emit, solid_cell((255, 200, 110)), 7, 0)

    agua_alb, agua_h = make_water_tiles()
    paste_sub(atlas, agua_alb, 0, 1)                                          # agua con relieve
    paste_sub(atlas, make_piano_keys(), 1, 1)                                 # piano_teclas
    paste_sub(atlas, make_ataud_emblem(), 2, 1)                               # ataud_emblema
    paste_sub(atlas, crop_norm(im_pasillo, 0.308, 0.400, 0.365, 0.495, (SUB, SUB)), 3, 1)  # cuadro_pasillo
    paste_sub(atlas, make_empedrado_rombo(), 4, 1)                            # empedrado_rombo
    paste_sub(atlas, make_bandera_belgrano(), 5, 1)                           # bandera_belgrano
    # Escudo Nacional de Bolivia circular/ovalado en medallon limpio sobre pared estuco
    S = SUB * 2
    cx, cy = S // 2, S // 2
    bg_hi = Image.new("RGB", (S, S), (242, 236, 226))
    d_esc = ImageDraw.Draw(bg_hi)
    # Banderas laterales cruzadas (tricolor boliviano) detras del ovalo (con amplio margen limpio)
    for side in (-1, 1):
        for idx_f, col_f in enumerate(((192, 34, 34), (218, 176, 36), (34, 118, 52))):
            y_band = cy - int(S * 0.11) + idx_f * int(S * 0.072)
            pts_f = [
                (cx + side * int(S * 0.09), y_band),
                (cx + side * int(S * 0.30), y_band - int(S * 0.04)),
                (cx + side * int(S * 0.28), y_band + int(S * 0.072)),
                (cx + side * int(S * 0.07), y_band + int(S * 0.068)),
            ]
            d_esc.polygon(pts_f, fill=col_f)
    # Ramas de laurel y olivo debajo
    d_esc.arc([cx - int(S * 0.25), cy - int(S * 0.11), cx + int(S * 0.25), cy + int(S * 0.28)],
              start=15, end=165, fill=(46, 98, 44), width=max(4, S // 30))
    # Condor andino coronando el ovalo superior (alas extendidas y cuello blanco, sin tocar borde)
    d_esc.polygon([(cx - int(S * 0.22), cy - int(S * 0.24)), (cx - int(S * 0.04), cy - int(S * 0.18)),
                   (cx, cy - int(S * 0.21)), (cx + int(S * 0.04), cy - int(S * 0.18)),
                   (cx + int(S * 0.22), cy - int(S * 0.24)), (cx + int(S * 0.13), cy - int(S * 0.14)),
                   (cx - int(S * 0.13), cy - int(S * 0.14))], fill=(46, 36, 30))
    d_esc.ellipse([cx - int(S * 0.025), cy - int(S * 0.26), cx + int(S * 0.025), cy - int(S * 0.20)],
                  fill=(226, 222, 212))
    # Marco dorado exterior e interior azul cielo del ovalo
    ow, oh = int(S * 0.17), int(S * 0.21)
    d_esc.ellipse([cx - ow - 7, cy - oh - 7, cx + ow + 7, cy + oh + 7],
                  fill=(188, 148, 52), outline=(92, 68, 28), width=3)
    d_esc.ellipse([cx - ow, cy - oh, cx + ow, cy + oh], fill=(42, 92, 164))
    # Cielo andino y Cerro Rico de Potosi con sol naciente
    d_esc.chord([cx - ow + 5, cy - oh + 5, cx + ow - 5, cy + oh - 5],
                start=178, end=362, fill=(138, 192, 232))
    d_esc.ellipse([cx - int(S * 0.045), cy - int(S * 0.14), cx + int(S * 0.045), cy - int(S * 0.05)],
                  fill=(242, 206, 74))
    d_esc.polygon([(cx - ow + 6, cy + int(S * 0.07)), (cx - int(S * 0.02), cy - int(S * 0.06)),
                   (cx + ow - 6, cy + int(S * 0.07))], fill=(142, 82, 54))
    d_esc.chord([cx - ow + 6, cy - int(S * 0.02), cx + ow - 6, cy + oh - 6],
                start=0, end=180, fill=(76, 134, 62))
    # Margen perimetral estuco limpio para evitar sangrado de mipmaps desde subceldas vecinas
    d_esc.rectangle([0, 0, S - 1, S - 1], outline=(242, 236, 226), width=20)
    bg_bol = bg_hi.resize((SUB, SUB), Image.Resampling.LANCZOS)
    paste_sub(atlas, bg_bol, 6, 1)                                          # escudo_bolivia limpio en pared blanca
    paste_sub(atlas, make_balcon_y_vereda(), 7, 1)                          # madera_balcon (sup) + vereda_gris (inf)

    rough_atlas, normal_atlas = make_atlas_normal_and_rough(agua_h)

    out_base = os.path.join(OUT_DIR, "atlas_museo.png")
    out_emit = os.path.join(OUT_DIR, "atlas_museo_emit.png")
    out_rough = os.path.join(OUT_DIR, "atlas_museo_rough.png")
    out_norm = os.path.join(OUT_DIR, "atlas_museo_normal.png")

    atlas.save(out_base, "PNG", optimize=True)
    emit.save(out_emit, "PNG", optimize=True)
    rough_atlas.save(out_rough, "PNG", optimize=True)
    normal_atlas.save(out_norm, "PNG", optimize=True)
    print(f"Atlas 2.6 guardado: {out_base} ({os.path.getsize(out_base)//1024} KB)")
    print(f"Emisivo 2.6 guardado: {out_emit} ({os.path.getsize(out_emit)//1024} KB)")
    print(f"Roughness atlas guardado: {out_rough} ({os.path.getsize(out_rough)//1024} KB)")
    print(f"Normal atlas guardado: {out_norm} ({os.path.getsize(out_norm)//1024} KB)")


if __name__ == "__main__":
    main()
