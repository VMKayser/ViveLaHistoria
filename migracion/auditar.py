#!/usr/bin/env python3
"""Auditoría de la migración, pensada para correr en un CLON LIMPIO del repositorio nuevo.

  git clone git@github.com:antrak13/Mi_Ciudad_Sucre.git auditoria && cd auditoria && git lfs pull
  python3 -I migracion/auditar.py [--hasta PR07] [--construir] [--informe migracion/auditorias/<usuario>.md]

--hasta PRxx : durante la migración, comprueba solo los PR ya fusionados (hasta ese inclusive).
--construir  : además instala y construye (npm ci + next build, importación de Godot si está la variable GODOT).
Sale con código 1 si hay algún INCUMPLIMIENTO. Las ADVERTENCIAS no bloquean pero deben quedar explicadas.
No modifica ningún archivo del repositorio (salvo el informe, si se pide).
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = Path(os.environ.get("MIC_RAIZ") or AQUI.parent).resolve()   # repo auditado (por defecto, el de este script)
MAN = json.loads((AQUI / "manifiesto.json").read_text())
EQ = json.loads((AQUI / "equipo.json").read_text())
PROPIOS = {".gitignore", ".gitattributes", "README.md", "MIGRATION_PLAN.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md"}
LFS_EXT = tuple(l.split()[0][1:] for l in (RAIZ / ".gitattributes").read_text().splitlines()
                if "filter=lfs" in l) if (RAIZ / ".gitattributes").exists() else ()
IA = re.compile(r"co-authored-by:|generated (with|by)|🤖|noreply@anthropic|anthropic\.com|claude code|claude\.ai|chatgpt|openai\.com|gemini cli|copilot", re.I)
SECRETO = re.compile(r"(sk-[A-Za-z0-9_-]{20,}|sk_[a-f0-9]{30,}|xi-api-key\s*[:=]|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|github_pat_\w{30,}"
                     r"|-----BEGIN [A-Z ]*PRIVATE KEY|(password|passwd|api[_-]?key|secret|token)\s*[:=]\s*['\"][^'\"\s]{6,})", re.I)
RUTA_LOCAL = re.compile(r"(/home/[a-z][\w.-]+/|/Users/[A-Za-z][\w.-]+/|\b[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+)", re.I)

fallos, avisos, ok = [], [], []


def sh(*c, check=False):
    r = subprocess.run(c, cwd=RAIZ, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"{' '.join(c)}: {r.stderr}")
    return r.stdout


def orden(pr):
    return int(pr[2:])


def comprobar_archivos(prs):
    esperados = {a["ruta"]: a for a in MAN["archivos"] if a["pr"] in prs}
    versionados = set(filter(None, sh("git", "ls-files", "-z").split("\0")))
    faltan = sorted(set(esperados) - versionados)
    sobran = sorted(r for r in versionados - set(esperados)
                    if r not in PROPIOS and not r.startswith(("migracion/", "docs/")))
    distintos = []
    for r, a in esperados.items():
        f = RAIZ / r
        if r in versionados and f.exists():
            h = sh("git", "hash-object", "--no-filters", r).strip()
            if h != a["oid"]:
                distintos.append(r)
    (fallos if faltan else ok).append(f"Archivos del manifiesto ({len(prs)} PR): {len(esperados)} esperados, faltan {len(faltan)}"
                                      + (": " + ", ".join(faltan[:15]) + (" …" if len(faltan) > 15 else "") if faltan else ""))
    (fallos if distintos else ok).append(f"Contenido idéntico al origen (huella git): distintos {len(distintos)}"
                                         + (": " + ", ".join(distintos[:10]) if distintos else ""))
    (avisos if sobran else ok).append(f"Archivos fuera del manifiesto: {len(sobran)}" + (": " + ", ".join(sobran[:15]) if sobran else ""))
    ignorados = [r for r in esperados if sh("git", "check-ignore", "--no-index", r).strip()]
    (fallos if ignorados else ok).append(f"Archivos necesarios que .gitignore ignoraría: {len(ignorados)}" + (": " + ", ".join(ignorados[:10]) if ignorados else ""))
    return versionados


def comprobar_lfs(versionados):
    if not shutil.which("git-lfs") and not sh("git", "lfs", "version"):
        fallos.append("Git LFS no está instalado"); return
    en_lfs = set(l.split(" ", 2)[-1] for l in sh("git", "lfs", "ls-files").splitlines())
    deberian = {r for r in versionados if r.lower().endswith(LFS_EXT)}
    fuera = sorted(deberian - en_lfs)
    (fallos if fuera else ok).append(f"Binarios en LFS: {len(deberian & en_lfs)}/{len(deberian)}" + (" · fuera de LFS: " + ", ".join(fuera[:10]) if fuera else ""))
    punteros = [r for r in deberian if (RAIZ / r).exists() and (RAIZ / r).read_bytes()[:30].startswith(b"version https://git-lfs")]
    (fallos if punteros else ok).append(f"Binarios descargados (no punteros LFS): faltan {len(punteros)}" + (" → correr git lfs pull" if punteros else ""))
    grandes = [r for r in versionados if r not in en_lfs and (RAIZ / r).exists() and (RAIZ / r).stat().st_size > 5e6]
    (avisos if grandes else ok).append(f"Archivos > 5 MB fuera de LFS: {len(grandes)} {grandes[:5] if grandes else ''}")


def comprobar_secretos(versionados):
    prohibidos = [r for r in versionados if re.search(r"(^|/)(export_presets\.cfg|\.env(\..*)?|.*\.(keystore|jks|pem|p12))$", r)
                  and not r.endswith(".env.example") and r != "godot/export_presets.cfg"]
    hallazgos, rutas, rutas_doc = [], [], []
    for r in versionados:
        f = RAIZ / r
        if not f.exists() or f.stat().st_size > 3e6 or r.lower().endswith(LFS_EXT) or r.endswith(".blend"):
            continue
        t = f.read_text(errors="ignore")
        for m in SECRETO.finditer(t):
            if not re.search(r"['\"]\s*$|\"\"|''", m.group(0)):
                hallazgos.append(f"{r}: {m.group(0)[:40]}")
        if RUTA_LOCAL.search(t) and not r.startswith("migracion/"):
            (rutas_doc if r.lower().endswith((".md", ".txt")) else rutas).append(r)
    pres = RAIZ / "godot/export_presets.cfg"
    if pres.exists() and re.search(r'password="[^"]+"', pres.read_text()):
        prohibidos.append("godot/export_presets.cfg (con contraseña)")
    (fallos if prohibidos else ok).append(f"Archivos de secretos versionados: {len(prohibidos)} {prohibidos}")
    (fallos if hallazgos else ok).append(f"Posibles credenciales en texto: {len(hallazgos)}" + (": " + "; ".join(hallazgos[:8]) if hallazgos else ""))
    (fallos if rutas else ok).append(f"Rutas absolutas de un equipo concreto (/home/…, C:\\Users\\…) en código o configuración: {len(rutas)}" + (": " + ", ".join(rutas[:10]) if rutas else ""))
    (avisos if rutas_doc else ok).append(f"Rutas absolutas de un equipo concreto en documentación: {len(rutas_doc)}" + (": " + ", ".join(rutas_doc[:10]) if rutas_doc else ""))


def comprobar_historial():
    fmt = "%H%x1f%an%x1f%ae%x1f%aI%x1f%cI%x1f%P%x1f%B%x1e"
    commits = [c.strip("\n").split("\x1f") for c in sh("git", "log", "--all", f"--format={fmt}").split("\x1e") if c.strip()]
    dia, tz = EQ["fecha"], EQ["zona_horaria"]
    ini, fin = EQ["ventana"]
    fuera, ia, autores = [], [], {}
    for h, an, ae, ad, cd, padres, msg in commits:
        for d in (ad, cd):
            if not d.startswith(dia):
                fuera.append(f"{h[:8]} {d}")
            elif not (ini <= d[11:16] <= fin):
                avisos.append(f"Commit {h[:8]} a las {d[11:16]}, fuera de la ventana {ini}–{fin}")
        if IA.search(msg):
            ia.append(f"{h[:8]}: {IA.search(msg).group(0)}")
        autores[an] = autores.get(an, 0) + 1
    (fallos if fuera else ok).append(f"Commits con fecha de autor y de commit del {dia}: {len(commits) - len(set(f[:8] for f in fuera))}/{len(commits)}"
                                     + (" · fuera: " + ", ".join(fuera[:8]) if fuera else ""))
    (fallos if ia else ok).append(f"Mensajes sin firmas ni atribuciones a asistentes de IA: {len(commits) - len(ia)}/{len(commits)}" + (" · " + ", ".join(ia[:8]) if ia else ""))
    raiz = sh("git", "rev-list", "--max-parents=0", "--all").split()
    (fallos if len(raiz) != 1 else ok).append(f"Un solo commit raíz (sin historial importado): {len(raiz)}")
    etiquetas = sh("git", "tag").split()
    (avisos if etiquetas else ok).append(f"Etiquetas: {etiquetas or 'ninguna'}")
    ok.append("Commits por autor: " + ", ".join(f"{a}={n}" for a, n in sorted(autores.items())))
    # fecha de incorporación de cada archivo = fecha del commit que lo añadió
    viejas = []
    for linea in sh("git", "log", "--diff-filter=A", "--format=@%aI", "--name-only").splitlines():
        if linea.startswith("@"):
            fecha = linea[1:]
        elif linea and not fecha.startswith(dia):
            viejas.append(linea)
    (fallos if viejas else ok).append(f"Archivos incorporados con fecha distinta del {dia}: {len(viejas)}" + (": " + ", ".join(viejas[:8]) if viejas else ""))


def comprobar_prs():
    if not shutil.which("gh"):
        avisos.append("gh no está instalado: no se verificaron los pull requests"); return
    r = subprocess.run(["gh", "pr", "list", "-R", EQ["repositorio"], "--state", "all", "--limit", "100", "--json",
                        "number,title,body,author,state,createdAt,mergedAt,mergedBy,headRefName"], capture_output=True, text=True)
    if r.returncode:
        avisos.append(f"No se pudieron leer los PR: {r.stderr.strip()[:120]}"); return
    prs = json.loads(r.stdout)
    login_a_nombre = {v["github"].lower(): k for k, v in EQ["integrantes"].items()}
    for p in prs:
        if not p.get("createdAt"):
            avisos.append(f"PR #{p.get('number')}: GitHub no devolvió la fecha de creación"); continue
        quien, fusiono = p["author"]["login"], (p.get("mergedBy") or {}).get("login", "")
        crea = datetime.datetime.fromisoformat(p["createdAt"].replace("Z", "+00:00")).astimezone(datetime.timezone(datetime.timedelta(hours=-4)))
        fus = p.get("mergedAt") and datetime.datetime.fromisoformat(p["mergedAt"].replace("Z", "+00:00")).astimezone(crea.tzinfo)
        linea = f"#{p['number']} {p['headRefName']} · {quien} · creado {crea:%Y-%m-%d %H:%M}" + (f" · fusionado {fus:%H:%M} por {fusiono}" if fus else f" · {p['state']}")
        problema = (crea.date().isoformat() != EQ["fecha"]) or (fus and fus.date().isoformat() != EQ["fecha"])
        if IA.search((p.get("body") or "") + p["title"]): problema = True; linea += " · ATRIBUCIÓN IA en título/descripción"
        if fus and fusiono.lower() != quien.lower(): avisos.append(f"PR {linea}: lo fusionó otra persona (documentar por qué)")
        if quien.lower() not in login_a_nombre: problema = True; linea += " · autor fuera del equipo"
        (fallos if problema else ok).append("PR " + linea)
    for nombre, v in EQ["integrantes"].items():
        n = sum(1 for p in prs if p["author"]["login"].lower() == v["github"].lower() and p.get("mergedAt"))
        (ok if n >= len(v["prs"]) else avisos).append(f"{nombre}: {n}/{len(v['prs'])} PR fusionados")


def comprobar_metadatos():
    r = subprocess.run([sys.executable, "-I", str(AQUI / "metadatos.py"), str(RAIZ)], capture_output=True, text=True)
    if r.returncode:
        avisos.append("metadatos.py falló: " + r.stderr[-200:]); return
    m = json.loads((RAIZ / "migracion" / "metadatos.json").read_text())
    hoy = EQ["fecha"]
    futuras = [k for k, v in m["archivos"].items() for f in re.findall(r"(20\d\d)[-:/](\d\d)[-:/](\d\d)", json.dumps(v))
               if "-".join(f) > hoy]
    gps = [k for k, v in m["archivos"].items() if v.get("GPS")]
    ok.append(f"Metadatos internos inventariados: {len(m['archivos'])} recursos, {m['con_fecha_interna']} con fecha interna previa "
              f"(procedencia: se conserva y está documentada en MIGRATION_PLAN.md §Metadatos)")
    (fallos if futuras else ok).append(f"Fechas internas posteriores al {hoy} (incoherentes): {len(futuras)} {futuras[:5]}")
    (avisos if gps else ok).append(f"Recursos con coordenadas GPS en EXIF: {len(gps)} {gps[:5]}")
    (RAIZ / "migracion" / "metadatos.json").unlink()  # el inventario se regenera; no se deja suelto en el clon


def construir():
    pasos = [("npm ci", ["npm", "ci"], RAIZ / "web"), ("next build", ["npm", "run", "build"], RAIZ / "web")]
    godot = os.environ.get("GODOT")
    if godot:
        presets = RAIZ / "ciudad3d" / "export_presets.cfg"
        if not presets.exists():
            shutil.copy(RAIZ / "ciudad3d" / "export_presets.ejemplo.cfg", presets)
        pasos += [("Ciudad 3D completa: empaquetar + exportar a la web (npm run ciudad)", ["npm", "run", "ciudad"], RAIZ / "web"),
                  ("Godot importa ciudad3d", [godot, "--headless", "--path", "ciudad3d", "--import"], RAIZ),
                  ("Godot importa godot (1809)", [godot, "--headless", "--path", "godot", "--import"], RAIZ)]
    else:
        avisos.append("Variable GODOT sin definir: no se probó la importación de los proyectos Godot")
    for nombre, cmd, cwd in pasos:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        (fallos if r.returncode else ok).append(f"{nombre}: {'correcto' if not r.returncode else 'FALLÓ ' + (r.stderr or r.stdout)[-300:]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hasta", default="PR12")
    ap.add_argument("--prs", help="lista de PR a comprobar (p. ej. PR01,PR02,PR03); manda sobre --hasta")
    ap.add_argument("--construir", action="store_true")
    ap.add_argument("--informe")
    a = ap.parse_args()
    prs = set(a.prs.split(",")) if a.prs else {f"PR{i:02d}" for i in range(1, orden(a.hasta) + 1)}
    versionados = comprobar_archivos(prs)
    comprobar_lfs(versionados)
    comprobar_secretos(versionados)
    comprobar_historial()
    comprobar_prs()
    comprobar_metadatos()
    if a.construir:
        construir()
    usuario = sh("git", "config", "user.name").strip()
    texto = [f"# Auditoría de la migración — {datetime.datetime.now().astimezone():%Y-%m-%d %H:%M %z}",
             f"Ejecutada por: {usuario} · commit {sh('git', 'rev-parse', '--short', 'HEAD').strip()} · PR comprobados: {','.join(sorted(prs))}", ""]
    texto += ["## Incumplimientos", *([f"- ❌ {x}" for x in fallos] or ["- ninguno"]), "",
              "## Advertencias", *([f"- ⚠️ {x}" for x in avisos] or ["- ninguna"]), "",
              "## Correcto", *(f"- ✅ {x}" for x in ok)]
    print("\n".join(texto))
    if a.informe:
        Path(a.informe).parent.mkdir(parents=True, exist_ok=True)
        Path(a.informe).write_text("\n".join(texto) + "\n")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
