# -*- coding: utf-8 -*-
"""生成印刷版（白底）使用说明，供 Chrome 打印成 PDF"""
import base64, io, os

TMP = os.path.join(os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp'))
OUT = os.path.join(TMP, 'guide-print.html')


def b64(name):
    with open(os.path.join(TMP, name), 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode('ascii')


IMG_HOME = b64('guide-home.png')
IMG_EDIT = b64('guide-edit.png')
IMG_VIDEO = b64('guide-video-crop.png')
IMG_VIDEO2 = b64('guide-video-custom-crop.png')
IMG_EXPORT = b64('guide-export-crop.png')

CSS = """
@page { size: A4; margin: 15mm 14mm 15mm 14mm; }
* { box-sizing: border-box; }
body { margin: 0; background: #fff; color: #17181a;
  font: 10.6pt/1.72 "Microsoft YaHei", "Source Han Sans SC", system-ui, sans-serif; }
h1 { font-size: 23pt; margin: 0 0 4mm; letter-spacing: .5px; }
.lead { color: #5a6068; margin: 0 0 3mm; font-size: 10pt; }
h2 { font-size: 13.5pt; margin: 9mm 0 3mm; padding-left: 3mm; border-left: 1.1mm solid #c08a4a;
  break-after: avoid; }
h3 { font-size: 11pt; margin: 5mm 0 2mm; color: #8a5a2b; break-after: avoid; }
p { margin: 2mm 0; }
ul, ol { margin: 2mm 0 2mm 6mm; }
li { margin: 1mm 0; }
.card { border: .3mm solid #dcd6cc; border-radius: 2mm; padding: 3mm 4mm; margin: 3mm 0; background: #fcfbf8; }
.tip { border-left: 1mm solid #5c9a8a; background: #f4f8f6; padding: 2.5mm 3.5mm; margin: 3mm 0; }
.warn { border-left: 1mm solid #c08a4a; background: #fdf6ec; padding: 2.5mm 3.5mm; margin: 3mm 0; }
img { max-width: 100%; display: block; margin: 3mm 0 1mm; border: .3mm solid #cfc9bf; border-radius: 1.5mm; }
img.crop { max-width: 62mm; }
.fig { margin: 3mm 0; break-inside: avoid; }
.fig img { margin: 0 0 1mm; }
.fig .cap { margin: 0; }
.cap { color: #5a6068; font-size: 8.6pt; margin: 0 0 3mm; }
table { border-collapse: collapse; width: 100%; margin: 3mm 0; font-size: 9.4pt; break-inside: avoid; }
th, td { border: .3mm solid #d8d2c8; padding: 1.6mm 2mm; text-align: left; vertical-align: top; }
th { background: #f2ece1; font-weight: 600; }
.k { display: inline-block; width: 5mm; height: 5mm; border-radius: 50%; background: #c08a4a;
  color: #fff; font-weight: 700; text-align: center; line-height: 5mm; font-size: 9pt; margin-right: 2mm; }
.note { font-size: 9pt; color: #4d535a; }
.cover { border-bottom: .4mm solid #d8d2c8; padding-bottom: 4mm; margin-bottom: 6mm; }
.meta { font-size: 9pt; color: #6a7077; }
.grid2 { display: flex; gap: 4mm; }
.grid2 > div { flex: 1; }
.foot { margin-top: 8mm; padding-top: 3mm; border-top: .3mm solid #ddd7cd; font-size: 8.6pt; color: #6a7077; }
code { background: #f2efe9; padding: .3mm 1.2mm; border-radius: 1mm; font-size: 9pt; }
"""

BODY = """
<div class="cover">
  <h1>蚕轨迹描图器 · 使用说明</h1>
  <p class="lead">面向现场操作者。重点讲清楚 Digital Habitat（数字蚕室）怎么用：放块、放蚕、改形状、存工程、导出视频。</p>
  <p class="meta">版本 r27 · 2026-11-18 · 随网页发布（网页地址见文末）</p>
</div>

<h2>一、界面只有三块，先认清各自干什么</h2>
<div class="card">
<p><span class="k">1</span><b>左栏＝设置区</b>：环境（温度 / 湿度）、场地形状、记录（保存 / 载入工程）、母版导出、网页端导出视频。</p>
<p><span class="k">2</span><b>中间＝场地</b>：你能看见蚕、织块、丝线的地方。所有拖拽都在这里发生。画面一屏看全，不用上下滚。</p>
<p><span class="k">3</span><b>右栏＝个体面板</b>：上面列出场地里每一只蚕、每一个织网单元；下面「选中调整」是选中对象的滑条。</p>
<p class="note">左右两栏各自可上下滚（把鼠标指在栏上滚滚轮就行），中间场地不滚。</p>
</div>
<figure class="fig"><img src="__IMG_HOME__" alt="Digital Habitat 主界面">
<p class="cap">图 1　主界面：左栏设置、中间场地（两个织网单元，各有一只实测蚕在格里爬）、右栏个体。</p></figure>

<h2>二、第一次上手：五步就出效果</h2>
<ol>
<li><b>放一块织网单元</b>：右栏「操作」里点「放入织网单元」（想一次放很多块就点「铺块群」）。中间出现一个方框，这就是“一格”。</li>
<li><b>选这一格用哪只蚕</b>：右栏「这一格用哪只蚕」→「蚕 N」＝只用那一只；「合并丝路」＝把现有丝路都叠进来；「全部蚕（每种一只）」＝每种蚕各放一只进去。</li>
<li><b>让蚕动起来</b>：底部「开始」。蚕只会在自己所属的那一格范围里爬，不会跑到别的格，也不会铺到场地空白处。</li>
<li><b>看时间</b>：底部橙色滑条就是时间轴，拖到任意位置等于快进 / 倒回，松手画面立刻跟上。想停就点「暂停」，想继续点「继续」。</li>
<li><b>存下来</b>：左栏「保存工程（.json）」，把整份工程（几格、每格用哪只蚕、改过的形状、随机种子）存成一个文件。</li>
</ol>
<div class="tip">蚕是「一种蚕」，不是「一只蚕」。同一只蚕的数据可以同时用在很多格里，每格各爬各的；给某格指定某只蚕，<b>不会</b>从别的格把它摘走。</div>

<h2>三、改形状：像建模软件一样拖</h2>
<p>先在场地里点中那一格（或右栏点它的名字）→ 右栏点「编辑这一格」→ 格子四周出现编辑手柄 → 拖 → 点「完成编辑」。</p>
<figure class="fig"><img src="__IMG_EDIT__" alt="形状编辑态">
<p class="cap">图 2　编辑态：四角与四边中点的橙色手柄、青色孔洞手柄、块上方「∅ 117 px」直径读数，底部一行白话提示。</p></figure>
<table>
<tr><th style="width:34%">你拖的东西</th><th>会发生什么</th></tr>
<tr><td>四角的橙色方点</td><td>改整块大小；对角那条边钉住不动</td></tr>
<tr><td>四条边中点的橙色短条</td><td><b>只改被拖的那条边</b>，拖左边就只动左边界，右边不动</td></tr>
<tr><td>中间的橙色十字</td><td>整块挪位置</td></tr>
<tr><td>青色实点 / 青色空心圈</td><td>挪孔洞位置 / 改孔洞大小（孔上直接标了直径）</td></tr>
<tr><td>白色小方点（多边形时出现）</td><td>改外框顶点；<b>白色空心方点</b>是每条边的中点，拖一下就多出一个新角点</td></tr>
</table>
<div class="warn">虚线框、手柄、直径标注<b>只是编辑辅助</b>，只在编辑时出现；成品图、导出的视频、母版里都不会有。底部提示条也写着这句话。</div>
<p class="note">改错了直接按 Ctrl+Z 撤回，Ctrl+Shift+Z 重做；右栏「操作」里也有「撤销 / 重做」按钮。</p>

<h2>四、能中途保存吗？能，而且不用你手动点</h2>
<div class="grid2">
<div class="card">
<h3>自动保存（默认就开着）</h3>
<p>每 3 秒把当前场地存进本机浏览器；切走窗口、关网页时再补存一次。<br>
下次打开同一个网页，自动接着上次的场地，并提示“已恢复上次编辑的场地（时间）”。</p>
<p class="note">左栏「记录」下面那行小字显示最近一次自动保存的时刻。</p>
</div>
<div class="card">
<h3>文件保存（换电脑 / 发给别人用这个）</h3>
<p>点「保存工程（.json）」，得到一个 <code>habitat-时间戳.json</code>。<br>
另一台机器打开网页 →「载入工程（.json）」→ 选这个文件 → 场地、格子、每格用哪只蚕、改过的形状、种子全部还原。</p>
<p class="note">这份 JSON 也正好是母版渲染的输入文件。</p>
</div>
</div>
<div class="tip">自动保存容量上限约 5 MB（浏览器限制）。若左栏提示“自动保存失败（存储满了）”，点一次「保存工程（.json）」手动存一份即可，不会丢你之前存的文件。</div>

<h2>五、网页端导出视频：更长、更清楚、可选画质</h2>
<figure class="fig"><img class="crop" src="__IMG_VIDEO__" alt="网页端导出视频设置">
<p class="cap">图 3　左栏「网页端导出视频」：分辨率、时长、帧率、画质四个下拉，加一个录制按钮。</p></figure>

<h3>1. 分辨率（屏体是 4:3，约 3.14 m × 2.36 m）</h3>
<table>
<tr><th style="width:26%">选项</th><th style="width:16%">比例</th><th>什么时候用</th></tr>
<tr><td>854×480</td><td>16:9</td><td>只想快速看效果</td></tr>
<tr><td>1280×720</td><td>16:9</td><td>发微信 / 做内部预览</td></tr>
<tr><td>1920×1080</td><td>16:9</td><td>普通 16:9 屏或视频号</td></tr>
<tr><td><b>1920×1440</b></td><td>4:3</td><td>4:3 屏的快速样片</td></tr>
<tr><td><b>2048×1536</b></td><td>4:3</td><td><b>上屏交付首选</b>：约 2K，现场播放片</td></tr>
<tr><td><b>2093×1573</b></td><td>4:3</td><td>屏体理论分辨率（按 3.14 m × 2.36 m 折算）</td></tr>
<tr><td>2560×1920</td><td>4:3</td><td>比交付更高一档，机器够快时用</td></tr>
<tr><td>3840×2880</td><td>4:3</td><td>4K 存档 / 后期再压</td></tr>
<tr><td>2419×1360</td><td>16:9</td><td>旧母版规格（早期样片）</td></tr>
<tr><td><b>自定义…</b></td><td>任意</td><td>填「宽 × 高」两个数字；旁边会立刻显示比例，并提示“不是 4:3 上屏会加黑边”</td></tr>
</table>
<p class="note">选好分辨率后，下面那行小字会实时告诉你当前比例和像素尺寸；不是 4:3 时会直接提醒“上屏会加黑边”。</p>
<figure class="fig"><img class="crop" src="__IMG_VIDEO2__" alt="自定义尺寸展开态">
<p class="cap">图 4　选「自定义…」后出现「自定义宽×高」两个输入框，下方显示「4:3 · 2048×1536」与比例提示。</p></figure>

<h3>2. 时长 / 帧率 / 画质</h3>
<table>
<tr><th style="width:20%">项目</th><th style="width:38%">可选</th><th>建议</th></tr>
<tr><td>时长</td><td>5 / 10 / 20 / 30 / 60 / 120 秒</td><td>循环片 10–20 秒够看；要长镜头就 60 / 120 秒</td></tr>
<tr><td>帧率</td><td>24 / 30 / 60 fps</td><td>LED 屏常用 30；追求顺滑用 60（更吃性能）</td></tr>
<tr><td>画质</td><td>8 / 16 / 28 / 40 Mbps</td><td>1080p 选 16；2048 以上选 28–40</td></tr>
</table>

<h3>3. 为什么“更长更清晰”是有保证的</h3>
<ul>
<li><b>码率真的给到编码器</b>：原来固定 14 Mbps，现在按你选的 8–40 Mbps 传给 VP9（不支持时自动退 VP8），同分辨率下细节明显更多。</li>
<li><b>长片边录边写盘</b>：超过 30 秒、或分辨率很大（2048 以上）时，先弹一次“保存到哪里”，之后边录边写文件，不把整段压在内存里 → 120 秒也不会录到一半断掉。</li>
<li><b>录完自报帧数</b>：状态栏会写“实际绘制 300/300 帧，没有掉帧”；如果掉了，会直接告诉你去降分辨率或改 30 fps。</li>
<li><b>循环相位是散开的</b>：多块不会同时亮灭，避免整面墙一起闪。</li>
</ul>
<h3>4. 导出单张图片（PNG，用同一个分辨率）</h3>
<p>「导出当前画面 PNG」：用上面那个分辨率出图，时间轴停在哪一帧就导哪一帧。导出的是成品块群画面，<b>不含蚕体、不含编辑手柄和虚线框</b>；文件名自带分辨率与时刻，例如 <code>weave_still_2048x1536_12s.png</code>。</p>
<figure class="fig"><img class="crop" style="max-width:46mm" src="__IMG_EXPORT__" alt="网页端导出图片">
<p class="cap">图 5　左栏下半段：同一个分辨率下拉下面就是「导出当前画面 PNG」。</p></figure>

<div class="warn">网页导出的是 <b>WebM</b>（观看与交付够用）。要做上屏无损母版，用左栏「导出母版场景 JSON」+ 本地渲染脚本（ProRes），那条才是 10-bit 母版路径；网页端不替代它。</div>

<h2>五之二、只看丝、或只看蚕：两个开关</h2>
<p>左栏「场地」下面两个勾：<b>隐藏所有蚕体（只留丝）</b>／<b>隐藏所有丝迹（只留蚕）</b>。隐藏丝时织网单元的丝也一起收起来，原地留一圈很淡的虚线框，方便找回那一块。</p>
<p>只想藏某一只：右栏个体卡片上有「蚕：显示中／已隐藏」「丝：显示中／已隐藏」两个小按钮，点一下只切换这一只。</p>
<p class="note">隐藏只是“看不看见”，不改数据——保存工程、导出母版 JSON 里该有的丝和蚕都还在。</p>

<h2>六、母版导出（给展陈 / 后期）</h2>
<ul>
<li>「屏体分辨率」默认 2048×1536（4:3 交付），也可选 2093×1573、2560×1920，或旧的 2419×1360（16:9）。</li>
<li>「帧数 / 帧率」默认 900 帧 / 30 fps＝30 秒。</li>
<li>「导出母版场景 JSON」是本地渲染脚本的输入；「导出曲线 JSON」「导出单元几何 SVG / DXF」给 Rhino、Blender 用。</li>
<li>「复制母版渲染命令」会给你一条可直接跑的 ffmpeg 命令。</li>
</ul>

<h2>七、名词表（界面里出现的词，一句话解释）</h2>
<table>
<tr><th style="width:26%">词</th><th>白话解释</th></tr>
<tr><td>织网单元 / 一格</td><td>场地里的一块织块。放几块就有几块，每块独立。</td></tr>
<tr><td>壁</td><td>这一格的边界。丝碰到壁就停下，不会穿出去。</td></tr>
<tr><td>丝路</td><td>蚕爬过的路线，决定丝往哪铺。可以从描图器里画，也可以手绘。</td></tr>
<tr><td>孔洞</td><td>格子中间挖空的圆。参考图里每块都有一个大圆孔。</td></tr>
<tr><td>缺口</td><td>从格的边缘往里挖的一块，像被咬掉一口。</td></tr>
<tr><td>缝（块缝）</td><td>两块之间留的黑边，让块群看起来是分开的。</td></tr>
<tr><td>覆盖率</td><td>这一格里被丝盖住的比例（0.55＝约一半多一点）。</td></tr>
<tr><td>一格 ≈ 多少份吐丝</td><td>格里的丝总长 ÷ 一次吐丝长度（70.42 mm＝7.042 个格宽）。当前参数下约 <b>25 份</b>（20.9–32.1）。</td></tr>
<tr><td>种子（seed）</td><td>同一套参数下决定“织出来是什么样”的随机号码。种子相同＝纹理相同。</td></tr>
<tr><td>自定义尺寸</td><td>视频导出的宽 × 高自己填。填完旁边会显示比例，不是 4:3 会提醒你。</td></tr>
</table>

<h2>八、常见问题</h2>
<h3>蚕为什么只在格子里爬，不铺满场地？</h3>
<p>这是故意的：蚕绑在所属单元上，活动范围收在格内，丝迹逐点夹在格内。想让丝铺满整场，就多放几块（「铺块群」）。</p>
<h3>左栏的滑条拖了没反应？</h3>
<p>先确认右栏顶部有没有选中对象（点中场地里的块或蚕）。右栏「选中调整」只对选中的那一个生效。</p>
<h3>录出来的视频有点糊？</h3>
<p>按顺序调：①画质往上调一档；②分辨率别超过实际用途（4:3 上屏用 2048×1536 就够）；③帧率 30 比 60 稳。状态栏若显示掉帧，说明这台机器渲染跟不上，降一档即可。</p>
<h3>视频上屏左右有黑边？</h3>
<p>说明导出比例不是 4:3。回到分辨率下拉，选 2048×1536 或 2093×1573，再录一次。</p>
<h3>关掉网页会丢吗？</h3>
<p>不会。每 3 秒自动存一次，下次打开自动恢复。要带走就用「保存工程（.json）」。</p>

<div class="foot">
网页：https://yuculikedogandfish-droid.github.io/silkworm-trajectory/　·　使用说明网页版：同目录 <code>使用说明.html</code><br>
版本 r27（2026-11-18）。截图取自当前网页实拍。参数若有调整，以网页里显示为准。
</div>
"""

HTML = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<title>蚕轨迹描图器 · 使用说明</title><style>' + CSS + '</style></head><body>' + BODY + '</body></html>')
HTML = HTML.replace('__IMG_HOME__', IMG_HOME).replace('__IMG_EDIT__', IMG_EDIT)
HTML = HTML.replace('__IMG_VIDEO2__', IMG_VIDEO2).replace('__IMG_VIDEO__', IMG_VIDEO)
HTML = HTML.replace('__IMG_EXPORT__', IMG_EXPORT)

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(OUT, os.path.getsize(OUT))
