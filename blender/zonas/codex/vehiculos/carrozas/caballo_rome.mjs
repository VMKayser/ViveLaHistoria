const ajustarFase = fase => ((fase % 1) + 1) % 1;

export function animarCaballoRome(escena, clips, AnimationMixer) {
  const contrato = escena.getObjectByName('caballo_rome').userData.clips;
  const mixer = new AnimationMixer(escena);
  const acciones = clips.map(clip => {
    const accion = mixer.clipAction(clip).play();
    accion.paused = true;
    accion.weight = Number(clip.name === 'reposo');
    return { accion, nombre:clip.name, duracion:clip.duration, zancada:contrato[clip.name].zancada_m, fase:0 };
  });

  const avanzar = (marcha, distancia, dt) => {
    const mezcla = 1-Math.exp(-13*dt);
    for (const estado of acciones) {
      const { accion, nombre, duracion, zancada } = estado;
      const activo = marcha===nombre;
      if (zancada && (activo || accion.weight>.001)) {
        estado.fase = ajustarFase(estado.fase+distancia/zancada);
      }
      accion.time = duracion*estado.fase;
      accion.weight += (Number(activo)-accion.weight)*mezcla;
    }
    mixer.update(0);
  };
  avanzar.detener = () => {
    mixer.stopAllAction();
    mixer.uncacheRoot(escena);
  };
  return avanzar;
}
