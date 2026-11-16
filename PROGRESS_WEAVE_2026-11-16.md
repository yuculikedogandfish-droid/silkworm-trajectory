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

## 8. 复现命令

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
