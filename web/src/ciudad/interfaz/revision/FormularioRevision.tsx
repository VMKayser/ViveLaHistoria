"use client";

// Formulario de una revisión: comentario (obligatorio), categoría, prioridad, foto de referencia (opcional) y fotos
// del proyecto tomadas cerca (opcional). Muestra lo enmarcado y los datos que se guardarán.
import { useEffect, useState } from "react";
import { ClienteRevisiones, type FotoCercana } from "../../revision/ClienteRevisiones";
import { Imagenes } from "../../revision/Imagenes";
import { CATEGORIAS, type Categoria, type DatosEscena, type Prioridad, type Revision } from "../../revision/tipos";

export type Encuadre = { datos: DatosEscena; captura: Blob; recorte: Blob; vistaPrevia: string };

const CLAVE_AUTOR = "sucre3d.revisor";

export default function FormularioRevision({ encuadre, cliente, alGuardar, alCancelar }: {
  encuadre: Encuadre;
  cliente: ClienteRevisiones;
  alGuardar: (r: Revision) => void;
  alCancelar: () => void;
}) {
  const [comentario, setComentario] = useState("");
  const [categoria, setCategoria] = useState<Categoria>("fachada");
  const [prioridad, setPrioridad] = useState<Prioridad>("media");
  const [autor, setAutor] = useState("");
  const [foto, setFoto] = useState<{ archivo: File; url: string } | null>(null);
  const [cercanas, setCercanas] = useState<FotoCercana[]>([]);
  const [elegidas, setElegidas] = useState<string[]>([]);
  const [estado, setEstado] = useState<{ guardando: boolean; error: string }>({ guardando: false, error: "" });
  const d = encuadre.datos;

  useEffect(() => {
    setAutor(localStorage.getItem(CLAVE_AUTOR) ?? "");
    const p = d.centro ?? d.camara.lienzo;
    cliente.fotosCerca(p).then(setCercanas);
  }, [cliente, d]);
  useEffect(() => () => {
    if (foto) URL.revokeObjectURL(foto.url);
  }, [foto]);

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!comentario.trim()) return setEstado({ guardando: false, error: "Escribe qué está mal o cómo corregirlo." });
    setEstado({ guardando: true, error: "" });
    try {
      localStorage.setItem(CLAVE_AUTOR, autor.trim());
      const referencia = foto ? await Imagenes.reducir(foto.archivo) : null;
      const r = await cliente.crear(
        { autor, categoria, prioridad, comentario, escena: d, fotos_proyecto: elegidas },
        { captura: encuadre.captura, recorte: encuadre.recorte, referencia },
      );
      alGuardar(r);
    } catch (err) {
      setEstado({ guardando: false, error: String((err as Error).message) });
    }
  };

  const p = d.centro;
  return (
    <form onSubmit={guardar}
      className="panel pointer-events-auto flex max-h-[calc(100dvh-2rem)] w-[380px] flex-col gap-3 overflow-y-auto p-4 text-sm">
      <div className="flex items-center justify-between">
        <h2 className="font-[family-name:var(--font-titulo)] text-xl font-semibold">Nueva corrección</h2>
        <button type="button" onClick={alCancelar} className="rounded px-1.5 text-sucre-tinta-suave hover:bg-sucre-oro-claro" aria-label="Cancelar">✕</button>
      </div>

      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={encuadre.vistaPrevia} alt="Zona enmarcada" className="max-h-48 w-full rounded-lg border-2 border-sucre-rojo object-contain bg-black/5" />
      <p className="-mt-1 font-mono text-[11px] leading-snug text-sucre-tinta-suave">
        {d.calle || "sin calle cercana"}
        {p && <> · punto ({p.x.toFixed(1)}, {p.y.toFixed(1)}, {p.z.toFixed(1)}) a {d.distancia_m} m</>}
        <br />cámara {d.camara.modo === "peaton" ? "a pie" : "aérea"} · rumbo {d.camara.rumbo_grados}° · manzana y dueño se calculan al guardar
      </p>

      <label className="flex flex-col gap-1">
        <span className="font-semibold">Qué está mal o cómo corregirlo <span className="text-sucre-rojo">*</span></span>
        <textarea autoFocus required rows={4} value={comentario} onChange={(e) => setComentario(e.target.value)}
          placeholder="Ej.: la fachada real tiene 3 balcones de hierro y el zócalo es de piedra gris, no blanco."
          className="rounded-lg border border-sucre-tinta/20 bg-white px-2.5 py-2 outline-none focus:border-sucre-oro focus:ring-2 focus:ring-sucre-oro/40" />
      </label>

      <div className="grid grid-cols-[1fr_auto] gap-2">
        <label className="flex flex-col gap-1">
          <span className="font-semibold">Tipo</span>
          <select value={categoria} onChange={(e) => setCategoria(e.target.value as Categoria)}
            className="rounded-lg border border-sucre-tinta/20 bg-white px-2 py-1.5">
            {Object.entries(CATEGORIAS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
        <fieldset className="flex flex-col gap-1">
          <legend className="mb-1 font-semibold">Prioridad</legend>
          <div className="flex overflow-hidden rounded-lg border border-sucre-tinta/20">
            {(["alta", "media", "baja"] as const).map((v) => (
              <button type="button" key={v} onClick={() => setPrioridad(v)}
                className={`px-2.5 py-1.5 capitalize ${prioridad === v ? "bg-sucre-rojo text-white" : "bg-white hover:bg-sucre-oro-claro"}`}>
                {v}
              </button>
            ))}
          </div>
        </fieldset>
      </div>

      <div className="flex flex-col gap-1">
        <span className="font-semibold">Foto de referencia <span className="font-normal text-sucre-tinta-suave">(opcional)</span></span>
        {foto ? (
          <div className="relative">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={foto.url} alt="Foto adjunta" className="max-h-40 w-full rounded-lg object-contain bg-black/5" />
            <button type="button" onClick={() => setFoto(null)} className="panel absolute right-1.5 top-1.5 px-2 text-xs">Quitar</button>
          </div>
        ) : (
          <label className="boton boton-cal cursor-pointer border-dashed">
            Adjuntar foto…
            <input type="file" accept="image/*" className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) setFoto({ archivo: f, url: URL.createObjectURL(f) });
              }} />
          </label>
        )}
      </div>

      {cercanas.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className="font-semibold">Fotos del proyecto cerca <span className="font-normal text-sucre-tinta-suave">(marca las que sirvan)</span></span>
          <div className="grid grid-cols-5 gap-1.5">
            {cercanas.map((f) => {
              const sel = elegidas.includes(f.archivo);
              return (
                <button type="button" key={f.archivo} title={`${f.archivo} · ${f.distancia.toFixed(0)} m`}
                  onClick={() => setElegidas((l) => (sel ? l.filter((x) => x !== f.archivo) : [...l, f.archivo]))}
                  className={`relative aspect-square overflow-hidden rounded-md ring-2 ${sel ? "ring-sucre-rojo" : "ring-transparent hover:ring-sucre-oro"}`}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={f.miniatura} alt={f.archivo} className="h-full w-full object-cover" loading="lazy" />
                  {sel && <span className="absolute right-0.5 top-0.5 rounded-full bg-sucre-rojo px-1 text-[10px] font-bold text-white">✓</span>}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <label className="flex flex-col gap-1">
        <span className="font-semibold">Revisor <span className="font-normal text-sucre-tinta-suave">(opcional)</span></span>
        <input value={autor} onChange={(e) => setAutor(e.target.value)} placeholder="Tu nombre"
          className="rounded-lg border border-sucre-tinta/20 bg-white px-2.5 py-1.5 outline-none focus:border-sucre-oro" />
      </label>

      {estado.error && <p className="rounded-md bg-sucre-rojo-claro px-2.5 py-1.5 text-sucre-rojo-oscuro">{estado.error}</p>}
      <div className="flex justify-end gap-2">
        <button type="button" onClick={alCancelar} className="boton boton-cal">Cancelar</button>
        <button type="submit" disabled={estado.guardando} className="boton boton-rojo disabled:opacity-60">
          {estado.guardando ? "Guardando…" : "Guardar corrección"}
        </button>
      </div>
    </form>
  );
}
