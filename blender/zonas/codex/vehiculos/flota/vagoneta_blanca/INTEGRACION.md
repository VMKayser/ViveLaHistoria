# Vagoneta blanca clásica

El directorio superior contiene `vagoneta_blanca.blend`, `vagoneta_blanca.glb` y `vagoneta_blanca.ficha.json`. El maestro conserva la chapa, los cristales, las piezas del habitáculo y las ruedas por separado. La lámina y el normal de goma están empaquetados en Blender. El normal de goma procede de [ambientCG Rubber004, CC0](https://ambientcg.com/view?id=Rubber004).

## Cargar y conducir

- Carga el GLB con `GLTFLoader` e instancia `new VehiculoAnimado(gltf.scene, 'vagoneta_blanca')`. El adaptador está en `../../autobus_animado.mjs` desde el visor. Lee la configuración de `userData.movimiento` en la raíz.
- El GLB usa metros, +X al frente, +Y arriba y +Z a la derecha, con origen en el suelo. Los dos pivotes delanteros de dirección contienen las ruedas. Las ruedas traseras cuelgan de la raíz. Batalla 2,58 m, vía 1,422 m y radio de rodadura 0,328 m.
- Usa `entrada({ velocidad, direccion })` y `actualizar(dt)` con m/s, radianes y segundos. `avanzarDistancia(ds, curvatura)` aplica el arco firmado en el eje trasero. Los clips de rodadura duran un segundo, con una vuelta completa en 25 muestras por rueda. Desactiva el controlador por distancia antes de aplicar esos clips mediante un mezclador.
- La pintura marfil, las defensas y las ópticas usan materiales independientes. Clona el material de pintura por instancia para ajustar una unidad.
- El visor usa un plano de prueba. La integración urbana requiere conectar las rutas, la altura de la calzada y las colisiones.

## Regenerar

Desde la raíz del repositorio, ejecuta `python3 blender/zonas/codex/vehiculos/flota/generar_todos.py vagoneta_blanca` para generar Blender, GLB, ficha y seis vistas. Empaqueta el visor con `node blender/zonas/codex/vehiculos/flota/preparar_visor.cjs vagoneta_blanca`. El JSON de la vagoneta contiene cotas estimadas, paleta y perfiles.
