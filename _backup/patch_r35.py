# -*- coding: utf-8 -*-
"""r35：缺口/孔洞三个问题
1) 缺口曲线改成向心 Catmull-Rom（锚点挤在一起时不再鼓出自交的小三角/圈）
2) 右键「添加缺口」立刻在点击处放一个缺口（有东西），另配「重画缺口」自由画
3) 孔洞大小不再限 45%，可以拉到几乎占满整格
4) 点线插锚点：离已有锚点太近就不插（避免重复锚点把曲线搞乱）
"""
import io

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()


def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:90])
    s = s.replace(old, new)


# ---------- 1. 向心 Catmull-Rom ----------
rep("""  function weaveNotchCurve(pts) {
    if (!Array.isArray(pts) || pts.length < 3) return pts || [];
    return weaveSmooth(pts, true);
  }""",
"""  function weaveNotchCurve(pts) {
    if (!Array.isArray(pts) || pts.length < 3) return pts || [];
    // 向心 Catmull-Rom（alpha=0.5）：锚点疏密不均时不会鼓出自交的小圈/尖角
    const n = pts.length;
    const get = (i) => pts[((i % n) + n) % n];
    const alpha = 0.5;
    const lerp = (a, b, t) => ({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t });
    const out = [];
    const steps = 8;
    for (let i = 0; i < n; i++) {
      const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
      const d01 = Math.pow(Math.hypot(p1.x - p0.x, p1.y - p0.y), alpha) || 1e-4;
      const d12 = Math.pow(Math.hypot(p2.x - p1.x, p2.y - p1.y), alpha) || 1e-4;
      const d23 = Math.pow(Math.hypot(p3.x - p2.x, p3.y - p2.y), alpha) || 1e-4;
      const t0 = 0, t1 = t0 + d01, t2 = t1 + d12, t3 = t2 + d23;
      for (let s2 = 0; s2 < steps; s2++) {
        const tt = t1 + (t2 - t1) * (s2 / steps);
        const A1 = lerp(p0, p1, (tt - t0) / (t1 - t0));
        const A2 = lerp(p1, p2, (tt - t1) / (t2 - t1));
        const A3 = lerp(p2, p3, (tt - t2) / (t3 - t2));
        const B1 = lerp(A1, A2, (tt - t0) / (t2 - t0));
        const B2 = lerp(A2, A3, (tt - t1) / (t3 - t1));
        out.push(lerp(B1, B2, (tt - t1) / (t2 - t1)));
      }
    }
    return out;
  }""")

# ---------- 2. 点线插锚点：离已有锚点太近就不插 ----------
rep("""            if (bd <= 24 / view().s) {
              pushUndo();""",
"""            let near = Infinity;
            pts2.forEach(q => { near = Math.min(near, Math.hypot(p.x - (ox2 + q.x), p.y - (oy2 + q.y))); });
            if (bd <= 24 / view().s && near > 10 / view().s) {
              pushUndo();""")

# ---------- 3. 孔洞大小不再限 45% ----------
rep("""        isl.r = Math.max(12, Math.min(Math.min(a.w, a.h) * 0.45, Math.hypot(p.x - ox - isl.cx, p.y - oy - isl.cy)));""",
"""        // 孔洞大小不限：只保证不把整格吃干净（留 1% 边），要多大拉多大
        isl.r = Math.max(6, Math.min(Math.min(a.w, a.h) * 0.99, Math.hypot(p.x - ox - isl.cx, p.y - oy - isl.cy)));""")

# ---------- 4. 右键：添加缺口 = 立刻放一个；重画 = 自己围 ----------
rep("""      { label: '添加缺口（在格内点几下围一圈）', run: () => {
          pushUndo();
          const sh = ensureShapeOverride(a, e.ix, e.iy);
          delete sh.notchPts; delete sh.notch;
          if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
          weaveCellContent(a, e.ix, e.iy);
          setWeaveTool('notch');
          e.mode = 'notch'; e.drafts = {};
          syncEditNote();
          hint('在格内连点几下围出形状，双击收尾（至少 3 点）。');
        } },""",
"""      { label: '添加缺口（放在这一点）', run: () => {
          pushUndo();
          const sh = ensureShapeOverride(a, e.ix, e.iy);
          // 立刻给一个看得见的缺口，再让你拖点改形（不是"点了没反应"）
          const rr = Math.max(40, Math.min(a.w, a.h) * 0.2);
          const pts0 = [];
          for (let i = 0; i < 6; i++) {
            const ang = (Math.PI * 2 / 6) * i - Math.PI / 2;
            pts0.push({ x: lx + Math.cos(ang) * rr * 1.08, y: ly + Math.sin(ang) * rr });
          }
          sh.notchPts = pts0;
          if (sh.notch) delete sh.notch;
          if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
          weaveCellContent(a, e.ix, e.iy);
          setWeaveTool('notch');
          syncEditNote();
          toast('缺口已经放在你点的地方：拖白点改形状，点线上就加锚点，右键可删。', 'ok');
        } },
      { label: '重画缺口（点几下围一圈）', run: () => {
          pushUndo();
          const sh = ensureShapeOverride(a, e.ix, e.iy);
          delete sh.notchPts; delete sh.notch;
          if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
          weaveCellContent(a, e.ix, e.iy);
          setWeaveTool('notch');
          e.mode = 'notch'; e.drafts = {};
          syncEditNote();
          hint('在格内连点几下围出形状，双击收尾（至少 3 点）。');
        } },""")

# ---------- 5. 文案 ----------
rep("""    notch: '点几下围一圈＝缺口（画的时候就是光滑曲线）· 双击收尾 · 拖白点挪锚点 · 点在线上就地加锚点 · 拖边小方点也加锚点 · 右键＝菜单',""",
"""    notch: '拖白点改缺口形状 · 点在线上＝就地加锚点 · 右键＝删点/删整个缺口 · 想重新围一圈：右键菜单「重画缺口」',""")

io.open(P, "w", encoding="utf-8").write(s)
print("r35 patched")
