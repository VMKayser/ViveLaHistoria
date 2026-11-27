#!/usr/bin/env python3
"""MODO AUTOMÁTICO: un solo comando por integrante. Espera cada turno y ejecuta solo todos sus PR del cronograma.

  cd ~/mic-origen && git pull && python3 migracion/auto.py        (ManuelRUa: MIC_REPO, MIC_ORIGEN, MIC_LOCAL)

Deja todo en ~/mic-migracion.log y termina cuando el integrante completó todo (o ante un error que necesita a una
persona). Se puede cortar y volver a lanzar en cualquier momento: retoma donde quedó.
"""
import subprocess, sys, time
from pathlib import Path
from comun import AQUI, CRON, ahora, hora, log

REINTENTOS = 3


def correr(script, *args):
    # cada vuelta toma la última versión de las herramientas (git pull en ~/mic-origen lo hace ejecutar_pr.py)
    return subprocess.run([sys.executable, str(AQUI / script), *args], text=True, capture_output=True)


def main():
    fallos = {}
    while True:
        r = correr("turno.py", "--max", "5")
        print(r.stdout, end="", flush=True)
        if r.returncode == 3:
            log("AUTO: TERMINADO. Todo lo de este integrante está fusionado.")
            return
        if r.returncode == 2:
            continue
        if r.returncode != 0:
            print(r.stderr, flush=True)
            log("AUTO: turno.py falló (¿sesión de gh? ¿red?). Reintento en 60 s.")
            time.sleep(60)
            continue
        pr = next(l.split()[-1] for l in r.stdout.splitlines() if l.startswith("EJECUTAR:"))
        log(f"AUTO: ejecutando {pr} …")
        e = subprocess.run([sys.executable, str(AQUI / "ejecutar_pr.py"), pr], text=True)
        if e.returncode in (0, 2):
            continue
        fallos[pr] = fallos.get(pr, 0) + 1
        if fallos[pr] >= REINTENTOS:
            log(f"AUTO: {pr} falló {REINTENTOS} veces. SE NECESITA A UNA PERSONA: leer el error de arriba y avisar al equipo.")
            sys.exit(1)
        log(f"AUTO: {pr} falló (intento {fallos[pr]}/{REINTENTOS}). Reintento en 60 s (retoma donde quedó).")
        time.sleep(60)


if __name__ == "__main__":
    main()
