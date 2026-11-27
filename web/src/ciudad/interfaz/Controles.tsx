"use client";

// Controles flotantes (abajo a la derecha): cambio de modo, acercar/alejar y norte arriba. En el recorrido a pie,
// una ayuda de teclas que se pliega sola a los pocos segundos.
import { useEffect, useState } from "react";
import type { EstadoVista } from "../motor/EstadoVista";
import type { Modo } from "../tipos";
import { IconoMapa, IconoPie } from "./PantallaInicio";

export function ControlesMapa({ vista, alCambiarModo }: { vista: EstadoVista; alCambiarModo: (m: Modo) => void }) {
  return (
    <div className="pointer-events-auto flex flex-col items-end gap-2">
      <div className="panel flex flex-col overflow-hidden p-0">
        <BotonIcono titulo="Acercar" onClick={() => vista.ordenar({ tipo: "zoom", factor: 0.6 })}>+</BotonIcono>
        <div className="h-px bg-sucre-tinta/10" />
        <BotonIcono titulo="Alejar" onClick={() => vista.ordenar({ tipo: "zoom", factor: 1.6 })}>−</BotonIcono>
        <div className="h-px bg-sucre-tinta/10" />
        <BotonIcono titulo="Norte arriba" onClick={() => vista.ordenar({ tipo: "norte" })}>
          <span className="text-sm font-bold text-sucre-rojo">N</span>
        </BotonIcono>
      </div>
      <button onClick={() => alCambiarModo("peaton")} className="boton boton-rojo shadow-[var(--shadow-panel)]" title="Caminar desde el centro de la vista (tecla M)">
        <IconoPie /> Caminar aquí
      </button>
    </div>
  );
}

/** Vista aérea desactivada por ahora: sin botón para salir de la primera persona. */
export function ControlesPeaton(_: { alCambiarModo: (m: Modo) => void }) {
  return null;
}

const TECLAS_PEATON: [string, string][] = [["W A S D", "caminar"], ["← →", "girar"], ["Shift", "correr"], ["Arrastrar", "mirar"]];
const TACTIL_PEATON: [string, string][] = [["Pulgar izquierdo", "caminar (al borde: correr)"], ["Otro dedo", "mirar"]];
const TACTIL_MAPA: [string, string][] = [["1 dedo", "mover"], ["2 dedos", "acercar y girar"]];
const TECLAS_MAPA: [string, string][] = [["← ↑ → ↓", "mover"], ["Q E", "girar"], ["R F", "inclinar"], ["+ −", "acercar"], ["Shift", "rápido"], ["M", "caminar"]];

/** Ayuda de teclas: visible al entrar al modo, luego se pliega a un botón "?". */
export function AyudaTeclas({ modo }: { modo: Modo }) {
  const [abierta, setAbierta] = useState(true);
  // pantalla táctil sin ratón (celular o tableta): se explican los gestos en lugar de las teclas
  const [tactil, setTactil] = useState(false);
  useEffect(() => setTactil(window.matchMedia?.("(pointer: coarse)").matches ?? false), []);
  useEffect(() => {
    const t = window.setTimeout(() => setAbierta(false), 7000);
    return () => window.clearTimeout(t);
  }, []);
  if (!abierta) {
    return (
      <button onClick={() => setAbierta(true)} className="panel pointer-events-auto h-9 w-9 font-bold text-sucre-tinta" title="Controles" aria-label="Ver controles">
        ?
      </button>
    );
  }
  return (
    <div className="panel pointer-events-auto flex flex-wrap items-center gap-x-4 gap-y-1.5 px-4 py-2.5 text-xs text-sucre-tinta">
      {(tactil ? (modo === "peaton" ? TACTIL_PEATON : TACTIL_MAPA) : modo === "peaton" ? TECLAS_PEATON : TECLAS_MAPA).map(([k, t]) => <Tecla key={k} k={k} t={t} />)}
      <button onClick={() => setAbierta(false)} className="ml-1 text-sucre-tinta-suave hover:text-sucre-tinta" aria-label="Cerrar ayuda">✕</button>
    </div>
  );
}

function Tecla({ k, t }: { k: string; t: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <kbd className="rounded-md border border-sucre-tinta/20 bg-white px-1.5 py-0.5 font-mono text-[11px] font-semibold shadow-[0_1px_0_rgb(43_29_22/0.2)]">{k}</kbd>
      {t}
    </span>
  );
}

function BotonIcono({ titulo, onClick, children }: { titulo: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick} title={titulo} aria-label={titulo}
      className="flex h-10 w-10 items-center justify-center text-lg font-semibold text-sucre-tinta hover:bg-sucre-oro-claro focus-visible:bg-sucre-oro-claro focus-visible:outline-none">
      {children}
    </button>
  );
}
