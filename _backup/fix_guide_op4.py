p = r"_backup\build_guide_r34.py"
s = open(p, encoding="utf-8").read()
a = """  '<p class="lead">一句话：<b>点线加锚点，拖点挪位置，右键删东西</b>。不需要先选工具再点按钮。</p>' +
  fig('edit', '编辑中的一格：白色方点是锚点，空心小方点是边中点，虚线就是缺口（编辑时才显示的辅助线）。') +
  '<table>"""
b = """  '<p class="lead">一句话：<b>点线加锚点，拖点挪位置，右键删东西</b>。不需要先选工具再点按钮。</p>'
  '<table>"""
assert s.count(a) == 1
s = s.replace(a, b)
c = """  '<tr><td>点「重画缺口」</td><td>清掉这一格的缺口，重新点几下围一圈。</td></tr>'
  '</table>'
  '<h3>画的时候就是曲线"""
d = """  '<tr><td>点「重画缺口」</td><td>清掉这一格的缺口，重新点几下围一圈。</td></tr>'
  '</table>' +
  fig('edit', '编辑中的一格：白色方点是锚点，空心小方点是边中点，虚线就是缺口（编辑时才显示的辅助线）。') +
  '<h3>画的时候就是曲线"""
assert s.count(c) == 1
s = s.replace(c, d)
open(p, "w", encoding="utf-8").write(s)
print("ok")
