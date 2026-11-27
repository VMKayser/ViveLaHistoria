"""Piezas comunes de turno.py y ejecutar_pr.py (modo automático de la migración)."""
import datetime, json, os, platform, shutil, subprocess, sys, tarfile, tempfile, urllib.request, zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CRON = json.loads((AQUI / "cronograma.json").read_text())
CRON["url"] = os.environ.get("MIC_URL", CRON["url"])  # solo para ensayos
EQUIPO = json.loads((AQUI / "equipo.json").read_text())
BOLIVIA = datetime.timezone(datetime.timedelta(hours=-4))
BIN = Path.home() / ".local" / "bin"
os.environ["PATH"] = f"{os.environ.get('PATH', '')}{os.pathsep}{BIN}"


def ahora():
    return datetime.datetime.now(BOLIVIA)


def hora(hhmm):
    h, m = map(int, hhmm.split(":"))
    return ahora().replace(hour=h, minute=m, second=0, microsecond=0)


def log(*a):
    print(f"[{ahora():%H:%M:%S}]", *a, flush=True)


def correr(cmd, cwd=None, check=True, capturar=True, entorno=None):
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=capturar, shell=isinstance(cmd, str),
                       env={**os.environ, **(entorno or {})})
    if check and r.returncode:
        raise SystemExit(f"FALLÓ: {cmd if isinstance(cmd, str) else ' '.join(cmd)}\n{(r.stderr or '') + (r.stdout or '')}"[-3000:])
    return r


def _descargar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": "mi-ciudad-migracion"})
    with urllib.request.urlopen(req, timeout=120) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)


def asegurar_herramientas():
    """Instala gh y git-lfs en ~/.local/bin si faltan (Linux/macOS). En Windows: winget install GitHub.cli GitHub.GitLFS."""
    sistema, maquina = platform.system().lower(), platform.machine().lower()
    arq = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(maquina, maquina)
    BIN.mkdir(parents=True, exist_ok=True)
    for prog, repo, nombre in (("gh", "cli/cli", "gh"), ("git-lfs", "git-lfs/git-lfs", "git-lfs")):
        if shutil.which(prog):
            continue
        if sistema == "windows":
            raise SystemExit(f"Falta {prog}. Instálalo con: winget install GitHub.cli GitHub.GitLFS  y vuelve a correr.")
        log(f"Instalando {prog} en {BIN} …")
        rel = json.load(urllib.request.urlopen(urllib.request.Request(
            f"https://api.github.com/repos/{repo}/releases/latest", headers={"User-Agent": "mi-ciudad-migracion"}), timeout=60))
        so = "macOS" if (sistema == "darwin" and prog == "gh") else ("darwin" if sistema == "darwin" else "linux")
        activo = next(a for a in rel["assets"] if so in a["name"] and arq in a["name"]
                      and a["name"].endswith((".tar.gz", ".zip")))
        with tempfile.TemporaryDirectory() as t:
            arch = Path(t) / activo["name"]
            _descargar(activo["browser_download_url"], arch)
            (zipfile.ZipFile(arch) if arch.suffix == ".zip" else tarfile.open(arch)).extractall(t)
            ejecutable = next(p for p in Path(t).rglob(nombre) if p.is_file())
            shutil.copy(ejecutable, BIN / nombre)
            (BIN / nombre).chmod(0o755)
    correr(["git", "lfs", "install"], check=False)


def login_github():
    r = correr(["gh", "api", "user", "-q", ".login"], check=False)
    if r.returncode:
        raise SystemExit("gh no tiene sesión. Corre una vez:  gh auth login   (GitHub.com, HTTPS, navegador) y luego  gh auth setup-git")
    return r.stdout.strip()


def integrante():
    login = login_github().lower()
    for nombre, d in EQUIPO["integrantes"].items():
        if d["github"].lower() == login:
            return nombre
    raise SystemExit(f"La cuenta {login} no está en migracion/equipo.json. Avisa a ManuelRUa.")


def prs_github():
    r = correr(["gh", "pr", "list", "-R", CRON["repositorio"], "--state", "all", "--limit", "100",
                "--json", "number,headRefName,state,mergedAt,author,url"], check=False)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []


def fusionados():
    """PR del cronograma ya fusionados (por nombre de rama)."""
    por_rama = {p["headRefName"]: p for p in prs_github() if p.get("mergedAt")}
    return {pr for pr, d in CRON["prs"].items() if d["rama"] in por_rama}


def informe_subido(nombre):
    r = correr(["gh", "api", f"repos/{CRON['repositorio']}/contents/migracion/auditorias/{nombre}.md?ref={CRON['prs']['PR12']['rama']}"], check=False)
    return r.returncode == 0


def rama_remota_existe(rama):
    return correr(["git", "ls-remote", "--exit-code", "--heads", CRON["url"], rama], check=False).returncode == 0


def carpeta_repo():
    return Path(os.environ.get("MIC_REPO", Path.home() / "Mi_Ciudad_Sucre"))


def carpeta_origen():
    return Path(os.environ.get("MIC_ORIGEN", Path.home() / "mic-origen"))
