extends Node3D
## Conecta las piezas de un nivel: jugador, gestor de misiones, interfaz y personajes.
## Cada escena histórica usa este mismo script; solo cambia su JSON en GestorMisiones.

@onready var jugador: Jugador = $Jugador
@onready var gestor: GestorMisiones = $GestorMisiones
@onready var interfaz: Interfaz = $Interfaz


func _ready() -> void:
	for personaje: Personaje in get_tree().get_nodes_in_group("personajes"):
		personaje.configurar(gestor.personaje(personaje.id_interaccion))
	interfaz.configurar(jugador, gestor)
