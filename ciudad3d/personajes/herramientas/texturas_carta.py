# Texturas de la carta de los encuentros (papel de 1809, sello de lacre, emblema del cronista).
# python3 ciudad3d/personajes/herramientas/texturas_carta.py  → ciudad3d/personajes/ui/*.png
import math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SALIDA = Path(__file__).resolve().parents[1] / "ui"
FUENTE = SALIDA / "fuentes" / "CormorantGaramond-Italic_wght.ttf"
random.seed(1809)

def papel(w=1600, h=300):
    # degradado cálido + grano + manchas suaves + oscurecido de bordes (como el CSS de la maqueta)
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            t = (x / w * 0.17 + y / h * 0.98) / 1.15
            px[x, y] = (int(245 - 11 * t), int(232 - 17 * t), int(204 - 28 * t))
    grano = Image.effect_noise((w, h), 22).convert("L")
    im = Image.composite(im, Image.new("RGB", (w, h), (196, 170, 128)), grano.point(lambda v: 255 - max(0, v - 120) // 3))
    manchas = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(manchas)
    for _ in range(26):
        x, y, r = random.randint(0, w), random.randint(0, h), random.randint(18, 90)
        d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=random.randint(12, 34))
    manchas = manchas.filter(ImageFilter.GaussianBlur(26))
    im = Image.composite(Image.new("RGB", (w, h), (170, 128, 70)), im, manchas)
    vin = Image.new("L", (w, h), 0)
    vp = vin.load()
    for y in range(h):
        for x in range(w):
            dx, dy = (x / w - 0.5) * 2, (y / h - 0.5) * 2
            r = math.sqrt(dx * dx + dy * dy)
            vp[x, y] = int(max(0.0, min(1.0, (r - 0.55) / 0.85)) * 110)
    im = Image.composite(Image.new("RGB", (w, h), (155, 122, 74)), im, vin)
    d = ImageDraw.Draw(im)
    m = 20
    d.rectangle([m, m, w - m, h - m], outline=(168, 135, 85))          # filete doble de imprenta
    d.rectangle([m + 7, m + 7, w - m - 7, h - m - 7], outline=(190, 160, 115))
    im.save(SALIDA / "papel.png")

def sello(n=192):
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    forma = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(forma)
    pts = []
    for k in range(40):
        a = k / 40 * math.tau
        r = n * 0.42 * (1 + 0.05 * math.sin(a * 5 + 1) + 0.03 * math.sin(a * 11))
        pts.append((n / 2 + r * math.cos(a), n / 2 + r * math.sin(a)))
    d.polygon(pts, fill=255)
    color = Image.new("RGBA", (n, n))
    cp = color.load()
    for y in range(n):
        for x in range(n):
            t = min(1.0, math.dist((x, y), (n * 0.36, n * 0.32)) / (n * 0.62))
            cp[x, y] = (int(212 - 104 * t), int(72 - 54 * t), int(58 - 46 * t), 255)
    im.paste(color, (0, 0), forma)
    d = ImageDraw.Draw(im)
    d.ellipse([n * 0.2, n * 0.2, n * 0.8, n * 0.8], outline=(108, 18, 12, 140), width=3)
    f = ImageFont.truetype(str(FUENTE), int(n * 0.42))
    f.set_variation_by_axes([700])
    d.text((n / 2, n / 2 + 2), "S", font=f, fill=(230, 106, 90, 120), anchor="mm")
    d.text((n / 2, n / 2), "S", font=f, fill=(109, 19, 12, 255), anchor="mm")
    im.rotate(12, resample=Image.BICUBIC).save(SALIDA / "sello.png")

def cronista(n=512):
    # emblema del narrador para el camafeo: tintero y pluma, en tinta sepia sobre fondo de pizarra
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tinta = (226, 204, 160, 255)
    # tintero
    d.rounded_rectangle([n * .30, n * .58, n * .62, n * .80], radius=n * .05, fill=tinta)
    d.rectangle([n * .40, n * .52, n * .52, n * .59], fill=tinta)
    d.ellipse([n * .38, n * .49, n * .54, n * .55], fill=(60, 80, 88, 255))
    # pluma: barbas a ambos lados de un raquis curvo
    cuerpo = []
    for k in range(0, 21):
        t = k / 20
        x = n * (.47 + .30 * t)
        y = n * (.53 - .40 * t) - n * .05 * math.sin(t * math.pi)
        ancho = n * .075 * math.sin(min(1.0, t * 1.25) * math.pi) * (0.2 if t < .15 else 1)
        cuerpo.append((x, y, ancho))
    izq = [(x - w * .75, y - w * .55) for x, y, w in cuerpo]
    der = [(x + w * .75, y + w * .55) for x, y, w in cuerpo]
    d.polygon(izq + der[::-1], fill=tinta)
    d.line([(x, y) for x, y, _ in cuerpo], fill=(120, 95, 60, 255), width=max(2, n // 128))
    im.save(SALIDA / "cronista.png")

if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    papel(); sello(); cronista()
    print("listo:", SALIDA)
