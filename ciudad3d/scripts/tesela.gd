class_name Tesela
extends RefCounted
## Lectura de un archivo de tesela (ciudad3d/herramientas/empaquetar.py): deflate → superficies con posiciones, normales,
## colores (RGB lineal + número de edificio en alfa), número de rol por vértice (UV.x) e índices, ya como arreglos nativos
## de Godot (sin bucles por vértice). Cada superficie junta todos los roles de un grupo, una clase de material y un origen.

## Devuelve [{grupo, clase, origen, pos, nor, col, rol, idx}] (o [] si los bytes no sirven).
static func leer(bytes: PackedByteArray, grupos: Array, clases: Array, origenes: Array) -> Array:
	if bytes.size() < 8:
		return []
	var tam := bytes.decode_u32(0)
	var d := bytes.slice(4).decompress(tam, FileAccess.COMPRESSION_DEFLATE)
	var n := d.decode_u32(0)
	var off := 4
	var cab := []
	for s in n:
		cab.append({"grupo": grupos[d.decode_u8(off)], "clase": clases[d.decode_u8(off + 1)], "origen": origenes[d.decode_u8(off + 2)],
			"v": d.decode_u32(off + 4), "i": d.decode_u32(off + 8)})
		off += 12
	var res := []
	for c in cab:
		var v: int = c["v"]
		var i: int = c["i"]
		c["pos"] = d.slice(off, off + v * 12).to_vector3_array(); off += v * 12
		c["nor"] = d.slice(off, off + v * 12).to_vector3_array(); off += v * 12
		c["col"] = d.slice(off, off + v * 16).to_color_array(); off += v * 16
		c["rol"] = d.slice(off, off + v * 8).to_vector2_array(); off += v * 8
		c["idx"] = d.slice(off, off + i * 4).to_int32_array(); off += i * 4
		res.append(c)
	return res

## Arma las mallas de una tesela: una por (grupo, origen), con grupo = suelo (sin sombra), sólido o liviano (no frena),
## y dentro una superficie por clase de material. 'roles' es la lista de ciudad.json (para los materiales).
## Devuelve {"mallas": [{malla, grupo, origen}], "suelo": [[pos, idx], …], "solido": [[pos, idx], …]}: la geometría de
## choque queda como arreglos (la colisión se arma solo cerca; antes era una ArrayMesh que ocupaba memoria de vídeo sin
## dibujarse nunca).
static func armar(superficies: Array, roles: Array) -> Dictionary:
	var mallas := {}
	var choque := {"suelo": [], "solido": []}
	for s in superficies:
		var g: String = s["grupo"]
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = s["pos"]
		arr[Mesh.ARRAY_NORMAL] = s["nor"]
		arr[Mesh.ARRAY_COLOR] = s["col"]
		arr[Mesh.ARRAY_TEX_UV] = s["rol"]
		arr[Mesh.ARRAY_INDEX] = s["idx"]
		var clave: String = g + "|" + s["origen"]
		if not mallas.has(clave):
			mallas[clave] = ArrayMesh.new()
		var m: ArrayMesh = mallas[clave]
		# sin ARRAY_FLAG_COMPRESS_ATTRIBUTES: ahorra ~30 % de memoria de vídeo pero cambia los vidrios (su tipo y reflejo
		# dependen de la normal y la posición exactas); probado el 2026-11-26, PSNR 22 dB
		m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		m.surface_set_material(m.get_surface_count() - 1, Estilo.material_ciudad(s["clase"], roles))
		if g != "liviano":
			choque[g].append([s["pos"], s["idx"]])
	var lista := []
	for clave in mallas:
		var partes: PackedStringArray = clave.split("|")
		lista.append({"malla": mallas[clave], "grupo": partes[0], "origen": partes[1]})
	return {"mallas": lista, "suelo": choque["suelo"], "solido": choque["solido"]}

## Forma de colisión (triángulos) a partir de los arreglos guardados por armar(). Antes pasaba por una ArrayMesh pasajera y
## create_trimesh_shape(), pero en la web eso sube la malla a la tarjeta de vídeo y la vuelve a leer (35–105 ms por tesela);
## desindexar aquí da las mismas caras en ~10 ms (medido el 2026-11-26).
static func forma(partes: Array) -> ConcavePolygonShape3D:
	if partes.is_empty():
		return null
	var caras := PackedVector3Array()
	for p in partes:
		var pos: PackedVector3Array = p[0]
		var idx: PackedInt32Array = p[1]
		var base := caras.size()
		caras.resize(base + idx.size())
		for i in idx.size():
			caras[base + i] = pos[idx[i]]
	var f := ConcavePolygonShape3D.new()
	f.set_faces(caras)
	return f
