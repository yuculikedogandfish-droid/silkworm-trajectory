p = r"_backup\build_guide_r34.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""  '<p class="lead">屏幕分成四块，各管一件事。</p>' +
  fig('home', '整体界面：左边环境与观感、中间场地、右边个体与选中调整、最下面时间轴。') +
  '<table>""", """  '<p class="lead">屏幕分成四块，各管一件事。</p>'
  '<table>""")
s = s.replace("""  '<tr><td>底部</td><td>时间轴：「开始 / 暂停 / 继续」＋一条可以拖的进度条，拖到哪儿就停在哪儿。</td></tr>'
  '</table>'""", """  '<tr><td>底部</td><td>时间轴：「开始 / 暂停 / 继续」＋一条可以拖的进度条，拖到哪儿就停在哪儿。</td></tr>'
  '</table>' +
  fig('home', '整体界面：左边环境与观感、中间场地、右边个体与选中调整、最下面时间轴。')""")
s = s.replace("figure.shot img{display:block;width:100%;height:auto}\nfigcaption{font-size:8pt;color:#666;padding:4pt 6pt;border-top:1px solid #eee}",
                "figure.shot img{display:block;width:100%;height:auto;max-height:112mm;object-fit:contain}\nfigcaption{font-size:8pt;color:#666;padding:4pt 6pt;border-top:1px solid #eee}")
open(p, "w", encoding="utf-8").write(s)
print("order fixed")
