# Instrucciones para asistentes de programación — Mi Ciudad Sucre

Estas reglas valen para **cualquier** asistente (Claude Code, Gemini, Codex u otro) que use un integrante del equipo
en este repositorio. `CLAUDE.md` y `GEMINI.md` las incluyen. Idioma del proyecto: español.

## ▶️ Modo automático (lo normal hoy)

El integrante te pedirá que hagas su parte de la migración. Hazlo así, sin preguntarle nada que el plan ya responde:

1. Lee `MIGRATION_PLAN.md` (§Modo automático y su PR) y este archivo.
2. Prepara el entorno una sola vez (§Modo automático del plan): `~/mic-origen` clonado, `gh auth login` hecho **por la
   persona** (es interactivo: pídeselo), `gh auth setup-git`, `user.name` y `user.email` del integrante. Comprueba con
   `python3 migracion/turno.py --max 0.1` desde `~/mic-origen`: debe imprimir su próximo PR o "Esperando…".
3. Lanza **en segundo plano** (dura hasta 2 h y supera el tiempo máximo de un comando de cualquier asistente):
   `cd ~/mic-origen && git pull && nohup python3 migracion/auto.py >> ~/mic-migracion.log 2>&1 &`
4. **Vigila** `~/mic-migracion.log` cada 2–5 minutos (`tail -n 40 ~/mic-migracion.log`) hasta ver `AUTO: TERMINADO` y
   resume al integrante cada PR fusionado.
   - Si ves `SE NECESITA A UNA PERSONA` o el proceso murió (`pgrep -f migracion/auto.py` vacío y sin TERMINADO), lee el
     error. Si es de entorno (sesión de gh, red, disco, git-lfs, credenciales) corrígelo o pídeselo al integrante y
     vuelve a lanzar el paso 3, que retoma solo.
   - **Nunca** edites archivos incorporados, el manifiesto o el cronograma, ni te saltes la auditoría o las
     validaciones, ni fusiones PR ajenos. Si el error es de contenido, avisa al integrante para que lo hable con el equipo.
5. Al terminar, corre `cd ~/Mi_Ciudad_Sucre && git pull && python3 -I migracion/auditar.py` e informa el resultado real.

Si el asistente no puede dejar procesos en segundo plano, el integrante lanza el paso 3 en una terminal y tú solo
vigilas el log.

## 0. Antes de cualquier operación

1. **Lee `MIGRATION_PLAN.md` completo.** Es la fuente única: cronograma, responsables, ramas, archivos, commits,
   PR y validaciones. Si algo de este archivo contradice al plan, manda el plan.
2. **Identifica a tu integrante** con `gh api user -q .login` y `git config user.name`, y búscalo en
   `migracion/equipo.json`. **Solo ejecutas los PR asignados a ese integrante.** Si te piden un PR de otra persona,
   detente y explícalo: cada integrante opera desde su propia cuenta.
3. **Comprueba la hora** (`TZ=America/La_Paz date`) y el estado de las dependencias del PR
   (`gh pr list -R antrak13/Mi_Ciudad_Sucre --state all`). Si una dependencia no está fusionada, espera; no adelantes
   trabajo copiando archivos de otro PR.

## 1. Reglas de organización

- Un PR = un módulo, con exactamente los commits y los mensajes del plan (en español, en infinitivo de 3.ª persona:
  "Incorpora…", "Agrega…", "Integra…").
- Los archivos entran **solo** con `python3 -I migracion/incorporar.py <PR> --origen ~/mic-origen` (ManuelRUa agrega
  `--local` en el PR03). Nunca copies a mano desde el repo anterior ni desde otra carpeta.
- `git add` con rutas explícitas, como en la tabla del PR. **Prohibido:** `git add -A`, `git add .`, `git commit -a`.
- No edites el contenido de los archivos incorporados: deben conservar la huella del origen (la auditoría lo
  comprueba). Las mejoras van **después** de la migración, en PR aparte.
- Nunca subas `ciudad3d/export_presets.cfg`, `movil/claves/`, `.env` ni llaves (`*.keystore`, `*.jks`). Nunca
  agregues fotos de referencia ni documentos de investigación (ver `.gitignore`).
- Prohibido: `push --force`, `git rebase` sobre ramas publicadas, `commit --amend` de lo publicado, `git reset --hard`
  sobre trabajo ajeno, borrar ramas de otros y fusionar PR de otro integrante.

## 2. Reglas de integración

- Rama nueva desde `main` actualizado (`git switch main && git pull && git lfs pull`).
- Git LFS activo (`git lfs install --local`) **antes** del primer `git add`. Comprueba con `git lfs ls-files` que los
  binarios nuevos aparezcan.
- Hook obligatorio: `git config core.hooksPath migracion/hooks`.
- Abre el PR con `gh pr create` usando el título y la descripción del plan. Fusiona con `gh pr merge <n> --merge
  --delete-branch` **solo** después de las validaciones y desde la cuenta del autor del PR (el modo automático ya lo hace así).
- Si te bloquea un conflicto o un error que el plan no cubre: detente, informa al integrante y no improvises
  cambios de historial.

## 3. Reglas de consistencia temporal

- Fechas **reales**: prohibido `GIT_AUTHOR_DATE`, `GIT_COMMITTER_DATE`, `--date`, `faketime` o cualquier otra forma de
  alterar fechas. Todo commit, PR y merge ocurre el **2026-11-27, entre 09:40 y 12:30 (UTC−4)**.
- **Sin firmas de IA:** ni `Co-authored-by`, ni "Generated with…", ni emojis de robot, ni menciones al asistente en
  commits, títulos o descripciones de PR. Desactiva la atribución automática de tu herramienta (ver `CLAUDE.md` o
  `GEMINI.md`). El hook la bloquea igual.
- No se importa historial del repo anterior: nada de `git remote add` hacia él, `fetch` a este repo, `subtree`,
  `cherry-pick` ni etiquetas viejas.
- **Metadatos internos:** no los modifiques (EXIF, tIME de PNG, `asset` de GLB, etiquetas ID3, `head` de fuentes).
  Las fechas previas son procedencia legítima y están documentadas en `MIGRATION_PLAN.md §1.3`. Tu tarea es
  **inspeccionarlos e informar** las inconsistencias: fechas posteriores a hoy, GPS, autoría o licencia que falten o
  no cuadren con `recursos/LICENCIAS.md` o `godot/CREDITOS.md`. Nunca los borres ni los reescribas.

## 4. Verificación (en cada PR)

```bash
python3 -I migracion/auditar.py --hasta <PR>        # 0 incumplimientos para poder fusionar
python3 -I migracion/metadatos.py                   # inventario; revisa las fechas internas nuevas y la autoría
git log --format='%h %an %aI %cI %s' main..HEAD     # tus commits: autor correcto, fecha de hoy, sin firmas
git lfs ls-files | wc -l                            # crece según el PR
```

Además, las validaciones funcionales de tu PR en el plan (build, `npm run ciudad`, importación de Godot, etc.).
Informa al integrante del resultado de cada comprobación, con la salida real; no des por buena una validación que no
corriste.

## 5. Cuándo continuar

Pasa a la siguiente tarea solo cuando se cumplan las cuatro condiciones:
(a) tu PR está fusionado en `main`;
(b) `auditar.py --hasta <PR>` sobre `main` da 0 incumplimientos;
(c) avisaste al equipo;
(d) llegó la hora del siguiente PR o se cumplieron sus dependencias.
Si terminas antes, revisa (sin modificar nada) los PR abiertos de los demás y deja comentarios.

## 6. Auditoría final (PR12, 12:10–12:25)

Desde un **clon limpio** (nunca tu carpeta de trabajo):
`python3 -I migracion/auditar.py --construir --informe migracion/auditorias/<Integrante>.md`. Informa **todo**
incumplimiento o advertencia, aunque parezca menor: el informe lo revisan personas y herramientas automáticas.

## 7. Después de la migración (trabajo normal)

Las reglas de modelado de la ciudad (por secciones, calidad a pie, coherencia) están en `docs/REGLAS_MODELADO.md` y
en `.agents/skills/`. Las carpetas `blender/zonas/{claude,codex,antigravity}` conservan su nombre por compatibilidad con
el empaquetador.
