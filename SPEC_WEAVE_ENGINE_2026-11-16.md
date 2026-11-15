# Digital Habitat 织网引擎 · 施工规格（LED 展陈版）

> 版本：2026-11-16 · 状态：可实施
> 配套：`prototype/weave-lab.html`（已跑通的原型）、`schemas/weave-*.schema.json`（数据契约）、`scripts/render_led_frames.ps1`（离线出片）。
> 读者：GPT（负责整合进主程序）、Cursor（负责仓库级重构与批量任务）、以及后续接手的人。

---

## 0. 四条确认对应的决策

| 你的确认 | 落到规格里的做法 |
| --- | --- |
| 长宽比不确定，要能人为设定 | 屏幕参数独立成组：面积 m²、比例（预设 16:9 / 2:1 / 1.85:1 / 4:3 / 1:1 / 9:16 / 自定义 W:H）、像素间距。三者决定原生分辨率，任何比例都不用改代码 |
| P1.5 像素间距 | 所有线宽、安全边、出片分辨率以「原生像素」为准反推毫米；7.4 m² @ P1.5 ≈ 3.29 MP（16:9 时 2419×1360） |
| 播片 + 网页实时预览 | **不做 4K 实时**：编辑预览按容器尺寸（≈1000–1920 px 宽）实时；母版走「无头 Chrome 逐帧 + ffmpeg」。这是最快的路线，见 §7 |
| 多蚕共织 / 一蚕一格都行 | 两种都支持，用「每格蚕数」+「目标覆盖率」两个参数切换；真实性由指纹约束，不靠参数硬凑，见 §4 |

---

## 1. 目标与判断标准

### 1.1 目标视觉（对照参考图）

参考图可分解为四个可参数化变量：

1. **格网轮廓**：矩形格 + 缺角（凹圆角）/ 圆洞，形成"被啃过的蚕簇"整体剪影。
2. **每格密度差异**：有的格接近实心网、有的只剩边缘一圈、有的几乎空。
3. **负空间**：圆洞里没有丝，洞缘丝最密（贴壁效应）。
4. **连续细丝 + 层叠**：放大看是连续线互相叠加，不是粒子点阵。

### 1.2 判断标准（可验收，不靠"感觉像"）

- **密度可控**：给定格，调整 `targetCoverage`，覆盖面积比例在 ±5% 内命中。
- **不重复**：同一 profile 换 seed，任意两格路径的 Hausdorff 距离 > 0.1×格宽；同一 seed 两次生成点列完全一致。
- **不空洞**：格内最大连续空白区直径 < 0.25×格宽（除非该格目标覆盖率 < 0.2）。
- **贴壁**：距壁 10% 格宽范围内的丝密度 ≥ 格内平均密度的 1.3 倍。
- **可追溯**：每条曲线都能追到 `profile → 实测工程 → 视频段 → 帧区间`。

---

## 2. 屏幕与比例（任意长宽比）

### 2.1 计算链

```
面积 A（mm²）= areaM2 × 1e6
比例 r = aspectW / aspectH
宽 W = √(A × r)        高 H = W / r
原生像素 pxW = round(W / pitchMM)    pxH = round(H / pitchMM)
```

7.4 m²、P1.5 的换算表：

| 比例 | 屏体（m） | 原生分辨率 | 总像素 |
| --- | --- | --- | --- |
| 16:9 | 3.63 × 2.04 | 2419 × 1360 | 3.29 MP |
| 2:1 | 3.85 × 1.92 | 2565 × 1282 | 3.29 MP |
| 1.85:1 | 3.70 × 2.00 | 2466 × 1333 | 3.29 MP |
| 4:3 | 3.14 × 2.36 | 2096 × 1572 | 3.29 MP |
| 1:1 | 2.72 × 2.72 | 1814 × 1814 | 3.29 MP |
| 9:16（竖） | 2.04 × 3.63 | 1360 × 2419 | 3.29 MP |

> 面积固定时总像素恒定，比例只改变形状。现场柜体拼缝会吃掉少量像素，以屏体实测 W×H 为准，规格里参数化即可。

### 2.2 出片侧硬约束

- 画布 = 原生像素，逐帧确定性重绘（`?native=1&frame=N&total=M&w=pxW&h=pxH&cfg=...`）。
- 母版：10-bit 4:2:2（ProRes 422 HQ）＋ H.264 播放版；暗场加 1–2% 抖动，避免色带。
- 线宽以像素为准：细丝 ≥ 2 px（P1.5 → 3 mm），最粗 ≤ 6 px；不要用 1 px 硬线（LED 上闪）。
- 四周留 2–3% 安全边。

---

## 3. 三层架构

```
A 运动语法层  profile（实测指纹）→ 采样器 → 每一步的转角/步长/停顿
B 约束层      cells（多边形+SDF）→ 占用场 occupancy → 候选方向打分
C 呈现层      2D 合成（strata）→ 生长进度 → 导出（SVG/JSON/PNG 序列）
```

三层的边界必须清晰：

- A 只输出"下一步怎么走"，不知道场地；
- B 只回答"这个方向能不能去、别处是否更空"，不决定节奏；
- C 只做绘制与导出，不改路径。

这样同一只蚕的 profile 可以丢进任意隔间；同一隔间换 profile 也不会跑出边界。

---

## 4. 运动指纹（真实性的防线）

### 4.1 必须由实测统计，不允许手填

`profile` 的每个字段都要有出处：

| 字段 | 来源 | 缺失时 |
| --- | --- | --- |
| `stepMean` / `stepSD` | 实测轨迹相邻点距的中位数 / P20 | 不得生成，要求先描线 |
| `turnHist`（36 桶） | 相邻段夹角绝对值直方图 | 同上 |
| `turnSignPersistence` | 连续同向转角游程均值 | 用 1.0 并在 `source.kind` 标 `assumption` |
| `maxTurn` | 转角 P95 | 同上 |
| `curveAmp` | 转角中位数映射 | 同上 |
| `wallAffinity` | 轨迹点到边界距离分布 | 标 `assumption` |

> 验收时检查 `source.kind`：`measured` 才允许进论文与展陈；`assumption` 只能出现在草稿，UI 上要显式标注。这条是防止"瞎编"的硬闸门。

### 4.2 采样器（原型已实现的版本）

```js
phase += phaseStep;                            // 0.02
desired = heading + curveAmp*cos(phase) + noise*gauss();
```

`curveAmp*cos(phase)` 产生左右交替的曲率振荡——这就是真实八字/绕圈节奏的低维表达；`noise` 是高频手抖，不是"随机装饰"。

对实测数据更严谨的做法（P1 升级）：直接从 `turnHist` 做马尔可夫采样，用 `turnSignPersistence` 控制左右交替长度，`curveAmp` 只做兜底。这一步做完，才算"运动模式"而不是"参数拟合"。

---

## 5. 约束层：隔间几何与占用场

### 5.1 SDF（已实现）

```
dRect  = max(|lx| - w/2, |ly| - h/2)
dNotch = -(dist(p, notchC) - notchR)
dIsle  = -(dist(p, isleC)  - isleR)
d      = max(dRect, dNotch, dIsle)      // 允许区域：d < 0
```

- 缺角圆与内岛圆都靠 `max(d, -circle)` 做布尔减，得到参考图里的凹圆角与圆洞。
- 壁轮廓用 marching squares 在 `d=0` 上取等值线，再链成折线 + Douglas-Peucker 简化 → 直接可导 SVG/DXF。

### 5.2 占用场（已实现）

- 网格分辨率 `res = max(1.4, min(w,h)/96)` mm。
- 每步用半径 `markR = 0.65 × stepLen` 打点，覆盖率 = 已标记允许格 / 允许格总数。
- 终止：`occN ≥ targetCoverage × allowCount`，或步数上限，或连续卡住 120 步。

### 5.3 候选方向打分（关键，别退回"简单转向"）

```js
desired += wallAff * (1 - (-d)/wallBand) * angDiff(wallTangent, desired);  // 贴壁
候选 = desired ± {0, .12, .26, .42, .58}
score = free*3.2 + wallBand质*wallAff*0.5 - |候选偏移|*0.9
```

- 只走 `score` 最高且不会撞壁的方向 → 不会原地打转；
- `free` 用占用场（离自己 2.4 步的前方是否已被填）→ 自动绕开旧丝；
- 贴壁权重只在距壁 6% 格宽内生效 → 不会变成"贴边描一圈"。

### 5.4 当前原型的实测数据（macOS/Chrome 环境不同会浮动）

- 10×6 格、3 层、每格 2 蚕 = 60 单元 / 120 条路径；
- 生成耗时 **约 2.3 s**（Chrome，i7 级 CPU）；
- 点 **266,947**、丝长 **4,352 m**、平均覆盖 **61.3%**；
- 预览 1010×568 px 流畅；原生 2419×1360 单帧绘制约 1–2 s。

这组数字说明：**编辑态实时没问题，母版必须离线**。

---

## 6. 多蚕共织 / 一蚕一格

| 模式 | 参数 | 效果 | 适用 |
| --- | --- | --- | --- |
| 多蚕共织 | `worms = 2–4`，`coverage 0.55–0.75` | 交叉网，最接近参考图 | 主视觉、密格 |
| 一蚕一格 | `worms = 1`，`coverage 0.25–0.45` | 单条丝绕圈，轮廓清晰 | 疏格、节奏对比、论文说明"一只蚕的贡献" |

两种可同屏混用：把 `worms`、`coverage` 做成**每格可覆写**（cell 级字段已预留），比全局滑杆更接近真实（真实蚕簇里每格桑叶量不同）。

---

## 7. 实时预览 vs 母版：三条路线与工时

| 路线 | 内容 | 工时（AI 辅助，1 人） | 结论 |
| --- | --- | --- | --- |
| **A. 现状增强（推荐）** | 保持 Canvas2D；预览按容器尺寸（≈1000–1920 宽）；母版走无头 Chrome 逐帧 + ffmpeg | **0.5–1 天**接进主程序并出 30 s 1080p 测试片；**+1 天**出 3.29 MP 母版与导出 | 最快、风险最低 |
| B. WebGL2 重写渲染 | 实例化线段 / SDF 后处理，3.29 MP 下 30–60 fps 实时 | **+5–8 天**（含分层 FBO、文字/HUD、跨显卡兼容） | 只有当"现场要实时生成"时才值 |
| C. 预渲染 + 播片 | 先把 900 帧渲好，页面只负责播放与调参 | 同 A | 与你"播片"的展陈方式一致，推荐 |

**给你的成本判断**：

- 只想先看效果、能拿去做评审 → **1 天**（A 的测试片部分）。
- 要交付 7.4 m² 母版 + 曲线/模型导出 → **2–3 天**（A 全量 + TD/Blender 脚本 + 现场调色）。
- 要现场实时 4K 生成 → **再 +5–8 天**，不建议（播片场景没有收益）。

母版机时估算：单帧生成 + 绘制约 3–5 s（3.29 MP），900 帧 ≈ **45–75 分钟**；ProRes 编码 5–10 分钟。可断点续渲（见 §10 待办）。

---

## 8. 导出契约（TD / Blender / 论文）

### 8.1 四类产物

| 产物 | 文件 | 内容 | 谁用 |
| --- | --- | --- | --- |
| 曲线包 | `weave-curves.json` | 每条路径 `cell/stratum/worm`、mm 点列、`u∈[0,1]`、`width_mm`、`coverage` | Blender/TD/论文定量 |
| 场景包 | `weave-scene.json` | 屏幕参数、格几何（含 notch/island）、覆盖率、seed、profile | 复现、CNC/激光切割、Rhino 建墙 |
| 矢量图 | `weave-curves.svg` | 壁轮廓 + 按层分组的丝（mm 单位） | Illustrator/Rhino 插图 |
| 位图/视频 | PNG 序列 → ProRes / H.264 | 母版与播放版 | LED 播控 |

### 8.2 Blender（可直接落地）

两条路，选一条即可：

1. **JSON → Python 建曲线**（推荐，保留 u 与宽度）：
   ```python
   # blender --background --python weave_to_blender.py
   import bpy, json, math
   data = json.load(open("weave-curves.json", encoding="utf-8"))
   for c in data["curves"]:
       cu = bpy.data.curves.new(c["id"], "CURVE"); cu.dimensions = "3D"
       sp = cu.splines.new("POLY"); sp.points.add(len(c["points"]) - 1)
       for i, p in enumerate(c["points"]):
           sp.points[i].co = (p["x"] / 1000, p["y"] / 1000, 0, 1)   # mm → m
       ob = bpy.data.objects.new(c["id"], cu)
       bpy.context.collection.objects.link(ob)
   ```
   墙：用 `weave-scene.json` 的 `cells` 生成 mesh（矩形 + 圆洞用 boolean，或直接吃 SVG 的折线）。

2. **SVG 直接导入**：Blender 自带 `io_curve_svg` 导入器读 `weave-curves.svg`；缺点是丢失 `u` 与逐点宽度，适合只看形态。

### 8.3 TouchDesigner

- `File In DAT` 读 `weave-curves.json` → `json.loads` → 按 `curves[]` 建点表；
- **Script SOP** 里逐条 `addPoint` + `addPolygon`，或 `Add SOP` + `DAT` 点表；
- `u` 送 `Pattern CHOP` 做沿丝扫描，`width_mm` 驱 `Sweep`/`Line` 宽度；
- 分层：按 `stratum` 分到不同 `Geo COMP`，用 `Over` 叠加并给每层独立 `Level`/`Blur`；
- 仿真扰动与实测务必分开标注（沿用现有 `examples/touchdesigner/README.md` 的口径）。

> 建议额外补一个 `tools/weave_to_td.py`（TD 内置 Python）与 `tools/weave_to_blender.py`，作为导出附件，Cursor 负责落地。

---

## 9. 分工与文件边界（避免并行改同一文件）

| 角色 | 负责 | 可写文件 |
| --- | --- | --- |
| 我（当前 Agent） | 原型与算法、数据契约、离线出片脚本、校验脚本 | `prototype/*`、`schemas/*`、`scripts/render_led_frames.ps1`、`_backup/check_*.py` |
| GPT | 把引擎整合进主程序：`docs/index.html` 的蚕室新增「隔间/织网」能力、UI 面板、保存载入、与现有 `agent` 数据兼容 | **只写** `docs/index.html`（改完同步 `editor/` 两份副本） |
| Cursor | 仓库级重构、性能优化、`tools/weave_to_td.py`、`tools/weave_to_blender.py`、批量渲染的断点续渲、Git 提交与备份、三副本一致性校验 | `tools/*`、`scripts/*`（除上面的渲染脚本需先 review）、`editor/*` |

**冲突规避**：同一时刻只允许一个人改 `docs/index.html`。GPT 提交后 Cursor 再动它；`prototype/` 与主程序解耦，可并行。

---

## 10. 分阶段任务（可直接派给 GPT / Cursor）

### P0 数据与指纹（0.5 天）

- 把 `schemas/weave-profile.schema.json` 落地成 `deriveProfile(points)`（主程序内）；
- 用 `data/projects/家蚕_15s/` 已描轨迹生成 3–5 个 profile JSON，人工核对；
- **验收**：`profile.source.kind = measured`，`loopsPerEnvelope` 与人工数得的环数误差 ≤ 1。

### P1 单格引擎进主程序（1 天）

- 把原型的 `cellSDF / prepareGrid / growInCell / simplify / contourPolylines / chainSegs` 移植到蚕室 IIFE（保持纯函数、无 DOM）；
- 新增 `kind:'weave'` 的个体/图层，避免污染现有 `kind:'route'`；
- **验收**：同一 seed 两次生成点列逐点一致；换 seed 形态明显不同。

### P2 多格 / 分层 / 生长动画（1–2 天）

- 格网布局 + 每格覆写（覆盖/蚕数/形状/开口）；
- `strata` 合成与生长进度；`duration` 控制；
- **验收**：60 格 3 层在 1000 px 预览下 ≥ 24 fps；30 s 动画无明显跳变。

### P3 母版与导出（1 天）

- `scripts/render_led_frames.ps1` 接 UI（复制命令 / 直接调用本地渲染入口）；
- 导出四类产物；Blender/TD 脚本；
- **验收**：2419×1360、900 帧、ProRes 母版可播；曲线在 Blender 里能重建；TD 点表能出 SOP。

### P4 现场（0.5 天）

- 亮度/对比调色、循环点、安全边检查；
- **验收**：1.5–3 m 观看距离下细丝不断、暗场无色带。

---

## 11. 验收清单（逐条点）

- [ ] 改面积 / 比例 / 像素间距，原生分辨率即时更新，丝与壁比例不变形。
- [ ] 同一 seed 刷新两次，画面完全一致。
- [ ] 换 seed，格内网形态明显不同，但疏密节奏仍属"同一只蚕"。
- [ ] 覆盖滑杆从 0.2 调到 0.7，格内密度单调变化，无突然"糊死"。
- [ ] 圆洞内没有丝，洞缘明显更密。
- [ ] 两条蚕在同一格内交叉，但不出现"打结死团"（连续 20 步在同一 3 mm 内）。
- [ ] 导出的 `weave-curves.json` 里 `u` 从 0 单调到 1，长度与 `length_mm` 一致。
- [ ] Blender 脚本导入后曲线位置与 SVG 预览一致（误差 < 1 mm）。
- [ ] 无头渲染 3 帧，首帧（进度 0）只有壁、无丝；末帧满网。

---

## 12. 风险与限制（必须在答辩/交付时说清）

1. **H 盘只剩 2.2 MB**（本次实测）：900 帧母版约 4–9 GB，**必须输出到 C/D 盘**；建议先把根目录 `silkworm-gpt_512MB内_两段15s.zip`（406 MB）与旧快照包移走。渲染脚本已内置空间预检，不足会直接报错。
2. **ffmpeg 未安装**：脚本会打印安装命令与备用手动命令；未装时只能拿到 PNG 序列。
3. **暗场色带**：8-bit H.264 播放版在 LED 上容易出色带；母版用 10-bit，播放版加轻微抖动。
4. **1 px 线闪烁**：细丝按 ≥2 px 出，靠亮度而不是靠细度表现"轻"。
5. **透明 3D 叠层**：不要做真 3D 半透明堆叠，会糊；用 §§6 的 strata 2D 合成，需要 3D 时导出带 z 的曲线。
6. **真实性**：`assumption` 指纹不得进论文与展陈；UI 必须显式标注"实测/假设"。
7. **计算耗时**：母版单帧 3–5 s，别指望浏览器边播边算 4K；这是播片方案的前提。

---

## 13. 论文口径（可直接改写）

- 本工具第三段能力的论点不是"模拟蚕"，而是**把一次自然主体的运动转译成可参数化的空间语法**：实测轨迹 → 运动指纹 → 在约束场地内重生成。
- 随机性有出处：每处变化由 `(profile, seed, coverage)` 三个可追溯参数决定，是**对个体差异的建模**，不是装饰性噪声。
- 分层不是特效，而是**蚕簇的空间分层**：一层 = 一批蚕的一次结茧尝试；十几层叠起来，是时间与空间的双重累积。
- 复现性是方法的一部分：同 seed 像素级一致，才让"作品"与"证据"同时成立。
