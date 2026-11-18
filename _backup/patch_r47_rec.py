# -*- coding: utf-8 -*-
import io
P = r"H:\tool\silkworm-trajectory\_backup\r43_module.js"
s = io.open(P, encoding="utf-8").read()
s = s.replace("/* ===== r43 识别升级：", "/* ===== r47 轮廓保真识别（基于 r43）：", 1)

old = """      octx.save();
      octx.strokeStyle = !b.present ? 'rgba(255,120,120,0.45)' : (weak ? 'rgba(240,200,90,0.95)' : 'rgba(121,203,182,0.95)');
      octx.lineWidth = weak ? 1.6 : 1.2;
      octx.setLineDash(b.present ? (weak ? [5, 3] : []) : [4, 4]);
      octx.strokeRect(x, y, w, h);
      if (b.present) { octx.fillStyle = 'rgba(121,203,182,0.05)'; octx.fillRect(x, y, w, h); }
      octx.restore();"""
new = """      octx.save();
      const col = !b.present ? 'rgba(255,120,120,0.45)' : (weak ? 'rgba(240,200,90,0.95)' : 'rgba(121,203,182,0.95)');
      // 外接矩形只作位置参考；真正的单元按丝面外轮廓画
      octx.strokeStyle = !b.present ? col : 'rgba(121,203,182,0.20)';
      octx.lineWidth = 0.8;
      octx.setLineDash([3, 4]);
      octx.strokeRect(x, y, w, h);
      octx.restore();
      octx.save();
      octx.strokeStyle = col;
      octx.lineWidth = weak ? 1.7 : 1.35;
      octx.setLineDash(b.present ? (weak ? [5, 3] : []) : [4, 4]);
      if (b.present && b.outline && b.outline.length >= 3) {
        drawPoly(b.outline.map(p => [v.px(b.wx + p.x), v.py(b.wy + p.y)]), true);
        octx.fillStyle = 'rgba(121,203,182,0.07)'; octx.fill(); octx.stroke();
      } else if (b.present) {
        octx.strokeRect(x, y, w, h);
        octx.fillStyle = 'rgba(121,203,182,0.05)'; octx.fillRect(x, y, w, h);
      }
      octx.restore();"""
assert old in s
s = s.replace(old, new, 1)

old = """  // 校对模式：点预览框 = 这块要 / 不要
  ov.addEventListener"""
new = """  function pointInPoly(pts, x, y) {
    let inside = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const a = pts[i], b = pts[j];
      if (((a.y > y) !== (b.y > y)) && x < (b.x - a.x) * (y - a.y) / ((b.y - a.y) || 1e-9) + a.x) inside = !inside;
    }
    return inside;
  }
  // 校对模式：点预览框 = 这块要 / 不要
  ov.addEventListener"""
assert old in s
s = s.replace(old, new, 1)
old = """    (state.boxes || []).forEach(b => {
      const d = Math.abs(wx - b.wx) / b.w + Math.abs(wy - b.wy) / b.h;
      if (Math.abs(wx - b.wx) <= b.w / 2 && Math.abs(wy - b.wy) <= b.h / 2 && d < bd) { bd = d; best = b; }
    });"""
new = """    (state.boxes || []).forEach(b => {
      const d = Math.abs(wx - b.wx) / b.w + Math.abs(wy - b.wy) / b.h;
      const inBox = Math.abs(wx - b.wx) <= b.w / 2 && Math.abs(wy - b.wy) <= b.h / 2;
      const hit = inBox && (!b.outline || pointInPoly(b.outline, wx - b.wx, wy - b.wy));
      if (hit && d < bd) { bd = d; best = b; }
    });"""
assert old in s
s = s.replace(old, new, 1)

# 外轮廓提取：最大亮丝连通区域 + Moore 外缘追踪 + RDP 保曲线
anchor = "  /* ---------- 主流程：自由版式 ---------- */"
helper = r"""  /* ---------- 丝面外轮廓：不是外接矩形 ---------- */
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

"""
assert anchor in s
s = s.replace(anchor, helper + anchor, 1)

old = """      boxes.push(b);
      if (!b.present || (!wantHoles && !wantNotch)) return;
      b.polys = [];

      // 格内暗区 → 圆孔 或 任意轮廓缺口"""
new = """      boxes.push(b);
      if (!b.present) return;

      // 先用稍糊的亮丝图取最大连通丝面，描它自己的外缘。
      // 与 mask（细丝覆盖率）分开：外缘要连成面，不能用一根根细丝直接描。
      const solid = new Uint8Array(W * H2);
      const outerThr = Math.max(16, glob * 0.34);
      for (let y = 0; y < H2; y++) for (let x = 0; x < W; x++) {
        solid[y * W + x] = bg[(y0 + y) * w + (x0 + x)] > outerThr ? 1 : 0;
      }
      // 只补 1px 小断口，不把大圆弧洞填掉
      const closed = morph(morph(solid, W, H2, 1, true), W, H2, 1, false);
      const outer = largestMask(closed, W, H2);
      if (outer && outer.pix.length >= Math.max(30, W * H2 * 0.035)) {
        let start = -1;
        for (let k = 0; k < outer.pix.length; k++) { const q = outer.pix[k]; if ((q % W) === outer.minX) { start = q; break; } }
        if (start >= 0) {
          const contour = trace(outer.mask, W, H2, start);
          let per = 0;
          for (let k = 0; k < contour.length; k++) { const p = contour[k], q = contour[(k + 1) % contour.length]; per += Math.hypot(q[0] - p[0], q[1] - p[1]); }
          let pts = rdp(contour, Math.max(0.85, per / 320));
          if (pts.length > 64) pts = rdp(contour, Math.max(1.15, per / 220));
          if (pts.length > 80) pts = rdp(contour, Math.max(1.5, per / 160));
          if (pts.length >= 3 && pts.length <= 80) {
            b.outline = pts.map(p => ({ x: (p[0] - W / 2) * scale, y: (p[1] - H2 / 2) * scale }));
            b.outlineArea = outer.pix.length / (W * H2);
          }
        }
      }
      if (!wantHoles && !wantNotch) return;
      b.polys = [];

      // 格内暗区 → 圆孔 或 任意轮廓缺口"""
assert old in s
s = s.replace(old, new, 1)

old = """        const touch = minX === 0 || minY === 0 || maxX === W - 1 || maxY === H2 - 1;
        if (touch && frac > 0.62) continue;"""
new = """        const touch = minX === 0 || minY === 0 || maxX === W - 1 || maxY === H2 - 1;
        // 外轮廓已经负责贴边的圆弧/咬口，不再重复写成格内缺口
        if (b.outline && touch) continue;
        if (touch && frac > 0.62) continue;"""
assert old in s
s = s.replace(old, new, 1)

old = """    say('按真实轮廓找到 ' + boxes.length + ' 块（' + state.grid.present + ' 块有丝，每块大小位置各自独立）；圆孔 ' + holeN + ' 个、曲线缺口 ' + polyN + ' 个。' +"""
new = """    const outlines = boxes.filter(b => b.present && b.outline).length;
    say('按真实轮廓找到 ' + boxes.length + ' 块（' + state.grid.present + ' 块有丝，' + outlines + ' 块已描出外轮廓）；圆孔 ' + holeN + ' 个、内部曲线缺口 ' + polyN + ' 个。' +"""
assert old in s
s = s.replace(old, new, 1)

old = """      u.tileField = false; u.shape = 'plain';
      u.seed = 1000 + i * 37;"""
new = """      u.tileField = false; u.shape = 'plain';
      u.outline = (b.outline && b.outline.length >= 3)
        ? b.outline.map(p => ({ x: Math.round(p.x * 10) / 10, y: Math.round(p.y * 10) / 10 }))
        : null;
      u.seed = 1000 + i * 37;"""
assert old in s
s = s.replace(old, new, 1)
s = s.replace("say('已生成 ' + made + ' 块（每块尺寸与位置按图摆放）", "say('已生成 ' + made + ' 块（尺寸、位置和外轮廓按图摆放）", 1)
io.open(P, "w", encoding="utf-8").write(s)
print("r47 module patched", len(s))
