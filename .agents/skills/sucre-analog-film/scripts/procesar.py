#!/usr/bin/env python3
"""Planificar ediciones, registrar salidas de Codex o ejecutar la CLI imagegen."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parents[1]
EXTENSIONES = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff', '.bmp'}


def huella(ruta):
    with ruta.open('rb') as archivo:
        return hashlib.file_digest(archivo, 'sha256').hexdigest()


def guardar_json(ruta, contenido):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=ruta.parent,
                                     suffix='.tmp', delete=False) as archivo:
        json.dump(contenido, archivo, ensure_ascii=False, indent=2)
        temporal = Path(archivo.name)
    temporal.replace(ruta)


def validar_imagen(ruta):
    with Image.open(ruta) as imagen:
        if getattr(imagen, 'n_frames', 1) != 1:
            raise ValueError(f'No se admiten imágenes animadas/multipágina: {ruta}')
        imagen.verify()
    with Image.open(ruta) as imagen:
        return ImageOps.exif_transpose(imagen).size


def crear_plan(entrada, referencias, recursivo=False):
    entrada = entrada.resolve(strict=True)
    if not entrada.is_dir() or entrada.name == 'generadas':
        raise ValueError('Selecciona una carpeta de originales, no generadas/.')
    salida = entrada / 'generadas'
    referencias = [r.resolve(strict=True) for r in referencias]
    for referencia in referencias:
        validar_imagen(referencia)
    prompt = (RAIZ / 'assets/prompt.txt').read_text(encoding='utf-8').strip()
    perfil = {'prompt': prompt, 'referencias': [
        {'ruta': str(r), 'sha256': huella(r)} for r in referencias]}
    archivos = entrada.rglob('*') if recursivo else entrada.iterdir()
    trabajos = []
    for origen in sorted(archivos):
        if (not origen.is_file() or origen.suffix.lower() not in EXTENSIONES
                or 'generadas' in origen.relative_to(entrada).parts
                or origen.is_symlink() or origen.resolve() in referencias):
            continue
        dimensiones = validar_imagen(origen)
        # La extensión original evita colisiones entre foto.jpg y foto.webp.
        destino = salida / origen.relative_to(entrada).parent / (origen.name + '.png')
        firma = hashlib.sha256(json.dumps({
            'perfil': perfil, 'origen': huella(origen)}, sort_keys=True).encode()).hexdigest()
        registro = destino.with_suffix('.json')
        estado = 'pendiente'
        if destino.exists() or registro.exists():
            estado = 'conflicto'
            if destino.is_file() and registro.is_file():
                datos = json.loads(registro.read_text(encoding='utf-8'))
                if datos.get('firma') == firma and datos.get('sha256_salida') == huella(destino):
                    estado = 'terminada'
        trabajos.append({'origen': str(origen), 'destino': str(destino),
                         'dimensiones_original': dimensiones, 'firma': firma, 'estado': estado})
    if not trabajos:
        raise ValueError('No hay fotografías compatibles en la carpeta.')
    return {'entrada': str(entrada), 'salida': str(salida), **perfil, 'trabajos': trabajos}


def registrar(plan, trabajo, generado, motor):
    if trabajo['estado'] != 'pendiente':
        raise ValueError('La salida ya existe o su perfil cambió; no se sobrescribe.')
    dimensiones = validar_imagen(generado)
    destino = Path(trabajo['destino'])
    destino.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(generado) as imagen:
        imagen.load()
        with destino.open('xb') as archivo:
            imagen.save(archivo, format='PNG')
    guardar_json(destino.with_suffix('.json'), {
        **trabajo, 'estado': 'terminada', 'motor': motor,
        'dimensiones_salida': dimensiones, 'sha256_salida': huella(destino),
        'referencias': plan['referencias'], 'prompt': plan['prompt'],
        'revision_visual': 'pendiente',
    })


def ejecutar_api(plan, args):
    configurada = os.getenv('IMAGE_GEN_CLI')
    cli = Path(configurada) if configurada else Path(
        os.getenv('CODEX_HOME', str(Path.home() / '.codex'))
    ) / 'skills/.system/imagegen/scripts/image_gen.py'
    if not cli.is_file():
        raise ValueError('No se encontró la CLI de imagegen. Configura IMAGE_GEN_CLI.')
    pendientes = [t for t in plan['trabajos'] if t['estado'] == 'pendiente']
    if args.limite:
        pendientes = pendientes[:args.limite]
    if not args.simular and not os.getenv('OPENAI_API_KEY'):
        raise ValueError('Falta OPENAI_API_KEY. Configúrala localmente; no la pegues en el chat. '
                         'También puedes usar image_gen dentro de Codex, sin clave.')
    for indice, trabajo in enumerate(pendientes, 1):
        print(f'[{indice}/{len(pendientes)}] {trabajo["origen"]}', flush=True)
        with tempfile.TemporaryDirectory(prefix='sucre-analog-') as temporal:
            carpeta = Path(temporal)
            prompt = carpeta / 'prompt.txt'
            prompt.write_text(plan['prompt'], encoding='utf-8')
            imagenes = [Path(trabajo['origen'])] + [Path(r['ruta']) for r in plan['referencias']]
            normalizadas = []
            for i, ruta in enumerate(imagenes):
                copia = carpeta / f'entrada-{i}.png'
                with Image.open(ruta) as imagen:
                    ImageOps.exif_transpose(imagen).convert('RGB').save(copia)
                if copia.stat().st_size >= 50 * 1024 * 1024:
                    raise ValueError(f'La entrada normalizada supera 50 MB: {ruta}')
                normalizadas.append(copia)
            generado = carpeta / 'resultado.png'
            comando = [sys.executable, str(cli), 'edit', '--model', 'gpt-image-2',
                       '--quality', args.calidad, '--size', 'auto', '--n', '1',
                       '--output-format', 'png', '--no-augment',
                       '--prompt-file', str(prompt), '--out', str(generado)]
            for imagen in normalizadas:
                comando.extend(['--image', str(imagen)])
            if args.simular:
                comando.append('--dry-run')
            # Sin reintentos propios; un error detiene el lote.
            subprocess.run(comando, check=True)
            if not args.simular:
                registrar(plan, trabajo, generado, 'Images API: gpt-image-2')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accion', choices=['plan', 'api', 'registrar'])
    parser.add_argument('carpeta', type=Path)
    parser.add_argument('--referencia', action='append', type=Path, default=[],
                        help='Repetible. Por defecto usa la carpeta hermana SucreAestheticAplied.')
    parser.add_argument('--recursivo', action='store_true')
    parser.add_argument('--limite', type=int)
    parser.add_argument('--calidad', choices=['low', 'medium', 'high', 'auto'], default='high')
    parser.add_argument('--simular', action='store_true', help='API dry-run; no consume saldo.')
    parser.add_argument('--origen', type=Path)
    parser.add_argument('--resultado', type=Path)
    args = parser.parse_args()
    try:
        if args.limite is not None and args.limite < 1:
            raise ValueError('--limite debe ser positivo.')
        referencias = args.referencia
        if not referencias:
            carpeta_refs = args.carpeta.resolve().parent / 'SucreAestheticAplied'
            if carpeta_refs.is_dir():
                referencias = sorted(p for p in carpeta_refs.iterdir()
                                     if p.is_file() and p.suffix.lower() in EXTENSIONES)
        plan = crear_plan(args.carpeta, referencias, args.recursivo)
        if args.accion == 'registrar':
            if not args.origen or not args.resultado:
                raise ValueError('registrar requiere --origen y --resultado.')
            trabajo = next((t for t in plan['trabajos']
                            if Path(t['origen']) == args.origen.resolve()), None)
            if trabajo is None:
                raise ValueError('El original no pertenece al plan.')
            registrar(plan, trabajo, args.resultado, 'Codex image_gen')
            plan = crear_plan(args.carpeta, referencias, args.recursivo)
        elif args.accion == 'api':
            if any(t['estado'] == 'conflicto' for t in plan['trabajos']):
                raise ValueError('Hay salidas con perfil distinto o sin registro. '
                                 'Consérvalas en otra carpeta antes de reprocesar.')
            ejecutar_api(plan, args)
            plan = crear_plan(args.carpeta, referencias, args.recursivo)
        if not args.simular:
            guardar_json(Path(plan['salida']) / 'plan.json', plan)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
