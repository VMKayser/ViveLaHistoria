# Plan de migración — Mi Ciudad Sucre

**Repositorio nuevo:** `https://github.com/antrak13/Mi_Ciudad_Sucre` (privado, dueño: Antrak13). Cuentas: ManuelRUa = `ManuelRua`, Antrak13 = `antrak13`, VMKayser = `VMKayser`
**Repositorio anterior (solo lectura, fuente de los archivos):** `git@github.com:ManuelRuaEchalar/miCiudadCharcas.git`,
commit `9461982` de `main` (más `museo_interior/README.md` del commit `452a364` de `develop`).
**Jornada:** viernes 27 de noviembre de 2026, de 09:40 a 12:30, hora de Bolivia (UTC−4).
**Responsable técnico:** ManuelRUa · **Integrantes:** ManuelRUa, Antrak13, VMKayser.

Este documento es la fuente única de la migración. `AGENTS.md`, `CLAUDE.md` y `GEMINI.md` remiten a él.

## ▶️ MODO AUTOMÁTICO (lo recomendado: nadie tiene que recordar horarios)

Cada integrante lanza **un solo comando** una vez y se olvida. El programa espera a que se fusionen las dependencias de
cada PR suyo (no hace falta esperar la hora: la hora del cronograma es la **máxima**) y luego, sin intervención, crea la
rama, incorpora los archivos, hace los commits del plan, audita, sube, abre el PR, valida y lo fusiona. Después pasa al
siguiente PR, hasta terminar. Si se corta, se vuelve a lanzar y retoma donde quedó.

```bash
# una sola vez (Linux/macOS; en Windows usar "python" y antes: winget install GitHub.cli GitHub.GitLFS)
git clone --depth 1 https://github.com/ManuelRuaEchalar/miCiudadCharcas.git ~/mic-origen
cd ~/mic-origen && python3 migracion/turno.py --max 0.1     # instala gh y git-lfs si faltan; dice si falta iniciar sesión
gh auth login            # GitHub.com → HTTPS → Login with a web browser (con TU cuenta)
gh auth setup-git
git config --global user.name "<tu nombre>" && git config --global user.email "<tu correo o el noreply de GitHub>"

# y lanzar (deja la terminal abierta y el equipo encendido y con internet hasta que diga TERMINADO)
cd ~/mic-origen && git pull && python3 migracion/auto.py 2>&1 | tee -a ~/mic-migracion.log
```

- **Antrak13:** antes de lanzar, aceptar que la cuenta `ManuelRua` y la cuenta `VMKayser` estén invitadas como colaboradoras con
  permiso *Write*, y después de su PR01 activar la protección de `main` (§3).
- **VMKayser:** aceptar la invitación de colaborador al repositorio antes de lanzar.
- Opcional, para las validaciones de Godot: `export GODOT=/ruta/a/Godot_v4.7.2-stable_...` antes de lanzar.
- Si `auto.py` se detiene con "SE NECESITA A UNA PERSONA", leer el error, corregir la causa (sesión de gh, red,
  disco) y volver a lanzar el mismo comando.
- Con un asistente de IA: pedirle que lea `AGENTS.md` §Modo automático y que ejecute y vigile `auto.py`.

Lo que sigue (horario, archivos y validaciones de cada PR) es lo que hace el modo automático. `migracion/cronograma.json` es su versión ejecutable: sirve para revisarlo o para hacerlo a mano si hiciera falta.

---

## 1. Qué es el proyecto (resultado de la inspección)

| Módulo | Carpetas | Qué hace | Cómo se ejecuta |
|---|---|---|---|
| **Web y portada** | `web/` (Next.js 15, React 19) | Portada, `/ciudad` (envoltorio de la ciudad 3D), `/mapa`, herramientas de revisión | `cd web && npm ci && npm run dev` |
| **Ciudad 3D** | `ciudad3d/` (Godot 4.7.2) | Ciudad navegable a pie, la misma para la web (WASM) y el APK de Android | `cd web && npm run ciudad` (empaqueta y exporta a `web/public/ciudad3d/`) |
| **Modelos de la ciudad** | `web/public/models/`, `blender/` | Manzanas, plaza y base urbana en GLB; scripts de Blender 5.2 que las generan | Blender: `blender -b -P blender/zonas/<zona>/<script>.py` |
| **Datos urbanos** | `Sucre.osm.*`, `urban-export_*.fbx`, `reparto/`, `estilo/`, `web/public/mapa/`, `scripts/` | Calles, huellas de manzanas, reparto y estilo | `python3 scripts/huellas.py`, etc. |
| **Tráfico** | `web/public/trafico/`, `web/scripts/`, `ciudad3d/scripts/trafico*`, `autos/` | Micros, autos y carrozas con física | `cd web && npm run trafico` |
| **Personajes y encuentros** | `ciudad3d/personajes/`, `ciudad3d/scripts/personajes/`, `personas/`, `contenido/` | 13 personajes animados, carta de 1809, guiones y voces | `python3 ciudad3d/herramientas/personajes.py` (lo hace `npm run ciudad`) |
| **Museo y escenas históricas** | `museo_interior/`, `ciudad3d/escenas_historicas/`, `ciudad3d/escape_rooms/` | Interior de la Casa de la Libertad | Blender + escena Godot |
| **Ciudad Charcas 1809** | `godot/`, `blender/*_1809.py`, `herramientas/` | Recorrido del 25 de mayo de 1809 (Godot independiente) | `godot --path godot` |
| **Revisiones y app móvil** | `web/src/ciudad/revision/`, `web/src/app/api/`, `web/src/servidor/`, `movil/` | Correcciones enmarcadas en el visor; guía del APK | `npm run dev` · `npm run ciudad:apk` |

**Dependencias de sistema:** Node 20+ (probado con 22.23), Python 3.10+ con `numpy` y `Pillow`, Godot 4.7.2 con
plantillas de exportación 4.7.2 (variable `GODOT`), Git LFS 3.x. Blender 5.2 solo para regenerar modelos.

### 1.1 Qué se incorpora y qué no

`migracion/manifiesto.json` lista **cada archivo** con su PR, su huella git (`oid`), su tamaño y su modo. Lo genera
`migracion/clasificar.py` a partir del commit de origen. El ensayo completo, hecho el 2026-11-27 a las 09:47 en un
repositorio local de prueba, dio esto: **1.733 archivos y 690 MB incorporados; 0 huellas distintas; 651 binarios en
LFS; 0 secretos; 0 rutas locales.**

| Se incorpora | Se excluye (motivo) |
|---|---|
| Código de la web, de Godot, de Blender y los scripts | Fotos de referencia: `fotos/`, `fotosCentro/`, `masCiudadFotos/`, `ultimasFotsos/`, `fotosPlazaYSanMiguel/`, `guia_plaza/`, `Peatonal/`, `museo_interior/referencias*` (≈ 580 MB) |
| Modelos GLB y `.blend` que usan el empaquetador y el tráfico | Coordinación interna y correcciones con capturas: `coordinacion/` (≈ 141 MB; solo se incorpora `coordinacion/revisiones/LEEME.md`) |
| Texturas, cielos, iconos y fuentes | Visores HTML y vistas previas de trabajo de personajes y vehículos (≈ 68 MB) |
| Voces (`personas/encuentros/audio/`, 123 MP3) y audio de 1809 | Pruebas de estilo (`SucreAesthetic*`, `piloto_estilos/`), `capturas/`, `ui_ideas/`, `secciones/` |
| Datos OSM y FBX de origen, reparto, estilo | Documentos de investigación: PDF, DOCX, `contenido/libro/`, anuncios HTML/ZIP |
| **`web/public/mapa/raw/lienzo.glb`**: está **solo en el equipo de ManuelRUa**; sin él no se puede empaquetar la ciudad | Generados y cachés: `ciudad3d/datos/`, `web/public/ciudad3d/`, `node_modules/`, `.next/`, `.godot/`, `web/public/models/opt/` |
| Licencias de terceros (`THREE-LICENSE.txt`, `OFL.txt`, `LICENSE.txt` de Quaternius, `recursos/LICENCIAS.md`, `godot/CREDITOS.md`) | **Secretos:** `ciudad3d/export_presets.cfg` (contraseña del APK) y `movil/claves/` (llave de firma). **Nunca se suben** |
| | ≈ 3,7 GB de personajes en preparación sin versionar (`personas/*/`): el juego no los usa; `contenido/personajes.json` solo pide los 13 incorporados |

Las referencias de código a lo excluido son solo comentarios, salvo tres scripts de desarrollo
(`blender/zonas/codex/revisar_exportados.py`, `recorrer_codex.py` y `contenido/herramientas/ocr_libro.py`), que leen
revisiones o el libro y no forman parte de la ejecución.

**Nombres de carpetas heredados:** `blender/zonas/{claude,codex,antigravity}/` y `web/public/models/ciudad/{claude,codex,antigravity}/`
se llaman así porque en el desarrollo cada zona la trabajó un asistente distinto. Se **conservan** porque el
empaquetador y los manifiestos usan esas rutas. Son nombres de carpeta, no firmas.

### 1.2 Git LFS

`.gitattributes` manda a LFS: `glb blend fbx bin hdr exr png jpg jpeg webp mp3 ogg wav opus ttf otf pbf gz xz zip rar apk`.
Son ≈ 685 MB en LFS. El texto (`.gltf`, `.json`, `.import`, `.tres`, `.gd`, código) queda en git normal.
**Antes del PR04, Antrak13 revisa la cuota LFS** de su cuenta (Settings → Billing → Git LFS). Si el plan gratuito tiene
1 GiB de almacenamiento y 1 GiB de ancho de banda al mes, los 690 MB entran, pero tres clones completos superan el
ancho de banda. En ese caso se compra un paquete de datos o las auditorías se hacen con un solo clon compartido.

### 1.3 Metadatos internos (inventario hecho el 2026-11-27)

`migracion/metadatos.py` (solo lectura) revisó 645 recursos binarios:

- **Programa de origen:** Blender glTF I/O 5.2.x (172 GLB), Lavf/FFmpeg (123 voces y audio), glTF-Transform 4.5.1 (15),
  Substance Designer (8), GIMP 2.10 (4), Photoshop 23.5 (4), xNormal (2), gnome-screenshot (2).
- **56 recursos con fecha interna anterior a hoy:**
  - texturas CC0 de terceros (Poly Haven, Substance) y fuentes OFL, de **2014 a 2024**;
  - recursos propios con fechas de **agosto y noviembre de 2026**, del desarrollo en el repositorio anterior.
- **Autoría y licencias embebidas:** 6 GLB del caballo llevan `copyright: "Horse model by Mirada from ROME (3 Dreams of Black) / three.js"`.
  Hay que verificar esa licencia antes de cualquier uso comercial.
- **Sin coordenadas GPS** en ningún recurso incorporado. Ninguna fecha interna es posterior a hoy.

**Regla:** los metadatos internos **no se modifican**. Las fechas previas son **procedencia**: el contenido se
desarrolló entre octubre y noviembre de 2026 en el repositorio anterior (cuyo historial no se importa) y se
**incorpora** hoy. Las fechas de incorporación son las de los commits, PR y merges de hoy, y esas sí deben ser
todas del 27 de noviembre de 2026. Las fechas que aparecen en la documentación (por ejemplo, las mediciones del
2026-11-26 en `ciudad3d/LEEME.md`) también son históricas y se dejan igual. Borrar o reescribir metadatos para que
el material parezca creado hoy sería falsear la procedencia y está prohibido.

---

## 2. Reglas de la migración

1. **Historial limpio:** el repo nuevo empieza con el commit de PR01. Prohibido importar o reutilizar commits, ramas
   o etiquetas del repo anterior (`git remote add` del repo viejo, `git subtree`, `git filter-repo`, `cherry-pick`).
   Los archivos se copian **solo** con `migracion/incorporar.py`, que verifica la huella de cada uno.
2. **Fechas reales:** no se usan `GIT_AUTHOR_DATE`, `GIT_COMMITTER_DATE`, `--date` ni `commit --amend` para cambiar fechas.
3. **Sin firmas de asistentes:** ningún commit, título ni descripción de PR lleva `Co-authored-by`, "Generated with",
   emojis de robot ni otras atribuciones automáticas a Claude, Codex, Gemini u otro asistente. El hook
   `migracion/hooks/commit-msg` lo bloquea (`git config core.hooksPath migracion/hooks`).
4. **Cuentas propias:** cada integrante commitea, abre y fusiona **sus** PR desde su cuenta de GitHub, con su
   `user.name` y su correo (o el `noreply` de GitHub).
5. **Un PR = un módulo**, con los commits indicados. Solo se agregan los archivos de ese PR
   (`git add <rutas>`; nunca `git add -A` ni `git add .`).
6. **Validar antes de fusionar:** `python3 -I migracion/auditar.py --hasta PRxx` sin incumplimientos, más las
   validaciones propias del PR.
7. **Merge:** "Create a merge commit" (conserva los commits pequeños). Después se borra la rama.
8. Si algo falla, se corrige con un commit nuevo en la misma rama, nunca reescribiendo lo publicado.

---

## 3. Preparación (10:00–10:15, los tres)

```bash
# 1. Git LFS y GitHub CLI
git lfs version || echo "instalar git-lfs 3.x"   # Linux sin sudo: binario de github.com/git-lfs/git-lfs/releases en ~/.local/bin
git lfs install
gh auth login                                     # cada uno con SU cuenta

# 2. Identidad (cada uno la suya; sin firmas de IA)
git config --global user.name  "<tu nombre>"
git config --global user.email "<tu correo o el noreply de GitHub>"

# 3. Repo anterior como FUENTE (solo lectura, superficial: ~0,7 GB)
git clone --depth 1 --branch main git@github.com:ManuelRuaEchalar/miCiudadCharcas.git ~/mic-origen

# 4. Repo nuevo
git clone git@github.com:antrak13/Mi_Ciudad_Sucre.git ~/Mi_Ciudad_Sucre
```

| Hora | Quién | Tarea |
|---|---|---|
| 09:40–10:05 | ManuelRUa | Inspección, manifiesto, ensayo completo y este plan. Publica `migracion/` en `main` y `develop` del repo anterior |
| 10:05–10:15 | Antrak13 | En `Mi_Ciudad_Sucre`: agrega como colaboradores con permiso *Write* a `ManuelRuaEchalar` y `VMKayser`. **Después de fusionar el PR01** (el primer commit de `main` se sube directo porque el repo está vacío), protege `main`: PR obligatorio, 0 aprobaciones obligatorias (cada uno fusiona lo suyo), sin forzar ni borrar. Activa solo "Allow merge commits" y "Automatically delete head branches". Revisa la cuota LFS |
| 10:05–10:15 | Los tres | Pasos 1–4 de arriba. VMKayser y Antrak13 aceptan la invitación. Si el repo está vacío, el paso 4 da un aviso: es normal |

**Continuar cuando** los tres tengan `~/mic-origen/migracion/manifiesto.json` y puedan clonar el repo nuevo.

---

## 4. Cronograma de incorporación

Cada PR se hace en `~/Mi_Ciudad_Sucre`, con la rama creada desde `main` actualizado:

```bash
cd ~/Mi_Ciudad_Sucre && git switch main && git pull && git lfs pull
git switch -c <rama>
python3 -I migracion/incorporar.py <PR> --origen ~/mic-origen          # ManuelRUa en PR03 agrega: --local <su carpeta miCIudad>
# commits según la tabla del PR (git add <rutas> && git commit -m "<mensaje>")
python3 -I migracion/auditar.py --hasta <PR>                          # 0 incumplimientos
git push -u origin <rama>
gh pr create --base main --head <rama> --title "<título>" --body-file <archivo con la descripción>
# validaciones del PR → merge (lo hace quien abrió el PR)
gh pr merge <número> --merge --delete-branch
```

### Resumen

| PR | Hora inicio → merge | Responsable | Rama | Depende de | Commits | Archivos · MB |
|---|---|---|---|---|---|---|
| PR01 | 10:15 → 10:25 | Antrak13 | `chore/inicializacion` | — | 2 | 14 · 0,9 |
| PR02 | 10:25 → 10:45 | VMKayser | `feat/web-portada` | PR01 | 2 | 72 · 5,7 |
| PR03 | 10:25 → 10:45 | ManuelRUa | `feat/datos-urbanos` | PR01 | 3 | 58 · 30,2 |
| PR04 | 10:45 → 11:10 | Antrak13 | `feat/modelos-ciudad` | PR03 | 3 | 325 · 154,0 |
| PR10 | 10:45 → 11:10 | VMKayser | `feat/ciudad-charcas-1809` | PR01 | 3 | 355 · 93,2 |
| PR05 | 11:10 → 11:35 | ManuelRUa | `feat/motor-ciudad3d` | PR02, PR03, PR04 | 3 | 165 · 12,9 |
| PR06 | 11:35 → 11:55 | VMKayser | `feat/trafico-vehiculos` | PR05 | 2 | 287 · 218,7 |
| PR07 | 11:35 → 11:55 | Antrak13 | `feat/personajes-animaciones` | PR05 | 2 | 151 · 100,8 |
| PR08 | 11:55 → 12:10 | ManuelRUa | `feat/encuentros-voces` | PR07 | 3 | 184 · 24,3 |
| PR09 | 11:55 → 12:10 | Antrak13 | `feat/museo-escenas-historicas` | PR05 | 2 | 126 · 46,1 |
| PR11 | 11:55 → 12:10 | VMKayser | `feat/revisiones-app-movil` | PR05 | 2 | 10 · 0,0 |
| PR12 | 12:10 → 12:25 | ManuelRUa (+ los tres) | `chore/auditoria-final` | todos | 3 (uno por integrante) | 3 informes |
| — | 12:25 → 12:30 | Los tres | — | PR12 | — | Auditoría sobre `main` y cierre |

**Reparto:** cada integrante tiene 4 PR y 10 commits.
- **ManuelRUa:** la integración más compleja (motor Godot, exportación web y recursos que solo están en su equipo), ≈ 67 MB.
- **Antrak13:** el repositorio y los modelos más pesados (personajes, museo), ≈ 301 MB.
- **VMKayser:** la web, el tráfico, la historia de 1809 y las revisiones, ≈ 318 MB.

Los PR de una misma franja no comparten archivos: se pueden fusionar en cualquier orden.

---

### PR01 · Antrak13 · `chore/inicializacion` · 10:15 → 10:25

**Archivos:** desde `~/mic-origen/migracion/raiz/`, copiar a la **raíz** `README.md`, `.gitignore` (de `gitignore`),
`.gitattributes` (de `gitattributes`), `MIGRATION_PLAN.md`, `AGENTS.md`, `CLAUDE.md` y `GEMINI.md`. Copiar
`~/mic-origen/migracion/{clasificar.py,incorporar.py,auditar.py,metadatos.py,manifiesto.json,equipo.json,hooks/}` a `migracion/`.

```bash
cd ~/Mi_Ciudad_Sucre && git switch -c chore/inicializacion
R=~/mic-origen/migracion
cp $R/raiz/README.md $R/raiz/MIGRATION_PLAN.md $R/raiz/AGENTS.md $R/raiz/CLAUDE.md $R/raiz/GEMINI.md .
cp $R/raiz/gitignore .gitignore && cp $R/raiz/gitattributes .gitattributes
mkdir -p migracion && cp -r $R/clasificar.py $R/incorporar.py $R/auditar.py $R/metadatos.py $R/manifiesto.json $R/equipo.json $R/hooks migracion/
git config core.hooksPath migracion/hooks && git lfs install --local
git add README.md .gitignore .gitattributes
git commit -m "Inicializa el repositorio con README, reglas de exclusión y Git LFS"
git add MIGRATION_PLAN.md AGENTS.md CLAUDE.md GEMINI.md migracion
git commit -m "Agrega el plan de migración, las instrucciones para asistentes y las herramientas de auditoría"
```

| Commit | Mensaje |
|---|---|
| 1 | `Inicializa el repositorio con README, reglas de exclusión y Git LFS` |
| 2 | `Agrega el plan de migración, las instrucciones para asistentes y las herramientas de auditoría` |

**PR:** *Inicialización del repositorio y plan de migración*
> Crea la base del repositorio: README general, `.gitignore` (excluye fotos de referencia, cachés, generados y secretos), `.gitattributes` con Git LFS para modelos, texturas, audio y fuentes, y el plan de migración con las herramientas que incorporan y auditan cada módulo (`migracion/`). Las instrucciones para asistentes (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) remiten al plan.

**Validar:** `git lfs track` lista los 22 patrones; `python3 -I migracion/auditar.py --hasta PR01` sale sin
incumplimientos (avisos aceptables: ninguno). **Merge 10:25** → avisar a los otros dos.

---

### PR02 · VMKayser · `feat/web-portada` · 10:25 → 10:45

**Archivos (72):** `web/` (configuración, `package.json`, `package-lock.json`, `src/app/` salvo `api/` y `ciudad/`,
`src/components/`, `src/data/`, `src/estilos/`, `src/mapa/`, `public/inicio/`, `public/cielo/`, `public/noche/`,
`public/texturas/`, svg, `scripts/optimizar_modelos.mjs`, `README.md`) y `banderaSucre.png`.

| Commit | `git add` | Mensaje |
|---|---|---|
| 1 | `web/package.json web/package-lock.json web/*.ts web/*.mjs web/*.json web/.gitignore web/README.md web/scripts/optimizar_modelos.mjs web/src/app/layout.tsx web/src/app/globals.css web/src/app/favicon.ico banderaSucre.png` | `Incorpora la aplicación web Next.js: dependencias, configuración y estilos base` |
| 2 | `web/` (el resto que dejó `incorporar.py`) | `Incorpora la portada, el mapa y las páginas de estilos de la web` |

**PR:** *Web: aplicación Next.js y portada*
> Incorpora la aplicación web (Next.js 15 / React 19): configuración, dependencias bloqueadas, colores de la bandera de Sucre, la portada (`public/inicio/`), el mapa y las páginas de estilos. La ciudad 3D (`/ciudad`) llega en PR05 y las revisiones en PR11.

**Validar:** `cd web && npm ci` (la compilación completa se valida en el PR11, cuando ya está todo el código de la web:
la portada importa componentes de la ciudad que llegan en el PR05) · auditoría.

---

### PR03 · ManuelRUa · `feat/datos-urbanos` · 10:25 → 10:45 (incluye recursos que solo están en su equipo)

**Archivos (58):** `Sucre.osm.gz`, `Sucre.osm.pbf`, `Sucre.osm.geojson.xz`, `urban-export_-19.0460_-65.2578_2230m.fbx`,
`reparto/`, `estilo/`, `web/public/mapa/` (incluido **`raw/lienzo.glb`, local**), `web/public/fotos/indice.json`,
`scripts/` (salvo `revisiones.py`), `blender/kit/`, `blender/scripts/`, `blender/secciones/`, `blender/zonas/PLANTILLA.py`,
`.agents/skills/` (salvo vehículos), `recursos/`, `docs/REGLAS_MODELADO.md`.

```bash
python3 -I migracion/incorporar.py PR03 --origen ~/mic-origen --local ~/Documents/miCIudad
```

| Commit | `git add` | Mensaje |
|---|---|---|
| 1 | `Sucre.osm.* urban-export_*.fbx web/public/mapa web/public/fotos` | `Incorpora los datos urbanos de Sucre: OpenStreetMap, lienzo de la ciudad y mapa` |
| 2 | `reparto estilo scripts recursos` | `Incorpora el reparto de manzanas, la paleta de estilo y los scripts de datos` |
| 3 | `blender/kit blender/scripts blender/secciones blender/zonas/PLANTILLA.py .agents docs` | `Incorpora el kit de modelado en Blender y sus reglas` |

**PR:** *Datos urbanos y kit de modelado*
> Incorpora la base geográfica (OSM, FBX urbano, lienzo y calles), el reparto de manzanas, la paleta de estilo, los scripts de datos y el kit de Blender con las reglas de modelado. `web/public/mapa/raw/lienzo.glb` se agrega desde el equipo de ManuelRUa (estaba fuera del repositorio anterior y lo necesita el empaquetador de la ciudad 3D).

**Validar:** `git lfs ls-files | grep lienzo` muestra los dos lienzos · `python3 scripts/huellas.py --help` o una
ejecución en seco sin error · `auditar.py --hasta PR03`.

---

### PR04 · Antrak13 · `feat/modelos-ciudad` · 10:45 → 11:10

**Archivos (325, 154 MB):** `web/public/models/` (manzanas, plaza, base, fondo, `manifiesto.json` y
`exportacion.json`), excepto personajes y vehículos; `blender/zonas/{claude,codex}/` (scripts de manzanas), excepto
personajes y vehículos.

| Commit | `git add` | Mensaje |
|---|---|---|
| 1 | `web/public/models/ciudad/claude web/public/models/fondo web/public/models/piloto.glb` | `Incorpora los modelos de la base urbana, la plaza y las manzanas del norte` |
| 2 | `web/public/models/ciudad/codex` | `Incorpora los modelos de la Plaza 25 de Mayo y las manzanas del sur` |
| 3 | `blender/zonas` | `Incorpora los scripts de Blender que generan cada manzana` |

**PR:** *Modelos 3D de la ciudad*
> Incorpora los GLB de las 92 piezas del manifiesto (base urbana, Plaza 25 de Mayo, manzanas del norte y del sur, cerros de fondo) y los scripts de Blender que las generan. Todo binario va por Git LFS.

**Validar:** `python3 -c "import json;[print(len(json.load(open(f'web/public/models/ciudad/{a}/manifiesto.json'))))for a in('claude','codex')]"`
y que cada `archivo` del manifiesto exista · `git lfs ls-files | wc -l` crece en ≈ 230 · `auditar.py --hasta PR04`.

---

### PR10 · VMKayser · `feat/ciudad-charcas-1809` · 10:45 → 11:10

**Archivos (355):** `godot/`, `blender/construir_1809.py`, `blender/personajes_1809.py`, `herramientas/`,
`docs/CIUDAD_CHARCAS_1809.md`.

| Commit | `git add` | Mensaje |
|---|---|---|
| 1 | `godot/project.godot godot/scripts godot/shaders godot/escenas godot/materiales godot/export_presets.cfg godot/.gitignore godot/CREDITOS.md` | `Incorpora el proyecto Godot de Ciudad Charcas 1809: escenas, scripts y shaders` |
| 2 | `godot/assets` | `Incorpora los modelos, personajes, texturas, cielos y audio de 1809` |
| 3 | `blender/construir_1809.py blender/personajes_1809.py herramientas docs` | `Incorpora las herramientas que generan la ciudad de 1809 y su documentación` |

**PR:** *Ciudad Charcas · 25 de mayo de 1809*
> Incorpora el recorrido interactivo del Primer Grito Libertario (Godot 4.7, renderer Compatibility): guion por pasos, personajes MakeHuman (CC0) con ropa de época, sonido sintetizado y las herramientas de Blender y Python que lo regeneran. Documentación en `docs/CIUDAD_CHARCAS_1809.md`.

**Validar:** `$GODOT --headless --path godot --import` sin errores · `$GODOT --headless --path godot -- --piloto`
recorre la historia hasta el final · `auditar.py --hasta PR10`. Si el PR05 todavía no se fusionó, usar `--hasta PR04`:
el PR10 queda cubierto en la auditoría siguiente.

---

### PR05 · ManuelRUa · `feat/motor-ciudad3d` · 11:10 → 11:35

**Archivos (165):** `ciudad3d/` (`project.godot`, `escenas/`, `scripts/` salvo `personajes/` y `trafico*`,
`shaders/`, `texturas/`, `cielo/`, `iconos/`, `icono.png`, `herramientas/` salvo personajes, cabezas, audio y vehículos,
`export_presets.ejemplo.cfg`, `LEEME.md`), `web/src/ciudad/` (salvo `revision/`) y `web/src/app/ciudad/`.

| Commit | `git add` | Mensaje |
|---|---|---|
| 1 | `ciudad3d/project.godot ciudad3d/escenas ciudad3d/scripts ciudad3d/LEEME.md ciudad3d/export_presets.ejemplo.cfg ciudad3d/icono.png* ciudad3d/iconos` | `Incorpora el motor de la ciudad 3D en Godot: carga por teselas, jugador, hora y calidad` |
| 2 | `ciudad3d/shaders ciudad3d/texturas ciudad3d/cielo ciudad3d/herramientas` | `Incorpora el estilo visual, los shaders y el empaquetador de la ciudad 3D` |
| 3 | `web/src/ciudad web/src/app/ciudad` | `Integra la ciudad 3D en la página web` |

**PR:** *Ciudad 3D en Godot integrada en la web*
> Incorpora el proyecto Godot que se exporta a la web (WASM) y al APK: carga por teselas, caminante, hora del día, calidad adaptativa, shaders de estilo y oclusión, empaquetador y exportador, y el puente con la página `/ciudad`. `export_presets.cfg` no se versiona: se arma desde `export_presets.ejemplo.cfg`.

**Validar desde un clon limpio** (es la prueba principal de que el proyecto funciona sin archivos locales):
```bash
git clone git@github.com:antrak13/Mi_Ciudad_Sucre.git /tmp/v && cd /tmp/v && git switch feat/motor-ciudad3d && git lfs pull
cp ciudad3d/export_presets.ejemplo.cfg ciudad3d/export_presets.cfg     # el preset Web no necesita la llave
cd web && npm ci && GODOT=<ruta a Godot 4.7.2> npm run ciudad && npm run dev
```
El modo automático valida aquí la importación de Godot (`$GODOT --headless --path ciudad3d --import`). La exportación
completa (`npm run ciudad`) necesita también personajes y tráfico, así que se valida en la auditoría final (PR12),
donde `auditar.py --construir` la ejecuta si está la variable `GODOT`.

---

### PR06 · VMKayser · `feat/trafico-vehiculos` · 11:35 → 11:55

**Archivos (287, 219 MB):** `web/public/trafico/`, `web/scripts/{preparar_vehiculos.mjs,red_vial*.py,vehiculos_trafico.json}`,
`web/public/models/ciudad/*/vehiculos/`, `blender/zonas/*/vehiculos/`, `autos/`, `ciudad3d/vehiculos/`,
`ciudad3d/scripts/trafico*`, `ciudad3d/herramientas/vehiculos.mjs`, `.agents/skills/vehiculo-3d-desde-diseno/`.

| Commit | `git add` | Mensaje |
|---|---|---|
| 1 | `web/public/models/ciudad/codex/vehiculos web/public/models/ciudad/antigravity/vehiculos blender/zonas/codex/vehiculos blender/zonas/antigravity/vehiculos autos .agents/skills/vehiculo-3d-desde-diseno` | `Incorpora los modelos de micros, autos, carrozas y caballos` |
| 2 | `web/public/trafico web/scripts ciudad3d/vehiculos ciudad3d/scripts ciudad3d/herramientas/vehiculos.mjs` | `Incorpora el tráfico con física, la red vial y su conversión para Godot` |

**PR:** *Tráfico y vehículos*
> Incorpora la flota (micros, autos clásicos, carrozas y caballos), la red vial con velocidades por calle y el tráfico con física real de Godot (`VehicleBody3D`, conductor IDM, anillo de la Plaza 25 de Mayo).

**Validar:** `npm ci` y `node ciudad3d/herramientas/vehiculos.mjs` (convierte la flota y la red vial para Godot) · auditoría.

---

### PR07 · Antrak13 · `feat/personajes-animaciones` · 11:35 → 11:55

**Archivos (151, 101 MB):** `ciudad3d/personajes/` (salvo `ui/` y `herramientas/`), `ciudad3d/scripts/personajes/personaje.gd*`,
`ciudad3d/herramientas/{personajes,cabezas}.py`, `web/public/models/ciudad/*/personajes/`, `blender/zonas/*/personajes/`,
`personas/{domingo_de_santo_tomas,jaime_zudanez,quitacapas}/`, `personas/lista_avance.md`, `contenido/personajes.json`.

| Commit | `git add` | Mensaje |
|---|---|---|
| 1 | `web/public/models/ciudad/*/personajes blender/zonas/*/personajes personas/domingo_de_santo_tomas personas/jaime_zudanez personas/quitacapas personas/lista_avance.md` | `Incorpora los modelos de los personajes históricos y sus scripts de Blender` |
| 2 | `ciudad3d/personajes ciudad3d/scripts/personajes ciudad3d/herramientas contenido/personajes.json` | `Incorpora las animaciones, la colocación y el comportamiento de los personajes` |

**PR:** *Personajes y animaciones*
> Incorpora los 13 personajes que aparecen en la ciudad, sus modelos animados, las animaciones estándar de Quaternius (CC0, con su licencia), los retratos y el script que los coloca (`contenido/personajes.json`).

**Validar:** auditoría (los 13 modelos con su huella). `personajes.py` necesita también los guiones del PR08 y se valida allí.

---

### PR08 · ManuelRUa · `feat/encuentros-voces` · 11:55 → 12:10

**Archivos (184):** `ciudad3d/scripts/personajes/{carta,encuentros,voz}.gd*`, `ciudad3d/herramientas/audio_encuentros.py`,
`ciudad3d/personajes/{ui,herramientas}/`, `personas/encuentros/` (guiones y 123 voces), `contenido/` (salvo
`personajes.json` y `libro/`).

| Commit | `git add` | Mensaje |
|---|---|---|
| 1 | `ciudad3d/scripts/personajes ciudad3d/personajes ciudad3d/herramientas` | `Incorpora el sistema de encuentros: carta de 1809, conversación y voz` |
| 2 | `personas/encuentros/PLAN.md personas/encuentros/guiones.md contenido` | `Incorpora los guiones verificados y el contenido histórico de los encuentros` |
| 3 | `personas/encuentros/audio` | `Incorpora las voces de los personajes` |

**PR:** *Encuentros con personajes y voces*
> Incorpora la conversación con los personajes: la interfaz de la carta de 1809 (fuentes OFL), el guion de cada encuentro con sus fuentes, las 123 voces sincronizadas con el texto y el contenido histórico de lugares y catálogo.

**Validar:** `python3 ciudad3d/herramientas/personajes.py` (13 personajes con guion y voces) · auditoría. La prueba en
`/ciudad` (tecla I) se hace con la exportación completa del PR12.

---

### PR09 · Antrak13 · `feat/museo-escenas-historicas` · 11:55 → 12:10

**Archivos (126):** `museo_interior/` (sin `referencias`; `README.md` viene de `develop`),
`ciudad3d/escenas_historicas/` y `ciudad3d/escape_rooms/`.

| Commit | `git add` | Mensaje |
|---|---|---|
| 1 | `museo_interior` | `Incorpora el interior del museo Casa de la Libertad: scripts, texturas y exportación` |
| 2 | `ciudad3d/escenas_historicas ciudad3d/escape_rooms` | `Incorpora la escena histórica de la Casa de la Libertad en la ciudad 3D` |

**PR:** *Museo Casa de la Libertad y escenas históricas*
> Incorpora el modelado del interior de la Casa de la Libertad (scripts de Blender, texturas PBR, atlas y GLB exportado, renders de documentación) y su escena recorrible dentro de la ciudad 3D.

**Validar:** `$GODOT --headless --path ciudad3d --import` sin errores de recursos de `escenas_historicas` ·
`auditar.py --hasta PR09`.

---

### PR11 · VMKayser · `feat/revisiones-app-movil` · 11:55 → 12:10

**Archivos (10):** `web/src/ciudad/revision/`, `web/src/app/api/`, `web/src/servidor/`, `scripts/revisiones.py`,
`coordinacion/revisiones/LEEME.md`, `movil/LEEME.md`.

| Commit | `git add` | Mensaje |
|---|---|---|
| 1 | `web/src/ciudad/revision web/src/app/api web/src/servidor scripts/revisiones.py coordinacion` | `Incorpora la herramienta de revisiones del visor` |
| 2 | `movil` | `Incorpora la guía de la aplicación Android` |

**PR:** *Revisiones del visor y guía de la app móvil*
> Incorpora la herramienta de correcciones (marcar en la ciudad lo que está mal; se guarda en `coordinacion/revisiones/`, que no se versiona salvo su LEEME) y la guía para compilar e instalar el APK. La llave de firma del APK no se versiona: el APK de release lo firma ManuelRUa.

**Validar:** `cd web && npm ci && npm run build` (compilación completa de la web) · auditoría.

---

### PR12 · ManuelRUa (con Antrak13 y VMKayser) · `chore/auditoria-final` · 12:10 → 12:25

Cada integrante, en **su** equipo y en un **clon limpio** (no la carpeta de trabajo):

```bash
rm -rf /tmp/auditoria && git clone git@github.com:antrak13/Mi_Ciudad_Sucre.git /tmp/auditoria && cd /tmp/auditoria && git lfs pull
git switch chore/auditoria-final 2>/dev/null || git switch -c chore/auditoria-final   # ManuelRUa la crea y la publica primero
GODOT=<ruta> python3 -I migracion/auditar.py --construir --informe migracion/auditorias/<TuNombre>.md
git add migracion/auditorias/<TuNombre>.md && git commit -m "Agrega la auditoría final de <TuNombre> desde una clonación limpia"
git pull --rebase=false && git push -u origin chore/auditoria-final
```

Orden: ManuelRUa 12:10 (crea la rama) → Antrak13 12:15 → VMKayser 12:20. Los informes son archivos distintos, así que
no hay conflictos.

**PR:** *Auditoría final de la migración*
> Agrega las tres auditorías independientes hechas desde clonaciones limpias: todos los archivos del manifiesto presentes y con la huella del origen, binarios en LFS, sin secretos ni rutas locales, historial de hoy sin firmas automáticas, PR de los tres integrantes, inventario de metadatos y construcción de la web y de los proyectos Godot.

**Merge 12:25** (ManuelRUa) si los tres informes dicen "Incumplimientos: ninguno".

### Cierre · los tres · 12:25 → 12:30

Sobre `main` actualizado, en un clon limpio: `python3 -I migracion/auditar.py`. Debe dar 0 incumplimientos, 12 PR
fusionados (4 por integrante) y todos los commits con fecha del 2026-11-27, entre 09:40 y 12:30. Cualquier incumplimiento se informa en el
chat del equipo y se corrige con un PR nuevo.

---

## 5. Qué comprueba la auditoría (`migracion/auditar.py`)

| Comprobación | Incumplimiento si… |
|---|---|
| Integridad | falta algún archivo del manifiesto, alguno tiene una huella distinta de la del origen, o `.gitignore` ignoraría alguno necesario |
| Git LFS | un binario de los patrones no está en LFS, quedan punteros sin descargar o hay archivos > 5 MB fuera de LFS (aviso) |
| Secretos | se versionan `export_presets.cfg` de `ciudad3d`, llaves (`.keystore`, `.jks`, `.pem`, `.env`) o aparecen credenciales en el texto |
| Rutas locales | hay rutas absolutas de un equipo (`/home/<usuario>/`, `C:\Users\`) en archivos de texto |
| Historial | hay más de un commit raíz, algún commit tiene fecha de autor o de commit distinta del 2026-11-27, o algún mensaje lleva firmas o atribuciones de IA |
| Fecha de incorporación | algún archivo se añadió en un commit con fecha distinta de hoy |
| Pull requests (`gh`) | un PR se creó o se fusionó en otra fecha, su autor no es del equipo o el título o la descripción llevan atribución de IA. Aviso si lo fusionó otra persona o si un integrante tiene menos PR de los previstos |
| Metadatos | algún recurso tiene una fecha interna posterior a hoy (incoherente) o coordenadas GPS (aviso). Las fechas previas se informan como procedencia |
| Construcción (`--construir`) | fallan `npm ci`, `next build` o la importación Godot de `ciudad3d` y `godot` |

## 6. Riesgos y contingencias

| Riesgo | Plan |
|---|---|
| Cuota LFS insuficiente | Antrak13 la revisa a las 10:10. Si no alcanza, se compra un paquete de datos antes del PR04 |
| Un PR se atrasa | Los PR de la misma franja son independientes. Se sigue con los que no dependen del atrasado; el cronograma tiene 5 min de holgura al final (límite absoluto: 12:30) |
| Subida lenta (PR04, PR06, PR07: 100–220 MB) | Empezar el `git push` apenas termine el commit; validar mientras sube |
| `npm ci` avisa de un lockfile dañado | Ver §7 (se resuelve en PR02 con un commit propio) |
| Falta Godot 4.7.2 en algún equipo | La validación Godot la hace ManuelRUa (PR05, PR08) y la auditoría la informa como aviso |
| Alguien necesita el APK firmado | Solo ManuelRUa tiene la llave (`movil/claves/`, fuera del repositorio) |

## 7. Pendientes detectados en la inspección

- `package-lock.json`: en el ensayo `npm ci` avisó "invalid or damaged lockfile", pero la instalación terminó y
  `next build` compiló bien (2026-11-27 09:5x, clon limpio). No se toca durante la migración; si en algún equipo
  `npm ci` falla, se corrige después con un PR aparte (`npm install` y lockfile nuevo).
- Licencia del modelo de caballo ROME (three.js): verificarla antes de un uso comercial.
- `godot/export_presets.cfg` se versiona porque no tiene contraseñas (la auditoría lo comprueba).
