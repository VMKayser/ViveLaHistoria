# Diseños de vehículos de Mi Ciudad

Siete láminas de referencia creadas con la herramienta integrada de generación de imágenes: seis vehículos a partir de sus fotografías y una nueva lámina del autobús BRONCO. Los originales tienen nombres descriptivos y conservan sus bytes originales.

Cada lámina contiene cuatro paneles: arriba izquierda, el vehículo en la ciudad; arriba derecha, frente; abajo izquierda, perfil con el frente hacia la derecha; abajo derecha, trasera. Se usa el autobús como referencia de estilo y composición y la captura de la Plaza 25 de Mayo como referencia del entorno, sin interfaz.

| Vehículo | Foto o diseño original | Lámina generada |
| --- | --- | --- |
| Autobús BRONCO | [Referencia](00_autobus_bronco_referencia_4_vistas.png) | [Diseño](generadas/00_autobus_bronco_diseno_miciudad.png) |
| Vagoneta blanca clásica | [Foto](01_vagoneta_blanca_clasica.jpg) | [Diseño](generadas/01_vagoneta_blanca_clasica_diseno_miciudad.png) |
| Mitsubishi Montero Sport blanca | [Foto](02_mitsubishi_montero_sport_blanca.jpg) | [Diseño](generadas/02_mitsubishi_montero_sport_blanca_diseno_miciudad.png) |
| Ford EcoSport blanca | [Foto](03_ford_ecosport_blanca.jpeg) | [Diseño](generadas/03_ford_ecosport_blanca_diseno_miciudad.png) |
| Toyota Hilux blanca de doble cabina | [Foto](04_toyota_hilux_blanca_doble_cabina.jpeg) | [Diseño](generadas/04_toyota_hilux_blanca_doble_cabina_diseno_miciudad.png) |
| Toyota pickup roja de cabina extendida | [Foto](05_toyota_pickup_roja_cabina_extendida.jpeg) | [Diseño](generadas/05_toyota_pickup_roja_cabina_extendida_diseno_miciudad.png) |
| Camioneta Ford azul oscuro y gris | [Foto](06_ford_camioneta_azul_oscuro_bicolor.jpeg) | [Diseño](generadas/06_ford_camioneta_azul_oscuro_bicolor_diseno_miciudad.png) |

El [fondo urbano original](fondo_plaza_25_de_mayo_miciudad.png) se conserva aparte. La generación reinterpreta el fondo; no es una composición exacta píxel a píxel sobre la captura.

Las vistas ocultas se completan como propuestas de diseño coherentes. Para construir los modelos 3D, contrastar los detalles con las fotos originales; las imágenes no fijan medidas físicas ni planos técnicos exactos. No se afirma año o versión exacta de vehículos cuando la foto no permite confirmarlos.

[indice_autos.json](indice_autos.json) registra nombres anteriores, nombres nuevos y hashes de los originales. [prompts_laminas.json](prompts_laminas.json) contiene los siete prompts completos usados, las referencias en su orden, las salidas, sus dimensiones reales y hashes. Las rutas de referencia se resuelven desde esta carpeta.
