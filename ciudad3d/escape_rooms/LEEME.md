# Escape rooms

Juegos de pistas dentro de edificios o en un recorrido por la ciudad. Cada uno: un `.tscn` con sus objetos
interactivos (zonas en `Interaccion`), su estado en `Guardado` (`Guardado.escribir("escape_<id>", {...})`) y su
propia interfaz (CanvasLayer por encima de la de la ciudad).
