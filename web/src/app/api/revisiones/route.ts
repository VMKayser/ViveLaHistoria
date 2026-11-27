// Revisiones del visor: GET lista todas; POST crea una (multipart: datos JSON + imágenes JPEG).
// Solo funciona con el servidor local (npm run dev / npm start): escribe en coordinacion/revisiones/.
import { AlmacenRevisiones } from "@/servidor/AlmacenRevisiones";
import { CATEGORIAS, type NuevaRevision } from "@/ciudad/revision/tipos";

export const dynamic = "force-dynamic";

const almacen = new AlmacenRevisiones();
const MAX_IMAGEN = 8 * 1024 * 1024;

export async function GET() {
  return Response.json(await almacen.listar());
}

export async function POST(req: Request) {
  const form = await req.formData();
  let datos: NuevaRevision;
  try {
    datos = JSON.parse(String(form.get("datos")));
  } catch {
    return Response.json({ error: "datos inválidos" }, { status: 400 });
  }
  if (!datos?.comentario?.trim()) return Response.json({ error: "el comentario es obligatorio" }, { status: 400 });
  if (!(datos.categoria in CATEGORIAS)) return Response.json({ error: "categoría desconocida" }, { status: 400 });
  if (!["alta", "media", "baja"].includes(datos.prioridad)) return Response.json({ error: "prioridad inválida" }, { status: 400 });
  if (!datos.escena?.camara) return Response.json({ error: "faltan los datos de la escena" }, { status: 400 });
  datos.fotos_proyecto = (Array.isArray(datos.fotos_proyecto) ? datos.fotos_proyecto : [])
    .filter((f) => typeof f === "string" && /^[\w.-]+$/.test(f)).slice(0, 12);

  const leer = async (campo: string) => {
    const f = form.get(campo);
    if (!(f instanceof Blob) || f.size === 0) return null;
    if (f.size > MAX_IMAGEN) throw new Error(`${campo}: imagen demasiado grande`);
    return Buffer.from(await f.arrayBuffer());
  };
  try {
    const captura = await leer("captura"), recorte = await leer("recorte");
    if (!captura || !recorte) return Response.json({ error: "falta la captura" }, { status: 400 });
    const rev = await almacen.crear(datos, { captura, recorte, referencia: await leer("referencia") });
    return Response.json(rev, { status: 201 });
  } catch (e) {
    return Response.json({ error: String((e as Error).message) }, { status: 400 });
  }
}
