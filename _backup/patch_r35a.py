# -*- coding: utf-8 -*-
"""r35 a: 向心 Catmull-Rom + 插点防重复锚点"""
import io

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()


def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:90])
    s = s.replace(old, new)


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

rep("""            if (bd <= 24 / view().s) {
              pushUndo();""",
"""            let near = Infinity;
            pts2.forEach(q => { near = Math.min(near, Math.hypot(p.x - (ox2 + q.x), p.y - (oy2 + q.y))); });
            if (bd <= 24 / view().s && near > 10 / view().s) {
              pushUndo();""")

io.open(P, "w", encoding="utf-8").write(s)
print("r35a patched")
