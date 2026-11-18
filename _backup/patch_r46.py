# -*- coding: utf-8 -*-
import io, shutil
P = r"H:\tool\silkworm-trajectory\docs\index.html"
h = io.open(P, encoding="utf-8").read()
shutil.copyfile(P, r"H:\tool\silkworm-trajectory\_backup\index-r45-before-r46.html")

# 1) 单个 / 批量删除共用同一个实现；批量只记一次撤销
old = """    function deleteWeaveUnit(a) {
      if (!a || a.kind !== 'weave') { toast('先点中一块织网单元，再删除。', 'err'); return; }
      pushUndo();"""
new = """    function deleteWeaveUnit(a, skipUndo) {
      if (!a || a.kind !== 'weave') { toast('先点中一块织网单元，再删除。', 'err'); return; }
      if (!skipUndo) pushUndo();"""
assert old in h
h = h.replace(old, new, 1)
old = """      deleteUnit: (id) => deleteWeaveUnit(habitat.agents.find(x => x.id === id) || chosen()),
    });"""
new = """      deleteUnit: (id) => deleteWeaveUnit(habitat.agents.find(x => x.id === id) || chosen()),
      deleteUnits: (ids) => {
        const set = new Set(ids || []);
        const list = habitat.agents.filter(a => a.kind === 'weave' && set.has(a.id));
        if (!list.length) return;
        pushUndo();
        list.forEach(a => deleteWeaveUnit(a, true));
        toast('已删除 ' + list.length + ' 块织网单元。按 Ctrl+Z 可以一次恢复整批。', 'ok');
      },
    });"""
assert old in h
h = h.replace(old, new, 1)
h = h.replace("""      ids.forEach(id => { if (window.__weaveHooks && window.__weaveHooks.deleteUnit) window.__weaveHooks.deleteUnit(id); });
      api.clear();""", """      if (window.__weaveHooks && window.__weaveHooks.deleteUnits) window.__weaveHooks.deleteUnits(ids);
      else ids.forEach(id => { if (window.__weaveHooks && window.__weaveHooks.deleteUnit) window.__weaveHooks.deleteUnit(id); });
      api.clear();""", 1)

# 2) 给双击模块提供“正在画外框”状态
h = h.replace("""    agents: () => habitat.agents,
    // 编辑态自检""", """    agents: () => habitat.agents,
    drawingOutline: () => !!habitat.newOutline,
    // 编辑态自检""", 1)

# 3) 识别条定位改用 ResizeObserver，避免持续布局轮询
h = h.replace("""  window.addEventListener('resize', placeRecBar);
  placeRecBar();
  setTimeout(placeRecBar, 400);
  setInterval(placeRecBar, 1500);""", """  window.addEventListener('resize', placeRecBar, { passive: true });
  if (window.ResizeObserver) {
    const ro = new ResizeObserver(placeRecBar);
    const top = document.querySelector('.hab-top');
    if (top) ro.observe(top);
    ro.observe($('habitat'));
  }
  placeRecBar();
  setTimeout(placeRecBar, 400);""", 1)

# 4) 缩略图：后台标签页不画，降低刷新频率
h = h.replace("""  setInterval(() => { const p = $('habRight'); if (p && p.offsetParent) paintThumbs(); }, 1200);""", """  setInterval(() => { const p = $('habRight'); if (!document.hidden && p && p.offsetParent) paintThumbs(); }, 2500);""", 1)

# 5) r46：双击切换选中（正在画线时保留“双击收尾”）
r46 = r"""
/* ===== r46 双击切换单元选定（独立模块，只加不改） ===== */
(function () {
  'use strict';
  const world = document.getElementById('habWorld');
  const H = () => window.__studioHabitat;
  if (!world) return;
  function hasOpenDraft(st) {
    return !!(st && (st.drafts || []).some(s => Number(s.split(':').pop()) > 0));
  }
  world.addEventListener('dblclick', (e) => {
    const api = window.__layerSel;
    const hab = H();
    if (!api || !hab) return;
    if (hab.drawingOutline && hab.drawingOutline()) return; // 画外框：双击封闭
    const st = hab.weaveEditState && hab.weaveEditState();
    if (hasOpenDraft(st)) return;                          // 画缺口/壁/丝路：双击收尾
    const r = world.getBoundingClientRect();
    const v = hab.view();
    const x = (e.clientX - r.left - v.cx) / v.s;
    const y = (e.clientY - r.top - v.cy) / v.s;
    const hit = hab.agents().filter(a => a.kind === 'weave' && Math.abs(a.x - x) <= a.w / 2 && Math.abs(a.y - y) <= a.h / 2).pop();
    if (!hit) return;
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    if (st && st.agentId && window.__weaveHooks && window.__weaveHooks.exit) window.__weaveHooks.exit();
    const ids = api.ids();
    if (ids.indexOf(hit.id) >= 0) {
      api.set(ids.filter(id => id !== hit.id));            // 再双击已选块：取消这一块
    } else if (e.shiftKey || e.ctrlKey || e.metaKey) {
      api.set(ids.concat(hit.id));                         // 修饰键双击：追加
    } else {
      api.set([hit.id]);                                   // 双击未选块：只选这一块
    }
  }, true);
})();
"""
j = h.rfind("</body>")
h = h[:j] + "<script>" + r46 + "</script>\n" + h[j:]
io.open(P, "w", encoding="utf-8").write(h)
print("r46 patched", len(h))
