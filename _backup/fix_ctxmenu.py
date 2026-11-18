p = r"docs\index.html"
s = open(p, encoding="utf-8").read()
def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)

rep("""  const ctxMenuEl = document.getElementById('habCtxMenu');
  function hideCtxMenu() { if (ctxMenuEl) ctxMenuEl.style.display = 'none'; }""",
"""  // 菜单节点在脚本之后才被解析，这里必须每次现查，不能提前缓存
  const getCtxMenu = () => document.getElementById('habCtxMenu');
  function hideCtxMenu() { const el = getCtxMenu(); if (el) el.style.display = 'none'; }""")

rep("""  function showCtxMenu(clientX, clientY, items) {
    if (!ctxMenuEl) return;
    ctxMenuEl.innerHTML = '<div class="ctx-title">这一格：</div>';""",
"""  function showCtxMenu(clientX, clientY, items) {
    const el = getCtxMenu();
    if (!el) return;
    el.innerHTML = '<div class="ctx-title">这一格：</div>';""")

rep("""      ctxMenuEl.appendChild(b);
    });
    ctxMenuEl.style.display = 'block';
    ctxMenuEl.style.left = Math.max(8, Math.min(clientX, window.innerWidth - 224)) + 'px';
    ctxMenuEl.style.top = Math.max(8, Math.min(clientY, window.innerHeight - 300)) + 'px';""",
"""      el.appendChild(b);
    });
    el.style.display = 'block';
    el.style.left = Math.max(8, Math.min(clientX, window.innerWidth - 224)) + 'px';
    el.style.top = Math.max(8, Math.min(clientY, window.innerHeight - 300)) + 'px';""")

rep("""  window.addEventListener('pointerdown', (ev) => {
    if (ctxMenuEl && ctxMenuEl.style.display === 'block' && !ctxMenuEl.contains(ev.target)) hideCtxMenu();
  }, true);""",
"""  window.addEventListener('pointerdown', (ev) => {
    const el = getCtxMenu();
    if (el && el.style.display === 'block' && !el.contains(ev.target)) hideCtxMenu();
  }, true);""")
open(p, "w", encoding="utf-8").write(s)
print('lazy menu ok')
