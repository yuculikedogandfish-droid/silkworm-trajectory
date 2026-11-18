# -*- coding: utf-8 -*-
import io, base64
G = r"H:\tool\silkworm-trajectory\docs\使用说明.html"
s = io.open(G, encoding="utf-8").read()
b64 = base64.b64encode(io.open(r"C:\Users\54364\AppData\Local\Temp\rec43_preview.png", "rb").read()).decode("ascii")

sec = f"""<section class="card newpage"><h2><span>12</span>从参考图识别版式（r43 之后）</h2>
<p class="lead">把一张参考图拖进去，它会自己找格子、找孔洞，先给你看预览，确认无误再生成到场地。识别本身不会动场地。</p>
<figure class="shot"><img alt="识别预览" src="data:image/png;base64,{b64}"><figcaption>预览直接叠在原图上：青绿框＝这块会生成，黄色虚线＝把握不高，红色虚线＝这块不要，金圈＝圆孔，蓝色虚线＝曲线缺口。</figcaption></figure>
<h3>四步</h3>
<ol>
<li><b>拖图</b>：点中间上方的「从图片识别版式」展开，把图片拖进框里（或点框选文件），一次一张。</li>
<li><b>识别并预览</b>：等一两秒，场地上叠出原图和识别框。</li>
<li><b>校对</b>：点「点预览框补块 / 去块」，再点某个框就能切换“这块要 / 不要”；再点一次按钮退出校对。</li>
<li><b>生成到场地（新增）</b>：按每块真实的宽、高、位置生成。「替换现有块群」会先删掉场上已有的块，慎用。</li>
</ol>
<table><colgroup><col style="width:28%"><col style="width:72%"></colgroup><tr><th>控件</th><th>什么时候调</th></tr>
<tr><td>列数 / 排数</td><td>都填 0＝按真实轮廓自动找，每块大小可以不一样、允许错位和窄条；填了数字＝按固定网格均分（老方式）。</td></tr>
<tr><td>丝多稀也算一块</td><td>丝很稀的块被漏掉时往左调；黑底被误当成块时往右调。</td></tr>
<tr><td>多小的洞才保留</td><td>小洞太多就往右调，小洞被吃掉就往左调。</td></tr>
<tr><td>识别孔洞 / 识别缺口</td><td>只要其中一类时，把另一类勾掉。</td></tr>
<tr><td>预览时叠上原图对比</td><td>关掉就只看识别框，方便检查有没有多出来的块。</td></tr></table>
<div class="tip">生成之后每一块都是普通织网单元：可以拖锚点改缺口、可以编组、可以整组拖动，也可以用框选＋对齐继续排版。</div>
</section>"""

i = s.index('<section class="card"><h2><span>10')
j = s.index('</section>', i) + len('</section>')
# 插到 FAQ 之后、11 之前会打乱阅读顺序，直接放到 11 之后
k = s.index('<section class="card newpage"><h2><span>11')
k2 = s.index('</section>', k) + len('</section>')
s = s[:k2] + sec + s[k2:]
s = s.replace("版本：<b>r42</b>", "版本：<b>r43</b>")
s = s.replace("使用说明 · r42", "使用说明 · r43")
s = s.replace("<li>图层、分组与排版</li></ol>", "<li>图层、分组与排版</li><li>从参考图识别版式</li></ol>", 1)
io.open(G, "w", encoding="utf-8").write(s)
print("guide §12 ok")
