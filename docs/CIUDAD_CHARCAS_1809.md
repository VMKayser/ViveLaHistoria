# Ciudad Charcas · 25 de mayo de 1809

Recorrido inmersivo en primera persona del **Primer Grito Libertario** en La Plata (hoy Sucre).
No solo se mira: el jugador camina la ciudad, sigue a la escolta que lleva preso a Zudáñez,
corre con Lemoine a San Francisco, sube al campanario, **toca la campana a rebato** y baja a
la plaza con el pueblo, del atardecer a la noche.

Hecho en **Godot 4.7** con el renderer *Compatibility* (el mismo de la versión web).
La ciudad se genera con un script de **Blender 5.2**; las personas son modelos de **MakeHuman
(MPFB 2, CC0)** con ropa de 1809 modelada por script y animaciones propias; texturas y cielos son
CC0 de Poly Haven; el sonido se sintetiza (todo original).

## Cómo probarlo

```bash
# Escritorio (desde la carpeta godot/)
godot --path godot

# Abrir el proyecto en el editor
godot --path godot --editor
```

**Controles:** clic para capturar el ratón · W A S D caminar · Shift correr · E interactuar ·
Q calidad gráfica · Esc soltar el ratón · R reiniciar al final.

### Versión web

```bash
godot --headless --path godot --export-release "Web" ../build/web/index.html
python3 -m http.server -d build/web 8060    # y abrir http://localhost:8060
```

Se exporta **sin hilos**, así que no hace falta configurar cabeceras COOP/COEP: sirve cualquier
hosting estático (itch.io, GitHub Pages, Netlify). La calidad gráfica baja sola si el equipo no
llega a ~27 FPS (resolución 3D, sombras y brillo).

## Los pasos de la historia

| Paso | Qué pasa | Qué hace el jugador |
|---|---|---|
| intro | La Plata, 5 de la tarde. El rumor de la entrega de Charcas a Carlota del Brasil | Aparece frente a la Universidad |
| arresto | Soldados del rey llevan preso a Jaime de Zudáñez | Lo ve pasar y sigue a la escolta hasta la Audiencia |
| llamado | Juan Manuel Lemoine llama a tocar a rebato | Habla con él y lo sigue calle arriba |
| torre | Iglesia de San Francisco | Sube al campanario |
| rebato | La campana despierta a la ciudad; responde la Catedral; cae la noche | Toca la campana al ritmo de su vaivén |
| pueblo | La multitud con antorchas pide al arzobispo que interceda; liberan a Zudáñez | Baja y se une al pueblo |
| audiencia | El pueblo rodea la casa del presidente García Pizarro | Sigue a la multitud |
| final | Madrugada del 26: García Pizarro entrega el mando | — |

Para probar un paso suelto: `godot --path godot -- --paso=rebato`.
Para recorrer toda la historia sola (prueba automática): `godot --headless --path godot -- --piloto`.

## Estructura

```
blender/construir_1809.py      Modela la ciudad, la campana, faroles y antorchas → godot/assets/modelos/
blender/personajes_1809.py     Personajes con MPFB: cuerpo, ropa de época, animaciones → godot/assets/personajes/
herramientas/descargar_assets.py  Baja texturas, cielos y objetos CC0 de Poly Haven
herramientas/generar_materiales.py  Crea los materiales PBR de Godot (godot/materiales/)
herramientas/sintetizar_audio.py  Sintetiza campanas, multitud, viento, pasos, fuego, disparos
herramientas/ajustar_importacion.py  Compresión Basis, mipmaps y tamaños de textura para la web
godot/scripts/nivel.gd         Arma el nivel: ciudad, luz por hora, faroles, sonido, calidad
godot/scripts/director.gd      Guion interactivo paso a paso
godot/scripts/persona.gd       Personas: caminan por rutas, miran, llevan antorcha y eligen su animación
godot/scripts/jugador.gd       Primera persona e interacciones
godot/scripts/ui.gd            Títulos, subtítulos, objetivo e indicador del rebato
godot/shaders/                 Cielo atardecer→noche, guía de luz, posproceso
```

Para regenerar todo:

```bash
python3 -I herramientas/descargar_assets.py
python3 -I herramientas/generar_materiales.py
python3 -I herramientas/sintetizar_audio.py
blender -b --factory-startup --python blender/construir_1809.py
blender -b --python blender/personajes_1809.py      # requiere MPFB y sus assets (abajo)
godot --headless --path godot --import
python3 -I herramientas/ajustar_importacion.py && godot --headless --path godot --import
```

**MPFB y assets de MakeHuman** (para regenerar personajes): `blender --online-mode --command extension
install -s -e mpfb` y descomprimir en `~/.config/blender/5.2/extensions/.user/blender_org/mpfb/data/`
los packs CC0 `makehuman_system_assets`, `skins01`, `skins02`, `suits02`, `skirts01` y `shoes01` de
<https://static.makehumancommunity.org/assets/assetpacks.html> (mirror `files.makehumancommunity.org`).

Pruebas visuales: `--fila=soldado,zudanez,lemoine --fila_anim=caminar` pone personajes en fila;
`--modelo=res://... --modelo_anim=...` muestra un modelo suelto.

## Decisiones de diseño

- **Personajes con dos niveles de detalle.** Los principales (Zudáñez, Lemoine, los soldados del rey
  y el arzobispo) usan el cuerpo completo de MakeHuman (~13 mil vértices) con texturas de 1024; la
  multitud usa la malla *proxy* (~1.700 vértices) con texturas de 512. Así entran ~40 personas con
  antorchas y la plaza sigue a 34–56 FPS en una gráfica integrada.
- **La ropa de 1809 se modela por script** (MakeHuman no la trae): casaca con chaleco, vueltas y
  faldones; ponchos y mantas que caen desde los hombros; muceta, bicornio, sombrero de fieltro,
  montera y fusil. Son aproximaciones: el uniforme del soldado del rey y los colores conviene
  validarlos con referencias de época.
- **Animaciones propias** (reposo, caminar, correr, marcha con fusil, preso con manos atadas,
  llamar, bendecir, vitorear, antorcha) generadas en el script y exportadas con cada personaje.
- **La ciudad es una reconstrucción aproximada**, no un levantamiento: la plaza, la Catedral, el
  Palacio Arzobispal, la Universidad (hoy Casa de la Libertad), la Real Audiencia y la calle a San
  Francisco están en posiciones simplificadas. La distancia a San Francisco está acortada.
- **Luz en tiempo real** (no horneada) porque la historia pasa del atardecer a la noche.

## Fuentes históricas

Hechos que usa el guion:

- Arresto de Jaime de Zudáñez, «el defensor de los pobres», el 25 de mayo de 1809; al ser
  llevado gritó que lo llevaban a matar. Repique a rebato de las campanas de San Francisco por
  los Lemoine; la multitud acudió al arzobispo; Zudáñez fue liberado; García Pizarro fue depuesto
  y apresado. — [Correo del Sur: El arzobispo en la revolución del 25 de mayo 1809](https://correodelsur.com/ecos/20240526/el-arzobispo-en-la-revolucion-del-25-de-mayo-1809.html),
  [Chuquisaca Revolution (Wikipedia)](https://en.wikipedia.org/wiki/Chuquisaca_Revolution),
  [Billiken: Revolución de Chuquisaca](https://billiken.lat/historia/revolucion-de-chuquisaca-la-primera-revolucion-de-mayo-que-sucedio-en-1809/)
- El rumor de la entrega de Charcas a la princesa Carlota del Brasil como detonante. — Correo del Sur (arriba)
- El Acta de Independencia se firmó en 1825 en el antiguo edificio universitario, hoy Casa de la
  Libertad. — [Acta de la Independencia, Casa de la Libertad](https://casadelalibertad.org.bo/wp-content/uploads/2017/08/ACTA-DE-LA-INDEPENDENCIA.pdf)

**Dramatizado:** los diálogos de Lemoine y de la multitud, que el jugador ayude a tocar la
campana, la posición exacta de cada edificio y el número de soldados. Conviene validar el guion
con la Casa de la Libertad o con un historiador antes de presentarlo como material educativo.

## Créditos

- Texturas, cielos y objetos: [Poly Haven](https://polyhaven.com), CC0 (ver `godot/CREDITOS.md`).
- Cuerpos, pieles, ojos, pelo y parte de la ropa de las personas: [MakeHuman](http://www.makehumancommunity.org)
  (MPFB 2 y asset packs CC0).
- Fuente EB Garamond: SIL Open Font License (`godot/assets/fuentes/OFL.txt`).
- Modelos de la ciudad, sonido y código: originales de este proyecto.
