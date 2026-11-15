# 交给 GPT / Cursor 的文件清单（2026-11-16）

给外部模型时按“必给 / 选给”两档传，避免上下文浪费。

## 必给（缺一不可）

| 文件 | 绝对路径 | 用途 |
| --- | --- | --- |
| 运行时主程序 | `H:\tool\silkworm-trajectory\docs\index.html` | 唯一真源（265,678 B）；三块脚本 + 蚕室 IIFE 都在这里 |
| 本轮规格存档 | `H:\tool\silkworm-trajectory\SPEC_HABITAT_MOTION_2026-11-16.md` | 需求原文 + 实施差异（`safeUnit`、留丝、step 20） |
| 本交接文档 | `H:\tool\silkworm-trajectory\HANDOFF_FOR_GPT_2026-11-16_HABITAT.md` | 改了什么、验收数据、限制、下一步约束 |

## 建议给（要改结构 / 要对比时）

| 文件 | 绝对路径 | 用途 |
| --- | --- | --- |
| 改动前基线 | `H:\tool\silkworm-trajectory\_backup\index-vNext-20261116-before-motion-canvas.html` | 253,657 B，做 diff 用 |
| 本轮快照 | `H:\tool\silkworm-trajectory\_backup\index-vNext-20261116-habitat-motion-infinite-canvas.html` | 与真源字节一致，防回滚 |
| 副本 1 | `H:\tool\silkworm-trajectory\editor\silkworm-tracer.html` | 必须与真源一致 |
| 副本 2 | `H:\tool\silkworm-trajectory\editor\蚕轨迹描图器.html` | 必须与真源一致 |
| 上一阶段交接 | `H:\tool\silkworm-trajectory\HANDOFF_FOR_GPT_2026-11-16.md`、`H:\tool\silkworm-trajectory\FILES_TO_GPT_2026-11-16.md` | 蚕室迁出 / 侧栏 / 拖拽反馈那轮 |
| 工程说明 | `H:\tool\silkworm-trajectory\README.md`（若存在） | 运行方式与目录约定 |

## 只在做织网 / LED 那条线时给

| 文件 | 绝对路径 |
| --- | --- |
| 织网原型 | `H:\tool\silkworm-trajectory\prototype\weave-lab.html` |
| 织网规格 | `H:\tool\silkworm-trajectory\SPEC_WEAVE_ENGINE_2026-11-16.md` |
| LED 方案 | `H:\tool\silkworm-trajectory\PLAN_LED_WEAVE_2026-11-16.md` |
| JSON Schema | `H:\tool\silkworm-trajectory\schemas\weave-profile.schema.json`、`H:\tool\silkworm-trajectory\schemas\weave-scene.schema.json` |
| 出片脚本 | `H:\tool\silkworm-trajectory\scripts\render_led_frames.ps1` |

## 不要给

- `H:\tool\silkworm-trajectory\_backup\_js\*`（拆分出来的临时脚本）
- `C:\Users\54364\AppData\Local\Temp\qa-hab.html`（探针副本，含注入脚本）
- 任何 `G:\led-render\frames` 下的中间帧

## 传参提示

- `index.html` 单文件 266 KB，超过部分模型单文件限制时，按 `<script>` 块拆成 3 份传（主描图器 / 蚕室 IIFE / srcdoc 预览），并注明“三块同属一个 HTML，不要合并职责”。
- 传文件时一并说明：改动必须同步两份 `editor` 副本并校验 SHA256。
