p = r"docs\index.html"
s = open(p, encoding="utf-8").read()
s = s.replace("""    if (tool === 'notch') { el.textContent = '正在改缺口 · 拖青色实点挪位置、拖青色圈改大小；点格边附近可把缺口挪到那边。'; return; }""",
"""    if (tool === 'notch') { el.textContent = '正在改缺口 · 在格内点几下围出一个形状，双击收尾（至少 3 点）；拖白点改形状、拖边中间的小方点加新点、右键删点或删整个缺口。'; return; }""")
s = s.replace("""    notch: '拖青点＝挪缺口 · 拖青圈＝改大小 · 点格子边缘附近＝把缺口挪到那边',""",
"""    notch: '在格内点几下＝围出缺口的形状（可任意曲线封闭形）· 双击收尾 · 拖白点改形状 · 拖边中点加新点 · 右键删点',""")
open(p, "w", encoding="utf-8").write(s)
print('texts ok')
