# Mi Ciudad Sucre

Réplica 3D navegable del centro histórico de Sucre (Bolivia), con personajes históricos con los que se conversa,
tráfico, el museo Casa de la Libertad y el recorrido interactivo del 25 de mayo de 1809.

> La organización del repositorio y su incorporación están en [`MIGRATION_PLAN.md`](MIGRATION_PLAN.md).
> Instrucciones para asistentes de programación: [`AGENTS.md`](AGENTS.md).

## Requisitos

- **Git LFS** 3.x (`git lfs install` antes de clonar; los modelos, texturas y voces viajan por LFS).
- **Node.js** 20 o posterior.
- **Python** 3.10 o posterior, con `numpy` y `Pillow` (`pip install numpy pillow`).
- **Godot 4.7.2** con las plantillas de exportación 4.7.2. Su ruta va en la variable `GODOT` (por defecto,
  `~/apps/godot/Godot_v4.7.2-stable_linux.x86_64`).
- **Blender 5.2**: solo para regenerar modelos.

## Instalar y ejecutar

```bash
git clone git@github.com:antrak13/Mi_Ciudad_Sucre.git && cd Mi_Ciudad_Sucre && git lfs pull

# Web (portada, mapa y página de la ciudad)
cd web && npm ci && npm run dev                 # http://localhost:3000

# Ciudad 3D: empaqueta los modelos y exporta Godot a la web (1–2 min)
cp ../ciudad3d/export_presets.ejemplo.cfg ../ciudad3d/export_presets.cfg   # una sola vez
GODOT=/ruta/a/Godot_v4.7.2 npm run ciudad       # luego abrir http://localhost:3000/ciudad

# APK de Android (necesita la llave de firma, que no se versiona)
GODOT=/ruta/a/Godot_v4.7.2 npm run ciudad:apk

# Ciudad Charcas 1809 (proyecto Godot independiente)
godot --path godot                              # ver docs/CIUDAD_CHARCAS_1809.md
```

## Estructura

| Carpeta | Contenido |
|---|---|
| `web/` | Aplicación Next.js: portada, `/ciudad`, `/mapa`, revisiones |
| `ciudad3d/` | Proyecto Godot de la ciudad (web y APK): motor, shaders, personajes, encuentros, tráfico, escenas históricas (ver `ciudad3d/LEEME.md`) |
| `web/public/models/`, `blender/` | Modelos GLB de la ciudad y scripts de Blender que los generan |
| `web/public/mapa/`, `reparto/`, `estilo/`, `scripts/`, `Sucre.osm.*` | Datos urbanos, reparto de manzanas y estilo |
| `personas/`, `contenido/` | Modelos de personajes, guiones y voces de los encuentros, contenido histórico |
| `museo_interior/` | Interior de la Casa de la Libertad (Blender) |
| `godot/`, `herramientas/` | Ciudad Charcas 1809 |
| `autos/`, `web/public/trafico/` | Vehículos y red vial |
| `movil/` | Guía de la app Android |
| `migracion/` | Manifiesto, incorporación y auditoría del repositorio |

## Licencias de terceros

Las texturas y cielos CC0 (Poly Haven), MakeHuman (CC0), las animaciones de Quaternius (CC0), las fuentes OFL y los
modelos con licencia propia están listados en `recursos/LICENCIAS.md` y `godot/CREDITOS.md`, y cada paquete conserva su
archivo de licencia.
