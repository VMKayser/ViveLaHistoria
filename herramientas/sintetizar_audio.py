"""Sintetiza los sonidos de la escena (todo original, sin licencias de terceros).

Uso:  python3 -I herramientas/sintetizar_audio.py
Escribe .ogg en godot/assets/audio/ (necesita numpy y ffmpeg con libvorbis).
"""
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

SR = 22050
SALIDA = Path(__file__).resolve().parent.parent / "godot" / "assets" / "audio"
rng = np.random.default_rng(1809)


def guardar(nombre, x, calidad=4):
    x = np.asarray(x, dtype=np.float64)
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
    SALIDA.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        ruta_wav = Path(tmp.name)
    with wave.open(str(ruta_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    destino = SALIDA / f"{nombre}.ogg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(ruta_wav), "-c:a", "libvorbis", "-q:a", str(calidad), str(destino)], check=True)
    ruta_wav.unlink()
    print(f"  {destino.name}  {len(x) / SR:.1f} s")


def t(segundos):
    return np.arange(int(segundos * SR)) / SR


def filtro_banda(x, bajo, alto):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < bajo) | (f > alto)] = 0
    return np.fft.irfft(X, len(x))


def pasabajos(x, corte):
    return filtro_banda(x, 0, corte)


def reverb(x, dur=1.6, mezcla=0.35, brillo=4000):
    n = int(dur * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (SR * dur / 6))
    ir = pasabajos(ir, brillo)
    ir /= np.sqrt(np.sum(ir ** 2))
    largo = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, largo) * np.fft.rfft(ir, largo), largo)
    return np.concatenate([x, np.zeros(n)]) * (1 - mezcla) + y * mezcla


def ciclo(x, cruce=1.0):
    """Hace un bucle sin corte: funde el final con el principio."""
    n = int(cruce * SR)
    rampa = np.linspace(0, 1, n)
    y = x[:-n].copy()
    y[:n] = y[:n] * rampa + x[-n:] * (1 - rampa)
    return y


def ruido_marron(n):
    b = np.cumsum(rng.standard_normal(n))
    b -= np.convolve(b, np.ones(2000) / 2000, mode="same")
    return b / (np.max(np.abs(b)) + 1e-9)


# ---------------------------------------------------------------- campana

def campana(f=262.0, dur=7.0):
    x = t(dur)
    # parciales de una campana de iglesia: hum, prime, tercera menor, quinta, nominal...
    parciales = [(0.5, 0.55, 7.0), (1.0, 0.8, 4.5), (1.19, 0.6, 3.6), (1.5, 0.35, 2.8), (2.0, 0.7, 2.6),
                 (2.52, 0.3, 1.6), (2.66, 0.25, 1.4), (3.01, 0.2, 1.1), (4.07, 0.12, 0.7), (5.4, 0.06, 0.4)]
    y = np.zeros_like(x)
    for rel, amp, dec in parciales:
        for det in (-0.6, 0.6):  # dos modos casi iguales: el batido típico del bronce
            y += amp * np.sin(2 * np.pi * (f * rel + det) * x + rng.uniform(0, 6)) * np.exp(-x / dec)
    golpe = filtro_banda(rng.standard_normal(len(x)), 800, 7000) * np.exp(-x / 0.012) * 1.5
    return reverb(y + golpe, 2.2, 0.3)


# ---------------------------------------------------------------- multitud

VOCALES = [(750, 1250), (500, 1800), (300, 2300), (450, 900), (350, 800), (650, 1100)]


def voz(dur, f0_base, intensidad=1.0, grito=False):
    """Una voz que habla en sílabas: tren de pulsos filtrado por formantes."""
    n = int(dur * SR)
    y = np.zeros(n)
    pos = int(rng.uniform(0, 0.6) * SR)
    while pos < n:
        hablar = rng.uniform(0.6, 2.2) if not grito else rng.uniform(1.0, 2.5)
        fin = min(n, pos + int(hablar * SR))
        while pos < fin:
            seg = int(rng.uniform(0.09, 0.22 if not grito else 0.45) * SR)
            seg = min(seg, n - pos)
            if seg < 64:
                break
            ts = np.arange(seg) / SR
            f0 = f0_base * rng.uniform(0.9, 1.15) * (1.25 if grito else 1.0)
            fase = np.cumsum(2 * np.pi * f0 * (1 + 0.02 * np.sin(2 * np.pi * 5 * ts)) / SR)
            fuente = np.sign(np.sin(fase)) * 0.3 + (2 * ((fase / (2 * np.pi)) % 1) - 1)
            fuente += rng.standard_normal(seg) * 0.15
            F1, F2 = VOCALES[rng.integers(len(VOCALES))]
            X = np.fft.rfft(fuente)
            fr = np.fft.rfftfreq(seg, 1 / SR)
            forma = np.exp(-((fr - F1) / 110) ** 2) + 0.7 * np.exp(-((fr - F2) / 170) ** 2) + 0.15 * np.exp(-((fr - 2800) / 400) ** 2)
            s = np.fft.irfft(X * forma, seg)
            s *= np.hanning(seg) * rng.uniform(0.5, 1.0) * intensidad
            y[pos:pos + seg] += s
            pos += int(seg * rng.uniform(0.75, 1.05))
        pos = fin + int(rng.uniform(0.3, 1.4 if not grito else 0.5) * SR)
    return y


def multitud(dur=14.0, voces=36, grito=False):
    y = np.zeros(int(dur * SR))
    for _ in range(voces):
        f0 = rng.choice([rng.uniform(95, 140), rng.uniform(170, 240)])
        d = rng.uniform(0.3, 1.0)
        y += voz(dur, f0, d, grito)
    y = pasabajos(y, 3500)
    y += ruido_marron(len(y)) * 0.04 * np.max(np.abs(y))
    return reverb(y, 1.2, 0.35, 3000)[: len(y)]


def ovacion(dur=4.5):
    y = multitud(dur, 48, grito=True)
    x = t(dur)[: len(y)]
    envolvente = np.clip(x / 0.6, 0, 1) * np.exp(-np.clip(x - 2.2, 0, None) / 0.9)
    return reverb(y * envolvente, 1.6, 0.3, 3000)


# ---------------------------------------------------------------- ambiente

def viento(dur=16.0):
    n = int(dur * SR)
    b = filtro_banda(ruido_marron(n) + rng.standard_normal(n) * 0.05, 80, 900)
    x = t(dur)
    mod = 0.6 + 0.4 * np.sin(2 * np.pi * x / 7.3) * np.sin(2 * np.pi * x / 3.1 + 1)
    return ciclo(b * mod, 1.5)


def paso(semilla):
    r = np.random.default_rng(semilla)
    dur = 0.22
    x = t(dur)
    impacto = filtro_banda(r.standard_normal(len(x)), 250, 4500) * np.exp(-x / 0.018)
    golpe = np.sin(2 * np.pi * r.uniform(70, 95) * x) * np.exp(-x / 0.03) * 0.8
    arena = filtro_banda(r.standard_normal(len(x)), 2000, 8000) * np.exp(-((x - 0.03) / 0.03) ** 2) * 0.25
    return impacto + golpe + arena


def fuego(dur=6.0):
    n = int(dur * SR)
    base = filtro_banda(ruido_marron(n), 60, 500) * 0.5
    y = base.copy()
    for _ in range(int(dur * 14)):
        p = rng.integers(0, n - 400)
        largo = rng.integers(40, 300)
        chispa = rng.standard_normal(largo) * np.exp(-np.arange(largo) / (largo / 4)) * rng.uniform(0.3, 1.0)
        y[p:p + largo] += filtro_banda(chispa, 1500, 9000) if largo > 64 else chispa
    return ciclo(y, 0.8)


def disparo():
    dur = 2.5
    x = t(dur)
    chasquido = rng.standard_normal(len(x)) * np.exp(-x / 0.006)
    boom = np.sin(2 * np.pi * 55 * x * (1 - 0.3 * x)) * np.exp(-x / 0.25) * 1.2
    cola = filtro_banda(rng.standard_normal(len(x)), 100, 2500) * np.exp(-x / 0.12) * 0.4
    y = chasquido + boom + cola
    eco = np.zeros_like(y)
    for retardo, g in ((0.11, 0.35), (0.23, 0.22), (0.41, 0.12)):
        k = int(retardo * SR)
        eco[k:] += y[:-k] * g
    return reverb(pasabajos(y + eco, 6000), 1.8, 0.35)


def tension(dur=24.0):
    x = t(dur)
    y = np.zeros_like(x)
    for f, a in ((73.42, 1.0), (110.0, 0.6), (146.83, 0.35), (174.61, 0.18)):
        for det in (-0.25, 0.0, 0.3):
            fase = 2 * np.pi * (f + det) * x
            sierra = sum(np.sin(k * fase) / k for k in range(1, 9))
            y += a * sierra
    y = pasabajos(y, 700)
    y *= 0.55 + 0.45 * np.sin(2 * np.pi * x / 12.0 - np.pi / 2) ** 2
    agudo = np.sin(2 * np.pi * 440 * x) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * x)) * 0.03
    agudo *= np.clip(np.sin(2 * np.pi * x / 24.0), 0, None)
    return ciclo(reverb(y + agudo * np.max(np.abs(y)), 2.5, 0.4, 2500)[: len(x)], 2.0)


def main():
    print("sintetizando…")
    guardar("campana", campana(262.0))
    guardar("campana_grave", campana(185.0, 8.0))
    guardar("multitud", ciclo(multitud(15.0, 40), 1.5))
    guardar("ovacion", ovacion())
    guardar("viento", viento())
    for i in range(4):
        guardar(f"paso_{i + 1}", paso(100 + i))
    guardar("fuego", fuego())
    guardar("disparo", disparo())
    guardar("tension", tension(), calidad=5)
    print("listo")


if __name__ == "__main__":
    main()
