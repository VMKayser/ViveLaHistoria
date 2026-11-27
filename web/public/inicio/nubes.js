// Animación de presentación en canvas: cámara y arquitectura inmóviles.
// Usa la fotografía ya tratada; no vuelve a generar sus edificios.
class CieloSucre {
  constructor(canvas, src) {
    this.canvas = canvas; this.paused = matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.seconds = 0; this.last = 0; this.visible = true;
    this.image = new Image();
    this.ready = new Promise((resolve, reject) => { this.image.onload = () => { this.setup(); resolve(this); }; this.image.onerror = reject; });
    this.image.src = src;
    new IntersectionObserver(entries => { this.visible = entries[0].isIntersecting; }).observe(canvas);
  }
  setup() {
    this.source = document.createElement('canvas'); this.source.width = this.image.width; this.source.height = this.image.height;
    this.layer = document.createElement('canvas'); this.layer.width = this.image.width; this.layer.height = this.image.height;
    this.mask = document.createElement('canvas'); this.mask.width = this.image.width; this.mask.height = this.image.height;
    const m = this.mask.getContext('2d'), w = this.image.width, h = this.image.height;
    const vertical = m.createLinearGradient(0, 0, 0, h * .445);
    vertical.addColorStop(0, 'white'); vertical.addColorStop(.65, 'white'); vertical.addColorStop(1, 'transparent');
    m.fillStyle = vertical; m.fillRect(0, 0, w, h * .445);
    m.globalCompositeOperation = 'destination-in';
    const edges = m.createLinearGradient(0, 0, w, 0);
    edges.addColorStop(0, 'transparent'); edges.addColorStop(.055, 'white'); edges.addColorStop(.945, 'white'); edges.addColorStop(1, 'transparent');
    m.fillStyle = edges; m.fillRect(0, 0, w, h);
    this.draw(0);
    const tick = time => {
      if (!this.last) this.last = time;
      if (time - this.last > 45) {
        if (!this.paused && this.visible && !document.hidden) { this.seconds += Math.min((time - this.last) / 1000, .12); this.draw(this.seconds); }
        this.last = time;
      }
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    new ResizeObserver(() => this.draw(this.seconds)).observe(this.canvas);
  }
  draw(seconds, exportWidth) {
    const w = this.image.width, h = this.image.height;
    const ctx = this.source.getContext('2d'), sky = this.layer.getContext('2d');
    const phase = seconds / 12 * Math.PI * 2;
    sky.clearRect(0, 0, w, h); sky.globalCompositeOperation = 'source-over';
    sky.drawImage(this.image, Math.sin(phase) * 20, Math.sin(phase) * 2);
    sky.globalCompositeOperation = 'destination-in'; sky.drawImage(this.mask, 0, 0);
    ctx.drawImage(this.image, 0, 0); ctx.drawImage(this.layer, 0, 0);
    const width = exportWidth || Math.ceil(this.canvas.clientWidth * Math.min(devicePixelRatio, 1.5));
    const height = exportWidth ? Math.round(width * h / w) : Math.ceil(this.canvas.clientHeight * Math.min(devicePixelRatio, 1.5));
    if (!width || !height) return;
    this.canvas.width = width; this.canvas.height = height;
    const out = this.canvas.getContext('2d');
    const ratio = Math.max(width / w, height / h), dw = w * ratio, dh = h * ratio;
    const horizontal = this.canvas.clientWidth <= 760 ? .90 : .64;
    out.drawImage(this.source, (width - dw) * horizontal, (height - dh) * .5, dw, dh);
    return this.canvas;
  }
}
window.CieloSucre = CieloSucre;
