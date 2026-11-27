---
name: desarrollo-por-seccion
description: Cómo se desarrolla la ciudad a partir de ahora: una SECCIÓN concreta por vez (un tramo de calle, una esquina, una cuadra), limpiando el terreno, modelando a mano lo que se ve en las fotos y revisando a pie, sin scripts genéricos que recorran toda la ciudad (relleno de cuadras, fachadas genéricas, macetas o adornos al azar). Usar SIEMPRE antes de modelar, corregir, decorar o limpiar cualquier parte de la ciudad, junto con la skill modelado-ciudad.
---

# Desarrollo de la ciudad por secciones (pedido del usuario, 2026-11-14)

> "Nada puede ser hecho con un script genérico, nunca trabajar sobre todo el conjunto de la ciudad, trabajar siempre
> sobre una sección específica, limpiando bien el terreno, modelando para esa sección, sin generalizar ni hacer
> scripts impersonales."

Por qué: los scripts que rellenaban o decoraban toda la ciudad de una vez dejaron casas genéricas en la calzada de la
plaza, una "ciudad perdida" detrás de las fachadas, callejones que no existen, macetas y faroles donde no van y
cientos de fachadas que nadie ve (el usuario se pega a una fachada buena, ve a través y encuentra genéricas detrás).
Gastan recursos y se notan enseguida a pie.

Esta skill manda sobre el método; los detalles técnicos (kit, fichas, exportar, calidad) siguen en `modelado-ciudad`.

## Qué es una sección

Lo que el usuario ve de una vez caminando: **un tramo de calle entre dos esquinas (las dos veredas y sus
fachadas), una esquina, una plazuela o el frente de un edificio importante**. Se nombra por la calle y las
esquinas: `Ravelo entre Junín y Arce`, `esquina Junín × Ravelo`, `Plazuela Cochabamba`.

## Prohibido

- Scripts que recorran toda la ciudad (o todas las manzanas) para **agregar** cosas: relleno de cuadras, fachadas
  genéricas en lados que no dan a la calle, macetas, flores, faroles de pared, bolardos, árboles o adornos
  repartidos con `random`. Un adorno existe porque está en una foto o porque la sección lo pide, y se coloca a mano
  (coordenadas o posición en la fachada escritas en el script de la sección).
- Fachadas en lados que no dan a la calle, casas en el interior de las cuadras, patios decorados que nadie ve.
  **Detrás de una fachada no hay nada** (a lo sumo el techo del propio edificio).
- Cambiar parámetros globales (anchos de todas las calles, color de todas las veredas, postes de toda la ciudad)
  para arreglar una sección. Los ajustes van por tramo (`TRAMOS` en `scripts/calles_reales.py`, datos de la sección).
- Inventar calles, callejones, pasajes o plazuelas que no están en las fotos ni en OSM.

Sí se permite usar **funciones reutilizables** (una ventana, un balcón, un poste, un árbol) llamadas desde el script
de la sección con parámetros elegidos mirando las fotos. Lo que está prohibido es que un script decida solo, para
toda la ciudad, dónde y qué poner.

## Flujo por sección

1. **Delimitar**: nombre de la sección, calles y esquinas, manzanas y espacios que toca (y de quién son). Anotarla
   en `coordinacion/estado_<agente>.md` como "en curso".
2. **Reunir referencias**: fotos ubicadas en esa calle (`fotos/ubicaciones.json`, fichas), correcciones del usuario
   (`coordinacion/revisiones/R####` con `referencia.jpg`), recorrido `Peatonal/` u otros. Inventario por foto:
   qué edificios, pisos, vanos, colores, árboles, postes, bolardos, bancos, letreros — y **qué NO hay**.
3. **Limpiar el terreno** de la sección: renderizar el estado actual desde las cámaras a pie (1,6 m) y listar todo
   lo que sobra (relleno, piezas genéricas, objetos de otros scripts que caen ahí, huecos, parpadeos, volúmenes que
   se cruzan, fachadas detrás de fachadas). Quitarlo en su origen (script), no tapándolo.
4. **Calle y veredas** de la sección: ancho real del tramo (fachada a fachada), veredas de baldosa (no tierra),
   bordillo, calzada (asfalto o empedrado según la foto), cebras. Postes y árboles **junto al bordillo** (a
   ~0,4 m del borde), dejando paso libre de ≥ 1,5 m hasta la fachada; solo donde la foto los muestra o donde
   la calle los necesita, nunca uno en cada metro. Bolardos solo en los tramos que tienen.
5. **Modelar las fachadas** de la sección a mano, edificio por edificio, en el script de la sección (o de la
   manzana): cada uno dentro de su huella, medianeras limpias, sin aberturas al cielo entre edificios, letreros y
   pantallas con un solo plano y separados del muro (sin parpadeo).
6. **Mobiliario y vegetación** de la sección, colocados a mano según las fotos.
7. **Revisar a pie**: vistas a 1,6 m por las dos veredas, en las esquinas y desde las cámaras de las correcciones;
   pegarse a las fachadas (lo que se ve detrás); `calidad.py` en cero para lo que toca la sección.
8. **Commit** de la sección (solo tus rutas) y anotar en el estado qué quedó y qué falta.

Una sección termina antes de empezar otra. Si un arreglo pide tocar otra sección, se anota y se hace cuando toque
esa sección.

## Lista de comprobación de la sección

- [ ] nada genérico ni al azar: cada pieza está porque una foto o la sección lo pide
- [ ] detrás de las fachadas no hay nada visible (ni casas, ni fachadas, ni callejones inventados)
- [ ] sin aberturas al cielo entre edificios ni muros sin terminar (todas las caras visibles cerradas)
- [ ] veredas de ciudad (baldosa/losa), anchas como en la foto; postes y árboles al borde de la vereda
- [ ] sin parpadeo (caras coplanares: calzada/empedrado, letreros, pantallas, pisos superpuestos)
- [ ] `calidad.py` en cero y vistas a pie revisadas
