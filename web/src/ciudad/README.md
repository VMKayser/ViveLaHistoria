# Ciudad (página web)

Desde el 2026-11-25 la ciudad 3D es el proyecto **Godot** `ciudad3d/` (ver `ciudad3d/LEEME.md`), exportado a
WebAssembly en `web/public/ciudad3d/` con `npm run ciudad`. Esta carpeta es solo la **página React** que lo envuelve:
la interfaz va encima del lienzo de Godot y habla con él por el puente `motor/MotorGodot.ts`.

| | |
|---|---|
| `Experiencia.tsx` | página: lienzo `#ciudad3d`, carga del motor, HUD, teclas (T taller, V/B revisiones), `?embebido` |
| `motor/MotorGodot.ts` | carga `sucre.js` + `sucre.wasm`/`.pck`; manda órdenes a `window.sucreGodot` y escucha los eventos `sucre` |
| `motor/EstadoVista.ts` | estado compartido de la vista (posición, rumbo, modo, calle) que lee el HUD |
| `motor/calidad.ts` | nivel de calidad elegido (alta/media/baja) que se pasa a Godot |
| `interfaz/` | pantalla de inicio, minimapa (imagen `ciudad3d/datos/minimapa.webp`), calle actual, ayuda, taller, `SoloEscritorio` (en celular: descarga del APK) |
| `interfaz/revision/`, `revision/` | correcciones del usuario: enmarcar, capturar (la captura la hace Godot), guardar en `coordinacion/revisiones/` |
| `datos/CatalogoModelos.ts` | lista de modelos (manifiestos) para el taller |

Para probar: `cd web && npm run dev` → http://localhost:3000/ciudad (en un celular la página ofrece el APK;
`?escritorio` fuerza la versión web). Después de exportar modelos: `npm run ciudad` y recargar.
