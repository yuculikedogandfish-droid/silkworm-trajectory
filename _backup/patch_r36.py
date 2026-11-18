# -*- coding: utf-8 -*-
"""r36：删除整块织网单元 —— 右键菜单 + 右栏按钮"""
import io

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:70])
    s = s.replace(a, b)


# 1. 删除函数
rep("""    // 编辑相关函数只活在这个面板闭包里，而场地画布的指针事件在更外层：""",
"""    function deleteWeaveUnit(a) {
      if (!a || a.kind !== 'weave') { toast('先点中一块织网单元，再删除。', 'err'); return; }
      pushUndo();
      if (habitat.weaveEdit && habitat.weaveEdit.agentId === a.id) exitWeaveEdit();
      const label = a.id;
      habitat.agents = habitat.agents.filter(x => x.id !== a.id);
      if (habitat.selected === a.id) habitat.selected = null;
      habitat.hoverHandle = null;
      if (a.cache && a.cache.clear) a.cache.clear();
      if (typeof renderList === 'function') renderList();
      const rest = habitat.agents.filter(x => x.kind === 'weave').length;
      toast('删掉了这一块织网单元（' + label + '）。还剩 ' + rest + ' 块。按 Ctrl+Z 可以撤回。', 'ok');
    }
    // 编辑相关函数只活在这个面板闭包里，而场地画布的指针事件在更外层：""")

rep("""      deleteAt: (p) => (typeof weaveDeleteAt === 'function' ? weaveDeleteAt(p) : false),""",
"""      deleteAt: (p) => (typeof weaveDeleteAt === 'function' ? weaveDeleteAt(p) : false),
      deleteUnit: (id) => deleteWeaveUnit(habitat.agents.find(x => x.id === id) || chosen()),""")

# 2. 右键菜单项
rep("""      { label: '退出编辑', run: () => { if (window.__weaveHooks && window.__weaveHooks.exit) window.__weaveHooks.exit(); } },""",
"""      { label: '删除这一块织网单元（整块消失）', danger: true, run: () => {
          if (window.__weaveHooks && window.__weaveHooks.deleteUnit) window.__weaveHooks.deleteUnit(a.id);
        } },
      { label: '退出编辑', run: () => { if (window.__weaveHooks && window.__weaveHooks.exit) window.__weaveHooks.exit(); } },""")

# 3. 右栏按钮（跟着「重新织」放，一眼能看到）
rep("""        <div class="row"><button type="button" id="habWeaveRebuild">重新织</button></div>""",
"""        <div class="row"><button type="button" id="habWeaveRebuild">重新织</button><button type="button" id="habDeleteUnit" style="border-color:#8a4141;color:#ffbdbd">删除这一块</button></div>""")

# 4. 按钮事件（挂在「移除该个体」旁边，逻辑同一份）
rep("""    document.getElementById('habAdjDrop').addEventListener('click', () => {""",
"""    const habDeleteUnitBtn = document.getElementById('habDeleteUnit');
    if (habDeleteUnitBtn) habDeleteUnitBtn.addEventListener('click', () => {
      const a = (habitat.weaveEdit && habitat.weaveEdit.agentId)
        ? habitat.agents.find(x => x.id === habitat.weaveEdit.agentId)
        : chosen();
      deleteWeaveUnit(a);
    });
    document.getElementById('habAdjDrop').addEventListener('click', () => {""")

io.open(P, "w", encoding="utf-8").write(s)
print("r36 patched")
