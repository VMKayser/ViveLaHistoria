# Fallos Frecuentes y Cómo Prevenirlos

Lista de control obligatoria antes de dar por terminado un vehículo con `vehiculo-3d-desde-diseno`.

| Síntoma observado | Causa raíz | Prevención / Corrección |
|---|---|---|
| Silueta genérica o irreconocible ("caja pintada") | No medir proporciones en la lámina o reutilizar dimensiones de otro vehículo | Medir en píxeles largo/alto, batalla, voladizos, caída de capó, inclinación de pilares y cintura antes de escribir geometría |
| Aspecto de "cubos apilados y cortes diagonales" | Construir flancos, pilares, portón y parachoques con paneles planos y rampas rectas | Modelar monocasco con sección transversal en barril continuo (zócalo recogido, panza, hombro de cintura redondeado, techo abovedado), morro *bullnose*, aletas abombadas con labio interior, parachoques con cojín sobresaliente + faldón recogido y accesorios con `SUBSURF` |
| Frente plano o techo con chaflanes duros | Usar biseles de 1–2 segmentos sobre un cubo | Construir techo por loft abovedado con hombros amplios y curvar el morro progresivamente en alzado y planta |
| Reflejos "abollados" en puertas o bandas | Promediar la normal de la cara exterior con el canto del espesor (`SOLIDIFY`) | Marcar aristas duras (`smooth = False`) cuando el ángulo entre caras supere `~45°` |
| Parachoques recto o matrícula flotando en las esquinas | Deformar la carrocería en planta sin subdividir ni incluir el parachoques | Subdividir el parachoques antes de curvar y aplicar exactamente la misma función espacial a parachoques, ópticas y portaplaca |
| Ranura de luz entre parabrisas y techo | Falta de pieza de transición entre el plano inclinado del cristal y el hombro curvo | Modelar el cintillo superior y los pilares cerrando geométricamente contra el techo |
| Moldura lateral cruzando el hueco de la rueda | Generar la moldura de extremo a extremo sin restar los pasos de rueda | Partir los intervalos longitudinales de faldones y molduras con el mismo radio de corte del guardabarros |
| Se ve el suelo o la rueda opuesta a través del arco | Paso de rueda recortado en la piel exterior pero abierto por dentro | Construir bóveda cilíndrica interior y cara interna oscura en los cuatro guardabarros |
| Llanta plana como moneda o agujeros pintados | Cilindro sin perfil ni booleanas | Tornear perfil cóncavo con labio escalonado y perforar las ventilaciones con booleana `EXACT` |
| Línea vertical oscura en el flanco del neumático | Cierre de revolución sin soldar vértices o con UV interpolado al revés | Colocar `t = -π/2` abajo, asignar UV por esquina de cara (`loop`) y ejecutar `remove_doubles` |
| Clips `rodar_adelante` / `rodar_atras` estáticos al exportar | Solo 2 keyframes en `0°` y `360°` (quaternions equivalentes) | Insertar 25 muestras explícitas (`frames 1..25`) en pistas NLA y validar el giro acumulado en el binario GLB |
| Ruedas patinando al estar detenido o girando igual en curvas | Giro sumado por fotograma fijo o ángulo único en ambas ruedas delanteras | Integrar rodadura desde distancia firmada por rueda y aplicar geometría Ackermann respecto al eje trasero |
| Cambiar el color de un auto cambia toda la flota | Mutar `.color` sobre el material compartido del `GLTFLoader` | Clonar únicamente los materiales de pintura por instancia (`WeakMap`) dejando intactos luces, gomas y cristales |
