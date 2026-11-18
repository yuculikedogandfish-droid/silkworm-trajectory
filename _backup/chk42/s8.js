
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
