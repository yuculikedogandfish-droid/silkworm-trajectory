import io
G=r"docs\使用说明.html"
s=io.open(G,encoding="utf-8").read()

# 版本
s=s.replace("版本：<b>r36</b>","版本：<b>r42</b>")
s=s.replace("使用说明 · r36","使用说明 · r42")
s=s.replace("使用说明 r36</title>","使用说明 r42</title>")

# 目录补 11
old_toc='<li>10. 常见问题</li>'
if old_toc in s:
    s=s.replace(old_toc, old_toc+'<li>11. 图层、分组与排版</li>',1)
else:
    # 目录可能是别的结构，退而求其次：给 10 项后面补一段
    pass

# 02 表格：右栏措辞
s=s.replace("个体列表（每块格子、每只蚕都能单独暂停/拖动/隐藏）；选中之后出现的「选中调整」滑条。",
            "「个体与图层」（每块格子、每只蚕都是一层，可单独显隐、锁定、编组、整组拖动）；选中之后的「选中调整」滑条。")
s=s.replace("整体界面：左边环境与观感、中间场地、右边个体与选中调整、最下面时间轴。",
            "整体界面：左边环境与观感、中间场地（识别条浮在左上角）、右边个体与图层、最下面时间轴。")

# 06 隐藏
s=s.replace("右栏每只个体卡片上有「蚕：显示中 / 丝：显示中」，点一下单独隐藏这一只的蚕或丝。",
            "右栏每一层右边有「显 / 隐」，点一下单独隐藏这一层；组行上的「显」一次管整组。")

# SVG 给深色底，打印也看得清
s=s.replace('<rect x="0" y="0" width="520" height="170" rx="8" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.10)"/>',
            '<rect x="0" y="0" width="520" height="170" rx="8" fill="#10171a" stroke="rgba(255,255,255,0.18)"/>')

# 打印样式：白底紧凑
print_css = """
@media print{
  @page{size:A4;margin:13mm 12mm}
  html,body{background:#fff!important;color:#16201d!important}
  .hero,.card,.tip,table,th,td{background:#fff!important;color:#16201d!important;border-color:#cfd6d2!important;box-shadow:none!important}
  h1,h2,h3,h4,p,li,td,th,figcaption,.lead,.toc,.toc b{color:#16201d!important}
  .eyebrow,.shot figcaption{color:#5b6a64!important}
  .card{break-inside:avoid;page-break-inside:avoid;margin-bottom:10px}
  figure.shot{break-inside:avoid}
  .shot img{border:1px solid #d5dcd8;max-width:100%}
  .tip{border-left:3px solid #93a89e!important}
  a{color:#24443c!important}
}
"""
if '@media print' not in s:
    s=s.replace('</style>', print_css + '</style>', 1)

io.open(G,"w",encoding="utf-8").write(s)
print("guide patch ok")
