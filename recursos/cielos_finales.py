#!/usr/bin/env python3
"""Cielos del visor a partir del elegido por el usuario (2026-11-23): FreeStylized 97 de día; atardecer y amanecer son
el mismo cielo con otra gradación de color (las nubes coinciden en la transición); la noche es oscura, sin nubes y con
estrellas, como pidió el usuario.

Uso: python3 recursos/cielos_finales.py → web/public/cielo/{dia,atardecer,amanecer,noche}.jpg y ciudad3d/cielo/
"""
import os

import numpy as np
from PIL import Image, ImageFilter

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIA = os.path.join(RAIZ, "recursos/originales/cielos_estilizados/sky_97_2k/sky_97_2k.png")
SAL = os.path.join(RAIZ, "web/public/cielo")
W, H = 2048, 1024


def elevacion():
    v = 1 - (np.arange(H) + 0.5) / H
    return np.clip((v - 0.5) * 2, -1, 1)[:, None, None]          # 0 en el horizonte, 1 en el cenit


def gradar(a, cenit, horizonte, nubes, exposicion):
    """a: imagen 0–1. Tiñe el cielo azul hacia `cenit` arriba y `horizonte` abajo; las nubes (claras y poco
    saturadas) toman el color `nubes`, más fuerte cerca del horizonte."""
    t = elevacion()
    lum = a.mean(axis=2, keepdims=True)
    sat = a.max(axis=2, keepdims=True) - a.min(axis=2, keepdims=True)
    nube = np.clip((lum - 0.55) * 3, 0, 1) * np.clip(1 - sat * 3, 0, 1)
    k = np.clip(1 - t, 0, 1) ** 2
    tinte = np.array(cenit) * (1 - k) + np.array(horizonte) * k
    cielo = a * tinte
    tn = np.array(nubes) * (0.75 + 0.25 * k)
    c = cielo * (1 - nube) + (lum * tn + a * 0.15) * nube
    return np.clip(c * exposicion, 0, 1)


def dia_azul(a):
    """Día claro (2026-11-26, salto de calidad: el sky_97 tal cual es de tarde y teñía la ciudad de rosa y lavanda): las
    mismas nubes, en blanco cálido con sombra azul gris, sobre un degradado limpio de azul profundo a celeste pálido."""
    from PIL import ImageFilter as F
    t = elevacion()
    lum = (a * [0.299, 0.587, 0.114]).sum(2, keepdims=True)
    fila = np.percentile(lum[:, :, 0], 25, axis=1)[:, None, None]          # el cielo sin nubes de cada altura
    nube = np.clip((lum - fila - 0.03) * 5.0, 0, 1)
    nube = np.asarray(Image.fromarray((nube[:, :, 0] * 255).astype(np.uint8)).filter(F.GaussianBlur(1.5)), np.float32)[:, :, None] / 255
    k = np.clip(1 - t, 0, 1)
    cenit, medio, hor = np.array([0.16, 0.42, 0.86]), np.array([0.36, 0.62, 0.93]), np.array([0.80, 0.88, 0.95])
    grad = np.where(k < 0.55, cenit + (medio - cenit) * (k / 0.55),
                    medio + (hor - medio) * np.clip((k - 0.55) / 0.45, 0, 1) ** 1.5)
    rel = np.clip((lum - fila) / np.maximum(1 - fila, 1e-3), 0, 1)
    sombra, luz = np.array([0.62, 0.68, 0.80]), np.array([1.0, 0.99, 0.96])
    c = grad * (1 - nube) + (sombra + (luz - sombra) * rel ** 0.7) * nube
    c = np.where(t < 0, hor + (np.array([0.70, 0.78, 0.86]) - hor) * np.clip(-t * 3, 0, 1), c)
    return np.clip(c, 0, 1)


def noche():
    rng = np.random.default_rng(97)
    t = elevacion()[:, :, 0]
    arriba, abajo = np.array([0.012, 0.018, 0.05]), np.array([0.04, 0.06, 0.13])
    k = np.clip(1 - t, 0, 1) ** 2.5
    img = np.repeat((arriba * (1 - k[..., None]) + abajo * k[..., None]), W, axis=1)
    img = img.reshape(H, W, 3).copy()
    # estrellas: uniformes sobre la esfera (más densas por área en el cenit de la panorámica), brillo en ley de potencia
    n = 4200
    u = rng.random(n)
    z = rng.random(n)                                               # seno de la elevación, solo hemisferio de arriba
    el = np.arcsin(z)
    xs = (u * W).astype(int)
    ys = ((0.5 - el / np.pi) * H).astype(int)
    brillo = 0.25 + 0.75 * rng.random(n) ** 6
    color = np.where(rng.random((n, 1)) < 0.12, [1.0, 0.85, 0.7], np.where(rng.random((n, 1)) < 0.12, [0.75, 0.85, 1.0], [1.0, 1.0, 1.0]))
    capa = np.zeros((H, W, 3))
    for x, y, b, c in zip(xs, ys, brillo, color):
        capa[y, x] += np.array(c) * b
        if b > 0.7:                                                 # las más brillantes, una cruz de un píxel
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                capa[(y + dy) % H, (x + dx) % W] += np.array(c) * b * 0.35
    halo = np.asarray(Image.fromarray((np.clip(capa, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)),
                      dtype=np.float32) / 255
    img = img + np.clip(capa, 0, 1) * 0.9 + halo * 0.5
    img *= np.clip(t * 6 + 0.15, 0.15, 1)[..., None] ** 0.0 * 1.0   # (sin cambio: el horizonte lo funde la niebla)
    return np.clip(img, 0, 1)


def main():
    a = np.asarray(Image.open(DIA).convert("RGB").resize((W, H), Image.LANCZOS), dtype=np.float32) / 255
    salidas = {
        "dia": dia_azul(a),
        "atardecer": gradar(a, cenit=(0.55, 0.5, 0.85), horizonte=(1.25, 0.72, 0.45), nubes=(1.0, 0.72, 0.55), exposicion=0.9),
        "amanecer": gradar(a, cenit=(0.75, 0.75, 1.0), horizonte=(1.15, 0.85, 0.9), nubes=(1.0, 0.86, 0.88), exposicion=0.95),
        "noche": noche(),
    }
    for n, img in salidas.items():
        for sal in (SAL, os.path.join(RAIZ, "ciudad3d", "cielo")):
            Image.fromarray((img * 255).astype(np.uint8)).save(os.path.join(sal, n + ".jpg"), quality=90, optimize=True,
                                                               progressive=True)
        print(n)


if __name__ == "__main__":
    main()
