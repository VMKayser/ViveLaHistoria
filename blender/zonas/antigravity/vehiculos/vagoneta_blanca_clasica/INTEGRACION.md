# Integración · Vagoneta Blanca Clásica (`vagoneta_blanca_clasica`)

Contrato completo para cargar, conducir, recolorear e integrar la vagoneta en Three.js / Mi Ciudad sin depender de la sesión de modelado.

## 1. Archivos publicados

Directorio público:

```text
web/public/models/ciudad/antigravity/vehiculos/vagoneta_blanca_clasica/
```

URL servida por Next.js (`cd web && npm run dev`):

<http://localhost:3000/models/ciudad/antigravity/vehiculos/vagoneta_blanca_clasica/index.html>

| Variante | GLB listo para producción | Blender editable (`.blend`) | Pintura sRGB |
|---|---|---|---|
| **Blanca clásica** *(maestro)* | `vagoneta_blanca_clasica.glb` / `vagoneta_blanca_clasica_blanca.glb` | `vagoneta_blanca_clasica.blend` / `vagoneta_blanca_clasica_blanca.blend` | `#f2ece4` |
| **Celeste años 90** | `vagoneta_blanca_clasica_celeste.glb` | `vagoneta_blanca_clasica_celeste.blend` | `#6d8fa8` |
| **Guinda clásico** | `vagoneta_blanca_clasica_guinda.glb` | `vagoneta_blanca_clasica_guinda.blend` | `#8c2f39` |
| **Verde botella** | `vagoneta_blanca_clasica_verde.glb` | `vagoneta_blanca_clasica_verde.blend` | `#356354` |

Los cuatro `.glb` comparten **exactamente el mismo bloque binario** (geometría, normales, UV, textura normal CC0 `Rubber004` empaquetada y clips NLA). Solo cambia el material de pintura exterior (`muro__rrggbb`), manteniendo intactos los parachoques oscuros (`#2b313f`), gomas, cristales, faros, pilotos y llantas de acero.

Módulos y metadatos junto al GLB:
- `cinematica_vehiculo.mjs`: controlador cinemático Ackermann + adaptador `VehiculoAnimado` para Three.js.
- `colores_vehiculo.mjs`: cambio de pintura por instancia (`WeakMap`) sin contaminar otras instancias.
- `vagoneta_blanca_clasica.ficha.json`: conteos geométricos, límites en metros y registro de recursos.
- `vagoneta_blanca_clasica.variantes.json`: catálogo con SHA-256, tamaños y paletas.
- `index.html`, `visor.bundle.js`, `THREE-LICENSE.txt`: visor autónomo de inspección y conducción.

## 2. Escala, ejes y jerarquía

| Propiedad | Valor |
|---|---|
| Unidades | Metros, segundos, radianes |
| Carrocería (estimada desde diseño) | `4,32 m` largo × `1,70 m` ancho (`~1,98 m` con espejos) × `1,53 m` alto |
| Radio de rodadura (`radio_rueda`) | `0,320 m` |
| Ejes (`[eje_trasero, eje_delantero]`) | `[-1,17 m, +1,13 m]` (batalla `2,30 m`) |
| Semivía (`semivia`) | `0,725 m` (vía `1,45 m`) |
| Origen | Centro longitudinal a ras del suelo (`Y = 0` en GLB, `Z = 0` en Blender) |
| Convención GLB / Three.js | `+X` frente, `+Y` arriba, `+Z` derecha |

Jerarquía garantizada:

```text
vagoneta_blanca_clasica (userData.movimiento incluido)
├── carroceria / interior / cristales / decoracion
├── direccion_delantera_derecha
│   └── rueda_delantera_derecha
├── direccion_delantera_izquierda
│   └── rueda_delantera_izquierda
├── rueda_trasera_derecha
└── rueda_trasera_izquierda
```

Clips NLA portables incluidos en el GLB: `rodar_adelante` y `rodar_atras` (25 muestras, 1 vuelta exacta en 1,0 s).

## 3. Uso en Three.js

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VehiculoAnimado } from './cinematica_vehiculo.mjs';
import { aplicarVariante } from './colores_vehiculo.mjs';

const BASE = '/models/ciudad/antigravity/vehiculos/vagoneta_blanca_clasica';
const loader = new GLTFLoader();
const gltf = await loader.loadAsync(`${BASE}/vagoneta_blanca_clasica.glb`);
const catalogo = await fetch(`${BASE}/vagoneta_blanca_clasica.variantes.json`).then(r => r.json());
const paletas = Object.fromEntries(catalogo.variantes.map(v => [v.id, v]));

// Instanciar y conducir:
const instancia = gltf.scene.clone(true);
aplicarVariante(instancia, 'blanca', paletas, { nombreRaiz: 'vagoneta_blanca_clasica' });
escena.add(instancia);

const auto = new VehiculoAnimado(instancia, null, 'vagoneta_blanca_clasica');
auto.teletransportar({ x: 12, y: alturaCalzada, z: -4, rumbo: 0 }, true);
auto.entrada({ velocidad: 25 / 3.6, direccion: 0.08 }); // m/s y rad (+izquierda)

// En cada fotograma del bucle principal:
auto.actualizar(dt);
```

Para rutas parametrizadas por longitud de arco sobre el eje trasero, llamar `auto.avanzarDistancia(ds, curvatura)` en lugar de `auto.actualizar(dt)`. No usar `AnimationMixer` simultáneamente sobre las ruedas.

## 4. Límites y qué queda a cargo del sistema urbano

- Modelo cinemático sobre plano horizontal: el seguimiento de carriles, semáforos, pendientes 3D sobre la calzada y colisiones pertenecen al sistema de tráfico de la ciudad.
- No registrar este GLB en manifiestos estáticos de manzanas ni fusionar sus ruedas con la carrocería.
- Medidas deducidas de las proporciones de la lámina y fotografía original; interior interpretado con sobriedad para acompañar la vista exterior.

## 5. Regeneración y validación desde fuentes

```bash
# 1. Construir maestro (.glb, .blend, ficha y renders de revisión con GPU NVIDIA):
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia \
  ~/apps/blender-5.2.3-linux-x64/blender -b -t 2 \
  -P blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/construir_vagoneta.py

# 2. Generar variantes GLB y copias Blender sin reconstruir geometría:
python3 .agents/skills/vehiculo-3d-desde-diseno/scripts/generar_variantes_glb.py \
  --datos blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/vagoneta_blanca_clasica.json \
  --maestro web/public/models/ciudad/antigravity/vehiculos/vagoneta_blanca_clasica/vagoneta_blanca_clasica.glb \
  --salida web/public/models/ciudad/antigravity/vehiculos/vagoneta_blanca_clasica

~/apps/blender-5.2.3-linux-x64/blender -b \
  web/public/models/ciudad/antigravity/vehiculos/vagoneta_blanca_clasica/vagoneta_blanca_clasica.blend -t 2 \
  -P blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/variantes_blender.py

# 3. Empaquetar visor autónomo:
cp .agents/skills/vehiculo-3d-desde-diseno/scripts/cinematica_vehiculo.mjs \
   .agents/skills/vehiculo-3d-desde-diseno/scripts/colores_vehiculo.mjs \
   blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/
node .agents/skills/vehiculo-3d-desde-diseno/scripts/empaquetar_visor.cjs \
  --entrada blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/visor.js \
  --salida web/public/models/ciudad/antigravity/vehiculos/vagoneta_blanca_clasica \
  --copiar blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/cinematica_vehiculo.mjs \
  --copiar blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/colores_vehiculo.mjs \
  --copiar blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/INTEGRACION.md

# 4. Validar GLB, variantes y pruebas unitarias:
node .agents/skills/vehiculo-3d-desde-diseno/scripts/validar_glb_vehiculo.mjs \
  --glb web/public/models/ciudad/antigravity/vehiculos/vagoneta_blanca_clasica/vagoneta_blanca_clasica.glb \
  --datos blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/vagoneta_blanca_clasica.json \
  --reporte revisiones/antigravity/vagoneta_blanca_clasica/validacion_gltf.json
node blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/validar_variantes.mjs
node --test blender/zonas/antigravity/vehiculos/vagoneta_blanca_clasica/movimiento_y_colores.test.mjs
```
