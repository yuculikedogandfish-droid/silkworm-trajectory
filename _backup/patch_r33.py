# -*- coding: utf-8 -*-
"""r33：右键不再"直接删"，改成菜单里给删除选项（锚点 / 整个缺口 / 孔）"""
import io

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()


def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:90])
    s = s.replace(old, new)


# 1) 去掉"右键直接删"，改成先找命中目标
rep("""      ev.preventDefault();
      if (weaveDeleteAt(p) === true) return;
      const a0 = habitat.agents.find(z => z.kind === 'weave' &&""",
"""      ev.preventDefault();
      const a0 = habitat.agents.find(z => z.kind === 'weave' &&""")

# 2) 命中检测 + 菜单项拼装
rep("""    const lx = ci.lx, ly = ci.ly;
    showCtxMenu(ev.clientX, ev.clientY, [""",
"""    const lx = ci.lx, ly = ci.ly;
    // 右键压在哪个可删的东西上：不立刻删，先把"删什么"做成菜单项
    const v = view();
    const tol = 16 / v.s;
    const delKinds = { islandMove: 3, islandR: 3, notchMove: 3, notchR: 3, notchV: 3, wallV: 2, pathV: 2, outlineV: 2, outlineMid: 1 };
    let hit = null, hd = Infinity, hw = 0;
    weaveHandles(a, e.ix, e.iy).forEach(h => {
      if (!delKinds[h.kind]) return;
      const d = Math.hypot(h.x - p.x, h.y - p.y);
      if (d > tol) return;
      const wgt = delKinds[h.kind];
      if (wgt > hw || (wgt === hw && d < hd)) { hw = wgt; hd = d; hit = h; }
    });
    const deleteWholeNotch = () => {
      pushUndo();
      const sh = ensureShapeOverride(a, e.ix, e.iy);
      delete sh.notchPts;
      delete sh.notch;
      if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
      weaveCellContent(a, e.ix, e.iy);
      syncEditNote();
      toast('这一格的缺口整个删掉了。', 'ok');
    };
    const deleteIsland = (i) => {
      pushUndo();
      const sh = ensureShapeOverride(a, e.ix, e.iy);
      if (sh.islands && sh.islands[i]) {
        sh.islands.splice(i, 1);
        if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
        weaveCellContent(a, e.ix, e.iy);
        syncEditNote();
        toast('这个孔删掉了。', 'ok');
      }
    };
    const hitItems = [];
    if (hit) {
      if (hit.kind === 'notchV') {
        hitItems.push({ label: '删除这个锚点', danger: true, run: () => { deleteWeaveHandleVertex(hit); } });
        hitItems.push({ label: '删除整个缺口', danger: true, run: deleteWholeNotch });
      } else if (hit.kind === 'notchMove' || hit.kind === 'notchR') {
        hitItems.push({ label: '删除整个缺口', danger: true, run: deleteWholeNotch });
      } else if (hit.kind === 'islandMove' || hit.kind === 'islandR') {
        hitItems.push({ label: '删除这个孔', danger: true, run: () => deleteIsland(hit.i) });
      } else {
        hitItems.push({ label: '删除这个锚点', danger: true, run: () => { deleteWeaveHandleVertex(hit); } });
      }
    }
    showCtxMenu(ev.clientX, ev.clientY, hitItems.concat([""")

rep("""      { label: '退出编辑', run: () => { if (window.__weaveHooks && window.__weaveHooks.exit) window.__weaveHooks.exit(); } },
    ]);""",
"""      { label: '退出编辑', run: () => { if (window.__weaveHooks && window.__weaveHooks.exit) window.__weaveHooks.exit(); } },
    ]));""")

# 3) 文案：右键不再"直接删"
rep("""    if (tool === 'notch') { el.textContent = '正在改缺口 · 已有缺口时点格内不会再加点：拖白点改形状、拖边中小方点加顶点、右键删点；想推倒重画点「重画缺口」，或在格内右键选菜单。'; return; }""",
"""    if (tool === 'notch') { el.textContent = '正在改缺口 · 已有缺口时点格内不会再加点：拖白点改形状、拖边中小方点加顶点；右键压到锚点上会列出「删除这个锚点 / 删除整个缺口」，想重画点「重画缺口」。'; return; }""")

rep("""    notch: '点几下围一圈＝缺口（首尾自动接成光滑曲线，不是折线）· 双击收尾 · 拖白点改形状 · 拖边小方点加顶点 · 右键删点 · 右键空白＝菜单',""",
"""    notch: '点几下围一圈＝缺口（首尾自动接成光滑曲线，不是折线）· 双击收尾 · 拖白点改形状 · 拖边小方点加顶点 · 右键＝菜单（在锚点上会给出「删除这个锚点 / 删除整个缺口」）',""")

rep("""hint('右键点在顶点、壁、丝路或孔洞/缺口上就能删；点空白处不删东西。');""",
"""hint('右键任意位置都会开菜单；压到锚点 / 孔 / 缺口时，菜单第一项就是「删除这个锚点」「删除整个缺口」。');""")

io.open(P, "w", encoding="utf-8").write(s)
print("r33 patched")
