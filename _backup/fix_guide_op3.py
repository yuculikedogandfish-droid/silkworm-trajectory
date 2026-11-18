p = r"_backup\build_guide_r34.py"
s = open(p, encoding="utf-8").read()
old_fig = """  '<p>在格子里的“空白处”按右键，菜单就是一份<b>添加清单</b>，点哪条就从那儿开始画：</p>' +
  fig('menu', '格内右键菜单：添加孔洞 / 添加缺口 / 添加壁 / 添加丝路 / 重设整块外框 / 清掉形状 / 退出编辑。') +
  '<table>"""
new_fig = """  '<p>在格子里的“空白处”按右键，菜单就是一份<b>添加清单</b>，点哪条就从那儿开始画（下图）：</p>'
  '<table>"""
assert s.count(old_fig) == 1
s = s.replace(old_fig, new_fig)
old_end = """  '</table>'
  '<h3>右键压在手柄上：出的是删除菜单</h3>'"""
new_end = """  '</table>' +
  fig('menu', '格内右键菜单：添加孔洞 / 添加缺口 / 添加壁 / 添加丝路 / 重设整块外框 / 清掉形状 / 退出编辑。') +
  '<h3>右键压在手柄上：出的是删除菜单</h3>'"""
assert s.count(old_end) == 1
s = s.replace(old_end, new_end)
open(p, "w", encoding="utf-8").write(s)
print("ok")
