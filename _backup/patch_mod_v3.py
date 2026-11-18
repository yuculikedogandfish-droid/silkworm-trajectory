import io
P = r"_backup\r37_module.js"
s = io.open(P, encoding="utf-8").read()

# 1) 新增 列数 / 排数 输入（HTML 在 index 里，这里是模块内读取）
s = s.replace("""  const state = { img: null, boxes: [], holes: [], grid: null };""",
"""  const state = { img: null, boxes: [], holes: [], grid: null, blur: null };""")

# 2) 用"整块外框 + 行列表"做近似切分，替代自相关找格距
old_start = s.index("  // 自相关找格距")
old_end = s.index("  function analyse()")
new_grid = '''  function blurImage(g, w, h, r) {
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

'''
s = s[:old_start] + new_grid + s[old_end:]

# 3) analyse 主体替换
a0 = s.index("  function analyse()")
a1 = s.index("  function apply(replace)")
new_analyse = '''  function analyse() {
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
    if (!cols) cols = Math.max(2, Math.round(bbW / (bbH / 8)));
    if (!rows) rows = Math.max(2, Math.round(bbH / (bbH / 8)));
    if (!rows) rows = 8;

    // 目标格边长 T：宽高按图里格子的实际比例，不强行拉成正方
    const T = Number(($('habRecCell') || {}).value || 320);
    const pxW = bbW / cols, pxH = bbH / rows;
    const scale = T / pxW;
    const bW = T, bH = pxH * scale;
    const gap = Math.max(2, Math.round(T * 0.02));       // 块与块之间留很细的缝（真实照片里也有）
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
            const rr = Math.sqrt(cnt / Math.PI);
            const isEdgeBite = maxX === W - 1 || minX === 0 || maxY === H2 - 1 || minY === 0;
            if (isEdgeBite && !wantNotch) continue;
            if (!isEdgeBite && !wantHoles) continue;
            b.islands.push({ cx: (ccx - W / 2) * scale, cy: (ccy - H2 / 2) * scale, r: Math.min(rr * scale, Math.min(bW, bH) * 0.62) });
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

'''
s = s[:a0] + new_analyse + s[a1:]
io.open(P, "w", encoding="utf-8").write(s)
print("module v3", len(s))
