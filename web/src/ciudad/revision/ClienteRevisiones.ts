// Acceso del navegador a /api/revisiones y a las fotos del proyecto cercanas a un punto.
import type { NuevaRevision, Punto3, Revision } from "./tipos";

export type FotoCercana = { archivo: string; distancia: number; miniatura: string };

export class ClienteRevisiones {
  private ubicaciones: Promise<Record<string, { x: number; y: number }>> | null = null;

  async listar(): Promise<Revision[]> {
    const r = await fetch("/api/revisiones", { cache: "no-store" });
    if (!r.ok) throw new Error("no se pudieron leer las revisiones");
    return r.json();
  }

  async crear(datos: NuevaRevision, imagenes: { captura: Blob; recorte: Blob; referencia: Blob | null }): Promise<Revision> {
    const f = new FormData();
    f.set("datos", JSON.stringify(datos));
    f.set("captura", imagenes.captura, "captura.jpg");
    f.set("recorte", imagenes.recorte, "recorte.jpg");
    if (imagenes.referencia) f.set("referencia", imagenes.referencia, "referencia.jpg");
    const r = await fetch("/api/revisiones", { method: "POST", body: f });
    const cuerpo = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(cuerpo.error ?? `error ${r.status}`);
    return cuerpo as Revision;
  }

  static urlImagen(id: string, archivo: string) {
    return `/api/revisiones/${id}/${archivo}`;
  }

  /** Fotos ubicadas del proyecto (fotos/ubicaciones.json) a menos de 'radio' m del punto (lienzo). */
  async fotosCerca(p: Punto3, radio = 45, max = 10): Promise<FotoCercana[]> {
    this.ubicaciones ??= fetch("/api/ubicaciones", { cache: "no-store" }).then((r) => r.json()).catch(() => ({}));
    const ub = await this.ubicaciones;
    return Object.entries(ub)
      .map(([archivo, u]) => ({ archivo, distancia: Math.hypot(u.x - p.x, u.y - p.y),
        miniatura: `/fotos/mini/${archivo.replace(/\.[^.]+$/, ".jpg")}` }))
      .filter((f) => f.distancia <= radio)
      .sort((a, b) => a.distancia - b.distancia)
      .slice(0, max);
  }
}
