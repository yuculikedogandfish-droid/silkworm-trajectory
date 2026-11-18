
/* ===== r39 个体与图层合并 + 组一起挪 + 吸附/对齐/阵列（独立模块，只加不改） ===== */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const H = () => window.__studioHabitat;
  const tree = $('habLayerTree');
  if (!tree) return;

  /* ---------- 组数据的存与带 ---------- */
  const KEY = 'silkworm-habitat-layer-groups/v2';
  let store = { groups: [], member: {}, order: [] };
  function norm(o) {
    return {
      groups: Array.isArray(o && o.groups) ? o.groups.map(g => ({ id: String(g.id), name: String(g.name || '组'), open: g.open !== false })) : [],
      member: (o && o.member && typeof o.member === 'object') ? o.member : {},
      order: Array.isArray(o && o.order) ? o.order.slice() : [],
    };
  }
  try { const raw = localStorage.getItem(KEY); if (raw) store = norm(JSON.parse(raw)); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {} };

  // 工程文件带组：exportHabitat / importHabitat 各挂一个钩子（由主程序调用）
  window.__layerStore = {
    dump: () => ({ groups: store.groups, member: store.member, order: store.order }),
    load: (o) => { store = norm(o); save(); sig = ''; refresh(true); },
  };

  /* ---------- 选中模型 ---------- */
  const sel = new Set();
  const agents = () => (H() && H().agents()) || [];
  const byId = (id) => agents().find(a => a.id === id);
  const nameOf = (a) => a.kind === 'weave'
    ? ('单元 ' + String(a.id).replace(/^wv-/, ''))
    : (a.kind === 'route' ? ('蚕 ' + (a.wormId != null ? a.wormId : a.id)) : String(a.id));
  const iconOf = (a) => a.kind === 'weave' ? '织' : (a.kind === 'route' ? '蚕' : '演');
  const hiddenOf = (a) => a.kind === 'weave' ? !!a.hideSilk : (!!a.hideSilk && !!a.hideBody);
  function setHidden(a, hide) {
    if (a.kind === 'weave') a.hideSilk = !!hide;
    else { a.hideSilk = !!hide; a.hideBody = !!hide; }
  }

  /* ---------- 画布提示（选中框 / 组框 / 吸附参考线） ---------- */
  const ov = $('habSnapOverlay');
  const octx = ov && ov.getContext('2d');
  let guides = [];
  let marquee = null;
  function resize() {
    const wrap = $('habWorldWrap'); const world = $('habWorld');
    if (!wrap || !ov) return;
    if (ov.width !== wrap.clientWidth || ov.height !== wrap.clientHeight) { ov.width = wrap.clientWidth; ov.height = wrap.clientHeight; }
    if (world) { ov.style.left = world.offsetLeft + 'px'; ov.style.top = world.offsetTop + 'px'; }
  }
  function bboxOf(ids) {
    const list = ids.map(byId).filter(a => a && a.kind === 'weave');
    if (!list.length) return null;
    let l = Infinity, r = -Infinity, t = Infinity, b = -Infinity;
    list.forEach(a => { l = Math.min(l, a.x - a.w / 2); r = Math.max(r, a.x + a.w / 2); t = Math.min(t, a.y - a.h / 2); b = Math.max(b, a.y + a.h / 2); });
    return { l, r, t, b };
  }
  function paint() {
    if (!octx || !H()) return;
    resize();
    const v = H().view();
    octx.clearRect(0, 0, ov.width, ov.height);
    const box = bboxOf([...sel]);
    if (box) {
      const x = v.px(box.l), y = v.py(box.t), w = (box.r - box.l) * v.s, h = (box.b - box.t) * v.s;
      octx.save();
      octx.strokeStyle = 'rgba(121,203,182,0.95)';
      octx.lineWidth = 1.4;
      octx.setLineDash([6, 4]);
      octx.strokeRect(x, y, w, h);
      octx.fillStyle = 'rgba(121,203,182,0.10)';
      octx.fillRect(x, y, w, h);
      octx.setLineDash([]);
      octx.fillStyle = 'rgba(121,203,182,0.95)';
      octx.font = '11px ui-monospace,monospace';
      octx.fillText(sel.size > 1 ? ('已选 ' + sel.size + ' 层') : '', x + 6, y - 6);
      octx.restore();
    }
    if (marquee && marquee.armed) {
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
    guides.forEach(g => {
      octx.save();
      octx.strokeStyle = 'rgba(255,140,190,0.95)';
      octx.lineWidth = 1;
      octx.setLineDash([3, 3]);
      octx.beginPath();
      if (g.axis === 'x') { const X = v.px(g.at); octx.moveTo(X, 0); octx.lineTo(X, ov.height); }
      else { const Y = v.py(g.at); octx.moveTo(0, Y); octx.lineTo(ov.width, Y); }
      octx.stroke();
      octx.restore();
    });
  }
  (function loop() { paint(); requestAnimationFrame(loop); })();

  /* ---------- 吸附（拖动结束后处理，屏幕上 8px 手感） ---------- */
  function snapDelta(box, skipIds) {
    const v = H().view();
    const thr = 9 / (v.s || 1);
    const cand = [];
    agents().forEach(a => {
      if (a.kind !== 'weave' || skipIds.has(a.id)) return;
      cand.push(a.x - a.w / 2, a.x, a.x + a.w / 2);
    });
    const candY = [];
    agents().forEach(a => {
      if (a.kind !== 'weave' || skipIds.has(a.id)) return;
      candY.push(a.y - a.h / 2, a.y, a.y + a.h / 2);
    });
    cand.push(0); candY.push(0);
    const mine = [box.l, (box.l + box.r) / 2, box.r];
    const mineY = [box.t, (box.t + box.b) / 2, box.b];
    let bestX = null, bestY = null;
    mine.forEach(m => cand.forEach(c => {
      const d = c - m;
      if (Math.abs(d) <= thr && (!bestX || Math.abs(d) < Math.abs(bestX.d))) bestX = { d, at: c };
    }));
    mineY.forEach(m => candY.forEach(c => {
      const d = c - m;
      if (Math.abs(d) <= thr && (!bestY || Math.abs(d) < Math.abs(bestY.d))) bestY = { d, at: c };
    }));
    // 没有边/中心命中时，试"与旁边两块保持同样的缝"
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
    return { dx: bestX ? bestX.d : 0, dy: bestY ? bestY.d : 0, gx: bestX && bestX.at != null ? bestX.at : null, gy: bestY && bestY.at != null ? bestY.at : null };
  }

  /* ---------- 拖动时整组一起走 ---------- */
  let pending = null, drag = null;
  const worldEl = $('habWorld');
  function baseOf(ids) { const m = {}; ids.forEach(id => { const a = byId(id); if (a) m[id] = { x: a.x, y: a.y }; }); return m; }
  function groupOf(id) { return store.member[id] || null; }
  function moveSet(anchorId) {
    const g = groupOf(anchorId);
    if (g) { const ids = agents().filter(a => store.member[a.id] === g).map(a => a.id); if (ids.length) return ids; }
    if (sel.has(anchorId) && sel.size > 1) return [...sel];
    return [anchorId];
  }
  let own = null;
  function toWorld(ev) {
    const v = H().view();
    const rect = worldEl.getBoundingClientRect();
    const sx = (ev.clientX - rect.left) * (worldEl.width / rect.width);
    const sy = (ev.clientY - rect.top) * (worldEl.height / rect.height);
    return { x: (sx - v.cx) / v.s, y: (sy - v.cy) / v.s };
  }
  function hitWeave(p) {
    let hit = null;
    agents().forEach(a => {
      if (a.kind !== 'weave' || a.locked) return;
      if (Math.abs(p.x - a.x) <= a.w / 2 && Math.abs(p.y - a.y) <= a.h / 2) hit = a;
    });
    return hit;
  }
  function inEditMode() {
    try { const st = H().weaveEditState && H().weaveEditState(); return !!(st && st.agentId); } catch (e) { return false; }
  }
  // 编辑态里，手柄（角/边中点/中心）附近要点就给原生手柄，别抢
  function nearHandle(a, p) {
    const v = H().view();
    const pts = [
      [a.x, a.y],
      [a.x - a.w / 2, a.y - a.h / 2], [a.x + a.w / 2, a.y - a.h / 2],
      [a.x - a.w / 2, a.y + a.h / 2], [a.x + a.w / 2, a.y + a.h / 2],
      [a.x, a.y - a.h / 2], [a.x, a.y + a.h / 2],
      [a.x - a.w / 2, a.y], [a.x + a.w / 2, a.y],
    ];
    return pts.some(q => Math.hypot(q[0] - p.x, q[1] - p.y) * v.s < 22);
  }
  if (worldEl) {
    worldEl.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      pending = { snap: baseOf(agents().map(a => a.id)), t: Date.now() };
      drag = null; own = null;
      const p = toWorld(e);
      const hit = hitWeave(p);
      if (!hit) {
        if (!inEditMode()) marquee = { x0: p.x, y0: p.y, x1: p.x, y1: p.y, add: !!(e.shiftKey || e.ctrlKey || e.metaKey), armed: false };
        return;
      }
      marquee = null;
      if (inEditMode() && nearHandle(hit, p)) return;   // 压在手柄上：交给原生拖拽
      if (inEditMode() && sel.size < 2 && !groupOf(hit.id)) return; // 编辑单块：交给原生
      const ids = moveSet(hit.id);
      own = { ids, base: baseOf(ids), start: p, anchor: hit.id };
    }, true);
    window.addEventListener('pointermove', (e) => {
      if (marquee) {
        const p = toWorld(e);
        marquee.x1 = p.x; marquee.y1 = p.y;
        const v = H().view();
        if (!marquee.armed && (Math.abs(p.x - marquee.x0) * v.s > 6 || Math.abs(p.y - marquee.y0) * v.s > 6)) marquee.armed = true;
        return;
      }
      if (own) {
        const p = toWorld(e);
        const dx = p.x - own.start.x, dy = p.y - own.start.y;
        own.ids.forEach(id => { const a = byId(id); const b = own.base[id]; if (a && b && !a.locked) { a.x = b.x + dx; a.y = b.y + dy; } });
        const box = bboxOf(own.ids);
        if (box && !(e.ctrlKey || e.metaKey)) {
          const sn = snapDelta(box, new Set(own.ids));
          if (sn.dx || sn.dy) own.ids.forEach(id => { const a = byId(id); if (a && !a.locked) { a.x += sn.dx; a.y += sn.dy; } });
          guides = [];
          if (sn.gx != null) guides.push({ axis: 'x', at: sn.gx });
          if (sn.gy != null) guides.push({ axis: 'y', at: sn.gy });
        } else guides = [];
        return;
      }
      if (!pending || drag === null) {
        if (!pending) return;
        if (!e.buttons) { pending = null; return; }
        // 找出"动得最多"的那一层 = 正在被拖的层
        let best = null;
        Object.keys(pending.snap).forEach(id => {
          const a = byId(id); const s = pending.snap[id];
          if (!a || a.locked) return;
          const d = Math.abs(a.x - s.x) + Math.abs(a.y - s.y);
          if (d > 1.5 && (!best || d > best.d)) best = { id, d };
        });
        if (!best) return;
        const ids = moveSet(best.id);
        drag = { anchor: best.id, ids, base: baseOf(ids), delta: 0 };
      }
      if (!drag) return;
      const a = byId(drag.anchor);
      if (!a) { drag = null; return; }
      const dx0 = a.x - drag.base[drag.anchor].x;
      const dy0 = a.y - drag.base[drag.anchor].y;
      // 其它成员跟齐
      drag.ids.forEach(id => {
        const b = drag.base[id], m = byId(id);
        if (!m || id === drag.anchor || m.locked) return;
        m.x = b.x + dx0; m.y = b.y + dy0;
      });
      // 吸附：按整组外包框对齐别人的边/中心与场地轴
      const box = bboxOf(drag.ids);
      if (box && !(e.ctrlKey || e.metaKey)) {
        const s = snapDelta(box, new Set(drag.ids));
        if (s.dx || s.dy) {
          drag.ids.forEach(id => { const m = byId(id); if (m && !m.locked) { m.x += s.dx; m.y += s.dy; } });
          a.cache = a.cache;
        }
        guides = [];
        if (s.gx != null) guides.push({ axis: 'x', at: s.gx });
        if (s.gy != null) guides.push({ axis: 'y', at: s.gy });
      } else { guides = []; }
    });
    window.addEventListener('pointerup', (e) => {
      if (marquee) {
        try { const p = toWorld(e); marquee.x1 = p.x; marquee.y1 = p.y; } catch (err) {}
      }
      if (marquee && marquee.armed) marqueeSelect();
      else { if (marquee && !marquee.add && sel.size) { sel.clear(); sig = ''; refresh(true); } marquee = null; }
      pending = null; drag = null; own = null; guides = []; sig = '';
    }, true);
  }


  /* ---------- 框选 ---------- */
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
  /* ---------- 键盘微调 ---------- */
  window.addEventListener('keydown', (e) => {
    if (!sel.size) return;
    const tag = (e.target && e.target.tagName) || '';
    if (/INPUT|TEXTAREA|SELECT/.test(tag) || (e.target && e.target.isContentEditable)) return;
    const step = e.shiftKey ? 10 : 1;
    let dx = 0, dy = 0;
    if (e.key === 'ArrowLeft') dx = -step;
    else if (e.key === 'ArrowRight') dx = step;
    else if (e.key === 'ArrowUp') dy = -step;
    else if (e.key === 'ArrowDown') dy = step;
    else return;
    sel.forEach(id => { const a = byId(id); if (a && !a.locked) { a.x += dx; a.y += dy; } });
    e.preventDefault();
  });

  /* ---------- 列表 ---------- */
  let sig = '';
  function orderKey(a) { const i = store.order.indexOf(a.id); return i < 0 ? 9999 : i; }
  function rowsFor(list) { return list.slice().sort((p, q) => orderKey(p) - orderKey(q)); }

  function metaOf(a) {
    if (a.kind === 'weave') {
      const w = Math.round(a.w || 0), h = Math.round(a.h || 0);
      const worms = Math.round(a.worms || 0);
      return w + '×' + h + (worms ? ' · ' + worms + ' 蚕/格' : '');
    }
    if (a.kind === 'route') return (Math.round(a.scale * 100) / 100) + '× · ' + a.route.length + ' 点';
    return a.mode || '';
  }
  function rowHTML(a, gid) {
    const off = hiddenOf(a);
    return '<div class="lay-row' + (off ? ' dim' : '') + (sel.has(a.id) ? ' on' : '') + '" data-agent="' + a.id + '">' +
      '<input type="checkbox" class="lay-chk" data-pick="' + a.id + '"' + (sel.has(a.id) ? ' checked' : '') + '>' +
      '<canvas class="lay-thumb" width="40" height="40" data-thumb="' + a.id + '"></canvas>' +
      '<span class="lay-txt"><button type="button" class="lay-name" title="选中这一层" data-focus="' + a.id + '">' + iconOf(a) + ' ' + nameOf(a) + '</button>' +
      '<i class="lay-meta">' + metaOf(a) + '</i></span>' +
      '<button type="button" class="lay-mini" data-eye="' + a.id + '" title="显示／隐藏这一层">' + (off ? '隐' : '显') + '</button>' +
      '<button type="button" class="lay-mini' + (a.locked ? ' on' : '') + '" data-menu="' + a.id + '" title="更多操作">⋯</button>' +
      '</div>';
  }

  function render() {
    const list = agents();
    Object.keys(store.member).forEach(id => { if (!list.some(a => a.id === id)) delete store.member[id]; });
    if (!list.length) { tree.innerHTML = '<div class="hab-note">场地里还没有任何层：放一块织网单元，或拖一只蚕进来。</div>'; return; }
    const groupedIds = new Set();
    const out = [];
    store.groups.forEach(g => {
      const members = rowsFor(list.filter(a => store.member[a.id] === g.id));
      if (!members.length) return;
      members.forEach(a => groupedIds.add(a.id));
      const allOff = members.every(hiddenOf);
      out.push('<div class="lay-group' + (sel.size && members.every(a => sel.has(a.id)) ? ' on' : '') + '" data-group="' + g.id + '">' +
        '<button type="button" class="lay-caret" data-open="' + g.id + '">' + (g.open ? '▾' : '▸') + '</button>' +
        '<span class="lay-gicon">组</span>' +
        '<button type="button" class="lay-gname" data-gsel="' + g.id + '">' + g.name + '</button>' +
        '<span class="lay-count">' + members.length + '</span>' +
        '<button type="button" class="lay-mini" data-geye="' + g.id + '">' + (allOff ? '隐' : '显') + '</button>' +
        '<button type="button" class="lay-mini" data-gren="' + g.id + '">改</button>' +
        '<button type="button" class="lay-mini" data-gdel="' + g.id + '">✕</button>' +
        '</div>');
      if (g.open) members.forEach(a => out.push(rowHTML(a, g.id)));
    });
    const free = rowsFor(list.filter(a => !groupedIds.has(a.id)));
    if (free.length) {
      out.push('<div class="lay-group plain"><span class="lay-caret" style="visibility:hidden">▸</span><span class="lay-gname">未编组</span><span class="lay-count">' + free.length + '</span></div>');
      free.forEach(a => out.push(rowHTML(a, null)));
    }
    tree.innerHTML = out.join('');
    paintThumbs();
  }

  function refresh(force) {
    const s = agents().map(a => a.id + (hiddenOf(a) ? '0' : '1') + (a.locked ? 'L' : '') + Math.round(a.x) + ',' + Math.round(a.y)).join('|') + '#' + [...sel].join(',');
    if (!force && s === sig) return;
    sig = s;
    render();
  }

  /* ---------- 列表交互 ---------- */

  /* ---------- 行内「⋯」菜单 ---------- */
  let menuEl = null;
  function closeMenu() { if (menuEl) { menuEl.remove(); menuEl = null; } }
  function openMenu(id, x, y) {
    closeMenu();
    const a = byId(id); if (!a) return;
    menuEl = document.createElement('div');
    menuEl.className = 'lay-menu';
    const items = [];
    items.push([a.locked ? '解锁这一层' : '锁定这一层（不能拖）', () => { a.locked = !a.locked; }]);
    items.push(['上移一层', () => { shiftOrder(id, -1); }]);
    items.push(['下移一层', () => { shiftOrder(id, 1); }]);
    if (store.member[id]) items.push(['移出所在组', () => { delete store.member[id]; save(); }]);
    if (a.kind === 'weave') items.push(['删掉这一块', () => { if (confirm('删掉这一块织网单元？')) { if (window.__weaveHooks && window.__weaveHooks.deleteUnit) window.__weaveHooks.deleteUnit(a.id); sel.delete(a.id); } }]);
    items.forEach(([label, fn], i) => {
      const b = document.createElement('button');
      b.type = 'button'; b.textContent = label;
      if (i === items.length - 1 && a.kind === 'weave') b.className = 'danger';
      b.addEventListener('click', (ev) => { ev.stopPropagation(); fn(); closeMenu(); sig = ''; render(); });
      menuEl.appendChild(b);
    });
    (document.getElementById('habitat') || document.body).appendChild(menuEl);
    const w = menuEl.offsetWidth, h = menuEl.offsetHeight;
    menuEl.style.left = Math.min(window.innerWidth - w - 8, x) + 'px';
    menuEl.style.top = Math.min(window.innerHeight - h - 8, y) + 'px';
  }
  function shiftOrder(id, dir) {
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
  }
  document.addEventListener('pointerdown', (e) => {
    if (menuEl && !menuEl.contains(e.target) && !(e.target.getAttribute && e.target.getAttribute('data-menu'))) closeMenu();
  }, true);
  tree.addEventListener('click', (e) => {
    const t = e.target; const at = (k) => t.getAttribute && t.getAttribute(k);
    if (at('data-menu')) {
      const r = t.getBoundingClientRect();
      openMenu(at('data-menu'), r.left - 150, r.bottom + 6);
      return;
    }
    const focus = at('data-focus');
    if (focus) {
      sel.clear(); sel.add(focus);
      const card = document.querySelector('#habAgents .agent-card[data-id="' + focus + '"]');
      if (card) card.click();
      refresh(true); return;
    }
    if (at('data-gsel')) {
      const gid = at('data-gsel');
      sel.clear();
      agents().filter(a => store.member[a.id] === gid).forEach(a => sel.add(a.id));
      refresh(true); return;
    }
    if (at('data-geye')) {
      const gid = at('data-geye');
      const mem = agents().filter(a => store.member[a.id] === gid);
      const anyOn = mem.some(a => !hiddenOf(a));
      mem.forEach(a => setHidden(a, anyOn));
      sig = ''; render(); return;
    }
    if (at('data-eye')) { const a = byId(at('data-eye')); if (a) { setHidden(a, !hiddenOf(a)); sig = ''; render(); } return; }
    if (at('data-lock')) { const a = byId(at('data-lock')); if (a) { a.locked = !a.locked; sig = ''; render(); } return; }
    if (at('data-open')) { const g = store.groups.find(x => x.id === at('data-open')); if (g) { g.open = !g.open; save(); render(); } return; }
    if (at('data-gren')) { const g = store.groups.find(x => x.id === at('data-gren')); const v = g && prompt('这组叫什么？', g.name); if (g && v && v.trim()) { g.name = v.trim().slice(0, 24); save(); render(); } return; }
    if (at('data-gdel')) {
      const gid = at('data-gdel');
      if (!confirm('解散这一组？（层不会被删掉，只是回到未编组）')) return;
      Object.keys(store.member).forEach(id => { if (store.member[id] === gid) delete store.member[id]; });
      store.groups = store.groups.filter(g => g.id !== gid);
      save(); sig = ''; render(); return;
    }
    if (at('data-del')) {
      const id = at('data-del');
      if (!confirm('删掉这一块织网单元？')) return;
      if (window.__weaveHooks && window.__weaveHooks.deleteUnit) window.__weaveHooks.deleteUnit(id);
      sel.delete(id); sig = ''; render(); return;
    }
    if (at('data-up') || at('data-down')) {
      const id = at('data-up') || at('data-down');
      const dir = at('data-up') ? -1 : 1;
      const list = agents().map(a => a.id);
      list.forEach(x => { if (store.order.indexOf(x) < 0) store.order.push(x); });
      shiftOrder(id, dir);
      save(); sig = ''; render(); return;
    }
  });
  tree.addEventListener('change', (e) => {
    const p = e.target.getAttribute && e.target.getAttribute('data-pick');
    if (!p) return;
    if (e.target.checked) sel.add(p); else sel.delete(p);
    refresh(true);
  });

  function btn(id, fn) { const b = $(id); if (b) b.addEventListener('click', fn); }
  btn('habLayerGroup', () => {
    if (sel.size < 1) { alert('先在列表里勾上要编组的层（两层以上更像 PS 的组）。'); return; }
    const v = prompt('新组叫什么？', '组 ' + (store.groups.length + 1));
    if (v === null) return;
    const g = { id: 'g' + Date.now().toString(36), name: (v || '组').trim().slice(0, 24) || '组', open: true };
    store.groups.push(g);
    sel.forEach(id => { store.member[id] = g.id; });
    save(); sig = ''; render();
  });
  btn('habLayerUngroup', () => {
    if (!sel.size) { alert('先勾选要解散的层。'); return; }
    sel.forEach(id => { delete store.member[id]; });
    save(); sig = ''; render();
  });
  btn('habLayerMerge', () => {
    if (!sel.size) { alert('先勾选要并到一组里的层。'); return; }
    let gid = null;
    sel.forEach(id => { if (store.member[id]) gid = store.member[id]; });
    if (!gid) { alert('这些层都还没编组，直接点「编组所选」就行。'); return; }
    sel.forEach(id => { store.member[id] = gid; });
    save(); sig = ''; render();
  });
  btn('habLayerClear', () => { store.groups.forEach(g => { g.open = true; }); save(); render(); });

  /* ---------- 对齐 / 等距 ---------- */
  function selAgents() { return [...sel].map(byId).filter(Boolean); }
  function applyAlign(kind) {
    const list = selAgents();
    if (list.length < 2) { alert('先勾选两层以上（或点一个组名）再对齐。'); return; }
    const box = bboxOf(list.map(a => a.id));
    list.forEach(a => {
      if (a.kind !== 'weave') return;
      if (kind === 'l') a.x = box.l + a.w / 2;
      if (kind === 'cx') a.x = (box.l + box.r) / 2;
      if (kind === 'r') a.x = box.r - a.w / 2;
      if (kind === 't') a.y = box.t + a.h / 2;
      if (kind === 'cy') a.y = (box.t + box.b) / 2;
      if (kind === 'b') a.y = box.b - a.h / 2;
    });
    if (kind === 'dx' || kind === 'dy') {
      const ws = list.filter(a => a.kind === 'weave');
      if (ws.length < 2) return;
      if (kind === 'dx') {
        ws.sort((p, q) => p.x - q.x);
        const first = ws[0], last = ws[ws.length - 1];
        const total = last.x - first.x;
        ws.forEach((a, i) => { a.x = first.x + total * (i / (ws.length - 1)); });
      } else {
        ws.sort((p, q) => p.y - q.y);
        const first = ws[0], last = ws[ws.length - 1];
        const total = last.y - first.y;
        ws.forEach((a, i) => { a.y = first.y + total * (i / (ws.length - 1)); });
      }
    }
    sig = ''; refresh(true);
  }
  document.querySelectorAll('[data-align]').forEach(b => b.addEventListener('click', () => applyAlign(b.dataset.align)));

  /* ---------- 阵列复制 ---------- */
  btn('habArrayGo', () => {
    const one = sel.size === 1 ? byId([...sel][0]) : null;
    if (!one || one.kind !== 'weave') { alert('阵列复制一次只对一块织网单元生效：先在列表里只勾选一块。'); return; }
    const n = Math.max(1, Math.min(20, parseInt(($('habArrayN') || {}).value, 10) || 1));
    const m = Math.max(1, Math.min(20, parseInt(($('habArrayM') || {}).value, 10) || 1));
    if (n * m <= 1) return;
    const gap = Number(($('habArrayGap') || {}).value || 12);
    const sx = one.w + gap, sy = one.h + gap;
    const H0 = H();
    for (let j = 0; j < m; j++) {
      for (let i = 0; i < n; i++) {
        if (i === 0 && j === 0) continue;
        const before = H0.agents().filter(a => a.kind === 'weave').length;
        H0.addWeave({});
        const l = H0.agents().filter(a => a.kind === 'weave');
        if (l.length <= before) continue;
        const u = l[l.length - 1];
        ['w', 'h', 'coverage', 'shape', 'worms', 'seed', 'duration', 'wallAff', 'tileField', 'tone', 'gap', 'strata', 'profile', 'outline'].forEach(k => { if (one[k] !== undefined) u[k] = one[k]; });
        u.custom = JSON.parse(JSON.stringify(one.custom || { walls: {}, paths: {}, shapes: {} }));
        u.x = one.x + i * sx;
        u.y = one.y + j * sy;
        u.tileField = false;
        if (u.cache && u.cache.clear) u.cache.clear();
        H0.buildWeave(u);
      }
    }
    sig = ''; refresh(true);
  });


  /* ---------- 缩略图：从主画布裁剪 ---------- */
  function paintThumbs() {
    const world = $('habWorld');
    if (!world || !H()) return;
    const v = H().view();
    const cw = world.width, chh = world.height;
    const rect = world.getBoundingClientRect();
    const kx = cw / (rect.width || 1), ky = chh / (rect.height || 1);
    document.querySelectorAll('#habLayerTree canvas[data-thumb]').forEach(cv => {
      const a = byId(cv.getAttribute('data-thumb'));
      const ctx = cv.getContext('2d');
      ctx.clearRect(0, 0, cv.width, cv.height);
      if (!a || a.kind !== 'weave') { ctx.fillStyle = 'rgba(255,255,255,0.06)'; ctx.fillRect(0, 0, cv.width, cv.height); return; }
      ctx.fillStyle = '#05080a';
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
      ctx.strokeRect(0.5, 0.5, cv.width - 1, cv.height - 1);
    });
  }
  setInterval(() => { const p = $('habRight'); if (!document.hidden && p && p.offsetParent) paintThumbs(); }, 2500);
  /* ---------- 与主界面同步 ---------- */
  const box0 = $('habAgents');
  if (box0 && window.MutationObserver) new MutationObserver(() => refresh(false)).observe(box0, { childList: true, subtree: true });
  setInterval(() => { const hab = $('habitat'); if (!document.hidden && hab && hab.offsetParent) refresh(false); }, 500);
  refresh(true);
  window.__layerSel = {
    ids: () => [...sel],
    size: () => sel.size,
    set: (ids) => { sel.clear(); (ids || []).forEach(id => sel.add(id)); sig = ''; refresh(true); },
    clear: () => { if (sel.size) { sel.clear(); sig = ''; refresh(true); } },
    bbox: () => bboxOf([...sel]),
    editing: () => inEditMode(),
  };
})();
