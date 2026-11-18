<script>
/* ===== r38 拖拽上传 + 图层组（PS 式）——全部独立，不改既有函数 ===== */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const H = () => window.__studioHabitat;

  /* ---------- 1) 拖拽上传图片 ---------- */
  const drop = $('habRecDrop');
  const fileEl = $('habRecFile');
  const dropText = $('habRecDropText');
  if (drop && fileEl) {
    const hi = (on) => drop.classList.toggle('hi', !!on);
    ['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, (e) => { e.preventDefault(); e.stopPropagation(); hi(true); }));
    ['dragleave', 'dragend'].forEach(ev => drop.addEventListener(ev, (e) => { e.preventDefault(); hi(false); }));
    drop.addEventListener('drop', (e) => {
      e.preventDefault(); e.stopPropagation(); hi(false);
      const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (!f) return;
      if (!/^image\//.test(f.type)) { const n = $('habRecImageNote'); if (n) n.textContent = '这不是图片文件，换一张 png / jpg。'; return; }
      if (dropText) dropText.textContent = '已接收：' + f.name;
      const note = $('habRecImageNote');
      if (note) note.textContent = '读图中：' + f.name;
      try {
        window.__imgRec.readImage(f, () => {
          const st = window.__imgRec.state;
          if (note) note.textContent = '已载入 ' + st.img.w + '×' + st.img.h + '（缩放后）。点「识别并预览」。';
        });
      } catch (err) { if (note) note.textContent = '读图出错：' + err.message; }
    });
    // 整个框点一下也能选文件
    drop.addEventListener('click', (e) => { if (e.target !== fileEl) fileEl.click(); });
    fileEl.addEventListener('change', () => {
      const f = fileEl.files && fileEl.files[0];
      if (f && dropText) dropText.textContent = '已接收：' + f.name;
    });
  }

  /* ---------- 2) 图层面板（组 / 层 / 眼睛 / 编组） ---------- */
  const tree = $('habLayerTree');
  if (!tree) return;
  const KEY = 'silkworm-habitat-layer-groups/v1';
  let store = { groups: [], member: {} };
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) { const o = JSON.parse(raw); if (o && Array.isArray(o.groups)) store = { groups: o.groups, member: o.member || {} }; }
  } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {} };
  const picked = new Set();
  let rev = 0;
  let sigLast = '';

  const nameOf = (a) => a.kind === 'weave' ? ('织网单元 ' + a.id) : (a.kind === 'route' ? ('蚕 ' + a.wormId) : String(a.id));
  const typeOf = (a) => a.kind === 'weave' ? '织' : (a.kind === 'route' ? '蚕' : '演');
  const hiddenOf = (a) => a.kind === 'weave' ? !!a.hideSilk : (!!a.hideSilk && !!a.hideBody);
  const toggleHide = (a, hide) => {
    if (a.kind === 'weave') a.hideSilk = !!hide;
    else { a.hideSilk = !!hide; a.hideBody = !!hide; }
  };

  function agents() { const h = H(); return (h && h.agents()) || []; }

  function rowLayer(a, groupId) {
    const off = hiddenOf(a);
    return '<div class="lay-row' + (off ? ' dim' : '') + '" data-agent="' + a.id + '">' +
      '<label class="lay-chk"><input type="checkbox" data-pick="' + a.id + '"' + (picked.has(a.id) ? ' checked' : '') + '></label>' +
      '<span class="lay-icon">' + typeOf(a) + '</span>' +
      '<button type="button" class="lay-name" data-focus="' + a.id + '">' + nameOf(a) + '</button>' +
      '<button type="button" class="lay-eye" data-eye="' + a.id + '" title="' + (off ? '显示这一层' : '隐藏这一层') + '">' + (off ? '隐' : '显') + '</button>' +
      '</div>';
  }

  function render() {
    const list = agents();
    const rows = [];
    // 清理已经不存在的成员
    Object.keys(store.member).forEach(id => { if (!list.some(a => a.id === id)) delete store.member[id]; });
    const grouped = [];
    store.groups.forEach((g, gi) => {
      const members = list.filter(a => store.member[a.id] === g.id);
      if (!members.length) return;
      grouped.push(...members.map(a => a.id));
      const allOff = members.every(hiddenOf);
      rows.push('<div class="lay-group" data-group="' + g.id + '">' +
        '<button type="button" class="lay-caret" data-open="' + g.id + '">' + (g.open ? '▾' : '▸') + '</button>' +
        '<button type="button" class="lay-gname" data-rename="' + g.id + '">' + g.name + '</button>' +
        '<span class="lay-count">' + members.length + '</span>' +
        '<button type="button" class="lay-eye" data-geye="' + g.id + '" title="整组显示／隐藏">' + (allOff ? '隐' : '显') + '</button>' +
        '</div>');
      if (g.open) members.forEach(a => rows.push(rowLayer(a, g.id)));
    });
    const free = list.filter(a => !grouped.includes(a.id));
    if (free.length) {
      rows.push('<div class="lay-group plain"><span class="lay-caret" style="visibility:hidden">▸</span><span class="lay-gname">未编组</span><span class="lay-count">' + free.length + '</span></div>');
      free.forEach(a => rows.push(rowLayer(a, null)));
    }
    tree.innerHTML = rows.join('') || '<div class="hab-note">场地里还没有任何层。</div>';
  }

  function refresh(force) {
    const list = agents();
    const sig = list.map(a => a.id + (hiddenOf(a) ? '0' : '1')).join('|') + '#' + rev + '#' + list.length;
    if (!force && sig === sigLast) return;
    sigLast = sig;
    render();
  }

  tree.addEventListener('click', (e) => {
    const t = e.target;
    const focus = t.getAttribute && t.getAttribute('data-focus');
    if (focus) {
      const card = document.querySelector('#habAgents .agent-card[data-id="' + focus + '"]');
      if (card) card.click();
      return;
    }
    const eye = t.getAttribute && t.getAttribute('data-eye');
    if (eye) {
      const a = agents().find(x => x.id === eye);
      if (a) { toggleHide(a, !hiddenOf(a)); rev++; render(); }
      return;
    }
    const geye = t.getAttribute && t.getAttribute('data-geye');
    if (geye) {
      const g = store.groups.find(x => x.id === geye);
      const members = agents().filter(a => store.member[a.id] === geye);
      const allOff = members.length && members.every(hiddenOf);
      members.forEach(a => toggleHide(a, !allOff));
      rev++; save(); render();
      return;
    }
    const open = t.getAttribute && t.getAttribute('data-open');
    if (open) {
      const g = store.groups.find(x => x.id === open);
      if (g) { g.open = !g.open; save(); render(); }
      return;
    }
    const rn = t.getAttribute && t.getAttribute('data-rename');
    if (rn) {
      const g = store.groups.find(x => x.id === rn);
      if (g) {
        const v = prompt('这组叫什么？', g.name);
        if (v && v.trim()) { g.name = v.trim().slice(0, 24); save(); render(); }
      }
    }
  });

  tree.addEventListener('change', (e) => {
    const p = e.target.getAttribute && e.target.getAttribute('data-pick');
    if (!p) return;
    if (e.target.checked) picked.add(p); else picked.delete(p);
  });

  function btn(id, fn) { const b = $(id); if (b) b.addEventListener('click', fn); }

  btn('habLayerGroup', () => {
    if (picked.size < 2) { alert('先在图层前勾上两个或更多，再点「编组所选」。'); return; }
    const name = prompt('新组叫什么？', '组 ' + (store.groups.length + 1));
    if (name === null) return;
    const g = { id: 'g' + Date.now().toString(36), name: (name || '组').trim().slice(0, 24) || '组', open: true };
    store.groups.push(g);
    picked.forEach(id => { store.member[id] = g.id; });
    picked.clear();
    rev++; save(); render();
  });

  btn('habLayerUngroup', () => {
    let n = 0;
    if (picked.size) { picked.forEach(id => { if (store.member[id]) { delete store.member[id]; n++; } }); }
    else { n = Object.keys(store.member).length; store.member = {}; }
    picked.clear();
    store.groups = store.groups.filter((g, i) => true);
    rev++; save(); render();
    if (!n) alert('现在没有编组中的层。先勾选层，再点「解散组」。');
  });

  btn('habLayerClear', () => {
    store.groups.forEach(g => { g.open = true; });
    save(); render();
  });

  const agentsBox = document.getElementById('habAgents');
  if (agentsBox && window.MutationObserver) {
    new MutationObserver(() => refresh(false)).observe(agentsBox, { childList: true, subtree: true });
  }
  setInterval(() => refresh(false), 600);
  refresh(true);
})();
</script>
