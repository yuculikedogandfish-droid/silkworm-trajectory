# -*- coding: utf-8 -*-
import io
P = r"H:\tool\silkworm-trajectory\docs\index.html"
h = io.open(P, encoding="utf-8").read()

# 1) r39：空白处单击（未形成框选）＝取消选择
old = "      if (marquee && marquee.armed) marqueeSelect(); else marquee = null;"
new = """      if (marquee && marquee.armed) marqueeSelect();
      else { if (marquee && !marquee.add && sel.size) { sel.clear(); sig = ''; refresh(true); } marquee = null; }"""
assert old in h
h = h.replace(old, new, 1)

# 2) r39 暴露选中集 API（供右键批量操作 / QA）
old2 = "  setInterval(() => refresh(false), 500);\n  refresh(true);\n})();"
new2 = """  setInterval(() => refresh(false), 500);
  refresh(true);
  window.__layerSel = {
    ids: () => [...sel],
    size: () => sel.size,
    set: (ids) => { sel.clear(); (ids || []).forEach(id => sel.add(id)); sig = ''; refresh(true); },
    clear: () => { if (sel.size) { sel.clear(); sig = ''; refresh(true); } },
    bbox: () => bboxOf([...sel]),
    editing: () => inEditMode(),
  };
})();"""
assert old2 in h
h = h.replace(old2, new2, 1)

# 3) r45 独立模块：识别条避让顶栏 + 框选右键批量删除
r45 = r"""
/* ===== r45 识别条避让顶栏 + 框选右键批量操作（独立模块，只加不改） ===== */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const H = () => window.__studioHabitat;

  /* 识别条：永远落在顶栏（含换行的按钮）下面，不再压住按钮 */
  function placeRecBar() {
    const bar = document.querySelector('.hab-rec-bar');
    const top = document.querySelector('.hab-top');
    const hab = $('habitat');
    if (!bar || !top || !hab) return;
    const hr = hab.getBoundingClientRect();
    const tr = top.getBoundingClientRect();
    bar.style.top = Math.max(8, tr.bottom - hr.top + 8) + 'px';
  }
  window.addEventListener('resize', placeRecBar);
  placeRecBar();
  setTimeout(placeRecBar, 400);
  setInterval(placeRecBar, 1500);

  /* 框选 / 多选之后：在选区里右键 = 批量操作 */
  const world = $('habWorld');
  if (!world) return;
  let menu = null;
  function closeMenu() { if (menu) { menu.remove(); menu = null; } }
  document.addEventListener('pointerdown', (e) => { if (menu && !menu.contains(e.target)) closeMenu(); }, true);
  window.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeMenu(); });

  function openBatch(x, y) {
    closeMenu();
    const api = window.__layerSel;
    const n = api.size();
    menu = document.createElement('div');
    menu.className = 'lay-menu';
    menu.style.cssText = 'position:fixed;z-index:60;';
    const mk = (label, fn, danger) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      b.style.display = 'block';
      if (danger) b.style.color = '#ff9a8a';
      b.addEventListener('click', () => { closeMenu(); fn(); });
      menu.appendChild(b);
    };
    mk('删除选中的 ' + n + ' 块', () => {
      const ids = api.ids().filter(id => (H().agents().find(a => a.id === id) || {}).kind === 'weave');
      if (!ids.length) return;
      if (!confirm('确定删掉选中的 ' + ids.length + ' 块织网单元？（Ctrl+Z 可撤销）')) return;
      ids.forEach(id => { if (window.__weaveHooks && window.__weaveHooks.deleteUnit) window.__weaveHooks.deleteUnit(id); });
      api.clear();
    }, true);
    if (n >= 2) mk('把这 ' + n + ' 层编为一组', () => { const b = $('habLayerGroup'); if (b) b.click(); });
    mk('取消选择', () => api.clear());
    ($('habitat') || document.body).appendChild(menu);
    const r = menu.getBoundingClientRect();
    menu.style.left = Math.max(6, Math.min(window.innerWidth - r.width - 8, x)) + 'px';
    menu.style.top = Math.max(6, Math.min(window.innerHeight - r.height - 8, y)) + 'px';
  }

  world.addEventListener('contextmenu', (e) => {
    const api = window.__layerSel;
    if (!api || api.editing() || !api.size()) return;
    const v = H().view();
    const r = world.getBoundingClientRect();
    const wx = (e.clientX - r.left - v.cx) / v.s, wy = (e.clientY - r.top - v.cy) / v.s;
    const b = api.bbox();
    if (!b) return;
    const pad = 12 / (v.s || 1);
    if (wx < b.l - pad || wx > b.r + pad || wy < b.t - pad || wy > b.b + pad) return;
    e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
    openBatch(e.clientX, e.clientY);
  }, true);
})();
"""
h = h.replace("</body>", "<script>" + r45 + "</script>\n</body>", 1)
io.open(P, "w", encoding="utf-8").write(h)
print("r45 patched", len(h))
