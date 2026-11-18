
/* ===== r37 图片识别（独立模块：不改任何既有函数，只新增） ===== */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const ov = $('habRecOverlay');
  if (!ov) return;
  const octx = ov.getContext('2d');
  const S = () => window.__studioHabitat;
  const state = { img: null, boxes: [], holes: [], grid: null, blur: null };
  const box = $('habRecBox');
  if (box) box.style.marginTop = '14px';

  function say(t) { const el = $('habRecNote'); if (el) el.textContent = t; }
  function imgNote(t) { const el = $('habRecImageNote'); if (el) el.textContent = t; }

  function resizeOverlay() {
    const wrap = $('habWorldWrap');
    if (!wrap) return;
    const w = wrap.clientWidth, h = wrap.clientHeight;
    if (ov.width !== w || ov.height !== h) { ov.width = w; ov.height = h; }
    const world = $('habWorld');
    if (world) { ov.style.left = world.offsetLeft + 'px'; ov.style.top = world.offsetTop + 'px'; }
  }

  function drawOverlay() {
    const H = S();
    if (!H || !octx) return;
    resizeOverlay();
    octx.clearRect(0, 0, ov.width, ov.height);
    if (!state.boxes.length) return;
    const v = H.view();
    octx.save();
    state.boxes.forEach(b => {
      const x = v.px(b.wx - b.w / 2), y = v.py(b.wy - b.h / 2);
      const w = b.w * v.s, h = b.h * v.s;
      octx.strokeStyle = b.present ? 'rgba(121,203,182,0.95)' : 'rgba(255,120,120,0.45)';
      octx.lineWidth = 1.2;
      octx.setLineDash(b.present ? [] : [4, 4]);
      octx.strokeRect(x, y, w, h);
      if (b.present) {
        octx.fillStyle = 'rgba(121,203,182,0.05)';
        octx.fillRect(x, y, w, h);
      }
    });
    octx.setLineDash([]);
    state.holes.forEach(h => {
      const cx = v.px(h.wx), cy = v.py(h.wy), r = Math.max(1, h.wr * v.s);
      octx.beginPath();
      octx.arc(cx, cy, r, 0, Math.PI * 2);
      octx.strokeStyle = 'rgba(232,201,138,0.9)';
      octx.lineWidth = 1.1;
      octx.stroke();
    });
    octx.restore();
  }

  (function tick() { drawOverlay(); requestAnimationFrame(tick); })();

  function readImage(file, cb) {
    const fr = new FileReader();
    fr.onload = () => {
      const im = new Image();
      im.onload = () => {
        const k = Math.min(1, 1400 / Math.max(im.width, im.height));
        const w = Math.max(1, Math.round(im.width * k));
        const h = Math.max(1, Math.round(im.height * k));
        const cv = document.createElement('canvas');
        cv.width = w; cv.height = h;
        const cx = cv.getContext('2d');
        cx.drawImage(im, 0, 0, w, h);
        const d = cx.getImageData(0, 0, w, h).data;
        const g = new Uint8Array(w * h);
        for (let i = 0, p = 0; i < g.length; i++, p += 4) g[i] = (d[p] * 0.299 + d[p + 1] * 0.587 + d[p + 2] * 0.114) | 0;
        state.img = { w, h, g };
        cb && cb();
      };
      im.onerror = () => imgNote('这张图片读不出来，换一张 png / jpg 试试。');
      im.src = fr.result;
    };
    fr.onerror = () => imgNote('文件读取失败。');
    fr.readAsDataURL(file);
  }

  function otsu(g) {
    const hist = new Int32Array(256);
    for (let i = 0; i < g.length; i++) hist[g[i]]++;
    const total = g.length;
    let sum = 0;
    for (let t = 0; t < 256; t++) sum += t * hist[t];
    let sumB = 0, wB = 0, best = 0, thr = 128;
    for (let t = 0; t < 256; t++) {
      wB += hist[t];
      if (!wB) continue;
      const wF = total - wB;
      if (!wF) break;
      sumB += t * hist[t];
      const mB = sumB / wB, mF = (sum - sumB) / wF;
      const between = wB * wF * (mB - mF) * (mB - mF);
      if (between > best) { best = between; thr = t; }
    }
    return thr;
  }

  function blurImage(g, w, h, r) {
    const tmp = new Uint8ClampedArray(g.length), out = new Uint8ClampedArray(g.length);
    const win = 2 * r + 1;
    for (let y = 0; y < h; y++) {
      let acc = 0;
      const base = y * w;
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

  function boundsOf(mask, w, h) {
    let x0 = w, x1 = 0, y0 = h, y1 = 0, n = 0;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      if (mask[y * w + x]) { n++; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    }
    return n ? { x0, x1, y0, y1, n } : null;
  }

  function analyse() {
    const im = state.img;
    if (!im) { say('先选一张图片。'); return; }
    const { w, h, g } = im;
    // 先轻度模糊：把丝线糊成"面"，否则丝是散的、算不出块
    const bg = blurImage(g, w, h, 4);
    const thr = otsu(bg);
    const mask = new Uint8Array(w * h);
    for (let i = 0; i < mask.length; i++) mask[i] = bg[i] > thr ? 1 : 0;
    const bb = boundsOf(mask, w, h);
    if (!bb || bb.n < w * h * 0.02) { say('这张图里没找到成片的白丝。换一张对比更强的图，或手动铺块。'); return; }

    let cols = Number(($('habRecCols') || {}).value || 0);
    let rows = Number(($('habRecRows') || {}).value || 0);
    const bbW = bb.x1 - bb.x0 + 1, bbH = bb.y1 - bb.y0 + 1;
    const cellGuess = Math.max(bbW, bbH) / 8;   // 长边按 8 格估，短边随之
    if (!cols) cols = Math.max(2, Math.round(bbW / cellGuess));
    if (!rows) rows = Math.max(2, Math.round(bbH / cellGuess));

    // 目标格边长 T 只是"上限"；整组块必须能放进场地（默认留 820px 的框）
    const Tuser = Number(($('habRecCell') || {}).value || 320);
    const pxW = bbW / cols, pxH = bbH / rows;
    const fitMax = 820;
    const fitScale = Math.min(fitMax / (cols * pxW), fitMax / (rows * pxH));
    const scale = Math.min(fitScale, Tuser / pxW);
    const bW = pxW * scale, bH = pxH * scale;
    const gap = Math.max(2, Math.round(bW * 0.02));       // 块与块之间留很细的缝（真实照片里也有）
    const stepX = bW + gap, stepY = bH + gap;
    const midC = (cols - 1) / 2, midR = (rows - 1) / 2;

    const boxes = [], holes = [];
    const wantHoles = !!($('habRecHoles') || {}).checked;
    const wantNotch = !!($('habRecNotches') || {}).checked;
    let present = 0;

    for (let ri = 0; ri < rows; ri++) {
      for (let ci = 0; ci < cols; ci++) {
        const cx0 = bb.x0 + Math.round(ci * pxW), cx1 = bb.x0 + Math.round((ci + 1) * pxW);
        const cy0 = bb.y0 + Math.round(ri * pxH), cy1 = bb.y0 + Math.round((ri + 1) * pxH);
        let on = 0, tot = 0;
        for (let y = cy0; y < cy1; y += 2) for (let x = cx0; x < cx1; x += 2) { tot++; if (mask[y * w + x]) on++; }
        const cov = tot ? on / tot : 0;
        const isOn = cov > 0.34;
        if (isOn) present++;
        const wx = (ci - midC) * stepX, wy = (ri - midR) * stepY;
        const b = { present: isOn, wx, wy, w: bW, h: bH, ci, ri, cov, islands: [] };
        boxes.push(b);
        if (!isOn) continue;

        // 格内"暗块"：内部→圆孔；贴边→缺口（圆负空间，画的时候被格边裁成咬口）
        const W = cx1 - cx0, H2 = cy1 - cy0;
        const dm = new Uint8Array(W * H2);
        for (let y = 0; y < H2; y++) for (let x = 0; x < W; x++) dm[y * W + x] = mask[(cy0 + y) * w + (cx0 + x)] ? 0 : 1;
        const seen = new Uint8Array(W * H2);
        const stack = [];
        const cellArea = W * H2;
        for (let y = 0; y < H2 && b.islands.length < 4; y++) {
          for (let x = 0; x < W && b.islands.length < 4; x++) {
            const idx = y * W + x;
            if (!dm[idx] || seen[idx]) continue;
            let sx2 = 0, sy2 = 0, cnt = 0, minX = W, maxX = 0, minY = H2, maxY = 0;
            stack.length = 0; stack.push(idx); seen[idx] = 1;
            while (stack.length) {
              const q = stack.pop();
              const qx = q % W, qy = (q - qx) / W;
              cnt++; sx2 += qx; sy2 += qy;
              if (qx < minX) minX = qx;
              if (qx > maxX) maxX = qx;
              if (qy < minY) minY = qy;
              if (qy > maxY) maxY = qy;
              if (cnt > cellArea) { stack.length = 0; break; }
              if (qx > 0 && dm[q - 1] && !seen[q - 1]) { seen[q - 1] = 1; stack.push(q - 1); }
              if (qx < W - 1 && dm[q + 1] && !seen[q + 1]) { seen[q + 1] = 1; stack.push(q + 1); }
              if (qy > 0 && dm[q - W] && !seen[q - W]) { seen[q - W] = 1; stack.push(q - W); }
              if (qy < H2 - 1 && dm[q + W] && !seen[q + W]) { seen[q + W] = 1; stack.push(q + W); }
            }
            if (!cnt) continue;
            const frac = cnt / cellArea;
            if (frac < 0.06 || frac > 0.55) continue;
            const ccx = sx2 / cnt, ccy = sy2 / cnt;
            const bwc = maxX - minX + 1, bhc = maxY - minY + 1;
            const extent = cnt / (bwc * bhc);
            const aspect = bwc / Math.max(1, bhc);
            if (extent < 0.55 || aspect < 0.6 || aspect > 1.7) continue;
            const rpx = Math.min(bwc, bhc) / 2;
            const left = minX === 0, right = maxX === W - 1, top = minY === 0, bot = maxY === H2 - 1;
            const isEdgeBite = left || right || top || bot;
            if (isEdgeBite && !wantNotch) continue;
            if (!isEdgeBite && !wantHoles) continue;
            if (isEdgeBite) {
              if (extent < 0.45) continue;
              // 咬口：把圆心贴到它咬住的那条边上，半径取短边的一半，画出来才会贴着格边
              let cxp = ccx, cyp = ccy;
              if (left) cxp = rpx; else if (right) cxp = W - rpx;
              if (top) cyp = rpx; else if (bot) cyp = H2 - rpx;
              b.islands.push({
                cx: (cxp - W / 2) * scale,
                cy: (cyp - H2 / 2) * scale,
                r: Math.min(rpx * scale, Math.min(bW, bH) * 0.55)
              });
            } else {
              if (extent < 0.62 || aspect < 0.7 || aspect > 1.45) continue;
              b.islands.push({
                cx: (ccx - W / 2) * scale,
                cy: (ccy - H2 / 2) * scale,
                r: Math.min(Math.sqrt(cnt / Math.PI) * scale, Math.min(bW, bH) * 0.42)
              });
            }
          }
        }
        b.islands.forEach(is2 => holes.push({ wx: wx + is2.cx, wy: wy + is2.cy, wr: is2.r }));
      }
    }

    state.boxes = boxes;
    state.holes = holes;
    state.grid = { cols, rows, present, bbox: bb, bW, bH };
    say('按整块外框切成 ' + cols + ' 列 × ' + rows + ' 排：' + present + ' 块有丝、' + (boxes.length - present) +
      ' 个格位是空的；圆孔／咬口 ' + holes.length + ' 个。行列不满意就在上面改数字再点一次。');
  }

  function apply(replace) {
    const H = S();
    if (!H) return;
    if (!state.boxes.length) { say('先点「识别并预览」。'); return; }
    const units0 = H.agents().filter(a => a.kind === 'weave');
    if (replace && window.__weaveHooks && window.__weaveHooks.deleteUnit) {
      units0.slice().forEach(u => window.__weaveHooks.deleteUnit(u.id));
    }
    let made = 0;
    state.boxes.filter(b => b.present).forEach((b, i) => {
      const before = H.agents().filter(a => a.kind === 'weave').length;
      H.addWeave({});
      const list = H.agents().filter(a => a.kind === 'weave');
      if (list.length <= before) return;
      const u = list[list.length - 1];
      u.w = Math.max(80, Math.round(b.w));
      u.h = Math.max(80, Math.round(b.h));
      u.x = Math.round(b.wx);
      u.y = Math.round(b.wy);
      u.tileField = false;
      u.shape = 'plain';
      u.seed = 1000 + i * 37;
      if (b.islands.length) {
        u.custom = u.custom || { walls: {}, paths: {}, shapes: {} };
        if (!u.custom.shapes) u.custom.shapes = {};
        u.custom.shapes['0,0'] = { notch: null, islands: b.islands.map(o => ({ cx: Math.round(o.cx), cy: Math.round(o.cy), r: Math.round(o.r) })) };
      }
      if (u.cache && u.cache.clear) u.cache.clear();
      H.buildWeave(u);
      made++;
    });
    say('已经生成 ' + made + ' 块（位置与孔洞按识别结果铺好）。可以直接拖白点改形状；不满意按 Ctrl+Z，或删掉重来。');
  }

  const fileEl = $('habRecFile');
  if (fileEl) fileEl.addEventListener('change', () => {
    const f = fileEl.files && fileEl.files[0];
    if (!f) return;
    imgNote('读图中：' + f.name);
    readImage(f, () => imgNote('已载入 ' + state.img.w + '×' + state.img.h + '（缩放后）。点「识别并预览」。'));
  });
  const cellEl = $('habRecCell');
  if (cellEl) cellEl.addEventListener('input', () => { const el = $('habRecCellVal'); if (el) el.textContent = cellEl.value + 'px'; });
  const runEl = $('habRecRun');
  if (runEl) runEl.addEventListener('click', () => {
    if (!state.img) { say('先选一张图片。'); return; }
    try { analyse(); } catch (e) { say('识别出错：' + e.message); }
  });
  const clearEl = $('habRecClear');
  if (clearEl) clearEl.addEventListener('click', () => { state.boxes = []; state.holes = []; say('预览已清掉，场地没有任何改动。'); });
  const applyEl = $('habRecApply');
  if (applyEl) applyEl.addEventListener('click', () => { try { apply(false); } catch (e) { say('生成出错：' + e.message); } });
  const repEl = $('habRecReplace');
  if (repEl) repEl.addEventListener('click', () => {
    if (!confirm('会先删掉场地上现有的织网单元，再按识别结果铺满。确定？')) return;
    try { apply(true); } catch (e) { say('生成出错：' + e.message); }
  });
  window.__imgRec = { analyse, apply, state, readImage };
})();
