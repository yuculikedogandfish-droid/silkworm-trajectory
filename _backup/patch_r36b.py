# -*- coding: utf-8 -*-
"""r36b：右键菜单变高后不超出屏幕；说明书补删除项"""
import io

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()
G = r"H:\tool\silkworm-trajectory\_backup\build_guide_r34.py"


def rep(text, a, b, n=1):
    assert text.count(a) == n, (text.count(a), a[:70])
    return text.replace(a, b)


s = rep(s, """    el.style.display = 'block';
    el.style.left = Math.max(8, Math.min(clientX, window.innerWidth - 224)) + 'px';
    el.style.top = Math.max(8, Math.min(clientY, window.innerHeight - 300)) + 'px';""",
"""    el.style.display = 'block';
    el.style.left = Math.max(8, Math.min(clientX, window.innerWidth - 224)) + 'px';
    // 菜单项会越来越多，按真实高度夹住，别掉到屏幕外面
    const mh = el.offsetHeight || 320;
    el.style.top = Math.max(8, Math.min(clientY, window.innerHeight - mh - 12)) + 'px';""")

s = rep(s, """#habCtxMenu{position:fixed;z-index:99999;display:none;min-width:196px;""",
"""#habCtxMenu{position:fixed;z-index:99999;display:none;max-height:calc(100vh - 24px);overflow:auto;min-width:196px;""")

io.open(P, "w", encoding="utf-8").write(s)

g = io.open(G, encoding="utf-8").read()
g = rep(g, """  '<tr><td>清掉这一格的形状（孔/缺口/壁/丝路）</td><td>这一格的所有自定义形状清空，回到默认。</td></tr>'""",
"""  '<tr><td>清掉这一格的形状（孔/缺口/壁/丝路）</td><td>这一格的所有自定义形状清空，回到默认。</td></tr>'
  '<tr><td><b>删除这一块织网单元（整块消失）</b></td><td>把这一整块从场地里删掉（不是只删形状）。删错按 <b>Ctrl+Z</b> 撤回。</td></tr>'""")
g = rep(g, """  '<p class="lead">在场地里<b>点哪个格子，就在改哪个格子</b>。这就是编辑状态的全部开关。</p>'""",
"""  '<p class="lead">在场地里<b>点哪个格子，就在改哪个格子</b>。这就是编辑状态的全部开关。</p>'
  '<p>想删掉一整块：格内右键最下面的「删除这一块织网单元」，或者选中这块之后按右栏「删除这一块」——两个入口做的是同一件事，删错都能 Ctrl+Z 撤回。</p>'""")
io.open(G, "w", encoding="utf-8").write(g)
print("r36b ok")
