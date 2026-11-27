"use client";

// Capa sobre la escena para dibujar el marco con el mouse (o el dedo). Mientras está activa, la escena no recibe el
// arrastre (no gira la cámara). Esc cancela.
import { useEffect, useRef, useState } from "react";

export type Marco = { x0: number; y0: number; x1: number; y1: number };

export default function Enmarcador({ alMarcar, alCancelar }: { alMarcar: (m: Marco) => void; alCancelar: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  // el arrastre vive en una ref (los eventos pueden llegar antes de que React vuelva a dibujar); el estado solo
  // sirve para pintar el rectángulo
  const arrastre = useRef<{ a: { x: number; y: number }; b: { x: number; y: number } } | null>(null);
  const [, redibujar] = useState(0);
  const inicio = arrastre.current?.a ?? null, fin = arrastre.current?.b ?? null;

  useEffect(() => {
    const tecla = (e: KeyboardEvent) => {
      if (e.code === "Escape") {
        e.stopPropagation();
        alCancelar();
      }
    };
    window.addEventListener("keydown", tecla, true);
    return () => window.removeEventListener("keydown", tecla, true);
  }, [alCancelar]);

  const punto = (e: React.PointerEvent) => {
    const r = ref.current!.getBoundingClientRect();
    return { x: Math.min(Math.max(e.clientX - r.left, 0), r.width), y: Math.min(Math.max(e.clientY - r.top, 0), r.height) };
  };
  const caja = inicio && fin && {
    left: Math.min(inicio.x, fin.x), top: Math.min(inicio.y, fin.y),
    width: Math.abs(fin.x - inicio.x), height: Math.abs(fin.y - inicio.y),
  };

  return (
    <div
      ref={ref}
      className="pointer-events-auto absolute inset-0 z-20 cursor-crosshair touch-none"
      onPointerDown={(e) => {
        try {
          e.currentTarget.setPointerCapture(e.pointerId);
        } catch {
          // puntero sintético: el arrastre sigue funcionando sin captura
        }
        const p = punto(e);
        arrastre.current = { a: p, b: p };
        redibujar((n) => n + 1);
      }}
      onPointerMove={(e) => {
        if (!arrastre.current) return;
        arrastre.current.b = punto(e);
        redibujar((n) => n + 1);
      }}
      onPointerUp={(e) => {
        const g = arrastre.current;
        arrastre.current = null;
        redibujar((n) => n + 1);
        if (!g) return;
        g.b = punto(e);
        const r = ref.current!.getBoundingClientRect();
        const x0 = Math.min(g.a.x, g.b.x), x1 = Math.max(g.a.x, g.b.x);
        const y0 = Math.min(g.a.y, g.b.y), y1 = Math.max(g.a.y, g.b.y);
        if (x1 - x0 > 12 && y1 - y0 > 12) alMarcar({ x0: x0 / r.width, y0: y0 / r.height, x1: x1 / r.width, y1: y1 / r.height });
      }}
    >
      {!caja && (
        <div className="panel pointer-events-none absolute left-1/2 top-20 -translate-x-1/2 px-4 py-2 text-sm">
          Arrastra para enmarcar la zona a corregir · <b>Esc</b> cancela
        </div>
      )}
      {caja && (
        <div className="pointer-events-none absolute border-[3px] border-sucre-rojo bg-sucre-rojo/10 shadow-[0_0_0_9999px_rgba(0,0,0,0.25)]"
          style={caja} />
      )}
    </div>
  );
}
