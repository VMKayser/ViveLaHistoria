#!/usr/bin/env node
// Captura los programas de shader (GLSL ES que Godot entrega a WebGL) que la ciudad compila al arrancar, para que la
// página los precompile en paralelo mientras baja el motor (web/src/ciudad/motor/precompilar.ts).
//
// Por qué: en la primera visita Chrome compila y enlaza cada programa de nuevo (≈15 s en total, con pausas de 1–5 s en
// las que la página se congela); en la segunda los toma de su caché de programas y la carga baja a la mitad. La caché es
// del navegador, no del contexto: si la página enlaza los mismos programas en un contexto WebGL aparte (en hilos, con
// KHR_parallel_shader_compile) mientras se descargan el wasm y las teselas, cuando Godot los pide ya están hechos.
//
//   node ciudad3d/herramientas/capturar_shaders.mjs [--esperar 60] [--huella h]   → web/public/ciudad3d/shaders.json
// Sirve web/public con un servidor propio (no hace falta npm run dev), abre sucre.html en Chrome sin ventana y anota
// cada linkProgram y las extensiones que habilita (cambian cómo se traduce el GLSL: con otras, la caché no acierta;
// probado el 2026-11-26: con todas las extensiones el segundo enlace tardó 11,5 s, con las de Godot 0,47 s). La corre exportar.mjs después de exportar la web; si un shader cambia y no se recaptura, la página
// precompila programas que ya nadie usa (no rompe nada, solo no ayuda).
import { spawn } from "node:child_process";
import { createReadStream, existsSync, mkdtempSync, rmSync, statSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { dirname, extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "../..");
const PUBLICO = join(RAIZ, "web/public");
const SALIDA = join(PUBLICO, "ciudad3d/shaders.json");
const arg = (n, d) => { const i = process.argv.indexOf("--" + n); return i < 0 ? d : process.argv[i + 1]; };
const esperar = Number(arg("esperar", 60)) * 1000;
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));

// --- servidor estático mínimo de web/public
const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".wasm": "application/wasm", ".json": "application/json",
  ".png": "image/png", ".webp": "image/webp", ".pck": "application/octet-stream", ".bin": "application/octet-stream" };
const servidor = createServer((req, res) => {
  const ruta = normalize(join(PUBLICO, decodeURIComponent(new URL(req.url, "http://x").pathname)));
  if (!ruta.startsWith(PUBLICO) || !existsSync(ruta) || !statSync(ruta).isFile()) { res.writeHead(404).end(); return; }
  res.writeHead(200, { "Content-Type": TIPOS[extname(ruta)] ?? "application/octet-stream" });
  createReadStream(ruta).pipe(res);
});
await new Promise((r) => servidor.listen(0, "127.0.0.1", r));
const url = `http://127.0.0.1:${servidor.address().port}/ciudad3d/sucre.html`;

// --- espía de WebGL: fuentes de cada programa en el orden en que se enlazan
const ESPIA = `(() => {
  const P = WebGL2RenderingContext.prototype, fuentes = new WeakMap(), tipos = new WeakMap(), progs = new WeakMap();
  window.__programas = [];
  window.__extensiones = [];
  const ge = P.getExtension; P.getExtension = function (n) { if (!window.__extensiones.includes(n)) window.__extensiones.push(n); return ge.call(this, n); };
  const cs = P.createShader; P.createShader = function (t) { const s = cs.call(this, t); tipos.set(s, t); return s; };
  const ss = P.shaderSource; P.shaderSource = function (s, src) { fuentes.set(s, src); return ss.call(this, s, src); };
  const at = P.attachShader; P.attachShader = function (p, s) { (progs.get(p) || progs.set(p, []).get(p)).push(s); return at.call(this, p, s); };
  const lk = P.linkProgram; P.linkProgram = function (p) {
    const l = progs.get(p) || [];
    const v = l.find((s) => tipos.get(s) === this.VERTEX_SHADER), f = l.find((s) => tipos.get(s) === this.FRAGMENT_SHADER);
    if (v && f) window.__programas.push([fuentes.get(v), fuentes.get(f)]);
    return lk.call(this, p);
  };
})();`;

const puerto = 9300 + Math.floor(Math.random() * 500);
const perfil = mkdtempSync(join(tmpdir(), "capturar-shaders-"));
const chrome = spawn("google-chrome", [`--headless=new`, `--remote-debugging-port=${puerto}`, `--user-data-dir=${perfil}`,
  "--window-size=1280,720", "--no-first-run", "--mute-audio", "--use-angle=gl", "--enable-gpu", "--ignore-gpu-blocklist",
  "about:blank"], { stdio: "ignore" });
try {
  let pag;
  for (let k = 0; k < 50 && !pag; k++) {
    await dormir(200);
    try { pag = (await (await fetch(`http://127.0.0.1:${puerto}/json/list`)).json()).find((t) => t.type === "page"); } catch { /* arrancando */ }
  }
  if (!pag) throw new Error("Chrome no arrancó");
  const ws = new WebSocket(pag.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener("open", r));
  let id = 0;
  const pend = new Map();
  ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
  const cdp = (method, params = {}) => new Promise((r) => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await cdp("Runtime.enable");
  await cdp("Page.enable");
  await cdp("Page.addScriptToEvaluateOnNewDocument", { source: ESPIA });
  await cdp("Page.navigate", { url });
  await dormir(esperar);
  const r = await cdp("Runtime.evaluate", { expression: "JSON.stringify([window.__programas || [], window.__extensiones || []])", returnByValue: true });
  const [lista, extensiones] = JSON.parse(r.result?.result?.value ?? "[[], []]");
  // sin repetidos, en el orden de uso (los primeros son los que Godot pide antes)
  const vistos = new Set();
  const programas = lista.filter(([v, f]) => { const k = v + "\u0000" + f; if (vistos.has(k)) return false; vistos.add(k); return true; });
  if (programas.length < 10) throw new Error(`solo ${programas.length} programas: ¿arrancó la ciudad?`);
  // los vértices se repiten mucho entre programas: se guardan una vez
  const fuentes = [], indice = new Map();
  const ref = (s) => { if (!indice.has(s)) { indice.set(s, fuentes.length); fuentes.push(s); } return indice.get(s); };
  const pares = programas.map(([v, f]) => [ref(v), ref(f)]);
  writeFileSync(SALIDA, JSON.stringify({ fecha: new Date().toISOString(), huella: arg("huella", null), extensiones, fuentes, programas: pares }));
  console.log(`shaders: ${pares.length} programas, ${fuentes.length} fuentes → ${SALIDA} (${(statSync(SALIDA).size / 1e6).toFixed(1)} MB)`);
} finally {
  chrome.kill();
  servidor.close();
  await dormir(800);
  rmSync(perfil, { recursive: true, force: true });
}
