#!/usr/bin/env python3
"""Genera variantes GLB preservando intacto el bloque binario del modelo maestro."""
import argparse
import copy
import hashlib
import json
import shutil
import struct
from pathlib import Path


def color_lineal(hex_srgb):
    c = [int(hex_srgb.lstrip("#")[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]


def leer_glb(datos_bytes):
    magic, version, largo = struct.unpack_from("<III", datos_bytes)
    assert magic == 0x46546C67 and version == 2 and largo == len(datos_bytes), "GLB inválido"
    bloques = []
    cursor = 12
    while cursor < largo:
        n, tipo = struct.unpack_from("<II", datos_bytes, cursor)
        bloques.append((tipo, datos_bytes[cursor + 8:cursor + 8 + n]))
        cursor += 8 + n
    assert bloques[0][0] == 0x4E4F534A, "Primer bloque no es JSON"
    return json.loads(bloques[0][1]), bloques[1:]


def escribir_glb(documento, bloques):
    texto = json.dumps(documento, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    texto += b" " * (-len(texto) % 4)
    cuerpo = struct.pack("<II", len(texto), 0x4E4F534A) + texto
    cuerpo += b"".join(struct.pack("<II", len(b), tipo) + b for tipo, b in bloques)
    return struct.pack("<III", 0x46546C67, 2, 12 + len(cuerpo)) + cuerpo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datos", required=True, type=Path, help="Ruta al JSON del vehículo")
    parser.add_argument("--maestro", required=True, type=Path, help="Ruta al GLB maestro")
    parser.add_argument("--salida", required=True, type=Path, help="Directorio de salida")
    args = parser.parse_args()

    datos = json.loads(args.datos.read_text())
    id_veh = datos["id"]
    predeterminado = datos["variante_predeterminada"]
    variantes = datos["variantes"]
    base_bytes = args.maestro.read_bytes()
    documento, bloques = leer_glb(base_bytes)

    paleta_base = variantes[predeterminado]
    ranuras = [k for k, v in paleta_base.items() if isinstance(v, str) and v.startswith("#")]
    indices_mat = {}
    for ranura in ranuras:
        sufijo = "__" + paleta_base[ranura].lstrip("#").lower()
        candidatos = [
            (i, m["name"].split("__")[0])
            for i, m in enumerate(documento.get("materials", []))
            if m.get("name", "").lower().endswith(sufijo)
        ]
        assert len(candidatos) == 1, f"No se identifica material único para ranura '{ranura}' ({sufijo}): {candidatos}"
        indices_mat[ranura] = candidatos[0]

    args.salida.mkdir(parents=True, exist_ok=True)
    manifiesto = {
        "version": 1,
        "id": id_veh,
        "predeterminado": predeterminado,
        "maestro": args.maestro.name,
        "controlador": "cinematica_vehiculo.mjs",
        "variantes": [],
    }
    for id_var, info in variantes.items():
        destino = args.salida / f"{id_veh}_{id_var}.glb"
        if id_var == predeterminado:
            shutil.copyfile(args.maestro, destino)
        else:
            nuevo = copy.deepcopy(documento)
            for ranura, (idx, prefijo_rol) in indices_mat.items():
                mat = nuevo["materials"][idx]
                hex_nuevo = info[ranura].lstrip("#").lower()
                mat["name"] = f"{prefijo_rol}__{hex_nuevo}"
                factor = mat["pbrMetallicRoughness"].get("baseColorFactor", [1, 1, 1, 1])
                mat["pbrMetallicRoughness"]["baseColorFactor"] = color_lineal(info[ranura]) + [factor[3]]
                mat.setdefault("extras", {})["pintura_vehiculo"] = ranura
            nodo_raiz = next(n for n in nuevo["nodes"] if n.get("name") == id_veh)
            nodo_raiz.setdefault("extras", {})["variante"] = id_var
            destino.write_bytes(escribir_glb(nuevo, bloques))

        raw = destino.read_bytes()
        manifiesto["variantes"].append({
            "id": id_var,
            **info,
            "glb": destino.name,
            "blend": f"{id_veh}_{id_var}.blend",
            "bytes_glb": len(raw),
            "sha256_glb": hashlib.sha256(raw).hexdigest(),
        })

    ruta_manifiesto = args.salida / f"{id_veh}.variantes.json"
    ruta_manifiesto.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"manifiesto": str(ruta_manifiesto), "variantes": len(manifiesto["variantes"])}))


if __name__ == "__main__":
    main()
