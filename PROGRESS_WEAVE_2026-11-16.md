# 织网引擎进度 · 2026-11-16（本轮）

对应计划：`PLAN_LED_WEAVE_2026-11-16.md`、`SPEC_WEAVE_ENGINE_2026-11-16.md`
执行：MainAgent 直接完成（用户确认「暂时不交给 GPT」）

---

## 0. 本轮结论

| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| P0 数据结构与指纹 | **契约完成，数据受限于素材** | 指纹已升级为 `silkworm-motion-profile/v1`；派生工具可用；现有轨迹是自动追踪结果，只能标 `assumption` |
| P1 单格生成器 | **已移植进 `docs/index.html`** | 原型 SDF + 占用场 + 直方图采样生长；主程序新增 `kind:'weave'` 单元（墙 + 丝 + 逐帧生长 + 面板 + 保存/导入） |
| P2 多格/分层/动画 | 原型内可用 | 60 格 × 3 层、逐帧确定重绘、母版脚本可跑 |
| P3 母版与导出 | 导出链完成 | SVG / curves JSON / scene JSON / PNG / Blender / TD 全部打通 |
| P4 现场 | 未开始 | 屏体宽高比、亮度、播放器待定 |

本轮修掉的一个真 bug：**闭合轮廓被退化简化成 2 个重合点，导致墙体在成片里完全不显示**。
`chainSegs()` 里对闭合链直接做 Douglas-Peucker，首尾同点使距离恒为 0，最终只剩起点和终点两个相同坐标，
`stroke()` 画出来是空路径。现在闭合链先去重收尾点再简化、最后显式补回闭合点，第 0 帧能正确显示空隔间。

---

## 1. P0：指纹契约

### 1.1 原型 `prototype/weave-lab.html`

`profileFromPoints()` 现在输出：

- `schema: silkworm-motion-profile/v1`、`wormId`、`label`
- `source`: `kind`（measured / assumption）、`project`、`calibrated`、`assumed`（当前为 `wallAffinity`）、`note`
- `fingerprint`: `stepMean`、`stepSD`(P25)、`turnHist`（36 桶归一化，覆盖 [0, π]）、`turnSignPersistence`、`maxTurn`(P95)、`curveAmp`、`radiusTyp` / `radiusMin`（R = ds/dθ 的中位数 / P05）、`pauseRate`（步长 < 0.25×中位数的占比）、`loopsPerEnvelope`、`bbox`
- `sampler`: `type: histogram`、`seed`、`temperature: 0.35`

统计前会按「跳变」切段：步长超过 `max(6×中位数, 2×P90)` 处视为跟踪身份错配/丢帧，不进入运动学统计。

### 1.2 生成器改为直方图采样

`growInCell()` 不再只用 `amp·cos(phase)` 振荡：

```
desired = heading
        + turnSign · histTurn · 0.55     // 从实测 turnHist 反 CDF 采样
        + amp · cos(phase) · 0.45        // 振荡兜底，保证环的节奏
        + noise · gauss(rng)
```

`turnSign` 按 `turnSignPersistence` 长度左右切换，保留「八字/回环」的方向持续性；
无 `turnHist` 时（演示指纹）退回原来的纯振荡。

### 1.3 `tools/derive_profile.py`（新增）

```
python tools\derive_profile.py data\projects\sample1_track.json data\projects\sample2_track.json --out profiles\auto-track --top 4
```

输出 8 个 profile。**重要红线**：`data/projects/sample{1,2}_track.json` 是自动追踪结果
（87 只短轨迹、存在身份跳变、`calibration: null`），不是人工描图。因此本工具默认标
`source.kind = "assumption"`、`quality = "auto-track"`，只能用于引擎联调；
人工描图数据加 `--measured` 才会标 `measured`，才允许进论文与展陈。

本轮产出的数字（px，未标定）：

| profile | 步长 | 典型半径 | 环数 | 转向持续 | 停顿率 |
| --- | --- | --- | --- | --- | --- |
| sample1-w269 | 31.06 | 68.07 | 75.24 | 1.69 | 0.582 |
| sample1-w153 | 28.65 | 42.57 | 58.85 | 1.58 | 0.633 |
| sample2-w212 | 14.87 | 91.78 | 31.75 | 1.57 | 0.636 |
| sample2-w51 | 31.15 | 107.98 | 44.93 | 1.53 | 0.583 |

环数偏高是自动追踪轨迹自身反复穿越造成的；这正是它不能当论文指纹的原因。

---

## 2. P1/P2：原型生成器现状

- 场景：10×6 格、3 层、覆盖目标 0.62、每格 2 蚕、种子 20261116
- 约束：`res = max(1.4, L/96)` 占用场；`markR = 0.65 × stepLen`；候选方向 `[0, ±0.12, ±0.26, ±0.42, ±0.58]`；
  打分 `free·3.2 + band·wallAff·0.5 - |偏移|·0.9`；卡 120 步退出
- 分层：`alpha = 0.16 + 0.40·(s/(strata-1))`（单层 0.62），2D 合成，不做真 3D 透明叠加

---

## 3. P3：导出链（本轮全部打通）

| 导出 | 契约 | 本轮状态 |
| --- | --- | --- |
| `weave-curves.svg` | `silkworm-weave-svg/v1`，mm | 可用（含墙体轮廓） |
| `weave-curves.json` | `silkworm-weave-curves/v1`，含 `screen` / `profile` / 每条 `cell·stratum·worm·u·width_mm·length_mm` | 可用，新增 `curvesPayload()` 统一构造 |
| `weave-scene.json` | `silkworm-weave-scene/v1`，config / profile / profiles / sampler / screen / cells | 可用，新增 `scenePayload()` |
| PNG → ProRes / H.264 | `scripts/render_led_frames.ps1` | 可用，新增 `-Resume` |

新增离线导出钩子：`?native=1&...&dump=curves|scene` 时把契约 JSON 写进 `<pre id="dump">`，
配合 `chrome --headless --dump-dom` 可在不点下载按钮的情况下取到完整 JSON（用于自动化验收）。

本轮实测样本（900×506 预览尺寸、seed 20261116）：

- 曲线：**360 条**，**265,240 个点**，`exports/weave-curves.json` 24.1 MB
- 场景：60 格，`exports/weave-scene.json` 24 KB

### 3.1 Blender

```
python tools\weave_to_blender.py exports\weave-curves.json --out exports\blender\weave_import.py
```

生成 `weave_import.py`：在 Blender 里 Run Script（或 `blender --background --python`）后得到
`SilkWeave` 集合，每条丝一根 POLY Curve，`bevel_depth = width_mm/2`，单位 m，原点在屏体中心，
`z = (stratum+0.5) · 0.35 mm` 分层，并写入 `cell / stratum / worm / length_mm / coverage` 自定义属性。
墙体暂不导入（Blender 端可由 `weave-scene.json` 的 cells 重建 SDF），避免给出错误的墙形。

### 3.2 TouchDesigner

```
python tools\weave_to_td.py exports\weave-curves.json --out exports\td
```

产物：
- `weave_td_script_sop.py`：贴进 Script SOP 的 `onCook`，用 `appendPoly(len, closed=False)` 逐条建折线，
  y 轴按屏幕向下取反，z 按层；单位 m
- `weave_td_points.csv`：265,240 行顶点表（tx/ty/tz/cell/stratum/worm/idx/u/width_mm/curve_id），
  供 DAT → Add SOP / Script SOP 做逐点动画、着色或按 cell 筛选

API 依据 Derivative 官方 `scriptSOP Class`（`clear()` / `appendPoly(numVertices, closed, addPoints)`）。

---

## 4. 验收记录（本轮实际跑的）

### 4.1 语法

`_backup/extract_weave_js.py` 拆出唯一脚本块 → `node --check`：**OK**（1102 行）
`python -m py_compile tools\derive_profile.py tools\weave_to_blender.py tools\weave_to_td.py`：**OK**

### 4.2 确定性（同 seed 像素级一致）

`?native=1&frame=2&total=5&w=900&h=506&seed=20261116&cov=0.62` 连跑两次：

```
a_f2.png       7B554229E8F04E98D8C271C564DC4E974A31DAE73DAC32D6A043233250176AB1
a_f2_again.png 7B554229E8F04E98D8C271C564DC4E974A31DAE73DAC32D6A043233250176AB1
```

换 seed=99：`436EA465305F45A5D232F9377076259B661B4BFB374572EBEF7375DDF309E96C`（不同）
同 seed 同帧 → 哈希一致，满足「同 seed 像素级一致」的硬指标。

### 4.3 逐帧生长

- frame 0：仅隔间墙体，无丝（`d_f0.png` 45 KB）
- frame 末：满密度（`d_f2.png` 829 KB）
- 说明墙体轮廓修复已生效

### 4.4 断点续渲

```
python scripts\render_led_frames.ps1 -Native "800x450" -Frames 3 -OutDir <tmp>          # 11.2s 出 3 帧
python scripts\render_led_frames.ps1 ... -Resume                                        # 跳过 3 帧，0 重渲
```

缺帧时会拒绝编码并 `exit 2`，避免母版时间轴错位。

---

## 5. 已知限制 / 下一步

1. **实测指纹缺位**：仓库里只有自动追踪轨迹。要拿到能进论文的 `measured` 指纹，需要用户在描图器里手工描 2–3 条，
   导出工程 JSON 后跑 `python tools\derive_profile.py <工程.json> --measured --out profiles\measured`。
   在此之前，所有展陈母版只能使用 `assumption` 指纹并在片头/文档中标注，不能声称是实测。
2. **P1 已移植，P2 多格/分层还没进主程序**：`docs/index.html` 的蚕室现在有 `kind:'weave'` 单格单元
   （一台「织网单元」= 一格，含墙体、丝、动画、参数面板、保存/导入）；60 格 × 3 层仍只在原型里。
   移植时未改动 `silkworm-habitat/v1` 现有字段含义，只新增 `weave` 可选字段。
3. **屏体宽高比未定**：`nativePx` 随 `areaM2/aspect/pitch` 自动算，当前 16:9 @ P1.5 → 2418×1360（3.29 MP）；
   若现场是 2419×1360 或 2565×1282，只改 config，不用改代码。
4. **母版耗时**：单帧约 3.7 s（800×450 测试），按 2418×1360 预计 5 s/帧，900 帧 ≈ 75 min。已支持 `-Resume`。
5. **墙体导出**：Blender/TD 目前只吃丝曲线；墙体需要从 `weave-scene.json` 的 cells 用 SDF 重建（TD 里可用 GLSL/CHOP 复算）。

---

## 7. P1 移植：主程序蚕室里的「织网单元」

代码位置：`docs/index.html` 蚕室 IIFE，`blocked()` 之后新增引擎段，`step()/paintWorld()/renderList()/syncRoutePanel()/bindRoutePanel()/exportHabitat()/importHabitat()` 各加一支。

### 7.1 新增函数

| 函数 | 作用 |
| --- | --- |
| `WEAVE_DEMO_PROFILE` | 演示指纹，`source.kind = assumption`，界面标注「演示（非实测）」 |
| `weaveProfile()` | 返回演示指纹（后续接 `profiles/measured`） |
| `weaveCellSpec(agent)` | 生成格子 SDF：`plain / notch / island / notchIsland` |
| `weaveSDF(cell,x,y)` | 矩形 + 缺角 + 内岛的有符号距离 |
| `weaveSimplify()` / `weaveChain()` | Douglas-Peucker + 闭合链修复（先去尾点再简化，最后补回） |
| `weaveContour()` / `weaveSDF` | marching squares 提取墙线 |
| `weaveGrowOne()` | 占用场生长：`res=max(2,min(W,H)/90)`；候选方向 ±0.9 rad；打分 `free·3.2 + band·wallAff·0.5 - |off|·0.9`；卡死时向空位跳跃（≤ `8+24·cov` 次） |
| `buildWeave()` / `makeWeaveAgent()` / `addWeaveAgent()` | 建格、建个体、放入场地 |
| `drawWeave()` | 画墙（常显）+ 丝（`lighter`、alpha 0.55、按 `u` 逐步显现） |

### 7.2 交互与持久化

- 「操作」区新增 **放入织网单元** 按钮；个体列表出现 `织网 wv-N` 卡片
- 右侧「选中调整」在选中织网单元时显示专有面板：织网宽/高（80–340 px）、覆盖率（0.15–0.85）、蚕数（1–6）、形状（矩形/缺角/内岛/缺角+内岛）、**重新织**、指纹来源说明
- 位置/速度沿用原滑杆；旋转、缩放、跟随对织网单元禁用（不适用）
- 覆盖率同时影响三件事：占用半径 `markR = stepLen·(0.52-0.22·cov)`、跳跃预算 `8+24·cov`、步数上限 `420+2800·cov`
- 开始/暂停/继续：`step()` 里 `u += dt/duration·speedScale`，到 1 自动 `idle`；再点开始会归零重播
- 保存 / 导出 / 导入都带 `weave:{w,h,coverage,shape,worms,seed,duration,u,wallAff}`，导入后按同 seed 重建，结果与导出前逐点一致
- `window.__studioHabitat` 增加 `agents()` 与 `addWeave()`，便于自动化验证

### 7.3 验收（无头 Chrome，`_backup/make_weave_qa.py`）

- 默认 252×252、3 条丝、覆盖率 0.55：**2,629 点**，墙体 1 条闭合线，画面为密集嵌套环 + 交叉丝
- 覆盖率单调：0.30 → 2,451 点；0.55 → 2,746；0.80 → 3,185
- 形状：`plain` 1 条墙线 / `notch` 1 条（凹多边形合并）/ `island` 2 条（外框 + 内岛）/ `notchIsland` 2 条
- 保存→导入闭环：`paths 3 / points 2816 / walls 1` 前后完全一致
- `u=0` 时只有墙，随动画逐段长出丝（见 `qa-weave-hold.png` 与 `qa-weave10.png`）
- 三副本 `docs/index.html` / `editor/silkworm-tracer.html` / `editor/蚕轨迹描图器.html` SHA256 一致

### 7.4 仍未做

- 多格阵列与分层合成（P2）仍在原型，主程序一次只放一个织网单元
- 织网单元的真蚕「爬行头」还没画，只有丝在长
- 指纹固定为 `assumption`，等人工描图后换成 `profiles/measured`

---

## 9. P2：无边界格网 + 八字运动语法（本轮）

### 9.1 为什么改

- 用户的实拍/描图反馈：蚕在一次框定里走的是**拉长的八字**（两瓣叠在一个交叉点），不是同心螺圈。
- 单格单元也不该有外边界：格子要能**一直延伸**，观众平移/缩放时继续长出新格。

### 9.2 实现

- **运动语法换成 Lissajous 八字**：`x = ax·sin t`、`y = ay·sin 2t`（纵向振幅 > 横向），随机旋转 ±0.45 rad；每格 1–3 个包络连成一根丝；点用 SDF 法线投影回格内（不穿墙、不进内岛）。
- **格网无限延伸**：一个 `kind:'weave'` 个体 = 一整片格网。格子按 `(ix, iy)` 惰性生成，内容由 `seed ^ hash(ix,iy)` 决定；只画视口内（最多 17×17）的格子，缓存上限 360 格，平移/缩放自动补新格。
- **每格参数**：格子宽高（80–340）、覆盖率（1–3 个包络 + 尺寸）、每格蚕数（1–6 条丝）、形状（矩形 / 缺角 / 内岛 / 缺角+内岛，逐格随机位置）。
- **指纹载入**：右侧新增「载入指纹 JSON」，读 `silkworm-motion-profile/v1`；`source.kind='measured'` 会显示「实测」，否则仍标「演示（非实测）」。指纹当前只影响包络数量与纵横比，细节采样仍走内置语法。

### 9.3 验收（无头 Chrome）

- 225×225 格、覆盖率 0.55、每格 2 条丝：每格 604 点、墙 1 条闭合线；视口内 36 格全部生成。
- 导出→导入：`w/h/cov/shape/worms/seed/sample` 完全一致（sample `3? → 2 条丝 / 453 点` 按参数而定），缓存按需重建。
- 画面：竖长八字包络 + 逐格交叉，无螺圈；格线随视口一直向外延伸。
- 三副本 SHA256 一致；三个脚本块 `node --check` 全绿。

### 9.4 仍未做 / 限制

- **仍不是实测行为**：仓库里没有人工描图的 `measured` 指纹，默认仍是 `assumption`；要真按某只蚕走，需在描图器里描 2–3 条后导出 profile，再点「载入指纹 JSON」。
- 分层（strata）尚未进主程序：P2 剩下的那一半。
- 格网是程序生成的规则矩形 + 逐格缺口，还没到参考图那种连续迷宫轮廓。
- 缩放到很远时有 17×17 格上限，再远会看到格网边界。

---

## 10. P2 修正：细网格 + 八字/爬行交替 + 实测样本纵横比

### 10.1 用户澄清（第二轮反馈）

- 「格子无界限」指的是**细密的场地网格**（约 10mm 一格、铺满视口、随缩放延伸），不是大格网的格墙。
- 八字要**严格按截图形态**：平滑竖长两瓣 + 交叉，织完一个后沿**直线爬行**到下一处再织。
- 运动形态来自**真实蚕样本**：`G:\raby model\trajectories.json`（curves3d/v2，worm 1，2 笔 272 点，标定 61.06 px/mm，cell 10mm）。
- 八字是**单次吐丝运动模式**，蚕在空间里爬来爬去、重复延伸。

### 10.2 实现

- **画法**：去掉大格墙线，改为细网格铺满整个视口（间距随缩放取 2 的整倍，对齐个体原点，`rgba 0.12`）；网格没有边界，缩放/平移一直延伸。
- **运动语法**：每条丝 = `织八字 → 直线爬行过渡 → 再织八字 → …`（覆盖率决定 1–3 次重复）；八字为平滑 Lissajous（x=sin t, y=sin 2t，纵向>横向），随机旋转 ±0.45 rad、随机镜像；吐丝点活动范围按环圈半径收边，避免环圈被格边压平。
- **实测参数**：八字纵横比默认取实测样本两笔丝迹的均值（1.78 / 1.45 → 1.6）；载入 measured 指纹时用其 `fingerprint.strokeAspects`。样本原件已入库 `data/projects/raby_sample/trajectories.json`，指纹 `profiles/raby-worm1.json`（measured，含 pathTemplate 备用）。
- **诚实标注**：环圈形状是理想化平滑八字，参数（纵横比、弧长尺度）来自实测样本；真实折线逐点回放（pathTemplate）已留接口、暂未接入。信息行显示「八字纵横比：实测样本 raby-1 · 其余参数：演示」。

### 10.3 验收

- 173% 放大截图：平滑竖长八字 + 直线爬行过渡，形态与用户草图一致；细网格铺满视口并延伸出场地边框。
- 导出→导入回归：`w/h/cov/shape/worms/seed/sample` 完全一致（每格 2 条丝 368 点），profile 字段随场景保存。
- 三脚本块 `node --check` 全绿；三副本 SHA256 `5829CD76…1390`（293,533 B）。

### 10.4 下一步

- 真实折线逐点回放：用 pathTemplate 让八字的每一次环绕按真实丝迹的形状走（当前只用了纵横比）。
- P2 剩余：分层 strata 进主程序（原型已有 3 层实现可参考）。
- 跨格连续性：让相邻格的丝在边界处衔接（当前每格独立成丝）。

## 11. P2 重构：黑底密织 + 形状可编辑 + 实测轨迹回放（2026-11-16）

### 11.1 用户新诉求（本轮四组）

1. 场地黑底；删掉原背景画布里的（大）格线；删掉桑叶功能。
2. 细密格子无边界、可一直延伸；网格不跟织网单元移动（世界锚定），可隐藏。
3. 织网单元可自建、形状（壁 / 路径）必须能人工放置与调节；自动生成的随机布局也要能改。
4. 测试蚕用 `G:\raby model\trajectories.json` 的真实运动；运动模式真实的前提下还原参考图（黑底马赛克织块 + 大圆孔负空间 + 块间黑缝 + 亮度不均）。

### 11.2 实现

- **黑底 / 删桑叶 / 删旧格线**：`paintStatic` 改为纯黑，去掉边缘叶片绘制；桑叶面板区块与事件、`blocked()` 的叶子判定、pointerdown/move/up 的 leaf 分支全部删除；`habitat.tool` 固定 `worm`。
- **网格世界锚定 + 可隐藏**：细网格从 `drawWeave`（跟随个体）搬到 `paintWorld`，间距 40 世界单位、按视口裁剪，`habitat.showGrid` 控制，面板勾选框 `habGridToggle`。
- **格内容（参考图形态）**：每格 SDF = 格框 ∩ 非缺口 ∩ 非圆孔；`cell.islands[]` 1–2 个大圆孔（r = 0.15–0.25 min(W,H)），缺口含「贴边半圆」与「四角四分之一圆」两种；格墙只描极淡方块缝 `rgba(206,216,210,0.16)`；按格哈希留约 12% 空格（swatch 黑缝），亮度按格哈希 0.30–0.60。
- **运动真实回放**：`weaveThread()` 不再用 Lissajous 八字，改为**实测折线逐笔回放**——`WEAVE_MEASURED_PATHS` 为 raby 样本两笔丝迹（弧长重采样、归一化 [-1,1]）；每根丝 4–9 笔：随机取一笔 → 随机镜像/旋转（同丝内保持主方向）→ 缩放到格高的 30%–58% → 落在绕圆孔的螺旋环带上（黄金角错开）→ 笔间以直线爬行过渡；遇到格边/圆孔则**断笔**（`weaveAllowed()` 显式几何判定，不做投影拖拽），保证不穿墙、孔洞干净。
- **密织**：`worms` 默认 8（面板 1–12），每格约 60–100 根丝、1000–2300 点。
- **形状编辑**：`habWeaveEdit`（进入/退出）、`habWeaveEditMode`（壁/丝路）、画布点顶点 + 双击结束（`finishWeaveEditLine`）、`habWeaveEditEnd`、`habWeaveEditClear`；草稿按格分桶（`e.drafts["ix,iy"]`）跨格不丢；自定义存 `agent.custom = { walls:{"ix,iy":[{pts}]}, paths:{...} }`，壁参与 `weaveWallRepel`（半径 `0.03 min(W,H)`），丝路直接混入该格丝迹并加亮绘制；清空只清当前格。
- **持久化**：`export`/`habSave` 的 weave 对象带 `custom`；`importHabitat` 恢复 `custom` 并把旧场景的 `shape/worms` 默认补成 `island/6`。
- **修复**：`__studioHabitat` 里仍引用已删的 `weaveFigureEight` 会导致该轮 ReferenceError（面板绑定与渲染整体失效），改为导出 `weaveThread` / `weaveTemplates`。

### 11.3 验收（无头 Chrome 1500×1000，注入 `u=1`）

- 引擎探针：9 格全部生成，每格 6–8 根丝/段、1000–2300 点，`islands` 1–2、`bbox` 均在格内（±117 / 225），无 NaN，运行时错误 0。
- 编辑烟测：`开始编辑 → 3 个顶点 → 双击结束` 记下 1 条壁（`custom` 计数 +1）→ 清空归零 → 退出编辑；无异常。
- 视觉：黑底、细网格世界锚定、织块边缘仅淡缝、每块中央一个黑圆孔、丝迹为实测折线的密集环带；与参考图同构（密度/孔洞比仍待继续调）。
- 三脚本块 `node --check` 全绿；三副本 SHA256 `F023953E…3949`（302,635 B）。

### 11.4 下一步

- 参考图还原继续：织块内层次（近孔密、边缘疏）、亮度不均与丝线粗细分级、块间缝更深。
- 分层 strata 进主程序；跨格丝线衔接；「一蚕一格 / 一格多蚕」共织模式。
- 屏体长宽比（2419×1360 / 2565×1282）与母版输出盘位待定。

## 12. 顶部 JSON 往返 / 残留场地边框 / 手柄式编辑（2026-11-16 续）

### 12.1 用户报的三个问题与根因

1. 顶栏「JSON」导出后再「载入 JSON」，弹窗「未识别到可用轨迹点列」。
   - 根因：`exportJSON()` 写的是 `curves3d` + `silkworms` 两种结构；`normalizeIncoming()` 只认 `type=silkworm-preview/v1`、`schema` 含 motion-model、`unifiedTrajectories`、`curves`、`worms`（对象），**没有 `curves3d` 与 `silkworms` 数组**两条分支，未标定的数据（`x_mm: null`，只有 `x_px`）也没兜底。
2. 背景仍有一个大方框。
   - 根因：`paintWorld()` 里还画着场地边界（`arenaSpec()` 的矩形/圆，`rgba(230,236,233,0.45)`、1.2px）；`paintDepth()` 仍有前景叶片 + 环境光 + 暗角，`paintMist()` 还有两团绿色柔光，`.hab-world` CSS 还带径向渐变。
3. 织网单元与单元内壁/路径只能靠滑条，不能像建模软件那样拖。

### 12.2 实现

- **导入兼容**：`normalizeIncoming()` 新增两条分支——`curves3d` / `curves` 数组（点坐标 `x_mm` 优先，`null` 时回落 `x_px`，再回落 `p.x`）与 `silkworms` 数组（同规则）；同时带回 `unit/calibration/provenance/behaviorBoxes`。导出→导入往返不再丢点。
- **黑场到底**：删掉 `paintWorld` 的场地边框绘制；`paintDepth` 只清屏（删叶片/环境光/暗角）；`paintMist` 只清屏；`.hab-world` 背景改 `#000`。场地范围仍由 `insideArena()` 判定，只是不再画出来。
- **手柄式编辑**（选中织网单元 → 「开始编辑形状」后出现）：
  - 橙色角点：拖角改单元宽高（对角固定）；橙色十字：拖动画布移动整个单元。
  - 青色实心点：拖圆孔/缺口中心；青色空心圈：拖半径改孔洞大小。
  - 自定义壁/丝路顶点：白色小方块，可直接拖动；`Alt+点` 删顶点；点空白继续加点、双击结束当前线。
  - 手柄命中优先于加点，命中半径 10px（按当前缩放换算世界距离）。
  - 手改动写入 `agent.custom.shapes["ix,iy"] = {notch, islands}` 与 `custom.walls/paths`，`weaveCellContent()` 优先用人工覆盖，随场景 JSON 保存。
- **交互提示**：底部 hint 与面板说明改成手柄语义（拖角/拖十字/拖青点/拖青圈/Alt 删点）。

### 12.3 验收

- 手柄拖拽探针：圆孔中心 `(-26.28,-10.49)` → `(-2.01,7.71)`（屏幕 +40/+30 对应世界位移一致）；随后画壁三点写入 `custom.walls["0,0"]`，`sample.custom` +1。
- 无头截图 1500×1000：纯黑底、无场地边框、无叶片/柔光；选中单元出现橙/青/白三类手柄；`node --check` 三块全绿。
- JSON 导入：新增分支对照 `exportJSON()` 的输出结构逐字段核对（`curves3d.points[x_mm|x_px]`、`silkworms.points[x_mm|x_px]`）；本条待真实文件再点一次确认。

### 12.4 下一步

- 「新建织网单元」也走多边形：直接点轮廓顶点生成自定义外框（当前先用矩形 + 角点缩放）。
- 壁做成可弯的折线/曲线（拖控制点加平滑），丝路支持闭合。
- 参考图还原继续：孔洞与块缝比例、亮度分层。

## 13. 单元一个一个放 + 蚕满场巡游（2026-11-16 续）

### 13.1 用户反馈与根因

1. 「格网不是一个个放置，而是整个画面里有很多单元格」
   - 根因：`drawWeave()` 按视口裁剪遍历 `i0..i1 / j0..j1`，把可见范围内所有格都画出来，于是一个单元会被摊成满屏马赛克。
2. 「蚕进场地只在原位置重复运动，不在整场 / 格里爬」
   - 根因：`normalizeRoute()` 把导入的实测轨迹整体缩放到 110 世界单位（场地半径约 350），`step()` 里 `agent.u = (u + …) % 1` 又对这段小轨迹取模循环——蚕被锁在中心一小块地方反复画同一笔。

### 13.2 实现

- **一个单元 = 一格**：`drawWeave()` 改成只渲染本单元自己的 `(0,0)` 格；视口铺格逻辑抽成 `weaveVisibleCells()`，只有显式 `tileField: true` 才启用（默认 false，随场景 JSON 保存）。要几块就手动放几个单元。
- **手放单元不留空格**：空格阈值（`hash > 0.88`）只在整场铺格模式生效，手动放的单元一定织满。
- **形状编辑只在本格**：编辑时点击单元外会提示「只在当前单元这一格内」，不再自动切到相邻格。
- **蚕满场巡游**：`step()` 的 route 分支改成「局部实测形态 + 整体巡游」叠加——
  - `u` 继续按实测折线回放（保留真实笔迹与笔长），`travel` 另行累积；
  - `roamPoint(agent, travel)` 给出一条覆盖整场的合成巡游线（半径 `0.20–0.82 × 场地半径`、角速度 2.05、带每只蚕的相位），蚕位置 = 巡游点 + 旋转/缩放后的实测笔迹（×0.6）；
  - 丝点阈值降到 2.2，上限 6000 点，整场都能留下丝迹。
  - 诚实标注：**局部笔迹是实测的，整场巡游方向是合成的**（用于展陈铺满，不是实测路径），接口导出 `roamPoint` 便于外部复现。
- **吐丝头**：`drawWeave()` 在未织完的格里沿已织出的丝画一个亮点，能看见「蚕正在这一格里往前爬」。
- 文案统一为「织网单元」（去掉「格网」旧称）。

### 13.3 验收

- 单格渲染：`u=1` 截图只剩一个 225×225 单元，不再满屏格。
- 半程渲染：`u=0.45` 截图可见未织完的丝 + 吐丝头亮点。
- 巡游探针（`_backup/probe_roam.py`，注入 60 点实测样式 route，模拟 60 s / 600 步）：
  - `travel=4.50`、`silkPts=591`；
  - 丝迹包围盒 `x[-149.3,60.2] y[-91.3,159.3]`，跨度 `209×251` 世界单位（此前锁在 110 单位内）；
  - `roamPoint` 采样 `t0(-17,121) t10(-59,43) t20(14,-7) t30(124,-114) t40(-31,-64)`，覆盖四个象限。
- `node --check` 三块脚本全绿。

### 13.4 下一步

- 织块结构还原：现在每条丝是同向密排的长折线，块内偏「乱线」；要改成沿主方向的往复密排 + 圆孔周围环带加密，接近参考图的马赛克织块。
- 多单元拼块时的缝宽 / 亮度分层；分层 strata 进主程序。

## 14. 织块质感重构：细纤维密排 + 环带（2026-11-16 续）

### 14.1 问题

第 13 轮的单格虽然只有一个块，但块内还是「几条大折线来回盖」，视觉上像乱麻 / 大片长线，不是参考图那种细密、有方向、带皱褶的织块。

### 14.2 实现

- `weaveThread()` 重写为**一根细纤维**：
  - 先定织块主方向 `weaveBandAngle(cell)`（同格所有丝同向，由格坐标哈希决定，±26°）；
  - 每根纤维沿主方向横穿整块，横向偏移按 `bandIndex/bandCount` 均分（排得越密越接近参考图质感）；
  - 皱褶用**折线随机游走**（每 6 个采样点换一次偏移目标、按 0.32 阻尼跟随）叠加一个小幅正弦，比纯正弦更像真实丝；
  - 抖动幅度由**实测笔迹归纳**：`amp = min(W,H) × (0.010 + coverage × 0.010)`，频率由实测折线相邻点的纵向差之和决定。
- 纤维条数 `bandCount = worms × 12`（16–160 之间），`每格蚕数` 滑条现在直接控制织块密度。
- 圆孔 / 缺口边缘加**环带**：半径从孔边往外递进 0.016·min(W,H)/圈，3–12 圈，每圈切两段弧，形成参考图那种「绕着黑孔的密丝」。
- 逐丝透明度：`weaveCellContent()` 给每段丝 `a = 0.25 + hash × 0.35`，绘制时按块亮度再缩放 → 块内有明暗层次。
- 线宽提高到 `1.15 × max(1, s × 0.6)`，接近参考图的密度感。

### 14.3 验收

- `u=1` 单格截图：225×225 块内 139 段丝、7419 点，主方向一致、细密皱褶、孔周有明显环带；孔洞为纯黑负空间。
- `u=0.45` 半程：纤维逐段生长 + 吐丝头亮点可见。
- `node --check` 三块脚本全绿。
- 与参考图对照仍差一层：**块间缝宽/块亮度分级**还没做（手放单元之间留多大空隙由人决定，亮度分层在下一步）。

### 14.4 下一步

- 块亮度分级：给每个单元一个 `tone`（参考图里有明显深浅不同的块），参与绘制 alpha。
- 块间缝：单元可设 `gap`，绘制时四周留黑边。
- 性能：单元多了以后每帧要重画上万点，计划把「已织满」的块缓存成离屏 canvas，只对未完成的块走逐点动画。
- 分层 strata（2D 合成）进主程序。

## 15. 块亮度 / 块缝 / 离屏缓存 + 逐丝推进（2026-11-16 续）

### 15.1 实现

- **块亮度 `agent.tone`**：0.4–1.2，默认按单元种子落在 0.62–1.12（每块深浅不同，接近参考图里明暗不一的织块）；面板新增「块亮度」滑条可手调。
- **块缝 `agent.gap`**：0–40 世界单位，默认 8；绘制时把单元四边各裁掉 `gap/2`，形成参考图那种块与块之间的硬黑缝。面板新增「块缝」滑条。
- 两者都进场景 JSON（`weave.tone` / `weave.gap`），导入时带范围钳制。
- **离屏缓存**：`lu ≥ 0.995`（已织满）的块改由 `weaveRasterFor()` 生成 512px 离屏位图，按 `seed + 尺寸 + tone` 做键，之后每帧只 `drawImage` 一次；未织满的块仍走逐点动画。单元多了以后不再每帧重画上万点。
- **逐丝推进**：绘制从「所有丝按比例同时长」改成「按丝的累计长度顺序推进」——`weavePathCum()` 先算每条丝长度与前缀和，`target = lu × 总长`，蚕是一根一根往前织，吐丝头落在当前断点处，看起来就是蚕在块内爬行吐丝。

### 15.2 验收

- `u=1`：块内 149 段丝 / 6878 点，四周有黑缝（默认 8），亮度按 tone 分层；走的离屏位图路径。
- `u=0.55`：上半块已织满、下半块还空着，环带只画出上段，吐丝头在断点处（截图可见）——推进顺序符合「一根一根织」。
- `node --check` 三块脚本全绿。

### 15.3 下一步

- 分层 strata（3 层 2D 合成）进主程序，给织块加纵深。
- 「新建单元走多边形轮廓」（`§12.4`），壁支持控制点平滑。
- 参考图的整体构图：单元自动排版成马赛克网格（现在靠手动放 + 拖）。








```powershell
# 1) 指纹
python tools\derive_profile.py data\projects\sample1_track.json --out profiles\auto-track --top 4

# 2) 原型出图（3 帧 900×506）
powershell -File scripts\render_led_frames.ps1 -Native "900x506" -Frames 3 -OutDir "C:\Temp\weave-render"

# 3) 导出契约（无头 Chrome dump）
# chrome --headless=new --dump-dom "file:///.../weave-lab.html?native=1&frame=1&total=2&w=900&h=506&dump=curves"
python _backup\extract_dump.py dump.html exports\weave-curves.json

# 4) 下游
python tools\weave_to_blender.py exports\weave-curves.json --out exports\blender\weave_import.py
python tools\weave_to_td.py exports\weave-curves.json --out exports\td
```

## §16 分层 strata / 多边形轮廓单元 / 有限块群（2026-11-16，第 8 轮）

用户本轮三项要求：① 织块要有分层（strata）；② 新单元按多边形轮廓创建，而不是只能拖矩形框；③ 不要无限格子，要有限数量、贴近参考图的块群。

### 16.1 分层（2D strata 合成，不用 3D 半透明叠）

- `agent.strata`（1–3，默认 2），面板「分层」滑条可改，导出/导入带 `strata`。
- 每层：`off = (L-(n-1)/2)*cw*0.012` 的微小位移 + `tone` 递减 `1-L*0.10`，`L=0` 先铺一遍粗线柔雾（`lineWidth*3.4`，alpha 0.04–0.14），再叠细纤维。
- 已织满（`u>=0.995`）的块走 `weaveRasterFor(..., light, tone, strata)` 离屏位图，缓存键含 `strata`；未织满仍逐丝推进（沿 `weavePathCum` 的实际丝长顺序）。

### 16.2 多边形轮廓单元（像建模软件那样手画 + 拖顶点）

- 新按钮「按轮廓新建单元」→ `startOutlineUnit()`：画布上依次点顶点（凹多边形也行），双击 → `finishOutlineUnit()` 按 bbox 建单元、`outline` 存相对中心的顶点、`shape='island'` 保留大圆孔；Esc 取消。
- 编辑已有单元：`habWeaveEditMode` 增加 `outline`，点顶点后双击即 `agent.outline = pts - 中心`，`buildWeave` 重建。
- `weaveHandles` 新增 `outlineV` 白点手柄：可拖动改顶点、Alt+点删顶点（少于 3 个拒绝）。
- 可织区域：`weaveAllowed` 对 `cell.outline` 走 `weaveInPoly` + `weavePolyDist`（壳内且距边 ≥ margin），外框描一道 `rgba(206,216,210,0.07)` 的边。
- 壁的渲染与评估都过 `weaveSmooth`（Catmull-Rom，`closed` 默认 true），人工画的壁是曲线而不是折线。

### 16.3 有限块群（贴参考图，不铺满）

- 新按钮「铺块群（≤20）」→ `addWeaveMosaic()`：5×5 位阵、间距 `tile*1.03`、随机挑约六成（`want = max(9, round(cand*0.62))`，总数上限 20）；单元边长 `tile = min(spanW/4.6, spanH/4.6)`（参考图 1095px 宽、块≈245px ≈ 1/4.5 场宽）。
- 每块：`gap=8` 硬黑缝、`strata=2`、`worms=6`、`tone=0.58–1.13`、`shape` 72% `island` / 28% `notchIsland`、`u=0`，放完每块都能单独拖 / 改形状 / 改亮度。
- 纤维方向：`weaveThread` 里 32% 的带在 `weaveBandAngle` 基础上再偏 ±(0.35–0.77) rad，形成参考图那种交错马赛克纹理（不是单向拉丝）。
- 整体亮度乘 0.82，块间 tone 差更接近参考图的黑白分层。

### 16.4 验收（无头 Chrome 截图）

- `_backup\probe_weave_mosaic.py`：点「铺块群」，16 块（5×5 位阵 62% 抽样），块 77×77，`gap 8 / strata 2 / tone 0.59–1.03`，各块大圆孔位置随机、块间硬黑缝、亮度分层可见。
- `_backup\probe_outline_unit.py`（模拟 4 次 pointerdown + dblclick）：新建 1 个轮廓单元，`outline=4`、`w=208 h=195`，织块按多边形裁剪、内含大圆孔。
- `node --check` 三块脚本（outer_0 / outer_1 / srcdoc_0）全绿。
- 截图：`C:\Users\54364\AppData\Local\Temp\qa-mosaic6.png`（整片块群）、`qa-outline2.png`（轮廓单元）。注意 canvas 内部高 2222px，headless 必须 `--window-size=1500,2400` 才能看全场地。

### 16.5 已知未完成

- 块群仍是「5×5 位阵抽样」的规则骨架；参考图里块边缘有轻微错位与缺块轮廓，需要再加不规则化。
- 轮廓单元的点集仍是手点折线，虽已可拖顶点，但还没有「点中边插入顶点 / 双点平滑手柄」。
- 跨格/跨单元丝线连续性、整场 `tileField` 模式（默认关）仍是 P2 余项。

## §17 织块线条改用实测丝迹回放（2026-11-16，第 9 轮）

用户指出「现在的线条应该不是实际上的蚕吐丝轨迹模式」，确认属实：上一轮的纤维是「沿格主方向的带 + 随机游走皱褶 + 正弦」合成的，实测折线只用来归纳振幅，不是真回放。

### 17.1 改动

- `WEAVE_MEASURED_PATHS` 用 `_backup\gen_measured_paths.py` 从 `G:\raby model\trajectories.json` 重新生成：两笔完整点列（114 / 158 点），每笔弧长重采样到 140 点、逐笔等比归一化到 [-1,1]，共 280 点（此前是 56 点降采样）。
- `weaveThread` 主体改为「实测折线回放」：每条带取一笔实测折线，缩放到约 0.15–0.19 格宽、随机旋转 ±0.5 rad、随机散布到格内任意位置；`fit/cxx/cyy` 由每带的 rng 决定。线条形状完全来自实测点列。
- 密度与亮度：`bandCount = worms*8`（默认 48 条/格），单条丝 alpha 0.10–0.26（���交 0.25–0.60），叠加后是参考图那种灰阶网状而不是过曝白团；孔周环带照旧由 bi===0 画。
- 顺带修了一个真 bug：`weaveCellContent` 构造的 `cell` 之前漏了 `cell0.outline`，多边形轮廓单元实际按矩形 bbox 织；现已带上 `outline`，`weaveAllowed` 的 `weaveInPoly / weavePolyDist` 才真正生效。

### 17.2 验收

- `node --check` 三块脚本全绿。
- 块群截图 `qa-mosaic9.png`：16 块、每块细密曲线小圈（实测折线的缩略复制）、大圆孔负空间、块间硬黑缝、块亮度分层；不再是单向拉丝或水纹。
- 轮廓单元 `outline` 现在参与裁剪（矩形 bbox 内但多边形外的区域不落丝）。

### 17.3 关于样本

- 当前唯一实测样本就是 `G:\raby model\trajectories.json`（curves3d/v2，wormId 1，两笔 29.5mm / 40.9mm，标定 61.06 px/mm）。要换另一只蚕，把它的 trajectories.json 给我，跑一遍 `_backup\gen_measured_paths.py` 即可替换模板，不用改代码。
- 仍属「假设」的部分：块的排布位置、孔洞位置、块亮度梯度是程序生成的（`source.kind='assumption'`），不进论文与展陈数据；只有丝迹形状来自实测。

## §18 修掉「两层一样的图错位叠加」+ 块群不规则化（2026-11-16，第 10 轮）

### 18.1 鬼影根因

上一轮 strata 的做法是：整套 `content.paths` 每层各画一遍，只把层整体平移 `cw*0.012`（≈1 px 世界、屏幕 2 px），亮度递减 10%。因为几何完全相同、位移又很大，视觉上就是「两张同样的网错开叠着」——用户看到的正是这个。

### 18.2 修法

- `weaveCellContent` 给每条路径记上带序号 `b`。
- `drawWeave` / `weaveRasterFor` 的分层改为**按带序号分集合**：第 L 层只画 `b % layers === L` 的丝，层间错位降到 `cw*0.006`（亚像素级），线宽逐层 −8%、亮度 −12%。同一根丝只出现一次，不再有第二份复制。
- 柔雾只铺一遍（全量、不位移、alpha 0.03–0.09），不再每层铺一次。
- 密度补偿：`bandCount = worms*12`（默认 72），单条 alpha 0.13–0.35，分层后总密度与上一版相当，但看到的是「一层丝压一层丝」，而不是两张图。

### 18.3 丝迹铺法（顺着上一轮实测回放继续）

- 每格按 4×4 小块位阵铺真实折线：`tileN=4`，`ti = b % 16`，`vi = b / 16`，每格位置再叠 4–5 份不同转角（`vi*0.5 rad`）与缩放（0.17–0.22 格）的副本，位置带 ±35% 子格抖动。
- 这样块内密度均匀、没有大片空洞，线条形态仍是实测折线的循环小圈（不是随机散点）。

### 18.4 块群不规则化

- `addWeaveMosaic` 每块位置 ±4% 方格抖动、边长 ±5% 抖动，块边缘出现参考图那种轻微错位；亮度仍 0.58–1.13 随机。

### 18.5 验收

- `node --check` 三块脚本全绿。
- 截图 `qa-mosaic13.png`：16 块，块内是均匀细丝网 + 大圆孔，块间硬黑缝，块边缘可见轻微错位；无叠影。
- 仍属程序生成（`assumption`）：块位置、孔位、亮度梯度。

### 18.6 下一步候选

- 跨单元丝线连续性（蚕从一块爬到相邻块时丝不断）。
- 块群缺块轮廓（参考图有些位置是纯黑，不是整齐缺一列）。

## §19 蚕的活动范围可选：单格内 / 跨格（2026-11-16，第 11 轮）

用户要求「蚕是在一个单元格内活动还是在多个单元格内活动是可以选择的」。

### 19.1 改动

- 右侧「选中调整」面板新增下拉 `habAdjScope`：`整场 / 跨格`（默认）与 `单个单元格内`。
- 每个 route 蚕带 `scope`（`'field'` / `'cell'`）和 `homeUnitId`；导出/导入都带上这两个字段，换机子打开保持原选择。
- `roamPoint` 分两支：
  - `cell`：巡游中心绑到最近的织网单元（首次自动取最近的，之后记住 `homeUnitId`），半径 `min(w,h)*0.30`，蚕只在格内绕爬，丝落在格内。
  - `field`：沿用原来的整场巡游（半径 0.20–0.82 场、角速 2.05、每蚕相位 `wormId*1.7`）。
- 切到「单格内」但场地还没有织网单元时会提示「先放一个/铺一块群」，此时暂时仍按整场跑，放下单元后自动收进格内。

### 19.2 验证（`_backup\probe_scope.py`，无头 Chrome）

- `scope select=yes`；场地 16 个织网单元。
- `cell` 模式：240 步内 `max |dx|/halfW = 0.60`（≤1，说明始终在单格内）。
- `field` 模式：`max |x| = 134`、`max |y| = 127`（跨整场，远超单格 77/2）。
- `node --check` 三块脚本全绿。

### 19.3 说明与边界

- 这里的「单格/跨格」控制的是**蚕本体（可见爬行 + 自己吐的丝路）**的活动范围；织块的填充进度仍按 `u` 推进（每块从 0 织到 1），两者目前是解耦的。
- 如果要做「蚕在某格吐丝 → 该格随之长满」的真联动，需要把块的 `u` 由格内丝长驱动（P2 余项，下一步候选）。

## §20 P2 验收：60 格 × 3 层性能、动画连续、覆盖与圆孔（2026-11-16，第 12 轮）

按 `SPEC_WEAVE_ENGINE_2026-11-16.md` §10/§11 的验收口径，用 `_backup\probe_p2_accept.py`
（同步执行、无头 Chrome 真实计时）逐条测。

### 20.1 本轮修掉的问题

1. **覆盖滑杆此前是死的**：`weaveThread` 里算了 `cov` 但没用在几何上，`bandCount` 也固定。
   现在覆盖率同时驱动两件事：
   - 笔迹尺寸 `fit = min(W,H) * (0.10 + cov*0.16 + rng*0.04)`；
   - 排数 `bandCount = worms*12 * (0.55 + cov*1.3)`；
   - 单条丝 alpha 也随覆盖率 `*(0.72 + cov*0.5)`。
   0.2 → 0.7 渲染亮度 76.7 → 97.5，单调且可见（+27%）。
2. **洞缘环带不够密**：环数 `min(W,H)*0.009`、上限 18 环、每环 6 段弧（原 0.014 / 14 环 / 3 段）。
   洞缘与远区的点数密度比从 1.45× 提到 **2.03×**，贴近参考图「孔边一圈明显更亮」。
3. 探针需要确定性调用，给 `window.__studioHabitat` 补了 `buildWeave` / `drawWeave` / `weavePathCum` 导出。

### 20.2 验收结果

| 验收项（SPEC §11） | 实测 | 结论 |
| --- | --- | --- |
| 60 格 3 层 1000px 预览帧率 | 11.31 ms/帧 → **88.4 fps**（满织走位图缓存） | ≥24 fps ✓ |
| 生长中（u=0.55）逐笔重画 | 12 格 3.75 ms；按 60 格外推 18.8 ms → **53.3 fps** | ≥24 fps ✓ |
| 同 seed 两次生成 | paths 242/242，不一致点 **0** | 逐点一致 ✓ |
| 覆盖 0.2→0.7 单调 | 亮度 76.7 → 84.8 → 90.5 → 96.0 → 97.5 | 单调 ✓ |
| 圆孔内无丝 | 孔内点 **0/9939** | ✓ |
| 洞缘更密 | 洞缘 526.8 vs 远区 260.0（每 1000 面积）≈ **2.03×** | ✓ |
| 首帧只有壁、末帧满网 | u=0 亮度 2.7 → u=1 亮度 118.5 | ✓ |
| 30 s 动画无跳变 | u 0→0.17→0.33→0.50→0.67→0.83→1.00，回退帧 0，单帧最大增量 0.0006 | ✓ |

单格规模：`paths=298`、`pts=9143`、`walls=2`（200×200 单元、worms=6、coverage=0.6、strata=3）。

### 20.3 仍未做（P2 余项，不在原计划验收内）

- 跨格丝线连续性（相邻块接缝处的 1–2 px 过渡）。
- 块群「缺块轮廓」（成片缺块 + 圆弧切口 + 台阶式外轮廓），已与用户约定排在 P3 之后再动。
- 「两条蚕在同一格内交叉不打结」：本轮实现是每根丝独立回放实测笔迹，不存在随机追尾，
  故按规则不产生死结，但未做定量检测。

## §21 P3 母版与导出：场景 JSON、曲线、单元几何、native 逐帧渲染（2026-11-16，第 13 轮）

按 `PLAN_LED_WEAVE_2026-11-16.md` §5.2 与 `SPEC_WEAVE_ENGINE_2026-11-16.md` §10 P3 落地。

### 21.1 主程序新增（`docs/index.html`）

右侧蚕室左栏新增「母版导出」区块：

| 控件 | id | 作用 |
| --- | --- | --- |
| 屏体分辨率 | `habLedRes` | 2419×1360 / 2565×1282 / 2466×1333 |
| 帧数 / 帧率 | `habLedFrames` / `habLedFps` | 默认 900 / 30 |
| 导出母版场景 JSON | `habLedScene` | `led-scene.json`（母版渲染输入） |
| 导出曲线 JSON | `habLedCurves` | `weave-curves.json`：每单元实际丝线点列、`u0`、`length`、`band`、`alpha` |
| 导出单元几何 SVG | `habLedGeom` | `weave-cells.svg`：外框 / 圆孔 / 缺口 / SDF 壁 / 人工壁 |
| 导出单元几何 DXF | `habLedDxf` | `weave-cells.dxf`：LWPOLYLINE，Y 轴已翻正 |
| 复制母版渲染命令 | `habLedCmd` | 拼好 `render_led_frames.ps1 -Scene …` 命令 |

函数：`ledResolve` / `ledScene` / `ledBounds` / `ledCurves` / `ledGeometryPolys` / `ledSvg` / `ledDxf` /
`ledDownload` / `ledRenderCommand` / `bindLedPanel` / `ledRenderNative` / `ledB64Json` / `ledAgentFromUnit`。

**场景取景不再沿用预览缩放**：`ledScene` 按目标像素算 `scale = min(w*0.92/bw, h*0.92/bh)`、
`center` 取块群外框中点，四周留 8% 安全边（LED 柜体拼缝）。预览里缩到 30% 也不会影响母版构图。

### 21.2 native 单帧渲染模式

`docs/index.html?native=1&frame=N&total=M`（可选 `&scene=<base64url>`）：
清空 DOM 只留一块 `w×h` 画布、纯黑填充、按场景重建每个织网单元、
`u = (T - delay)/(1 - delay)`（`delay = order%7*0.045`，块与块错开起织），绘制一次即返回，
不启动 `rAF`、不跑动画、不画网格/雾/蚕体——只出丝与壁。

### 21.3 渲染脚本接入

`scripts/render_led_frames.ps1` 新增 `-Scene <led-scene.json>`：

- 把场景 JSON 注入页面副本（`<head>` 后插 `window.__LED_SCENE=…`），避免超长 URL；
- `-Native / -Frames / -Fps` 留空时自动取场景里的 `px` / `frames` / `fps`；
- 仍是逐帧 `--screenshot` + `-Resume` 断点续渲 + 缺帧拒编码 + `-Encode` 出 ProRes / H.264。

### 21.4 试片验收

| 项 | 结果 |
| --- | --- |
| 6 帧 960×540 出片 | 7.1 s；`frame_0000…0005.png` 体积 15 KB → 220 KB（丝逐步长满，符合生长动画） |
| ProRes / H.264 编码 | `weave_master_prores.mov` 781 KB、`weave_playback_h264.mp4` 115 KB，均成功 |
| 原生分辨率单帧 | 2419×1360（PNG 291 KB，1.8 s/帧含 Chrome 启动） |
| 同帧两次渲染 | SHA256 `8F6C122D…D3C4` 两次完全一致（确定性 ✓） |
| 导出结构探针（`probe_led_export.py`） | 8 个控件全在；scene `px=2419×1360 frames=900 fps=30 units=16 scale=3.143`；curves 179 条 / 6396 点 / totalLength 5994.57；svg 30,786 B（84 path）；dxf 39,517 B（84 polyline） |

按 1.8 s/帧估算，900 帧原生母版约 **27 分钟**（SPEC 原估 45–75 分钟，实测更快）；
900 帧 × 约 0.3 MB（暗场为主，PNG 压缩率高）≈ 0.3 GB，G 盘 106 GB 余量足够。

### 21.5 余项

- 900 帧全量原生母版尚未实跑（本轮只验证到 6 帧试片 + 单帧原生分辨率），需要一次挂机渲染。
- 10-bit / dither：ProRes 已用 `yuv422p10le`，播放版 H.264 未加噪点抖动（P4 现场调）。
- 块群「缺块轮廓」按约定排在 P4 之后再动。
