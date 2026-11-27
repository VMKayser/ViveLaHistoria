# Gemini — Mi Ciudad Sucre

Lee **`MIGRATION_PLAN.md` completo** y luego **`AGENTS.md`** antes de ejecutar cualquier operación: sus reglas son
obligatorias también para ti (organización, integración, consistencia temporal, verificación y cuándo continuar).
Solo ejecutas los PR del integrante dueño de la sesión (`gh api user -q .login` → `migracion/equipo.json`).

## Configuración obligatoria de Gemini CLI

- No agregues firmas, trailers `Co-authored-by` ni menciones a Gemini en commits, títulos o descripciones de PR. Si
  tu configuración agrega alguna atribución automática, desactívala antes de commitear. El hook
  `migracion/hooks/commit-msg` rechaza los mensajes con atribuciones.
- Hoy se trabaja en **modo automático** (`AGENTS.md` §Modo automático): el integrante ya autorizó que `auto.py` haga
  push, PR y merge de **sus** PR. Tú lo lanzas en segundo plano, vigilas `~/mic-migracion.log` y le informas.
  Cualquier otro push, PR o merge fuera de `auto.py` necesita su confirmación.
- Los comandos de shell de Gemini CLI tienen un tiempo máximo: lanza `auto.py` con `nohup … &` y consulta el log; no
  lo ejecutes en primer plano.

## Forma de trabajo

- Sigue el flujo de tu PR paso a paso:
  rama → `python3 -I migracion/incorporar.py <PR> --origen ~/mic-origen` → commits del plan (con `git add` de rutas
  explícitas) → `python3 -I migracion/auditar.py --hasta <PR>` → push → PR → validaciones → merge.
- No modifiques archivos incorporados ni sus metadatos internos. Inspecciona e informa (`migracion/metadatos.py`).
- Muestra la salida real de cada validación. Si algo falla y el plan no lo cubre, detente e informa.
