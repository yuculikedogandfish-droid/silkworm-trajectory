# -*- coding: utf-8 -*-
import base64, io, os, textwrap

TMP = os.path.join(os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp'))
OUT = r"H:\tool\silkworm-trajectory\docs\使用说明.html"


def b64(name):
    p = os.path.join(TMP, name)
    with open(p, 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode('ascii')


IMG_HOME = b64('guide-home.png')
IMG_EDIT = b64('guide-edit.png')
IMG_VIDEO = b64('guide-video.png')
IMG_EXPORT = b64('guide-export.png')

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>蚕轨迹描图器 · 使用说明</title>
<style>
:root{
  --bg:#0c0f0e; --panel:#121716; --line:#243130; --ink:#e8eee9; --dim:#9fb1ab;
  --acc:#f0b45a; --acc2:#79cbb6;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.75 "Microsoft YaHei",system-ui,-apple-system,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:48px 24px 96px}
h1{font-size:30px;letter-spacing:.5px;margin:0 0 8px}
.sub{color:var(--dim);margin:0 0 36px}
h2{font-size:19px;margin:44px 0 12px;padding-left:12px;border-left:3px solid var(--acc)}
h3{font-size:15px;margin:22px 0 8px;color:var(--acc2)}
p{margin:8px 0}
ul,ol{margin:8px 0 8px 20px}
li{margin:4px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:14px 0}
.tip{border-left:3px solid var(--acc2);background:#0f1615;padding:10px 14px;margin:12px 0;color:#cfe3dd;border-radius:0 6px 6px 0}
.warn{border-left:3px solid var(--acc);background:#171310;padding:10px 14px;margin:12px 0;color:#f3e3c8;border-radius:0 6px 6px 0}
img{max-width:100%;border:1px solid var(--line);border-radius:8px;display:block;margin:12px 0}
.cap{color:var(--dim);font-size:13px;margin:6px 0 0}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left}
th{background:#161d1c;font-weight:600}
td.num{font-variant-numeric:tabular-nums}
code{background:#0b1110;border:1px solid var(--line);border-radius:4px;padding:1px 6px;font-size:13px}
.k{display:inline-block;width:22px;height:22px;border-radius:50%;background:var(--acc);color:#161008;font-weight:700;text-align:center;line-height:22px;font-size:13px;margin-right:6px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:760px){.grid2{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">

<h1>蚕轨迹描图器 · 使用说明</h1>
<p class="sub">重点讲清楚 Digital Habitat（数字蚕室）怎么用：放块、放蚕、改形状、存工程、导出视频。不需要懂代码。</p>

<h2>一、界面只有三块，先认清各自干什么</h2>
<div class="card">
<p><span class="k">1</span><b>左栏＝设置区</b>：环境（温度/湿度）、场地形状、记录（保存/载入工程）、母版导出、网页端导出视频。</p>
<p><span class="k">2</span><b>中间＝场地</b>：你能看见蚕、织块、丝线的地方。所有拖拽都在这里发生。</p>
<p><span class="k">3</span><b>右栏＝个体面板</b>：上面列出场地里每一只蚕、每一个织网单元；下面「选中调整」是选中对象的滑条。</p>
<p class="cap">左右栏各自可上下滚（鼠标指在栏上滚滚轮就行）。</p>
</div>
<img src="__IMG_HOME__" alt="Digital Habitat 主界面">
<p class="cap">↑ 主界面：左栏设置、中间场地、右栏个体。图里两个织网单元，各有一只实测蚕在格里爬。</p>

<h2>二、第一次上手：五步就出效果</h2>
<ol>
<li><b>放一块织网单元</b>：右栏「操作」里点「放入织网单元」（或「铺块群」一次放很多块）。中间出现一个虚线方框，这就是“一格”。</li>
<li><b>选这一格用哪只蚕</b>：右栏滚到下面「这一格用哪只蚕」，选「蚕N」＝只用那一只；选「合并丝路」＝把现有丝路都叠进来；选「全部蚕（每种一只）」＝每种蚕各放一只进去。</li>
<li><b>让蚕动起来</b>：底部「开始」。蚕只会在自己所属的那一格范围里爬，不会跑到别的格，也不会铺到场地空白处。</li>
<li><b>看时间</b>：底部那条橙色滑条就是时间轴，拖到任意位置等于“快进/倒回”，松手画面立刻跟上。想停在某一刻就点「暂停」。</li>
<li><b>存下来</b>：左栏「保存工程（.json）」，把整份工程（几格、每格用哪只蚕、改过的形状、随机种子）存成一个文件。</li>
</ol>
<div class="tip">蚕是「一种蚕」，不是「一只蚕」。同一只蚕的数据可以同时用在很多格里，每格各爬各的；给某格指定某只蚕，<b>不会</b>从别的格把它摘走。</div>

<h2>三、改形状：像建模软件一样拖</h2>
<p>步骤：先在场地里点中那一格（或右栏点它的名字）→ 右栏点「编辑这一格」→ 格子四周出现编辑手柄 → 拖 → 点「完成编辑」。</p>
<img src="__IMG_EDIT__" alt="形状编辑态">
<table>
<tr><th>你拖的东西</th><th>会发生什么</th></tr>
<tr><td>四角的橙色方点</td><td>改整块大小；对角那条边钉住不动</td></tr>
<tr><td>四条边中点的橙色短条</td><td><b>只改被拖的那条边</b>，比如拖左边就只动左边界，右边不动</td></tr>
<tr><td>中间的橙色十字</td><td>整块挪位置</td></tr>
<tr><td>青色实点 / 青色空心圈</td><td>挪孔洞位置 / 改孔洞大小（孔上直接标了直径）</td></tr>
<tr><td>白色小方点（多边形时出现）</td><td>改外框顶点；<b>白色空心方点</b>是每条边的中点，拖一下就多出一个新角点</td></tr>
</table>
<div class="warn">虚线框、手柄、直径标注<b>只是编辑辅助</b>，只在编辑时出现；成品图、导出的视频、母版里都不会有。底部提示条也写着这句话。</div>

<h2>四、能中途保存吗？能，而且不用你手动点</h2>
<div class="grid2">
<div class="card">
<h3>自动保存（默认就开着）</h3>
<p>每 3 秒把当前场地存进你本机浏览器；切走窗口、关网页时也会补存一次。<br>
下次打开同一个网页，会自动接着上次的场地，并提示“已恢复上次编辑的场地（时间）”。</p>
<p class="cap">左栏「记录」下面那行小字会显示最近一次自动保存的时间。</p>
</div>
<div class="card">
<h3>文件保存（换电脑/发给别人用这个）</h3>
<p>点「保存工程（.json）」，得到一个 <code>habitat-时间戳.json</code>。<br>
到另一台机器打开网页 → 左栏「载入工程（.json）」→ 选这个文件 → 场地、格子、每格用哪只蚕、改过的形状、种子全部还原。</p>
<p class="cap">这个 JSON 也正好是母版渲染的输入文件，一举两得。</p>
</div>
</div>
<div class="tip">自动保存容量上限约 5 MB（浏览器限制）。如果左栏提示“自动保存失败（存储满了）”，点一次「保存工程（.json）」手动存一份即可，不会丢你之前存的文件。</div>

<h2>五、网页端导出视频：更长、更清楚、可选画质</h2>
<img src="__IMG_VIDEO__" alt="网页端导出视频设置">
<p>左栏「网页端导出视频」有四个下拉，加一个按钮：</p>
<table>
<tr><th>选项</th><th>可选的</th><th>怎么选</th></tr>
<tr><td>分辨率</td><td>854×480 / 1280×720 / 1920×1080（16:9）<br><b>1920×1440 / 2048×1536 / 2093×1573 / 2560×1920 / 3840×2880（4:3）</b><br>2419×1360（旧 16:9 母版）/ <b>自定义…</b></td><td><b>上屏用 2048×1536</b>（4:3，约 3.14 m × 2.36 m 的屏）；要更贴屏体理论值选 2093×1573；选「自定义…」可自己填宽 × 高，旁边会实时显示比例</td></tr>
<tr><td>时长</td><td>5 / 10 / 20 / 30 / 60 / 120 秒</td><td>循环片 10–20 秒够看；要长镜头就 60/120 秒</td></tr>
<tr><td>帧率</td><td>24 / 30 / 60 fps</td><td>LED 屏常用 30；追求顺滑用 60（更吃性能）</td></tr>
<tr><td>画质</td><td>8 / 16 / 28 / 40 Mbps</td><td>1080p 选 16；母版分辨率选 28–40</td></tr>
</table>
<h3>为什么说“更长更清晰”是有保证的</h3>
<ul>
<li><b>码率真的给到编码器</b>：原来固定 14 Mbps，现在按你选的 8–40 Mbps 传给 VP9（不支持时自动退 VP8），同分辨率下细节明显更多。</li>
<li><b>长片边录边写盘</b>：超过 30 秒（或分辨率很大）会先弹一次“保存到哪里”，之后边录边写文件，不把整段压在内存里 → 120 秒也不会录到一半断掉。</li>
<li><b>录完自报帧数</b>：状态栏会写“实际绘制 300/300 帧，没有掉帧”；如果掉了，会直接告诉你去降分辨率或改 30 fps。</li>
<li><b>循环相位是散开的</b>：42 块不会同时亮灭，避免整面墙一起闪。</li>
</ul>
<div class="warn">网页导出的是 <b>WebM</b>（观看/交付够用）。要做上屏 ProRes 母版，用左栏「导出母版场景 JSON」+ 本地渲染脚本，那条路径是无损 10-bit 的；网页端不替代它。</div>

<h3>导出单张图片（PNG，用同一个分辨率）</h3>
<p>左栏「网页端导出图片」→ 点「导出当前画面 PNG」。用的是上面那个分辨率下拉，所以想出 2048×1536 的成品图，先把分辨率选到 2048×1536；时间轴停在哪一帧，导出的就是哪一帧。</p>
<img src="__IMG_EXPORT__" alt="网页端导出图片">
<p class="cap">导出的是成品块群画面：不含蚕体、不含编辑手柄和虚线框。文件名自带分辨率与时刻，例如 <code>weave_still_2048x1536_12s.png</code>。</p>

<h2>五之二、只看丝、或只看蚕：两个开关</h2>
<p>左栏「场地」下面有两个勾：</p>
<ul>
<li><b>隐藏所有蚕体（只留丝）</b>：蚕身不画，丝迹照常留着——适合看纹理、拍成品图。</li>
<li><b>隐藏所有丝迹（只留蚕）</b>：丝迹不画，蚕身留着——适合看蚕在哪儿爬。织网单元的丝也会一起隐藏，只在原地留一圈很淡的虚线框，方便你找回这一块。</li>
</ul>
<p>只想藏某一只：右栏个体卡片上有两个小按钮——「蚕：显示中 / 已隐藏」「丝：显示中 / 已隐藏」，点一下单独切换这一只，不影响别的格。</p>
<p class="cap">注意：隐藏是“看不看见”，不改数据——保存工程、导出母版 JSON 里该有的丝和蚕都还在。</p>

<h2>六、母版导出（给展陈/后期）</h2>
<ul>
<li>「屏体分辨率」默认 2048×1536（4:3 交付），也可选 2093×1573、2560×1920，或旧的 2419×1360（16:9）；「帧数/帧率」默认 900 帧 / 30 fps＝30 秒。</li>
<li>点「导出母版场景 JSON」，这是本地渲染脚本的输入。</li>
<li>「导出曲线 JSON」「导出单元几何 SVG / DXF」给 Rhino、Blender 用。</li>
<li>「复制母版渲染命令」会给你一条可直接跑的 ffmpeg 命令。</li>
</ul>

<h2>七、名词表（界面里出现的词，一句话解释）</h2>
<table>
<tr><th>词</th><th>白话解释</th></tr>
<tr><td>织网单元 / 一格</td><td>场地里的一块织块。放几个就有几块，每块独立。</td></tr>
<tr><td>壁</td><td>这一格的边界。丝碰到壁就停下，不会穿出去。</td></tr>
<tr><td>丝路</td><td>蚕爬过的路线，决定丝往哪铺。可以从描图器里画，也可以手绘。</td></tr>
<tr><td>孔洞</td><td>格子中间挖空的圆。参考图里每块都有一个大圆孔。</td></tr>
<tr><td>缺口</td><td>从格的边缘往里挖的一块，像被咬掉一口。</td></tr>
<tr><td>缝（块缝）</td><td>两块之间留的黑边，让块群看起来是分开的。</td></tr>
<tr><td>覆盖率</td><td>这一格里被丝盖住的比例（0.55＝约一半多一点）。</td></tr>
<tr><td>一格 ≈ 多少份吐丝</td><td>一格里的丝总长 ÷ 一次吐丝的长度（70.42 mm＝7.042 个格宽）。当前参数下约 <b>25 份</b>（20.9–32.1）。</td></tr>
<tr><td>种子（seed）</td><td>同一套参数下决定“织出来是什么样”的随机号码。种子相同＝织出的纹理相同。</td></tr>
</table>

<h2>八、常见问题</h2>
<h3>蚕为什么只在格子里爬，不铺满场地？</h3>
<p>这是故意的：蚕绑在所属单元上，活动半径收在格内，丝迹逐点夹在格内。想让丝铺满整场，就多放几块（「铺块群」）。</p>
<h3>为什么左栏的滑条拖了没反应？</h3>
<p>先确认右栏顶部有没有选中对象（点中场地里的块或蚕）。右栏「选中调整」只对选中的那一个生效。</p>
<h3>录出来的视频有点糊？</h3>
<p>按顺序调：①画质往上调一档；②分辨率别超过实际用途（4:3 上屏用 2048×1536 就够）；③帧率 30 比 60 稳。状态栏如果显示掉帧，说明这台机器渲染跟不上，降一档即可。</p>
<h3>视频上屏左右有黑边？</h3>
<p>说明导出比例不是 4:3。回到分辨率下拉，选 2048×1536 或 2093×1573 再录一次；选「自定义…」时看下方那行小字，是 4:3 就不会有黑边。</p>
<h3>关掉网页会丢吗？</h3>
<p>不会。每 3 秒自动存一次，下次打开自动恢复。要带走就用「保存工程（.json）」。</p>

<p class="cap" style="margin-top:48px">本说明随 r27 版本一起发布；截图取自当前网页实拍。</p>
</div>
</body>
</html>
"""

HTML = HTML.replace('__IMG_EXPORT__', IMG_EXPORT).replace('__IMG_HOME__', IMG_HOME).replace('__IMG_EDIT__', IMG_EDIT).replace('__IMG_VIDEO__', IMG_VIDEO)

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(OUT, os.path.getsize(OUT))

