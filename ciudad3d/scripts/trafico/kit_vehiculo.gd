class_name KitVehiculo
extends RefCounted
## Un tipo de vehículo listo para circular: mallas por pieza y nivel de detalle (datos/vehiculos/<id>.bin, de
## herramientas/vehiculos.mjs), sus medidas (movimiento, caja) y un material por variante de color.
##
## Marco: el kit viene con x adelante, y arriba, z a la derecha. En Godot el vehículo mira a +Z (así ruedan las
## VehicleWheel3D), con +X a su izquierda: (x, y, z) → (−z, y, x).

## Distancias de cambio de nivel de detalle (m): cerca (0), medio (1) y lejos (2).
const LOD := [36.0, 140.0, 1100.0]

var id: String
var mov: Dictionary          # velocidad_maxima, aceleracion, frenada, direccion_maxima, radio_rueda, ejes, semivia…
var frente: float            # paragolpes delantero (z del cuerpo)
var cola: float              # paragolpes trasero
var medio_ancho: float
var alto: float
var mallas := {}             # pieza -> ArrayMesh
var materiales: Array = []   # por variante: {cuerpo, vidrio}
var masa := 7500.0
var piso := 0.62             # altura donde empieza la caja de choque
var radio_delantera := 0.0   # si la rueda delantera es de otro tamaño (carrozas, remolque); 0: la misma que la trasera
## Eje delantero que gira entero (carrozas, remolque): pivote en el marco del vehículo (x adelante, y arriba) y anclajes
## en su marco (tirantes y varas del tiro, ojo de la lanza). Vacío si gira como un auto.
var tornamesa := {}
var anclas := {}
var caballo := {}            # posición del caballo en el marco de la tornamesa {x, y, boca}
var riendas := {}            # puños del cochero (marco del kit) {izquierda, derecha}: de ahí a la boca del caballo

func _init(nombre: String, datos: Dictionary, bin: PackedByteArray) -> void:
	id = nombre
	mov = datos["movimiento"]
	var caja: Dictionary = datos["caja"]
	frente = float(caja["max"][0])
	cola = float(caja["min"][0])
	medio_ancho = float(caja["max"][2])
	alto = float(caja["max"][1])
	masa = float(datos.get("masa", masa))
	piso = float(datos.get("piso", piso))
	radio_delantera = float(datos.get("radio_delantera", 0.0))
	tornamesa = datos.get("tornamesa", {})
	anclas = datos.get("anclas", {})
	caballo = datos.get("caballo", {})
	riendas = datos.get("riendas", {})
	_leer(bin)
	for v in datos["variantes"]:
		var p := Color(str(v["principal"])).srgb_to_linear()
		var d := Color(str(v["detalle"])).srgb_to_linear()
		materiales.append({"cuerpo": Estilo.material_movil("vehiculo", p, d), "vidrio": Estilo.material_movil("vidrio", p, d)})

func _leer(bin: PackedByteArray) -> void:
	var d := bin.slice(4).decompress(bin.decode_u32(0), FileAccess.COMPRESSION_DEFLATE)
	var n := d.decode_u32(0)
	var o := 4
	for _k in n:
		var largo := d[o]
		var nombre := d.slice(o + 1, o + 1 + largo).get_string_from_utf8()
		o += 1 + largo
		var nv := d.decode_u32(o)
		var ni := d.decode_u32(o + 4)
		o += 8
		var pos := d.slice(o, o + nv * 12).to_float32_array()
		o += nv * 12
		var nor := d.slice(o, o + nv * 12).to_float32_array()
		o += nv * 12
		var col := d.slice(o, o + nv * 12).to_float32_array()
		o += nv * 12
		var tipo := d.slice(o, o + nv * 4).to_float32_array()
		o += nv * 4
		var idx := d.slice(o, o + ni * 4).to_int32_array()
		o += ni * 4
		var vp := PackedVector3Array()
		var vn := PackedVector3Array()
		var vc := PackedColorArray()
		var vt := PackedVector2Array()
		vp.resize(nv)
		vn.resize(nv)
		vc.resize(nv)
		vt.resize(nv)
		for i in nv:
			vp[i] = Vector3(-pos[3 * i + 2], pos[3 * i + 1], pos[3 * i])
			vn[i] = Vector3(-nor[3 * i + 2], nor[3 * i + 1], nor[3 * i])
			vc[i] = Color(col[3 * i], col[3 * i + 1], col[3 * i + 2], 1.0)
			vt[i] = Vector2(tipo[i], 0.0)
		# triángulos: el giro de glTF (antihorario) se invierte para Godot (horario = cara frontal)
		for t in range(0, ni, 3):
			var a := idx[t + 1]
			idx[t + 1] = idx[t + 2]
			idx[t + 2] = a
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = vp
		arr[Mesh.ARRAY_NORMAL] = vn
		arr[Mesh.ARRAY_COLOR] = vc
		arr[Mesh.ARRAY_TEX_UV2] = vt
		arr[Mesh.ARRAY_INDEX] = idx
		var m := ArrayMesh.new()
		m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		mallas[nombre] = m

func tiene(nombre: String) -> bool:
	return mallas.has(nombre)

## Del marco del kit (x adelante, y arriba, z a la derecha) al de Godot (el vehículo mira a +Z, +X a su izquierda).
static func a_godot(p: Array) -> Vector3:
	return Vector3(-float(p[2]), float(p[1]), float(p[0]))

## Instancia de una pieza con su material y rango de visibilidad (nivel de detalle).
func pieza(nombre: String, variante: int, nivel: int) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = nombre
	mi.mesh = mallas[nombre]
	var mats: Dictionary = materiales[variante % materiales.size()]
	mi.material_override = mats["vidrio"] if nombre.begins_with("vidrio") else mats["cuerpo"]
	mi.visibility_range_begin = 0.0 if nivel == 0 else LOD[nivel - 1]
	mi.visibility_range_end = LOD[nivel]
	if nivel == 2:
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi
