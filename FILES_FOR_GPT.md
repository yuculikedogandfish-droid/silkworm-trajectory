# 源码清单与「依次发给 GPT」指南

**仓库根目录（本机）**：`H:\tool\silkworm-trajectory\`  
**公开仓库**：https://github.com/yuculikedogandfish-droid/silkworm-trajectory  
**约束不变**：单文件 HTML 可离线双击运行；优化顺序 **结构 → 算法 → 性能 → 导出 → 交互**。

---

## 一、若直链失败，请优先用这两条（纯英文路径）

| 用途 | 链接 |
|------|------|
| **主程序（与 `editor/蚕轨迹描图器.html` 同源）** | https://raw.githubusercontent.com/yuculikedogandfish-droid/silkworm-trajectory/main/docs/index.html |
| **同上（镜像副本）** | https://raw.githubusercontent.com/yuculikedogandfish-droid/silkworm-trajectory/main/editor/silkworm-tracer.html |
| **jsDelivr 镜像（部分环境更稳）** | https://cdn.jsdelivr.net/gh/yuculikedogandfish-droid/silkworm-trajectory@main/docs/index.html |

GitHub **网页查看（可整页复制）**：  
https://github.com/yuculikedogandfish-droid/silkworm-trajectory/blob/main/docs/index.html  

中文文件名版（部分工具会 404，仅作备用）：  
https://github.com/yuculikedogandfish-droid/silkworm-trajectory/blob/main/editor/%E8%9A%95%E8%BD%A8%E8%BF%B9%E6%8F%8F%E5%9B%BE%E5%99%A8.html  

**在线可运行（不代替读源码）**：https://yuculikedogandfish-droid.github.io/silkworm-trajectory/

---

## 二、仓库内完整文件树（Git 已跟踪，无视频）

```
silkworm-trajectory/
├── README.md
├── PROJECT_BRIEF.md
├── HANDOFF_FOR_GPT.md          ← 交接总览（对方已读过）
├── REPO_FOR_GPT.md             ← 链接汇总
├── FILES_FOR_GPT.md            ← 本文件
├── .gitignore
├── docs/
│   └── index.html              ← 主程序（Pages 部署用，≈84KB）
├── editor/
│   ├── 蚕轨迹描图器.html       ← 主程序（本地双击用，与 docs 同源）
│   └── silkworm-tracer.html    ← 主程序 ASCII 副本
├── tracking/                   ← Python 自动追踪实验（未接入 HTML）
│   ├── track_silkworm.py
│   ├── link_tracks.py
│   └── extract_silk.py
├── scripts/
│   └── push-via-api.ps1        ← 维护者推送脚本（可忽略）
└── data/
    ├── projects/               ← 样例工程/追踪结果（JSON/CSV/JPG/SVG）
    │   ├── sample1_track.json
    │   ├── sample1_track.csv
    │   ├── sample1_linked.json
    │   ├── sample1_overview.jpg
    │   ├── sample2_track.json
    │   ├── sample2_track.csv
    │   ├── silk_trajectory.svg
    │   └── silk_timeline_final.jpg
    └── samples/                ← OpenCV 实验图 + 小脚本
        ├── frame_0_0.jpg … frame_5_99.jpg
        ├── preview_0.jpg … preview_4.jpg
        ├── detect_*.jpg, threshold_*.jpg
        ├── silk_*.jpg
        └── _peek.py, _silk_test.py, …
```

**不在 Git 内（仅本机，需你另行传 zip）**

```
data/projects/家蚕_15s/          ← 6 段 15s 4K mp4
data/archive_videos/               ← 完整版 / 旧预览
silkworm-gpt_512KB内_代码文档.zip
silkworm-gpt_512MB内_两段15s.zip
silkworm-trajectory-src.zip
```

---

## 三、建议发给对方的顺序（聊天里一条条贴）

### 第 0 步：说明（复制一段话即可）

「主程序约 **84KB、2200 行单文件**，请用 **docs/index.html** 或 **editor/silkworm-tracer.html** 的 raw 链接拉全文；不要用中文路径 raw。优化按 HANDOFF 第五节，第一批见下文第六节。」

### 第 1 步：文档（小文件，整文件粘贴）

| 顺序 | 文件 | Raw |
|------|------|-----|
| 1 | HANDOFF_FOR_GPT.md | https://raw.githubusercontent.com/yuculikedogandfish-droid/silkworm-trajectory/main/HANDOFF_FOR_GPT.md |
| 2 | PROJECT_BRIEF.md | https://raw.githubusercontent.com/yuculikedogandfish-droid/silkworm-trajectory/main/PROJECT_BRIEF.md |
| 3 | FILES_FOR_GPT.md | https://raw.githubusercontent.com/yuculikedogandfish-droid/silkworm-trajectory/main/FILES_FOR_GPT.md |

### 第 2 步：主程序 HTML

**优先**：让对方用工具拉 **一条 URL 的全文**（`docs/index.html`）。  
若仍失败，按 **第四节分片** 把同一份源码分 6 段粘贴（每段标注起止行号）。

### 第 3 步（可选）：`tracking/*.py`

仅在做「导入自动追踪 JSON」时需要；每文件 4–7KB。

### 第 4 步（可选）：`data/projects/sample1_track.json` 等

用于理解旧自动追踪数据格式，单文件可达数百 KB，可只发 JSON 头部 + schema 说明。

---

## 四、主 HTML 分片地图（手工粘贴用）

与 `docs/index.html` / `editor/蚕轨迹描图器.html` **内容相同**，约 **2310 行**（以仓库最新为准）。

| 片 | 大约行号 | 区块标记 / 内容 |
|----|----------|-----------------|
| A | 1–425 | `<!DOCTYPE>` … CSS |
| B | 426–532 | `// 状态`、`// 初始化` |
| C | 533–704 | `// 视频` |
| D | 705–1165 | `// 交互`（含 **`commitStroke`** ~993、**`resampleUniform`** ~977） |
| E | 1166–1890 | `// 样式`、`buildWormTrajectory` ~1302、`// 绘制` |
| F | 1891–末尾 | `// 导出`（SVG/JSON/3D/DXF/OBJ/glTF/motion-model 等） |
| G | 2268–末尾 | `// 工程保存/打开`、快捷键 |

**第一批优化应对照的函数（均在片 D–F）**

- `resampleUniform` — 弧长均匀重采样  
- `commitStroke` — 提交一笔 + Chaikin + 重采样  
- `buildWormTrajectory` — 统一 u、segments、mm 映射  
- `exportMetaBlock` / `exportCurves3D` / `exportMotionModel` / 等 — 导出与单位  

---

## 五、对方已确认的 P0 修改项（来自 HANDOFF，非臆测）

1. **结构**：理清 `commitStroke`、`resampleUniform`、`buildWormTrajectory` 与各 `export*` 职责；保持单 HTML 离线。  
2. **数据**：**未完成 mm 标定**时，导出不得把像素标成真实毫米（HANDOFF §7.3）。  
3. **编辑**：**Redo** 真历史栈，撤点/撤笔不破坏 `points` 与 `strokes` 索引（HANDOFF §6、§8 P0）。  
4. **性能**：视频帧刷新与轨迹层重绘分离，减轻 4K 卡顿（HANDOFF §8 P0）。  
5. **导出**：格式带 **schema/version**；保留逐笔 `strokes` + 统一 **u∈[0,1]**（HANDOFF §5、§8 P1）。

---

## 六、本机 zip 仍可作为备选

路径：`H:\tool\silkworm-trajectory\silkworm-gpt_512KB内_代码文档.zip`（仅代码文档，约 120KB）  
或：`silkworm-trajectory-src.zip`（Git 全量无 mp4，约 7.4MB）

---

## 七、给对方的一段「固定开场白」（可直接复制）

```
我已把项目放在公开仓 silkworm-trajectory。请只读英文路径源码：
raw main/docs/index.html 或 main/editor/silkworm-tracer.html。
交接见 HANDOFF_FOR_GPT.md。第一轮按：结构→算法→性能→导出→交互；
具体 P0：标定前导出单位、Redo 栈、绘制分层、导出版本号。
不要重写简化版，在现有单文件上改。
```
