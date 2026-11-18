# -*- coding: utf-8 -*-
"""追加 §28（r20）：编辑交互可视化 + 网页端导出视频 + 布局（两侧栏各自滚，画布一屏看全）"""
import io, os

DOC = r'H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md'

S28 = u'''
---

## §28 r20：编辑态"看得懂"、网页端直接出片、布局不再别着拧（2026-11-17）

### 28.1 先把布局修对（这是最影响手感的一条）
- 症状：整页比窗口宽，右侧「个体」面板被挤到屏幕外，滑条数值看不到；一定要上下滚整页才能看全场地。
- 根因：全局 `aside { width: 300px; }` 把 `.hab-side` 也按 300px 撑宽，而网格列是 `250px / 1fr / 270px`，于是两侧栏各越界 30–50 px。
  量测（1600×1000 窗口，`probe_r20_diag.py`）：修前 `habLeft width=300` / `habRight width=300`，网格 `250px 1062px 270px`。
- 修法：`.hab-side { width: auto; min-width: 0; }` + 网格中间列 `minmax(0, 1fr)` + `.hab-top { flex-wrap: wrap }` + 侧栏内控件的 `min-width` 放宽。
  修后量测：`habLeft=250 / habRight=270`，网格 `250px 1062px 270px`，页面无横向溢出。
- 高度：`--hab-stage-height` 改成按窗口算（`innerHeight - 顶部条 - 12`），滑条降级为"高度上限"（默认 1400，实际取值会被窗口截住）。
  这样**中间画布一屏看全**，**两侧栏各自 `overflow-y:auto` 上下滚**，滚轮落在侧栏里不再带动整页。

### 28.2 编辑态：让人一眼知道在改哪一块、改的是什么
- 画布底部常驻一条编辑浮条（`#habEditHud`）：`编辑中 · 第 N 块` + `工具：孔洞` + 该工具的下一步操作句 + 实时读数。
- 进入编辑时**其余块压暗到 42%**，被编辑的块保持原亮度，外圈加橙色虚线框和「编辑：第 N 块」角标。
- 实时预览（新增 `drawEditLivePreview`）：
  - 孔：虚线圆 + 圆心十字 + 半径线 + `Ø 150 px` 读数（正在拖的那个孔描边更亮）；
  - 缺口：橙色虚线圆；
  - 壁：实线高亮，正在拖的那条变蓝白；丝路：绿色虚线 + 正在拖的变亮绿；
  - 正在连点、还没收尾的顶点：蓝色虚线折线 + 方块顶点；
  - 外框轮廓绘制中：蓝色虚线多边形。
- **这些预览只画在 `paintWorld` 里，从不写进 agent 数据**：`ledScene()` / `ledCurves()` / 网页录制都只用 agent 的 `custom`，所以虚线、手柄、压暗都不会出现在成品图或视频里。HUD 上也直接写了这句话。

### 28.3 网页端直接导出视频（不再需要回本地跑脚本）
- 左栏新增「网页端导出视频」：分辨率 1280×720 / 1920×1080 / 2419×1360，时长 5 / 10 / 30 秒，24 / 30 fps，输出 **WebM（VP9 优先，回退 VP8）**。
- 实现：`ledRecordWebVideo()` —— 离屏 canvas + `captureStream(fps)` + `MediaRecorder`，实时录制；每帧只改 `agent.u`，42 块的几何只建一次（缓存），所以录制不会因重建而卡死。
- 为此把原生渲染的合成逻辑抽成 `ledComposeFrame(g, scene, T, isLoop, W, H, cache)`，**离线渲染与网页录制共用同一条画法**。
- 回归：重构后单帧与重构前逐像素对比 `PSNR = inf`（完全一致），见 `ck-frame200b.png`。
- 实测（无头 Chrome，真实时间，`probe_r20_rec.py`，720p / 30 fps / 5 s）：`已导出 weave_web_1280x720_5s.webm（0.8 MB）`，进度 20%→100%，150/150 帧，没有掉帧。
- 诚实的边界：网页端只能出 WebM（浏览器里没有 x264/ProRes）；2419×1360 @30 fps 在普通机器上大概率掉帧；要 ProRes 10-bit 母版仍然走 `render_led_frames.ps1`。

### 28.4 回归（P2 探针，引擎未改）
`probe_p2_accept.py` 重跑：60 格 × 3 层 @u=1 **11.31 ms/帧（88.4 fps）**；12 格 @u=0.55 5.30 ms（60 格外推 26.5 ms/37.7 fps）；
同 seed 113/113 中 `paths=164/164` 一致；圆孔内 **0/7116** 点；孔缘 276.6 vs 远区 269.0（≈1.03×）；u=0→1 亮度 0→108.7。

### 28.5 这版留下的取舍
- 编辑浮条贴在画布底部，会遮住最下面一行块的下边缘约 40 px；编辑时若嫌挡，把鼠标移出该块即可，浮条只在编辑态出现。
- 侧栏滚轮拦截用的是 `wheel` 的 `stopPropagation`（passive），不会阻止侧栏自己的滚动。
- 网页录制是实时的：10 秒片就要等 10 秒，30 秒片等 30 秒；期间页面不要切走（后台标签会降频）。
'''

with io.open(DOC, 'r', encoding='utf-8') as f:
    txt = f.read()
if u'## §28' in txt:
    print('already s28')
else:
    with io.open(DOC, 'w', encoding='utf-8', newline='') as f:
        f.write(txt.rstrip('\n') + '\n' + S28)
    print('appended', os.path.getsize(DOC))
