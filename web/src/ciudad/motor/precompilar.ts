// Precompilación de los shaders de la ciudad mientras se descarga el motor.
//
// En la primera visita, Chrome compila y enlaza cada programa de shader que pide Godot (≈40 programas, ≈15 s en total)
// y Godot espera cada uno en el hilo principal: la pantalla de carga se congela de a 1–5 s. La caché de programas es del
// navegador, no del contexto WebGL: si aquí se enlazan los mismos programas en un contexto aparte, en hilos
// (KHR_parallel_shader_compile) y sin esperar el resultado, cuando Godot los pide ya están hechos (como en la segunda
// visita). La lista sale de ciudad3d/herramientas/capturar_shaders.mjs (al exportar) → /ciudad3d/shaders.json.
//
// Si los programas no coinciden con los de este equipo (otro navegador, otros límites de WebGL) no pasa nada: solo no
// ayuda. Sin KHR_parallel_shader_compile no se hace (los enlaces irían en serie delante de los de Godot).

type ListaShaders = { extensiones?: string[]; fuentes: string[]; programas: [number, number][] };

export type Precompilacion = { soltar(): void };

export async function precompilarShaders(url: string): Promise<Precompilacion | null> {
  const lienzo = document.createElement("canvas");
  lienzo.width = lienzo.height = 1;
  const gl = lienzo.getContext("webgl2");
  if (!gl || !gl.getExtension("KHR_parallel_shader_compile")) return null;
  let lista: ListaShaders;
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    lista = await r.json();
  } catch {
    return null;
  }
  // las extensiones habilitadas cambian cómo se traduce el GLSL y por lo tanto la clave de la caché: tienen que ser
  // exactamente las que habilita el contexto de Godot (con todas, la caché no acertaba)
  if (!lista.extensiones) return null;
  for (const e of lista.extensiones) gl.getExtension(e);
  const shaders = new Map<string, WebGLShader>();
  const shader = (tipo: number, src: string) => {
    const clave = tipo + src;
    let s = shaders.get(clave);
    if (!s) {
      s = gl.createShader(tipo)!;
      gl.shaderSource(s, src);
      gl.compileShader(s);
      shaders.set(clave, s);
    }
    return s;
  };
  const programas: WebGLProgram[] = [];
  for (const [v, f] of lista.programas) {
    const p = gl.createProgram()!;
    gl.attachShader(p, shader(gl.VERTEX_SHADER, lista.fuentes[v]));
    gl.attachShader(p, shader(gl.FRAGMENT_SHADER, lista.fuentes[f]));
    gl.linkProgram(p);           // no se consulta el estado: eso obligaría a esperarlo
    programas.push(p);
  }
  gl.flush();
  return {
    // cuando la ciudad ya está lista: los programas ya quedaron en la caché del navegador
    soltar() {
      programas.forEach((p) => gl.deleteProgram(p));
      shaders.forEach((s) => gl.deleteShader(s));
      gl.getExtension("WEBGL_lose_context")?.loseContext();
    },
  };
}
