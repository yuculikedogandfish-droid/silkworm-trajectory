# -*- coding: utf-8 -*-
import io

MOD = r"H:\tool\silkworm-trajectory\_backup\r39_module.js"
P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(MOD, encoding="utf-8").read()

# ---------- 1) 缩略图改用真正的 drawWeave ----------
old_thumb = """      const sx = v.px(a.x - a.w / 2) * kx, sy = v.py(a.y - a.h / 2) * ky;
      const sw = a.w * v.s * kx, sh = a.h * v.s * ky;
      if (sw < 2 || sh < 2) return;
      try {
        ctx.fillStyle = '#05080a';
        ctx.fillRect(0, 0, cv.width, cv.height);
        ctx.drawImage(world, sx, sy, sw, sh, 0, 0, cv.width, cv.height);
        ctx.globalCompositeOperation = 'lighter';
        ctx.globalAlpha = 0.55;
        ctx.drawImage(world, sx, sy, sw, sh, 0, 0, cv.width, cv.height);
        ctx.globalAlpha = 1;
        ctx.globalCompositeOperation = 'source-over';
        ctx.strokeStyle = 'rgba(255,255,255,0.14)';
        ctx.strokeRect(0.5, 0.5, cv.width - 1, cv.height - 1);
      } catch (e) {}"""
new_thumb = """      ctx.fillStyle = '#05080a';
      ctx.fillRect(0, 0, cv.width, cv.height);
      // 首选：直接调用引擎的织块绘制，画一块"自己的样子"
      try {
        const k = Math.min(cv.width / a.w, cv.height / a.h) * 0.96;
        const tv = {
          s: k, cx: cv.width / 2 - a.x * k, cy: cv.height / 2 - a.y * k,
          px: (x) => cv.width / 2 + (x - a.x) * k,
          py: (y) => cv.height / 2 + (y - a.y) * k,
          w: cv.width, h: cv.height,
        };
        H().drawWeave(ctx, a, tv);
      } catch (e) {
        // 退路：从主画布抠
        const sx = v.px(a.x - a.w / 2) * kx, sy = v.py(a.y - a.h / 2) * ky;
        const sw = a.w * v.s * kx, sh = a.h * v.s * ky;
        try { if (sw > 2 && sh > 2) ctx.drawImage(world, sx, sy, sw, sh, 0, 0, cv.width, cv.height); } catch (e2) {}
      }
      ctx.strokeStyle = 'rgba(255,255,255,0.14)';
      ctx.strokeRect(0.5, 0.5, cv.width - 1, cv.height - 1);"""
assert s.count(old_thumb) == 1
s = s.replace(old_thumb, new_thumb)

# ---------- 2) 方向键/↑↓ 真正改画布压盖次序 ----------
old_shift = """  function shiftOrder(id, dir) {
    const list = agents().map(a => a.id);
    list.forEach(x => { if (store.order.indexOf(x) < 0) store.order.push(x); });
    const i = store.order.indexOf(id), j = i + dir;
    if (i >= 0 && j >= 0 && j < store.order.length) { const t2 = store.order[i]; store.order[i] = store.order[j]; store.order[j] = t2; save(); }
  }"""
new_shift = """  function shiftOrder(id, dir) {
    const list = agents().map(a => a.id);
    list.forEach(x => { if (store.order.indexOf(x) < 0) store.order.push(x); });
    const i = store.order.indexOf(id), j = i + dir;
    if (i >= 0 && j >= 0 && j < store.order.length) {
      const t2 = store.order[i]; store.order[i] = store.order[j]; store.order[j] = t2; save();
    }
    // 同时改真实绘制顺序：把这一层在 agents 数组里挪一格
    const arr = agents();
    const k = arr.findIndex(a => a.id === id);
    const k2 = k + dir;
    if (k >= 0 && k2 >= 0 && k2 < arr.length) {
      const item = arr.splice(k, 1)[0];
      arr.splice(k2, 0, item);
    }
  }"""
assert s.count(old_shift) == 1
s = s.replace(old_shift, new_shift)

# 让 ↑↓ 按钮分支也走新实现
s = s.replace("""      const i = store.order.indexOf(id), j = i + dir;
      if (i >= 0 && j >= 0 && j < store.order.length) { const t2 = store.order[i]; store.order[i] = store.order[j]; store.order[j] = t2; }
      save(); render(); return;
    }""", """      shiftOrder(id, dir);
      save(); sig = ''; render(); return;
    }""")

# ---------- 3) 等间距吸附 ----------
old_snap = """    return { dx: bestX ? bestX.d : 0, dy: bestY ? bestY.d : 0, gx: bestX ? bestX.at : null, gy: bestY ? bestY.at : null };"""
new_snap = """    // 没有边/中心命中时，试"与旁边两块保持同样的缝"
    if (!bestX) {
      const ws = agents().filter(a => a.kind === 'weave' && !skipIds.has(a.id));
      for (let i = 0; i < ws.length && !bestX; i++) {
        for (let j = 0; j < ws.length; j++) {
          const p = ws[i], q = ws[j];
          if (p === q) continue;
          const pr = p.x + p.w / 2, ql = q.x - q.w / 2;
          const gap = ql - pr;
          if (gap <= 4) continue;
          const l2 = q.x + q.w / 2 + gap;      // 放在 q 右边，缝一样
          const d2 = l2 - box.l;
          if (Math.abs(d2) <= thr) { bestX = { d: d2, at: null }; break; }
          const r2 = p.x - p.w / 2 - gap;     // 放在 p 左边，缝一样
          const d3 = r2 - box.r;
          if (Math.abs(d3) <= thr) { bestX = { d: d3, at: null }; break; }
        }
      }
    }
    if (!bestY) {
      const ws = agents().filter(a => a.kind === 'weave' && !skipIds.has(a.id));
      for (let i = 0; i < ws.length && !bestY; i++) {
        for (let j = 0; j < ws.length; j++) {
          const p = ws[i], q = ws[j];
          if (p === q) continue;
          const pb = p.y + p.h / 2, qt = q.y - q.h / 2;
          const gap = qt - pb;
          if (gap <= 4) continue;
          const t2 = q.y + q.h / 2 + gap;
          const d2 = t2 - box.t;
          if (Math.abs(d2) <= thr) { bestY = { d: d2, at: null }; break; }
          const b2 = p.y - p.h / 2 - gap;
          const d3 = b2 - box.b;
          if (Math.abs(d3) <= thr) { bestY = { d: d3, at: null }; break; }
        }
      }
    }
    return { dx: bestX ? bestX.d : 0, dy: bestY ? bestY.d : 0, gx: bestX && bestX.at != null ? bestX.at : null, gy: bestY && bestY.at != null ? bestY.at : null };"""
assert s.count(old_snap) == 1
s = s.replace(old_snap, new_snap)

# ---------- 4) 框选（marquee） ----------
marq = """
  /* ---------- 框选 ---------- */
  let marquee = null;   // {x0,y0,x1,y1,add}
  function marqueeSelect() {
    if (!marquee) return;
    const l = Math.min(marquee.x0, marquee.x1), r = Math.max(marquee.x0, marquee.x1);
    const t = Math.min(marquee.y0, marquee.y1), b = Math.max(marquee.y0, marquee.y1);
    if (!marquee.add) sel.clear();
    agents().forEach(a => {
      if (a.kind !== 'weave') return;
      const box = { l: a.x - a.w / 2, r: a.x + a.w / 2, t: a.y - a.h / 2, b: a.y + a.h / 2 };
      if (box.l < r && box.r > l && box.t < b && box.b > t) sel.add(a.id);
    });
    marquee = null;
    sig = ''; refresh(true);
  }
"""
anchor_marq = """  /* ---------- 键盘微调 ---------- */"""
assert s.count(anchor_marq) == 1
s = s.replace(anchor_marq, marq + anchor_marq)

# pointerdown：空地按下且非编辑态 → 记框选起点
s = s.replace("""      const p = toWorld(e);
      const hit = hitWeave(p);
      if (!hit) return;""", """      const p = toWorld(e);
      const hit = hitWeave(p);
      if (!hit) {
        if (!inEditMode()) marquee = { x0: p.x, y0: p.y, x1: p.x, y1: p.y, add: !!(e.shiftKey || e.ctrlKey || e.metaKey), armed: false };
        return;
      }
      marquee = null;""")

# pointermove：框选推进（优先级最高）
s = s.replace("""    window.addEventListener('pointermove', (e) => {
      if (own) {""", """    window.addEventListener('pointermove', (e) => {
      if (marquee) {
        const p = toWorld(e);
        marquee.x1 = p.x; marquee.y1 = p.y;
        const v = H().view();
        if (!marquee.armed && (Math.abs(p.x - marquee.x0) * v.s > 6 || Math.abs(p.y - marquee.y0) * v.s > 6)) marquee.armed = true;
        return;
      }
      if (own) {""")

# pointerup：结算框选
s = s.replace("""    window.addEventListener('pointerup', () => { pending = null; drag = null; own = null; guides = []; sig = ''; }, true);""",
"""    window.addEventListener('pointerup', () => {
      if (marquee && marquee.armed) marqueeSelect(); else marquee = null;
      pending = null; drag = null; own = null; guides = []; sig = '';
    }, true);""")

# 覆盖层画框选
s = s.replace("""    guides.forEach(g => {""", """    if (marquee && marquee.armed) {
      const x0 = v.px(Math.min(marquee.x0, marquee.x1)), y0 = v.py(Math.min(marquee.y0, marquee.y1));
      const x1 = v.px(Math.max(marquee.x0, marquee.x1)), y1 = v.py(Math.max(marquee.y0, marquee.y1));
      octx.save();
      octx.strokeStyle = 'rgba(121,203,182,0.9)';
      octx.fillStyle = 'rgba(121,203,182,0.10)';
      octx.lineWidth = 1;
      octx.setLineDash([4, 3]);
      octx.fillRect(x0, y0, x1 - x0, y1 - y0);
      octx.strokeRect(x0, y0, x1 - x0, y1 - y0);
      octx.restore();
    }
    guides.forEach(g => {""")

io.open(MOD, "w", encoding="utf-8").write(s)

h = io.open(P, encoding="utf-8").read()
i = h.find("/* ===== r39 个体与图层合并"); st = h.rfind("<script>", 0, i); en = h.find("</script>", i)
h = h[:st] + s.rstrip() + h[en + len("</script>"):]
io.open(P, "w", encoding="utf-8").write(h)
print("r41 ok", len(h))
