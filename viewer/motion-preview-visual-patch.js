// =====================================================
// SILKWORM VISUAL PATCH
// Replace SILK_LOOK through drawWormHead()
// Keep projectPoint(), draw(), and all motion logic.
// =====================================================

const SILK_LOOK = Object.freeze({
  widthScale: 0.035,
  minHalfWidth: 0.28,
  maxHalfWidth: 0.85,
  silkHalo: 'rgba(236,241,242,0.055)',
  silkCore: 'rgba(236,240,240,0.30)',
  silkSheen: 'rgba(255,255,255,0.16)',
  ribbonBase: 'rgba(236,240,240,0.24)',
  ribbonShadow: 'rgba(120,128,130,0.12)',
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

  const isPrefix = route && pts.length &&
    pts.length <= route.length &&
    pts[0] === route[0] &&
    pts[pts.length - 1] === route[pts.length - 1];

  const cache = state._vertCache;

  if (isPrefix && cache &&
      cache.sig === sig &&
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
  if (v.length < 2) return;

  ctx.save();
  ctx.globalAlpha = clamp01(alpha);
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  if (mat === 'line') {
    ctx.strokeStyle = 'rgba(236,240,240,0.62)';
    ctx.lineWidth = 0.68;
    strokeCenter(ctx, v);
    ctx.restore();
    return;
  }

  if (mat === 'silk') {
    // 细微乳白光晕
    ctx.strokeStyle = SILK_LOOK.silkHalo;
    ctx.lineWidth = 1.25;
    strokeCenter(ctx, v);

    // 主丝线
    ctx.strokeStyle = SILK_LOOK.silkCore;
    ctx.lineWidth = 0.62;
    strokeCenter(ctx, v);

    // 极细高光
    ctx.strokeStyle = SILK_LOOK.silkSheen;
    ctx.lineWidth = 0.24;
    strokeCenter(ctx, v, 0.12);

    ctx.restore();
    return;
  }

  // 可选丝带模式，但限制宽度
  traceRibbonShape(ctx, v);
  ctx.fillStyle = SILK_LOOK.ribbonBase;
  ctx.fill();

  ctx.strokeStyle = SILK_LOOK.ribbonShadow;
  ctx.lineWidth = 0.55;
  ctx.stroke();

  ctx.save();
  traceRibbonShape(ctx, v);
  ctx.clip();

  ctx.strokeStyle = SILK_LOOK.ribbonHighlight;
  ctx.lineWidth = 0.38;
  ctx.globalAlpha *= 0.72;
  strokeCenter(ctx, v, -0.12);

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
  const route = (state.route && state.route.length)
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
  for (let i = idx; i > 0 && acc < bodyLen; i--) {
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
  // tx / ty point from the head towards the tail
  const tail = safeUnit(p.tx, p.ty);

  const forward = {
    x: -tail.x,
    y: -tail.y
  };

  const normal = {
    x: p.nx,
    y: p.ny
  };

  const headLen = maxHalf * 1.02;
  const headHalf = maxHalf * 0.45;

  const center = {
    x: p.x + tail.x * headLen * 0.48,
    y: p.y + tail.y * headLen * 0.48
  };

  const at = (along, across) => ({
    x: center.x +
      forward.x * along * headLen +
      normal.x * across * headHalf,

    y: center.y +
      forward.y * along * headLen +
      normal.y * across * headHalf
  });

  ctx.save();
  ctx.globalAlpha = clamp01(alpha);
  ctx.beginPath();

  let q = at(-0.54, 0.48);
  ctx.moveTo(q.x, q.y);

  q = at(-0.12, 0.96);
  let c = at(-0.42, 1.00);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  q = at(0.43, 0.42);
  c = at(0.30, 0.92);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  q = at(0.58, 0);
  c = at(0.66, 0.08);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  q = at(0.43, -0.42);
  c = at(0.66, -0.08);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  q = at(-0.12, -0.96);
  c = at(0.30, -0.92);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  q = at(-0.54, -0.48);
  c = at(-0.42, -1.00);
  ctx.quadraticCurveTo(c.x, c.y, q.x, q.y);

  ctx.closePath();

  ctx.fillStyle = '#4b392e';
  ctx.fill();

  ctx.strokeStyle = 'rgba(35,27,22,0.72)';
  ctx.lineWidth = 0.72;
  ctx.stroke();

  // Restrained shell highlight; no oversized cartoon eyes.
  ctx.globalAlpha = clamp01(alpha * 0.30);
  ctx.beginPath();

  const h1 = at(-0.16, 0.62);
  const h2 = at(0.25, 0.48);
  const hc = at(0.12, 0.70);

  ctx.moveTo(h1.x, h1.y);
  ctx.quadraticCurveTo(
    hc.x, hc.y,
    h2.x, h2.y
  );

  ctx.strokeStyle = 'rgba(235,220,202,0.62)';
  ctx.lineWidth = 0.75;
  ctx.stroke();

  ctx.restore();
}

// =====================================================
// 7. COMPLETE WORM BODY
// =====================================================

function drawWormBody(ctx, head, style, alpha, angle) {
  if (!head) return;

  const W = ctx.canvas.width;
  const H = ctx.canvas.height;

  // Display proportions, not physical measurements.
  const bodyLen = Math.max(
    96,
    Math.min(190, Math.min(W, H) * 0.19)
  );

  const maxHalf = bodyLen / 12.2;

  const spine = spineBehind(
    head, W, H, bodyLen, angle
  );

  if (spine.length < 2) return;

  const widthAt = t => wormHalfWidth(t) * maxHalf;

  const widths = spine.map((_, i) =>
    widthAt(i / (spine.length - 1))
  );

  ctx.save();
  ctx.globalAlpha = clamp01(alpha);
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';

  // Main body
  traceBodySilhouette(ctx, spine, widths);

  ctx.fillStyle = '#ecebe5';
  ctx.fill();

  ctx.strokeStyle = 'rgba(151,148,139,0.58)';
  ctx.lineWidth = 0.72;
  ctx.stroke();

  // Internal body details
  ctx.save();

  traceBodySilhouette(ctx, spine, widths);
  ctx.clip();

  // Dorsal highlight
  ctx.globalAlpha = clamp01(alpha * 0.34);
  ctx.strokeStyle = 'rgba(255,255,250,0.72)';
  ctx.lineWidth = maxHalf * 0.78;
  strokeCenter(ctx, spine);

  // Lateral shading
  ctx.globalAlpha = clamp01(alpha * 0.22);
  ctx.strokeStyle = 'rgba(139,136,127,0.48)';
  ctx.lineWidth = 1.05;

  strokeCenter(ctx, spine, maxHalf * 0.68);
  strokeCenter(ctx, spine, -maxHalf * 0.68);

  // Segment folds
  const ringTs = [
    0.12, 0.19, 0.26,
    0.33, 0.40, 0.47, 0.54, 0.61,
    0.68, 0.75, 0.82, 0.88
  ];

  ctx.globalAlpha = clamp01(alpha * 0.52);
  ctx.strokeStyle = 'rgba(130,127,119,0.38)';
  ctx.lineWidth = 0.72;

  for (const t of ringTs) {
    const p = sampleSpineAt(spine, t);
    const w = widthAt(t) * 0.86;

    ctx.beginPath();

    ctx.moveTo(
      p.x + p.nx * w,
      p.y + p.ny * w
    );

    ctx.quadraticCurveTo(
      p.x + p.tx * 1.25,
      p.y + p.ty * 1.25,
      p.x - p.nx * w,
      p.y - p.ny * w
    );

    ctx.stroke();
  }

  // Subtle lateral spiracles
  ctx.globalAlpha = clamp01(alpha * 0.42);
  ctx.fillStyle = 'rgba(116,108,98,0.42)';

  for (let j = 0; j < 8; j++) {
    const t = 0.34 + j * 0.067;
    const p = sampleSpineAt(spine, t);
    const w = widthAt(t) * 0.84;
    const rot = Math.atan2(p.ny, p.nx);

    for (const side of [-1, 1]) {
      ctx.beginPath();

      ctx.ellipse(
        p.x + p.nx * w * side,
        p.y + p.ny * w * side,
        1.05, 0.62,
        rot, 0, Math.PI * 2
      );

      ctx.fill();
    }
  }

  ctx.restore();

  // Posterior caudal horn
  drawCaudalHorn(ctx, spine, widthAt, alpha);

  // Anterior dark head capsule
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

  const prev = state.route && state.frame > 0
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
