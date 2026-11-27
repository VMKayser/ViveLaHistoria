# Ford azul oscuro bicolor

El directorio superior contiene `ford_azul.blend`, `ford_azul.glb` y `ford_azul.ficha.json`. Blender conserva las piezas editables, la lámina y el normal de goma. La textura de goma proviene de [ambientCG Rubber004, CC0](https://ambientcg.com/view?id=Rubber004).

## Cargar y conducir

- Carga `ford_azul.glb` con `GLTFLoader` y crea `new VehiculoAnimado(gltf.scene, 'ford_azul')`. El adaptador está en `../../autobus_animado.mjs` desde el visor. Lee la configuración de `userData.movimiento` en la raíz.
- El GLB usa metros, origen en el suelo, +X al frente, +Y arriba y +Z a la derecha. Los pivotes de dirección delanteros contienen cada rueda. Los de las ruedas traseras cuelgan de la raíz. Radio 0,447 m, batalla 3,19 m y vía 1,67 m.
- `entrada({ velocidad, direccion })` y `actualizar(dt)` reciben m/s, radianes y segundos. `avanzarDistancia(ds, curvatura)` integra la distancia firmada a partir del eje trasero. Los dos clips de rodadura incorporan una vuelta en un segundo y 25 muestras por rueda. Activa el mezclador de clips con el controlador cinemático desactivado.
- El azul de pintura, el azul de molduras y el gris champán son materiales independientes. Clona los materiales por instancia para editar una unidad en Three.js.
- El visor permite inspeccionar y conducir sobre un plano. La integración urbana requiere conectar rutas, altura de calzada y colisiones.

## Regenerar

Desde la raíz ejecuta `python3 blender/zonas/codex/vehiculos/flota/generar_todos.py ford_azul`. Esto genera Blender, GLB, ficha y seis vistas de estudio. Ejecuta `node blender/zonas/codex/vehiculos/flota/preparar_visor.cjs ford_azul` para empaquetar el visor. Los perfiles y cotas se guardan en `ford_azul.json`.
