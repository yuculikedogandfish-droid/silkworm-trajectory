
const STORAGE_KEY = 'SILKWORM_PREVIEW_V1';
const state = {
  unit: 'px',
  scale: null,
  origin: null,
  cellMm: 10,
  trajectories: [],
  activeIdx: 0,
  points: [],
  style: { headWidth: 0.2, midWidth: 0.2, tailWidth: 0.2, opacity: 0.95, material: 'line' },
  color: '#f7f5f2',
  behaviorBoxes: [],
  provenance: 'measured',
  playing: false,
  frame: 0,
  ghostPoints: null,
  bounds: null,
  tilt: 0,
  yaw: 0,
  litCells: [],
  route: [],
  panX: 0,
  panY: 0,
  drag: null,
  cellMarks: [],
  statusNote: '',
  playAcc: 0,
};

if (new URLSearchParams(location.search).get('embed') === '1') {
  document.body.classList.add('embed');
}

function mulberry32(a) {
  return function() {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t ^= t + Math.imul(t ^ t >>> 7, 61 | t);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

function widthAlongStyle(style, u) {
  const h = style.headWidth, m = style.midWidth, t = style.tailWidth;
  if (u <= 0.5) return h + (m - h) * (u / 0.5);
  return m + (t - m) * ((u - 0.5) / 0.5);
}

function normalizeIncoming(doc) {
  const out = { trajectories: [], behaviorBoxes: [], unit: 'px', calibration: null, provenance: 'measured', synth: null };
  if (doc.type === 'silkworm-preview/v1') {
    Object.assign(out, doc);
    out.trajectories = doc.trajectories || [];
    return out;
  }
  if (doc.schema &amp;&amp; String(doc.schema).includes('motion-model')) {
    out.provenance = 'measured';
    out.synth = doc.synthesis || null;
    out.unit = doc.unit || (doc.calibration ? 'mm' : 'px');
    out.calibration = doc.calibration;
    out.behaviorBoxes = doc.behaviorUnits || [];
    out.trajectories = (doc.unifiedTrajectories || []).map(t => ({
      wormId: t.wormId,
      color: '#f7f5f2',
      style: t.style || state.style,
      points: (t.points || []).map(p => ({
        x: p.x_mm != null ? p.x_mm : (p.x_px != null ? p.x_px : p.x),
        y: p.y_mm != null ? p.y_mm : (p.y_px != null ? p.y_px : p.y),
        u: p.u != null ? p.u : 0,
        width_mm: p.width_mm,
        kind: p.kind || 'stroke',
      })),
    }));
    return out;
  }
  if (doc.unifiedTrajectories) {
    return normalizeIncoming({ ...doc, schema: 'curves3d/v2' });
  }
  if (doc.curves &amp;&amp; doc.curves.length &amp;&amp; doc.curves[0].points) {
    out.trajectories = doc.curves.map((c, i) => ({
      wormId: c.virtualId || c.wormId || i + 1,
      color: '#f7f5f2',
      style: c.style || state.style,
      points: c.points.map(p => ({ x: p.x_mm, y: p.y_mm, u: p.u, width_mm: p.width_mm })),
    }));
    out.provenance = doc.provenance || 'synthetic';
    return out;
  }
  if (doc.worms) {
    out.trajectories = Object.keys(doc.worms).map(id => {
      const w = doc.worms[id];
      return {
        wormId: +id,
        color: w.color,
        style: w.style || state.style,
        points: (w.points || []).map((p, i, arr) => ({
          x: p.x, y: p.y, u: arr.length > 1 ? i / (arr.length - 1) : 0,
        })),
      };
    });
    out.calibration = doc.calibration;
    return out;
  }
  return out;
}

function setTrajectoryList(norm, pickIdx) {
  state.trajectories = norm.trajectories.filter(t => t.points &amp;&amp; t.points.length >= 2);
  if (!state.trajectories.length) return false;
  state.activeIdx = pickIdx != null ? pickIdx : 0;
  const t = state.trajectories[state.activeIdx];
  state.points = t.points.map(p => ({ ...p }));
  state.style = { ...state.style, ...(t.style || {}) };
  state.color = '#f7f5f2';
  state.behaviorBoxes = norm.behaviorBoxes || [];
  state.provenance = norm.provenance || 'measured';
  state.synth = norm.synth;
  state.unit = norm.unit || 'px';
  if (norm.calibration &amp;&amp; norm.calibration.scalePxPerMm) {
    state.scale = norm.calibration.scalePxPerMm;
    state.origin = norm.calibration.originPx;
    state.cellMm = norm.calibration.cell_mm || 10;
  } else state.scale = null;
  ensureUMonotone();
  computeBounds();
  state.frame = 0;
  state.ghostPoints = null;
  state.litCells = [];
  state.panX = 0;
  state.panY = 0;
  rebuildRoute();
  document.getElementById('dataBadge').textContent =
    state.provenance === 'synthetic' ? '合成轨迹' : '实测/描线轨迹';
  updateTrajStat();
  syncTrajTabs();
  return true;
}

function ensureUMonotone() {
  const n = state.points.length;
  if (n < 2) return;
  if (state.points[0].u == null || state.points[n - 1].u == null) {
    state.points.forEach((p, i) => { p.u = i / (n - 1); });
  }
}

function computeBounds() {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const p of state.points) {
    minX = Math.min(minX, p.x); minY = Math.min(minY, p.y);
    maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y);
  }
  for (const b of state.behaviorBoxes) {
    const box = b.box_px || b;
    if (box.x0 != null) {
      minX = Math.min(minX, box.x0); minY = Math.min(minY, box.y0);
      maxX = Math.max(maxX, box.x1); maxY = Math.max(maxY, box.y1);
    }
  }
  const home = homeBox();
  const reach = 2;
  minX = Math.min(minX, home.x0 - home.w * reach);
  minY = Math.min(minY, home.y0 - home.h * reach);
  maxX = Math.max(maxX, home.x1 + home.w * reach);
  maxY = Math.max(maxY, home.y1 + home.h * reach);
  for (const c of state.litCells) {
    const r = cellRect(c.ix, c.iy);
    minX = Math.min(minX, r.x0); minY = Math.min(minY, r.y0);
    maxX = Math.max(maxX, r.x1); maxY = Math.max(maxY, r.y1);
  }
  const pad = Math.max(20, (maxX - minX) * 0.08);
  state.bounds = { minX: minX - pad, minY: minY - pad, maxX: maxX + pad, maxY: maxY + pad };
}

function homeBox() {
  const b = state.behaviorBoxes[0];
  const box = b &amp;&amp; (b.box_px || b);
  if (box &amp;&amp; box.x0 != null) {
    const x0 = Math.min(box.x0, box.x1), x1 = Math.max(box.x0, box.x1);
    const y0 = Math.min(box.y0, box.y1), y1 = Math.max(box.y0, box.y1);
    return { x0, y0, x1, y1, w: Math.max(8, x1 - x0), h: Math.max(8, y1 - y0) };
  }
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const p of state.points) {
    minX = Math.min(minX, p.x); minY = Math.min(minY, p.y);
    maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y);
  }
  if (!Number.isFinite(minX)) return { x0: 0, y0: 0, x1: 80, y1: 80, w: 80, h: 80 };
  const pad = 8;
  return { x0: minX - pad, y0: minY - pad, x1: maxX + pad, y1: maxY + pad, w: maxX - minX + pad * 2, h: maxY - minY + pad * 2 };
}

function cellRect(ix, iy) {
  const h = homeBox();
  return {
    ix, iy,
    x0: h.x0 + ix * h.w,
    y0: h.y0 + iy * h.h,
    x1: h.x0 + (ix + 1) * h.w,
    y1: h.y0 + (iy + 1) * h.h,
    w: h.w,
    h: h.h,
  };
}

function mapIntoCell(p, rect) {
  const h = homeBox();
  return {
    ...p,
    x: rect.x0 + (p.x - h.x0),
    y: rect.y0 + (p.y - h.y0),
  };
}

function joinStrokeGaps(pts) {
  if (pts.length < 2) return pts.map(p => ({ ...p }));
  const gaps = [];
  for (let i = 1; i < pts.length; i++) gaps.push(Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y));
  const sorted = gaps.slice().sort((a, b) => a - b);
  const med = sorted[Math.floor(sorted.length / 2)] || 1;
  const out = [{ ...pts[0] }];
  for (let i = 1; i < pts.length; i++) {
    const a = out[out.length - 1];
    const b = pts[i];
    const d = Math.hypot(b.x - a.x, b.y - a.y);
    if (d > Math.max(12, med * 3.2)) {
      const prev = out[Math.max(0, out.length - 2)];
      let hx = a.x - prev.x, hy = a.y - prev.y;
      let hl = Math.hypot(hx, hy) || 1;
      hx /= hl; hy /= hl;
      const tx = (b.x - a.x) / d, ty = (b.y - a.y) / d;
      const c1 = { x: a.x + hx * d * 0.4, y: a.y + hy * d * 0.4 };
      const c2 = { x: b.x - tx * d * 0.4, y: b.y - ty * d * 0.4 };
      const n = Math.max(4, Math.round(d / Math.max(med, 1)));
      for (let k = 1; k < n; k++) {
        const t = k / n, u = 1 - t;
        out.push({
          ...b,
          x: u*u*u*a.x + 3*u*u*t*c1.x + 3*u*t*t*c2.x + t*t*t*b.x,
          y: u*u*u*a.y + 3*u*u*t*c1.y + 3*u*t*t*c2.y + t*t*t*b.y,
          kind: 'bridge',
        });
      }
    }
    out.push({ ...b });
  }
  return out;
}

function stepLaw(pts) {
  const steps = [];
  for (let i = 1; i < pts.length; i++) {
    steps.push({
      dx: pts[i].x - pts[i - 1].x,
      dy: pts[i].y - pts[i - 1].y,
      u: pts[i].u,
      width_mm: pts[i].width_mm,
    });
  }
  return steps;
}

function driftReplay(steps, start, dirx, diry, cellW, cellH, seed) {
  const noiseEl = document.getElementById('noise');
  const noise = noiseEl ? Math.min(1, parseFloat(noiseEl.value) / 100) : 0.2;
  const rand = mulberry32(seed);
  const rot = (rand() - 0.5) * 0.16 * noise;
  const scale = 1 + (rand() - 0.5) * 0.08 * noise;
  const cs = Math.cos(rot), sn = Math.sin(rot);
  const out = [];
  let x = start.x, y = start.y;
  const n = Math.max(1, steps.length);
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i];
    const dx = s.dx * scale, dy = s.dy * scale;
    x += dx * cs - dy * sn + dirx * cellW / n;
    y += dx * sn + dy * cs + diry * cellH / n;
    out.push({ x, y, u: s.u, width_mm: s.width_mm, kind: 'stroke' });
  }
  return out;
}

function adjacentCells(pool, cell) {
  return pool.filter(c => Math.abs(c.ix - cell.ix) + Math.abs(c.iy - cell.iy) === 1);
}

function rebuildRoute() {
  if (!state.points.length) { state.route = []; state.cellMarks = []; return; }
  const base = joinStrokeGaps(state.points);
  const steps = stepLaw(base);
  const home = homeBox();
  const pending = state.litCells.map(c => ({ ix: c.ix, iy: c.iy }));
  const route = base.map(p => ({ ...p }));
  const marks = [];
  const tailOf = () => route[route.length - 1];
  const markNow = () => {
    const last = tailOf();
    const prev = route[Math.max(0, route.length - 2)];
    marks.push({
      endIndex: route.length - 1,
      x: last.x,
      y: last.y,
      ang: Math.atan2(last.y - prev.y, last.x - prev.x),
    });
  };
  markNow();
  let current = { ix: 0, iy: 0 };
  const used = new Set(['0,0']);
  let gen = 1;
  while (pending.length) {
    const nexts = adjacentCells(pending.filter(c => !used.has(c.ix + ',' + c.iy)), current);
    if (!nexts.length) break;
    const tail = tailOf();
    nexts.sort((a, b) => {
      const ra = cellRect(a.ix, a.iy), rb = cellRect(b.ix, b.iy);
      const da = Math.hypot((ra.x0 + ra.x1) / 2 - tail.x, (ra.y0 + ra.y1) / 2 - tail.y);
      const db = Math.hypot((rb.x0 + rb.x1) / 2 - tail.x, (rb.y0 + rb.y1) / 2 - tail.y);
      return da - db;
    });
    const next = nexts[0];
    const replay = driftReplay(
      steps,
      tail,
      next.ix - current.ix,
      next.iy - current.iy,
      home.w,
      home.h,
      1000 + gen * 97 + next.ix * 13 + next.iy * 29
    );
    route.push(...replay);
    markNow();
    used.add(next.ix + ',' + next.iy);
    current = next;
    gen++;
  }
  state.route = route;
  state.cellMarks = marks;
  if (state.frame >= route.length) state.frame = Math.max(0, route.length - 1);
}

function cameraAngles() {
  const yawEl = document.getElementById('yaw');
  const tiltEl = document.getElementById('tilt');
  return {
    yaw: ((yawEl ? parseFloat(yawEl.value) : 0) || 0) * Math.PI / 180,
    tilt: ((tiltEl ? parseFloat(tiltEl.value) : 0) || 0) * Math.PI / 180,
  };
}

function projectPoint(p, W, H) {
  const sc = worldToScreen({ x: p.x, y: p.y }, W, H);
  const { yaw, tilt } = cameraAngles();
  const cx = W / 2, cy = H / 2;
  const x = sc.x - cx, y = sc.y - cy;
  const xr = x * Math.cos(yaw) - y * Math.sin(yaw);
  const yr = x * Math.sin(yaw) + y * Math.cos(yaw);
  const y2 = yr * Math.cos(tilt);
  const persp = tilt > 0.001 ? 1 / (1 + y2 / (H * 6)) : 1;
  return { x: cx + xr * persp, y: cy + y2 * persp, scale: sc.scale * persp };
}
function worldToScreen(p, W, H) {
  const b = state.bounds;
  const spanX = b.maxX - b.minX || 1;
  const spanY = b.maxY - b.minY || 1;
  const s = Math.min(W / spanX, H / spanY);
  const ox = (W - spanX * s) / 2 + state.panX;
  const oy = (H - spanY * s) / 2 + state.panY;
  return {
    x: ox + (p.x - b.minX) * s,
    y: oy + (p.y - b.minY) * s,
    scale: s,
  };
}

// =====================================================
// SILKWORM VISUAL PATCH
// Replace SILK_LOOK through drawWormHead()
// Keep projectPoint(), draw(), and all motion logic.
// =====================================================

const SILK_LOOK = Object.freeze({
  widthScale: 0.032,
  minHalfWidth: 0.26,
  maxHalfWidth: 0.72,
  silkHalo: 'rgba(236,241,238,0.045)',
  silkCore: 'rgba(236,240,238,0.34)',
  silkSheen: 'rgba(255,255,255,0.46)',
  ribbonBase: 'rgba(226,232,228,0.23)',
  ribbonShadow: 'rgba(72,82,76,0.22)',
  ribbonHighlight: 'rgba(255,255,255,0.38)'
});

function clamp01(v) {
  return Math.max(0, Math.min(1, v));
}

function safeUnit(x, y) {
  const len = Math.hypot(x, y);
  if (!Number.isFinite(len) || len < 1e-6) {
    return { x: 0, y: -1 };
  }
  return { x: x / len, y: y / len };
}

function cameraSignature(W, H) {
  const b = state.bounds || {};
  const yaw = document.getElementById('yaw');
  const tilt = document.getElementById('tilt');
  const st = state.style || {};

  return [
    W, H, state.panX, state.panY,
    yaw ? yaw.value : 0,
    tilt ? tilt.value : 0,
    b.minX, b.minY, b.maxX, b.maxY,
    st.headWidth, st.midWidth, st.tailWidth
  ].join('|');
}

function buildRibbonVertices(ctx, pts, style) {
  const W = ctx.canvas.width;
  const H = ctx.canvas.height;
  const n = pts.length;
  const v = new Array(n);

  for (let i = 0; i < n; i++) {
    const p = pts[i];
    const u = Number.isFinite(p.u)
      ? p.u : i / Math.max(1, n - 1);

    const q = projectPoint(p, W, H);
    const sourceWidth = Number.isFinite(p.width_mm)
      ? p.width_mm : widthAlongStyle(style, u);

    v[i] = {
      x: q.x,
      y: q.y,
      halfWidth: Math.max(
        SILK_LOOK.minHalfWidth,
        Math.min(
          SILK_LOOK.maxHalfWidth,
          Math.abs(sourceWidth * q.scale * SILK_LOOK.widthScale)
        )
      )
    };
  }

  for (let i = 0; i < n; i++) {
    const prev = v[Math.max(0, i - 1)];
    const next = v[Math.min(n - 1, i + 1)];
    const tangent = safeUnit(
      next.x - prev.x,
      next.y - prev.y
    );

    v[i].nx = -tangent.y;
    v[i].ny = tangent.x;
  }

  for (let i = 1; i < n; i++) {
    const a = v[i - 1];
    const b = v[i];

    if (a.nx * b.nx + a.ny * b.ny < 0) {
      b.nx *= -1;
      b.ny *= -1;
    }
  }

  return v;
}

function getRibbonVertices(ctx, pts, style) {
  const route = state.route;
  const sig = cameraSignature(
    ctx.canvas.width,
    ctx.canvas.height
  );

  const isPrefix = route &amp;&amp; pts.length &amp;&amp;
    pts.length <= route.length &amp;&amp;
    pts[0] === route[0] &amp;&amp;
    pts[pts.length - 1] === route[pts.length - 1];

  const cache = state._vertCache;

  if (isPrefix &amp;&amp; cache &amp;&amp;
      cache.sig === sig &amp;&amp;
      cache.src === route) {
    return cache.verts.slice(0, pts.length);
  }

  const full = isPrefix ? route : pts;
  const verts = buildRibbonVertices(ctx, full, style);

  if (isPrefix) {
    state._vertCache = { sig, src: route, verts };
  }

  return isPrefix ? verts.slice(0, pts.length) : verts;
}

function traceRibbonShape(ctx, v) {
  if (!v.length) return;

  ctx.beginPath();

  ctx.moveTo(
    v[0].x + v[0].nx * v[0].halfWidth,
    v[0].y + v[0].ny * v[0].halfWidth
  );

  for (let i = 1; i < v.length; i++) {
    const p = v[i];
    ctx.lineTo(
      p.x + p.nx * p.halfWidth,
      p.y + p.ny * p.halfWidth
    );
  }

  for (let i = v.length - 1; i >= 0; i--) {
    const p = v[i];
    ctx.lineTo(
      p.x - p.nx * p.halfWidth,
      p.y - p.ny * p.halfWidth
    );
  }

  ctx.closePath();
}

// 平滑显示线条，不改变原始轨迹数据
function strokeCenter(ctx, v, normalOffset = 0) {
  if (!v || v.length < 2) return;

  const point = p => ({
    x: p.x + (p.nx || 0) * normalOffset,
    y: p.y + (p.ny || 0) * normalOffset
  });

  ctx.beginPath();

  const first = point(v[0]);
  ctx.moveTo(first.x, first.y);

  for (let i = 1; i < v.length; i++) {
    const a = point(v[i - 1]);
    const b = point(v[i]);

    ctx.quadraticCurveTo(
      a.x, a.y,
      (a.x + b.x) * 0.5,
      (a.y + b.y) * 0.5
    );
  }

  const last = point(v[v.length - 1]);
  ctx.lineTo(last.x, last.y);
  ctx.stroke();
}

// =====================================================
// 1. SILK
// =====================================================

function drawRibbon(ctx, pts, style, color, alpha) {
  if (!pts || pts.length < 2) return;

  const matEl = document.getElementById('matSel');
  const mat = matEl ? matEl.value : 'silk';
  const v = getRibbonVertices(ctx, pts, style);
  if (!v || v.length < 2) return;

  // 固定左上方光源
  let lightScore = 0;
  for (let i = 0; i < v.length; i++) {
    lightScore += v[i].nx * -0.55 + v[i].ny * -0.84;
  }
  const litSide = lightScore >= 0 ? 1 : -1;

  ctx.save();
  ctx.globalAlpha = clamp01(alpha);
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  if (mat === 'line') {
    ctx.strokeStyle = color || '#f4f5f1';
    ctx.lineWidth = 0.48;
    strokeCenter(ctx, v);
    ctx.restore();
    return;
  }

  if (mat === 'silk') {
    // 极淡的外层
    ctx.strokeStyle = SILK_LOOK.silkHalo;
    ctx.lineWidth = 1.05;
    strokeCenter(ctx, v);

    // 背光侧
    ctx.strokeStyle = 'rgba(38,45,43,0.24)';
    ctx.lineWidth = 0.88;
    strokeCenter(ctx, v, -litSide * 0.16);

    // 半透明丝芯
    ctx.strokeStyle = SILK_LOOK.silkCore;
    ctx.lineWidth = 0.50;
    strokeCenter(ctx, v);

    // 受光侧的纵向细高光
    ctx.strokeStyle = SILK_LOOK.silkSheen;
    ctx.lineWidth = 0.20;
    strokeCenter(ctx, v, litSide * 0.17);

    ctx.strokeStyle = 'rgba(255,255,255,0.16)';
    ctx.lineWidth = 0.12;
    strokeCenter(ctx, v, litSide * 0.29);

    ctx.restore();
    return;
  }

  // Ribbon：仍然是乳白色，不使用金棕色
  traceRibbonShape(ctx, v);
  ctx.fillStyle = SILK_LOOK.ribbonBase;
  ctx.fill();

  ctx.strokeStyle = SILK_LOOK.ribbonShadow;
  ctx.lineWidth = 0.52;
  ctx.stroke();

  ctx.save();
  traceRibbonShape(ctx, v);
  ctx.clip();

  ctx.strokeStyle = SILK_LOOK.ribbonHighlight;
  ctx.lineWidth = 0.28;
  ctx.globalAlpha *= 0.68;
  strokeCenter(ctx, v, litSide * 0.26);

  ctx.restore();
  ctx.restore();
}

// =====================================================
// 2. BODY WIDTH
// =====================================================

function wormHalfWidth(t) {
  const smooth = x => {
    const q = clamp01(x);
    return q * q * (3 - 2 * q);
  };

  if (t < 0.12) {
    return 0.40 + 0.42 * smooth(t / 0.12);
  }

  if (t < 0.24) {
    return 0.82 + 0.18 * smooth((t - 0.12) / 0.12);
  }

  if (t < 0.78) {
    return 1.00 - 0.05 * ((t - 0.24) / 0.54);
  }

  if (t < 0.90) {
    return 0.95 - 0.20 * smooth((t - 0.78) / 0.12);
  }

  return 0.75 - 0.70 * smooth((t - 0.90) / 0.10);
}

// =====================================================
// 3. HISTORICAL SPINE
// =====================================================

function spineBehind(head, W, H, bodyLen, angle) {
  const route = (state.route &amp;&amp; state.route.length)
    ? state.route
    : (state.points || []);

  if (!head || !route.length) return [];

  const headSc = projectPoint(head, W, H);

  let idx = Math.min(
    route.length - 1,
    Math.max(0, state.frame || 0)
  );

  if (Number.isFinite(head.endIndex)) {
    idx = Math.min(
      route.length - 1,
      Math.max(0, head.endIndex)
    );
  } else if (route[idx] !== head) {
    let best = idx;
    let bestD = Infinity;

    for (let i = 0; i < route.length; i++) {
      const dx = route[i].x - head.x;
      const dy = route[i].y - head.y;
      const d = dx * dx + dy * dy;

      if (d < bestD) {
        bestD = d;
        best = i;
      }
    }

    idx = best;
  }

  const raw = [{ x: headSc.x, y: headSc.y }];
  let acc = 0;

  // 沿历史轨迹向后取身体骨架
  for (let i = idx; i > 0 &amp;&amp; acc < bodyLen; i--) {
    const a = i === idx
      ? headSc
      : projectPoint(route[i], W, H);

    const b = projectPoint(route[i - 1], W, H);
    const seg = Math.hypot(b.x - a.x, b.y - a.y);

    if (seg < 1e-4) continue;

    if (acc + seg <= bodyLen) {
      raw.push(b);
      acc += seg;
    } else {
      const f = (bodyLen - acc) / seg;

      raw.push({
        x: a.x + (b.x - a.x) * f,
        y: a.y + (b.y - a.y) * f
      });

      acc = bodyLen;
    }
  }

  // 播放初期历史长度不足时，沿当前方向补足身体
  if (acc < bodyLen) {
    const tail = raw[raw.length - 1];
    const prev = raw[Math.max(0, raw.length - 2)];

    let dir;

    if (raw.length >= 2) {
      dir = safeUnit(
        tail.x - prev.x,
        tail.y - prev.y
      );
    } else {
      const a = Number.isFinite(angle) ? angle : 0;
      dir = {
        x: -Math.cos(a),
        y: -Math.sin(a)
      };
    }

    raw.push({
      x: tail.x + dir.x * (bodyLen - acc),
      y: tail.y + dir.y * (bodyLen - acc)
    });
  }

  let total = 0;

  for (let i = 1; i < raw.length; i++) {
    total += Math.hypot(
      raw[i].x - raw[i - 1].x,
      raw[i].y - raw[i - 1].y
    );
  }

  if (total < 1e-5) return [];

  // 等弧长采样
  const n = 44;
  const out = [];

  for (let k = 0; k < n; k++) {
    const target = total * k / (n - 1);
    let run = 0;
    let placed = raw[raw.length - 1];

    for (let i = 1; i < raw.length; i++) {
      const a = raw[i - 1];
      const b = raw[i];

      const seg = Math.hypot(
        b.x - a.x,
        b.y - a.y
      );

      if (run + seg >= target || i === raw.length - 1) {
        const f = seg < 1e-6
          ? 0
          : clamp01((target - run) / seg);

        placed = {
          x: a.x + (b.x - a.x) * f,
          y: a.y + (b.y - a.y) * f
        };

        break;
      }

      run += seg;
    }

    out.push(placed);
  }

  for (let i = 0; i < n; i++) {
    const prev = out[Math.max(0, i - 1)];
    const next = out[Math.min(n - 1, i + 1)];

    const tangent = safeUnit(
      next.x - prev.x,
      next.y - prev.y
    );

    out[i].nx = -tangent.y;
    out[i].ny = tangent.x;
    out[i].tx = tangent.x;
    out[i].ty = tangent.y;
  }

  for (let i = 1; i < n; i++) {
    if (
      out[i - 1].nx * out[i].nx +
      out[i - 1].ny * out[i].ny < 0
    ) {
      out[i].nx *= -1;
      out[i].ny *= -1;
    }
  }

  return out;
}

function sampleSpineAt(spine, t) {
  const f = clamp01(t) * (spine.length - 1);
  const i = Math.floor(f);
  const j = Math.min(spine.length - 1, i + 1);
  const q = f - i;

  const a = spine[i];
  const b = spine[j];

  const tangent = safeUnit(
    a.tx + (b.tx - a.tx) * q,
    a.ty + (b.ty - a.ty) * q
  );

  const normal = safeUnit(
    a.nx + (b.nx - a.nx) * q,
    a.ny + (b.ny - a.ny) * q
  );

  return {
    x: a.x + (b.x - a.x) * q,
    y: a.y + (b.y - a.y) * q,
    tx: tangent.x,
    ty: tangent.y,
    nx: normal.x,
    ny: normal.y
  };
}

// =====================================================
// 4. BODY SILHOUETTE
// =====================================================

function traceBodySilhouette(ctx, spine, widths) {
  const left = [];
  const right = [];

  for (let i = 0; i < spine.length; i++) {
    const p = spine[i];
    const w = widths[i];

    left.push({
      x: p.x + p.nx * w,
      y: p.y + p.ny * w
    });

    right.push({
      x: p.x - p.nx * w,
      y: p.y - p.ny * w
    });
  }

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

  ctx.lineTo(
    left[left.length - 1].x,
    left[left.length - 1].y
  );

  ctx.lineTo(
    right[right.length - 1].x,
    right[right.length - 1].y
  );

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
}

// =====================================================
// 5. CAUDAL HORN
// =====================================================

function drawCaudalHorn(ctx, spine, widthAt, alpha) {
  const p = sampleSpineAt(spine, 0.90);
  const base = Math.max(1.25, widthAt(0.90) * 0.20);

  const tipX = p.x + p.tx * 6.2 + p.nx * base * 1.8;
  const tipY = p.y + p.ty * 6.2 + p.ny * base * 1.8;

  ctx.save();
  ctx.globalAlpha = clamp01(alpha * 0.88);

  ctx.beginPath();

  ctx.moveTo(
    p.x - p.nx * base,
    p.y - p.ny * base
  );

  ctx.quadraticCurveTo(
    p.x + p.tx * 2.4 - p.nx * base * 0.75,
    p.y + p.ty * 2.4 - p.ny * base * 0.75,
    tipX, tipY
  );

  ctx.quadraticCurveTo(
    p.x + p.tx * 2.4 + p.nx * base * 0.75,
    p.y + p.ty * 2.4 + p.ny * base * 0.75,
    p.x + p.nx * base,
    p.y + p.ny * base
  );

  ctx.closePath();
  ctx.fillStyle = '#b7b2a6';
  ctx.fill();

  ctx.strokeStyle = 'rgba(145,141,132,0.42)';
  ctx.lineWidth = 0.55;
  ctx.stroke();

  ctx.restore();
}

// =====================================================
// 6. HEAD CAPSULE
// =====================================================

function drawWormHeadCap(ctx, p, maxHalf, alpha) {
  const tail = safeUnit(p.tx, p.ty);
  const forward = { x: -tail.x, y: -tail.y };
  const normal = safeUnit(p.nx, p.ny);

  const headLen = maxHalf * 0.92;
  const headHalf = maxHalf * 0.30;

  const center = {
    x: p.x + tail.x * headLen * 0.36,
    y: p.y + tail.y * headLen * 0.36
  };

  const at = (along, across) => ({
    x: center.x + forward.x * along * headLen
      + normal.x * across * headHalf,
    y: center.y + forward.y * along * headLen
      + normal.y * across * headHalf
  });

  ctx.save();
  ctx.globalAlpha = clamp01(alpha);
  ctx.beginPath();

  let q = at(-0.54, 0.42);
  ctx.moveTo(q.x, q.y);

  q = at(-0.10, 0.92);
  let c = at(-0.40, 0.98);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  q = at(0.38, 0.44);
  c = at(0.28, 0.88);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  q = at(0.58, 0);
  c = at(0.62, 0.08);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  q = at(0.38, -0.44);
  c = at(0.62, -0.08);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  q = at(-0.10, -0.92);
  c = at(0.28, -0.88);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  q = at(-0.54, -0.42);
  c = at(-0.40, -0.98);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  ctx.closePath();

  const grad = ctx.createLinearGradient(
    center.x - headHalf, center.y - headHalf,
    center.x + headHalf, center.y + headHalf
  );
  grad.addColorStop(0, '#715b49');
  grad.addColorStop(0.42, '#514034');
  grad.addColorStop(1, '#302720');

  ctx.fillStyle = grad;
  ctx.fill();

  ctx.strokeStyle = 'rgba(35,27,22,0.62)';
  ctx.lineWidth = 0.62;
  ctx.stroke();

  // 微弱头壳反光，不画夸张的大眼睛
  ctx.beginPath();
  const h1 = at(-0.18, 0.54);
  const h2 = at(0.20, 0.42);
  const hc = at(0.08, 0.66);

  ctx.moveTo(h1.x, h1.y);
  ctx.quadraticCurveTo(hc.x, hc.y, h2.x, h2.y);

  ctx.strokeStyle = 'rgba(241,225,205,0.25)';
  ctx.lineWidth = 0.62;
  ctx.stroke();

  // 极小的吐丝口
  const tip = at(0.56, 0);
  ctx.beginPath();
  ctx.ellipse(
    tip.x, tip.y, 0.72, 0.42,
    Math.atan2(forward.y, forward.x),
    0, Math.PI * 2
  );
  ctx.fillStyle = 'rgba(30,24,20,0.70)';
  ctx.fill();

  ctx.restore();
}

// =====================================================
// 7. COMPLETE WORM BODY
// =====================================================

function drawWormBody(ctx, head, style, alpha, angle) {
  if (!head) return;

  const W = ctx.canvas.width;
  const H = ctx.canvas.height;

  const bodyLen = Math.max(
    96,
    Math.min(190, Math.min(W, H) * 0.19)
  );
  const maxHalf = bodyLen / 12.2;

  // 沿真实历史轨迹取身体骨架
  const spine = spineBehind(
    head, W, H, bodyLen, angle
  );

  if (spine.length < 2) return;

  const widthAt = t => wormHalfWidth(t) * maxHalf;
  const widths = spine.map((_, i) =>
    widthAt(i / (spine.length - 1))
  );

  let minX = Infinity, minY = Infinity;
  let maxX = -Infinity, maxY = -Infinity;

  for (let i = 0; i < spine.length; i++) {
    minX = Math.min(minX, spine[i].x - widths[i]);
    minY = Math.min(minY, spine[i].y - widths[i]);
    maxX = Math.max(maxX, spine[i].x + widths[i]);
    maxY = Math.max(maxY, spine[i].y + widths[i]);
  }

  let lightScore = 0;
  for (const p of spine) {
    lightScore += p.nx * -0.55 + p.ny * -0.84;
  }
  const litSide = lightScore >= 0 ? 1 : -1;

  ctx.save();
  ctx.globalAlpha = clamp01(alpha);
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';

  // 乳白、浅米色身体
  traceBodySilhouette(ctx, spine, widths);

  const bodyGrad = ctx.createLinearGradient(
    minX, minY, maxX, maxY
  );
  bodyGrad.addColorStop(0, '#fffdf6');
  bodyGrad.addColorStop(0.24, '#f2f0e8');
  bodyGrad.addColorStop(0.58, '#e7e4da');
  bodyGrad.addColorStop(0.84, '#d9d6cc');
  bodyGrad.addColorStop(1, '#c6c2b8');

  ctx.fillStyle = bodyGrad;
  ctx.fill();

  ctx.strokeStyle = 'rgba(126,122,113,0.30)';
  ctx.lineWidth = 0.68;
  ctx.stroke();

  ctx.save();
  traceBodySilhouette(ctx, spine, widths);
  ctx.clip();

  // 背部柔和高光
  ctx.globalAlpha = clamp01(alpha * 0.34);
  ctx.strokeStyle = 'rgba(255,255,250,0.72)';
  ctx.lineWidth = maxHalf * 0.44;
  strokeCenter(ctx, spine, litSide * maxHalf * 0.18);

  // 背光侧阴影
  ctx.globalAlpha = clamp01(alpha * 0.18);
  ctx.strokeStyle = 'rgba(112,108,99,0.34)';
  ctx.lineWidth = Math.max(1, maxHalf * 0.22);
  strokeCenter(ctx, spine, -litSide * maxHalf * 0.62);

  // 不等距的浅体节沟
  const ringTs = [
    0.14, 0.21, 0.29, 0.37, 0.45,
    0.53, 0.61, 0.69, 0.77, 0.84
  ];

  for (let i = 0; i < ringTs.length; i++) {
    const t = ringTs[i];
    const p = sampleSpineAt(spine, t);
    const w = widthAt(t) * 0.88;

    ctx.globalAlpha = clamp01(
      alpha * (i < 2 ? 0.30 : 0.23)
    );
    ctx.strokeStyle = 'rgba(119,115,106,0.40)';
    ctx.lineWidth = 0.62;

    ctx.beginPath();
    ctx.moveTo(
      p.x + p.nx * w,
      p.y + p.ny * w
    );
    ctx.quadraticCurveTo(
      p.x + p.tx * 1.35,
      p.y + p.ty * 1.35,
      p.x - p.nx * w,
      p.y - p.ny * w
    );
    ctx.stroke();

    // 环沟旁边的细微受光边
    ctx.globalAlpha = clamp01(alpha * 0.16);
    ctx.strokeStyle = 'rgba(255,255,250,0.60)';
    ctx.lineWidth = 0.48;

    ctx.beginPath();
    ctx.moveTo(
      p.x + p.tx + p.nx * w * 0.92,
      p.y + p.ty + p.ny * w * 0.92
    );
    ctx.quadraticCurveTo(
      p.x + p.tx * 2.1,
      p.y + p.ty * 2.1,
      p.x + p.tx - p.nx * w * 0.92,
      p.y + p.ty - p.ny * w * 0.92
    );
    ctx.stroke();
  }

  // 很淡的侧面气门
  ctx.globalAlpha = clamp01(alpha * 0.25);
  ctx.fillStyle = 'rgba(103,99,91,0.38)';

  for (let j = 0; j < 7; j++) {
    const t = 0.35 + j * 0.071;
    const p = sampleSpineAt(spine, t);
    const w = widthAt(t) * 0.76;
    const rot = Math.atan2(p.ny, p.nx);

    for (const side of [-1, 1]) {
      ctx.beginPath();
      ctx.ellipse(
        p.x + p.nx * w * side,
        p.y + p.ny * w * side,
        0.82, 0.48, rot,
        0, Math.PI * 2
      );
      ctx.fill();
    }
  }

  ctx.restore();

  // 后段尾角和前端头壳
  drawCaudalHorn(ctx, spine, widthAt, alpha);
  drawWormHeadCap(ctx, spine[0], maxHalf, alpha);

  ctx.restore();
}

// =====================================================
// 8. KEEP ORIGINAL DRAW INTERFACE
// =====================================================

function screenHeading(from, to, W, H) {
  if (!from || !to) return 0;

  const a = projectPoint(from, W, H);
  const b = projectPoint(to, W, H);

  return Math.atan2(
    b.y - a.y,
    b.x - a.x
  );
}

function drawWormHead(ctx, head, style) {
  if (
    !document.getElementById('showWorm').checked ||
    !head
  ) return;

  const prev = state.route &amp;&amp; state.frame > 0
    ? state.route[Math.max(0, state.frame - 1)]
    : null;

  const ang = screenHeading(
    prev,
    head,
    ctx.canvas.width,
    ctx.canvas.height
  );

  drawWormBody(ctx, head, style, 1, ang);
}

function draw() {
  const cvs = document.getElementById('cvs');
  const ctx = cvs.getContext('2d');
  const W = cvs.width, H = cvs.height;
  ctx.fillStyle = '#1a1c21';
  ctx.fillRect(0, 0, W, H);

  if (!state.points.length) {
    ctx.fillStyle = '#8a8f99';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('请从描图器点「并排吐丝预览」或载入 motion-model / 3D JSON', W / 2, H / 2);
    return;
  }

  const home = homeBox();
  ctx.strokeStyle = 'rgba(210,206,198,0.14)';
  ctx.lineWidth = 1;
  for (let ix = -3; ix <= 4; ix++) {
    for (let iy = -3; iy <= 3; iy++) {
      traceProjectedRect(ctx, cellRect(ix, iy), W, H);
      ctx.stroke();
    }
  }

  for (const cell of state.litCells) {
    const r = cellRect(cell.ix, cell.iy);
    traceProjectedRect(ctx, r, W, H);
    ctx.fillStyle = 'rgba(196,164,122,0.14)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(214,176,122,0.85)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  if (document.getElementById('showBeh').checked) {
    const boxes = state.behaviorBoxes.length ? state.behaviorBoxes : [{ box_px: home }];
    boxes.forEach((bu, i) => {
      const box = bu.box_px || bu;
      if (box.x0 == null) return;
      const rect = {
        x0: Math.min(box.x0, box.x1),
        y0: Math.min(box.y0, box.y1),
        x1: Math.max(box.x0, box.x1),
        y1: Math.max(box.y0, box.y1)
      };
      const corners = traceProjectedRect(ctx, rect, W, H);
      ctx.strokeStyle = i === 0 ? 'rgba(150,176,170,0.9)' : 'rgba(196,164,122,0.85)';
      ctx.lineWidth = 1.6;
      ctx.stroke();
      ctx.fillStyle = 'rgba(150,176,170,0.08)';
      ctx.fill();
      ctx.fillStyle = '#d7c4a4';
      ctx.font = 'bold 16px sans-serif';
      ctx.fillText(String(box.id || bu.boxId || i + 1), corners[0].x + 8, corners[0].y + 20);
    });
  }

  const route = state.route.length ? state.route : state.points;
  const end = Math.min(state.frame + 1, route.length);
  const slice = route.slice(0, end);
  if (document.getElementById('showSilk').checked &amp;&amp; slice.length >= 2) {
    drawRibbon(ctx, slice, state.style, state.color, state.style.opacity);
  }
  if (document.getElementById('showPts') &amp;&amp; document.getElementById('showPts').checked) {
    ctx.fillStyle = state.color;
    for (const p of slice) {
      const sc = projectPoint(p, W, H);
      ctx.beginPath(); ctx.arc(sc.x, sc.y, 2.2, 0, Math.PI * 2); ctx.fill();
    }
  }
  const head = slice[slice.length - 1];
  if (document.getElementById('showResidue') &amp;&amp; document.getElementById('showResidue').checked) {
    (state.cellMarks || []).forEach((mark) => {
      if (mark.endIndex < end - 1) {
        const i = Math.min(route.length - 1, Math.max(1, mark.endIndex));
        const ang = screenHeading(route[i - 1], route[i], W, H);
        drawWormBody(ctx, mark, state.style, 0.38, ang);
      }
    });
  }
  drawWormHead(ctx, head, state.style);

  const u = head &amp;&amp; head.u != null ? head.u : (end - 1) / Math.max(1, route.length - 1);
  document.getElementById('uSlider').value = Math.round((u || 0) * 1000);
  document.getElementById('playStat').innerHTML =
    `帧 <b>${end}</b> / ${route.length} · 点亮 <b>${state.litCells.length}</b> 格` +
    (state.statusNote ? `<br>${state.statusNote}` : '');
}

function tick(ts) {
  if (!state.playing) return;
  if (!state.lastT) state.lastT = ts;
  const dt = (ts - state.lastT) / 1000;
  state.lastT = ts;
  const pps = parseFloat(document.getElementById('pps').value);
  const rate = Number.isFinite(pps) ? pps : 4;
  state.playAcc += dt * rate;
  const adv = Math.floor(state.playAcc);
  state.playAcc -= adv;
  const route = state.route.length ? state.route : state.points;
  state.frame += adv;
  if (state.frame >= route.length - 1) {
    if (document.getElementById('loopOn').checked) {
      state.frame = 0;
      state.playAcc = 0;
    } else {
      state.frame = Math.max(0, route.length - 1);
      state.playing = false;
    }
  }
  draw();
  if (state.playing) requestAnimationFrame(tick);
}

function clearLit() {
  state.litCells = [];
  rebuildRoute();
  computeBounds();
  draw();
}

function traceProjectedRect(ctx, rect, W, H) {
  const corners = [
    { x: rect.x0, y: rect.y0 },
    { x: rect.x1, y: rect.y0 },
    { x: rect.x1, y: rect.y1 },
    { x: rect.x0, y: rect.y1 }
  ].map(p => projectPoint(p, W, H));
  ctx.beginPath();
  ctx.moveTo(corners[0].x, corners[0].y);
  for (let i = 1; i < corners.length; i++) ctx.lineTo(corners[i].x, corners[i].y);
  ctx.closePath();
  return corners;
}

function screenToWorld(sx, sy) {
  const cvs = document.getElementById('cvs');
  const W = cvs.width, H = cvs.height;
  const cx = W / 2, cy = H / 2;
  const { yaw, tilt } = cameraAngles();
  const sxr = sx - cx;
  const syr = sy - cy;
  let xr, y2;
  if (tilt > 0.001) {
    const K = H * 6;
    const denom = 1 - syr / K;
    y2 = Math.abs(denom) < 1e-6 ? 0 : syr / denom;
    const persp = 1 / (1 + y2 / K);
    xr = sxr / (persp || 1);
  } else {
    xr = sxr;
    y2 = syr;
  }
  const yr = y2 / (Math.cos(tilt) || 1e-6);
  const cosY = Math.cos(yaw), sinY = Math.sin(yaw);
  const preX = xr * cosY + yr * sinY + cx;
  const preY = -xr * sinY + yr * cosY + cy;
  const b = state.bounds;
  const spanX = b.maxX - b.minX || 1;
  const spanY = b.maxY - b.minY || 1;
  const s = Math.min(W / spanX, H / spanY);
  const ox = (W - spanX * s) / 2 + state.panX;
  const oy = (H - spanY * s) / 2 + state.panY;
  return { x: (preX - ox) / s + b.minX, y: (preY - oy) / s + b.minY };
}

function reachableLit(cells) {
  const keep = [];
  const pool = cells.map(c => ({ ix: c.ix, iy: c.iy }));
  const seen = new Set(['0,0']);
  const q = [{ ix: 0, iy: 0 }];
  while (q.length) {
    const cur = q.shift();
    for (const c of pool) {
      const key = c.ix + ',' + c.iy;
      if (seen.has(key)) continue;
      if (Math.abs(c.ix - cur.ix) + Math.abs(c.iy - cur.iy) === 1) {
        seen.add(key);
        keep.push(c);
        q.push(c);
      }
    }
  }
  return keep;
}

function toggleCellAt(sx, sy) {
  const wpt = screenToWorld(sx, sy);
  const h = homeBox();
  const ix = Math.floor((wpt.x - h.x0) / h.w);
  const iy = Math.floor((wpt.y - h.y0) / h.h);
  if (ix === 0 &amp;&amp; iy === 0) return;
  const i = state.litCells.findIndex(c => c.ix === ix &amp;&amp; c.iy === iy);
  if (i >= 0) {
    state.litCells.splice(i, 1);
    state.litCells = reachableLit(state.litCells);
    state.statusNote = '';
  } else {
    const occupied = [{ ix: 0, iy: 0 }, ...state.litCells];
    const near = occupied.some(c => Math.abs(c.ix - ix) + Math.abs(c.iy - iy) === 1);
    if (!near) {
      state.statusNote = '只能点亮上下左右相邻的格子';
      draw();
      return;
    }
    state.litCells.push({ ix, iy });
    state.statusNote = '';
  }
  rebuildRoute();
  computeBounds();
  draw();
}

function onPointerDown(e) {
  const cvs = document.getElementById('cvs');
  const rect = cvs.getBoundingClientRect();
  state.drag = {
    id: e.pointerId,
    x: e.clientX,
    y: e.clientY,
    panX: state.panX,
    panY: state.panY,
    moved: false,
    sx: (e.clientX - rect.left) * (cvs.width / rect.width),
    sy: (e.clientY - rect.top) * (cvs.height / rect.height),
  };
  cvs.setPointerCapture(e.pointerId);
}

function onPointerMove(e) {
  const d = state.drag;
  if (!d || d.id !== e.pointerId) return;
  const dx = e.clientX - d.x;
  const dy = e.clientY - d.y;
  if (Math.hypot(dx, dy) > 5) d.moved = true;
  if (d.moved) {
    const cvs = document.getElementById('cvs');
    const rect = cvs.getBoundingClientRect();
    state.panX = d.panX + dx * (cvs.width / rect.width);
    state.panY = d.panY + dy * (cvs.height / rect.height);
    draw();
  }
}

function onPointerUp(e) {
  const d = state.drag;
  if (!d || d.id !== e.pointerId) return;
  if (!d.moved) toggleCellAt(d.sx, d.sy);
  state.drag = null;
}

function exportPng() {
  const cvs = document.getElementById('cvs');
  cvs.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'silk-preview-' + Date.now() + '.png';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }, 'image/png');
}

function togglePlay() {
  state.playing = !state.playing;
  state.lastT = 0;
  if (state.playing) requestAnimationFrame(tick);
}

function scrubU(v) {
  const u = parseInt(v, 10) / 1000;
  const route = state.route.length ? state.route : state.points;
  let best = 0, bestD = 1e9;
  for (let i = 0; i < route.length; i++) {
    const d = Math.abs((route[i].u || 0) - u);
    if (d < bestD) { bestD = d; best = i; }
  }
  state.frame = best;
  state.playing = false;
  draw();
}

function syncUI() {
  document.getElementById('ppsVal').textContent = parseFloat(document.getElementById('pps').value).toFixed(1);
  const n = parseFloat(document.getElementById('noise').value) / 100;
  document.getElementById('noiseVal').textContent = n.toFixed(2);
}

function perturbPoints(base, noise, seed) {
  const rand = mulberry32(seed);
  const stoch = (state.synth &amp;&amp; state.synth.stochasticLayer) || {};
  const sigma = (stoch.stepLength_mm &amp;&amp; stoch.stepLength_mm.sigma) || 0.15;
  return base.map((p, i) => {
    if (i === 0 || i === base.length - 1) return { ...p };
    const j = noise * sigma * (rand() - 0.5) * 1.2;
    const k = noise * sigma * (rand() - 0.5) * 1.2;
    return { ...p, x: p.x + j, y: p.y + k, width_mm: p.width_mm };
  });
}

function regenerateSynthetic() {
  if (state.points.length < 2) return;
  const noise = parseFloat(document.getElementById('noise').value) / 100;
  const seed = parseInt(document.getElementById('seed').value, 10) || 1;
  state.ghostPoints = state.points.map(p => ({ ...p }));
  state.points = perturbPoints(state.points, noise, seed);
  ensureUMonotone();
  rebuildRoute();
  computeBounds();
  state.provenance = 'synthetic';
  state.frame = 0;
  state.playing = true;
  state.lastT = 0;
  document.getElementById('seed').value = seed + 1;
  document.getElementById('dataBadge').textContent = '合成轨迹';
  updateTrajStat();
  requestAnimationFrame(tick);
  draw();
}

function updateTrajStat() {
  const t = state.trajectories[state.activeIdx];
  document.getElementById('trajStat').innerHTML = t
    ? `蚕 <b>${t.wormId}</b> · <b>${state.points.length}</b> 点 · 单位 <b>${state.unit}</b>`
    : '—';
}

function syncTrajTabs() {
  const box = document.getElementById('trajTabs');
  if (!box) return;
  box.innerHTML = state.trajectories.map((t, i) =>
    '<button type=&quot;button&quot; class=&quot;' + (i === state.activeIdx ? 'active' : '') + '&quot; data-i=&quot;' + i + '&quot;>蚕 ' + t.wormId + '</button>'
  ).join('');
  Array.prototype.forEach.call(box.children, btn => {
    btn.addEventListener('click', () => switchTrajectory(Number(btn.dataset.i)));
  });
}

function switchTrajectory(i) {
  if (!state.trajectories[i] || i === state.activeIdx) return;
  state.activeIdx = i;
  const t = state.trajectories[i];
  state.points = t.points.map(p => ({ ...p }));
  state.style = { ...state.style, ...(t.style || {}) };
  ensureUMonotone();
  computeBounds();
  state.frame = 0;
  state.ghostPoints = null;
  state.litCells = [];
  rebuildRoute();
  updateTrajStat();
  syncTrajTabs();
  draw();
}

function pushTrajToParent() {
  if (window.parent === window) return;
  try {
    window.parent.postMessage({
      type: 'silkworm-preview/data',
      trajectories: state.trajectories.map(t => ({
        wormId: t.wormId, color: t.color, style: t.style,
        points: (t.points || []).map(p => ({ x: p.x, y: p.y, u: p.u, kind: p.kind })),
      })),
    }, '*');
  } catch (_) { /* */ }
}

function ingestPayload(doc) {
  const norm = normalizeIncoming(doc);
  if (!setTrajectoryList(norm)) {
    alert('未识别到可用轨迹点列');
    return;
  }
  draw();
  pushTrajToParent();
}

function loadJsonFile(e) {
  const f = e.target.files[0];
  if (!f) return;
  const rd = new FileReader();
  rd.onload = () => {
    try { ingestPayload(JSON.parse(rd.result)); }
    catch (err) { alert('JSON 无效: ' + err.message); }
    e.target.value = '';
  };
  rd.readAsText(f);
}

function tryStorage() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) ingestPayload(JSON.parse(raw));
  } catch (_) { /* */ }
}

window.addEventListener('message', (ev) => {
  if (ev.data &amp;&amp; ev.data.type === 'silkworm-preview/v1') ingestPayload(ev.data);
  if (ev.data &amp;&amp; ev.data.type === 'silkworm-preview-push') ingestPayload(ev.data.payload);
  if (ev.data &amp;&amp; ev.data.type === 'silkworm-preview/request-data') pushTrajToParent();
});

window.addEventListener('resize', () => draw());
tryStorage();
const cvs = document.getElementById('cvs');
cvs.addEventListener('pointerdown', onPointerDown);
cvs.addEventListener('pointermove', onPointerMove);
cvs.addEventListener('pointerup', onPointerUp);
cvs.addEventListener('pointercancel', onPointerUp);
draw();
const goHab = document.getElementById('goHabitat');
if (goHab) goHab.addEventListener('click', () => {
  if (window.parent !== window) window.parent.postMessage({ type: 'silkworm-goto-habitat' }, '*');
  else {
    const h = document.getElementById('habitat');
    if (h) h.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
});

let applyingConditions = false;

function readConditions() {
  const recordedAt = (document.getElementById('condTime').value || '').trim() || null;
  const t = parseFloat(document.getElementById('condTemp').value);
  const h = parseFloat(document.getElementById('condHum').value);
  return {
    recordedAt,
    temperatureC: Number.isFinite(t) ? t : null,
    humidity: Number.isFinite(h) ? h : null,
  };
}

function formatConditions(c) {
  if (!c || (!c.recordedAt &amp;&amp; c.temperatureC == null &amp;&amp; c.humidity == null)) return '未填写实验条件';
  const when = c.recordedAt ? String(c.recordedAt).replace('T', ' ') : '时间未填';
  const temp = c.temperatureC == null ? '温度未填' : c.temperatureC + ' °C';
  const hum = c.humidity == null ? '湿度未填' : c.humidity + '%';
  return when + ' · ' + temp + ' · 湿度 ' + hum;
}

function syncConditionPreset() {
  const sel = document.getElementById('condPreset');
  if (!sel) return;
  const key = document.getElementById('condTemp').value + ',' + document.getElementById('condHum').value;
  sel.value = [...sel.options].some(o => o.value === key) ? key : '';
}

function applyConditions(c) {
  const next = c || { recordedAt: null, temperatureC: null, humidity: null };
  applyingConditions = true;
  document.getElementById('condTime').value = next.recordedAt ? String(next.recordedAt).slice(0, 16) : '';
  document.getElementById('condTemp').value = next.temperatureC == null ? '' : next.temperatureC;
  document.getElementById('condHum').value = next.humidity == null ? '' : next.humidity;
  applyingConditions = false;
  syncConditionPreset();
  document.getElementById('condStat').textContent = formatConditions(readConditions());
}

function onConditionsEdited() {
  syncConditionPreset();
  const c = readConditions();
  document.getElementById('condStat').textContent = formatConditions(c);
  if (applyingConditions) return;
  if (window.parent !== window) {
    window.parent.postMessage({ type: 'silkworm-studio/conditions', conditions: c }, '*');
  }
}

function fillConditionNow() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  document.getElementById('condTime').value = d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + 'T' + p(d.getHours()) + ':' + p(d.getMinutes());
  onConditionsEdited();
}

function applyConditionPreset() {
  const v = document.getElementById('condPreset').value;
  if (!v) return;
  const parts = v.split(',');
  document.getElementById('condTemp').value = parts[0];
  document.getElementById('condHum').value = parts[1];
  onConditionsEdited();
}

function numInput(id, fallback) {
  const el = document.getElementById(id);
  const n = el ? parseFloat(el.value) : NaN;
  return Number.isFinite(n) ? n : fallback;
}

function studioPreviewSlice() {
  return {
    pps: numInput('pps', 4),
    loopOn: document.getElementById('loopOn').checked,
    showSilk: document.getElementById('showSilk').checked,
    showWorm: document.getElementById('showWorm').checked,
    showResidue: document.getElementById('showResidue').checked,
    showPts: document.getElementById('showPts').checked,
    showBeh: document.getElementById('showBeh').checked,
    mat: document.getElementById('matSel').value,
    tilt: numInput('tilt', 0),
    yaw: numInput('yaw', 0),
    noise: numInput('noise', 35),
    seed: document.getElementById('seed').value,
    frame: state.frame,
    panX: state.panX,
    panY: state.panY,
    litCells: state.litCells.map(c => ({ ix: c.ix, iy: c.iy })),
    trajectories: state.trajectories,
    activeIdx: state.activeIdx,
    behaviorBoxes: state.behaviorBoxes,
    unit: state.unit,
    provenance: state.provenance,
  };
}

function applyStudioPreview(preview) {
  if (!preview) return;
  const setCheck = (id, val) => { if (typeof val === 'boolean') document.getElementById(id).checked = val; };
  const setVal = (id, val) => { if (val != null) document.getElementById(id).value = val; };
  setVal('pps', preview.pps);
  setVal('tilt', preview.tilt);
  setVal('yaw', preview.yaw);
  setVal('noise', preview.noise);
  setVal('seed', preview.seed);
  setVal('matSel', preview.mat);
  setCheck('loopOn', preview.loopOn);
  setCheck('showSilk', preview.showSilk);
  setCheck('showWorm', preview.showWorm);
  setCheck('showResidue', preview.showResidue);
  setCheck('showPts', preview.showPts);
  setCheck('showBeh', preview.showBeh);
  if (preview.trajectories &amp;&amp; preview.trajectories.length) {
    setTrajectoryList({
      trajectories: preview.trajectories,
      behaviorBoxes: preview.behaviorBoxes || [],
      unit: preview.unit || 'px',
      provenance: preview.provenance || 'measured',
    }, preview.activeIdx || 0);
  }
  if (Array.isArray(preview.litCells)) {
    state.litCells = preview.litCells.map(c => ({ ix: c.ix, iy: c.iy }));
    rebuildRoute();
    computeBounds();
  }
  if (Number.isFinite(preview.panX)) state.panX = preview.panX;
  if (Number.isFinite(preview.panY)) state.panY = preview.panY;
  if (Number.isFinite(preview.frame)) state.frame = preview.frame;
  syncUI();
  draw();
  pushTrajToParent();
}

function saveStudioProject() {
  const data = {
    schema: 'silkworm-studio/project',
    projectVersion: 3,
    savedAt: new Date().toISOString(),
    conditions: readConditions(),
    preview: studioPreviewSlice(),
    habitat: window.__studioHabitat ? window.__studioHabitat.export() : null,
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'silkworm-project-' + Date.now() + '.json';
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

function loadStudioProject(e) {
  const f = e.target.files &amp;&amp; e.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result);
      if (data.preview) applyStudioPreview(data.preview);
      else if (data.trajectories || data.unifiedTrajectories || data.curves) ingestPayload(data);
      else if (data.worms) {
        const trajectories = Object.keys(data.worms).map((id) => {
          const w = data.worms[id];
          const points = (w.points || []).map((p, i, arr) => ({
            x: p.x, y: p.y, u: arr.length > 1 ? i / (arr.length - 1) : 0, width_mm: p.width_mm,
          }));
          return { wormId: +id, color: w.color || '#ffffff', style: w.style, points };
        }).filter(t => t.points.length >= 2);
        const behaviorBoxes = [];
        Object.keys(data.worms).forEach((id) => {
          (data.worms[id].behaviorBoxes || []).forEach((b) => behaviorBoxes.push({ box_px: b, boxId: b.id }));
        });
        if (trajectories.length) ingestPayload({ type: 'silkworm-preview/v1', trajectories, behaviorBoxes, provenance: 'measured' });
      }
      if (data.habitat &amp;&amp; window.parent !== window) window.parent.postMessage({ type: 'silkworm-habitat/import', habitat: data.habitat }, '*');
      if (data.schema === 'silkworm-studio/project' || Object.prototype.hasOwnProperty.call(data, 'conditions')) {
        applyConditions(data.conditions || null);
        if (window.parent !== window) {
          window.parent.postMessage({ type: 'silkworm-studio/conditions', conditions: readConditions() }, '*');
        }
      }
      if (!data.preview &amp;&amp; !data.habitat &amp;&amp; !data.conditions &amp;&amp; !data.trajectories &amp;&amp; !data.worms &amp;&amp; !data.curves &amp;&amp; !data.unifiedTrajectories) {
        alert('这个 JSON 里没有可载入的工程、轨迹或蚕室数据');
      }
    } catch (err) {
      alert('工程 JSON 无效: ' + err.message);
    }
    e.target.value = '';
  };
  reader.readAsText(f);
}

window.addEventListener('message', (ev) => {
  if (!ev.data) return;
  if (ev.data.type === 'silkworm-studio/export-request') {
    window.parent.postMessage({
      type: 'silkworm-studio/export',
      preview: studioPreviewSlice(),
      habitat: window.__studioHabitat ? window.__studioHabitat.export() : null,
      conditions: readConditions(),
    }, '*');
  }
  if (ev.data.type === 'silkworm-studio/import') {
    applyStudioPreview(ev.data.preview);
    if (ev.data.habitat &amp;&amp; window.parent !== window) window.parent.postMessage({ type: 'silkworm-habitat/import', habitat: ev.data.habitat }, '*');
    if (ev.data.conditions) applyConditions(ev.data.conditions);
  }
  if (ev.data.type === 'silkworm-studio/conditions' &amp;&amp; ev.data.conditions) {
    applyConditions(ev.data.conditions);
  }
});

if (window.parent !== window) {
  window.parent.postMessage({ type: 'silkworm-preview-ready' }, '*');
}
