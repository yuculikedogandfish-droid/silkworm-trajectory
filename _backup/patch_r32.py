# -*- coding: utf-8 -*-
"""r32：缺口闭合曲线化 + 点一下不再堆锚点 + 右键菜单"""
import io

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()

def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:80])
    s = s.replace(old, new)

def rep_last(old, new):
    global s
    i = s.rfind(old)
    assert i >= 0, old[:60]
    s = s[:i] + new + s[i + len(old):]


# ---------- 1. weaveSmooth：闭合时首尾连续（去掉接缝的折角） ----------
rep("""    const P = pts.map(p => ({ x: p.x, y: p.y }));
    const cl = !!closed && P.length >= 3;
    if (cl) P.push(P[0]);""",
"""    const cl = !!closed && pts.length >= 3;
    // 闭合时在两端各补一个环绕点，接缝处切线才连续（不然首尾会鼓出一个折角）
    const P = cl
      ? [pts[pts.length - 1], ...pts, pts[0], pts[1]].map(p => ({ x: p.x, y: p.y }))
      : pts.map(p => ({ x: p.x, y: p.y }));
    if (!cl) P.push(P[0]);""")

# ---------- 2. 缺口曲线助手 ----------
rep("""  function weavePolyDist(pts, x, y) {""",
"""  // 缺口：控制点 -> 闭合平滑曲线（Catmull-Rom）。所有判定/绘制都走这一份，形状才是"曲线闭合"。
  function weaveNotchCurve(pts) {
    if (!Array.isArray(pts) || pts.length < 3) return pts || [];
    return weaveSmooth(pts, true);
  }

  function weavePolyDist(pts, x, y) {""")

# ---------- 3. 判定、投影、法线、孔缘、右键命中的多边形分支全部改成曲线 ----------
rep("""      if (weaveInPoly(cell.notchPts, x, y) || weavePolyDist(cell.notchPts, x, y) < m) return false;""",
"""      const cv = weaveNotchCurve(cell.notchPts);
      if (weaveInPoly(cv, x, y) || weavePolyDist(cv, x, y) < m) return false;""")

rep("""      || (Array.isArray(cell.notchPts) && cell.notchPts.length >= 3 && weavePolyDist(cell.notchPts, x, y) < 9);""",
"""      || (Array.isArray(cell.notchPts) && cell.notchPts.length >= 3 && weavePolyDist(weaveNotchCurve(cell.notchPts), x, y) < 9);""")

rep("""      const inside = weaveInPoly(cell.notchPts, x, y);
      const d = weavePolyDist(cell.notchPts, x, y);
      if (inside || d < p) {
        const pts = cell.notchPts;""",
"""      const pts = weaveNotchCurve(cell.notchPts);
      const inside = weaveInPoly(pts, x, y);
      const d = weavePolyDist(pts, x, y);
      if (inside || d < p) {""")

rep("""      const inside = weaveInPoly(cell.notchPts, x, y);
      const d = weavePolyDist(cell.notchPts, x, y);
      if (inside || d < 6) {
        const pts = cell.notchPts;""",
"""      const pts = weaveNotchCurve(cell.notchPts);
      const inside = weaveInPoly(pts, x, y);
      const d = weavePolyDist(pts, x, y);
      if (inside || d < 6) {""")

rep("""      const np = c.cell.notchPts.map(q => ({ x: q.x + ox, y: q.y + oy }));""",
"""      const np = weaveNotchCurve(c.cell.notchPts).map(q => ({ x: q.x + ox, y: q.y + oy }));""")

# ---------- 4. 编辑预览：虚线画曲线而不是折线 ----------
rep("""    const npC = (sh && sh.notchPts) || (c.cell && c.cell.notchPts) || null;
    if (Array.isArray(npC) && npC.length >= 3) {""",
"""    const npC = (sh && sh.notchPts) || (c.cell && c.cell.notchPts) || null;
    const npCurve = weaveNotchCurve(npC);
    if (Array.isArray(npCurve) && npCurve.length >= 3) {""")
rep("""      npC.forEach((q, k) => {
        const px = v.px(ox + q.x), py = v.py(oy + q.y);
        if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.closePath();""",
"""      npCurve.forEach((q, k) => {
        const px = v.px(ox + q.x), py = v.py(oy + q.y);
        if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.closePath();""")

# ---------- 5. 手感：已有缺口时点格内不再堆锚点；连点同一点都不记 ----------
rep("""        weaveEditDraft(e, e.ix + ',' + e.iy).push({ x: c.lx, y: c.ly });
        syncEditNote();
        return;""",
"""        const ek = e.ix + ',' + e.iy;
        const dr = weaveEditDraft(e, ek);
        if (e.mode === 'notch') {
          const sh2 = (a.custom && a.custom.shapes && a.custom.shapes[ek]) || null;
          const hasN = !!((sh2 && sh2.notchPts && sh2.notchPts.length >= 3) ||
            (c.spec && c.spec.notchPts && c.spec.notchPts.length >= 3));
          if (hasN && !dr.length) {
            hint('这一格已经有缺口了：拖白点改形状、拖边上的小方点加顶点、右键删点。想推倒重画，右键菜单里选「重画缺口」。');
            return;
          }
          if (dr.length && Math.hypot(dr[dr.length - 1].x - c.lx, dr[dr.length - 1].y - c.ly) < 12) return;
        }
        dr.push({ x: c.lx, y: c.ly });
        syncEditNote();
        return;""")

# ---------- 6. 「重画缺口」按钮 ----------
rep("""          <button type="button" id="habWeaveEditEnd">这一笔收尾</button>
          <button type="button" id="habWeaveEditClear">清掉本格自定义</button>""",
"""          <button type="button" id="habWeaveEditEnd">这一笔收尾</button>
          <button type="button" id="habWeaveNotchRedraw">重画缺口</button>
          <button type="button" id="habWeaveEditClear">清掉本格自定义</button>""")

rep("""    const weaveEditEnd = document.getElementById('habWeaveEditEnd');
    if (weaveEditEnd) weaveEditEnd.addEventListener('click', finishWeaveEditLine);""",
"""    const weaveEditEnd = document.getElementById('habWeaveEditEnd');
    if (weaveEditEnd) weaveEditEnd.addEventListener('click', finishWeaveEditLine);
    const notchRedraw = document.getElementById('habWeaveNotchRedraw');
    if (notchRedraw) notchRedraw.addEventListener('click', () => {
      const a = weaveEditAgent();
      const e = habitat.weaveEdit;
      if (!a || !e) { hint('先点一块织网单元进编辑，再用「重画缺口」。'); return; }
      pushUndo();
      const sh = ensureShapeOverride(a, e.ix, e.iy);
      delete sh.notchPts;
      delete sh.notch;
      if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
      weaveCellContent(a, e.ix, e.iy);
      setWeaveTool('notch');
      e.mode = 'notch';
      e.drafts = {};
      syncEditNote();
      toast('旧缺口已清掉：在格内点几下围出新形状，双击（或点「这一笔收尾」）收尾。', 'ok');
    });""")

# ---------- 7. 右键菜单：HTML + CSS + JS ----------
rep_last("""</body>""",
"""<div id="habCtxMenu" role="menu"></div>
</body>""")

rep(""".hab-tools[aria-disabled="true"] { opacity: .45; pointer-events: none; }""",
""".hab-tools[aria-disabled="true"] { opacity: .45; pointer-events: none; }
#habCtxMenu{position:fixed;z-index:99999;display:none;min-width:196px;padding:6px;background:#0e1614;border:1px solid #3a4a44;box-shadow:0 10px 28px rgba(0,0,0,.55);border-radius:8px}
#habCtxMenu button{display:block;width:100%;margin:2px 0;padding:7px 10px;text-align:left;font:13px "Microsoft YaHei",system-ui,sans-serif;color:#e7efeb;background:#16201d;border:1px solid #2b3a35;border-radius:6px;cursor:pointer}
#habCtxMenu button:hover{background:#1d2a26;border-color:#4d6a60}
#habCtxMenu button.danger{color:#ffb3a3;border-color:#5a3330}
#habCtxMenu .ctx-title{padding:2px 8px 6px;font:11px "Microsoft YaHei",system-ui,sans-serif;color:#8fa7a0}
</style>""")

rep("""  world.addEventListener('contextmenu', (ev) => {
    if (!habitat.weaveEdit || !habitat.weaveEdit.agentId) return;
    ev.preventDefault();
    const p = screenToHab(ev);
    weaveDeleteAt(p);
  });""",
"""  // 右键菜单：点格内空白处弹出「这一格能做什么」，点到可删的东西时仍然右键=删
  const ctxMenuEl = document.getElementById('habCtxMenu');
  function hideCtxMenu() { if (ctxMenuEl) ctxMenuEl.style.display = 'none'; }
  function showCtxMenu(clientX, clientY, items) {
    if (!ctxMenuEl) return;
    ctxMenuEl.innerHTML = '<div class="ctx-title">这一格：</div>';
    items.forEach(it => {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = it.label;
      if (it.danger) b.className = 'danger';
      b.addEventListener('click', () => {
        hideCtxMenu();
        try { it.run(); } catch (err) { console.warn(err); }
      });
      ctxMenuEl.appendChild(b);
    });
    ctxMenuEl.style.display = 'block';
    ctxMenuEl.style.left = Math.max(8, Math.min(clientX, window.innerWidth - 224)) + 'px';
    ctxMenuEl.style.top = Math.max(8, Math.min(clientY, window.innerHeight - 300)) + 'px';
  }
  window.addEventListener('pointerdown', (ev) => {
    if (ctxMenuEl && ctxMenuEl.style.display === 'block' && !ctxMenuEl.contains(ev.target)) hideCtxMenu();
  }, true);
  window.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') hideCtxMenu(); });

  world.addEventListener('contextmenu', (ev) => {
    const p = screenToHab(ev);
    // 没在编辑：右键点某一块 = 直接进这一块的编辑，再弹菜单
    if (!habitat.weaveEdit || !habitat.weaveEdit.agentId) {
      const hit0 = habitat.agents.find(z => z.kind === 'weave' &&
        Math.abs(z.x - p.x) <= z.w / 2 && Math.abs(z.y - p.y) <= z.h / 2);
      if (!hit0) return;
      ev.preventDefault();
      if (window.__weaveHooks && window.__weaveHooks.enter) window.__weaveHooks.enter(hit0.id);
    } else {
      ev.preventDefault();
      if (weaveDeleteAt(p) === true) return;
      const a0 = habitat.agents.find(z => z.kind === 'weave' &&
        Math.abs(z.x - p.x) <= z.w / 2 && Math.abs(z.y - p.y) <= z.h / 2);
      if (!a0) { hideCtxMenu(); return; }
      if (a0.id !== habitat.weaveEdit.agentId && window.__weaveHooks && window.__weaveHooks.enter) {
        window.__weaveHooks.enter(a0.id);
      }
    }
    const a = weaveEditAgent();
    const e = habitat.weaveEdit;
    if (!a || !e) return;
    // 让 e.ix/e.iy 对准右键点所在的格
    const ci = weaveCellAt(a, p);
    e.ix = ci.ix; e.iy = ci.iy;
    const lx = ci.lx, ly = ci.ly;
    showCtxMenu(ev.clientX, ev.clientY, [
      { label: '在这里开一个孔', run: () => {
          pushUndo();
          const sh = ensureShapeOverride(a, e.ix, e.iy);
          if (!sh.islands || !sh.islands.length) sh.islands = [{ cx: 0, cy: 0, r: Math.min(a.w, a.h) * 0.26 }];
          sh.islands[0].cx = lx; sh.islands[0].cy = ly;
          if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
          weaveCellContent(a, e.ix, e.iy); syncEditNote();
          toast('孔已开在你点的地方，拖青圈可改大小。', 'ok');
        } },
      { label: '重画缺口（从这里围一圈）', run: () => {
          pushUndo();
          const sh = ensureShapeOverride(a, e.ix, e.iy);
          delete sh.notchPts; delete sh.notch;
          if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
          weaveCellContent(a, e.ix, e.iy);
          setWeaveTool('notch');
          e.mode = 'notch'; e.drafts = {};
          syncEditNote();
          hint('在格内连点几下围出形状，双击收尾（至少 3 点）。');
        } },
      { label: '从这里起笔画一条壁', run: () => {
          setWeaveTool('wall');
          e.mode = 'wall';
          const dr = weaveEditDraft(e, e.ix + ',' + e.iy);
          dr.push({ x: lx, y: ly });
          syncEditNote();
          hint('接着点，双击收尾。壁是曲线，只挡蚕不显示在成品里。');
        } },
      { label: '从这里起笔画一条丝路', run: () => {
          setWeaveTool('path');
          e.mode = 'path';
          const dr = weaveEditDraft(e, e.ix + ',' + e.iy);
          dr.push({ x: lx, y: ly });
          syncEditNote();
          hint('接着点，双击收尾。蚕会顺着这条线走。');
        } },
      { label: '清掉这一格的自定义形状', danger: true, run: () => {
          pushUndo();
          clearWeaveCellCustom(a, e.ix, e.iy);
          syncEditNote();
          toast('这一格回到默认形状。', 'ok');
        } },
      { label: '退出编辑', run: () => { if (window.__weaveHooks && window.__weaveHooks.exit) window.__weaveHooks.exit(); } },
    ]);
  });""")

# ---------- 8. 文案：缺口说明改成曲线 ----------
rep("""    notch: '在格内点几下＝围出缺口的形状（可任意曲线封闭形）· 双击收尾 · 拖白点改形状 · 拖边中点加新点 · 右键删点',""",
"""    notch: '点几下围一圈＝缺口（首尾自动接成光滑曲线，不是折线）· 双击收尾 · 拖白点改形状 · 拖边小方点加顶点 · 右键删点 · 右键空白＝菜单',""")
rep("""    if (tool === 'notch') { el.textContent = '正在改缺口 · 在格内点几下围出一个形状，双击收尾（至少 3 点）；拖白点改形状、拖边中间的小方点加新点、右键删点或删整个缺口。'; return; }""",
"""    if (tool === 'notch') { el.textContent = '正在改缺口 · 已有缺口时点格内不会再加点：拖白点改形状、拖边中小方点加顶点、右键删点；想推倒重画点「重画缺口」，或在格内右键选菜单。'; return; }""")

io.open(P, "w", encoding="utf-8").write(s)
print("r32 patched", len(s))
