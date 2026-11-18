# -*- coding: utf-8 -*-
import io, base64, os

G = r"H:\tool\silkworm-trajectory\docs\使用说明.html"
IMG = r"C:\Users\54364\AppData\Local\Temp\qa-r41-layers.png"
s = io.open(G, encoding="utf-8").read()

b64 = base64.b64encode(io.open(IMG, "rb").read()).decode("ascii")

svg_marq = """<svg viewBox="0 0 520 170" style="width:100%;max-width:520px;display:block;margin:6px 0 10px" aria-hidden="true">
<rect x="0" y="0" width="520" height="170" rx="8" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.10)"/>
<g>
<rect x="60" y="46" width="110" height="80" fill="rgba(207,216,210,0.18)" stroke="rgba(207,216,210,0.45)"/>
<rect x="190" y="46" width="110" height="80" fill="rgba(207,216,210,0.18)" stroke="rgba(207,216,210,0.45)"/>
<rect x="320" y="46" width="110" height="80" fill="rgba(207,216,210,0.06)" stroke="rgba(207,216,210,0.25)"/>
</g>
<rect x="40" y="30" width="290" height="112" fill="rgba(121,203,182,0.12)" stroke="#79cbb6" stroke-dasharray="6 4" stroke-width="1.4"/>
<circle cx="40" cy="30" r="5" fill="#79cbb6"/><circle cx="330" cy="142" r="5" fill="#79cbb6"/>
<text x="42" y="24" font-size="13" fill="#9fd8c6">从这里按下</text>
<text x="250" y="158" font-size="13" fill="#9fd8c6">拖到这里松手 → 框住的两块被选中</text>
<text x="60" y="140" font-size="12" fill="#b9c6c0">已选</text>
<text x="190" y="140" font-size="12" fill="#b9c6c0">已选</text>
<text x="322" y="140" font-size="12" fill="#7f8c87">没框到，不选</text>
</svg>"""

svg_snap = """<svg viewBox="0 0 520 170" style="width:100%;max-width:520px;display:block;margin:6px 0 10px" aria-hidden="true">
<rect x="0" y="0" width="520" height="170" rx="8" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.10)"/>
<rect x="40" y="40" width="90" height="70" fill="rgba(207,216,210,0.16)" stroke="rgba(207,216,210,0.45)"/>
<rect x="170" y="40" width="90" height="70" fill="rgba(207,216,210,0.16)" stroke="rgba(207,216,210,0.45)"/>
<text x="52" y="34" font-size="12" fill="#a9b7b1">已有的块</text>
<text x="182" y="34" font-size="12" fill="#a9b7b1">已有的块</text>
<rect x="300" y="46" width="90" height="70" fill="rgba(240,180,90,0.18)" stroke="#f0b45a" stroke-dasharray="4 3"/>
<text x="306" y="34" font-size="12" fill="#f0b45a">正在拖的块</text>
<path d="M132 76 H168" stroke="#ff8cbe" stroke-width="1.2" stroke-dasharray="3 3"/>
<path d="M262 76 H298" stroke="#ff8cbe" stroke-width="1.2" stroke-dasharray="3 3"/>
<text x="136" y="96" font-size="11" fill="#ff8cbe">缝 40</text>
<text x="266" y="96" font-size="11" fill="#ff8cbe">自动变成同一个缝</text>
<line x1="300" y1="10" x2="300" y2="160" stroke="#ff8cbe" stroke-dasharray="3 3"/>
<text x="306" y="156" font-size="11" fill="#ff8cbe">对齐参考线（粉色）</text>
</svg>"""

section = f"""<section class="card"><h2><span>11</span>图层、分组与排版（r39 之后的新东西）</h2>
<p class="lead">右栏只有一个列表，每块织网单元、每只蚕都是其中的一层。先在列表里点它，场地上就会画出虚线框告诉你“选中的是这一块”。</p>
<figure class="shot"><img alt="图层面板" src="data:image/png;base64,{b64}"><figcaption>一行就是一层：缩略图是这一块此刻织出来的样子；下面是尺寸与每格蚕数；右边是「显」和「⋯」。</figcaption></figure>
<table><colgroup><col style="width:22%"><col style="width:78%"></colgroup><tr><th>行上的东西</th><th>点它会怎样</th></tr>
<tr><td>勾选框</td><td>多选。勾两层以上就能编组、对齐、阵列。</td></tr>
<tr><td>缩略图</td><td>这一块当前的样子，随织丝实时更新，不用回场地上找。</td></tr>
<tr><td>层名（单元 1 / 蚕 1）</td><td>选中这一层，场地上出现青绿虚线框；右栏下面「选中调整」也切到它。</td></tr>
<tr><td>显 / 隐</td><td>只影响画面和导出，数据不丢，再点一下就回来。</td></tr>
<tr><td>⋯</td><td>弹出小菜单：锁定这一层、上移一层、下移一层、移出所在组、删掉这一块。</td></tr></table>
<h3>组：把几层捆在一起</h3>
<p>勾上要捆的层 → 点「编组所选」→ 起个名字。组行上：<b>▾</b> 收起/展开，<b>组名</b> 一点＝整组选中，后面的数字是层数，<b>显</b> 管整组显隐，<b>改</b> 改名，<b>✕</b> 解散（只散组，不删块）。「并入同组」把勾选的层塞进已有的组里。</p>
<p><b>整组一起挪：</b>拖组里任意一块，整组跟着走；没编组的单块只动它自己。指针落在那块的手柄（角、边中点、中心）附近时仍交给手柄，不会抢。</p>
<h3>框选：在空地拉一个框</h3>
<p>按住空地拖动，超过一点点距离才算框选（所以普通点击不会误选）。框到的块全部选中；按住 Shift 拉框是追加。</p>
{svg_marq}
<h3>吸附：拖到位会“啪”地对齐</h3>
<p>拖动时自动贴别人的边、中线，或者与旁边两块保持同一道缝；命中时画粉色虚线做参考。按住 Ctrl（Mac 上 ⌘）拖，就临时不吸附，想微调时用。</p>
{svg_snap}
<h3>对齐、等距、阵列</h3>
<table><colgroup><col style="width:26%"><col style="width:74%"></colgroup><tr><th>按钮</th><th>作用</th></tr>
<tr><td>左 / 横中 / 右 / 上 / 竖中 / 下</td><td>把选中的几块按某个方向对齐（边缘或中线）。</td></tr>
<tr><td>水平等距 / 垂直等距</td><td>首尾不动，中间几块按等间距重新摆。</td></tr>
<tr><td>列 / 排 / 缝 → 复制</td><td>只选一块时用：按列数×排数复制，缝是块与块之间的空隙。复制出来的是同样的尺寸、孔洞与缺口。</td></tr>
<tr><td>方向键 / Shift + 方向键</td><td>选中后微调 1 像素 / 10 像素。</td></tr></table>
<h3>层序与锁定</h3>
<p>⋯ 里的「上移一层 / 下移一层」会真的改变叠放次序（有交叠时谁盖谁）；「锁定这一层」之后它不再跟着拖动，也不会被方向键挪走，适合已经把位置定死的块。</p>
<div class="tip">组关系会写进<b>工程 JSON</b>：换机器载入工程，组、组名、层序都还在。本机浏览器里也留了一份缓存，方便下次直接接着用。</div>
</section>"""

# 插到 FAQ（10）之后
i = s.index('<section class="card"><h2><span>10')
j = s.index('</section>', i) + len('</section>')
s = s[:j] + section + s[j:]

# 02 界面地图：右栏措辞
s = s.replace("右栏个体列表（每块格子、每只蚕都能单独暂停/拖动/隐藏）；选中之后出现的「选中调整」滑条。",
              "右栏「个体与图层」：每块格子、每只蚕都是一层，可单独显隐、锁定、编组、整组拖动；选中之后的「选中调整」滑条。")
s = s.replace("整体界面：左边环境与观感、中间场地、右边个体与选中调整、最下面时间轴。",
              "整体界面：左边环境与观感、中间场地（识别条浮在它左上角）、右边个体与图层、最下面时间轴。")

# 06 隐藏：卡片措辞
s = s.replace("右栏每只个体卡片上有「蚕：显示中 / 丝：显示中」，点一下单独隐藏这一只的蚕或丝。",
              "右栏每一层右边有「显 / 隐」，点一下单独隐藏这一层；组行上的「显」一次管整组。")

io.open(G, "w", encoding="utf-8").write(s)
print("guide §11 ok", len(s))
