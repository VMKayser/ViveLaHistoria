// Lee y guarda fotos/ubicaciones.json (fuera de web/, junto a las fotos originales).
// Solo funciona con el servidor local (npm run dev / npm start).
import { promises as fs } from "fs";
import path from "path";

export const dynamic = "force-dynamic";

const DESCRIPCION =
  "Ubicación de lo que aparece en cada foto (el edificio, fachada o lugar fotografiado), NO el punto desde donde se tomó. " +
  "Para identificar el objeto, cruzar la foto con lo que el mapa tiene en ese punto (campo 'cerca', OSM). " +
  "Coordenadas en el lienzo urban-export: metros, X este, Y norte, Z altura; centro -19.0460,-65.2578 + desfase 4.69 E, 3.09 N. " +
  "rumbo: opcional, dirección en que se tomó la foto (0 = norte, 90 = este).";

const ARCHIVO = path.resolve(process.cwd(), "..", "fotos", "ubicaciones.json");

export async function GET() {
  try {
    const texto = await fs.readFile(ARCHIVO, "utf8");
    return Response.json(JSON.parse(texto).fotos ?? {});
  } catch {
    return Response.json({});
  }
}

export async function PUT(req: Request) {
  const fotos = await req.json();
  if (typeof fotos !== "object" || fotos === null || Array.isArray(fotos)) {
    return Response.json({ error: "formato inválido" }, { status: 400 });
  }
  // se conservan los campos de cabecera (descripcion, estado) que ya tenga el archivo
  let previo: Record<string, unknown> = {};
  try {
    previo = JSON.parse(await fs.readFile(ARCHIVO, "utf8"));
  } catch {}
  const datos = { descripcion: DESCRIPCION, ...previo, fotos };
  // escritura atómica: primero a un temporal y luego renombrar
  const tmp = ARCHIVO + ".tmp";
  await fs.writeFile(tmp, JSON.stringify(datos, null, 1));
  await fs.rename(tmp, ARCHIVO);
  return Response.json({ ok: true, total: Object.keys(fotos).length });
}
