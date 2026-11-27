"use client";

// Lista de correcciones guardadas y detalle de la elegida, con "ver desde donde se marcó".
import { useState } from "react";
import { ClienteRevisiones } from "../../revision/ClienteRevisiones";
import { CATEGORIAS, type EstadoRevision, type Revision } from "../../revision/tipos";

const COLOR_ESTADO: Record<EstadoRevision, string> = {
  pendiente: "bg-sucre-rojo text-white",
  en_curso: "bg-sucre-oro text-sucre-tinta",
  resuelta: "bg-sucre-esmeralda text-white",
  descartada: "bg-sucre-tinta/30 text-sucre-tinta",
};

export default function PanelRevisiones({ revisiones, elegida, alElegir, alIr, alCerrar }: {
  revisiones: Revision[];
  elegida: string | null;
  alElegir: (id: string | null) => void;
  alIr: (r: Revision) => void;
  alCerrar: () => void;
}) {
  const [todas, setTodas] = useState(false);
  const lista = revisiones.filter((r) => todas || r.estado === "pendiente" || r.estado === "en_curso").slice().reverse();
  const r = revisiones.find((x) => x.id === elegida);

  return (
    <aside className="panel pointer-events-auto flex max-h-[calc(100dvh-6rem)] w-[340px] flex-col overflow-hidden text-sm">
      <div className="flex items-center justify-between border-b border-sucre-tinta/10 px-3 py-2">
        <h2 className="font-[family-name:var(--font-titulo)] text-lg font-semibold">Correcciones</h2>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1 text-xs text-sucre-tinta-suave">
            <input type="checkbox" checked={todas} onChange={(e) => setTodas(e.target.checked)} /> ver resueltas
          </label>
          <button onClick={alCerrar} className="rounded px-1.5 text-sucre-tinta-suave hover:bg-sucre-oro-claro" aria-label="Cerrar">✕</button>
        </div>
      </div>

      {r ? (
        <div className="flex flex-col gap-2 overflow-y-auto p-3">
          <button onClick={() => alElegir(null)} className="self-start text-xs text-sucre-tinta-suave hover:text-sucre-tinta">← todas</button>
          <div className="flex items-center gap-2">
            <b>{r.id}</b>
            <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${COLOR_ESTADO[r.estado]}`}>{r.estado.replace("_", " ")}</span>
            <span className="text-xs text-sucre-tinta-suave">{CATEGORIAS[r.categoria]} · prioridad {r.prioridad}</span>
          </div>
          <a href={ClienteRevisiones.urlImagen(r.id, r.archivos.captura)} target="_blank" rel="noreferrer">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={ClienteRevisiones.urlImagen(r.id, r.archivos.recorte)} alt="Zona enmarcada" className="max-h-52 w-full rounded-lg bg-black/5 object-contain" />
          </a>
          <p className="whitespace-pre-wrap rounded-lg bg-white px-3 py-2">{r.comentario}</p>
          {r.archivos.referencia && (
            <a href={ClienteRevisiones.urlImagen(r.id, r.archivos.referencia)} target="_blank" rel="noreferrer">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={ClienteRevisiones.urlImagen(r.id, r.archivos.referencia)} alt="Foto de referencia" className="max-h-40 w-full rounded-lg bg-black/5 object-contain" />
            </a>
          )}
          {r.archivos.fotos_proyecto.length > 0 && (
            <p className="text-xs text-sucre-tinta-suave">Fotos del proyecto: {r.archivos.fotos_proyecto.join(", ")}</p>
          )}
          <p className="font-mono text-[11px] leading-snug text-sucre-tinta-suave">
            {[r.lugar.manzana, r.lugar.edificio, r.lugar.espacio].filter(Boolean).join(" / ") || "fuera del reparto"}
            {r.lugar.asignado && <> · para <b>{r.lugar.asignado}</b></>}
            <br />{r.escena.calle} · {r.autor} · {new Date(r.creada).toLocaleString("es-BO")}
          </p>
          {r.resolucion && (
            <p className="rounded-lg bg-sucre-esmeralda/10 px-3 py-2 text-xs">
              <b>{r.resolucion.agente}</b>: {r.resolucion.nota}
            </p>
          )}
          <button onClick={() => alIr(r)} className="boton boton-rojo">Ver desde donde se marcó</button>
        </div>
      ) : (
        <ul className="overflow-y-auto">
          {lista.length === 0 && <li className="px-3 py-4 text-center text-sucre-tinta-suave">No hay correcciones {todas ? "" : "pendientes"}.</li>}
          {lista.map((x) => (
            <li key={x.id}>
              <button onClick={() => alElegir(x.id)} className="flex w-full gap-2.5 border-b border-sucre-tinta/5 px-3 py-2 text-left hover:bg-sucre-oro-claro">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={ClienteRevisiones.urlImagen(x.id, x.archivos.recorte)} alt="" className="h-12 w-16 shrink-0 rounded object-cover" loading="lazy" />
                <span className="min-w-0">
                  <span className="flex items-center gap-1.5 text-xs">
                    <b>{x.id}</b>
                    <span className={`rounded-full px-1.5 text-[10px] font-semibold ${COLOR_ESTADO[x.estado]}`}>{x.estado.replace("_", " ")}</span>
                    <span className="truncate text-sucre-tinta-suave">{x.lugar.manzana ?? x.lugar.espacio ?? ""} {x.lugar.asignado ? `· ${x.lugar.asignado}` : ""}</span>
                  </span>
                  <span className="line-clamp-2 text-xs">{x.comentario}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
