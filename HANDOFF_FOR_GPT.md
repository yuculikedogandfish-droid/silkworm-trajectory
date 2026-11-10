# 蚕轨迹描图器 — GPT 优化交接文档

> **用途**：把本文件 + 仓库路径交给 GPT/其他模型，用于继续优化产品、算法与导出管线。  
> **主交付物**：单文件网页 `editor/蚕轨迹描图器.html`（纯前端，无构建）。  
> **读者**：接手优化的工程师/模型；不要求先读完整个 HTML，可按本文章节跳转。

---

## 1. 项目一句话

硕士论文实验工具：**顶视视频上手描蚕丝路径** → **mm 坐标 + 弧长参数 u∈[0,1]** → 导出 **Rhino / Blender / TouchDesigner** 可用曲线与 **运动统计/合成配方**，支撑「手绘曲线三维化」与后续 **虚拟蚕吐丝 / 生成艺术**。

更完整背景见 [`PROJECT_BRIEF.md`](PROJECT_BRIEF.md)。

---

## 2. 仓库结构（Windows 路径）

```
H:\tool\silkworm-trajectory\
├── PROJECT_BRIEF.md          # 原始需求与自动方案失败记录
├── HANDOFF_FOR_GPT.md        # 本文件
├── README.md
├── editor\
│   └── 蚕轨迹描图器.html     # ★ 唯一需要重点维护的前端
├── data\projects\
│   ├── 家蚕_15s/               # ★ 主素材：完整片按 15s 切段（段00–段05）
│   ├── archive_videos/         # 完整版 + 旧预览 + 微信备份（非默认）
│   └── …
└── tracking\                   # Python 实验脚本（自动追踪/差分，未融入 HTML）
    ├── track_silkworm.py
    ├── extract_silk.py
    └── link_tracks.py
```

**打开方式**：浏览器打开 `editor/蚕轨迹描图器.html`；推荐 **Chrome/Edge**。  
**家蚕视频快捷载入**：页顶「家蚕运动视频」→ `../data/projects/家蚕运动视频.mp4`（`file://` 下若失败则用手动「载入视频」）。

---

## 3. 用户已确认的领域事实（来自微信/实验）

| 项 | 值 |
|----|-----|
| 格子边长 | **1 cm**（标定时间距填 **10 mm**） |
| 头部运动形态 | 近似 **「八字」** |
| 单次八字包络 | 约 **1.5×1 格**，**不是**固定 2×2 或 1×1 |
| 个体差异 | 每次八字 **大小略有不同** → 需 **手动画框** 标本次包络 |

自动从消费级视频提取连续单根丝：**基本不可行**（见 PROJECT_BRIEF）；主流程是 **手动描线 + 参数化导出**。

---

## 4. 当前 HTML 已实现功能（截至交接）

### 4.1 视频与画布

- 本地载入 MP4；帧画到 **Canvas**（`drawImage`），避免 video 被盖层挡住。
- **视频分段**：默认 15s 一段，进度条按段 seek，段末自动暂停。
- 4K 素材会自动建议 **均匀点距**（约 `videoWidth/270` px）。

### 4.2 标定

- 原点 + 两点比例尺 → **px/mm**；格边默认 10 mm，按钮「1cm」。

### 4.3 描线（数位板/鼠标）

- **Pointer Events**；**不记录笔压**。
- 拖动时密采样；**抬笔后**：Chaikin 平滑 + **按弧长均匀重采样**（与描线快慢无关）。
- 侧栏：均匀点距、平滑强度、微抖过滤。
- 数据：`worms[id].points[]` + `strokes[]`（每笔在 points 中的 start/end）。

### 4.4 样式预览

- 每蚕：颜色、头/中/尾粗、透明度、材质 line / ribbon / tube。
- 画布线宽随分辨率放大（`canvasWidth/260`）；**每笔单独**头→中→尾渐变（非整条蚕一根参数）。
- 侧栏小预览条实时反映样式。

### 4.5 笔间连接与统一轨迹

- 全局 **笔间平滑连接**（B 键）；**三次 Bézier** 过渡（张力可调），非直线硬连。
- 统一轨迹：**u∈[0,1]** 弧长参数；点带 `kind: stroke | bridge`。
- 导出 **motion-model.json**：`features`（步长/转角/线宽统计）、`synthesis`（随机层公式草图 + TD 提示）、`behaviorUnits`（八字框）。

### 4.6 八字运动单元块

- **框选范围**（R 键拖拽）或 **1.5×1 格参考框**；绑定当前蚕 `behaviorBox`。
- 导出写入 `behaviorUnits` / `gridReference`。

### 4.7 导出格式

| 按钮 | 文件 | 说明 |
|------|------|------|
| SVG / JSON / CSV | 传统 + `curves3d` | JSON 含分段曲线 |
| 3D JSON | `curves-3d.json` | 可选 `unifiedTrajectories` |
| DXF / OBJ / glTF | CAD/DCC | 每笔或统一曲线 |
| Rhino.py / Blender.py | 脚本 | 生成曲线对象 |
| 运动模型 | `motion-model.json` | 统计 + 合成 + 八字框 |

### 4.8 快捷键（`onKey`，输入框内不触发）

- **Ctrl+Z** 撤点 · **Ctrl+Shift+Z / Ctrl+Y** 撤笔  
- **Space** 播放 · **←/→** , . 逐帧 · **[ / ]** 上/下段  
- **1–9** 蚕 · **O/L/R** 原点/比例尺/框选 · **B** 笔间连接  
- **Ctrl+S/O/E** 保存/打开/运动模型 · **Esc** 取消模式  
- 按钮 `data-tip` 悬停显示快捷键说明。

### 4.9 工程

- `saveProject()` → JSON（calibration, worms, bridge, segments, strokeOpts…）。

---

## 5. 核心数据结构（简化）

```javascript
state = {
  cal: { ox, oy, scale, p1 },
  worms: {
    [id]: {
      color, points: [{ x, y, t? }],
      strokes: [{ start, end }],
      style: { headWidth, midWidth, tailWidth, opacity, material },
      behaviorBox: { x0, y0, x1, y1 } | null,
      motionPattern: 'figure8',
      bridgeStrokes: null | false,
    }
  },
  bridge: { enabled, tension },
  segments: [{ start, end }],  // 视频时间分段
  videoFps, ...
}
```

**统一轨迹构建**：`buildWormTrajectory(w)` → `points[]`（含 `u, x_mm, y_mm, kind`）+ `segments[]`（笔/过渡在统一 u 上的区间）。

**关键函数名（便于 GPT 搜索）**：

- 交互：`onPointerDown/Move/Up`, `commitStroke`, `resampleUniform`
- 绘制：`draw`, `drawStyledPath`, `drawWormTrajectories`
- 导出：`collectExportCurves`, `exportCurves3D`, `exportMotionModel`, `buildSynthesisRecipe`

---

## 6. 用户长期目标（优化时请对齐）

1. **分析**真实蚕吐丝轨迹规律（分段 + 全段 u=0→1）。
2. **复现**大致规律 + **可控抖动**，批量生成 **不完全相同** 的虚拟丝轨迹。
3. **数学/参数可交付**：便于 TouchDesigner、p5、Rhino Grasshopper 二次创作。
4. 论文叙事：**自然主体绘制曲线** → 数字概念资产草模。

**尚未实现、用户期望的下一层**（优化优先级建议）：

- [ ] 读取 `motion-model.json` 的 **批量轨迹生成器**（Python 或 TD 示例）。
- [ ] **Redo** 栈（目前仅撤点/撤笔）。
- [ ] 导入旧 **自动追踪 JSON** 再手修（PROJECT_BRIEF 原缺口）。
- [ ] **点序播放器**：按「每秒 N 个点」预览，而非仅视频时间轴。
- [ ] 4K 性能：绘制/导出大数据时的卡顿。
- [ ] `file://` 与编码兼容性文档化或本地静态服务一键启动。
- [ ] 运动模型：从多条样本 **拟合** `synthesis.stochasticLayer` 的 μ/σ，而非手写占位。
- [ ] 可选 **z(t)** 或头高轨迹层（当前 z 多为 0）。

---

## 7. 已知问题与坑

1. **`sample*.preview.mp4`** 为 OpenCV **mp4v**，浏览器可能黑屏；主素材用 **H.264**（家蚕视频 / 微信原片）。
2. 单文件 **~2200+ 行**，无模块拆分，重构时可拆 `editor/js/*.js` 但需保持「双击 HTML 可用」或文档说明。
3. 未标定时 `x_mm` 实为像素占位；导出前应提示标定。
4. 蚕编号 **勿**再使用 `maxId+1` 自动多 tab（已修）；新蚕用「＋ 新蚕编号」。
5. `tracking/` 脚本路径含 `F:\xwechat_files\...`，换机器需改路径，与 HTML **未集成**。

---

## 8. 给 GPT 的优化任务建议（可任选）

### P0 — 体验与稳定

- 性能：4K 视频下 `draw()` 降频、脏矩形或仅重绘轨迹层。
- 快捷键与撤消：**Redo**、操作历史合并（撤笔 vs 撤点）。
- 悬停提示在顶栏拥挤时的布局（tooltip 被裁切）。

### P1 — 科研闭环

- `tools/generate_silk.py`：读 `motion-model.json` → 输出 N 条带噪声的 `curves-3d.json`。
- TouchDesigner：**IMPORT 范例**（CHOP u → Line SOP → Noise）。
- 点序播放 UI + 与 `u` 同步高亮。

### P1 — 数据

- 统一 schema 版本号 `curves3d/v2`、`silkworm-motion-model/v2` 的 migration 说明。
- SVG/DXF 导出 **可变宽度**（真实 ribbon 而非恒定 stroke-width）。

### P2 — 代码质量

- ESLint、函数分区、单元测试（`resampleUniform`, `buildWormTrajectory`, Bézier bridge）。
- 可选 Vite 构建，保留 `dist/蚕轨迹描图器.html` 单文件打包。

---

## 9. 验收清单（优化后自测）

- [ ] 载入 `家蚕运动视频.mp4`，画面正常，分段 seek 正常。
- [ ] 标定 1 cm 后，描一笔 → 均匀点距不随快慢变化。
- [ ] 两笔 + 开连接 → 过渡为曲线非折线；关连接 → 两笔分离。
- [ ] 框选八字 → `motion-model.json` 含 `behaviorUnits`。
- [ ] Ctrl+Z / Ctrl+Shift+Z、Ctrl+S、悬停 tip 正常。
- [ ] 3D JSON 含 `unifiedTrajectories` 且 `u` 单调 0→1。
- [ ] DXF 在 Rhino 中可 import，OBJ 在 Blender 中可 import。

---

## 10. 附带：运动合成公式（当前 JSON 中的逻辑草稿）

从实测轨迹统计：

- 步长 Δs ~ LogNormal(0, σ_step)，σ 来自 `features[].stepLength_mm.std/mean`
- 转角 Δθ ~ Normal(0, σ_θ)，来自 `turning_rad.std`
- 线宽 w(u) = `widthAlongStyle`(head, mid, tail) × (1 + Normal(0, σ_w))

批量生成：按 `strokeBlocks` / `behaviorUnits.envelope_grid` 缩放包络，块内带噪声采样控制点，块间用与编辑器相同 Bézier bridge + `bridge.tension`。

GPT 优化时可 **替换占位 σ** 为多样本 MLE/矩估计，并给出可执行代码。

---

## 10.1 发给 GPT 的压缩包（已生成）

| 文件 | 体积 | 内容 |
|------|------|------|
| `silkworm-gpt_512KB内_代码文档.zip` | ~120 KB | 交接文档 + 完整 HTML + tracking 脚本（**无视频**） |
| `silkworm-gpt_512MB内_两段15s.zip` | **~406 MB** | 同上 + **段00、段01** 各约 15s（4320² HEVC 原清晰度） |
| `silkworm-gpt_512MB内_含段05样片.zip` | ~30 MB | 旧版：仅余量段（可删用上面） |

路径：`H:\tool\silkworm-trajectory\`。GPT 阅读优先传 **512KB 包**；需要看视频再传 MB 包。

---

## 11. 交接给 GPT 的提示词模板（复制即用）

```text
请阅读 H:\tool\silkworm-trajectory\HANDOFF_FOR_GPT.md 与 PROJECT_BRIEF.md。
主文件：editor/蚕轨迹描图器.html（单文件前端，勿破坏本地/offline 使用）。

本次优化目标：（在这里写 P0/P1，例如：批量生成脚本 + TD 范例 + Redo）

约束：
- 默认保持单 HTML 可双击运行；若拆分构建需说明。
- 不记录数位板 pressure；均匀点距在抬笔后重采样。
- 导出需同时保留「分段 strokes」与「unified u∈[0,1]」。
- 格子标定 1cm；八字包络 behaviorUnits 需保留。

请先列出改动计划，再改代码，并更新 HANDOFF 的「已实现」与验收清单。
```

---

## 12. 联系上下文（与 curve-extractor 关系）

同仓库上级 `H:\tool\` 另有 `curve-extractor\`（金色光带等），**与蚕项目独立**。蚕论文素材以本目录为准。

---

*文档版本：交接日 2026-03；对应编辑器为对话迭代后的 `蚕轨迹描图器.html`。*
