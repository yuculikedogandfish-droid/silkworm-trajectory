
(function () {
  if (document.body.classList.contains('embed')) return;

  const MODEL = 'habitat-demo-0.1';
  const habitat = {
    shape: 'square',
    tempC: 25,
    humidity: 65,
    seed: 1,
    simTime: 0,
    runningClock: false,
    tool: 'worm',
    selected: null,
    selectedLeaf: null,
    agents: [],
    orphans: [],
    obstacles: [],
    reference: null,
    undo: [],
    drag: null,
    mistPhase: 0,
  };

  const habViewport = {
    zoom: 1,
    panX: 0,
    panY: 0,
    panMode: false,
  };

  /* 本脚本块独立作用域：单位向量工具需在本块内定义 */
  function safeUnit(x, y) {
    const len = Math.hypot(x, y);
    if (!Number.isFinite(len) || len < 1e-6) return { x: 0, y: -1 };
    return { x: x / len, y: y / len };
  }

  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      let t = Math.imul(a ^ a >>> 15, 1 | a);
      t ^= t + Math.imul(t ^ t >>> 7, 61 | t);
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  function arenaSpec() {
    if (habitat.shape === 'rect') return { kind: 'rect', hw: 220, hh: 140 };
    if (habitat.shape === 'circle') return { kind: 'circle', r: 180 };
    return { kind: 'square', hw: 180, hh: 180 };
  }

  function insideArena(x, y, pad) {
    const a = arenaSpec();
    const p = pad || 0;
    if (a.kind === 'circle') return x * x + y * y <= (a.r - p) * (a.r - p);
    return Math.abs(x) <= a.hw - p && Math.abs(y) <= a.hh - p;
  }

  function inLeaf(x, y, leaf, pad) {
    const extra = pad || 0;
    const dx = x - leaf.x, dy = y - leaf.y;
    const c = Math.cos(-leaf.rot), s = Math.sin(-leaf.rot);
    const lx = dx * c - dy * s;
    const ly = dx * s + dy * c;
    const rx = leaf.rx + extra, ry = leaf.ry + extra;
    return (lx * lx) / (rx * rx) + (ly * ly) / (ry * ry) < 1;
  }

  function blocked(x, y) {
    if (!insideArena(x, y, 10)) return true;
    return habitat.obstacles.some(leaf => inLeaf(x, y, leaf, 8));
  }

  let toastTimer = 0;
  function toast(msg, kind) {
    const el = document.getElementById('habToast');
    if (!el) return;
    el.textContent = msg;
    el.className = 'show' + (kind ? ' ' + kind : '');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { el.className = ''; }, 2600);
  }

  function hint(msg) {
    const el = document.getElementById('habHint');
    if (el) el.textContent = msg;
  }

  const ghost = document.getElementById('habGhost');

  function drive() {
    const t = habitat.tempC;
    const h = habitat.humidity / 100;
    const tempDelta = t - 25;
    const speed = 22 * (1 + tempDelta * 0.035) * (0.72 + h * 0.45);
    const sway = 0.55 + Math.abs(tempDelta) * 0.03 + (1 - h) * 0.65;
    const pauseChance = Math.min(0.35, Math.abs(tempDelta) * 0.012 + (h < 0.45 ? 0.08 : 0));
    const silkAlpha = 0.22 + h * 0.18;
    return { speed, sway, pauseChance, silkAlpha, version: MODEL };
  }

  function pushUndo() {
    habitat.undo.push(JSON.stringify({
      agents: habitat.agents,
      orphans: habitat.orphans,
      obstacles: habitat.obstacles,
    }));
    if (habitat.undo.length > 24) habitat.undo.shift();
  }

  function makeRandomDemo() {
    const n = habitat.agents.filter(a => a.kind === 'random').length + 1;
    habitat.agents.push({
      id: 'sw-' + n,
      kind: 'random',
      wormId: null,
      mode: 'bench',
      bodyVisible: true,
      x: 0, y: 0, heading: -Math.PI / 2,
      silk: [],
      phase: n * 1.7,
      turnSign: n % 2 ? 1 : -1,
      pauseUntil: 0,
      speedScale: 1,
    });
  }

  function normalizeRoute(raw) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    raw.forEach(p => {
      minX = Math.min(minX, p.x); minY = Math.min(minY, p.y);
      maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y);
    });
    const span = Math.max(maxX - minX, maxY - minY) || 1;
    const s = 110 / span;
    const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    return raw.map(p => ({ x: (p.x - cx) * s, y: (p.y - cy) * s }));
  }

  function transformRoute(agent) {
    const cs = Math.cos(agent.rot || 0);
    const sn = Math.sin(agent.rot || 0);
    const sc = agent.scale || 1;
    return agent.route.map(p => {
      const lx = p.x * sc, ly = p.y * sc;
      return {
        x: lx * cs - ly * sn + (agent.offX || 0),
        y: lx * sn + ly * cs + (agent.offY || 0),
      };
    });
  }

  function applyRouteTransform(agent) {
    const pts = transformRoute(agent);
    agent.routeWorld = pts;
    agent.silk = pts.slice().reverse();
    const h = pts[0];
    agent.x = h.x;
    agent.y = h.y;
    const n = pts[Math.min(1, pts.length - 1)];
    agent.heading = Math.atan2(n.y - h.y, n.x - h.x);
  }

  function sampleRoute(agent, u) {
    const pts = agent.routeWorld || agent.silk;
    if (!pts.length) return { x: agent.x, y: agent.y };
    const f = Math.max(0, Math.min(1, u)) * (pts.length - 1);
    const i = Math.floor(f);
    const t = f - i;
    const a = pts[i];
    const b = pts[Math.min(pts.length - 1, i + 1)];
    return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
  }

  function measuredSource() {
    const pushed = window.__previewTrajs;
    if (Array.isArray(pushed) && pushed.length) return pushed;
    try {
      const payload = buildPreviewPayload();
      if (payload && Array.isArray(payload.trajectories) && payload.trajectories.length) return payload.trajectories;
    } catch (_) { /* 描图器还没数据 */ }
    return [];
  }

  function syncMeasured() {
    const srcs = measuredSource();
    const valid = srcs.map((t, i) => ({
      t, i,
      raw: (t.points || []).filter(p => p && Number.isFinite(p.x) && Number.isFinite(p.y)),
    })).filter(x => x.raw.length >= 2);
    const seen = new Set();
    valid.forEach(({ t, i, raw }, order) => {
      const wid = t.wormId != null ? t.wormId : i + 1;
      seen.add(wid);
      const route = normalizeRoute(raw);
      const existing = habitat.agents.find(a => a.kind === 'route' && a.wormId === wid);
      if (existing) {
        existing.route = route;
        existing.color = t.color || existing.color;
        applyRouteTransform(existing);
        if (existing.mode === 'bench' || existing.mode === 'drag') existing.mode = 'idle';
      } else {
        const agent = {
          id: 'rt-' + wid,
          kind: 'route',
          wormId: wid,
          color: t.color || '#d4c4a8',
          mode: 'idle',
          bodyVisible: true,
          route: route,
          offX: (order - (valid.length - 1) / 2) * 26,
          offY: 0,
          rot: 0,
          scale: 1,
          follow: false,
          u: 0,
          phase: 0,
          turnSign: 1,
          pauseUntil: 0,
          speedScale: 1,
          silk: [],
          x: 0, y: 0, heading: 0,
        };
        applyRouteTransform(agent);
        habitat.agents.push(agent);
      }
    });
    habitat.agents = habitat.agents.filter(a => a.kind !== 'route' || seen.has(a.wormId));
    renderList();
    syncRoutePanel();
    return valid.length;
  }

  function importMeasuredTrajectories() {
    const n = syncMeasured();
    if (!n) toast('还没描好的实测轨迹：先在上方描线，再回到这里。', 'err');
    else toast('已同步 ' + n + ' 条实测轨迹到场地。', 'ok');
  }

  const bg = document.getElementById('habBg');
  const far = document.getElementById('habLeaves');
  const mist = document.getElementById('habMist');
  const world = document.getElementById('habWorld');
  const depth = document.getElementById('habDepth');
  const wrap = document.getElementById('habWorldWrap');

  function fit(canvas, scale) {
    const r = wrap.getBoundingClientRect();
    const w = Math.max(2, Math.floor(r.width * (scale || 1)));
    const h = Math.max(2, Math.floor(r.height * (scale || 1)));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    return { w, h, cssW: r.width, cssH: r.height };
  }

  function view() {
    const w = world.width, h = world.height;
    const a = arenaSpec();
    const span = a.kind === 'circle' ? a.r * 2 : Math.max(a.hw, a.hh) * 2;
    const baseScale = Math.min(w, h) / (span * 1.35);
    const s = baseScale * habViewport.zoom;
    const cx = w / 2 + habViewport.panX;
    const cy = h / 2 + habViewport.panY;
    return {
      w, h, s, cx, cy,
      px: x => cx + x * s,
      py: y => cy + y * s,
    };
  }

  function screenToHab(ev) {
    const rect = world.getBoundingClientRect();
    const sx = (ev.clientX - rect.left) * (world.width / rect.width);
    const sy = (ev.clientY - rect.top) * (world.height / rect.height);
    const v = view();
    return { x: (sx - v.cx) / v.s, y: (sy - v.cy) / v.s, sx, sy };
  }

  function updateHabZoomLabel() {
    const el = document.getElementById('habZoomLabel');
    if (el) el.textContent = Math.round(habViewport.zoom * 100) + '%';
  }

  function zoomAt(sx, sy, factor) {
    if (!world.width || !world.height) return;
    const before = view();
    const wx = (sx - before.cx) / before.s;
    const wy = (sy - before.cy) / before.s;
    habViewport.zoom = Math.max(0.12, Math.min(8, habViewport.zoom * factor));
    const after = view();
    habViewport.panX += sx - (after.cx + wx * after.s);
    habViewport.panY += sy - (after.cy + wy * after.s);
    updateHabZoomLabel();
  }

  function resetHabView() {
    habViewport.zoom = 1;
    habViewport.panX = 0;
    habViewport.panY = 0;
    updateHabZoomLabel();
  }

  function drawLeaf(ctx, x, y, rot, rx, ry, fill) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.beginPath();
    ctx.moveTo(0, -ry);
    ctx.bezierCurveTo(rx, -ry * 0.25, rx * 0.72, ry * 0.45, 0, ry);
    ctx.bezierCurveTo(-rx * 0.72, ry * 0.45, -rx, -ry * 0.25, 0, -ry);
    ctx.shadowColor = 'rgba(0,0,0,0.30)';
    ctx.shadowBlur = 7;
    ctx.shadowOffsetY = 2;

    ctx.fillStyle = fill;
    ctx.fill();

    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;
    ctx.beginPath();
    ctx.moveTo(0, -ry * 0.8);
    ctx.lineTo(0, ry * 0.75);
    ctx.strokeStyle = 'rgba(180,196,176,0.18)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.restore();
  }

  function drawBackdropLeaf(ctx, x, y, rot, rx, ry, opacity) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.globalAlpha = opacity;

    ctx.shadowColor = 'rgba(0,0,0,0.34)';
    ctx.shadowBlur = 18;

    ctx.beginPath();
    ctx.moveTo(0, -ry);
    ctx.bezierCurveTo(
      rx * 0.92, -ry * 0.28,
      rx * 0.72, ry * 0.48,
      0, ry
    );
    ctx.bezierCurveTo(
      -rx * 0.72, ry * 0.48,
      -rx * 0.92, -ry * 0.28,
      0, -ry
    );

    const grad = ctx.createLinearGradient(-rx, 0, rx, 0);
    grad.addColorStop(0, 'rgba(17,35,29,0.92)');
    grad.addColorStop(0.48, 'rgba(42,70,52,0.86)');
    grad.addColorStop(1, 'rgba(16,31,27,0.92)');

    ctx.fillStyle = grad;
    ctx.fill();

    ctx.shadowBlur = 0;
    ctx.strokeStyle = 'rgba(142,171,139,0.20)';
    ctx.lineWidth = 1;

    ctx.beginPath();
    ctx.moveTo(0, -ry * 0.88);
    ctx.quadraticCurveTo(0, 0, 0, ry * 0.88);
    ctx.stroke();

    for (let i = 0; i < 6; i++) {
      const t = -0.55 + i * 0.19;
      const yy = t * ry;
      const spread = rx * (0.28 + 0.28 * Math.cos(t * 1.35));
      const side = i % 2 ? -1 : 1;

      ctx.beginPath();
      ctx.moveTo(0, yy);
      ctx.quadraticCurveTo(
        side * spread * 0.48,
        yy - ry * 0.05,
        side * spread,
        yy - ry * 0.18
      );

      ctx.strokeStyle = 'rgba(160,184,148,0.12)';
      ctx.lineWidth = 0.8;
      ctx.stroke();
    }

    ctx.restore();
  }

  function paintStatic() {
    fit(bg, 1);
    fit(far, 1);

    const w = bg.width;
    const h = bg.height;
    const g = bg.getContext('2d');

    g.clearRect(0, 0, w, h);

    const base = g.createLinearGradient(0, 0, w, h);
    base.addColorStop(0, '#080e0d');
    base.addColorStop(0.48, '#0a1210');
    base.addColorStop(1, '#060a0a');

    g.fillStyle = base;
    g.fillRect(0, 0, w, h);

    const glow = g.createRadialGradient(
      w * 0.50, h * 0.48, w * 0.04,
      w * 0.50, h * 0.48, w * 0.76
    );
    glow.addColorStop(0, 'rgba(30,51,42,0.40)');
    glow.addColorStop(0.56, 'rgba(17,31,27,0.20)');
    glow.addColorStop(1, 'rgba(0,0,0,0)');

    g.fillStyle = glow;
    g.fillRect(0, 0, w, h);

    const vignette = g.createRadialGradient(
      w * 0.50, h * 0.48, w * 0.30,
      w * 0.50, h * 0.48, w * 0.78
    );
    vignette.addColorStop(0, 'rgba(0,0,0,0)');
    vignette.addColorStop(1, 'rgba(0,0,0,0.42)');

    g.fillStyle = vignette;
    g.fillRect(0, 0, w, h);

    const f = far.getContext('2d');
    f.clearRect(0, 0, w, h);

    // 叶片只放在边缘，中央保持干净
    f.save();
    f.filter = 'blur(1.4px)';

    const decor = [
      [0.055, 0.20, -0.58, 82, 154, 0.28],
      [0.93, 0.17, 0.62, 76, 142, 0.24],
      [0.045, 0.82, 0.72, 70, 132, 0.22],
      [0.955, 0.80, -0.66, 88, 164, 0.25],
      [0.25, 0.015, 1.08, 44, 88, 0.14],
      [0.77, 0.99, -1.04, 48, 96, 0.14]
    ];

    decor.forEach(d => {
      drawBackdropLeaf(
        f,
        d[0] * w,
        d[1] * h,
        d[2],
        d[3],
        d[4],
        d[5]
      );
    });

    f.restore();
  }

  function paintMist() {
    // 用稳定的低频柔光，不再逐帧绘制颗粒噪声
    const m = fit(mist, 0.22);
    const ctx = mist.getContext('2d');

    ctx.clearRect(0, 0, m.w, m.h);

    const glowA = ctx.createRadialGradient(
      m.w * 0.30, m.h * 0.28, 0,
      m.w * 0.30, m.h * 0.28, m.w * 0.52
    );

    glowA.addColorStop(0, 'rgba(126,164,139,0.10)');
    glowA.addColorStop(1, 'rgba(126,164,139,0)');

    ctx.fillStyle = glowA;
    ctx.fillRect(0, 0, m.w, m.h);

    const glowB = ctx.createRadialGradient(
      m.w * 0.76, m.h * 0.72, 0,
      m.w * 0.76, m.h * 0.72, m.w * 0.42
    );

    glowB.addColorStop(0, 'rgba(104,137,120,0.055)');
    glowB.addColorStop(1, 'rgba(104,137,120,0)');

    ctx.fillStyle = glowB;
    ctx.fillRect(0, 0, m.w, m.h);
  }

  function paintDepth() {
    const d = fit(depth, 1);
    const ctx = depth.getContext('2d');

    ctx.clearRect(0, 0, d.w, d.h);
    ctx.save();

    // 前景叶片：靠边、较大、较模糊
    ctx.filter = 'blur(2.8px)';

    drawBackdropLeaf(
      ctx, -d.w * 0.015, d.h * 0.82,
      -0.74, d.w * 0.075, d.h * 0.24, 0.22
    );

    drawBackdropLeaf(
      ctx, d.w * 1.015, d.h * 0.84,
      0.70, d.w * 0.07, d.h * 0.23, 0.20
    );

    drawBackdropLeaf(
      ctx, d.w * 0.14, -d.h * 0.045,
      1.18, d.w * 0.045, d.h * 0.14, 0.12
    );

    drawBackdropLeaf(
      ctx, d.w * 0.88, -d.h * 0.035,
      -1.08, d.w * 0.05, d.h * 0.15, 0.11
    );

    ctx.filter = 'none';

    // 环境光：很弱的中央光照
    ctx.globalCompositeOperation = 'screen';

    const light = ctx.createLinearGradient(
      d.w * 0.48, 0,
      d.w * 0.62, d.h
    );

    light.addColorStop(0, 'rgba(170,190,160,0.018)');
    light.addColorStop(0.5, 'rgba(170,190,160,0.026)');
    light.addColorStop(1, 'rgba(170,190,160,0)');

    ctx.fillStyle = light;
    ctx.fillRect(
      d.w * 0.32, 0,
      d.w * 0.42, d.h
    );

    ctx.globalCompositeOperation = 'source-over';

    // 最外层暗角
    const vignette = ctx.createRadialGradient(
      d.w * 0.5, d.h * 0.5, d.w * 0.25,
      d.w * 0.5, d.h * 0.5, d.w * 0.72
    );

    vignette.addColorStop(0, 'rgba(0,0,0,0)');
    vignette.addColorStop(0.72, 'rgba(0,0,0,0.025)');
    vignette.addColorStop(1, 'rgba(0,0,0,0.20)');

    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, d.w, d.h);

    ctx.restore();
  }

  function drawSilk(ctx, pts, v, alpha) {
    if (!pts || pts.length < 2) return;
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = 'rgba(226,230,228,' + alpha + ')';
    ctx.lineWidth = 0.7;
    ctx.beginPath();
    ctx.moveTo(v.px(pts[0].x), v.py(pts[0].y));
    for (let i = 1; i < pts.length; i++) ctx.lineTo(v.px(pts[i].x), v.py(pts[i].y));
    ctx.stroke();
    ctx.restore();
  }

  function drawHabitatWorm(ctx, agent, v) {
    if (!agent.bodyVisible || agent.mode === 'bench') return;

    const bodyLen = 78;
    const pts = [{ x: agent.x, y: agent.y }];
    let acc = 0;

    for (let i = agent.silk.length - 1; i >= 0 && acc < bodyLen; i--) {
      const b = agent.silk[i];
      const a = pts[pts.length - 1];
      const seg = Math.hypot(b.x - a.x, b.y - a.y) * v.s;

      if (seg < 0.4) continue;

      if (acc + seg >= bodyLen) {
        const u = (bodyLen - acc) / seg;
        pts.push({
          x: a.x + (b.x - a.x) * u,
          y: a.y + (b.y - a.y) * u
        });
        acc = bodyLen;
      } else {
        pts.push(b);
        acc += seg;
      }
    }

    if (acc < bodyLen) {
      pts.push({
        x: agent.x - Math.cos(agent.heading) * ((bodyLen - acc) / v.s),
        y: agent.y - Math.sin(agent.heading) * ((bodyLen - acc) / v.s)
      });
    }

    const scr = pts.map(p => ({
      x: v.px(p.x),
      y: v.py(p.y)
    }));

    for (let i = 0; i < scr.length; i++) {
      const prev = scr[Math.max(0, i - 1)];
      const next = scr[Math.min(scr.length - 1, i + 1)];
      const t = safeUnit(next.x - prev.x, next.y - prev.y);

      scr[i].tx = t.x;
      scr[i].ty = t.y;
      scr[i].nx = -t.y;
      scr[i].ny = t.x;
    }

    for (let i = 1; i < scr.length; i++) {
      if (scr[i - 1].nx * scr[i].nx +
          scr[i - 1].ny * scr[i].ny < 0) {
        scr[i].nx *= -1;
        scr[i].ny *= -1;
      }
    }

    const maxHalf = 6.4;

    const widthAt = t => {
      if (t < 0.12) {
        const q = Math.max(0, Math.min(1, t / 0.12));
        return 0.40 + 0.42 * q * q * (3 - 2 * q);
      }
      if (t < 0.24) {
        const q = (t - 0.12) / 0.12;
        return 0.82 + 0.18 * q * q * (3 - 2 * q);
      }
      if (t < 0.78) {
        return 1 - 0.05 * ((t - 0.24) / 0.54);
      }
      if (t < 0.90) {
        const q = (t - 0.78) / 0.12;
        return 0.95 - 0.20 * q * q * (3 - 2 * q);
      }
      const q = (t - 0.90) / 0.10;
      return 0.75 - 0.70 * q * q * (3 - 2 * q);
    };

    const hw = i => widthAt(
      i / Math.max(1, scr.length - 1)
    ) * maxHalf;

    const left = [];
    const right = [];

    for (let i = 0; i < scr.length; i++) {
      left.push({
        x: scr[i].x + scr[i].nx * hw(i),
        y: scr[i].y + scr[i].ny * hw(i)
      });
      right.push({
        x: scr[i].x - scr[i].nx * hw(i),
        y: scr[i].y - scr[i].ny * hw(i)
      });
    }

    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;

    scr.forEach(p => {
      minX = Math.min(minX, p.x - maxHalf);
      minY = Math.min(minY, p.y - maxHalf);
      maxX = Math.max(maxX, p.x + maxHalf);
      maxY = Math.max(maxY, p.y + maxHalf);
    });

    ctx.save();
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    ctx.beginPath();
    ctx.moveTo(left[0].x, left[0].y);

    for (let i = 1; i < left.length; i++) {
      const a = left[i - 1];
      const b = left[i];
      ctx.quadraticCurveTo(
        a.x, a.y,
        (a.x + b.x) * 0.5,
        (a.y + b.y) * 0.5
      );
    }

    ctx.lineTo(left[left.length - 1].x, left[left.length - 1].y);
    ctx.lineTo(right[right.length - 1].x, right[right.length - 1].y);

    for (let i = right.length - 1; i > 0; i--) {
      const a = right[i];
      const b = right[i - 1];
      ctx.quadraticCurveTo(
        a.x, a.y,
        (a.x + b.x) * 0.5,
        (a.y + b.y) * 0.5
      );
    }

    ctx.lineTo(right[0].x, right[0].y);
    ctx.closePath();

    const bodyGrad = ctx.createLinearGradient(
      minX, minY, maxX, maxY
    );
    bodyGrad.addColorStop(0, '#fffdf6');
    bodyGrad.addColorStop(0.26, '#f2f0e8');
    bodyGrad.addColorStop(0.62, '#e6e3d9');
    bodyGrad.addColorStop(1, '#c7c3b9');

    ctx.save();

    ctx.shadowColor = 'rgba(0,0,0,0.34)';
    ctx.shadowBlur = 5;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 2;

    ctx.fillStyle = bodyGrad;
    ctx.fill();

    ctx.restore();

    ctx.strokeStyle = 'rgba(126,122,113,0.30)';
    ctx.lineWidth = 0.68;
    ctx.stroke();

    ctx.save();
    ctx.clip();

    ctx.strokeStyle = 'rgba(255,255,250,0.46)';
    ctx.lineWidth = maxHalf * 0.40;
    ctx.beginPath();
    ctx.moveTo(scr[0].x, scr[0].y);

    for (let i = 1; i < scr.length; i++) {
      const a = scr[i - 1];
      const b = scr[i];
      ctx.quadraticCurveTo(
        a.x, a.y,
        (a.x + b.x) * 0.5,
        (a.y + b.y) * 0.5
      );
    }
    ctx.stroke();

    const ringTs = [
      0.14, 0.22, 0.30, 0.38, 0.46,
      0.54, 0.62, 0.70, 0.78, 0.85
    ];

    ringTs.forEach(t => {
      const f = t * (scr.length - 1);
      const i = Math.min(scr.length - 1, Math.floor(f));
      const j = Math.min(scr.length - 1, i + 1);
      const q = f - i;

      const tangent = safeUnit(
        scr[i].tx + (scr[j].tx - scr[i].tx) * q,
        scr[i].ty + (scr[j].ty - scr[i].ty) * q
      );

      const normal = safeUnit(
        scr[i].nx + (scr[j].nx - scr[i].nx) * q,
        scr[i].ny + (scr[j].ny - scr[i].ny) * q
      );

      const p = {
        x: scr[i].x + (scr[j].x - scr[i].x) * q,
        y: scr[i].y + (scr[j].y - scr[i].y) * q
      };

      const w = maxHalf * widthAt(t) * 0.88;

      ctx.beginPath();
      ctx.moveTo(
        p.x + normal.x * w,
        p.y + normal.y * w
      );
      ctx.quadraticCurveTo(
        p.x + tangent.x * 1.2,
        p.y + tangent.y * 1.2,
        p.x - normal.x * w,
        p.y - normal.y * w
      );

      ctx.strokeStyle = 'rgba(119,115,106,0.30)';
      ctx.lineWidth = 0.58;
      ctx.stroke();
    });

    for (let j = 0; j < 6; j++) {
      const t = 0.36 + j * 0.075;
      const i = Math.min(
        scr.length - 1,
        Math.round(t * (scr.length - 1))
      );

      const p = scr[i];
      const w = hw(i) * 0.76;

      ctx.fillStyle = 'rgba(103,99,91,0.30)';

      for (const side of [-1, 1]) {
        ctx.beginPath();
        ctx.ellipse(
          p.x + p.nx * w * side,
          p.y + p.ny * w * side,
          0.78, 0.46,
          Math.atan2(p.ny, p.nx),
          0, Math.PI * 2
        );
        ctx.fill();
      }
    }

    ctx.restore();

    const hornI = Math.min(
      scr.length - 1,
      Math.round(0.90 * (scr.length - 1))
    );
    const horn = scr[hornI];
    const hornW = hw(hornI) * 0.20;

    ctx.beginPath();
    ctx.moveTo(
      horn.x - horn.nx * hornW,
      horn.y - horn.ny * hornW
    );
    ctx.quadraticCurveTo(
      horn.x + horn.tx * 2.8 - horn.nx * hornW * 0.6,
      horn.y + horn.ty * 2.8 - horn.ny * hornW * 0.6,
      horn.x + horn.tx * 7.0 + horn.nx * hornW * 1.6,
      horn.y + horn.ty * 7.0 + horn.ny * hornW * 1.6
    );
    ctx.lineTo(
      horn.x + horn.tx * 2.2,
      horn.y + horn.ty * 2.2
    );
    ctx.closePath();
    ctx.fillStyle = '#b8b3a8';
    ctx.fill();

    const head = scr[0];
    const headCx = head.x - head.tx * 2.4;
    const headCy = head.y - head.ty * 2.4;

    ctx.beginPath();
    ctx.ellipse(
      headCx, headCy,
      maxHalf * 0.48,
      maxHalf * 0.29,
      Math.atan2(-head.ty, -head.tx),
      0, Math.PI * 2
    );

    const headGrad = ctx.createLinearGradient(
      headCx - maxHalf, headCy - maxHalf,
      headCx + maxHalf, headCy + maxHalf
    );
    headGrad.addColorStop(0, '#715b49');
    headGrad.addColorStop(0.48, '#514034');
    headGrad.addColorStop(1, '#302720');

    ctx.fillStyle = headGrad;
    ctx.fill();

    ctx.strokeStyle = 'rgba(35,27,22,0.52)';
    ctx.lineWidth = 0.55;
    ctx.stroke();

    ctx.restore();
  }

  function paintWorld() {
    fit(world, 1);
    const ctx = world.getContext('2d');
    const v = view();
    ctx.clearRect(0, 0, v.w, v.h);
    ctx.save();
    ctx.strokeStyle = 'rgba(230,236,233,0.09)';
    ctx.lineWidth = 1;
    const a = arenaSpec();
    const reach = a.kind === 'circle' ? a.r : Math.max(a.hw, a.hh);
    for (let x = -reach; x <= reach; x += 20) {
      ctx.beginPath();
      ctx.moveTo(v.px(x), v.py(-reach));
      ctx.lineTo(v.px(x), v.py(reach));
      ctx.stroke();
    }
    for (let y = -reach; y <= reach; y += 20) {
      ctx.beginPath();
      ctx.moveTo(v.px(-reach), v.py(y));
      ctx.lineTo(v.px(reach), v.py(y));
      ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(230,236,233,0.45)';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    if (a.kind === 'circle') {
      ctx.arc(v.px(0), v.py(0), a.r * v.s, 0, Math.PI * 2);
    } else {
      ctx.rect(v.px(-a.hw), v.py(-a.hh), a.hw * 2 * v.s, a.hh * 2 * v.s);
    }
    ctx.stroke();
    habitat.obstacles.forEach(leaf => {
      drawLeaf(ctx, v.px(leaf.x), v.py(leaf.y), leaf.rot, leaf.rx * v.s, leaf.ry * v.s,
        leaf.id === habitat.selectedLeaf ? 'rgba(46,78,64,0.82)' : 'rgba(32,58,48,0.72)');
    });
    const env = drive();
    if (habitat.reference && habitat.reference.length > 1) {
      drawSilk(ctx, habitat.reference, v, 0.09);
    }
    habitat.orphans.forEach(line => drawSilk(ctx, line, v, env.silkAlpha));
    habitat.agents.forEach(agent => {
      if (agent.mode === 'bench') return;
      if (agent.kind === 'route' && agent.route && agent.route.length > 1) {
        drawSilk(ctx, agent.route, v, 0.06);
      }
      drawSilk(ctx, agent.silk, v, env.silkAlpha);
      drawHabitatWorm(ctx, agent, v);
      if (agent.id === habitat.selected) {
        ctx.strokeStyle = 'rgba(230,236,233,0.35)';
        ctx.strokeRect(v.px(agent.x) - 16, v.py(agent.y) - 16, 32, 32);
      }
    });
    ctx.restore();
  }

  function renderList() {
    const box = document.getElementById('habAgents');
    const syncStat = document.getElementById('habSyncStat');
    const routeN = habitat.agents.filter(a => a.kind === 'route').length;
    const demoN = habitat.agents.length - routeN;
    if (syncStat) syncStat.textContent = '实测 ' + routeN + ' 只 · 演示 ' + demoN + ' 只';
    if (!habitat.agents.length) {
      box.innerHTML = '<div class="hab-note">暂无个体：描好的蚕会自动出现在这里；也可添加随机演示蚕。</div>';
      syncRoutePanel();
      return;
    }
    box.innerHTML = habitat.agents.map(a => {
      const label = { bench: '待放入', idle: '已放置', drag: '拖动中', run: '爬行', paused: '暂停' }[a.mode] || a.mode;
      const disp = a.kind === 'route' ? '蚕 ' + a.wormId : a.id;
      const tag = a.kind === 'route' ? '<span class="tag">实测</span>' : '<span class="tag">演示</span>';
      const tip = a.kind === 'route'
        ? (a.mode === 'idle' || a.mode === 'paused' ? '<span class="drag-tip">可拖动改位置</span>' : '<span class="drag-tip">拖动可改位置</span>')
        : (a.mode === 'bench' ? '<span class="drag-tip">按住拖到场地放入</span>' : '<span class="drag-tip">可拖动改位置</span>');
      return '<div class="agent-card' + (a.id === habitat.selected ? ' on' : '') + '" data-id="' + a.id + '"><b>' + disp + '</b>' + tag + '<br><span class="hab-note">' + label + (a.bodyVisible ? '' : ' · 身体已隐藏') + '</span>' + tip + '</div>';
    }).join('');
    syncRoutePanel();
  }

  function renderDrive() {
    const d = drive();
    document.getElementById('habTempVal').textContent = habitat.tempC.toFixed(1);
    document.getElementById('habHumVal').textContent = String(habitat.humidity);
    document.getElementById('habDrive').textContent =
      '演示：速度 ' + d.speed.toFixed(1) + '，摆动 ' + d.sway.toFixed(2) + '，停顿倾向 ' + d.pauseChance.toFixed(2) + '。模型 ' + MODEL + '。';
    document.getElementById('habClock').textContent = '模拟 ' + habitat.simTime.toFixed(1) + ' s';
  }

  function selectAgent(id) {
    habitat.selected = id;
    habitat.selectedLeaf = null;
    renderList();
  }

  function placeAgent(agent, x, y) {
    if (blocked(x, y)) return false;
    agent.x = x;
    agent.y = y;
    if (agent.mode === 'bench') agent.silk = [{ x, y, t: habitat.simTime }];
    agent.mode = 'idle';
    return true;
  }

  function panelVal(id, txt) { const el = document.getElementById(id); if (el) el.textContent = txt; }
  function panelSet(id, val) { const el = document.getElementById(id); if (el) el.value = val; }
  function panelCheck(id, on) { const el = document.getElementById(id); if (el) el.checked = !!on; }

  function syncRoutePanel() {
    const a = chosen();
    const info = document.getElementById('habRouteInfo');
    if (!a) {
      info.textContent = '未选中个体';
      panelSet('habAdjX', 0); panelVal('habAdjXVal', '0');
      panelSet('habAdjY', 0); panelVal('habAdjYVal', '0');
      panelSet('habAdjRot', 0); panelVal('habAdjRotVal', '0°');
      panelSet('habAdjScale', 1); panelVal('habAdjScaleVal', '1.00');
      panelSet('habAdjFollow', false);
      panelCheck('habAdjFollow', false);
      panelSet('habAdjSpeed', 1); panelVal('habAdjSpeedVal', '1.00×');
      ['habAdjRot', 'habAdjScale', 'habAdjFollow', 'habAdjSpeed'].forEach(id => { const el = document.getElementById(id); if (el) el.disabled = true; });
      return;
    }
    const isRoute = a.kind === 'route';
    info.innerHTML = isRoute ? '实测 · 蚕 ' + a.wormId + ' · ' + a.route.length + ' 点' : '随机个体 · ' + a.id;
    const px = isRoute ? (a.offX || 0) : a.x;
    const py = isRoute ? (a.offY || 0) : a.y;
    panelSet('habAdjX', Math.round(px)); panelVal('habAdjXVal', String(Math.round(px)));
    panelSet('habAdjY', Math.round(py)); panelVal('habAdjYVal', String(Math.round(py)));
    const deg = Math.round((a.rot || 0) * 180 / Math.PI);
    panelSet('habAdjRot', deg); panelVal('habAdjRotVal', deg + '°');
    panelSet('habAdjScale', a.scale || 1); panelVal('habAdjScaleVal', (a.scale || 1).toFixed(2));
    panelSet('habAdjFollow', !!a.follow);
    panelCheck('habAdjFollow', !!a.follow);
    ['habAdjRot', 'habAdjScale', 'habAdjFollow'].forEach(id => { const el = document.getElementById(id); if (el) el.disabled = !isRoute; });
    const speedScale = Number.isFinite(a.speedScale) ? a.speedScale : 1;
    panelSet('habAdjSpeed', speedScale);
    panelVal('habAdjSpeedVal', speedScale.toFixed(2) + '×');
    const speedEl = document.getElementById('habAdjSpeed');
    if (speedEl) speedEl.disabled = false;
  }

  function bindRoutePanel() {
    const bind = (id, fn) => { const el = document.getElementById(id); if (el) el.addEventListener('input', fn); };
    bind('habAdjX', () => { const a = chosen(); if (!a) return; const v = parseFloat(document.getElementById('habAdjX').value); if (a.kind === 'route') { a.offX = v; applyRouteTransform(a); } else { a.x = v; } syncRoutePanel(); });
    bind('habAdjY', () => { const a = chosen(); if (!a) return; const v = parseFloat(document.getElementById('habAdjY').value); if (a.kind === 'route') { a.offY = v; applyRouteTransform(a); } else { a.y = v; } syncRoutePanel(); });
    bind('habAdjRot', () => { const a = chosen(); if (!a || a.kind !== 'route') return; a.rot = parseFloat(document.getElementById('habAdjRot').value) * Math.PI / 180; applyRouteTransform(a); syncRoutePanel(); });
    bind('habAdjScale', () => { const a = chosen(); if (!a || a.kind !== 'route') return; a.scale = parseFloat(document.getElementById('habAdjScale').value); applyRouteTransform(a); syncRoutePanel(); });
    bind('habAdjSpeed', () => {
      const a = chosen(); if (!a) return;
      const value = parseFloat(document.getElementById('habAdjSpeed').value);
      a.speedScale = Math.max(0.1, Math.min(3, Number.isFinite(value) ? value : 1));
      panelVal('habAdjSpeedVal', a.speedScale.toFixed(2) + '×');
    });
    const fol = document.getElementById('habAdjFollow');
    if (fol) fol.addEventListener('change', () => {
      const a = chosen(); if (!a) return;
      a.follow = fol.checked;
      if (a.follow && a.mode === 'idle') a.mode = 'run';
      renderList();
    });
    document.getElementById('habAdjCenter').addEventListener('click', () => {
      const a = chosen(); if (!a) return;
      if (a.kind === 'route') { a.offX = 0; a.offY = 0; a.rot = 0; a.scale = 1; a.u = 0; applyRouteTransform(a); }
      else if (!blocked(0, 0)) { a.x = 0; a.y = 0; }
      renderList();
    });
    document.getElementById('habAdjDrop').addEventListener('click', () => {
      const a = chosen(); if (!a) return;
      pushUndo();
      habitat.agents = habitat.agents.filter(x => x.id !== a.id);
      habitat.selected = null;
      renderList();
    });
  }

  function step(dt) {
    const env = drive();
    habitat.agents.forEach(agent => {
      if (agent.mode !== 'run') return;
      if (agent.kind === 'route') {
        if (agent.follow && agent.route && agent.route.length >= 2) {
          const speedScale = Number.isFinite(agent.speedScale) ? agent.speedScale : 1;
          agent.u = (agent.u + dt * 0.18 * speedScale) % 1;
          const h = sampleRoute(agent, agent.u);
          const ahead = sampleRoute(agent, Math.min(1, agent.u + 0.002));
          agent.x = h.x;
          agent.y = h.y;
          agent.heading = Math.atan2(ahead.y - h.y, ahead.x - h.x);
          const last = agent.silk[agent.silk.length - 1];
          if (!last || Math.hypot(last.x - h.x, last.y - h.y) > 2.5) {
            agent.silk.push({ x: h.x, y: h.y, t: habitat.simTime });
            if (agent.silk.length > 4000) agent.silk.shift();
          }
        }
        return;
      }
      const rand = mulberry32((habitat.seed * 1000 + Math.floor(habitat.simTime * 20) + agent.id.length * 17) >>> 0);
      if (performance.now() < agent.pauseUntil) return;
      if (rand() < env.pauseChance * dt) {
        agent.pauseUntil = performance.now() + 500 + rand() * 700;
        return;
      }
      agent.phase += dt * (0.8 + env.sway);
      const turn = Math.sin(agent.phase) * env.sway * dt * agent.turnSign;
      agent.heading += Math.max(-1.2 * dt, Math.min(1.2 * dt, turn));
      const speedScale = Number.isFinite(agent.speedScale) ? agent.speedScale : 1;
      const actualSpeed = env.speed * speedScale;
      const nx = agent.x + Math.cos(agent.heading) * actualSpeed * dt;
      const ny = agent.y + Math.sin(agent.heading) * actualSpeed * dt;
      if (!blocked(nx, ny)) {
        agent.x = nx;
        agent.y = ny;
        const last = agent.silk[agent.silk.length - 1];
        if (!last || Math.hypot(last.x - nx, last.y - ny) > 1.2) {
          agent.silk.push({ x: nx, y: ny, t: habitat.simTime });
        }
      } else {
        agent.heading += agent.turnSign * 1.6 * dt;
      }
    });
  }

  let last = 0;
  function frame(ts) {
    const dt = Math.min(0.05, last ? (ts - last) / 1000 : 0.016);
    last = ts;
    if (habitat.agents.some(a => a.mode === 'run')) {
      habitat.runningClock = true;
      habitat.simTime += dt;
      step(dt);
    }
    paintMist();
    paintWorld();
    renderDrive();
    requestAnimationFrame(frame);
  }

  world.addEventListener('pointerdown', (ev) => {
    if (ev.button === 1 || ev.shiftKey || habViewport.panMode) {
      habitat.drag = {
        kind: 'pan',
        x: ev.clientX,
        y: ev.clientY,
        panX: habViewport.panX,
        panY: habViewport.panY,
      };
      world.setPointerCapture(ev.pointerId);
      world.classList.add('panning');
      ev.preventDefault();
      return;
    }
    const p = screenToHab(ev);
    if (habitat.tool === 'leaf') {
      if (!insideArena(p.x, p.y, 0)) return;
      pushUndo();
      const id = 'leaf-' + Date.now();
      habitat.obstacles.push({ id, x: p.x, y: p.y, rot: 0, rx: 36, ry: 58 });
      habitat.selectedLeaf = id;
      habitat.drag = { kind: 'leaf', id, dx: 0, dy: 0 };
      world.setPointerCapture(ev.pointerId);
      return;
    }
    const hit = habitat.agents.find(a => a.mode !== 'bench' && Math.hypot(a.x - p.x, a.y - p.y) < 16);
    if (!hit) return;
    selectAgent(hit.id);
    habitat.drag = { kind: 'agent', id: hit.id, modeBefore: hit.mode === 'drag' ? 'idle' : hit.mode, x0: hit.x, y0: hit.y };
    hit.mode = 'drag';
    renderList();
    world.setPointerCapture(ev.pointerId);
  });

  world.addEventListener('pointermove', (ev) => {
    const d = habitat.drag;
    if (!d) return;
    if (d.kind === 'pan') {
      habViewport.panX = d.panX + ev.clientX - d.x;
      habViewport.panY = d.panY + ev.clientY - d.y;
      return;
    }
    const p = screenToHab(ev);
    if (d.kind === 'leaf') {
      const leaf = habitat.obstacles.find(l => l.id === d.id);
      if (leaf && insideArena(p.x, p.y, 0)) { leaf.x = p.x; leaf.y = p.y; }
      return;
    }
    const agent = habitat.agents.find(a => a.id === d.id);
    if (!agent) return;
    if (!blocked(p.x, p.y)) {
      if (agent.kind === 'route') { agent.offX = p.x; agent.offY = p.y; applyRouteTransform(agent); }
      else { agent.x = p.x; agent.y = p.y; }
    }
  });

  world.addEventListener('pointerup', () => {
    const d = habitat.drag;
    if (!d) return;
    if (d.kind === 'pan') {
      habitat.drag = null;
      world.classList.remove('panning');
      return;
    }
    if (d.kind !== 'agent' && d.kind !== 'leaf') return;
    habitat.drag = null;
    if (d.kind !== 'agent') return;
    const agent = habitat.agents.find(a => a.id === d.id);
    if (!agent) return;
    agent.mode = d.modeBefore === 'run' ? 'paused' : (d.modeBefore === 'bench' ? 'idle' : d.modeBefore);
    if (agent.mode === 'bench') agent.mode = 'idle';
    const moved = Math.hypot(agent.x - d.x0, agent.y - d.y0) > 2;
    if (moved) hint('已移动「' + (agent.kind === 'route' ? '蚕 ' + agent.wormId : agent.id) + '」；右侧滑杆可精确微调。');
    renderList();
  });

  function updateGhost(ev, agent) {
    if (!ghost) return;
    if (!agent) { ghost.style.display = 'none'; return; }
    const label = agent.kind === 'route' ? '蚕 ' + agent.wormId : agent.id;
    const rect = world.getBoundingClientRect();
    const inside = ev.clientX >= rect.left && ev.clientX <= rect.right && ev.clientY >= rect.top && ev.clientY <= rect.bottom;
    const ok = inside && !blocked(screenToHab(ev).x, screenToHab(ev).y);
    ghost.textContent = ok ? '松手放到「' + label + '」处' : (inside ? '这里被桑叶或边界挡住' : '拖到场地里松手');
    ghost.className = ok ? 'canDrop' : (inside ? 'noDrop' : '');
    ghost.style.display = 'block';
    ghost.style.left = ev.clientX + 'px';
    ghost.style.top = ev.clientY + 'px';
    world.classList.toggle('drop-ready', ok);
    world.classList.toggle('drop-fail', inside && !ok);
  }

  function clearGhost() {
    if (ghost) { ghost.style.display = 'none'; ghost.className = ''; }
    world.classList.remove('drop-ready', 'drop-fail');
  }

  document.getElementById('habAgents').addEventListener('pointerdown', (ev) => {
    const card = ev.target.closest('.agent-card');
    if (!card) return;
    const agent = habitat.agents.find(a => a.id === card.dataset.id);
    if (!agent) return;
    selectAgent(agent.id);
    habitat.drag = { kind: 'card', id: agent.id };
    hint('按住拖动到场地内松手，即可把这一个体放到该处。');
    updateGhost(ev, agent);
    if (world.setPointerCapture) world.setPointerCapture(ev.pointerId);
  });

  window.addEventListener('pointermove', (ev) => {
    const d = habitat.drag;
    if (!d || d.kind !== 'card') return;
    const agent = habitat.agents.find(a => a.id === d.id);
    updateGhost(ev, agent);
  });

  window.addEventListener('pointerup', (ev) => {
    const d = habitat.drag;
    if (!d || d.kind !== 'card') return;
    habitat.drag = null;
    clearGhost();
    const agent = habitat.agents.find(a => a.id === d.id);
    if (!agent) return;
    const label = agent.kind === 'route' ? '蚕 ' + agent.wormId : agent.id;
    const rect = world.getBoundingClientRect();
    if (ev.clientX < rect.left || ev.clientX > rect.right || ev.clientY < rect.top || ev.clientY > rect.bottom) {
      hint('未放置：请在场地范围内松手。');
      toast('没有放到场地里，「' + label + '」保持原位。', 'err');
      return;
    }
    const p = screenToHab(ev);
    if (blocked(p.x, p.y)) {
      toast('放不进去：该处被桑叶或场地边界占用，换个位置。', 'err');
      hint('该位置不可放置，请换一处。');
      return;
    }
    if (agent.kind === 'route') {
      agent.offX = p.x;
      agent.offY = p.y;
      applyRouteTransform(agent);
      agent.mode = 'idle';
      toast('「' + label + '」已放到该处。', 'ok');
      hint('已放置实测个体；右侧滑杆可继续微调位置、旋转与缩放。');
    } else {
      placeAgent(agent, p.x, p.y);
      toast('「' + label + '」已放入场地。', 'ok');
      hint('已放入。选中后可用右侧滑杆微调。');
    }
    renderList();
    syncRoutePanel();
  });

  document.getElementById('habTemp').addEventListener('input', (e) => { habitat.tempC = parseFloat(e.target.value); });
  document.getElementById('habHum').addEventListener('input', (e) => { habitat.humidity = parseFloat(e.target.value); });
  document.querySelectorAll('[data-shape]').forEach(btn => {
    btn.addEventListener('click', () => {
      habitat.shape = btn.dataset.shape;
      document.querySelectorAll('[data-shape]').forEach(b => b.classList.toggle('active', b === btn));
      habitat.agents.forEach(a => {
        if (a.mode !== 'bench' && blocked(a.x, a.y)) a.mode = 'paused';
      });
    });
  });
  document.getElementById('habLeafTool').addEventListener('click', () => {
    habitat.tool = habitat.tool === 'leaf' ? 'worm' : 'leaf';
    document.getElementById('habLeafTool').classList.toggle('active', habitat.tool === 'leaf');
  });
  function currentLeaf() { return habitat.obstacles.find(l => l.id === habitat.selectedLeaf); }
  document.getElementById('habLeafRotL').addEventListener('click', () => { const l = currentLeaf(); if (l) l.rot -= 0.25; });
  document.getElementById('habLeafRotR').addEventListener('click', () => { const l = currentLeaf(); if (l) l.rot += 0.25; });
  document.getElementById('habLeafDel').addEventListener('click', () => {
    const l = currentLeaf();
    if (!l) return;
    pushUndo();
    habitat.obstacles = habitat.obstacles.filter(x => x.id !== l.id);
    habitat.selectedLeaf = null;
  });

  function chosen() { return habitat.agents.find(a => a.id === habitat.selected); }
  document.getElementById('habAddRandom').addEventListener('click', () => {
    pushUndo();
    makeRandomDemo();
    renderList();
  });
  document.getElementById('habHide').addEventListener('click', () => { const a = chosen(); if (a) { a.bodyVisible = false; renderList(); } });
  document.getElementById('habShow').addEventListener('click', () => { const a = chosen(); if (a) { a.bodyVisible = true; renderList(); } });
  document.getElementById('habDropSilk').addEventListener('click', () => {
    const a = chosen();
    if (!a || a.mode === 'bench') return;
    pushUndo();
    if (a.kind === 'route') { a.route = []; a.kind = 'random'; }
    else if (a.silk.length > 1) habitat.orphans.push(a.silk.slice());
    a.mode = 'bench'; a.silk = []; a.bodyVisible = true;
    renderList();
  });
  document.getElementById('habDropAll').addEventListener('click', () => {
    const a = chosen();
    if (!a || a.mode === 'bench') return;
    pushUndo();
    if (a.kind === 'route') { a.route = []; a.kind = 'random'; }
    a.mode = 'bench'; a.silk = []; a.bodyVisible = true;
    renderList();
  });
  document.getElementById('habUndo').addEventListener('click', () => {
    const raw = habitat.undo.pop();
    if (!raw) return;
    const data = JSON.parse(raw);
    habitat.agents = data.agents;
    habitat.orphans = data.orphans;
    habitat.obstacles = data.obstacles;
    renderList();
  });
  document.getElementById('habStart').addEventListener('click', () => {
    const ready = habitat.agents.filter(a =>
      a.mode !== 'bench' &&
      a.mode !== 'drag' &&
      (a.kind !== 'route' || (a.route && a.route.length >= 2))
    );
    if (!ready.length) {
      toast('请先将蚕拖入场地，再点击开始。', 'err');
      hint('目前没有已放入场地、可以运动的个体。');
      return;
    }
    ready.forEach(a => {
      if (a.kind === 'route') {
        a.follow = true;
        if (!Number.isFinite(a.u)) a.u = 0;
      }
      a.mode = 'run';
    });
    renderList();
    toast('已启动 ' + ready.length + ' 只蚕。', 'ok');
    hint('实测蚕正在沿测量轨迹运动；可在右侧调整每只蚕的速度倍率。');
  });
  document.getElementById('habPause').addEventListener('click', () => {
    habitat.agents.forEach(a => { if (a.mode === 'run') a.mode = 'paused'; });
    renderList();
  });
  document.getElementById('habResume').addEventListener('click', () => {
    habitat.agents.forEach(a => { if (a.mode === 'paused') a.mode = 'run'; });
    renderList();
  });
  document.getElementById('habSave').addEventListener('click', () => {
    const doc = {
      type: 'silkworm-habitat/v1',
      modelVersion: MODEL,
      disclaimer: '温湿度映射为演示模型，不是已验证的生理规律',
      temperatureC: habitat.tempC,
      humidity: habitat.humidity,
      seed: habitat.seed,
      simTime: habitat.simTime,
      shape: habitat.shape,
      obstacles: habitat.obstacles,
      agents: habitat.agents.map(a => ({
        id: a.id, mode: a.mode, bodyVisible: a.bodyVisible,
        x: a.x, y: a.y, heading: a.heading, silk: a.silk,
        kind: a.kind, wormId: a.wormId, route: a.route,
        offX: a.offX, offY: a.offY, rot: a.rot, scale: a.scale,
        follow: a.follow, u: a.u, color: a.color,
        speedScale: Number.isFinite(a.speedScale) ? a.speedScale : 1,
      })),
      orphanSilk: habitat.orphans,
      referenceReadOnly: habitat.reference,
    };
    const blob = new Blob([JSON.stringify(doc, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'habitat-' + Date.now() + '.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  });
  document.getElementById('habImportTraj').addEventListener('click', importMeasuredTrajectories);
  document.getElementById('habRef').addEventListener('click', () => {
    const srcs = measuredSource();
    const t0 = srcs.find(t => (t.points || []).length > 1);
    const src = t0 ? t0.points.filter(p => p && Number.isFinite(p.x) && Number.isFinite(p.y)) : [];
    if (!src.length) { toast('没有可铺底的实测轨迹。', 'err'); return; }
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    src.forEach(p => { minX = Math.min(minX, p.x); minY = Math.min(minY, p.y); maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y); });
    const a = arenaSpec();
    const span = Math.max(maxX - minX, maxY - minY) || 1;
    const target = (a.kind === 'circle' ? a.r * 1.4 : Math.min(a.hw, a.hh) * 1.4);
    habitat.reference = src.map(p => ({
      x: ((p.x - (minX + maxX) / 2) / span) * target,
      y: ((p.y - (minY + maxY) / 2) / span) * target,
    }));
    toast('已铺入蚕 ' + (t0.wormId != null ? t0.wormId : 1) + ' 的只读底图。', 'ok');
  });
  document.getElementById('habClearRef').addEventListener('click', () => { habitat.reference = null; toast('已去掉底图。', 'ok'); });
  const stage = document.querySelector('.hab-stage');
  const narrow = () => window.matchMedia('(max-width: 860px)').matches;
  const panelOpen = { left: true, right: true };

  function applyPanelState() {
    const left = document.getElementById('habLeft');
    const right = document.getElementById('habRight');
    const leftBtn = document.getElementById('habOpenLeft');
    const rightBtn = document.getElementById('habOpenRight');
    if (narrow()) {
      stage.classList.remove('left-off', 'right-off');
      left.classList.toggle('open', panelOpen.left);
      right.classList.toggle('open', panelOpen.right);
    } else {
      left.classList.remove('open');
      right.classList.remove('open');
      stage.classList.toggle('left-off', !panelOpen.left);
      stage.classList.toggle('right-off', !panelOpen.right);
    }
    const lOpen = panelOpen.left;
    const rOpen = panelOpen.right;
    leftBtn.textContent = lOpen ? '收起环境' : '展开环境';
    rightBtn.textContent = rOpen ? '收起个体' : '展开个体';
    leftBtn.classList.toggle('on', lOpen);
    rightBtn.classList.toggle('on', rOpen);
    leftBtn.setAttribute('aria-pressed', String(!lOpen));
    rightBtn.setAttribute('aria-pressed', String(!rOpen));
  }

  function togglePanel(which) {
    panelOpen[which] = !panelOpen[which];
    applyPanelState();
    const name = which === 'left' ? '环境' : '个体';
    hint(name + '面板已' + (panelOpen[which] ? '展开' : '收起') + '。');
    toast(name + '面板已' + (panelOpen[which] ? '展开' : '收起') + '（再点一次可切换）。', 'ok');
    setTimeout(() => repaintStaticLayers(), 80);
  }

  document.getElementById('habOpenLeft').addEventListener('click', () => togglePanel('left'));
  document.getElementById('habOpenRight').addEventListener('click', () => togglePanel('right'));
  window.addEventListener('resize', applyPanelState);
  applyPanelState();

  /* ===== 无限画布：滚轮缩放 / 平移 / 适应场地 ===== */
  world.addEventListener('wheel', (ev) => {
    const rect = world.getBoundingClientRect();
    const sx = (ev.clientX - rect.left) * (world.width / rect.width);
    const sy = (ev.clientY - rect.top) * (world.height / rect.height);
    const factor = Math.exp(-ev.deltaY * 0.001);
    zoomAt(sx, sy, factor);
    ev.preventDefault();
  }, { passive: false });

  document.getElementById('habZoomIn').addEventListener('click', () => {
    zoomAt(world.width / 2, world.height / 2, 1.2);
  });
  document.getElementById('habZoomOut').addEventListener('click', () => {
    zoomAt(world.width / 2, world.height / 2, 1 / 1.2);
  });
  document.getElementById('habFitView').addEventListener('click', () => {
    resetHabView();
    toast('已恢复到 100% 并居中。', 'ok');
  });
  document.getElementById('habPanToggle').addEventListener('click', (ev) => {
    habViewport.panMode = !habViewport.panMode;
    ev.currentTarget.classList.toggle('active', habViewport.panMode);
    ev.currentTarget.classList.toggle('on', habViewport.panMode);
    world.classList.toggle('pan-mode', habViewport.panMode);
    hint(habViewport.panMode ? '平移模式：按住拖动可移动画布，滚轮缩放。' : '已退出平移模式。');
  });
  updateHabZoomLabel();

  /* ===== 场地高度 ===== */
  const canvasHeightInput = document.getElementById('habCanvasHeight');
  if (canvasHeightInput) {
    const applyCanvasHeight = () => {
      const h = Math.max(640, Math.min(1400, parseInt(canvasHeightInput.value, 10) || 780));
      document.getElementById('habitat').style.setProperty('--hab-stage-height', h + 'px');
      const valEl = document.getElementById('habCanvasHeightVal');
      if (valEl) valEl.textContent = h + 'px';
      repaintStaticLayers();
    };
    canvasHeightInput.addEventListener('input', applyCanvasHeight);
    applyCanvasHeight();
  }
  if (window.ResizeObserver) {
    const ro = new ResizeObserver(() => repaintStaticLayers());
    ro.observe(wrap);
  }

  /* ===== 运动预览宽度拖动 + 放大 ===== */
  function bindPreviewResizer() {
    const panes = document.querySelector('.panes');
    const handle = document.getElementById('previewSplitter');
    const frame = document.getElementById('previewFrame');
    if (!panes || !handle || !frame) return;

    let active = false;

    function setWidth(clientX) {
      const rect = panes.getBoundingClientRect();
      const maxWidth = Math.max(360, Math.min(1100, rect.width - 320 - handle.offsetWidth));
      const desired = rect.right - clientX - handle.offsetWidth / 2;
      const width = Math.max(360, Math.min(maxWidth, desired));
      document.documentElement.style.setProperty('--preview-width', width + 'px');
    }

    handle.addEventListener('pointerdown', (ev) => {
      if (narrow()) return;
      active = true;
      handle.setPointerCapture(ev.pointerId);
      document.body.classList.add('resizing-preview');
      ev.preventDefault();
    });
    handle.addEventListener('pointermove', (ev) => { if (active) setWidth(ev.clientX); });
    const stop = () => { active = false; document.body.classList.remove('resizing-preview'); };
    handle.addEventListener('pointerup', stop);
    handle.addEventListener('pointercancel', stop);
    handle.addEventListener('dblclick', () => {
      document.documentElement.style.setProperty('--preview-width', '48%');
    });
    handle.addEventListener('keydown', (ev) => {
      if (ev.key !== 'ArrowLeft' && ev.key !== 'ArrowRight') return;
      const current = frame.getBoundingClientRect().width;
      const next = current + (ev.key === 'ArrowLeft' ? -32 : 32);
      const rect = panes.getBoundingClientRect();
      const width = Math.max(360, Math.min(1100, rect.width - 328, next));
      document.documentElement.style.setProperty('--preview-width', width + 'px');
      ev.preventDefault();
    });
  }
  bindPreviewResizer();
  const cueEl = document.getElementById('scrollCue');
  if (cueEl) cueEl.addEventListener('click', () => {
    const h = document.getElementById('habitat');
    if (h) h.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  /* 滚到蚕室时自动再同步一次，避免描图后忘了手动点同步 */
  let lastSyncAt = 0;
  const enterObs = new IntersectionObserver((entries) => {
    if (!entries[0] || !entries[0].isIntersecting) return;
    const now = Date.now();
    if (now - lastSyncAt < 800) return;
    lastSyncAt = now;
    try {
      const n = syncMeasured();
      if (n) hint('已自动同步 ' + n + ' 条实测轨迹到蚕室。');
    } catch (_) { }
  }, { threshold: 0.2 });
  const habSection = document.getElementById('habitat');
  if (habSection && window.IntersectionObserver) enterObs.observe(habSection);

  function exportHabitat() {
    return {
      modelVersion: MODEL,
      disclaimer: '温湿度映射为演示模型，不是已验证的生理规律',
      temperatureC: habitat.tempC,
      humidity: habitat.humidity,
      seed: habitat.seed,
      simTime: habitat.simTime,
      shape: habitat.shape,
      tool: habitat.tool,
      selected: habitat.selected,
      selectedLeaf: habitat.selectedLeaf,
      obstacles: habitat.obstacles,
      orphanSilk: habitat.orphans,
      reference: habitat.reference,
      agents: habitat.agents.map(a => ({
        id: a.id,
        mode: a.mode,
        bodyVisible: a.bodyVisible,
        x: a.x,
        y: a.y,
        heading: a.heading,
        phase: a.phase,
        turnSign: a.turnSign,
        silk: a.silk,
        kind: a.kind,
        wormId: a.wormId,
        route: a.route,
        offX: a.offX,
        offY: a.offY,
        rot: a.rot,
        scale: a.scale,
        follow: a.follow,
        u: a.u,
        color: a.color,
        speedScale: Number.isFinite(a.speedScale) ? a.speedScale : 1,
      })),
    };
  }

  function importHabitat(data) {
    if (!data) return;
    if (Number.isFinite(data.temperatureC)) {
      habitat.tempC = data.temperatureC;
      document.getElementById('habTemp').value = data.temperatureC;
    }
    if (Number.isFinite(data.humidity)) {
      habitat.humidity = data.humidity;
      document.getElementById('habHum').value = data.humidity;
    }
    if (data.seed != null) habitat.seed = data.seed;
    if (Number.isFinite(data.simTime)) habitat.simTime = data.simTime;
    if (data.shape) {
      habitat.shape = data.shape;
      document.querySelectorAll('[data-shape]').forEach(b => b.classList.toggle('active', b.dataset.shape === data.shape));
    }
    habitat.tool = data.tool || 'worm';
    document.getElementById('habLeafTool').classList.toggle('active', habitat.tool === 'leaf');
    habitat.obstacles = Array.isArray(data.obstacles) ? data.obstacles : [];
    habitat.orphans = Array.isArray(data.orphanSilk) ? data.orphanSilk : [];
    habitat.reference = data.reference || null;
    habitat.selected = data.selected || null;
    habitat.selectedLeaf = data.selectedLeaf || null;
    if (Array.isArray(data.agents)) {
      habitat.agents = data.agents.map(a => {
        const agent = {
          id: a.id,
          kind: a.kind || 'random',
          wormId: a.wormId != null ? a.wormId : null,
          mode: a.mode || 'bench',
          bodyVisible: a.bodyVisible !== false,
          x: a.x || 0,
          y: a.y || 0,
          heading: a.heading || 0,
          phase: a.phase || 0,
          turnSign: a.turnSign || 1,
          silk: Array.isArray(a.silk) ? a.silk : [],
          route: Array.isArray(a.route) ? a.route : [],
          offX: Number.isFinite(a.offX) ? a.offX : 0,
          offY: Number.isFinite(a.offY) ? a.offY : 0,
          rot: Number.isFinite(a.rot) ? a.rot : 0,
          scale: Number.isFinite(a.scale) ? a.scale : 1,
          follow: !!a.follow,
          u: Number.isFinite(a.u) ? a.u : 0,
          color: a.color || '#d4c4a8',
          speedScale: Number.isFinite(a.speedScale) ? Math.max(0.1, Math.min(3, a.speedScale)) : 1,
          pauseUntil: 0,
        };
        if (agent.kind === 'route' && agent.route.length >= 2) applyRouteTransform(agent);
        return agent;
      });
    }
    renderList();
    renderDrive();
  }

  window.__studioHabitat = { export: exportHabitat, import: importHabitat, syncMeasured: syncMeasured, toast: toast, hint: hint };

  bindRoutePanel();
  syncMeasured();
  renderList();
  function repaintStaticLayers() {
    paintStatic();
    paintDepth();
  }

  repaintStaticLayers();

  window.addEventListener(
    'resize',
    repaintStaticLayers
  );
  requestAnimationFrame(frame);
})();
