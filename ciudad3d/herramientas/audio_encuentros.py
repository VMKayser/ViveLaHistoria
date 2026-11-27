#!/usr/bin/env python3
"""Pedidos de audio de los encuentros (ElevenLabs), una frase = un audio.

    python3 ciudad3d/herramientas/audio_encuentros.py            → verifica y lista lo que falta generar
    python3 ciudad3d/herramientas/audio_encuentros.py --json     → idem, en JSON (texto final, voz y archivo)

Lee el texto con etiquetas de personas/encuentros/audio/voces.json y comprueba que, sin etiquetas, sea idéntico a la
frase de guiones.md (mismo orden que personajes.py). El audio de cada frase va en
personas/encuentros/audio/<personaje>/<NN>.mp3 (NN = índice del paso en el guion).
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import personajes  # noqa: E402

AUDIO = personajes.RAIZ / "personas" / "encuentros" / "audio"
ETIQUETA = re.compile(r"\[[^\]]*\]\s*")


def limpiar(texto: str) -> str:
    return re.sub(r"\s+", " ", ETIQUETA.sub("", texto)).strip()


def pedidos() -> tuple:
    voces = json.loads((AUDIO / "voces.json").read_text())
    bloques = personajes.secciones_de_guion(personajes.GUIONES.read_text())
    lista, errores = [], []
    for pid, frases in voces["frases"].items():
        pasos = personajes.guion(bloques[pid])
        if len(pasos) != len(frases):
            errores.append(f"{pid}: {len(pasos)} pasos en el guion y {len(frases)} frases con etiquetas")
            continue
        for i, (paso, frase) in enumerate(zip(pasos, frases)):
            if limpiar(frase) != paso["texto"]:
                errores.append(f"{pid}[{i}] distinto:\n  carta: {paso['texto']}\n  audio: {limpiar(frase)}")
            voz = voces["voces"]["cronista" if paso["quien"] == "cronista" else pid]
            texto = frase
            for escrito, dicho in voces["pronunciacion"].items():
                texto = texto.replace(escrito, dicho)
            archivo = AUDIO / pid / f"{i:02d}.mp3"
            lista.append({"id": f"{pid}/{i:02d}", "voice_id": voz["voice_id"], "texto": texto,
                          "archivo": str(archivo.relative_to(personajes.RAIZ)), "hecho": archivo.exists()})
    return voces["modelo"], lista, errores


def main() -> int:
    modelo, lista, errores = pedidos()
    for e in errores:
        print(e, file=sys.stderr)
    faltan = [p for p in lista if not p["hecho"]]
    if "--json" in sys.argv:
        print(json.dumps({"modelo": modelo, "faltan": faltan}, ensure_ascii=False, indent=1))
    else:
        print(f"{len(lista)} frases, {len(faltan)} sin audio, {sum(len(p['texto']) for p in faltan)} caracteres")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
