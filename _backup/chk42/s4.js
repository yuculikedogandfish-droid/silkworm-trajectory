
/* ===== r43 识别升级：自由版式（连通域）+ 圆/轮廓双通道 + 局部阈值 + 校对（独立模块，不改既有函数） ===== */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const REC = () => window.__imgRec;
  if (!REC() || !$('habRecOverlay')) return;
  const state = REC().state;
  const legacyAnalyse = REC().analyse;
  const S = () => window.__studioHabitat;
  const say = (t) => { const el = $('habRecNote'); if (el) el.textContent = t; };

  /* ---------- 覆盖层：r43 自己画（原 r37 画布停用，避免两套预览打架） ---------- */
  const old = $('habRecOverlay');
  old.style.display = 'none';
  const ov = document.createElement('canvas');
  ov.id = 'habRecOverlay43';
  ov.style.cssText = 'position:absolute;z-index:7;pointer-events:none;';
  const wrap = $('habWorldWrap');
  wrap.appendChild(ov);
  const octx = ov.getContext('2d');
  state.compare = true;
  state.pick = false;

  function resize() {
    const world = $('habWorld');
    if (!wrap || !world) return;
    if (ov.width !== wrap.clientWidth || ov.height !== wrap.clientHeight) { ov.width = wrap.clientWidth; ov.height = wrap.clientHeight; }
    ov.style.left = world.offsetLeft + 'px'; ov.style.top = world.offsetTop + 'px';
  }
  function drawPoly(pts, close) {
    octx.beginPath();
    pts.forEach((p, i) => { const X = p[0], Y = p[1]; if (i) octx.lineTo(X, Y); else octx.moveTo(X, Y); });
    if (close) octx.closePath();
  }
  function paint() {
    resize();
    octx.clearRect(0, 0, ov.width, ov.height);
    const H = S();
    if (!H) return;
    const v = H.view();
    if (state.compare && state.map && state.thumb) {
      const m = state.map;
      octx.save();
      octx.globalAlpha = 0.34;
      octx.drawImage(state.thumb, v.px(m.ox), v.py(m.oy), m.w * v.s, m.h * v.s);
      octx.restore();
    }
    (state.boxes || []).forEach(b => {
      const x = v.px(b.wx - b.w / 2), y = v.py(b.wy - b.h / 2);
      const w = b.w * v.s, h = b.h * v.s;
      const weak = b.present && b.conf < 0.55;
      octx.save();
      octx.strokeStyle = !b.present ? 'rgba(255,120,120,0.45)' : (weak ? 'rgba(240,200,90,0.95)' : 'rgba(121,203,182,0.95)');
      octx.lineWidth = weak ? 1.6 : 1.2;
      octx.setLineDash(b.present ? (weak ? [5, 3] : []) : [4, 4]);
      octx.strokeRect(x, y, w, h);
      if (b.present) { octx.fillStyle = 'rgba(121,203,182,0.05)'; octx.fillRect(x, y, w, h); }
      octx.restore();
      (b.polys || []).forEach(poly => {
        octx.save();
        octx.strokeStyle = 'rgba(150,190,255,0.95)';
        octx.lineWidth = 1.2;
        octx.setLineDash([3, 3]);
        drawPoly(poly.pts.map(p => [v.px(b.wx + p.x), v.py(b.wy + p.y)]), true);
        octx.stroke();
        octx.restore();
      });
    });
    (state.holes || []).forEach(h2 => {
      octx.save();
      octx.beginPath();
      octx.arc(v.px(h2.wx), v.py(h2.wy), Math.max(1, h2.wr * v.s), 0, Math.PI * 2);
      octx.strokeStyle = 'rgba(232,201,138,0.9)';
      octx.lineWidth = 1.1;
      octx.stroke();
      octx.restore();
    });
    requestAnimationFrame(paint);
  }
  requestAnimationFrame(paint);

  // 校对模式：点预览框 = 这块要 / 不要
  ov.addEventListener('pointerdown', (e) => {
    if (!state.pick) return;
    e.preventDefault(); e.stopPropagation();
    const H = S(); if (!H) return;
    const v = H.view();
    const r = ov.getBoundingClientRect();
    const wx = (e.clientX - r.left - v.cx) / v.s, wy = (e.clientY - r.top - v.cy) / v.s;
    let best = null, bd = Infinity;
    (state.boxes || []).forEach(b => {
      const d = Math.abs(wx - b.wx) / b.w + Math.abs(wy - b.wy) / b.h;
      if (Math.abs(wx - b.wx) <= b.w / 2 && Math.abs(wy - b.wy) <= b.h / 2 && d < bd) { bd = d; best = b; }
    });
    if (best) { best.present = !best.present; best.conf = 1; }
  });

  /* ---------- 控件（操作者语言） ---------- */
  const cols = document.querySelector('.hab-rec-cols');
  if (cols && !$('habRecCov')) {
    const div = document.createElement('div');
    div.innerHTML =
      '<div class="row"><label>丝多稀也算一块</label><input type="range" id="habRecCov" min="12" max="60" step="1" value="28" style="width:110px"><span class="hab-adj-val" id="habRecCovVal">28%</span></div>' +
      '<div class="row"><label>多小的洞才保留</label><input type="range" id="habRecMinHole" min="2" max="30" step="1" value="4" style="width:110px"><span class="hab-adj-val" id="habRecMinHoleVal">4%</span></div>' +
      '<div class="row"><label><input type="checkbox" id="habRecCompare" checked> 预览时叠上原图对比</label></div>' +
      '<div class="row"><button type="button" id="habRecPick">点预览框补块 / 去块</button></div>' +
      '<p class="hab-note" style="margin:2px 0 0">列 / 排填 0＝按真实轮廓自动找块（每块可大小不同）；填了数字＝按固定网格切。黄色虚线＝把握不高，点它可改。</p>';
    cols.appendChild(div);
    const cov = $('habRecCov'), mh = $('habRecMinHole');
    cov.addEventListener('input', () => { $('habRecCovVal').textContent = cov.value + '%'; });
    mh.addEventListener('input', () => { $('habRecMinHoleVal').textContent = mh.value + '%'; });
    $('habRecCompare').addEventListener('change', (e) => { state.compare = !!e.target.checked; });
    $('habRecPick').addEventListener('click', () => {
      state.pick = !state.pick;
      ov.style.pointerEvents = state.pick ? 'auto' : 'none';
      ov.style.cursor = state.pick ? 'crosshair' : 'default';
      $('habRecPick').textContent = state.pick ? '校对有块 / 无块中…（再点我退出）' : '点预览框补块 / 去块';
      if (state.pick) say('点预览里的框：红变绿＝补一块，绿变红＝这块不要。改完再点「生成到场地」。');
    });
  }

  /* ---------- 图像基础 ---------- */
  function blur(g, w, h, r) {
    const tmp = new Float32Array(w * h), out = new Float32Array(w * h), win = 2 * r + 1;
    for (let y = 0; y < h; y++) {
      let acc = 0; const base = y * w;
      for (let x = -r; x <= r; x++) acc += g[base + Math.min(w - 1, Math.max(0, x))];
      for (let x = 0; x < w; x++) {
        tmp[base + x] = acc / win;
        acc += g[base + Math.min(w - 1, x + r + 1)] - g[base + Math.max(0, x - r)];
      }
    }
    for (let x = 0; x < w; x++) {
      let acc = 0;
      for (let y = -r; y <= r; y++) acc += tmp[Math.min(h - 1, Math.max(0, y)) * w + x];
      for (let y = 0; y < h; y++) {
        out[y * w + x] = acc / win;
        acc += tmp[Math.min(h - 1, y + r + 1) * w + x] - tmp[Math.max(0, y - r) * w + x];
      }
    }
    return out;
  }
  function otsu(g) {
    const hist = new Int32Array(256);
    for (let i = 0; i < g.length; i++) hist[Math.max(0, Math.min(255, g[i] | 0))]++;
    const total = g.length; let sum = 0;
    for (let t = 0; t < 256; t++) sum += t * hist[t];
    let sumB = 0, wB = 0, best = 0, thr = 100;
    for (let t = 0; t < 256; t++) {
      wB += hist[t]; if (!wB) continue;
      const wF = total - wB; if (!wF) break;
      sumB += t * hist[t];
      const mB = sumB / wB, mF = (sum - sumB) / wF, between = wB * wF * (mB - mF) * (mB - mF);
      if (between > best) { best = between; thr = t; }
    }
    return thr;
  }
  // 可分离 3×3 最大/最小滤波（反复 r 次），只用于把同一块里的丝连成一片
  function morph(src, w, h, r, maxMode) {
    let a = src, b = new Uint8Array(w * h);
    for (let k = 0; k < r; k++) {
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        let v = maxMode ? 0 : 1;
        for (let dx = -1; dx <= 1; dx++) { const xx = x + dx; if (xx < 0 || xx >= w) continue; const q = a[y * w + xx]; if (maxMode ? q > v : q < v) v = q; }
        b[y * w + x] = v;
      }
      a.set(b);
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        let v = maxMode ? 0 : 1;
        for (let dy = -1; dy <= 1; dy++) { const yy = y + dy; if (yy < 0 || yy >= h) continue; const q = a[yy * w + x]; if (maxMode ? q > v : q < v) v = q; }
        b[y * w + x] = v;
      }
      a.set(b);
    }
    return a;
  }
  function components(mask, w, h) {
    const seen = new Uint8Array(w * h), out = [], stack = new Int32Array(w * h);
    for (let i = 0; i < mask.length; i++) {
      if (!mask[i] || seen[i]) continue;
      let sp = 0; stack[sp++] = i; seen[i] = 1;
      let cnt = 0, minX = w, maxX = 0, minY = h, maxY = 0;
      while (sp) {
        const q = stack[--sp], qx = q % w, qy = (q - qx) / w;
        cnt++; if (qx < minX) minX = qx; if (qx > maxX) maxX = qx; if (qy < minY) minY = qy; if (qy > maxY) maxY = qy;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          const xx = qx + dx, yy = qy + dy;
          if (xx < 0 || yy < 0 || xx >= w || yy >= h) continue;
          const n = yy * w + xx;
          if (mask[n] && !seen[n]) { seen[n] = 1; stack[sp++] = n; }
        }
      }
      out.push({ cnt, minX, maxX, minY, maxY });
    }
    return out;
  }
  // 二值区域外轮廓（Moore 邻接追踪），返回相对 region 左上角的点列
  function trace(mask, W, H2, startIdx) {
    const startX = startIdx % W, startY = (startIdx - startX) / W;
    const pts = [];
    const dirs = [[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]];
    let cx = startX, cy = startY, dir = 6, guard = W * H2 * 4;
    const isOn = (x, y) => x >= 0 && y >= 0 && x < W && y < H2 && mask[y * W + x];
    do {
      pts.push([cx, cy]);
      let found = false;
      for (let k = 0; k < 8; k++) {
        const d = (dir + k) % 8, nx = cx + dirs[d][0], ny = cy + dirs[d][1];
        if (isOn(nx, ny)) { cx = nx; cy = ny; dir = (d + 5) % 8; found = true; break; }
      }
      if (!found) break;
    } while ((cx !== startX || cy !== startY) && --guard > 0 && pts.length < 20000);
    return pts;
  }
  function rdp(pts, eps) {
    if (pts.length < 4) return pts;
    const keep = new Uint8Array(pts.length); keep[0] = keep[pts.length - 1] = 1;
    const stack = [[0, pts.length - 1]];
    while (stack.length) {
      const [a, b] = stack.pop();
      const ax = pts[a][0], ay = pts[a][1], bx = pts[b][0], by = pts[b][1];
      const len = Math.hypot(bx - ax, by - ay) || 1e-6;
      let bi = -1, bd = 0;
      for (let i = a + 1; i < b; i++) {
        const d = Math.abs((bx - ax) * (ay - pts[i][1]) - (ax - pts[i][0]) * (by - ay)) / len;
        if (d > bd) { bd = d; bi = i; }
      }
      if (bd > eps && bi > 0) { keep[bi] = 1; stack.push([a, bi], [bi, b]); }
    }
    return pts.filter((p, i) => keep[i]);
  }


  /* ---------- 版式切分：黑色细分隔线 + 区域递归（块可不等大、可错位） ---------- */
  function segment(gray, bg, w, h, glob) {
    const sb = blur(gray, w, h, 1);
    const lineThr = Math.max(18, glob * 0.55);
    const dark = new Uint8Array(w * h);
    let dx0 = w, dx1 = 0, dy0 = h, dy1 = 0, bright = 0;
    for (let i = 0; i < dark.length; i++) {
      dark[i] = gray[i] < lineThr ? 1 : 0;
      if (sb[i] > glob) {
        bright++;
        const x = i % w, y = (i - x) / w;
        if (x < dx0) dx0 = x; if (x > dx1) dx1 = x; if (y < dy0) dy0 = y; if (y > dy1) dy1 = y;
      }
    }
    if (bright < w * h * 0.01) return [];
    // 允许 2px 断口的最长暗线长度
    function colRun(x, y0, y1) {
      let n = 0;
      for (let y = y0; y <= y1; y++) if (dark[y * w + x]) n++;
      return n;
    }
    function rowRun(y, x0, x1) {
      let n = 0;
      for (let x = x0; x <= x1; x++) if (dark[y * w + x]) n++;
      return n;
    }
    const MIN = 26;
    const out = [];
    function split(x0, x1, y0, y1, depth) {
      const W = x1 - x0 + 1, H2 = y1 - y0 + 1;
      if (W < MIN * 2 || H2 < MIN * 2 || depth > 14) { out.push({ minX: x0, maxX: x1, minY: y0, maxY: y1 }); return; }
      let bv = null, bh = null;
      if (depth === 0) { window.__segDebug = { v: 0, h: 0, W, H: H2, lineThr }; }
      for (let x = x0 + MIN; x <= x1 - MIN; x++) {
        const sc = colRun(x, y0, y1) / H2;
        if (depth === 0 && sc > window.__segDebug.v) window.__segDebug.v = Math.round(sc * 100) / 100;
        if (sc < 0.42) continue;
        if (bv && sc <= bv.sc) continue;
        // 细线特征：左右 3px 外不能同样暗（否则是大片暗区/孔洞，不是分隔线）
        const side = Math.max(colRun(Math.max(x0, x - 3), y0, y1), colRun(Math.min(x1, x + 3), y0, y1)) / H2;
        if (side > sc * 0.72) continue;
        bv = { x, sc };
      }
      for (let y = y0 + MIN; y <= y1 - MIN; y++) {
        const sc = rowRun(y, x0, x1) / W;
        if (depth === 0 && sc > window.__segDebug.h) window.__segDebug.h = Math.round(sc * 100) / 100;
        if (sc < 0.42) continue;
        if (bh && sc <= bh.sc) continue;
        const side = Math.max(rowRun(Math.max(y0, y - 3), x0, x1), rowRun(Math.min(y1, y + 3), x0, x1)) / W;
        if (side > sc * 0.72) continue;
        bh = { y, sc };
      }
      if (!bv && !bh) { out.push({ minX: x0, maxX: x1, minY: y0, maxY: y1 }); return; }
      if (bv && (!bh || bv.sc >= bh.sc)) {
        let a = bv.x, b = bv.x;
        while (a - 1 > x0 && colRun(a - 1, y0, y1) / H2 > bv.sc * 0.55) a--;
        while (b + 1 < x1 && colRun(b + 1, y0, y1) / H2 > bv.sc * 0.55) b++;
        if (a - 1 - x0 >= MIN && x1 - (b + 1) >= MIN) {
          split(x0, a - 1, y0, y1, depth + 1);
          split(b + 1, x1, y0, y1, depth + 1);
          return;
        }
      } else if (bh) {
        let a = bh.y, b = bh.y;
        while (a - 1 > y0 && rowRun(a - 1, x0, x1) / W > bh.sc * 0.55) a--;
        while (b + 1 < y1 && rowRun(b + 1, x0, x1) / W > bh.sc * 0.55) b++;
        if (a - 1 - y0 >= MIN && y1 - (b + 1) >= MIN) {
          split(x0, x1, y0, a - 1, depth + 1);
          split(x0, x1, b + 1, y1, depth + 1);
          return;
        }
      }
      out.push({ minX: x0, maxX: x1, minY: y0, maxY: y1 });
    }
    split(dx0, dx1, dy0, dy1, 0);
    return out.filter(r => (r.maxX - r.minX + 1) >= MIN && (r.maxY - r.minY + 1) >= MIN);
  }

  /* ---------- 主流程：自由版式 ---------- */
  function analyseAuto() {
    const im = state.img;
    const w = im.w, h = im.h;
    const bg = blur(im.g, w, h, 3);
    // 局部均值（积分图）：丝稀的地方也能被算作"有丝"
    const integ = new Float64Array((w + 1) * (h + 1));
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      integ[(y + 1) * (w + 1) + (x + 1)] = bg[y * w + x] + integ[y * (w + 1) + (x + 1)] + integ[(y + 1) * (w + 1) + x] - integ[y * (w + 1) + x];
    }
    const R = Math.max(14, Math.round(Math.min(w, h) / 36));
    const glob = otsu(bg);
    const mask = new Uint8Array(w * h);
    for (let y = 0; y < h; y++) {
      const y0 = Math.max(0, y - R), y1 = Math.min(h - 1, y + R);
      for (let x = 0; x < w; x++) {
        const x0 = Math.max(0, x - R), x1 = Math.min(w - 1, x + R);
        const s = integ[(y1 + 1) * (w + 1) + (x1 + 1)] - integ[y0 * (w + 1) + (x1 + 1)] - integ[(y1 + 1) * (w + 1) + x0] + integ[y0 * (w + 1) + x0];
        const mean = s / ((y1 - y0 + 1) * (x1 - x0 + 1));
        const thr = Math.max(glob * 0.42, mean * 1.03);
        mask[y * w + x] = bg[y * w + x] > thr ? 1 : 0;
      }
    }
    const comps = segment(im.g, bg, w, h, glob);
    if (!comps.length) { say('没找到成片的丝。换张对比更强的图，或把「丝多稀也算一块」往左调。'); return; }

    let bx0 = w, bx1 = 0, by0 = h, by1 = 0;
    comps.forEach(c => { bx0 = Math.min(bx0, c.minX); bx1 = Math.max(bx1, c.maxX); by0 = Math.min(by0, c.minY); by1 = Math.max(by1, c.maxY); });
    const bbW = bx1 - bx0 + 1, bbH = by1 - by0 + 1;
    const med = (arr) => { const a = arr.slice().sort((p, q) => p - q); return a[a.length >> 1] || 120; };
    const medW = med(comps.map(c => c.maxX - c.minX + 1));
    const Tuser = Number(($('habRecCell') || {}).value || 320);
    const scale = Math.min(900 / bbW, 900 / bbH, Tuser / Math.max(30, medW));
    const ccx = (bx0 + bx1) / 2, ccy = (by0 + by1) / 2;
    state.map = { ox: -ccx * scale, oy: -ccy * scale, w: w * scale, h: h * scale, scale, bx0, by0 };
    if (!state.thumb) {
      const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
      const cx2 = cv.getContext('2d'), id = cx2.createImageData(w, h);
      for (let i = 0; i < w * h; i++) { const v = im.g[i]; id.data[i * 4] = v; id.data[i * 4 + 1] = v; id.data[i * 4 + 2] = v; id.data[i * 4 + 3] = 255; }
      cx2.putImageData(id, 0, 0); state.thumb = cv;
    }

    const covThr = Number(($('habRecCov') || {}).value || 28) / 100;
    const minHoleFrac = Number(($('habRecMinHole') || {}).value || 4) / 100;
    const wantHoles = !!($('habRecHoles') || {}).checked;
    const wantNotch = !!($('habRecNotches') || {}).checked;
    const boxes = [], holes = [];
    let holeN = 0, polyN = 0;

    comps.forEach((c, idx) => {
      const x0 = Math.max(0, c.minX - 1), x1 = Math.min(w - 1, c.maxX + 1);
      const y0 = Math.max(0, c.minY - 1), y1 = Math.min(h - 1, c.maxY + 1);
      const W = x1 - x0 + 1, H2 = y1 - y0 + 1;
      let on = 0;
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (mask[y * w + x]) on++;
      const cov = on / (W * H2);
      const b = {
        present: cov >= covThr, conf: Math.min(1, cov / Math.max(0.001, covThr * 1.8)),
        wx: ((x0 + x1) / 2 - ccx) * scale, wy: ((y0 + y1) / 2 - ccy) * scale,
        w: Math.max(24, W * scale), h: Math.max(24, H2 * scale),
        cov, ci: idx, ri: 0, islands: [], polys: [],
      };
      boxes.push(b);
      if (!b.present || (!wantHoles && !wantNotch)) return;
      b.polys = [];

      // 格内暗区 → 圆孔 或 任意轮廓缺口
      // 孔洞用"糊过的灰度"判定：丝线本身的细缝不会被当成洞
      const holeThr = Math.max(18, glob * 0.55);
      const dm = new Uint8Array(W * H2);
      for (let y = 0; y < H2; y++) for (let x = 0; x < W; x++) dm[y * W + x] = bg[(y0 + y) * w + (x0 + x)] < holeThr ? 1 : 0;
      const seen = new Uint8Array(W * H2), stack = [];
      const area = W * H2;
      for (let i = 0; i < dm.length; i++) {
        if (!dm[i] || seen[i]) continue;
        let minX = W, maxX = 0, minY = H2, maxY = 0, cnt = 0, sx = 0, sy = 0;
        stack.length = 0; stack.push(i); seen[i] = 1;
        const pix = [];
        while (stack.length) {
          const q = stack.pop(), qx = q % W, qy = (q - qx) / W;
          cnt++; sx += qx; sy += qy;
          pix.push(q);
          if (qx < minX) minX = qx; if (qx > maxX) maxX = qx; if (qy < minY) minY = qy; if (qy > maxY) maxY = qy;
          if (qx > 0 && dm[q - 1] && !seen[q - 1]) { seen[q - 1] = 1; stack.push(q - 1); }
          if (qx < W - 1 && dm[q + 1] && !seen[q + 1]) { seen[q + 1] = 1; stack.push(q + 1); }
          if (qy > 0 && dm[q - W] && !seen[q - W]) { seen[q - W] = 1; stack.push(q - W); }
          if (qy < H2 - 1 && dm[q + W] && !seen[q + W]) { seen[q + W] = 1; stack.push(q + W); }
        }
        const frac = cnt / area;
        if (frac < minHoleFrac) continue;
        const touch = minX === 0 || minY === 0 || maxX === W - 1 || maxY === H2 - 1;
        if (touch && frac > 0.62) continue;               // 块外背景，不是咬口
        if (!touch && frac > 0.80) continue;              // 整块都是暗的，按无丝处理
        const bw = maxX - minX + 1, bh = maxY - minY + 1;
        const extent = cnt / (bw * bh), aspect = bw / Math.max(1, bh);
        const sub = new Uint8Array(W * H2);
        pix.forEach(q => { sub[q] = 1; });
        let start = -1;
        for (let k = 0; k < pix.length; k++) { const q = pix[k]; if ((q % W) === minX) { start = q; break; } }
        if (start < 0) start = pix[0];
        let contour = trace(sub, W, H2, start);
        if (contour.length < 6) continue;
        let per = 0;
        for (let k = 0; k < contour.length; k++) { const p = contour[k], q = contour[(k + 1) % contour.length]; per += Math.hypot(q[0] - p[0], q[1] - p[1]); }
        const circ = per > 0 ? (4 * Math.PI * cnt) / (per * per) : 0;
        const isCircle = circ > 0.72 && extent > 0.55 && aspect > 0.6 && aspect < 1.65;
        const lcx = sx / cnt - W / 2, lcy = sy / cnt - H2 / 2;
        if (isCircle && (touch ? wantNotch : wantHoles)) {
          const r = Math.sqrt(cnt / Math.PI) * scale;
          const isl = { cx: lcx * scale, cy: lcy * scale, r };
          b.islands.push(isl);
          holes.push({ wx: b.wx + isl.cx, wy: b.wy + isl.cy, wr: r });
          holeN++;
        } else if (wantNotch && circ >= 0.38) {
          let pts = rdp(contour, Math.max(1.1, per / 220));
          if (pts.length > 26) pts = rdp(contour, Math.max(1.6, per / 130));
          if (pts.length < 3 || pts.length > 30) continue;
          const world = pts.map(p => ({ x: (p[0] - W / 2) * scale, y: (p[1] - H2 / 2) * scale }));
          b.polys.push({ pts: world, area: cnt });
        }
      }
    });

    boxes.forEach(b => {
      if (b.polys && b.polys.length > 2) b.polys = b.polys.sort((p, q) => q.area - p.area).slice(0, 2);
      polyN += (b.polys || []).length;
    });
    state.boxes = boxes;
    state.holes = holes;
    state.grid = { cols: 0, rows: 0, present: boxes.filter(b => b.present).length, free: true };
    const weak = boxes.filter(b => b.present && b.conf < 0.55).length;
    say('按真实轮廓找到 ' + boxes.length + ' 块（' + state.grid.present + ' 块有丝，每块大小位置各自独立）；圆孔 ' + holeN + ' 个、曲线缺口 ' + polyN + ' 个。' +
      (weak ? weak + ' 块把握不高（黄色虚线），可点「点预览框补块 / 去块」校对。' : '可叠加原图核对后再生成。'));
  }

  function analyse() {
    const im = state.img;
    if (!im) { say('先选一张图片。'); return; }
    const cols = Number(($('habRecCols') || {}).value || 0);
    const rows = Number(($('habRecRows') || {}).value || 0);
    state.thumb = null;
    if (cols > 0 || rows > 0) { state.map = null; legacyAnalyse(); return; }
    analyseAuto();
  }

  function apply(replace) {
    const H = S();
    if (!H) return;
    if (!state.boxes.length) { say('先点「识别并预览」。'); return; }
    const units0 = H.agents().filter(a => a.kind === 'weave');
    if (replace && window.__weaveHooks && window.__weaveHooks.deleteUnit) {
      units0.slice().forEach(u => window.__weaveHooks.deleteUnit(u.id));
    }
    let made = 0, holes = 0, polys = 0;
    state.boxes.filter(b => b.present).forEach((b, i) => {
      const before = H.agents().filter(a => a.kind === 'weave').length;
      H.addWeave({});
      const list = H.agents().filter(a => a.kind === 'weave');
      if (list.length <= before) return;
      const u = list[list.length - 1];
      // 不强行拉宽：参考图里本来就有窄条，硬拉到 80 会把版式改样
      u.w = Math.max(40, Math.round(b.w));
      u.h = Math.max(40, Math.round(b.h));
      u.x = Math.round(b.wx); u.y = Math.round(b.wy);
      u.tileField = false; u.shape = 'plain';
      u.seed = 1000 + i * 37;
      u.custom = u.custom || { walls: {}, paths: {}, shapes: {} };
      const sh = {};
      if (b.islands && b.islands.length) {
        sh.islands = b.islands.map(o => ({ cx: Math.round(o.cx), cy: Math.round(o.cy), r: Math.round(o.r) }));
        holes += sh.islands.length;
      }
      if (b.polys && b.polys.length) {
        // 多个暗区时保留面积最大的那条轮廓，其余仍按圆孔处理
        const poly = b.polys.slice().sort((p, q) => (q.area || 0) - (p.area || 0))[0];
        sh.notchPts = poly.pts.map(p => ({ x: Math.round(p.x * 10) / 10, y: Math.round(p.y * 10) / 10 }));
        polys++;
      }
      if (Object.keys(sh).length) u.custom.shapes['0,0'] = sh;
      if (u.cache && u.cache.clear) u.cache.clear();
      H.buildWeave(u);
      made++;
    });
    state.pick = false; ov.style.pointerEvents = 'none';
    const btn = $('habRecPick'); if (btn) btn.textContent = '点预览框补块 / 去块';
    say('已生成 ' + made + ' 块（每块尺寸与位置按图摆放），圆孔 ' + holes + ' 个、曲线缺口 ' + polys + ' 条。可直接拖锚点微调，Ctrl+Z 可撤销。');
  }

  REC().analyse = analyse;
  REC().apply = apply;
  REC().readDataURL = function (url, cb) {   // 供 QA / 以后"从链接读图"用
    const im = new Image();
    im.onload = () => {
      const k = Math.min(1, 1400 / Math.max(im.width, im.height));
      const w = Math.max(1, Math.round(im.width * k)), h = Math.max(1, Math.round(im.height * k));
      const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
      const cx = cv.getContext('2d'); cx.drawImage(im, 0, 0, w, h);
      const d = cx.getImageData(0, 0, w, h).data;
      const g = new Uint8Array(w * h);
      for (let i = 0, p = 0; i < g.length; i++, p += 4) g[i] = (d[p] * 0.299 + d[p + 1] * 0.587 + d[p + 2] * 0.114) | 0;
      state.img = { w, h, g }; state.thumb = null;
      cb && cb();
    };
    im.src = url;
  };
})();