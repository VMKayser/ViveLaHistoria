"use client";

// La web es solo para computadora (decisión del usuario, 2026-11-12): en celulares y tabletas se usa la app móvil.
// Se detecta el dispositivo ANTES de cargar la experiencia, para no descargar la ciudad (decenas de MB) en el
// teléfono. `?escritorio` en la dirección fuerza la versión web (pruebas).
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

const Experiencia = dynamic(() => import("../Experiencia"), { ssr: false });

function esMovil(): boolean {
  if (new URLSearchParams(window.location.search).has("escritorio")) return false;
  const nav = navigator as Navigator & { userAgentData?: { mobile?: boolean } };
  if (nav.userAgentData?.mobile) return true;
  const ua = navigator.userAgent;
  if (/Android|iPhone|iPad|iPod|Mobile|Silk|Kindle|Opera Mini|IEMobile/i.test(ua)) return true;
  // iPad con iPadOS se presenta como Mac: se reconoce por la pantalla táctil
  if (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1) return true;
  // pantalla táctil sin ratón y pequeña (tabletas Android en modo escritorio, etc.)
  const tactilSinRaton = window.matchMedia("(pointer: coarse)").matches && !window.matchMedia("(any-pointer: fine)").matches;
  return tactilSinRaton && Math.min(window.screen.width, window.screen.height) < 1100;
}

export default function SoloEscritorio() {
  const [movil, setMovil] = useState<boolean | null>(null);
  useEffect(() => setMovil(esMovil()), []);
  if (movil === null) return <div className="h-dvh bg-sucre-cal" />;
  if (!movil) return <Experiencia />;
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-6 bg-sucre-cal px-7 py-10 text-center text-sucre-tinta">
      <div className="flex h-1.5 w-24 overflow-hidden rounded-full">
        <span className="flex-1 bg-sucre-rojo" />
        <span className="flex-1 bg-sucre-oro" />
      </div>
      <h1 className="text-3xl font-bold leading-tight">Sucre 3D</h1>
      <p className="max-w-sm text-base leading-relaxed text-sucre-tinta-suave">
        En el celular y la tableta, el centro histórico de Sucre se recorre con la <b className="text-sucre-tinta">app
        Sucre 3D</b>, pensada para caminar sus calles con el dedo.
      </p>
      <div className="flex w-full max-w-xs flex-col gap-3">
        <span className="boton boton-rojo justify-center opacity-70" aria-disabled="true">App Store · muy pronto</span>
        {/* mientras no esté en Google Play, el APK firmado se descarga directo (npm run ciudad:apk lo deja aquí) */}
        <a href="/descargas/MiCiudad-Sucre.apk" download className="boton boton-cal justify-center">
          Descargar para Android (APK)
        </a>
      </div>
      <p className="max-w-sm text-sm text-sucre-tinta-suave">
        La versión web está hecha para computadora: ábrela desde tu PC o laptop.
      </p>
    </main>
  );
}
