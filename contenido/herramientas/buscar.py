"""Busca expresiones (regex, sin distinguir mayúsculas ni tildes) en contenido/libro/paginas.
Uso: python3 contenido/herramientas/buscar.py "casa de moneda" "colegio .{0,20}jesuit" [--contexto 150]
Imprime por cada término las páginas PDF con número de apariciones, y con --contexto, los fragmentos."""
import os, re, sys, unicodedata, glob

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAG = os.path.join(RAIZ, "contenido", "libro", "paginas")

def norm(s):
    s = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s)          # palabras cortadas
    s = re.sub(r"\s+", " ", s)
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")

def cargar():
    out = {}
    for f in sorted(glob.glob(os.path.join(PAG, "p*.txt"))):
        out[int(os.path.basename(f)[1:5])] = norm(open(f, encoding="utf-8").read())
    return out

if __name__ == "__main__":
    args = sys.argv[1:]; ctx = 0
    if "--contexto" in args:
        i = args.index("--contexto"); ctx = int(args[i + 1]); del args[i:i + 2]
    pags = cargar()
    for t in args:
        rx = re.compile(norm(t))
        hits = {p: list(rx.finditer(x)) for p, x in pags.items()}
        hits = {p: m for p, m in hits.items() if m}
        print(f"\n## {t}: {sum(len(m) for m in hits.values())} en {len(hits)} págs")
        print("   " + " ".join(f"{p}({len(m)})" if len(m) > 1 else str(p) for p, m in hits.items()))
        if ctx:
            for p, ms in hits.items():
                for m in ms:
                    x = pags[p]; print(f"  [{p}] …{x[max(0, m.start()-ctx):m.end()+ctx]}…")
