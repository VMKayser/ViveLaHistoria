// Imágenes de una revisión (captura.jpg, recorte.jpg, referencia.jpg).
import { AlmacenRevisiones } from "@/servidor/AlmacenRevisiones";

export const dynamic = "force-dynamic";

const almacen = new AlmacenRevisiones();

export async function GET(_req: Request, { params }: { params: Promise<{ id: string; archivo: string }> }) {
  const { id, archivo } = await params;
  const datos = await almacen.imagen(id, archivo);
  if (!datos) return new Response("no existe", { status: 404 });
  return new Response(new Uint8Array(datos), { headers: { "Content-Type": "image/jpeg", "Cache-Control": "no-cache" } });
}
