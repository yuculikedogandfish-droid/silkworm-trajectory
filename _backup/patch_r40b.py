# -*- coding: utf-8 -*-
import io

MOD = r"H:\tool\silkworm-trajectory\_backup\r39_module.js"
P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(MOD, encoding="utf-8").read()

# 行按钮精简为「显 / ⋯」，其余动作进右键式小菜单
old = """      '<button type="button" class="lay-mini" data-eye="' + a.id + '" title="显示／隐藏这一层">' + (off ? '隐' : '显') + '</button>' +
      '<button type="button" class="lay-mini' + (a.locked ? ' on' : '') + '" data-lock="' + a.id + '" title="锁定后不能拖动">' + (a.locked ? '锁' : '开') + '</button>' +
      (a.kind === 'weave'
        ? '<button type="button" class="lay-mini" data-up="' + a.id + '" title="上移一层">↑</button><button type="button" class="lay-mini" data-down="' + a.id + '" title="下移一层">↓</button><button type="button" class="lay-mini" data-del="' + a.id + '" title="删掉这一层">✕</button>'
        : '<button type="button" class="lay-mini" data-up="' + a.id + '">↑</button><button type="button" class="lay-mini" data-down="' + a.id + '">↓</button>') +
      '</div>';"""
new = """      '<button type="button" class="lay-mini" data-eye="' + a.id + '" title="显示／隐藏这一层">' + (off ? '隐' : '显') + '</button>' +
      '<button type="button" class="lay-mini' + (a.locked ? ' on' : '') + '" data-menu="' + a.id + '" title="更多操作">⋯</button>' +
      '</div>';"""
assert s.count(old) == 1
s = s.replace(old, new)

# 菜单：一个小浮层
menu_code = """
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
    document.body.appendChild(menuEl);
    const w = menuEl.offsetWidth, h = menuEl.offsetHeight;
    menuEl.style.left = Math.min(window.innerWidth - w - 8, x) + 'px';
    menuEl.style.top = Math.min(window.innerHeight - h - 8, y) + 'px';
  }
  function shiftOrder(id, dir) {
    const list = agents().map(a => a.id);
    list.forEach(x => { if (store.order.indexOf(x) < 0) store.order.push(x); });
    const i = store.order.indexOf(id), j = i + dir;
    if (i >= 0 && j >= 0 && j < store.order.length) { const t2 = store.order[i]; store.order[i] = store.order[j]; store.order[j] = t2; save(); }
  }
  document.addEventListener('pointerdown', (e) => {
    if (menuEl && !menuEl.contains(e.target) && !(e.target.getAttribute && e.target.getAttribute('data-menu'))) closeMenu();
  }, true);
"""
anchor = """  tree.addEventListener('click', (e) => {"""
assert s.count(anchor) == 1
s = s.replace(anchor, menu_code + anchor)

# 菜单按钮点击拦截（放在 click 处理最前）
old_click = """    const t = e.target; const at = (k) => t.getAttribute && t.getAttribute(k);
    const focus = at('data-focus');"""
new_click = """    const t = e.target; const at = (k) => t.getAttribute && t.getAttribute(k);
    if (at('data-menu')) {
      const r = t.getBoundingClientRect();
      openMenu(at('data-menu'), r.left - 150, r.bottom + 6);
      return;
    }
    const focus = at('data-focus');"""
assert s.count(old_click) == 1
s = s.replace(old_click, new_click)

# 旧的 up/down/del 分支保留（菜单外不再有按钮，不影响）
io.open(MOD, "w", encoding="utf-8").write(s)

h = io.open(P, encoding="utf-8").read()
i = h.find("/* ===== r39 个体与图层合并"); st = h.rfind("<script>", 0, i); en = h.find("</script>", i)
h = h[:st] + s.rstrip() + h[en + len("</script>"):]

# 识别条位置：贴到画布左上角，不压左栏
h = h.replace(".hab-rec-bar{position:absolute;left:12px;top:54px;z-index:9;width:min(620px,calc(100% - 200px));padding:0}",
              ".hab-rec-bar{position:absolute;left:264px;top:52px;z-index:9;width:min(560px,calc(100% - 560px));padding:0}", 1)
h = h.replace(".lay-thumb{width:26px;height:26px;flex:0 0 26px",
              ".lay-thumb{width:28px;height:28px;flex:0 0 28px", 1)
h = h.replace(".lay-gicon{width:26px;flex:0 0 26px", ".lay-gicon{width:28px;flex:0 0 28px", 1)

# 菜单样式
h = h.replace(""".lay-mini.on{background:rgba(232,201,138,0.25)}""",
""".lay-mini.on{background:rgba(232,201,138,0.25)}
.lay-menu{position:fixed;z-index:1000;min-width:160px;padding:4px;background:#0e1614;border:1px solid #3a4a44;border-radius:8px;box-shadow:0 10px 24px rgba(0,0,0,.5)}
.lay-menu button{display:block;width:100%;text-align:left;padding:6px 9px;margin:2px 0;font-size:12px;background:#16201d;border:1px solid #2b3a35;border-radius:5px;color:#e7efeb;cursor:pointer}
.lay-menu button:hover{background:#1d2a26;border-color:#4d6a60}
.lay-menu button.danger{color:#ffb3a3;border-color:#5a3330}""", 1)
io.open(P, "w", encoding="utf-8").write(h)
print("r40b ok", len(h))
