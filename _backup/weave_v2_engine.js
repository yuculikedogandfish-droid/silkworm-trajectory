  function weaveSdfGrad(cell, x, y) {
    const e = 0.8;
    return {
      dx: (weaveSDF(cell, x + e, y) - weaveSDF(cell, x - e, y)) / (2 * e),
      dy: (weaveSDF(cell, x, y + e) - weaveSDF(cell, x, y - e)) / (2 * e),
    };
  }

  function weaveProject(cell, x, y, pad) {
    for (let k = 0; k < 5; k++) {
      const d = weaveSDF(cell, x, y);
      if (d <= -pad) break;
      const g = weaveSdfGrad(cell, x, y);
      const len = Math.hypot(g.dx, g.dy) || 1;
      const push = d + pad + 0.3;
      x -= g.dx / len * push;
      y -= g.dy / len * push;
    }
    return { x, y };
  }

  /* 一条丝 = 若干「竖长八字」包络连成的一根线。
     实测：蚕在一次框定里走的是拉长的 8 字（两瓣叠在一个交叉点），不是同心螺圈。
     所以这里用 Lissajous 8 字（x=sin t, y=sin 2t，纵向振幅大于横向）当运动语法，
     再把点投影回格内（SDF 推开墙与外岛），保证不穿墙。 */
  function weaveFigureEight(cell, agent, seed) {
    const rng = mulberry32(seed >>> 0);
    const W = cell.w, H = cell.h;
    const cov = Math.max(0.15, Math.min(0.85, Number.isFinite(agent.coverage) ? agent.coverage : 0.55));
    const loops = 1 + Math.floor(cov * 2.2 + rng() * 0.9);
    const pad = Math.min(W, H) * (0.09 + (1 - cov) * 0.05);
    const pts = [];
    const baseRot = (rng() < 0.5 ? -1 : 1) * (0.24 + rng() * 0.30);
    for (let L = 0; L < loops; L++) {
      const ax = W * (0.28 + rng() * 0.10);
      const ay = H * (0.36 + rng() * 0.10);
      const rot = baseRot + (rng() - 0.5) * 0.32;
      const ph = rng() * Math.PI * 2;
      const ox = (rng() - 0.5) * W * 0.16;
      const oy = (rng() - 0.5) * H * 0.20;
      const cs = Math.cos(rot), sn = Math.sin(rot);
      const N = 150;
      for (let k = 0; k <= N; k++) {
        const t = ph + k / N * Math.PI * 2;
        const rx = ax * Math.sin(t);
        const ry = ay * Math.sin(2 * t);
        let x = ox + rx * cs - ry * sn;
        let y = oy + rx * sn + ry * cs;
        const q = weaveProject(cell, x, y, pad);
        const jitter = Math.min(W, H) * 0.004 * (0.4 + (agent.wallAff || 0.6));
        pts.push({
          x: q.x + (rng() - 0.5) * jitter,
          y: q.y + (rng() - 0.5) * jitter,
        });
      }
    }
    return pts;
  }

  function weaveHash01(ix, iy, seed) {
    let h = Math.imul(ix, 374761393) ^ Math.imul(iy, 668265263) ^ (seed >>> 0);
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
  }

  function weaveCellContent(agent, ix, iy) {
    if (!agent.cache) agent.cache = new Map();
    const key = ix + ',' + iy;
    const hit = agent.cache.get(key);
    if (hit) return hit;
    const seed = (((agent.seed >>> 0) ^ Math.imul(ix, 374761393) ^ Math.imul(iy, 668265263)) ^ 0x9e3779b9) >>> 0;
    const cell = weaveCellSpecAt(agent, ix, iy, seed);
    const n = Math.max(1, Math.min(6, Math.round(agent.worms || 3)));
    const paths = [];
    for (let t = 0; t < n; t++) {
      const pts = weaveFigureEight(cell, agent, (seed + t * 7919 + 17) >>> 0);
      if (pts.length > 20) paths.push({ pts, seed });
    }
    const content = { cell, paths, walls: weaveContour(cell), seed };
    agent.cache.set(key, content);
    if (agent.cache.size > 360) agent.cache.delete(agent.cache.keys().next().value);
    return content;
  }

  function buildWeave(agent) {
    agent.cache = new Map();
    agent.paths = [];
    agent.walls = [];
    const origin = weaveCellContent(agent, 0, 0);
    agent.sample = {
      threads: origin.paths.length,
      points: origin.paths.reduce((s, p) => s + p.pts.length, 0),
      walls: origin.walls.length,
    };
    if (!Number.isFinite(agent.u)) agent.u = 0;
  }

  function makeWeaveAgent(x, y, seed) {
    return {
      id: 'wv-' + (habitat.agents.filter(a => a.kind === 'weave').length + 1),
      kind: 'weave',
      mode: 'idle',
      bodyVisible: true,
      x: x, y: y,
      w: 200, h: 200,
      coverage: 0.55,
      shape: 'plain',
      worms: 3,
      wallAff: 0.6,
      seed: (seed == null ? Math.floor(Math.random() * 1e9) : seed) >>> 0,
      u: 0,
      duration: 22,
      speedScale: 1,
      silk: [],
      heading: 0,
      walls: [],
      paths: [],
      cache: null,
      sample: null,
    };
  }

  function addWeaveAgent() {
    const a = arenaSpec();
    const base = a.kind === 'circle' ? a.r : Math.min(a.hw, a.hh);
    const x = Math.round((Math.random() - 0.5) * base * 0.2);
    const y = Math.round((Math.random() - 0.5) * base * 0.2);
    pushUndo();
    const agent = makeWeaveAgent(x, y);
    agent.w = agent.h = Math.round(Math.min(240, Math.max(150, base * 0.62)));
    agent.u = 0;
    buildWeave(agent);
    habitat.agents.push(agent);
    habitat.selected = agent.id;
    renderList();
    toast('已放入织网格网 ' + agent.id + '，点「开始」让它织。', 'ok');
    hint('格子没有外边界，平移或缩放会继续长出新的格子；右侧可改格子尺寸、覆盖率与每格丝数。');
  }

  function drawWeave(ctx, agent, v) {
    const cw = Math.max(60, agent.w), ch = Math.max(60, agent.h);
    const wx0 = (0 - v.cx) / v.s - agent.x;
    const wx1 = (v.w - v.cx) / v.s - agent.x;
    const wy0 = (0 - v.cy) / v.s - agent.y;
    const wy1 = (v.h - v.cy) / v.s - agent.y;
    let i0 = Math.floor(wx0 / cw) - 1, i1 = Math.floor(wx1 / cw) + 1;
    let j0 = Math.floor(wy0 / ch) - 1, j1 = Math.floor(wy1 / ch) + 1;
    if (i1 - i0 > 40) i1 = i0 + 40;
    if (j1 - j0 > 40) j1 = j0 + 40;
    const u = Math.max(0, Math.min(1, agent.u || 0));
    const seed = agent.seed >>> 0;
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    for (let j = j0; j <= j1; j++) {
      for (let i = i0; i <= i1; i++) {
        const content = weaveCellContent(agent, i, j);
        const ox = agent.x + i * cw;
        const oy = agent.y + j * ch;
        ctx.strokeStyle = 'rgba(196,214,204,0.40)';
        ctx.lineWidth = Math.max(0.8, 1.0 * v.s);
        content.walls.forEach(line => {
          ctx.beginPath();
          for (let k = 0; k < line.length; k++) {
            const px = v.px(ox + line[k].x), py = v.py(oy + line[k].y);
            if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
          }
          ctx.stroke();
        });
        if (agent.bodyVisible === false) continue;
        const delay = weaveHash01(i, j, seed) * 0.18;
        const lu = Math.max(0, Math.min(1, (u - delay) / (1 - delay || 1)));
        if (lu <= 0) continue;
        const light = 0.34 + weaveHash01(i, j, seed + 101) * 0.26;
        ctx.globalCompositeOperation = 'lighter';
        ctx.strokeStyle = 'rgba(226,232,228,' + light.toFixed(2) + ')';
        ctx.lineWidth = Math.max(0.8, 0.9 * Math.max(1, v.s * 0.6));
        content.paths.forEach(p => {
          const n = Math.max(2, Math.floor(p.pts.length * lu));
          ctx.beginPath();
          for (let k = 0; k < n; k++) {
            const px = v.px(ox + p.pts[k].x), py = v.py(oy + p.pts[k].y);
            if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
          }
          ctx.stroke();
        });
      }
    }
    ctx.restore();
  }

