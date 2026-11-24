/* ===== r48 叠层与光滑轮廓识别：独立面板检测 + 直线/曲线分段拟合 + 圆孔双通道 ===== */
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
      const selected = state.selectedBox === b;
      octx.save();
      const col = selected ? 'rgba(255,210,90,1)' : (!b.present ? 'rgba(255,120,120,0.45)' : (weak ? 'rgba(240,200,90,0.95)' : 'rgba(121,203,182,0.95)'));
      // 外接矩形只作位置参考；真正的单元按丝面外轮廓画
      octx.strokeStyle = !b.present ? col : 'rgba(121,203,182,0.20)';
      octx.lineWidth = 0.8;
      octx.setLineDash([3, 4]);
      octx.strokeRect(x, y, w, h);
      octx.restore();
      octx.save();
      octx.strokeStyle = col;
      octx.lineWidth = selected ? 2.5 : (weak ? 1.7 : 1.35);
      octx.setLineDash(b.present ? (weak ? [5, 3] : []) : [4, 4]);
      if (b.present && b.outline && b.outline.length >= 3) {
        drawPoly(b.outline.map(p => [v.px(b.wx + p.x), v.py(b.wy + p.y)]), true);
        octx.fillStyle = 'rgba(121,203,182,0.07)'; octx.fill(); octx.stroke();
      } else if (b.present) {
        octx.strokeRect(x, y, w, h);
        octx.fillStyle = 'rgba(121,203,182,0.05)'; octx.fillRect(x, y, w, h);
      }
      octx.restore();
      if (b.present && ((b.layer || 1) > 1 || selected)) {
        octx.save();
        octx.fillStyle = 'rgba(232,201,138,0.96)';
        octx.font = '11px system-ui';
        octx.fillText('第 ' + b.layer + ' 层', x + 5, y + 15);
        octx.restore();
      }
      (b.polys || []).forEach(poly => {
        octx.save();
        octx.beginPath(); octx.rect(x, y, w, h); octx.clip();
        octx.strokeStyle = 'rgba(150,190,255,0.95)';
        octx.lineWidth = 1.2;
        octx.setLineDash([3, 3]);
        drawPoly(poly.pts.map(p => [v.px(b.wx + p.x), v.py(b.wy + p.y)]), true);
        octx.stroke();
        octx.restore();
      });
    });
    if (state.drag) {
      const d = state.drag;
      octx.save(); octx.strokeStyle = 'rgba(255,210,90,0.98)'; octx.lineWidth = 1.6; octx.setLineDash([6, 4]);
      octx.strokeRect(v.px(Math.min(d.x0, d.x1)), v.py(Math.min(d.y0, d.y1)), Math.abs(d.x1 - d.x0) * v.s, Math.abs(d.y1 - d.y0) * v.s);
      octx.restore();
    }
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

  function pointInPoly(pts, x, y) {
    let inside = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const a = pts[i], b = pts[j];
      if (((a.y > y) !== (b.y > y)) && x < (b.x - a.x) * (y - a.y) / ((b.y - a.y) || 1e-9) + a.x) inside = !inside;
    }
    return inside;
  }
  // 校对模式：点预览框 = 这块要 / 不要
  ov.addEventListener('pointerdown', (e) => {
    if (!state.pick && !state.layerMode && !state.rectMode) return;
    e.preventDefault(); e.stopPropagation();
    const H = S(); if (!H) return;
    const v = H.view();
    const r = ov.getBoundingClientRect();
    const wx = (e.clientX - r.left - v.cx) / v.s, wy = (e.clientY - r.top - v.cy) / v.s;
    if (state.rectMode) {
      state.drag = { x0: wx, y0: wy, x1: wx, y1: wy };
      ov.setPointerCapture && ov.setPointerCapture(e.pointerId);
      return;
    }
    let best = null, bd = Infinity;
    (state.boxes || []).forEach(b => {
      const d = Math.abs(wx - b.wx) / b.w + Math.abs(wy - b.wy) / b.h;
      const inBox = Math.abs(wx - b.wx) <= b.w / 2 && Math.abs(wy - b.wy) <= b.h / 2;
      const hit = inBox && (!b.outline || pointInPoly(b.outline, wx - b.wx, wy - b.wy));
      if (hit && (!best || (b.layer || 1) > (best.layer || 1) || ((b.layer || 1) === (best.layer || 1) && d < bd))) { bd = d; best = b; }
    });
    if (state.layerMode) {
      state.selectedBox = best || null;
      if (best) say('已选中第 ' + (best.layer || 1) + ' 层的块，可上移或下移。');
      return;
    }
    if (best) { best.present = !best.present; best.conf = 1; state.selectedBox = best; }
  });
  ov.addEventListener('pointermove', (e) => {
    if (!state.rectMode || !state.drag) return;
    const H = S(); if (!H) return;
    const v = H.view(), r = ov.getBoundingClientRect();
    state.drag.x1 = (e.clientX - r.left - v.cx) / v.s;
    state.drag.y1 = (e.clientY - r.top - v.cy) / v.s;
  });
  ov.addEventListener('pointerup', (e) => {
    if (!state.rectMode || !state.drag) return;
    const d = state.drag; state.drag = null;
    const x0 = Math.min(d.x0, d.x1), x1 = Math.max(d.x0, d.x1), y0 = Math.min(d.y0, d.y1), y1 = Math.max(d.y0, d.y1);
    if (x1 - x0 < 8 || y1 - y0 < 8) { say('框选太小，请拖出要补的单元范围。'); return; }
    let layer = 1;
    (state.boxes || []).forEach(b => {
      if (!b.present) return;
      const iw = Math.max(0, Math.min(x1, b.wx + b.w / 2) - Math.max(x0, b.wx - b.w / 2));
      const ih = Math.max(0, Math.min(y1, b.wy + b.h / 2) - Math.max(y0, b.wy - b.h / 2));
      if (iw * ih > 0.12 * Math.min((x1 - x0) * (y1 - y0), b.w * b.h)) layer = Math.max(layer, (b.layer || 1) + 1);
    });
    const w = x1 - x0, h = y1 - y0;
    const b = { present: true, conf: 1, wx: (x0 + x1) / 2, wy: (y0 + y1) / 2, w, h, layer, islands: [], polys: [], outline: [{ x: -w / 2, y: -h / 2 }, { x: w / 2, y: -h / 2 }, { x: w / 2, y: h / 2 }, { x: -w / 2, y: h / 2 }] };
    state.boxes.push(b); state.selectedBox = b;
    say('已补 1 块，第 ' + layer + ' 层。可继续框选，或点「点选调层」调整。');
  });
  const cols = document.querySelector('.hab-rec-cols');
  if (cols && !$('habRecCov')) {
    const div = document.createElement('div');
    div.innerHTML =
      '<div class="row"><label>丝多稀也算一块</label><input type="range" id="habRecCov" min="12" max="60" step="1" value="28" style="width:110px"><span class="hab-adj-val" id="habRecCovVal">28%</span></div>' +
      '<div class="row"><label>多小的洞才保留</label><input type="range" id="habRecMinHole" min="2" max="30" step="1" value="4" style="width:110px"><span class="hab-adj-val" id="habRecMinHoleVal">4%</span></div>' +
      '<div class="row"><label><input type="checkbox" id="habRecCompare" checked> 预览时叠上原图对比</label></div>' +
      '<div class="row"><button type="button" id="habRecPick">点预览框补块 / 去块</button></div>' +
      '<div class="row"><button type="button" id="habRecRect">框选补一块 / 叠层</button><button type="button" id="habRecSelect">点选调层</button></div>' +
      '<div class="row"><button type="button" id="habRecLayerDown">下移一层</button><button type="button" id="habRecLayerUp">上移一层</button></div>' +
      '<p class="hab-note" style="margin:2px 0 0">列 / 排填 0＝按真实轮廓自动找块（每块可大小不同）；填了数字＝按固定网格切。黄色虚线＝把握不高，点它可改。</p>';
    cols.appendChild(div);
    const cov = $('habRecCov'), mh = $('habRecMinHole');
    cov.addEventListener('input', () => { $('habRecCovVal').textContent = cov.value + '%'; });
    mh.addEventListener('input', () => { $('habRecMinHoleVal').textContent = mh.value + '%'; });
    $('habRecCompare').addEventListener('change', (e) => { state.compare = !!e.target.checked; });
    const mode = (name) => {
      state.pick = name === 'pick'; state.layerMode = name === 'layer'; state.rectMode = name === 'rect'; state.drag = null;
      ov.style.pointerEvents = name ? 'auto' : 'none'; ov.style.cursor = name ? 'crosshair' : 'default';
      $('habRecPick').textContent = state.pick ? '校对有块 / 无块中…（再点我退出）' : '点预览框补块 / 去块';
      $('habRecRect').textContent = state.rectMode ? '框选中…（再点我退出）' : '框选补一块 / 叠层';
      $('habRecSelect').textContent = state.layerMode ? '点选调层中…（再点我退出）' : '点选调层';
    };
    $('habRecPick').addEventListener('click', () => mode(state.pick ? '' : 'pick'));
    $('habRecRect').addEventListener('click', () => { mode(state.rectMode ? '' : 'rect'); if (state.rectMode) say('在原图上拖出一个矩形。与已有块相交时自动作为上一层；松手后即可继续调层或生成。'); });
    $('habRecSelect').addEventListener('click', () => { mode(state.layerMode ? '' : 'layer'); if (state.layerMode) say('点一个预览框选中，再用「上移一层 / 下移一层」。'); });
    $('habRecLayerUp').addEventListener('click', () => { const b = state.selectedBox; if (!b) { say('先点「点选调层」，再点一个预览框。'); return; } b.layer = Math.min(9, (b.layer || 1) + 1); say('选中块现为第 ' + b.layer + ' 层。'); });
    $('habRecLayerDown').addEventListener('click', () => { const b = state.selectedBox; if (!b) { say('先点「点选调层」，再点一个预览框。'); return; } b.layer = Math.max(1, (b.layer || 1) - 1); say('选中块现为第 ' + b.layer + ' 层。'); });
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
      const need = (W > 180 && H2 > 140) ? 0.18 : 0.32;
      const sideNeed = need < 0.20 ? 0.98 : 0.82;
      if (depth === 0) { window.__segDebug = { v: 0, h: 0, W, H: H2, lineThr }; }
      for (let x = x0 + MIN; x <= x1 - MIN; x++) {
        const sc = colRun(x, y0, y1) / H2;
        if (depth === 0 && sc > window.__segDebug.v) window.__segDebug.v = Math.round(sc * 100) / 100;
        if (sc < need) continue;
        if (bv && sc <= bv.sc) continue;
        // 细线特征：左右 3px 外不能同样暗（否则是大片暗区/孔洞，不是分隔线）
        const side = Math.max(colRun(Math.max(x0, x - 3), y0, y1), colRun(Math.min(x1, x + 3), y0, y1)) / H2;
        if (side > sc * sideNeed) continue;
        bv = { x, sc };
      }
      for (let y = y0 + MIN; y <= y1 - MIN; y++) {
        const sc = rowRun(y, x0, x1) / W;
        if (depth === 0 && sc > window.__segDebug.h) window.__segDebug.h = Math.round(sc * 100) / 100;
        if (sc < need) continue;
        if (bh && sc <= bh.sc) continue;
        const side = Math.max(rowRun(Math.max(y0, y - 3), x0, x1), rowRun(Math.min(y1, y + 3), x0, x1)) / W;
        if (side > sc * sideNeed) continue;
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

  /* ---------- 距离变换找圆：分隔线把洞与背景连住也能认 ---------- */
  function distanceCircles(dm, gray, W, H2, x0, y0, imgW, minFrac) {
    const N = W * H2, d = new Float32Array(N), INF = 1e6;
    for (let i = 0; i < N; i++) d[i] = dm[i] ? INF : 0;
    const relax = (i, v) => { if (v < d[i]) d[i] = v; };
    for (let y = 0; y < H2; y++) for (let x = 0; x < W; x++) {
      const i = y * W + x; if (!d[i]) continue;
      if (x === 0 || y === 0) d[i] = 1;
      if (x > 0) relax(i, d[i - 1] + 1);
      if (y > 0) relax(i, d[i - W] + 1);
      if (x > 0 && y > 0) relax(i, d[i - W - 1] + 1.4142);
      if (x < W - 1 && y > 0) relax(i, d[i - W + 1] + 1.4142);
    }
    for (let y = H2 - 1; y >= 0; y--) for (let x = W - 1; x >= 0; x--) {
      const i = y * W + x; if (!d[i]) continue;
      if (x === W - 1 || y === H2 - 1 && d[i] > 1) d[i] = 1;
      if (x < W - 1) relax(i, d[i + 1] + 1);
      if (y < H2 - 1) relax(i, d[i + W] + 1);
      if (x < W - 1 && y < H2 - 1) relax(i, d[i + W + 1] + 1.4142);
      if (x > 0 && y < H2 - 1) relax(i, d[i + W - 1] + 1.4142);
    }
    const minR = Math.max(20, Math.min(W, H2) * 0.24, Math.sqrt(minFrac * W * H2 / Math.PI) * 1.10);
    const cand = [];
    for (let y = 1; y < H2 - 1; y++) for (let x = 1; x < W - 1; x++) {
      const i = y * W + x, r = d[i];
      if (r < minR || r > Math.max(W, H2) * 0.72) continue;
      let peak = true;
      for (let dy = -2; dy <= 2 && peak; dy++) for (let dx = -2; dx <= 2; dx++) {
        const xx = x + dx, yy = y + dy;
        if (xx < 0 || yy < 0 || xx >= W || yy >= H2) continue;
        if (d[yy * W + xx] > r + 0.01) { peak = false; break; }
      }
      if (peak) cand.push({ x, y, r: r * 0.96 });
    }
    cand.sort((a, b) => b.r - a.r);
    const out = [];
    for (const c of cand) {
      if (out.some(o => Math.hypot(o.x - c.x, o.y - c.y) < Math.max(o.r, c.r) * 1.05)) continue;
      // 圆内暗、圆外亮；压边圆只统计仍在格内的采样点
      let inside = 0, outside = 0, ni = 0, no = 0;
      for (let k = 0; k < 24; k++) {
        const a = k * Math.PI * 2 / 24, ca = Math.cos(a), sa = Math.sin(a);
        const xi = Math.round(c.x + ca * c.r * 0.55), yi = Math.round(c.y + sa * c.r * 0.55);
        if (xi >= 0 && yi >= 0 && xi < W && yi < H2) { inside += gray[(y0 + yi) * imgW + x0 + xi]; ni++; }
        const xo = Math.round(c.x + ca * c.r * 1.22), yo = Math.round(c.y + sa * c.r * 1.22);
        if (xo >= 0 && yo >= 0 && xo < W && yo < H2) { outside += gray[(y0 + yo) * imgW + x0 + xo]; no++; }
      }
      if (ni < 10 || no < 7 || outside / no < inside / ni + 10) continue;
      c.full = no >= 21;
      out.push(c);
      if (out.length >= 2) break;
    }
    return out;
  }

  /* ---------- 丝面外轮廓：不是外接矩形 ---------- */
  function largestMask(src, W, H2) {
    const seen = new Uint8Array(W * H2), stack = [];
    let best = null;
    for (let i = 0; i < src.length; i++) {
      if (!src[i] || seen[i]) continue;
      let minX = W, maxX = 0, minY = H2, maxY = 0;
      const pix = [];
      stack.length = 0; stack.push(i); seen[i] = 1;
      while (stack.length) {
        const q = stack.pop(), x = q % W, y = (q - x) / W;
        pix.push(q);
        if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y;
        if (x > 0 && src[q - 1] && !seen[q - 1]) { seen[q - 1] = 1; stack.push(q - 1); }
        if (x < W - 1 && src[q + 1] && !seen[q + 1]) { seen[q + 1] = 1; stack.push(q + 1); }
        if (y > 0 && src[q - W] && !seen[q - W]) { seen[q - W] = 1; stack.push(q - W); }
        if (y < H2 - 1 && src[q + W] && !seen[q + W]) { seen[q + W] = 1; stack.push(q + W); }
      }
      if (!best || pix.length > best.pix.length) best = { pix, minX, maxX, minY, maxY };
    }
    if (!best) return null;
    const mask = new Uint8Array(W * H2);
    best.pix.forEach(q => { mask[q] = 1; });
    best.mask = mask;
    return best;
  }

  // 把像素边缘分成“确定直线”和“曲线段”。直线不再带像素抖动，
  // 曲线用连续三次曲线重新采样，不直接把毛刺交给 RDP。
  function smoothClosed(contour, W, H2, snapBox) {
    if (!contour || contour.length < 6) return contour || [];
    const ring = contour.slice();
    let per = 0;
    for (let i = 0; i < contour.length; i++) {
      const a = contour[i], b = contour[(i + 1) % contour.length];
      per += Math.hypot(b[0] - a[0], b[1] - a[1]);
    }
    let eps = Math.max(5.2, per / 72), coarse = rdp(ring, eps);
    if (coarse.length > 18) coarse = rdp(ring, Math.max(7.5, per / 40));
    if (coarse.length > 2 && coarse[0] === coarse[coarse.length - 1]) coarse.pop();
    else if (coarse.length > 2 && coarse[0][0] === coarse[coarse.length - 1][0] && coarse[0][1] === coarse[coarse.length - 1][1]) coarse.pop();
    const n = coarse.length;
    if (n < 3) return coarse;
    const ids = coarse.map(p => contour.indexOf(p));
    const pts = coarse.map(p => [p[0], p[1]]);
    const straight = new Array(n).fill(false);
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n, a = contour[ids[i]], b = contour[ids[j]];
      const ax = a[0], ay = a[1], bx = b[0], by = b[1], len = Math.hypot(bx - ax, by - ay) || 1;
      let md = 0, k = ids[i], guard = 0;
      while (k !== ids[j] && guard++ <= contour.length) {
        const p = contour[k];
        md = Math.max(md, Math.abs((bx - ax) * (ay - p[1]) - (ax - p[0]) * (by - ay)) / len);
        k = (k + 1) % contour.length;
      }
      straight[i] = md <= 2.35;
      if (snapBox) {
        const a0 = pts[i], b0 = pts[j], len2 = Math.hypot(b0[0] - a0[0], b0[1] - a0[1]);
        const near = (v, target) => Math.abs(v - target) <= 7;
        if (len2 > 18 && near(a0[0], 0) && near(b0[0], 0)) { straight[i] = true; a0[0] = b0[0] = 0; }
        if (len2 > 18 && near(a0[0], W - 1) && near(b0[0], W - 1)) { straight[i] = true; a0[0] = b0[0] = W - 1; }
        if (len2 > 18 && near(a0[1], 0) && near(b0[1], 0)) { straight[i] = true; a0[1] = b0[1] = 0; }
        if (len2 > 18 && near(a0[1], H2 - 1) && near(b0[1], H2 - 1)) { straight[i] = true; a0[1] = b0[1] = H2 - 1; }
        for (const q of [pts[i], pts[j]]) {
          if (q[0] <= 2.2) q[0] = 0; else if (q[0] >= W - 3.2) q[0] = W - 1;
          if (q[1] <= 2.2) q[1] = 0; else if (q[1] >= H2 - 3.2) q[1] = H2 - 1;
        }
      }
      if (straight[i]) {
        const dx = pts[j][0] - pts[i][0], dy = pts[j][1] - pts[i][1];
        if (Math.abs(dx) <= Math.max(1.2, Math.abs(dy) * 0.055)) { const x = (pts[i][0] + pts[j][0]) / 2; pts[i][0] = pts[j][0] = x; }
        if (Math.abs(dy) <= Math.max(1.2, Math.abs(dx) * 0.055)) { const y = (pts[i][1] + pts[j][1]) / 2; pts[i][1] = pts[j][1] = y; }
      }
    }
    const out = [];
    function emit(p) {
      const q = out[out.length - 1];
      if (!q || Math.hypot(q[0] - p[0], q[1] - p[1]) > 0.05) out.push(p);
    }
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n, a = pts[i], b = pts[j];
      if (straight[i]) { emit([a[0], a[1]]); continue; }
      const prev = pts[(i - 1 + n) % n], next = pts[(i + 2) % n];
      const steps = Math.max(6, Math.min(8, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / 12)));
      for (let k = 0; k < steps; k++) {
        const t = k / steps, t2 = t * t, t3 = t2 * t;
        const x = 0.5 * ((2 * a[0]) + (-prev[0] + b[0]) * t + (2 * prev[0] - 5 * a[0] + 4 * b[0] - next[0]) * t2 + (-prev[0] + 3 * a[0] - 3 * b[0] + next[0]) * t3);
        const y = 0.5 * ((2 * a[1]) + (-prev[1] + b[1]) * t + (2 * prev[1] - 5 * a[1] + 4 * b[1] - next[1]) * t2 + (-prev[1] + 3 * a[1] - 3 * b[1] + next[1]) * t3);
        emit(snapBox ? [Math.max(0, Math.min(W - 1, x)), Math.max(0, Math.min(H2 - 1, y))] : [x, y]);
      }
    }
    if (!window.__smoothDebug) window.__smoothDebug = { input: contour.length, coarse: n, output: out.length, ids: ids.slice(0, 30) };
    return out;
  }

  function fitArcCircle(contour, W, H2, touch) {
    const pp = contour.filter(p => {
      if (touch.minY === 0 && p[1] <= 2) return false;
      if (touch.maxY === H2 - 1 && p[1] >= H2 - 3) return false;
      if (touch.minX === 0 && p[0] <= 2) return false;
      if (touch.maxX === W - 1 && p[0] >= W - 3) return false;
      return true;
    }).filter((p, i) => i % 2 === 0);
    if (pp.length < 8) return null;
    let sx = 0, sy = 0, sxx = 0, sxy = 0, syy = 0, sxz = 0, syz = 0, sz = 0;
    pp.forEach(p => {
      const x = p[0], y = p[1], z = x * x + y * y;
      sx += x; sy += y; sxx += x * x; sxy += x * y; syy += y * y; sxz += x * z; syz += y * z; sz += z;
    });
    const n = pp.length, A = [[sxx, sxy, sx, -sxz], [sxy, syy, sy, -syz], [sx, sy, n, -sz]];
    for (let k = 0; k < 3; k++) {
      let pivot = k;
      for (let i = k + 1; i < 3; i++) if (Math.abs(A[i][k]) > Math.abs(A[pivot][k])) pivot = i;
      if (Math.abs(A[pivot][k]) < 1e-8) return null;
      [A[k], A[pivot]] = [A[pivot], A[k]];
      const d = A[k][k];
      for (let j = k; j < 4; j++) A[k][j] /= d;
      for (let i = 0; i < 3; i++) {
        if (i === k) continue;
        const f = A[i][k];
        for (let j = k; j < 4; j++) A[i][j] -= f * A[k][j];
      }
    }
    const D = A[0][3], E = A[1][3], F = A[2][3], cx = -D / 2, cy = -E / 2;
    const r2 = cx * cx + cy * cy - F;
    if (r2 <= 16) return null;
    const r = Math.sqrt(r2);
    if (r > Math.max(W, H2) * 2.2) return null;
    let err = 0;
    pp.forEach(p => { const d = Math.hypot(p[0] - cx, p[1] - cy) - r; err += d * d; });
    const rms = Math.sqrt(err / n) / r;
    if (rms > 0.60) return null;
    const out = [];
    for (let i = 0; i < 64; i++) { const a = i * Math.PI * 2 / 64; out.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); }
    return { pts: out, rms, cx, cy, r };
  }

  function fitArcCircleRefined(contour, W, H2, touch) {
    let pp = contour.filter((p, i) => {
      // 连续 30px 都贴一条直线的是格线，不是圆弧采样点。
      for (let s = Math.max(0, i - 25); s <= Math.min(i, contour.length - 26); s += 5) {
        const a = contour[s], b = contour[s + 25], dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy) || 1;
        let md = 0;
        for (let k = s + 1; k < s + 25; k++) md = Math.max(md, Math.abs(dx * (a[1] - contour[k][1]) - dy * (a[0] - contour[k][0])) / len);
        if (md < 0.58) return false;
      }
      return true;
    });
    if (pp.length < 10) pp = contour.slice();
    let fit = fitArcCircle(pp, W, H2, touch);
    const noTouch = { minX: -1, maxX: -1, minY: -1, maxY: -1 };
    for (let pass = 0; pass < 3 && fit && fit.rms > 0.10; pass++) {
      pp = pp.filter(p => Math.abs(Math.hypot(p[0] - fit.cx, p[1] - fit.cy) - fit.r) < Math.max(3, fit.r * 0.07));
      if (pp.length < 8) return null;
      fit = fitArcCircle(pp, W, H2, noTouch);
    }
    return fit && fit.rms <= 0.14 ? fit : null;
  }

  function arcFromBounds(W, H2, minX, maxX, minY, maxY, clean) {
    const top = minY === 0, bottom = maxY === H2 - 1, left = minX === 0, right = maxX === W - 1;
    if (top + bottom + left + right === 0 || top + bottom + left + right > 2 || (top && bottom) || (left && right)) return null;
    const bw = maxX - minX + 1, bh = maxY - minY + 1;
    let cx = (minX + maxX) / 2, cy = (minY + maxY) / 2, r;
    if (top || bottom) { cy = top ? 0 : H2 - 1; r = Math.max(bw / 2, bh); }
    if (left || right) { cx = left ? 0 : W - 1; r = Math.max(bh / 2, bw); }
    if ((top || bottom) && (left || right)) { cx = left ? 0 : W - 1; cy = top ? 0 : H2 - 1; r = (bw + bh) / 2; }
    if (!r || r > Math.max(W, H2) * 2.2) return null;
    let inter = 0, union = 0;
    for (let y = minY; y <= maxY; y++) for (let x = minX; x <= maxX; x++) {
      const pred = Math.hypot(x - cx, y - cy) <= r, actual = !!clean[y * W + x];
      if (pred && actual) inter++;
      if (pred || actual) union++;
    }
    if (!union || inter / union < 0.34) return null;
    const pts = [];
    for (let i = 0; i < 64; i++) { const a = i * Math.PI * 2 / 64; pts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); }
    return { pts, cx, cy, r, iou: inter / union };
  }

  function ellipseContour(contour) {
    const n = contour.length;
    if (n < 6) return contour;
    let mx = 0, my = 0;
    contour.forEach(p => { mx += p[0]; my += p[1]; });
    mx /= n; my /= n;
    let xx = 0, xy = 0, yy = 0;
    contour.forEach(p => { const x = p[0] - mx, y = p[1] - my; xx += x * x; xy += x * y; yy += y * y; });
    xx /= n; xy /= n; yy /= n;
    const tr = xx + yy, det = xx * yy - xy * xy;
    const disc = Math.sqrt(Math.max(0, tr * tr / 4 - det));
    const l1 = Math.max(1, tr / 2 + disc), l2 = Math.max(1, tr / 2 - disc);
    const ang = Math.atan2(l1 - xx, xy || 1e-9);
    const ca = Math.cos(ang), sa = Math.sin(ang), r1 = Math.sqrt(2 * l1) * 1.08, r2 = Math.sqrt(2 * l2) * 1.08;
    const out = [];
    for (let i = 0; i < 48; i++) {
      const a = i * Math.PI * 2 / 48, u = Math.cos(a) * r1, v = Math.sin(a) * r2;
      out.push([mx + u * ca - v * sa, my + u * sa + v * ca]);
    }
    return out;
  }

  /* ---------- r48：独立面板 / 叠层检测 ----------
     旧递归切分只能得到互不重叠的格子。这里直接为四条边计分，
     允许边界不同、位置相交的矩形同时存在；相近边界才按同一层去重。 */
  function detectPanels(gray, bg, w, h, glob, fallback) {
    const N = w * h, darkThr = Math.max(18, glob * 0.55), brightThr = Math.max(40, darkThr + 10);
    const vm = new Uint8Array(N), hm = new Uint8Array(N), bright = new Uint8Array(N);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const i = y * w + x, d = gray[i] < darkThr;
      bright[i] = bg[i] > Math.max(16, glob * 0.34) ? 1 : 0;
      if (!d) continue;
      const l = gray[y * w + Math.max(0, x - 3)], r = gray[y * w + Math.min(w - 1, x + 3)];
      const t = gray[Math.max(0, y - 3) * w + x], b = gray[Math.min(h - 1, y + 3) * w + x];
      if (l > brightThr || r > brightThr) vm[i] = 1;
      if (t > brightThr || b > brightThr) hm[i] = 1;
    }
    function peaks(vertical) {
      const A = vertical ? w : h, B = vertical ? h : w, counts = new Int32Array(A);
      for (let a = 0; a < A; a++) {
        let n = 0;
        for (let b = 0; b < B; b++) n += vertical ? vm[b * w + a] : hm[a * w + b];
        counts[a] = n;
      }
      const local = [];
      for (let a = 1; a < A - 1; a++) {
        const n = counts[a];
        if (n < 24) continue;
        let peak = true;
        for (let d = -2; d <= 2; d++) if (a + d >= 0 && a + d < A && counts[a + d] > n) { peak = false; break; }
        if (peak) local.push({ a, n });
      }
      local.sort((p, q) => q.n - p.n);
      const picked = [];
      for (const p of local) {
        if (picked.some(q => Math.abs(q.a - p.a) <= 5)) continue;
        picked.push(p);
        if (picked.length >= 52) break;
      }
      return picked.map(p => p.a).sort((a, b) => a - b);
    }
    const xs = peaks(true), ys = peaks(false);
    (fallback || []).forEach(f => {
      [f.minX, f.maxX].forEach(x => { if (!xs.some(v => Math.abs(v - x) <= 4)) xs.push(x); });
      [f.minY, f.maxY].forEach(y => { if (!ys.some(v => Math.abs(v - y) <= 4)) ys.push(y); });
    });
    xs.sort((a, b) => a - b); ys.sort((a, b) => a - b);
    function integral(src) {
      const it = new Float64Array((w + 1) * (h + 1));
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        it[(y + 1) * (w + 1) + x + 1] = src[y * w + x] + it[y * (w + 1) + x + 1] + it[(y + 1) * (w + 1) + x] - it[y * (w + 1) + x];
      }
      return it;
    }
    const vi = integral(vm), hi = integral(hm), bi = integral(bright);
    function sum(it, x0, y0, x1, y1) {
      x0 = Math.max(0, x0); y0 = Math.max(0, y0); x1 = Math.min(w - 1, x1); y1 = Math.min(h - 1, y1);
      if (x1 < x0 || y1 < y0) return 0;
      return it[(y1 + 1) * (w + 1) + x1 + 1] - it[y0 * (w + 1) + x1 + 1] - it[(y1 + 1) * (w + 1) + x0] + it[y0 * (w + 1) + x0];
    }
    const cand = [], maxW = Math.min(500, w * 0.62), maxH = Math.min(390, h * 0.62);
    const nearDuplicate = (a, b) => {
      const sameX = Math.abs(a.minX - b.minX) < 28 && Math.abs(a.maxX - b.maxX) < 28;
      const sameY = Math.abs(a.minY - b.minY) < 28 && Math.abs(a.maxY - b.maxY) < 28;
      const iy = Math.min(a.maxY, b.maxY) - Math.max(a.minY, b.minY);
      const ix = Math.min(a.maxX, b.maxX) - Math.max(a.minX, b.minX);
      return (sameX && iy > 0 && iy / Math.min(a.maxY - a.minY, b.maxY - b.minY) > 0.62) ||
        (sameY && ix > 0 && ix / Math.min(a.maxX - a.minX, b.maxX - b.minX) > 0.62);
    };
    for (let ai = 0; ai < xs.length; ai++) for (let bi2 = ai + 1; bi2 < xs.length; bi2++) {
      const x0 = xs[ai], x1 = xs[bi2], W = x1 - x0;
      if (W < 50 || W > maxW) continue;
      for (let ci = 0; ci < ys.length; ci++) for (let di = ci + 1; di < ys.length; di++) {
        const y0 = ys[ci], y1 = ys[di], H2 = y1 - y0;
        if (H2 < 50 || H2 > maxH || W / H2 > 3.5 || H2 / W > 3.5) continue;
        const lv = sum(vi, x0 - 1, y0, x0 + 1, y1) / (3 * (H2 + 1));
        const rv = sum(vi, x1 - 1, y0, x1 + 1, y1) / (3 * (H2 + 1));
        const th = sum(hi, x0, y0 - 1, x1, y0 + 1) / (3 * (W + 1));
        const bh = sum(hi, x0, y1 - 1, x1, y1 + 1) / (3 * (W + 1));
        const sides = [lv, rv, th, bh], strong = sides.filter(v => v >= 0.42).length;
        const mean = (lv + rv + th + bh) / 4, min = Math.min(lv, rv, th, bh);
        const sameBand = (fallback || []).some(f => Math.abs(f.minY - y0) <= 6 && Math.abs(f.maxY - y1) <= 6);
        const sameColumn = (fallback || []).some(f => Math.abs(f.minX - x0) <= 6 && Math.abs(f.maxX - x1) <= 6);
        const relaxed = y0 < 300 && (sameBand || sameColumn);
        if (min < (relaxed ? 0.06 : 0.14) || mean < (relaxed ? 0.32 : 0.45) || strong < (relaxed ? 2 : 3)) continue;
        const fill = sum(bi, x0 + 2, y0 + 2, x1 - 2, y1 - 2) / Math.max(1, (W - 3) * (H2 - 3));
        if (fill < 0.07) continue;
        let cross = 0;
        for (const xx of xs) {
          if (xx <= x0 + 18 || xx >= x1 - 18) continue;
          cross = Math.max(cross, sum(vi, xx - 1, y0, xx + 1, y1) / (3 * (H2 + 1)));
        }
        for (const yy of ys) {
          if (yy <= y0 + 18 || yy >= y1 - 18) continue;
          cross = Math.max(cross, sum(hi, x0, yy - 1, x1, yy + 1) / (3 * (W + 1)));
        }
        // 内部还有一条更完整分隔线时，这是把多个单元拼成的大框，不是叠层。
        if (cross > 0.70 && cross > mean * 1.05) continue;
        const score = mean * 0.62 + min * 0.23 + Math.min(1, fill * 2) * 0.15 - cross * 0.10;
        cand.push({ minX: x0, maxX: x1, minY: y0, maxY: y1, panelScore: score, detected: true, relaxed });
      }
    }
    cand.sort((a, b) => b.panelScore - a.panelScore);
    const kept = [];
    for (const c of cand) {
      if (c.panelScore < (c.relaxed ? 0.38 : 0.58)) continue;
      if (c.relaxed && (c.maxX - c.minX < 80 || c.maxY - c.minY < 70)) continue;
      if (kept.some(k => nearDuplicate(k, c) || (Math.abs(k.minX - c.minX) <= 6 && Math.abs(k.maxX - c.maxX) <= 6 && Math.abs(k.minY - c.minY) <= 6 && Math.abs(k.maxY - c.maxY) <= 6))) continue;
      kept.push(c);
      if (kept.length >= 96) break;
    }
    // 旧切分只补尚未覆盖的空白；已被独立面板覆盖的大框必须移除，避免假叠层。
    (fallback || []).forEach(f => {
      let covered = 0, total = 0;
      for (let gy = 1; gy <= 6; gy++) for (let gx = 1; gx <= 6; gx++) {
        const x = f.minX + (f.maxX - f.minX) * gx / 7, y = f.minY + (f.maxY - f.minY) * gy / 7;
        total++;
        if (kept.some(k => k.detected !== false && x >= k.minX && x <= k.maxX && y >= k.minY && y <= k.maxY)) covered++;
      }
      if (covered / total > 0.62) return;
      if (!kept.some(k => Math.abs(k.minX - f.minX) <= 5 && Math.abs(k.maxX - f.maxX) <= 5 && Math.abs(k.minY - f.minY) <= 5 && Math.abs(k.maxY - f.maxY) <= 5)) {
        kept.push(Object.assign({ panelScore: 0.38, detected: false }, f));
      }
    });
    kept.sort((a, b) => ((b.maxX - b.minX) * (b.maxY - b.minY)) - ((a.maxX - a.minX) * (a.maxY - a.minY)) || a.minY - b.minY || a.minX - b.minX);
    const overlap = (a, b) => {
      const iw = Math.min(a.maxX, b.maxX) - Math.max(a.minX, b.minX), ih = Math.min(a.maxY, b.maxY) - Math.max(a.minY, b.minY);
      if (iw <= 4 || ih <= 4) return 0;
      return iw * ih / Math.max(1, Math.min((a.maxX - a.minX) * (a.maxY - a.minY), (b.maxX - b.minX) * (b.maxY - b.minY)));
    };
    kept.forEach(c => {
      if (c.detected === false) { c.layer = 1; return; }
      c.layer = 1;
      for (const p of kept) {
        if (p === c) break;
        if (p.detected === false) continue;
        if (overlap(p, c) > 0.25) c.layer = Math.min(3, Math.max(c.layer, (p.layer || 1) + 1));
      }
    });
    kept.sort((a, b) => a.layer - b.layer || a.minY - b.minY || a.minX - b.minX);
    window.__panelsDebug = { xs: xs.length, ys: ys.length, candidates: cand.length, kept: kept.length, layers: Math.max(1, ...kept.map(c => c.layer || 1)), upper: cand.filter(c => c.minY < 300).slice(0, 30).map(c => [c.minX, c.maxX, c.minY, c.maxY, Math.round(c.panelScore * 100) / 100]), topRow: cand.filter(c => c.minY < 400).slice(0, 30).map(c => [c.minX, c.maxX, c.minY, c.maxY, Math.round(c.panelScore * 100) / 100]), top: cand.slice(0, 18).map(c => [c.minX, c.maxX, c.minY, c.maxY, Math.round(c.panelScore * 100) / 100]) };
    return kept;
  }

  function contourArcCandidate(gray, W, H2, thr, minFrac) {
    const N = W * H2, dm = new Uint8Array(N);
    for (let i = 0; i < N; i++) dm[i] = gray[i] < thr ? 1 : 0;
    const clean = morph(morph(dm, W, H2, 1, false), W, H2, 1, true);
    const seen = new Uint8Array(N), stack = [], noTouch = { minX: -1, maxX: -1, minY: -1, maxY: -1 };
    const minR = Math.max(14, Math.sqrt(minFrac * N / Math.PI) * 0.90);
    let best = null;
    for (let i = 0; i < N; i++) {
      if (!clean[i] || seen[i]) continue;
      const pix = [], mask = new Uint8Array(N);
      let minX = W, maxX = 0, minY = H2, maxY = 0;
      seen[i] = 1; stack.push(i); mask[i] = 1;
      while (stack.length) {
        const q = stack.pop(), x = q % W, y = (q - x) / W;
        pix.push(q); minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y);
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          if (!dx && !dy) continue;
          const xx = x + dx, yy = y + dy;
          if (xx < 0 || yy < 0 || xx >= W || yy >= H2) continue;
          const z = yy * W + xx;
          if (clean[z] && !seen[z]) { seen[z] = 1; mask[z] = 1; stack.push(z); }
        }
      }
      if (pix.length < 70) continue;
      let start = -1;
      for (const q of pix) if (q % W === minX) { start = q; break; }
      if (start < 0) continue;
      const contour = trace(mask, W, H2, start);
      if (contour.length < 28) continue;
      for (let s = 0; s < contour.length - 24; s += 10) {
        for (let len = 30; len <= Math.min(150, contour.length - s); len += 10) {
          const part = contour.slice(s, s + len);
          const fit = fitArcCircle(part, W, H2, noTouch);
          if (!fit || fit.rms > 0.065 || fit.r < minR || fit.r > Math.max(W, H2) * 2.1 || len / fit.r < 0.85) continue;
          let valid = 0, con = 0, near = 0;
          for (let k = 0; k < 48; k++) {
            const a = k * Math.PI * 2 / 48, ca = Math.cos(a), sa = Math.sin(a);
            const x = Math.round(fit.cx + ca * fit.r), y = Math.round(fit.cy + sa * fit.r);
            if (x < 1 || y < 1 || x >= W - 1 || y >= H2 - 1) continue;
            valid++;
            const xi = Math.round(fit.cx + ca * fit.r * 0.68), yi = Math.round(fit.cy + sa * fit.r * 0.68);
            const xo = Math.round(fit.cx + ca * fit.r * 1.24), yo = Math.round(fit.cy + sa * fit.r * 1.24);
            if (xi >= 0 && yi >= 0 && xo >= 0 && yo >= 0 && xi < W && xo < W && yi < H2 && yo < H2 && gray[yi * W + xi] < thr + 4 && gray[yo * W + xo] > gray[yi * W + xi] + 6) con++;
          }
          if (valid < 10 || con / valid < 0.60) continue;
          contour.forEach(p => { if (Math.abs(Math.hypot(p[0] - fit.cx, p[1] - fit.cy) - fit.r) < Math.max(3, fit.r * 0.05)) near++; });
          const full = valid >= 44 && fit.cx - fit.r >= -2 && fit.cy - fit.r >= -2 && fit.cx + fit.r <= W + 1 && fit.cy + fit.r <= H2 + 1;
          const score = len + con / valid * 36 + (full ? 30 : 0);
          if (!best || score > best.score) best = { cx: fit.cx, cy: fit.cy, r: fit.r, full, score, support: len / contour.length, con: con / valid, rms: fit.rms };
        }
      }
    }
    return best ? [best] : [];
  }

  function ransacCircles(gray, W, H2, thr, minFrac) {
    const N = W * H2, dark = new Uint8Array(N), edge = new Uint8Array(N), near = new Uint8Array(N), pts = [];
    for (let i = 0; i < N; i++) dark[i] = gray[i] < thr ? 1 : 0;
    for (let y = 1; y < H2 - 1; y++) for (let x = 1; x < W - 1; x++) {
      const i = y * W + x;
      if (dark[i] && (!dark[i - 1] || !dark[i + 1] || !dark[i - W] || !dark[i + W])) { edge[i] = 1; pts.push([x, y]); }
    }
    for (let y = 0; y < H2; y++) for (let x = 0; x < W; x++) {
      let hit = 0;
      for (let dy = -2; dy <= 2 && !hit; dy++) for (let dx = -2; dx <= 2; dx++) {
        const xx = x + dx, yy = y + dy;
        if (xx >= 0 && yy >= 0 && xx < W && yy < H2 && edge[yy * W + xx]) { hit = 1; break; }
      }
      near[y * W + x] = hit;
    }
    if (pts.length < 12) return [];
    let seed = 1234567;
    const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
    const minR = Math.max(14, Math.min(W, H2) * 0.14, Math.sqrt(minFrac * W * H2 / Math.PI) * 0.95);
    const found = [], iterations = 3000;
    for (let it = 0; it < iterations; it++) {
      const a = pts[(rnd() * pts.length) | 0], b = pts[(rnd() * pts.length) | 0], c = pts[(rnd() * pts.length) | 0];
      const d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]));
      if (Math.abs(d) < 2) continue;
      const aa = a[0] * a[0] + a[1] * a[1], bb = b[0] * b[0] + b[1] * b[1], cc = c[0] * c[0] + c[1] * c[1];
      const cx = (aa * (b[1] - c[1]) + bb * (c[1] - a[1]) + cc * (a[1] - b[1])) / d;
      const cy = (aa * (c[0] - b[0]) + bb * (a[0] - c[0]) + cc * (b[0] - a[0])) / d;
      const r = Math.hypot(a[0] - cx, a[1] - cy);
      if (r < minR || r > Math.max(W, H2) * 2.1 || cx < -r * 1.2 || cy < -r * 1.2 || cx > W + r * 1.2 || cy > H2 + r * 1.2) continue;
      let valid = 0, hit = 0, contrast = 0, checks = 0;
      for (let k = 0; k < 72; k++) {
        const ang = k * Math.PI * 2 / 72, ca = Math.cos(ang), sa = Math.sin(ang);
        const x = Math.round(cx + ca * r), y = Math.round(cy + sa * r);
        if (x < 1 || y < 1 || x >= W - 1 || y >= H2 - 1) continue;
        valid++;
        if (near[y * W + x]) hit++;
        const xi = Math.round(cx + ca * r * 0.68), yi = Math.round(cy + sa * r * 0.68);
        const xo = Math.round(cx + ca * r * 1.24), yo = Math.round(cy + sa * r * 1.24);
        if (xi >= 0 && yi >= 0 && xo >= 0 && yo >= 0 && xi < W && xo < W && yi < H2 && yo < H2) {
          checks++;
          if (gray[yi * W + xi] < thr + 4 && gray[yo * W + xo] > gray[yi * W + xi] + 6) contrast++;
        }
      }
      if (valid < 12 || checks < 8) continue;
      const support = hit / valid, con = contrast / checks;
      if (support < 0.58 || con < 0.55) continue;
      const full = valid >= 68 && cx - r >= -2 && cy - r >= -2 && cx + r <= W + 1 && cy + r <= H2 + 1;
      const score = support * 0.67 + con * 0.33 + Math.min(0.08, valid / 72 * 0.08);
      if (found.some(o => Math.hypot(o.cx - cx, o.cy - cy) < Math.max(o.r, r) * 0.45 && Math.abs(o.r - r) < Math.max(o.r, r) * 0.35)) {
        const o = found.find(o => Math.hypot(o.cx - cx, o.cy - cy) < Math.max(o.r, r) * 0.45 && Math.abs(o.r - r) < Math.max(o.r, r) * 0.35);
        if (score > o.score) Object.assign(o, { cx, cy, r, full, score, support, con });
      } else {
        found.push({ cx, cy, r, full, score, support, con });
        found.sort((p, q) => q.score - p.score);
        if (found.length > 8) found.pop();
      }
    }
    const out = [];
    for (const c of found) {
      if (out.some(o => Math.hypot(o.cx - c.cx, o.cy - c.cy) < Math.max(o.r, c.r) * 0.70)) continue;
      out.push(c);
      if (out.length >= 1) break;
    }
    return out;
  }

  function modelOutline(b, W, H2, scale) {
    const rect = [[0, 0], [W - 1, 0], [W - 1, H2 - 1], [0, H2 - 1]];
    const shapes = [];
    (b.islands || []).forEach(o => shapes.push({ kind: 'circle', cx: o.cx / scale + W / 2, cy: o.cy / scale + H2 / 2, r: o.r / scale }));
    (b.polys || []).forEach(p => shapes.push({ kind: 'poly', pts: p.pts.map(q => [q.x / scale + W / 2, q.y / scale + H2 / 2]) }));
    if (!shapes.length) return rect;
    const mask = new Uint8Array(W * H2); mask.fill(1);
    for (const sh of shapes) {
      if (sh.kind === 'circle') {
        const x0 = Math.max(0, Math.floor(sh.cx - sh.r - 1)), x1 = Math.min(W - 1, Math.ceil(sh.cx + sh.r + 1));
        const y0 = Math.max(0, Math.floor(sh.cy - sh.r - 1)), y1 = Math.min(H2 - 1, Math.ceil(sh.cy + sh.r + 1));
        for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (Math.hypot(x - sh.cx, y - sh.cy) <= sh.r) mask[y * W + x] = 0;
      } else {
        const pp = sh.pts;
        for (let y = 0; y < H2; y++) for (let x = 0; x < W; x++) {
          let inside = false;
          for (let i = 0, j = pp.length - 1; i < pp.length; j = i++) {
            const a = pp[i], b2 = pp[j];
            if (((a[1] > y) !== (b2[1] > y)) && x < (b2[0] - a[0]) * (y - a[1]) / ((b2[1] - a[1]) || 1e-9) + a[0]) inside = !inside;
          }
          if (inside) mask[y * W + x] = 0;
        }
      }
    }
    const outer = largestMask(mask, W, H2);
    if (!outer || outer.pix.length < W * H2 * 0.08) return rect;
    let start = -1;
    for (const q of outer.pix) if ((q % W) === outer.minX) { start = q; break; }
    if (start < 0) return rect;
    const pts = smoothClosed(trace(outer.mask, W, H2, start), W, H2, true);
    return pts.length >= 3 && pts.length <= 240 ? pts : rect;
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
        const thr = Math.max(glob * 0.30, mean * 0.94);
        mask[y * w + x] = bg[y * w + x] > thr ? 1 : 0;
      }
    }
    const baseComps = segment(im.g, bg, w, h, glob);
    const comps = window.__recBaseOnly ? baseComps : detectPanels(im.g, bg, w, h, glob, baseComps);
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
        cov, ci: idx, ri: 0, islands: [], polys: [], layer: c.layer || 1, panelScore: c.panelScore || 0,
      };
      boxes.push(b);
      if (!b.present) return;

      if (!wantHoles && !wantNotch) {
        b.outline = modelOutline(b, W, H2, scale).map(p => ({ x: (p[0] - W / 2) * scale, y: (p[1] - H2 / 2) * scale }));
        return;
      }
      b.polys = [];

      // 格内暗区 → 圆孔 或 任意轮廓缺口
      // 孔洞用"糊过的灰度"判定：丝线本身的细缝不会被当成洞
      const holeThr = Math.max(18, glob * 0.55);
      const dm = new Uint8Array(W * H2), localGray = new Float32Array(W * H2);
      for (let y = 0; y < H2; y++) for (let x = 0; x < W; x++) localGray[y * W + x] = bg[(y0 + y) * w + (x0 + x)];
      // 每块单独分阈值：参考图里有些圆是纯黑，有些盖着灰雾，不能用同一条黑线。
      const localThr = Math.min(120, Math.max(holeThr, otsu(localGray) * 0.90));
      for (let i = 0; i < dm.length; i++) dm[i] = localGray[i] < localThr ? 1 : 0;
      const chain = contourArcCandidate(localGray, W, H2, localThr, minHoleFrac);
      const vote = ransacCircles(localGray, W, H2, localThr, minHoleFrac);
      chain.forEach(c => { c.quality = c.con * 0.45 + Math.min(1, c.support * 2) * 0.25 + Math.min(1, c.r / 100) * 0.20 - c.rms; });
      vote.forEach(c => { c.quality = c.support * 0.50 + c.con * 0.35 + Math.min(1, c.r / 100) * 0.15; });
      const rc = chain.concat(vote).filter(c => {
        if (c.quality < 0.88 || c.con < 0.72) return false;
        if (c.full) return true;
        const top = c.cy - c.r <= 0, bottom = c.cy + c.r >= H2, left = c.cx - c.r <= 0, right = c.cx + c.r >= W;
        const sides = top + bottom + left + right;
        if (sides > 2 || (top && bottom) || (left && right)) return false;
        const centerInside = c.cx >= 0 && c.cx <= W && c.cy >= 0 && c.cy <= H2;
        const centerNearEdge = Math.min(Math.abs(c.cx), Math.abs(c.cx - W), Math.abs(c.cy), Math.abs(c.cy - H2)) <= c.r * 0.35;
        return !centerInside || centerNearEdge;
      }).sort((a, b) => b.quality - a.quality).slice(0, 1);
      if (!window.__rcDebug) window.__rcDebug = [];
      window.__rcDebug.push({ idx, W, H2, thr: localThr, rc });
      b.islands = [];
      b.polys = [];
      rc.forEach(c => {
        const pts = [];
        for (let k = 0; k < 64; k++) {
          const ang = k * Math.PI * 2 / 64;
          pts.push({ x: (c.cx + Math.cos(ang) * c.r - W / 2) * scale, y: (c.cy + Math.sin(ang) * c.r - H2 / 2) * scale });
        }
        if (c.full) {
          if (!wantHoles) return;
          const isl = { cx: (c.cx - W / 2) * scale, cy: (c.cy - H2 / 2) * scale, r: c.r * scale };
          b.islands.push(isl);
          holes.push({ wx: b.wx + isl.cx, wy: b.wy + isl.cy, wr: isl.r });
          holeN++;
        } else if (wantNotch) {
          b.polys.push({ pts, area: Math.PI * c.r * c.r });
        }
      });
      b.outline = modelOutline(b, W, H2, scale).map(p => ({ x: (p[0] - W / 2) * scale, y: (p[1] - H2 / 2) * scale }));
    });

    boxes.forEach(b => {
      if (b.polys && b.polys.length > 2) b.polys = b.polys.sort((p, q) => q.area - p.area).slice(0, 2);
      polyN += (b.polys || []).length;
    });
    state.boxes = boxes;
    state.holes = holes;
    state.grid = { cols: 0, rows: 0, present: boxes.filter(b => b.present).length, free: true };
    const weak = boxes.filter(b => b.present && b.conf < 0.55).length;
    const outlines = boxes.filter(b => b.present && b.outline).length;
    const stacked = boxes.filter(b => b.present && (b.layer || 1) > 1).length;
    say('找到 ' + boxes.filter(b => b.present).length + ' 块独立丝面（' + outlines + ' 块光滑外轮廓，叠放上层 ' + stacked + ' 块）；圆孔 ' + holeN + ' 个、曲线缺口 ' + polyN + ' 个。低可信形状不硬猜；请叠加原图，用「框选补块 / 点选调层」校对后再生成。');
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
      u.w = Math.max(12, Math.round(b.w));
      u.h = Math.max(12, Math.round(b.h));
      u.x = Math.round(b.wx); u.y = Math.round(b.wy);
      u.tileField = false; u.shape = 'plain';
      u.outline = (b.outline && b.outline.length >= 3)
        ? b.outline.map(p => ({ x: Math.round(p.x * 10) / 10, y: Math.round(p.y * 10) / 10 }))
        : null;
      u.seed = 1000 + i * 37;
      u.recLayer = b.layer || 1;
      u.strata = Math.max(1, Math.min(3, b.layer || 1));
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
    state.pick = false; state.rectMode = false; state.layerMode = false; state.drag = null; ov.style.pointerEvents = 'none';
    const btn = $('habRecPick'); if (btn) btn.textContent = '点预览框补块 / 去块';
    const br = $('habRecRect'); if (br) br.textContent = '框选补一块 / 叠层';
    const bs = $('habRecSelect'); if (bs) bs.textContent = '点选调层';
    say('已生成 ' + made + ' 块（尺寸、位置和外轮廓按图摆放），圆孔 ' + holes + ' 个、曲线缺口 ' + polys + ' 条。可直接拖锚点微调，Ctrl+Z 可撤销。');
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
