"use client";

// Minimapa (abajo a la izquierda, como en los juegos de mundo abierto).
//  - A pie: el mapa gira para que hacia adelante quede arriba; la flecha dorada es el caminante.
//  - Vista aérea: norte arriba; el trapecio claro es lo que se ve en pantalla.
// Clic en el minimapa: ir a ese punto (volando o, a pie, apareciendo ahí). Se dibuja en su propio ciclo leyendo
// EstadoVista, sin renders de React.
import { useEffect, useRef } from "react";
import type { EstadoVista } from "../motor/EstadoVista";

const TAM = 196;          // px (CSS)
const RADIO_PEATON = 85;  // metros desde el centro hasta el borde, a pie

export default function Minimapa({ vista, calle }: { vista: EstadoVista; calle: string }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const cv = ref.current!;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    cv.width = cv.height = TAM * dpr;
    const ctx = cv.getContext("2d")!;
    let ultimo = "";
    let raf = 0;
    const dibujar = () => {
      raf = requestAnimationFrame(dibujar);
      const peaton = vista.modo === "peaton";
      const radio = peaton ? RADIO_PEATON : Math.max(120, Math.min(900, vista.distancia * 0.9));
      const huella = vista.huella?.flat().map((v) => v.toFixed(0)).join(",") ?? "";
      const clave = [vista.modo, vista.x.toFixed(1), vista.z.toFixed(1), vista.rumbo.toFixed(3), radio.toFixed(0), huella, !!vista.mapa].join("|");
      if (clave === ultimo) return; // nada cambió
      ultimo = clave;
      const s = (TAM * dpr) / 2 / radio; // px por metro
      const c = (TAM * dpr) / 2;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.fillStyle = "#e9e2d2";
      ctx.fillRect(0, 0, cv.width, cv.height);
      ctx.save();
      ctx.translate(c, c);
      if (peaton) ctx.rotate(-vista.rumbo);
      ctx.scale(s, s);
      ctx.translate(-vista.x, -vista.z);
      const m = vista.mapa;
      if (m) {
        const { x0, z0, x1, z1 } = m.limites;
        ctx.imageSmoothingQuality = "high";
        ctx.drawImage(m.lienzo, x0, z0, x1 - x0, z1 - z0);
      }
      if (!peaton && vista.huella) {
        ctx.beginPath();
        vista.huella.forEach(([x, z], i) => (i ? ctx.lineTo(x, z) : ctx.moveTo(x, z)));
        ctx.closePath();
        ctx.fillStyle = "rgba(255,255,255,0.28)";
        ctx.fill();
        ctx.lineWidth = 2 / s;
        ctx.strokeStyle = "rgba(255,255,255,0.95)";
        ctx.stroke();
      }
      ctx.restore();
      // posición: flecha (a pie siempre hacia arriba; en vista aérea, gira con el rumbo de la cámara)
      ctx.save();
      ctx.translate(c, c);
      if (!peaton) ctx.rotate(vista.rumbo);
      const k = dpr * (peaton ? 1 : 0.8);
      ctx.beginPath();
      ctx.moveTo(0, -11 * k);
      ctx.lineTo(8 * k, 8 * k);
      ctx.lineTo(0, 4 * k);
      ctx.lineTo(-8 * k, 8 * k);
      ctx.closePath();
      ctx.fillStyle = "#eac102";
      ctx.strokeStyle = "#2b1d16";
      ctx.lineWidth = 1.6 * dpr;
      ctx.fill();
      ctx.stroke();
      ctx.restore();
      // norte: una "N" roja sobre el borde
      const angN = peaton ? -vista.rumbo - Math.PI / 2 : -Math.PI / 2;
      const rN = c - 13 * dpr;
      ctx.beginPath();
      ctx.arc(c + Math.cos(angN) * rN, c + Math.sin(angN) * rN, 9 * dpr, 0, Math.PI * 2);
      ctx.fillStyle = "#d9171a";
      ctx.fill();
      ctx.fillStyle = "white";
      ctx.font = `700 ${11 * dpr}px system-ui, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("N", c + Math.cos(angN) * rN, c + Math.sin(angN) * rN + 0.5 * dpr);
    };
    raf = requestAnimationFrame(dibujar);
    return () => cancelAnimationFrame(raf);
  }, [vista]);

  // Arrastrar el minimapa (vista aérea) mueve la vista al instante, como "agarrar" el mapa; un clic sin
  // arrastrar va a ese punto; la rueda acerca o aleja.
  const arrastre = useRef<{ x: number; y: number; movido: number } | null>(null);

  /** Escala (px CSS por metro) y giro del dibujo actual. */
  const geometria = (el: HTMLElement) => {
    const r = el.getBoundingClientRect();
    const peaton = vista.modo === "peaton";
    const radio = peaton ? RADIO_PEATON : Math.max(120, Math.min(900, vista.distancia * 0.9));
    return { r, s: r.width / 2 / radio, a: peaton ? vista.rumbo : 0 };
  };
  /** Vector de pantalla (px) → vector del mundo (m), deshaciendo giro y escala. */
  const aMundo = (px: number, py: number, s: number, a: number) =>
    [(px * Math.cos(a) - py * Math.sin(a)) / s, (px * Math.sin(a) + py * Math.cos(a)) / s] as const;

  const alBajar = (e: React.PointerEvent<HTMLCanvasElement>) => {
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {
      // puntero sintético o ya liberado: el arrastre funciona igual mientras esté encima
    }
    arrastre.current = { x: e.clientX, y: e.clientY, movido: 0 };
  };
  const alMover = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const a = arrastre.current;
    if (!a) return;
    const px = e.clientX - a.x, py = e.clientY - a.y;
    a.x = e.clientX;
    a.y = e.clientY;
    a.movido += Math.abs(px) + Math.abs(py);
    if (vista.modo !== "mapa" || a.movido < 4) return;
    const { s } = geometria(e.currentTarget);
    vista.ordenar({ tipo: "desplazar", dx: -px / s, dz: -py / s });
  };
  const alSoltar = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const a = arrastre.current;
    arrastre.current = null;
    if (!a || a.movido >= 4) return;
    const { r, s, a: giro } = geometria(e.currentTarget);
    const [dx, dz] = aMundo(e.clientX - r.left - r.width / 2, e.clientY - r.top - r.height / 2, s, giro);
    vista.ordenar({ tipo: "ir", x: vista.x + dx, z: vista.z + dz });
  };
  useEffect(() => {
    const cv = ref.current!;
    const rueda = (e: WheelEvent) => {
      e.preventDefault();
      if (vista.modo === "mapa") vista.ordenar({ tipo: "zoom", factor: e.deltaY > 0 ? 1.35 : 0.74 });
    };
    cv.addEventListener("wheel", rueda, { passive: false });
    return () => cv.removeEventListener("wheel", rueda);
  }, [vista]);

  return (
    <div className="pointer-events-auto flex flex-col items-center gap-1.5">
      <div className="relative rounded-full p-[3px] shadow-[var(--shadow-panel)]"
        style={{ background: "conic-gradient(from 45deg, #d9171a 0 25%, #fff 0 50%, #d9171a 0 75%, #fff 0)" }}>
        <canvas
          ref={ref}
          onPointerDown={alBajar}
          onPointerMove={alMover}
          onPointerUp={alSoltar}
          onPointerCancel={() => (arrastre.current = null)}
          title="Arrastra para mover la vista · clic para ir a un punto · rueda para acercar"
          aria-label="Minimapa"
          className="block cursor-grab touch-none rounded-full border-2 border-sucre-oro active:cursor-grabbing"
          style={{ width: TAM, height: TAM }}
        />
      </div>
      {calle && (
        <div className="panel max-w-[220px] truncate px-3 py-1 text-center text-xs font-semibold text-sucre-tinta">{calle}</div>
      )}
    </div>
  );
}
