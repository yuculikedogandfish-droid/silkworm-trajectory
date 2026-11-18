# -*- coding: utf-8 -*-
import io
p = r"H:\tool\silkworm-trajectory\_backup\r43_module.js"
s = io.open(p, encoding="utf-8").read()

old = """    // 闭运算：连丝成面，但不越过黑色分隔线
    const CR = (window.__rec43close != null ? window.__rec43close : 1);
    const closed = CR > 0 ? morph(morph(mask, w, h, CR, true), w, h, CR, false) : mask;
    const minArea = Math.max(500, Math.round(w * h * 0.0012));
    const comps = components(closed, w, h).filter(c => c.cnt >= minArea);
    if (!comps.length) { say('没找到成片的丝。换张对比更强的图，或把「丝多稀也算一块」往左调。'); return; }
"""
new = """    const comps = segment(im.g, bg, w, h, glob);
    if (!comps.length) { say('没找到成片的丝。换张对比更强的图，或把「丝多稀也算一块」往左调。'); return; }
"""
assert old in s
s = s.replace(old, new, 1)

seg = """
  /* ---------- 版式切分：黑色细分隔线 + 区域递归（块可不等大、可错位） ---------- */
  function segment(gray, bg, w, h, glob) {
    const sb = blur(gray, w, h, 1);
    const lineThr = Math.max(14, glob * 0.42);
    const dark = new Uint8Array(w * h);
    let dx0 = w, dx1 = 0, dy0 = h, dy1 = 0, bright = 0;
    for (let i = 0; i < dark.length; i++) {
      dark[i] = sb[i] < lineThr ? 1 : 0;
      if (sb[i] > glob) {
        bright++;
        const x = i % w, y = (i - x) / w;
        if (x < dx0) dx0 = x; if (x > dx1) dx1 = x; if (y < dy0) dy0 = y; if (y > dy1) dy1 = y;
      }
    }
    if (bright < w * h * 0.01) return [];
    // 允许 2px 断口的最长暗线长度
    function colRun(x, y0, y1) {
      let best = 0, cur = 0, gap = 0;
      for (let y = y0; y <= y1; y++) {
        if (dark[y * w + x]) { cur += gap + 1; gap = 0; if (cur > best) best = cur; }
        else { gap++; if (gap > 2) { cur = 0; gap = 0; } }
      }
      return best;
    }
    function rowRun(y, x0, x1) {
      let best = 0, cur = 0, gap = 0;
      for (let x = x0; x <= x1; x++) {
        if (dark[y * w + x]) { cur += gap + 1; gap = 0; if (cur > best) best = cur; }
        else { gap++; if (gap > 2) { cur = 0; gap = 0; } }
      }
      return best;
    }
    const MIN = 26;
    const out = [];
    function split(x0, x1, y0, y1, depth) {
      const W = x1 - x0 + 1, H2 = y1 - y0 + 1;
      if (W < MIN * 2 || H2 < MIN * 2 || depth > 14) { out.push({ minX: x0, maxX: x1, minY: y0, maxY: y1 }); return; }
      let bv = null, bh = null;
      for (let x = x0 + MIN; x <= x1 - MIN; x++) {
        const sc = colRun(x, y0, y1) / H2;
        if (sc < 0.55) continue;
        if (bv && sc <= bv.sc) continue;
        // 细线特征：左右 3px 外不能同样暗（否则是大片暗区/孔洞，不是分隔线）
        const side = Math.max(colRun(Math.max(x0, x - 3), y0, y1), colRun(Math.min(x1, x + 3), y0, y1)) / H2;
        if (side > sc * 0.72) continue;
        bv = { x, sc };
      }
      for (let y = y0 + MIN; y <= y1 - MIN; y++) {
        const sc = rowRun(y, x0, x1) / W;
        if (sc < 0.55) continue;
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
"""
anchor = "  /* ---------- 主流程：自由版式 ---------- */"
assert anchor in s
s = s.replace(anchor, seg + "\n" + anchor, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("segment ok")
