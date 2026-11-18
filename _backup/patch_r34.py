# -*- coding: utf-8 -*-
"""r34：缺口按平面/建模软件的手感来——画的时候就是曲线；点到曲线上加锚点；锚点更大更好拖；右键菜单补齐"添加"项"""
import io

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()


def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:90])
    s = s.replace(old, new)


# ---------- 1. 画的时候就是曲线（草稿也按 Catmull-Rom 闭合画） ----------
rep("""    // 正在画、还没收尾的点（加壁/加丝路/缺口/外框）
    const draft = (e.drafts && e.drafts[key]) || [];
    if (draft.length) {
      ctx.strokeStyle = 'rgba(120,210,255,0.8)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      draft.forEach((q, k) => {
        const px = v.px(ox + q.x), py = v.py(oy + q.y);
        if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      if (e.mode === 'notch' && draft.length >= 3) ctx.closePath();
      ctx.stroke();""",
"""    // 正在画、还没收尾的点（加壁/加丝路/缺口/外框）
    const draft = (e.drafts && e.drafts[key]) || [];
    if (draft.length) {
      // 缺口在"画"的时候就已经是光滑曲线（跟收尾后一致），不是先折线后变曲线
      const draftLine = (e.mode === 'notch' && draft.length >= 3) ? weaveNotchCurve(draft) : draft;
      ctx.strokeStyle = 'rgba(120,210,255,0.8)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      draftLine.forEach((q, k) => {
        const px = v.px(ox + q.x), py = v.py(oy + q.y);
        if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      if (e.mode === 'notch' && draft.length >= 3) ctx.closePath();
      ctx.stroke();""")

# ---------- 2. 点到"曲线上"就插一个锚点（老规矩）；点在面里不动 ----------
rep("""        if (e.mode === 'notch') {
          const sh2 = (a.custom && a.custom.shapes && a.custom.shapes[ek]) || null;
          const hasN = !!((sh2 && sh2.notchPts && sh2.notchPts.length >= 3) ||
            (c.spec && c.spec.notchPts && c.spec.notchPts.length >= 3));
          if (hasN && !dr.length) {
            hint('这一格已经有缺口了：拖白点改形状、拖边上的小方点加顶点、右键删点。想推倒重画，右键菜单里选「重画缺口」。');
            return;
          }
          if (dr.length && Math.hypot(dr[dr.length - 1].x - c.lx, dr[dr.length - 1].y - c.ly) < 12) return;
        }""",
"""        if (e.mode === 'notch') {
          const sh2 = (a.custom && a.custom.shapes && a.custom.shapes[ek]) || null;
          const pts2 = (sh2 && sh2.notchPts && sh2.notchPts.length >= 3) ? sh2.notchPts
            : ((weaveCellContent(a, e.ix, e.iy).cell || {}).notchPts || null);
          // 已经有缺口、还没在重画：点在这条线上＝就地插一个锚点（平面软件的老规矩）
          if (pts2 && pts2.length >= 3 && !dr.length) {
            const ox2 = a.x + e.ix * a.w, oy2 = a.y + e.iy * a.h;
            let bi = -1, bd = Infinity, bt = 0.5;
            for (let i = 0; i < pts2.length; i++) {
              const q0 = pts2[i], q1 = pts2[(i + 1) % pts2.length];
              const ax2 = ox2 + q0.x, ay2 = oy2 + q0.y, bx2 = ox2 + q1.x, by2 = oy2 + q1.y;
              const ex = bx2 - ax2, ey = by2 - ay2, L2 = ex * ex + ey * ey || 1;
              let t2 = ((p.x - ax2) * ex + (p.y - ay2) * ey) / L2;
              t2 = Math.max(0, Math.min(1, t2));
              const dd = Math.hypot(p.x - (ax2 + ex * t2), p.y - (ay2 + ey * t2));
              if (dd < bd) { bd = dd; bi = i; bt = t2; }
            }
            if (bd <= 24 / view().s) {
              pushUndo();
              const sh = ensureShapeOverride(a, e.ix, e.iy);
              const arr = (sh.notchPts && sh.notchPts.length >= 3) ? sh.notchPts : pts2.map(v2 => ({ x: v2.x, y: v2.y }));
              sh.notchPts = arr;
              if (sh.notch) delete sh.notch;
              const q0 = arr[bi], q1 = arr[(bi + 1) % arr.length];
              arr.splice(bi + 1, 0, {
                x: q0.x + (q1.x - q0.x) * bt,
                y: q0.y + (q1.y - q0.y) * bt,
              });
              if (a.cache && a.cache.delete) a.cache.delete(ek);
              weaveCellContent(a, e.ix, e.iy);
              // 插完直接进入"拖这个新锚点"，手感跟钢笔工具一样顺
              habitat.drag = { kind: 'weaveHandle', handle: { kind: 'notchV', vi: bi + 1 } };
              syncEditNote();
              hint('在这条线上加了一个锚点，现在直接拖动它就能微调。');
              return;
            }
            hint('点在缺口的"线"上才会加锚点；拖白点改形状，想推倒重画点「重画缺口」。');
            return;
          }
          if (dr.length && Math.hypot(dr[dr.length - 1].x - c.lx, dr[dr.length - 1].y - c.ly) < 12) return;
        }""")

# ---------- 3. 锚点画得更大、更好抓；中点用小空心方 ----------
rep("""      } else if (h.kind === 'outlineMid') {""",
"""      } else if (h.kind === 'notchV') {
        const sz = hov ? 11 : 8.5;
        ctx.fillStyle = '#e8eee9';
        ctx.fillRect(px - sz / 2, py - sz / 2, sz, sz);
        ctx.strokeStyle = 'rgba(121,203,182,0.9)';
        ctx.strokeRect(px - sz / 2, py - sz / 2, sz, sz);
      } else if (h.kind === 'notchMid') {
        ctx.strokeStyle = hov ? 'rgba(232,238,233,0.95)' : 'rgba(232,238,233,0.55)';
        ctx.strokeRect(px - 4, py - 4, 8, 8);
      } else if (h.kind === 'outlineMid') {""")

rep("""        const hs = weaveHandles(a, e.ix, e.iy);
        const hit = hs.find(h => Math.hypot(h.x - p.x, h.y - p.y) <= tol);""",
"""        const hs = weaveHandles(a, e.ix, e.iy);
        // 缺口工具下把抓取半径放大（白点小、又贴着曲线，手要够得着）
        const tol2 = (e.tool === 'notch') ? 22 / v.s : tol;
        const hit = hs.find(h => Math.hypot(h.x - p.x, h.y - p.y) <= tol2);""")

rep("""          const tol = 12 / v.s;
          const hs = weaveHandles(a, e.ix, e.iy);""",
"""          const tol = (e.tool === 'notch') ? 18 / v.s : 12 / v.s;
          const hs = weaveHandles(a, e.ix, e.iy);""")

# ---------- 4. 右键菜单：把"添加"补齐 ----------
rep("""      { label: '在这里开一个孔', run: () => {""",
"""      { label: '添加孔洞（放在这一点）', run: () => {""")
rep("""      { label: '重画缺口（从这里围一圈）', run: () => {""",
"""      { label: '添加缺口（在格内点几下围一圈）', run: () => {""")
rep("""      { label: '从这里起笔画一条壁', run: () => {""",
"""      { label: '添加壁（从这里起笔）', run: () => {""")
rep("""      { label: '从这里起笔画一条丝路', run: () => {""",
"""      { label: '添加丝路（从这里起笔）', run: () => {""")
rep("""      { label: '清掉这一格的自定义形状', danger: true, run: () => {""",
"""      { label: '重设整块外框（点几下围一圈）', run: () => {
          setWeaveTool('outline');
          e.mode = 'outline';
          e.outlinePts = [{ x: p.x, y: p.y }];
          syncEditNote();
          hint('绕着这一块点一圈，双击收尾，整块外形就换成你画的了。');
        } },
      { label: '清掉这一格的形状（孔/缺口/壁/丝路）', danger: true, run: () => {""")

# ---------- 5. 文案 ----------
rep("""    if (tool === 'notch') { el.textContent = '正在改缺口 · 已有缺口时点格内不会再加点：拖白点改形状、拖边中小方点加顶点；右键压到锚点上会列出「删除这个锚点 / 删除整个缺口」，想重画点「重画缺口」。'; return; }""",
"""    if (tool === 'notch') { el.textContent = '正在改缺口 · 拖白点＝挪锚点；点在这条缺口的线上＝就地加一个锚点（加完直接能拖）；拖边中间的小方点＝加锚点；右键压到锚点＝删这个锚点/删整个缺口。'; return; }""")

rep("""    notch: '点几下围一圈＝缺口（首尾自动接成光滑曲线，不是折线）· 双击收尾 · 拖白点改形状 · 拖边小方点加顶点 · 右键＝菜单（在锚点上会给出「删除这个锚点 / 删除整个缺口」）',""",
"""    notch: '点几下围一圈＝缺口（画的时候就是光滑曲线）· 双击收尾 · 拖白点挪锚点 · 点在线上就地加锚点 · 拖边小方点也加锚点 · 右键＝菜单',""")

io.open(P, "w", encoding="utf-8").write(s)
print("r34 patched")
