# -*- coding: utf-8 -*-
import io
P = r"H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md"
S = """

## §35 r27 工程保存/自动恢复 + 网页导出视频升级 + 图文使用说明（2026-11-18）

### 35.1 中途保存：原来是「只能手动存文件」，现在两层
| 层 | 行为 | 实现 |
| --- | --- | --- |
| 自动保存 | 每 3 秒把 `exportHabitat()` 写进 `localStorage['silkworm-habitat-autosave/v1']`；`beforeunload`、`visibilitychange`（切走/最小化）再补存一次 | `autoSaveNow()` / `autoTimer` |
| 打开即恢复 | 启动 500 ms 后读快照，7 天内有效，`importHabitat(doc)` 还原；toast 写明「已恢复上次编辑的场地（月日 时:分）」 | `setTimeout(restore)` |
| 存成文件 | 「保存工程（.json）」= `exportHabitat()` 全量（几格、每格用哪只蚕、`custom.shapes`、`outline`、seed、丝迹、底层只读轨迹） | 原 `habSave` 逻辑保留 |
| 载入文件 | 新增「载入工程（.json）」+ 隐藏 `#habSceneFile`；校验 `type` 必须是 `silkworm-habitat/*`，不是就明确提示「这是 xx 文件，不是场地工程」 | `#habLoad` / `#habSceneFile` change |

实测（`_backup/probe_r27_autosave.py`，同一 Chrome 用户目录跑两次）：
- 第一次：放 1 格、设 `x=120, y=-40, seed=909` → 3.8 s 后 `habAutoStat` = 「自动保存：16:46:07 已存」，`localStorage` 有键。
- 第二次（全新页面）：读到 `units=1, pos=[120,-40,909]` → 位置与种子完整恢复。

### 35.2 网页端导出视频：从「固定 14 Mbps、最长 30 s、只进内存」升级
- 分辨率：854×480 / 1280×720 / 1920×1080 / **2419×1360（母版）** / **2560×1440**
- 时长：5 / 10 / 20 / 30 / **60 / 120 秒**
- 帧率：24 / 30 / **60**
- 画质（码率）：8 / 16 / 28 / **40 Mbps**（直接传给 MediaRecorder，VP9 优先，失败退 VP8）
- **长片边录边写盘**：`secs > 30` 且有 `showSaveFilePicker` 时，先让用户选保存位置，`createWritable()` 后 `ondataavailable` 里按队列逐块写盘（`writeChain`），不再把整段压在内存 —— 120 s 也不会中途失败
- **掉帧自检**：`composedFrames` 统计实际绘制帧，导出后状态栏写「实际绘制 N/M 帧」；有掉落就直接给出「降分辨率或改 30 fps」的处置建议

### 35.3 图文使用说明
新增 `docs/使用说明.html`（单文件、截图 base64 内联、随 Pages 一起发布）：
- 三区总览（左/中/右）＋主界面实拍
- 五步上手（放块 → 选蚕 → 开始 → 拖时间轴 → 存工程）
- 形状编辑手柄对照表（四角 / 边中点 / 十字 / 青点 / 白点 / 边中点拉新角）＋编辑态实拍
- 保存与恢复（自动保存 vs 文件保存，两种场景怎么选）
- 视频导出四下拉对照表 + 「为什么更长更清晰」的四条保证
- 名词表（壁 / 丝路 / 孔 / 缺口 / 缝 / 覆盖率 / 一份吐丝 = 7.042 格宽 / 一格 ≈ 25 份）
- FAQ（蚕为何只在格内、滑条为何没反应、视频糊、关网页会不会丢）

### 35.4 验收
- `node --check` outer_0 / outer_1 通过。
- 自动保存/恢复：见 35.1 实测数字。
- 视频录制：无头环境无法点系统保存对话框，`virtual-time` 下 MediaRecorder 会挂住；**这一段需要在真实 Chrome 里点一次验收**（代码路径按 MediaRecorder 标准写，语法已校验）。已如实标注，不算通过。
- 遗留：`localStorage` 约 5 MB 上限，超了会提示改用手动存文件。
"""
with io.open(P, "a", encoding="utf-8") as f:
    f.write(S)
print("ok")
