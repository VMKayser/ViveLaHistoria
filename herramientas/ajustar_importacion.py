"""Fija la importación de texturas para 3D y web: compresión de GPU, mipmaps y tamaño máximo.

Uso:  python3 -I herramientas/ajustar_importacion.py   (después: godot --headless --path godot --import)
Sin esto, una importación sin editor deja las texturas sin comprimir y sin mipmaps:
el .pck pesa el triple y las paredes "chispean" a la distancia.
"""
import re
from pathlib import Path

GODOT = Path(__file__).resolve().parent.parent / "godot"

GRANDES = {"empedrado_color", "revoque_blanco_color", "tejas_color"}


def ajustar(ruta_import: Path, valores: dict) -> bool:
    texto = ruta_import.read_text(encoding="utf-8")
    nuevo = texto
    for clave, valor in valores.items():
        patron = re.compile(rf"^{re.escape(clave)}=.*$", re.M)
        if patron.search(nuevo):
            nuevo = patron.sub(f"{clave}={valor}", nuevo)
        else:
            nuevo = nuevo.rstrip("\n") + f"\n{clave}={valor}\n"
    if nuevo != texto:
        ruta_import.write_text(nuevo, encoding="utf-8")
        return True
    return False


def main():
    cambiados = 0
    for imp in sorted((GODOT / "assets").rglob("*.import")):
        fuente = imp.with_suffix("")
        ext = fuente.suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".hdr") or "fuentes" in fuente.parts:
            continue
        if ext == ".hdr":
            valores = {"compress/mode": 2, "compress/hdr_compression": 1, "mipmaps/generate": "false", "process/size_limit": 2048}
        else:
            normal = "_normal" in fuente.stem or "nor_gl" in fuente.stem
            # 1024 solo para lo que se ve de cerca y en grande; el resto, 512.
            grande = fuente.stem in GRANDES or "personajes" in fuente.parts
            valores = {"compress/mode": 4, "mipmaps/generate": "true", "process/size_limit": 1024 if grande else 512,
                       "compress/normal_map": 1 if normal else 0}
        cambiados += ajustar(imp, valores)
    # Animaciones de personajes comprimidas al importar.
    for imp in sorted((GODOT / "assets" / "personajes").glob("*.gltf.import")):
        cambiados += ajustar(imp, {"animation/compression/enabled": "true", "animation/remove_immutable_tracks": "true"})
    print(f"{cambiados} archivos .import ajustados")


if __name__ == "__main__":
    main()
