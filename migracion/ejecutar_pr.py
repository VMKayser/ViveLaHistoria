#!/usr/bin/env python3
"""Ejecuta un PR completo del cronograma, sin intervención:
rama → incorporar → commits → auditoría → push → PR → validaciones → merge.

  cd ~/mic-origen && python3 migracion/ejecutar_pr.py PRxx

- Se corre SIEMPRE desde el clon del repo anterior (~/mic-origen, o MIC_ORIGEN), que trae estas herramientas.
- Trabaja sobre el repo nuevo en ~/Mi_Ciudad_Sucre (o MIC_REPO); lo clona si no existe.
- Se puede volver a correr si algo se corta: retoma (no repite commits ni PR ya hechos).
- Solo ejecuta PR del integrante dueño de la cuenta de gh (PR12: cada uno sube su informe; ManuelRUa fusiona).
- Variables opcionales: GODOT (ruta a Godot 4.7.2, para las validaciones de la ciudad), MIC_LOCAL (solo PR03).
Códigos de salida: 0 PR fusionado (o informe subido) · 1 falló algo (leer el mensaje) · 2 todavía no es su turno.
"""
import glob, json, os, shutil, sys, time
from pathlib import Path
from comun import (AQUI, CRON, ahora, asegurar_herramientas, carpeta_origen, carpeta_repo, correr, fusionados, hora,
                   informe_subido, integrante, log, prs_github, rama_remota_existe)

HERRAMIENTAS = ["clasificar.py", "incorporar.py", "auditar.py", "metadatos.py", "manifiesto.json", "equipo.json",
                "cronograma.json", "comun.py", "turno.py", "ejecutar_pr.py", "auto.py", "hooks"]


def git(*a, cwd=None, check=True):
    return correr(["git", *a], cwd=cwd or carpeta_repo(), check=check)


def preparar_repo():
    repo = carpeta_repo()
    if not (repo / ".git").exists():
        log(f"Clonando el repo nuevo en {repo} …")
        correr(["git", "clone", CRON["url"], str(repo)])
    git("lfs", "install", "--local")
    git("config", "core.hooksPath", "migracion/hooks")
    git("fetch", "origin", "--prune", check=False)
    return repo


def remoto_tiene_main():
    return rama_remota_existe("main")


def abrir_o_retomar_rama(rama):
    git("switch", "main")
    git("pull", "--ff-only", "origin", "main")
    git("lfs", "pull", check=False)
    locales = git("branch", "--list", rama).stdout.strip()
    if locales:
        git("switch", rama)
    elif rama_remota_existe(rama):
        git("switch", "--track", f"origin/{rama}")
    else:
        git("switch", "-c", rama)


def commitear(add, mensaje, yo):
    repo = carpeta_repo()
    rutas = []
    for patron in add:
        patron = patron.format(integrante=yo)
        encontrados = glob.glob(str(repo / patron), include_hidden=True)
        rutas += [os.path.relpath(e, repo) for e in encontrados]
    if not rutas:
        log(f"(nada que agregar para «{mensaje}»)")
        return
    git("add", "--", *rutas)
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        log(f"Ya estaba commiteado: «{mensaje.format(integrante=yo)}»")
        return
    git("commit", "-q", "-m", mensaje.format(integrante=yo))
    log(f"Commit: {mensaje.format(integrante=yo)}")


def auditar(pr, extra=()):
    prs = sorted(fusionados() | {pr}, key=lambda x: int(x[2:]))
    r = correr([sys.executable, "-I", str(AQUI / "auditar.py"), "--prs", ",".join(prs), *extra], cwd=carpeta_repo(), check=False,
               entorno={"MIC_RAIZ": str(carpeta_repo())})
    print(r.stdout[-6000:], r.stderr[-3000:])
    if r.returncode:
        raise SystemExit(f"La auditoría encontró INCUMPLIMIENTOS en {pr}: no se sube nada. Revisar la salida de arriba.")


def pr_abierto(rama):
    for p in prs_github():
        if p["headRefName"] == rama and p["state"] == "OPEN":
            return p
    return None


def crear_pr(d):
    p = pr_abierto(d["rama"])
    if p:
        return p
    correr(["gh", "pr", "create", "-R", CRON["repositorio"], "--base", "main", "--head", d["rama"],
            "--title", d["titulo"], "--body", d["cuerpo"]], cwd=carpeta_repo())
    time.sleep(3)
    return pr_abierto(d["rama"])


def validar(pr, d, numero):
    resultados, fallo = [], False
    for v in d["validar"]:
        req = v.get("requiere")
        if req and not os.environ.get(req):
            resultados.append(f"- ⏭️ `{v['cmd']}`: omitida (falta la variable {req} en este equipo)")
            continue
        log(f"Validando: {v['cmd']}")
        r = correr(v["cmd"], cwd=carpeta_repo() / v["cwd"], check=False)
        ok = r.returncode == 0
        fallo |= not ok
        cola = (r.stdout or "")[-400:] + (r.stderr or "")[-400:]
        resultados.append(f"- {'✅' if ok else '❌'} `{v['cmd']}`" + ("" if ok else f"\n```\n{cola.strip()}\n```"))
    texto = f"Validaciones de {pr} ({ahora():%Y-%m-%d %H:%M} BOT):\n" + ("\n".join(resultados) or "- (solo auditoría)")
    texto = texto.replace(" BOT", "")
    correr(["gh", "pr", "comment", str(numero), "-R", CRON["repositorio"], "--body", texto], check=False)
    print(texto)
    if fallo:
        raise SystemExit(f"Falló una validación de {pr}: el PR #{numero} queda abierto sin fusionar. Corregir y volver a correr.")


def fusionar(numero):
    correr(["gh", "pr", "merge", str(numero), "-R", CRON["repositorio"], "--merge", "--delete-branch"], cwd=carpeta_repo())
    git("switch", "main", check=False)
    git("pull", "--ff-only", "origin", "main", check=False)
    log(f"PR #{numero} fusionado.")


def pr01(yo, d):
    repo, origen = carpeta_repo(), carpeta_origen() / "migracion"
    raiz = origen / "raiz"

    def copiar():
        for f in ("README.md", "MIGRATION_PLAN.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md"):
            shutil.copy(raiz / f, repo / f)
        shutil.copy(raiz / "gitignore", repo / ".gitignore")
        shutil.copy(raiz / "gitattributes", repo / ".gitattributes")
        (repo / "migracion").mkdir(exist_ok=True)
        for h in HERRAMIENTAS:
            src = origen / h
            if src.is_dir():
                shutil.copytree(src, repo / "migracion" / h, dirs_exist_ok=True)
            else:
                shutil.copy(src, repo / "migracion" / h)
        (repo / "migracion" / "hooks" / "commit-msg").chmod(0o755)

    resto = d["commits"]
    if not remoto_tiene_main():
        log("Repo vacío: se crea main con el primer commit.")
        git("symbolic-ref", "HEAD", "refs/heads/main")
        copiar()
        commitear(d["commits"][0]["add"], d["commits"][0]["mensaje"], yo)
        git("push", "-u", "origin", "main")
        resto = d["commits"][1:]
    abrir_o_retomar_rama(d["rama"])
    copiar()
    for c in resto:  # si main ya existía (otro commit previo), todos los commits van por el PR
        commitear(c["add"], c["mensaje"], yo)


def incorporar(pr, d):
    args = [sys.executable, "-I", str(AQUI / "incorporar.py"), pr, "--origen", str(carpeta_origen()), "--destino", str(carpeta_repo())]
    if d.get("local"):
        local = Path(os.environ.get("MIC_LOCAL", Path.home() / "Documents" / "miCIudad"))
        if not local.exists():
            raise SystemExit(f"{pr} necesita los archivos locales de ManuelRUa: definir MIC_LOCAL=<carpeta miCIudad>")
        args += ["--local", str(local)]
    r = correr(args, check=False)
    print(r.stdout, r.stderr)
    if r.returncode:
        raise SystemExit(f"incorporar.py falló en {pr}")


def pr_normal(pr, d, yo):
    abrir_o_retomar_rama(d["rama"])
    incorporar(pr, d)
    for c in d["commits"]:
        commitear(c["add"], c["mensaje"], yo)
    sueltos = git("status", "--porcelain", "--untracked-files=all").stdout.strip()
    if sueltos:
        raise SystemExit(f"Quedaron archivos sin commitear tras los commits del plan:\n{sueltos[:2000]}")


def al_dia_con_main():
    """Integra en la rama lo que otros fusionaron en main mientras tanto (los PR no comparten archivos)."""
    git("fetch", "origin", "main")
    if git("merge-base", "--is-ancestor", "origin/main", "HEAD", check=False).returncode:
        git("merge", "--no-edit", "-q", "origin/main")
        git("lfs", "pull", check=False)
        log("Rama actualizada con main.")


def subir_y_fusionar(pr, d):
    al_dia_con_main()
    log("Auditoría previa al push …")
    auditar(pr)
    log(f"git push de {d['rama']} (los binarios suben por LFS; puede tardar) …")
    git("push", "-u", "origin", d["rama"])
    p = crear_pr(d)
    if not p:
        raise SystemExit("No se pudo crear o encontrar el PR")
    log(f"PR #{p['number']}: {p['url']}")
    validar(pr, d, p["number"])
    fusionar(p["number"])


def pr12(yo, d):
    """Auditoría final: informe propio desde un clon limpio; ManuelRUa fusiona cuando están los tres."""
    if not informe_subido(yo):
        limpio = Path.home() / ".cache" / "mic_auditoria_limpia"
        shutil.rmtree(limpio, ignore_errors=True)
        log("Clonación limpia para la auditoría final …")
        correr(["git", "clone", CRON["url"], str(limpio)])
        correr(["git", "lfs", "pull"], cwd=limpio)
        informe = f"migracion/auditorias/{yo}.md"
        r = correr([sys.executable, "-I", str(AQUI / "auditar.py"), "--construir", "--informe", str(Path.home() / ".cache" / f"{yo}.md")],
                   cwd=limpio, check=False, entorno={"MIC_RAIZ": str(limpio)})
        print(r.stdout[-8000:])
        sin_fallos = r.returncode == 0
        abrir_o_retomar_rama(d["rama"])
        (carpeta_repo() / "migracion" / "auditorias").mkdir(parents=True, exist_ok=True)
        shutil.copy(Path.home() / ".cache" / f"{yo}.md", carpeta_repo() / informe)
        commitear(d["commits"][0]["add"], d["commits"][0]["mensaje"], yo)
        for intento in range(5):
            git("pull", "--no-rebase", "--no-edit", "origin", d["rama"], check=False)
            if git("push", "-u", "origin", d["rama"], check=False).returncode == 0:
                break
            time.sleep(10)
        else:
            raise SystemExit("No se pudo subir el informe (push rechazado 5 veces)")
        log(f"Informe subido: {informe} · {'sin incumplimientos' if sin_fallos else 'CON INCUMPLIMIENTOS: avisar al equipo'}")
        if not sin_fallos:
            raise SystemExit(1)
    if yo != d["responsable"]:
        log("Tu parte de la auditoría está hecha. ManuelRUa fusiona el PR12.")
        return
    nombres = list(json.loads((AQUI / "equipo.json").read_text())["integrantes"])
    limite = hora(CRON["limite"])
    while not all(informe_subido(n) for n in nombres):
        faltan = [n for n in nombres if not informe_subido(n)]
        if ahora() > limite.replace(minute=limite.minute - 3):
            log(f"Hora límite y faltan informes de {faltan}: se fusiona igual y queda anotado en el PR.")
            break
        log(f"Esperando los informes de {faltan} …")
        time.sleep(30)
    p = crear_pr(d)
    abrir_o_retomar_rama(d["rama"])
    malos = [f for f in (carpeta_repo() / "migracion" / "auditorias").glob("*.md")
             if "## Incumplimientos\n- ❌" in f.read_text()]
    if malos:
        raise SystemExit(f"Hay informes con incumplimientos: {[m.name for m in malos]}. Corregir antes de fusionar el PR12.")
    validar("PR12", d, p["number"])
    fusionar(p["number"])


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in CRON["prs"]:
        raise SystemExit(__doc__)
    pr = sys.argv[1]
    d = CRON["prs"][pr]
    asegurar_herramientas()
    correr(["gh", "auth", "setup-git"], check=False)
    yo = integrante()
    if pr != "PR12" and d["responsable"] != yo:
        raise SystemExit(f"{pr} es de {d['responsable']}, no de {yo}. Cada integrante ejecuta solo sus PR.")
    correr(["git", "pull", "--ff-only"], cwd=carpeta_origen(), check=False)  # herramientas al día
    hechos = fusionados()
    if pr in hechos:
        log(f"{pr} ya está fusionado.")
        return
    faltan = [x for x in d["depende"] if x not in hechos]
    if faltan:
        log(f"Todavía no: faltan {faltan}. Correr  python3 migracion/turno.py")
        sys.exit(2)
    preparar_repo()
    log(f"=== {pr} · {d['titulo']} · {yo} · merge previsto {d['merge']} ===")
    if pr == "PR12":
        pr12(yo, d)
    else:
        (pr01(yo, d) if pr == "PR01" else pr_normal(pr, d, yo))
        subir_y_fusionar(pr, d)
    log(f"{pr} TERMINADO. Siguiente:  python3 migracion/turno.py")


if __name__ == "__main__":
    main()
