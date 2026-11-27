class_name ValidadorEscena
extends RefCounted
## Revisa que el JSON de una escena sea coherente con las fichas y consigo mismo:
## toda ficha citada existe, toda decisión y misión referida existe, etc.

const TIPOS_OBJETIVO := ["tomar", "hablar", "zona", "decision", "firma", "firma_presidente", "entregar", "observar"]


static func validar(escena: Dictionary, fuentes: RepositorioFuentes) -> PackedStringArray:
	# Array (no PackedStringArray) para que la lambda de abajo modifique la misma lista.
	var errores: Array[String] = []
	if escena.is_empty():
		errores.append("La escena está vacía o no se pudo leer.")
		return PackedStringArray(errores)

	var misiones: Array = escena.get("misiones", [])
	var decisiones: Dictionary = escena.get("decisiones", {})
	var personajes: Dictionary = escena.get("personajes", {})
	var objetos: Dictionary = escena.get("objetos", {})
	var ids_misiones := []
	for mision: Dictionary in misiones:
		ids_misiones.append(str(mision.get("id", "")))

	var revisar_ficha := func(id_ficha: String, donde: String) -> void:
		if not id_ficha.is_empty() and not fuentes.tiene_ficha(id_ficha):
			errores.append("%s cita una ficha inexistente: '%s'." % [donde, id_ficha])

	for id: String in personajes:
		revisar_ficha.call(str(personajes[id].get("ficha", "")), "El personaje '%s'" % id)
	for id: String in objetos:
		revisar_ficha.call(str(objetos[id].get("ficha", "")), "El objeto '%s'" % id)

	for mision: Dictionary in misiones:
		var objetivos: Array = mision.get("objetivos", [])
		if objetivos.is_empty():
			errores.append("La misión '%s' no tiene objetivos." % mision.get("id", ""))
		for objetivo: Dictionary in objetivos:
			var tipo := str(objetivo.get("tipo", ""))
			if not tipo in TIPOS_OBJETIVO:
				errores.append("La misión '%s' tiene un objetivo de tipo desconocido: '%s'." % [mision.get("id", ""), tipo])
			if tipo == "decision" and not decisiones.has(str(objetivo.get("objetivo", ""))):
				errores.append("La misión '%s' espera una decisión inexistente: '%s'." % [mision.get("id", ""), objetivo.get("objetivo", "")])

	for id_personaje: String in escena.get("dialogos", {}):
		if not personajes.has(id_personaje):
			errores.append("Hay diálogos para un personaje que no está en 'personajes': '%s'." % id_personaje)
		for variante: Dictionary in escena["dialogos"][id_personaje]:
			var si_mision := str(variante.get("si_mision", ""))
			if not si_mision.is_empty() and not si_mision in ids_misiones:
				errores.append("Un diálogo de '%s' depende de una misión inexistente: '%s'." % [id_personaje, si_mision])
			for linea: Dictionary in variante.get("lineas", []):
				revisar_ficha.call(str(linea.get("ficha", "")), "Un diálogo de '%s'" % id_personaje)
			var al_terminar: Dictionary = variante.get("al_terminar", {})
			if al_terminar.has("decision") and not decisiones.has(str(al_terminar["decision"])):
				errores.append("Un diálogo de '%s' abre una decisión inexistente: '%s'." % [id_personaje, al_terminar["decision"]])
			if al_terminar.has("entregar") and not objetos.has(str(al_terminar["entregar"])):
				errores.append("Un diálogo de '%s' entrega un objeto inexistente: '%s'." % [id_personaje, al_terminar["entregar"]])

	for id: String in decisiones:
		var decision: Dictionary = decisiones[id]
		if decision.get("opciones", []).size() < 2:
			errores.append("La decisión '%s' necesita al menos dos opciones." % id)
		if str(decision.get("ficha_resultado", "")).is_empty():
			errores.append("La decisión '%s' no tiene ficha de 'Lo que realmente pasó'." % id)
		revisar_ficha.call(str(decision.get("ficha_resultado", "")), "La decisión '%s'" % id)
		var siguiente := str(decision.get("siguiente", ""))
		if not siguiente.is_empty() and not decisiones.has(siguiente):
			errores.append("La decisión '%s' sigue con una decisión inexistente: '%s'." % [id, siguiente])

	for id_ficha: String in escena.get("cierre", {}).get("fichas", []):
		revisar_ficha.call(id_ficha, "El cierre de la escena")
	return PackedStringArray(errores)
