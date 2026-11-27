#!/usr/bin/env python3
"""Temporizador de la migración: espera hasta que le toque a tu integrante y dice qué PR ejecutar.

  python3 migracion/turno.py [--max 9]

Códigos de salida (para que un asistente de IA lo repita en bucle sin intervención):
  0  → TURNO: imprime el PR y el comando exacto (python3 migracion/ejecutar_pr.py PRxx). Ejecútalo.
  2  → todavía no (dependencias sin fusionar): vuelve a correr turno.py enseguida.
  3  → TERMINADO: este integrante ya hizo todo lo suyo.
Un PR empieza apenas sus dependencias están fusionadas (no hace falta esperar la hora del cronograma, que es la
hora máxima). Avisa si algún compañero va atrasado respecto del cronograma.
"""
import argparse, sys, time
from comun import CRON, ahora, asegurar_herramientas, fusionados, hora, informe_subido, integrante, log


def pendientes(yo, hechos):
    orden = sorted(CRON["prs"].items(), key=lambda kv: (kv[1]["inicio"], kv[0]))
    out = []
    for pr, d in orden:
        if pr == "PR12":
            if pr in hechos:
                continue
            if not informe_subido(yo) or d["responsable"] == yo:
                out.append(pr)
        elif d["responsable"] == yo and pr not in hechos:
            out.append(pr)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=float, default=9, help="minutos máximos de espera en esta llamada")
    a = ap.parse_args()
    asegurar_herramientas()
    yo = integrante()
    fin = time.time() + a.max * 60
    ultimo = 0
    while True:
        hechos = fusionados()
        mios = pendientes(yo, hechos)
        if not mios:
            log(f"TERMINADO: {yo} completó todos sus PR. Fusionados: {sorted(hechos)}")
            sys.exit(3)
        pr = mios[0]
        d = CRON["prs"][pr]
        faltan = [x for x in d["depende"] if x not in hechos]
        if not faltan:
            log(f"TURNO {pr} · {d['titulo']} · rama {d['rama']} · merge previsto {d['merge']} (límite {CRON['limite']})")
            print(f"EJECUTAR: python3 migracion/ejecutar_pr.py {pr}", flush=True)
            sys.exit(0)
        if time.time() - ultimo > 120:
            ultimo = time.time()
            detalle = []
            for x in faltan:
                dx = CRON["prs"][x]
                tarde = ahora() > hora(dx["merge"])
                detalle.append(f"{x} ({dx['responsable']}, merge previsto {dx['merge']}{', ATRASADO' if tarde else ''})")
            log(f"{yo}: tu próximo es {pr} (hora máxima de inicio {d['inicio']}). Esperando: " + "; ".join(detalle))
        if time.time() > fin:
            log("SIGUE ESPERANDO: vuelve a correr  python3 migracion/turno.py")
            sys.exit(2)
        time.sleep(30)


if __name__ == "__main__":
    main()
