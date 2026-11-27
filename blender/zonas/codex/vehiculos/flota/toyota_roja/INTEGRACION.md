# Toyota roja de cabina extendida

El paquete incluye `toyota_roja.glb`, el maestro editable `toyota_roja.blend` y `toyota_roja.ficha.json` en el directorio superior. El maestro conserva por separado la chapa, las ópticas, los marcos, la caja, el habitáculo, los neumáticos y las llantas. La referencia y el normal de goma están empaquetados en Blender. El normal es [ambientCG Rubber004, CC0](https://ambientcg.com/view?id=Rubber004).

## Carga y movimiento

- Carga `toyota_roja.glb` con `GLTFLoader` y pasa `gltf.scene` junto con el identificador `toyota_roja` a `VehiculoAnimado`, en `../../autobus_animado.mjs` desde el visor. La configuración está en `userData.movimiento` de la raíz.
- El GLB usa metros, +X hacia delante, +Y hacia arriba, +Z hacia la derecha y origen en el suelo. Los pivotes delanteros de dirección contienen las ruedas correspondientes. Las traseras cuelgan de la raíz. Radio 0,445 m, batalla 3,05 m y vía 1,59 m.
- Usa `entrada({ velocidad, direccion })` y `actualizar(dt)` para conducir con velocidad en m/s, giro en radianes y tiempo en segundos. `avanzarDistancia(distancia, curvatura)` aplica un arco firmado de referencia al eje trasero.
- `rodar_adelante` y `rodar_atras` son clips de una vuelta en un segundo, con 25 muestras por rueda. Úsalos con un mezclador de animación solo cuando el controlador cinemático esté desactivado.
- La pintura roja, las franjas y las ópticas tienen materiales independientes. Para cambiar el rojo en una instancia, clona los materiales `pintura` y `pintura_sombra` de esa instancia antes de modificar su color.
- La integración al tráfico queda pendiente de asignar rutas, apoyar las ruedas en la pendiente de la calzada y conectar las colisiones. La conducción del visor usa un plano de prueba.

## Regeneración

Desde la raíz del proyecto, usa `python3 blender/zonas/codex/vehiculos/flota/generar_todos.py toyota_roja` para reconstruir el maestro, el GLB, la ficha y las seis vistas. Empaqueta el visor con `node blender/zonas/codex/vehiculos/flota/preparar_visor.cjs toyota_roja`. Los parámetros de este diseño se guardan en `toyota_roja/toyota_roja.json`.
