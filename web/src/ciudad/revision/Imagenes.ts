// Preparación de imágenes en el navegador antes de subirlas: captura con el marco dibujado, recorte de lo
// enmarcado y reducción de la foto adjunta (las fotos del celular pesan varios MB).
import type { DatosEscena } from "./tipos";

const LADO_MAX = 1600;

function aBlob(c: HTMLCanvasElement, calidad = 0.86): Promise<Blob> {
  return new Promise((ok, mal) => c.toBlob((b) => (b ? ok(b) : mal(new Error("no se pudo codificar la imagen"))), "image/jpeg", calidad));
}

function lienzo(w: number, h: number) {
  const c = document.createElement("canvas");
  c.width = Math.max(1, Math.round(w));
  c.height = Math.max(1, Math.round(h));
  return c;
}

export class Imagenes {
  /** Pantalla completa (reducida) con el marco dibujado en rojo, y el recorte a resolución completa. */
  static async componer(cuadro: HTMLCanvasElement, marco: DatosEscena["marco"]) {
    const W = cuadro.width, H = cuadro.height;
    const k = Math.min(1, LADO_MAX / Math.max(W, H));
    const total = lienzo(W * k, H * k);
    const ctx = total.getContext("2d")!;
    ctx.drawImage(cuadro, 0, 0, total.width, total.height);
    const [x0, y0, x1, y1] = [marco.x0 * total.width, marco.y0 * total.height, marco.x1 * total.width, marco.y1 * total.height];
    ctx.fillStyle = "rgba(0,0,0,0.28)"; // oscurece lo de afuera
    ctx.fillRect(0, 0, total.width, y0);
    ctx.fillRect(0, y1, total.width, total.height - y1);
    ctx.fillRect(0, y0, x0, y1 - y0);
    ctx.fillRect(x1, y0, total.width - x1, y1 - y0);
    ctx.lineWidth = Math.max(3, total.width / 400);
    ctx.strokeStyle = "#d9171a";
    ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);

    const rw = (marco.x1 - marco.x0) * W, rh = (marco.y1 - marco.y0) * H;
    const kr = Math.min(1, LADO_MAX / Math.max(rw, rh));
    const recorte = lienzo(rw * kr, rh * kr);
    recorte.getContext("2d")!.drawImage(cuadro, marco.x0 * W, marco.y0 * H, rw, rh, 0, 0, recorte.width, recorte.height);
    return { captura: await aBlob(total), recorte: await aBlob(recorte, 0.9), vistaPrevia: recorte.toDataURL("image/jpeg", 0.8) };
  }

  /** Foto adjunta → JPEG de lado ≤ 1600 px (respeta la orientación EXIF con createImageBitmap). */
  static async reducir(archivo: File): Promise<Blob> {
    const bmp = await createImageBitmap(archivo, { imageOrientation: "from-image" });
    const k = Math.min(1, LADO_MAX / Math.max(bmp.width, bmp.height));
    const c = lienzo(bmp.width * k, bmp.height * k);
    c.getContext("2d")!.drawImage(bmp, 0, 0, c.width, c.height);
    bmp.close();
    return aBlob(c, 0.85);
  }
}
