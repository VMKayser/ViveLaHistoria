#!/usr/bin/env node
// Captura de una página con Chrome sin ventana (perfil propio, no toca el Chrome del usuario), por CDP.
// Sirve para comparar la ciudad Godot web contra capturas de referencia y para revisar a pie.
//   node ciudad3d/herramientas/captura_web.mjs --url http://localhost:3000/ciudad --salida a.png [--antes "js"]
//        [--recargar] [--esperar 20] [--orden "js" --esperar-orden 6] [--ancho 1280 --alto 720] [--gpu] [--eval "js que devuelve texto"]
//        [--final "js que devuelve texto"]   (se evalúa al terminar, después de la serie)
//        [--serie tomas.json]   (varias capturas en la misma carga: [{"orden": "js", "salida": "a.png"}, …], cada una tras --esperar-orden)
// --antes: JavaScript que se ejecuta al cargar (p. ej. guardar algo en sessionStorage); con --recargar se recarga después.
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const arg = (n, d) => {
  const i = process.argv.indexOf("--" + n);
  return i < 0 ? d : process.argv[i + 1];
};
const tiene = (n) => process.argv.includes("--" + n);
const url = arg("url");
const salida = arg("salida", "captura.png");
const ancho = Number(arg("ancho", 1280)), alto = Number(arg("alto", 720));
const esperar = Number(arg("esperar", 20)) * 1000;
const puerto = 9300 + Math.floor(Math.random() * 500);
const perfil = mkdtempSync(join(tmpdir(), "captura-web-"));
const banderas = [`--headless=new`, `--remote-debugging-port=${puerto}`, `--user-data-dir=${perfil}`, `--window-size=${ancho},${alto}`,
  "--no-first-run", "--no-default-browser-check", "--hide-scrollbars", "--mute-audio",
  ...(tiene("gpu") ? ["--use-angle=gl", "--enable-gpu", "--ignore-gpu-blocklist"] : ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]),
  "about:blank"];
const chrome = spawn("google-chrome", banderas, { stdio: "ignore" });
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));

try {
  let pag;
  for (let k = 0; k < 50 && !pag; k++) {
    await dormir(200);
    try {
      pag = (await (await fetch(`http://127.0.0.1:${puerto}/json/list`)).json()).find((t) => t.type === "page");
    } catch { /* todavía arrancando */ }
  }
  if (!pag) throw new Error("Chrome no arrancó");
  const ws = new WebSocket(pag.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener("open", r));
  let id = 0;
  const pend = new Map();
  ws.addEventListener("message", (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); }
    if (m.method === "Runtime.consoleAPICalled" && tiene("consola")) console.log("[consola]", m.params.args.map((a) => a.value ?? a.description).join(" "));
  });
  const cdp = (method, params = {}) => new Promise((r) => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await cdp("Runtime.enable");
  await cdp("Emulation.setDeviceMetricsOverride", { width: ancho, height: alto, deviceScaleFactor: 1, mobile: false });
  await cdp("Page.enable");
  await cdp("Page.navigate", { url });
  await dormir(1500);
  if (arg("antes")) {
    await cdp("Runtime.evaluate", { expression: arg("antes") });
    if (tiene("recargar")) { await cdp("Page.reload"); await dormir(1500); }
  }
  await dormir(esperar);
  if (arg("orden")) {            // JS que se ejecuta ya cargada la página (p. ej. mover la cámara) y luego otra espera
    await cdp("Runtime.evaluate", { expression: arg("orden") });
    await dormir(Number(arg("esperar-orden", 6)) * 1000);
  }
  if (arg("eval")) {
    const r = await cdp("Runtime.evaluate", { expression: arg("eval"), returnByValue: true, awaitPromise: true });
    console.log(JSON.stringify(r.result?.result?.value ?? r.result));
  }
  if (arg("serie")) {
    for (const t of JSON.parse(readFileSync(arg("serie"), "utf8"))) {
      await cdp("Runtime.evaluate", { expression: t.orden });
      await dormir(Number(arg("esperar-orden", 6)) * 1000);
      const s = await cdp("Page.captureScreenshot", { format: "png" });
      writeFileSync(t.salida, Buffer.from(s.result.data, "base64"));
      console.log("captura →", t.salida);
    }
  }
  if (arg("final")) {
    const r = await cdp("Runtime.evaluate", { expression: arg("final"), returnByValue: true, awaitPromise: true });
    console.log(JSON.stringify(r.result?.result?.value ?? r.result));
  }
  if (!arg("serie")) {
    const shot = await cdp("Page.captureScreenshot", { format: "png" });
    writeFileSync(salida, Buffer.from(shot.result.data, "base64"));
    console.log("captura →", salida);
  }
  ws.close();
} finally {
  chrome.kill("SIGKILL");
  await dormir(300);
  rmSync(perfil, { recursive: true, force: true });
}
