# MiCiudad Sucre — app móvil (Android, Godot 4.7)

**El proyecto ya no está aquí:** desde el 2026-11-25 la web (PC) y la app son el mismo proyecto Godot, `ciudad3d/`
(ver `ciudad3d/LEEME.md`). Aquí quedan el APK (`build/`), la llave de firma (`claves/`) y esta guía de la app.

La misma ciudad de la versión web (`web/`), pero en el teléfono: pantalla de inicio con carga, recorrido a pie con
**joystick digital**, minimapa y nombre de la calle. Todo lo que hay en la web (sin la herramienta de "Revisión", que es de desarrollo).

**APK listo para instalar:** `movil/build/MiCiudad-Sucre.apk` (≈ 50 MB, Android 7+, 64 bits, firmado).

## Descarga para testers (web)
El APK se copia a `web/public/descargas/MiCiudad-Sucre.apk` (no se versiona) y la web lo sirve con `Content-Type:
application/vnd.android.package-archive` y `Content-Disposition: attachment` (`web/next.config.ts`), para que Android lo abra con el
instalador de paquetes y no con WPS u otro lector. La página `/inicio/instalar.html` lleva el botón de descarga y los 3 pasos. Si el
APK se comparte por otro medio (Drive, WhatsApp), el teléfono puede ofrecer lectores de documentos: usar siempre el enlace de la web.

## Identidad
Ícono: campanario de la Catedral sobre verde oscuro (`ciudad3d/herramientas/dibujar_icono.py` lo genera: `ciudad3d/icono.png`,
`ciudad3d/iconos/`). Mismo paquete y misma llave que las versiones anteriores, así que actualiza sobre la instalada.

## Instalar y probar
- Por cable (depuración USB activada): `~/apps/android-sdk/platform-tools/adb install -r movil/build/MiCiudad-Sucre.apk`
- O copia el APK al teléfono, ábrelo y permite "instalar apps de orígenes desconocidos".

## Modo noche
Botón "Noche/Día" arriba a la derecha (se recuerda la última hora): pasa por atardecer y amanecer con fundidos, como la web.

## Cómo se usa
- **Inicio:** la ciudad gira detrás de un velo mientras carga; al terminar se entra a pie (como en la web).
- **A pie:** pulgar izquierdo = caminar (al borde del círculo: correr); cualquier dedo en la mitad derecha = mirar; toque en el
  minimapa = ir a ese punto. Buses con física real circulando por las calles.

## Cómo se arma (si cambia la ciudad)
`cd web && npm run ciudad:apk`: empaqueta los modelos de los agentes (sin navegador ni Blender), convierte los vehículos y exporta
el APK firmado a `movil/build/MiCiudad-Sucre.apk` (plantillas en `~/.local/share/godot/export_templates/4.7.2.stable/`, SDK de
Android en `~/Android/Sdk`). Los datos van dentro del paquete.

## Diferencias con la web (conocidas)
- Sin el filtro "pintado" (Kuwahara): es un pase de pantalla demasiado caro para un teléfono. El resto del aspecto (shader por
  rol, sombras de sol, cielo, niebla, noche) es el mismo código.
- Solo Android 64 bits (arm64-v8a). Sin Vulkan, usa OpenGL ES 3 (el mismo renderizador que la web).

## Llave de firma
`movil/claves/sucre3d.keystore` (contraseña en `ciudad3d/export_presets.cfg` y en `movil/claves/CONTRASENA.txt`; llave nueva del 2026-11-26, la anterior quedó en `movil/claves/retirada_2026-11-26/`) **no se versiona**: guárdala; sin ella no se
puede actualizar una app ya instalada con una versión nueva. Por el cambio de llave, quien tenga instalado un APK anterior al
2026-11-26 tiene que desinstalarlo antes de instalar el nuevo (Android no acepta una actualización firmada con otra llave).

## Pruebas en el escritorio
Ver "Probar sin navegador" en `ciudad3d/LEEME.md` (`--rendering-method mobile` prueba el renderizador del teléfono).
