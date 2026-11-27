---
name: vehiculo-3d-desde-diseno
description: >-
  Crear, corregir, riggear, validar y entregar modelos 3D funcionales de vehículos
  (autos, vagonetas, camionetas, minibuses, autobuses) en Blender y GLB a partir de
  láminas de diseño, vistas o fotografías, con ruedas volumétricas, dirección Ackermann,
  rodadura por distancia, variantes de pintura, visor interactivo y contrato de integración.
  Usar cuando se pida modelar un vehículo 3D desde imagen/diseño o preparar sus ruedas,
  acabados y exportación; no usar para edificios, logos sueltos ni sistemas de tráfico urbano.
---

# Vehículo 3D desde Diseño

Produce un vehículo 3D reconocible, a escala humana en metros, editable en Blender (`.blend`) y listo para producción en `.glb`, con jerarquía de dirección/rodadura, clips portables, controlador cinemático independiente de los FPS, visor web de prueba y documentación de integración.

> **Principio rector:** Extraer la identidad geométrica propia de cada vehículo (silueta, proporciones, curvaturas, vanos, pilares, ópticas y llantas). Nunca deformar un vehículo anterior ni pintar colores sobre cajas lisas. Separar siempre lo observado en la referencia de lo interpretado en vistas ocultas.

---

## 1. Detección de entorno y convivencia segura

Antes de modelar:

1. **Inspeccionar el workspace:** leer `AGENTS.md` (si existe), detectar rutas propias del agente, guía de estilo/paleta y dependencias locales (`gltf-validator`, `three`, empaquetador).
2. **Detectar herramientas y recursos:** ejecutar:
   ```bash
   python3 .agents/skills/vehiculo-3d-desde-diseno/scripts/detectar_entorno.py
   ```
   - Nunca incrustar nombres de usuario del sistema en scripts reutilizables.
   - Si hay sesiones activas de Blender (p. ej. otro agente usando MCP) o poca RAM libre, ejecutar **un único proceso Blender en segundo plano a la vez** limitando hilos (`blender -b -t 2 -P ...`) y sin tocar escenas ajenas.
   - Si existe GPU NVIDIA, renderizar revisiones con `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia`.
3. **Aislamiento urbano:** no registrar el vehículo en manifiestos de manzanas/edificios ni fusionarlo con lotes estáticos. El código y el JSON de datos son la única fuente de verdad.

---

## 2. Flujo obligatorio paso a paso

### Paso A — Inventariar la referencia antes de modelar
Examinar la lámina completa y contrastar con fotografías originales si existen. Registrar en un archivo `<vehiculo>.json` e `INVENTARIO.md`:
- **Gobierno de vistas:** fijar qué vista manda en cada dimensión (el perfil gobierna largo, batalla, voladizos, altura de techo, cintura y vanos; frente y trasera gobiernan ancho, caída de invernadero/tumblehome, parrilla, ópticas y matrículas).
- **Cotas estimadas en metros:** largo, ancho de carrocería, alto, posiciones de ejes `[eje_trasero, eje_delantero]`, `radio_rueda`, `centro_rueda_z` y `semivia_ruedas`. Declarar explícitamente que son estimaciones si no hay plano acotado.
- **Elementos de identidad:** cantidad exacta de puertas y ventanas laterales, inclinación de pilares (A/B/C/D), curvatura de capó/techo, parachoques, molduras, manillas, espejos, limpiaparabrisas, faros, intermitentes, pilotos traseros, tipo de llanta (número real de perforaciones y tuercas) y paleta sRGB.
- **Límites documentados:** qué lados o detalles interiores fueron interpretados.

### Paso B — Coordenadas, estructura modular y nombres semánticos
- **Unidades:** metros, origen `(0, 0, 0)` a nivel del suelo en el centro longitudinal del cuerpo.
- **Ejes:**
  - Blender: `+X` frente, `+Y` izquierda, `+Z` arriba.
  - GLB / Three.js (`export_yup=True`): `+X` frente, `+Y` arriba, `+Z` derecha.
- Separar datos (`<id>.json`), construcción de carrocería/acabados (`construir_<id>.py`) y utilidades reutilizables ([scripts/kit_vehiculo_bpy.py](scripts/kit_vehiculo_bpy.py)). Nombrar cada objeto por su función real (`Capo`, `Pilar A`, `Faro delantero`), nunca `Cube.001`.

### Paso C — Silueta, volúmenes orgánicos y curvas 3D (antes que los adornos)
Consultar detalles en [references/geometria_y_materiales.md](references/geometria_y_materiales.md).
- **Prohibido modelar apilando o cortando cubos y planos diagonales:** la carrocería de un vehículo real no tiene paredes laterales verticales ni quiebres rectos de regla en capó, pilares o cola. Construir **superficies continuas en barril 3D** (`crear_superficie_grid` / lofts bicúbicos) con curvatura simultánea en alzado, planta y sección transversal:
  - Sección transversal curva continua desde el faldón inferior recogido (*rocker roll-under*), panza de puerta con moldura/cintura redondeada, invernadero curvado (*tumblehome*) y techo abovedado con hombros amplios.
  - Morro con caída progresiva (*bullnose*) y aletas que envuelven suavemente ópticas de esquinas redondeadas y lentes abombadas.
  - Parachoques volumétricos en 3D reales: repisa superior entrante bajo carrocería, barra/cojín principal sobresaliente y faldón inferior decididamente recogido hacia adentro (*tuck-under*), nunca una cinta vertical plana.
  - Pasos de rueda con **aleta abombada (*fender flare*) y labio de chapa volteado hacia adentro**, y accesorios (espejos en gota, manillas en cuenco ovalado, asientos) suavizados con subdivisión (`suavizar_subsurf`).
- Cerrar encuentros críticos (cintillo techo/parabrisas, pilares A/B/C/D curvados sobre el barril, portón abombado) con transiciones tangentes y sin caras coplanares.
- Controlar bordes duros por ángulo (`~58°` en chapa curva, `~78°` en llantas torneadas) para preservar reflejos continuos sin contaminar con el canto interior.

### Paso D — Aberturas reales, pasos de rueda e interior sobrio
- Ventanas con hueco real en la carrocería, burlete/marco perimetral y cristal translúcido separado en el grupo `cristales`.
- Recortar los pasos de rueda tanto en la chapa como en las molduras laterales; cerrar la bóveda interior del guardabarros y el piso para que no se vea luz de lado a lado ni el neumático atraviese el habitáculo.
- Modelar únicamente el interior visible a través de los cristales (piso oscuro, asientos con apoyacabezas, tablero, volante, espejo interior y maletero si es vagoneta/hatchback). Si el diseño tiene puerta abierta, incluir caja de peldaños y pivote propio.

### Paso E — Ruedas y llantas volumétricas
- Neumático por revolución (`crear_torno` / `construir_ruedas_volumetricas`): talón, flanco convexo, hombro, canales longitudinales y cortes de banda reales.
- Costura UV situada abajo (contacto con el suelo `t = -π/2`), soldando vértices geométricos (`remove_doubles`) mientras se preservan las esquinas UV para evitar rayas en el flanco.
- Llanta por revolución con plato cóncavo/escalonado, **perforaciones de ventilación abiertas mediante booleana real**, buje central, arandelas y tuercas según el diseño.
- Si se añade microrelieve de goma (normal map OpenGL con licencia CC0 registrada), empaquetarlo dentro del `.blend` y `.glb`, conservar tangentes/UV solo en el neumático y mantener albedo limpio sin iluminación horneada.

### Paso F — Materiales, paleta y variantes
- Respetar la paleta y estilo del proyecto (albedo limpio, sin negro puro `#000000`, sin sombras pintadas).
- Consolidar mallas por `(pivote_padre, material)` para minimizar llamadas de dibujo móviles sin fusionar nunca las ruedas con la carrocería.
- Si se entregan variantes de color, generar los `.glb` con [scripts/generar_variantes_glb.py](scripts/generar_variantes_glb.py) conservando intacto el bloque binario del maestro (convirtiendo hex sRGB a lineal en `baseColorFactor`), y clonar materiales por instancia en web con [scripts/colores_vehiculo.mjs](scripts/colores_vehiculo.mjs).

### Paso G y H — Rig exacto, clips NLA y cinemática Ackermann
Consultar fórmulas y contrato en [references/cinematica_y_rig.md](references/cinematica_y_rig.md).
- Jerarquía obligatoria bajo la raíz `<id_vehiculo>`:
  - Estáticos: `carroceria`, `interior`, `cristales`, `decoracion` (y pivotes extra opcionales como `puerta_pivote`).
  - Delanteras: `direccion_delantera_derecha` → `rueda_delantera_derecha`, `direccion_delantera_izquierda` → `rueda_delantera_izquierda`.
  - Traseras: `rueda_trasera_derecha`, `rueda_trasera_izquierda`.
- Pivotes centrados exactamente en `(x_eje, ±semivia, centro_rueda_z)`.
- Exportar pistas NLA `rodar_adelante` y `rodar_atras` con **25 muestras en 1 s** (evita el fallo de 0°→360° con dos quaternions iguales).
- En tiempo real usar [scripts/cinematica_vehiculo.mjs](scripts/cinematica_vehiculo.mjs): referencia en el eje trasero, dirección Ackermann, arco individual por rueda (`rodadura = -distancia / radio`), frenada previa al invertir marcha y pasos internos `<= 1/120 s`. No mezclar `AnimationMixer` con el controlador por distancia.

### Paso I y J — Verificación rigurosa, visor y entrega
Revisar la tabla de prevención en [references/fallos_frecuentes.md](references/fallos_frecuentes.md) antes de cerrar:
1. **Validación geométrica y formato GLB:**
   ```bash
   node .agents/skills/vehiculo-3d-desde-diseno/scripts/validar_glb_vehiculo.mjs \
     --glb <ruta/modelo.glb> --datos <ruta/datos.json>
   ```
   Debe dar **0 errores y 0 advertencias** en `gltf-validator`, 0 triángulos degenerados, sin cámaras/luces de estudio filtradas, clips verificados con vuelta completa `±2π` y contacto firme con el suelo.
2. **Pruebas numéricas de movimiento y colores:** ejecutar pruebas con `node --test` verificando avance, reversa, arcos en curva, Ackermann, frenada, parada sin giro residual, teletransporte e invariancia a 30/60/120 FPS.
3. **Inspección visual de renders:** renderizar en Blender las vistas `perspectiva`, `frente`, `lateral`, `trasera`, `peaton` (a 1,6 m) y `rueda`, y **abrir las imágenes generadas junto a la lámina original** para corregir discrepancias de silueta, ópticas, altura o normales antes de entregar.
4. **Visor interactivo y contrato:** empaquetar el visor con [scripts/empaquetar_visor.cjs](scripts/empaquetar_visor.cjs), comprobar carga del GLB real y entregar `INTEGRACION.md` + `<id>.ficha.json` indicando claramente qué se entrega y qué queda pendiente para el sistema de tráfico de la aplicación.
