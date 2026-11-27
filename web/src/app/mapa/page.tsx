"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Calle, FotoIndice, LugarOSM, Ubicacion, Ubicaciones } from "@/mapa/tipos";
import type { Modo, PuntoMapa } from "@/mapa/Escena";
import { Buscador } from "@/mapa/busqueda";
import { aLatLon, nombreRumbo } from "@/mapa/geo";

const Escena = dynamic(() => import("@/mapa/Escena"), { ssr: false });

type Punto = PuntoMapa & { rumbo: number | null };
type Panel =
  | { tipo: "elegir"; punto: Punto }
  | { tipo: "grupo"; archivos: string[] }
  | { tipo: "gps"; archivos: string[] }
  | null;

const mini = (f: string) => `/fotos/mini/${f.replace(/\.[^.]+$/, ".jpg")}`;
const medio = (f: string) => `/fotos/medio/${f.replace(/\.[^.]+$/, ".jpg")}`;
const hora = (f?: FotoIndice) => f?.fecha.slice(11, 16) ?? "";

export default function PaginaMapa() {
  const [calles, setCalles] = useState<Calle[]>([]);
  const [lugares, setLugares] = useState<LugarOSM[]>([]);
  const [fotos, setFotos] = useState<FotoIndice[]>([]);
  const [ubic, setUbic] = useState<Ubicaciones>({});
  const [cargado, setCargado] = useState(false);
  const [estado, setEstado] = useState("");

  const [modo, setModo] = useState<Modo>("mano");
  const [verGPS, setVerGPS] = useState(true);
  const [verNombres, setVerNombres] = useState(true);
  const [panel, setPanel] = useState<Panel>(null);
  const [moviendo, setMoviendo] = useState<string[] | null>(null);
  const [visor, setVisor] = useState<{ lista: string[]; i: number } | null>(null);
  const [hover, setHover] = useState<PuntoMapa | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("/mapa/calles.json").then((r) => r.json()),
      fetch("/mapa/lugares.json").then((r) => r.json()),
      fetch("/fotos/indice.json", { cache: "no-store" }).then((r) => r.json()),
      fetch("/api/ubicaciones", { cache: "no-store" }).then((r) => r.json()),
    ]).then(([c, l, f, u]) => {
      setCalles(c);
      setLugares(l);
      setFotos(f);
      setUbic(u);
      setCargado(true);
    });
  }, []);

  const buscador = useMemo(() => new Buscador(calles, lugares), [calles, lugares]);
  const porArchivo = useMemo(() => new Map(fotos.map((f) => [f.archivo, f])), [fotos]);
  const inicio = useMemo<[number, number]>(() => {
    const p = lugares.find((l) => l.nombre === "Plaza 25 de Mayo");
    return p ? [p.x, p.y] : [0, 0];
  }, [lugares]);

  const guardar = useCallback(async (nuevo: Ubicaciones) => {
    setUbic(nuevo);
    setEstado("Guardando…");
    try {
      const r = await fetch("/api/ubicaciones", { method: "PUT", body: JSON.stringify(nuevo) });
      setEstado(r.ok ? `Guardado · ${Object.keys(nuevo).length} fotos ubicadas` : "Error al guardar");
    } catch {
      setEstado("Error al guardar (¿está corriendo npm run dev?)");
    }
  }, []);

  const datosPunto = useCallback(
    (p: PuntoMapa, rumbo: number | null, origen: Ubicacion["origen"], nota = ""): Ubicacion => {
      const [lat, lon] = aLatLon(p.x, p.y);
      return {
        x: +p.x.toFixed(1), y: +p.y.toFixed(1), z: +p.z.toFixed(1),
        lat: +lat.toFixed(7), lon: +lon.toFixed(7),
        rumbo: rumbo === null ? null : Math.round(rumbo),
        calle: buscador.calle(p.x, p.y)?.nombre ?? "",
        cerca: buscador.cercanos(p.x, p.y).map((l) => l.nombre),
        origen, nota,
        actualizado: new Date().toISOString(),
      };
    },
    [buscador],
  );

  const asignar = (archivos: string[], p: PuntoMapa, rumbo: number | null, origen: Ubicacion["origen"], nota = "") => {
    const nuevo = { ...ubic };
    for (const a of archivos) nuevo[a] = datosPunto(p, rumbo, origen, nota || ubic[a]?.nota || "");
    guardar(nuevo);
  };

  const onMarcar = useCallback(
    (p: PuntoMapa, rumbo: number | null) => {
      if (moviendo) {
        const nuevo = { ...ubic };
        for (const a of moviendo) nuevo[a] = datosPunto(p, rumbo ?? ubic[a]?.rumbo ?? null, "manual", ubic[a]?.nota ?? "");
        guardar(nuevo);
        setPanel({ tipo: "grupo", archivos: moviendo });
        setMoviendo(null);
        return;
      }
      setPanel({ tipo: "elegir", punto: { ...p, rumbo } });
    },
    [moviendo, ubic, datosPunto, guardar],
  );

  const onFoto = useCallback(
    (archivo: string) => setPanel({ tipo: ubic[archivo] ? "grupo" : "gps", archivos: [archivo] }),
    [ubic],
  );
  // Soltar un punto arrastrado: queda como posición manual, conservando dirección y nota
  const onSoltar = useCallback(
    (archivo: string, p: PuntoMapa) => {
      const u = ubic[archivo];
      guardar({ ...ubic, [archivo]: datosPunto(p, u?.rumbo ?? null, "manual", u?.nota ?? "") });
      setPanel((pa) => (pa && pa.tipo !== "elegir" && pa.archivos.includes(archivo) ? { tipo: "grupo", archivos: pa.archivos } : pa));
    },
    [ubic, guardar, datosPunto],
  );
  const aceptarTodasGPS = () => {
    const pendientes = fotos.filter((f) => f.gps && !ubic[f.archivo]);
    if (!pendientes.length || !confirm(`¿Confirmar la posición GPS de ${pendientes.length} fotos? Luego puedes seguir arrastrándolas.`)) return;
    const nuevo = { ...ubic };
    for (const f of pendientes) nuevo[f.archivo] = datosPunto({ x: f.gps!.x, y: f.gps!.y, z: hoverZ(calles, f.gps!.x, f.gps!.y) }, null, "gps");
    guardar(nuevo);
  };

  // Atajos: M marcar, H mano, G GPS, Esc cerrar
  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === "INPUT" || (e.target as HTMLElement).tagName === "TEXTAREA") return;
      if (visor) {
        if (e.key === "ArrowRight") setVisor((v) => v && { ...v, i: Math.min(v.lista.length - 1, v.i + 1) });
        if (e.key === "ArrowLeft") setVisor((v) => v && { ...v, i: Math.max(0, v.i - 1) });
        if (e.key === "Escape") setVisor(null);
        return;
      }
      if (e.key === "m" || e.key === "M") setModo("marcar");
      if (e.key === "h" || e.key === "H") setModo("mano");
      if (e.key === "g" || e.key === "G") setVerGPS((v) => !v);
      if (e.key === "Escape") { setPanel(null); setMoviendo(null); }
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [visor]);

  const seleccion = useMemo(
    () => (panel?.tipo === "grupo" ? panel.archivos : moviendo ?? []),
    [panel, moviendo],
  );
  const hoverInfo = useMemo(() => {
    if (!hover) return null;
    const c = buscador.calle(hover.x, hover.y);
    const cerca = buscador.cercanos(hover.x, hover.y, 50, 2);
    return { calle: c && c.distancia < 30 ? c.nombre : "", cerca: cerca.map((l) => l.nombre).join(" · ") };
  }, [hover, buscador]);

  const total = fotos.length;
  const ubicadas = fotos.filter((f) => ubic[f.archivo]).length;

  return (
    <main className="relative h-dvh w-full overflow-hidden bg-[#cfe3ef] text-stone-800">
      {cargado ? (
        <Escena
          calles={calles}
          lugares={lugares}
          fotos={fotos}
          ubicaciones={ubic}
          modo={moviendo ? "marcar" : modo}
          verGPS={verGPS}
          verNombres={verNombres}
          seleccion={seleccion}
          inicio={inicio}
          onHover={setHover}
          onMarcar={onMarcar}
          onFoto={onFoto}
          onSoltar={onSoltar}
        />
      ) : (
        <p className="p-6">Cargando mapa…</p>
      )}

      {/* Barra superior */}
      <div className="absolute left-3 top-3 z-[90] flex flex-wrap items-center gap-2">
        <div className="flex overflow-hidden rounded-lg bg-white shadow">
          <BotonModo activo={modo === "mano" && !moviendo} onClick={() => setModo("mano")} titulo="Mano: arrastrar para moverse (H)">
            ✋ Mano
          </BotonModo>
          <BotonModo activo={modo === "marcar" || !!moviendo} onClick={() => setModo("marcar")} titulo="Marcar: clic en el mapa para poner fotos (M)">
            📍 Marcar
          </BotonModo>
        </div>
        <label className="flex items-center gap-1 rounded-lg bg-white px-2 py-1.5 text-sm shadow">
          <input type="checkbox" checked={verGPS} onChange={(e) => setVerGPS(e.target.checked)} /> GPS del celular
        </label>
        <label className="flex items-center gap-1 rounded-lg bg-white px-2 py-1.5 text-sm shadow">
          <input type="checkbox" checked={verNombres} onChange={(e) => setVerNombres(e.target.checked)} /> Nombres
        </label>
        <span className="rounded-lg bg-white px-2 py-1.5 text-sm shadow">
          <b>{ubicadas}</b> / {total} fotos ubicadas
        </span>
        {fotos.some((f) => f.gps && !ubic[f.archivo]) && (
          <button onClick={aceptarTodasGPS} className="rounded-lg bg-white px-2 py-1.5 text-sm shadow hover:bg-slate-100" title="Da por buenas las posiciones GPS de las fotos grises">
            ✓ Confirmar GPS de las pendientes
          </button>
        )}
        {estado && <span className="rounded-lg bg-white/80 px-2 py-1.5 text-xs shadow">{estado}</span>}
      </div>

      {moviendo && (
        <div className="absolute left-1/2 top-16 z-[90] -translate-x-1/2 rounded-lg bg-red-600 px-4 py-2 text-sm text-white shadow">
          Haz clic en la nueva posición de {moviendo.length} foto(s) (arrastra para indicar hacia dónde mira) · Esc cancela
        </div>
      )}

      {/* Ayuda e info bajo el cursor */}
      <div className="pointer-events-none absolute bottom-3 left-3 z-[90] max-w-xl rounded-lg bg-white/90 px-3 py-2 text-xs shadow">
        {hoverInfo && (hoverInfo.calle || hoverInfo.cerca) ? (
          <p className="mb-1 text-sm">
            {hoverInfo.calle && <b>{hoverInfo.calle}</b>}
            {hoverInfo.cerca && <span className="text-stone-600"> {hoverInfo.calle ? "· " : ""}{hoverInfo.cerca}</span>}
          </p>
        ) : null}
        {modo === "mano" && !moviendo ? (
          <p>Arrastrar el mapa: mover · Clic derecho + arrastrar: girar · Rueda: zoom</p>
        ) : (
          <p>
            <b>Clic</b>: poner fotos aquí · <b>Clic y arrastrar</b>: además indica hacia dónde mira la cámara · Botón central: mover ·
            Derecho: girar · Rueda: zoom
          </p>
        )}
        <p>
          <b>Cada punto es una foto</b>: pasa el cursor para verla, <b>arrástralo</b> para corregir su posición, clic para abrirla.
        </p>
        <p className="text-stone-500">Gris: posición GPS del celular sin confirmar · Naranja claro: GPS confirmado · Naranja oscuro: ubicada a mano.</p>
      </div>

      {panel && (
        <aside className="absolute bottom-0 right-0 top-0 z-[100] flex w-[420px] max-w-full flex-col bg-white shadow-2xl">
          {panel.tipo === "elegir" && (
            <Elegir
              punto={panel.punto}
              fotos={fotos}
              ubic={ubic}
              buscador={buscador}
              onCerrar={() => setPanel(null)}
              onVer={(lista, i) => setVisor({ lista, i })}
              onAsignar={(archivos, nota) => {
                asignar(archivos, panel.punto, panel.punto.rumbo, "manual", nota);
                setPanel({ tipo: "grupo", archivos });
              }}
            />
          )}
          {(panel.tipo === "grupo" || panel.tipo === "gps") && (
            <PanelGrupo
              tipo={panel.tipo}
              archivos={panel.archivos}
              porArchivo={porArchivo}
              ubic={ubic}
              onCerrar={() => setPanel(null)}
              onVer={(lista, i) => setVisor({ lista, i })}
              onMover={(arch) => { setMoviendo(arch); setPanel(null); }}
              onQuitar={(arch) => {
                const nuevo = { ...ubic };
                for (const a of arch) delete nuevo[a];
                guardar(nuevo);
                const resto = panel.archivos.filter((a) => !arch.includes(a));
                setPanel(resto.length ? { ...panel, archivos: resto } : null);
              }}
              onNota={(arch, nota) => {
                const nuevo = { ...ubic };
                for (const a of arch) if (nuevo[a]) nuevo[a] = { ...nuevo[a], nota };
                guardar(nuevo);
              }}
              onAceptarGPS={(arch) => {
                const nuevo = { ...ubic };
                for (const a of arch) {
                  const g = porArchivo.get(a)?.gps;
                  if (g) nuevo[a] = datosPunto({ x: g.x, y: g.y, z: hoverZ(calles, g.x, g.y) }, null, "gps");
                }
                guardar(nuevo);
                setPanel({ tipo: "grupo", archivos: arch });
              }}
            />
          )}
        </aside>
      )}

      {visor && (
        <div className="absolute inset-0 z-[200] flex items-center justify-center bg-black/85" onClick={() => setVisor(null)}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={medio(visor.lista[visor.i])} alt="" className="max-h-[90vh] max-w-[92vw] object-contain" onClick={(e) => e.stopPropagation()} />
          <p className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded bg-black/60 px-3 py-1 text-sm text-white">
            {visor.lista[visor.i]} · {hora(porArchivo.get(visor.lista[visor.i]))} · {visor.i + 1}/{visor.lista.length} · ← → para pasar, Esc cierra
          </p>
        </div>
      )}
    </main>
  );
}

/** Altura aproximada del terreno: la del punto de calle más cercano */
function hoverZ(calles: Calle[], x: number, y: number) {
  let z = 0, d = Infinity;
  for (const c of calles) for (const [px, py, pz] of c.puntos) {
    const dd = (px - x) ** 2 + (py - y) ** 2;
    if (dd < d) { d = dd; z = pz - 0.6; }
  }
  return z;
}

function BotonModo(p: { activo: boolean; onClick: () => void; titulo: string; children: React.ReactNode }) {
  return (
    <button
      onClick={p.onClick}
      title={p.titulo}
      className={`px-3 py-1.5 text-sm font-semibold ${p.activo ? "bg-amber-600 text-white" : "hover:bg-amber-50"}`}
    >
      {p.children}
    </button>
  );
}

function Miniatura(p: { archivo: string; foto?: FotoIndice; marcada?: boolean; extra?: string; onClick: () => void; onVer: () => void }) {
  return (
    <div className={`relative overflow-hidden rounded-md border-2 ${p.marcada ? "border-amber-600" : "border-transparent"}`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={mini(p.archivo)} alt={p.archivo} loading="lazy" className="aspect-[4/3] w-full cursor-pointer object-cover" onClick={p.onClick} />
      <button onClick={p.onVer} title="Ver grande" className="absolute right-1 top-1 rounded bg-black/50 px-1 text-xs text-white">⤢</button>
      {p.marcada && <span className="absolute left-1 top-1 rounded-full bg-amber-600 px-1.5 text-xs text-white">✓</span>}
      <p className="truncate bg-stone-100 px-1 text-[10px] text-stone-600">
        {hora(p.foto)} {p.extra}
      </p>
    </div>
  );
}

function Elegir(p: {
  punto: Punto;
  fotos: FotoIndice[];
  ubic: Ubicaciones;
  buscador: Buscador;
  onCerrar: () => void;
  onVer: (lista: string[], i: number) => void;
  onAsignar: (archivos: string[], nota: string) => void;
}) {
  const [marcadas, setMarcadas] = useState<string[]>([]);
  const [orden, setOrden] = useState<"cerca" | "hora">("cerca");
  const [verUbicadas, setVerUbicadas] = useState(false);
  const [nota, setNota] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  const calle = p.buscador.calle(p.punto.x, p.punto.y);
  const cerca = p.buscador.cercanos(p.punto.x, p.punto.y);

  const lista = useMemo(() => {
    const dist = (f: FotoIndice) => (f.gps ? Math.hypot(f.gps.x - p.punto.x, f.gps.y - p.punto.y) : Infinity);
    return p.fotos
      .filter((f) => verUbicadas || !p.ubic[f.archivo])
      .map((f) => ({ f, d: dist(f) }))
      .sort((a, b) => (orden === "cerca" ? a.d - b.d || a.f.fecha.localeCompare(b.f.fecha) : a.f.fecha.localeCompare(b.f.fecha)));
  }, [p.fotos, p.ubic, p.punto, orden, verUbicadas]);

  const alternar = (a: string) => setMarcadas((m) => (m.includes(a) ? m.filter((x) => x !== a) : [...m, a]));

  return (
    <>
      <header className="border-b p-3">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold uppercase text-amber-700">Nuevo punto</p>
            <h2 className="font-bold">{calle && calle.distancia < 40 ? calle.nombre : "Sin calle cercana"}</h2>
            {cerca.length > 0 && <p className="text-xs text-stone-600">Cerca de: {cerca.map((c) => c.nombre).join(", ")}</p>}
            <p className="text-xs text-stone-500">
              Cámara mirando: {p.punto.rumbo === null ? "sin indicar (arrastra al marcar)" : `${nombreRumbo(p.punto.rumbo)} (${Math.round(p.punto.rumbo)}°)`}
            </p>
          </div>
          <button onClick={p.onCerrar} className="text-xl leading-none text-stone-500">×</button>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-3 text-xs">
          <label className="flex items-center gap-1">
            Ordenar:
            <select value={orden} onChange={(e) => setOrden(e.target.value as "cerca" | "hora")} className="rounded border px-1">
              <option value="cerca">más cerca según GPS</option>
              <option value="hora">por hora</option>
            </select>
          </label>
          <label className="flex items-center gap-1">
            <input type="checkbox" checked={verUbicadas} onChange={(e) => setVerUbicadas(e.target.checked)} /> incluir ya ubicadas
          </label>
        </div>
      </header>
      <div ref={ref} className="grid flex-1 grid-cols-3 content-start gap-2 overflow-y-auto p-3">
        {lista.map(({ f, d }) => (
          <Miniatura
            key={f.archivo}
            archivo={f.archivo}
            foto={f}
            marcada={marcadas.includes(f.archivo)}
            extra={`${Number.isFinite(d) ? `· GPS ${Math.round(d)} m` : ""}${p.ubic[f.archivo] ? " · ya ubicada" : ""}`}
            onClick={() => alternar(f.archivo)}
            onVer={() => p.onVer(lista.map((x) => x.f.archivo), lista.findIndex((x) => x.f.archivo === f.archivo))}
          />
        ))}
        {lista.length === 0 && <p className="col-span-3 text-sm text-stone-500">No quedan fotos sin ubicar.</p>}
      </div>
      <footer className="space-y-2 border-t p-3">
        <input
          value={nota}
          onChange={(e) => setNota(e.target.value)}
          placeholder="Nota opcional (p. ej. «fachada esquina, casa azul»)"
          className="w-full rounded border px-2 py-1 text-sm"
        />
        <button
          disabled={!marcadas.length}
          onClick={() => p.onAsignar(marcadas, nota)}
          className="w-full rounded-lg bg-amber-600 py-2 font-semibold text-white disabled:opacity-40"
        >
          Poner {marcadas.length || ""} foto{marcadas.length === 1 ? "" : "s"} aquí
        </button>
      </footer>
    </>
  );
}

function PanelGrupo(p: {
  tipo: "grupo" | "gps";
  archivos: string[];
  porArchivo: Map<string, FotoIndice>;
  ubic: Ubicaciones;
  onCerrar: () => void;
  onVer: (lista: string[], i: number) => void;
  onMover: (archivos: string[]) => void;
  onQuitar: (archivos: string[]) => void;
  onNota: (archivos: string[], nota: string) => void;
  onAceptarGPS: (archivos: string[]) => void;
}) {
  const [marcadas, setMarcadas] = useState<string[]>([]);
  const u = p.ubic[p.archivos[0]];
  const [nota, setNota] = useState(u?.nota ?? "");
  useEffect(() => { setMarcadas([]); setNota(p.ubic[p.archivos[0]]?.nota ?? ""); }, [p.archivos, p.ubic]);
  const objetivo = marcadas.length ? marcadas : p.archivos;
  const alternar = (a: string) => setMarcadas((m) => (m.includes(a) ? m.filter((x) => x !== a) : [...m, a]));

  return (
    <>
      <header className="border-b p-3">
        <div className="flex items-start justify-between">
          <div>
            {p.tipo === "gps" ? (
              <>
                <p className="text-xs font-semibold uppercase text-slate-500">GPS del celular (aproximado)</p>
                <h2 className="font-bold">{p.archivos.length === 1 ? "Foto sin confirmar" : `${p.archivos.length} fotos sin confirmar`}</h2>
                <p className="text-xs text-stone-600">
                  El celular la registró aquí. Si coincide con lo que ves en la foto, acéptala; si no, cierra este panel y arrastra el punto a su sitio.
                </p>
              </>
            ) : (
              <>
                <p className="text-xs font-semibold uppercase text-amber-700">{p.archivos.length} foto(s) en este punto</p>
                <h2 className="font-bold">{u?.calle || "Sin calle cercana"}</h2>
                {u?.cerca?.length ? <p className="text-xs text-stone-600">Cerca de: {u.cerca.join(", ")}</p> : null}
                <p className="text-xs text-stone-500">
                  {u?.rumbo != null ? `Mirando ${nombreRumbo(u.rumbo)} (${u.rumbo}°)` : "Dirección sin indicar"} · {u?.origen === "gps" ? "posición GPS" : "posición manual"} ·{" "}
                  {u?.lat.toFixed(6)}, {u?.lon.toFixed(6)}
                </p>
              </>
            )}
          </div>
          <button onClick={p.onCerrar} className="text-xl leading-none text-stone-500">×</button>
        </div>
      </header>
      <div className="grid flex-1 grid-cols-3 content-start gap-2 overflow-y-auto p-3">
        {p.archivos.map((a, i) => (
          <Miniatura
            key={a}
            archivo={a}
            foto={p.porArchivo.get(a)}
            marcada={marcadas.includes(a)}
            onClick={() => alternar(a)}
            onVer={() => p.onVer(p.archivos, i)}
          />
        ))}
      </div>
      <footer className="space-y-2 border-t p-3 text-sm">
        <p className="text-xs text-stone-500">
          {marcadas.length ? `${marcadas.length} seleccionada(s)` : "Sin selección: las acciones aplican a todas"} · clic en una miniatura para seleccionar
        </p>
        {p.tipo === "gps" ? (
          <button onClick={() => p.onAceptarGPS(objetivo)} className="w-full rounded-lg bg-slate-700 py-2 font-semibold text-white">
            Aceptar posición GPS ({objetivo.length})
          </button>
        ) : (
          <>
            <div className="flex gap-2">
              <input value={nota} onChange={(e) => setNota(e.target.value)} placeholder="Nota" className="flex-1 rounded border px-2 py-1" />
              <button onClick={() => p.onNota(objetivo, nota)} className="rounded border px-2">Guardar nota</button>
            </div>
            <div className="flex gap-2">
              <button onClick={() => p.onMover(objetivo)} className="flex-1 rounded-lg bg-amber-600 py-2 font-semibold text-white">
                Mover ({objetivo.length})
              </button>
              <button onClick={() => p.onQuitar(objetivo)} className="flex-1 rounded-lg border border-red-300 py-2 font-semibold text-red-700">
                Quitar ({objetivo.length})
              </button>
            </div>
          </>
        )}
      </footer>
    </>
  );
}
