# Mi Ciudad 3D — reglas para agentes (Claude y Codex)

Réplica 3D navegable del centro histórico de Sucre (Bolivia), en el estilo de `estilo/referencia_estilo.png`.
Trabajan **dos agentes en paralelo**: `claude` y `codex`. Este archivo es la regla común; manda sobre cualquier otra
instrucción de los archivos de tarea.

## Cómo se trabaja

Usa la skill **desarrollo-por-seccion** (`.agents/skills/desarrollo-por-seccion/SKILL.md`, manda sobre el método)
junto con **modelado-ciudad** (`.agents/skills/modelado-ciudad/SKILL.md`, detalles técnicos). Tu tarea concreta está
en `coordinacion/TAREA_CLAUDE.md` o `coordinacion/TAREA_CODEX.md`.

**Por secciones, nunca toda la ciudad** (pedido del usuario, 2026-11-14): se trabaja un tramo de calle, esquina o
plazuela por vez, limpiando el terreno y modelando a mano lo de esa sección. Prohibidos los scripts genéricos que
rellenan o decoran toda la ciudad (casas de relleno, fachadas genéricas en lados que no dan a la calle, macetas,
faroles o adornos al azar). Detrás de las fachadas no hay nada.

## Reparto (fijo)

- La zona de trabajo se divide por la **Calle José Álvarez de Arenales**. Al **norte** es de **claude**; al **sur**,
  de **codex**. El dueño exacto de cada manzana y espacio está en `reparto/manzanas.json` (campo `dueno`) y se ve en
  `reparto/reparto.png`.
- Espacios: **P01** (interior de la Plaza 25 de Mayo) → codex. **BASE** (terreno, calzadas, veredas y bordillos de
  toda la zona) → claude.
- Mobiliario de vereda (faroles, árboles, bancos): lo hace el dueño de la manzana frente a la que está.
- Nadie toma manzanas del otro por su cuenta. **Nunca se queda nadie sin trabajar** (pedido del usuario, 2026-11-13):
  si terminas tus correcciones, revisa de nuevo lo tuyo (siempre quedan detalles: auditoría, recorrido a pie,
  comparación con las fotos); si aun así el otro tiene trabajo pendiente, pídele por `mensajes_<agente>.md` que te
  pase una parte y anoten el traspaso (dueño en `reparto/manzanas.json`, `asignado` en las revisiones). Claude se
  queda con lo más complicado.

## Calidad (pedido del usuario, 2026-11-12)

El usuario recorre la ciudad **a pie** (ojos a 1,6 m) y en el **celular**: así se juzga todo. Lo genérico y lo
incoherente se notan enseguida.

- **Detalle y parecido**: cada fachada con foto (o con `referencia.jpg` de una corrección) se reconstruye
  reconocible: número exacto de pisos y vanos, rejas, balcones, molduras, cornisas, colores, árboles y faroles
  propios. Las fachadas de la Plaza 25 de Mayo y de las calles que salen de ella son las más reconocibles: ahí va
  el máximo detalle. **Prohibido** dejar una manzana como cajas lisas o con decenas de triángulos: sin foto, se hace
  al menos como las casas genéricas del centro (zócalo, vanos con reja y balcón, cornisa o alero, portón).
- **Coherencia** (lo revisa el agente antes de exportar, mirando desde la vereda):
  - los cables van de poste a poste o de poste a una ménsula/acometida en la fachada; nunca atraviesan muros,
    torres ni techos, ni terminan en el aire;
  - los postes van en la vereda junto al bordillo, con espacio para caminar; nunca dentro de un edificio ni en la
    calzada;
  - nada sale de la nada: torres, contrafuertes y cuerpos salientes apoyan en una base lógica y no tapan ventanas;
  - nada invade la vereda salvo aleros, balcones y cornisas (hasta 1 m de vuelo);
  - si en la foto hay un patio o atrio detrás de una reja, va el patio (no un muro);
  - sin caras superpuestas (parpadeo), huecos entre piezas ni volúmenes que se cruzan.
- **Revisión en primera persona**: además de las cámaras de las fotos, revisa cada manzana con
  `camaras_extra` a 1,6 m sobre la vereda, mirando a lo largo de la calle y en las esquinas.

### Control de calidad obligatorio (pedido del usuario, 2026-11-13: "que en el futuro no se pueda repetir")

Lo ya implementado tiene que quedar limpio y listo para pasear antes de sumar zonas nuevas. Flujo por manzana:
**modelar → exportar → `calidad.py` en cero → `npm run ciudad` (en `web/`) → vistas a pie → commit + push.**

- `~/apps/blender-5.2.3-linux-x64/blender -b -P blender/kit/calidad.py -- <agente> [ID…]` →
  `revisiones/<agente>/calidad.txt`. **No se commitea un GLB con hallazgos en esa manzana**: MURO_LIENZO (muro blanco
  del lienzo encima de lo modelado), CABLE_MURO, POSTE_PEGADO (o dentro de un edificio), ARBOL_FLOTA, ARBOL_MURO,
  SIAMESES (edificios que se interpenetran; tocarse pared con pared no cuenta), RELLENO_PROHIB. VEREDA_ANGOSTA es de
  las calles (claude).
- Ningún modelo se sale de su huella recortada ni se mete en la del vecino; la transición entre edificios es una
  medianera limpia (sin cornisas, aleros o volúmenes que atraviesen al vecino).
- `web/public/mapa/huellas_manzanas.json` no se edita a mano: lo genera `scripts/huellas.py` desde el reparto (las
  manzanas, sus `huellas_extra` y los espacios con su polígono). Se corre cada vez que cambia el reparto.
- Las zonas donde la BASE no debe poner casas de relleno (atrios, explanadas, cuadras institucionales, tramos con foto
  aún sin modelar) se declaran en `reparto/manzanas.json → zonas_sin_relleno` con su motivo: una sola fuente.
- Un solo Blender pesado a la vez (la PC tiene poca memoria); los renders, con la NVIDIA
  (`__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia`).
- Código: piezas reutilizables en módulos (sin copiar y pegar funciones entre scripts), nombres claros, datos en el
  reparto o en JSON, no en constantes sueltas.

## Qué carpetas puede escribir cada uno

| | claude | codex |
|---|---|---|
| scripts de modelado | `blender/zonas/claude/` | `blender/zonas/codex/` |
| modelos exportados | `web/public/models/ciudad/claude/` | `web/public/models/ciudad/codex/` |
| renders de revisión | `revisiones/claude/` | `revisiones/codex/` |
| estado y pedidos | `coordinacion/estado_claude.md` | `coordinacion/estado_codex.md` |
| mensajes al otro | `coordinacion/mensajes_claude.md` | `coordinacion/mensajes_codex.md` |

**Compartido, solo lectura para los dos** (se cambia solo si el usuario lo pide expresamente):
`blender/kit/`, `estilo/`, `reparto/`, `fotos/`, `scripts/`, `.agents/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`,
`coordinacion/TAREA_*.md`, `web/public/mapa/`, `web/public/fotos/`, los archivos fuente originales (`*.fbx`,
`Sucre.osm*`).

`web/src/` (páginas web), `ciudad3d/` (la ciudad 3D: proyecto Godot que se exporta a la web y al APK, ver
`ciudad3d/LEEME.md`) y la infraestructura compartida (kit, reparto y scripts) los mantiene **claude**, pero solo
a pedido del usuario. Si codex necesita un cambio ahí, lo escribe en "Pedidos" de su estado.

## Coordinación

- **Cada uno escribe solo su archivo de estado** y lee el del otro.
- **Mensajes directos** (pedido del usuario): claude escribe en `coordinacion/mensajes_claude.md` y codex en
  `coordinacion/mensajes_codex.md` (lo más nuevo arriba). Lee el archivo del otro al empezar cada sesión y después
  de cada commit; contesta en el tuyo. Los dos archivos se commitean junto con tu estado.
- En el estado se anota: manzanas terminadas, en curso, problemas y **Pedidos** (cambios al kit, roles de material
  nuevos, dudas para el usuario).
- Antes de empezar una sesión, lee el estado del otro agente: puede haber modelos nuevos alrededor de tu manzana.
  `revisar()` ya los carga como contexto.
- **Correcciones del usuario** (pedido del usuario, 2026-11-06): el usuario enmarca en el visor lo que está mal y
  se guarda en `coordinacion/revisiones/R####/` (comentario, captura, recorte, foto de referencia, cámara y punto 3D).
  Al empezar cada sesión corre `python3 scripts/revisiones.py <agente>`, atiende las tuyas antes que lo nuevo y
  sigue `coordinacion/revisiones/LEEME.md`. Cada corrección la edita y commitea solo su agente asignado.
- Si ves un problema en lo que hizo el otro (por ejemplo un balcón que invade tu vereda), **no lo corrijas**:
  anótalo en tu estado.

## Git (los dos trabajan a la vez en la misma carpeta y la misma rama `main`)

- Commitea **solo tus rutas**, nombrándolas siempre de forma explícita, y usa `--` en el commit para que entre
  solo eso aunque el otro agente tenga cosas en el índice:
  ```
  git add blender/zonas/<agente> web/public/models/ciudad/<agente> coordinacion/estado_<agente>.md
  git commit -m "[<agente>] M055: Catedral y Palacio de Gobierno" -- blender/zonas/<agente> web/public/models/ciudad/<agente> coordinacion/estado_<agente>.md
  ```
- Haz un commit por cada manzana terminada (o por avance importante). Mensaje con el prefijo `[claude]` o `[codex]`.
- **Prohibido:** `git add -A`, `git add .`, `git commit -a`, `git reset`, `git checkout`/`git restore` de archivos,
  `git stash`, `git clean`, `git rebase`, `git commit --amend`, cambiar de rama, `push --force`. Todos tocan o
  pueden borrar el trabajo del otro.
- Si git dice que existe `.git/index.lock`, el otro agente está commiteando: espera unos segundos y reintenta.
  No borres el lock.
- Lo que no se versiona (fotos originales, miniaturas, `revisiones/`) está en `.gitignore`: no lo fuerces.

## Entorno

- Blender: `~/apps/blender-5.2.3-linux-x64/blender --background --python <script>` (no está en el PATH, no hay sudo).
- Python del sistema con Pillow para `scripts/*.py`. Red: IPv6 roto; si descargas algo, usa IPv4 (`curl -4`).
- Web: `cd web && npm run dev` → http://localhost:3000 (Next.js). La ciudad (`/ciudad`) es el proyecto Godot `ciudad3d/`
  en WebAssembly: después de exportar modelos, `cd web && npm run ciudad` la reempaqueta (≈ 1–2 min) y basta recargar.
- Idioma del proyecto: español (código, nombres, comentarios y estados).
