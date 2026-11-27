"""OCR del libro OLIMPIADAS CONOCE TU HISTORIA.pdf -> contenido/libro/paginas/p0001.txt ...
Las páginas con capa de texto se extraen con pdftotext; las escaneadas, con tesseract (spa, 300 dpi).
Reanudable: salta las páginas ya hechas.  Uso: python3 contenido/herramientas/ocr_libro.py [procesos]

Rehacer un tramo con fondo texturado (el *Cofre*, págs. 956-1226, tiene fondo de pergamino que oscurece los bordes y
hacía perder palabras): python3 contenido/herramientas/ocr_libro.py 4 --rehacer 956-1226
Se resta el fondo (desenfoque gaussiano) antes del umbral y se usa --psm 6; método "ocr2" en la cabecera."""
import os, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDF = os.path.join(RAIZ, "OLIMPIADAS CONOCE TU HISTORIA.pdf")
SAL = os.path.join(RAIZ, "contenido", "libro", "paginas")
TESS = os.path.expanduser("~/apps/tesseract/tesseract")
os.makedirs(SAL, exist_ok=True)

def n_paginas():
    out = subprocess.run(["pdfinfo", PDF], capture_output=True, text=True).stdout
    return int([l for l in out.splitlines() if l.startswith("Pages:")][0].split()[1])

def limpiar_fondo(img):
    """Texto oscuro sobre fondo de pergamino desparejo -> blanco y negro limpio."""
    from PIL import Image, ImageChops, ImageFilter
    im = Image.open(img).convert("L")
    fondo = im.filter(ImageFilter.GaussianBlur(30))
    ImageChops.subtract(fondo, im).point(lambda v: 0 if v > 35 else 255).save(img)


def rehacer(p):
    dest = os.path.join(SAL, f"p{p:04d}.txt")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", "300", "-gray", "-png",
                        PDF, os.path.join(tmp, "i")], check=True)
        img = os.path.join(tmp, os.listdir(tmp)[0])
        limpiar_fondo(img)
        txt = subprocess.run([TESS, img, "-", "-l", "spa", "--psm", "6"], capture_output=True, text=True,
                             env={**os.environ, "OMP_THREAD_LIMIT": "1"}).stdout
    with open(dest + ".tmp", "w", encoding="utf-8") as f:
        f.write(f"<<pdf_pagina {p} | ocr2>>\n{txt}")
    os.replace(dest + ".tmp", dest)


def hacer(p):
    dest = os.path.join(SAL, f"p{p:04d}.txt")
    if os.path.exists(dest):
        return
    txt = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), PDF, "-"],
                         capture_output=True, text=True).stdout
    metodo = "texto"
    if len(txt.split()) < 20:
        metodo = "ocr"
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", "300", "-gray", "-png",
                            PDF, os.path.join(tmp, "i")], check=True)
            img = os.path.join(tmp, os.listdir(tmp)[0])
            txt = subprocess.run([TESS, img, "-", "-l", "spa"], capture_output=True, text=True,
                                 env={**os.environ, "OMP_THREAD_LIMIT": "1"}).stdout
    with open(dest + ".tmp", "w", encoding="utf-8") as f:
        f.write(f"<<pdf_pagina {p} | {metodo}>>\n{txt}")
    os.replace(dest + ".tmp", dest)

if __name__ == "__main__":
    if "--rehacer" in sys.argv:
        a, b = map(int, sys.argv[sys.argv.index("--rehacer") + 1].split("-"))
        with ThreadPoolExecutor(int(sys.argv[1])) as ex:
            list(ex.map(rehacer, range(a, b + 1)))
        print("listo")
        sys.exit()
    n = n_paginas()
    with ThreadPoolExecutor(int(sys.argv[1]) if len(sys.argv) > 1 else 6) as ex:
        for i, _ in enumerate(ex.map(hacer, range(1, n + 1)), 1):
            if i % 50 == 0:
                print(f"{i}/{n}", flush=True)
    print("listo")
