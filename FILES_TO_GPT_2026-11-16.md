# 交给 GPT 的文件清单（2026-11-16）

> 配套文档：`HANDOFF_FOR_GPT_2026-11-16.md`（先读它，再按本清单发包）。
> 原则：**只给"真源 + 说明 + 必要背景"**，不要给历史快照和素材库——那会让 GPT 分不清哪份是当前版本。

---

## A. 必给（4 个文件，约 280 KB）

| # | 绝对路径 | 作用 | 说明 |
| --- | --- | --- | --- |
| 1 | `H:\tool\silkworm-trajectory\docs\index.html` | **运行时唯一真源**：描图器 + 运动预览（iframe srcdoc）+ Digital Habitat 蚕室，全在这一个文件里 | 约 253 KB。不要给它 `editor/` 副本，三份内容一致，给多份会造成"改哪份"的困惑 |
| 2 | `H:\tool\silkworm-trajectory\HANDOFF_FOR_GPT_2026-11-16.md` | 本轮交接文档：定位、布局规范、数据流、状态机、修改守则、待办任务池 | 约 19 KB |
| 3 | `H:\tool\silkworm-trajectory\docs\使用介绍.md` | 面向用户的功能口径（按钮叫什么、做什么、Demo 模型边界） | 约 11 KB。GPT 改 UI 文案时以它为准 |
| 4 | `H:\tool\silkworm-trajectory\README.md` | 仓库入口、在线地址、素材位置 | 约 1.6 KB |

---

## B. 强烈建议一起给（背景与契约，约 30 KB）

| # | 绝对路径 | 作用 |
| --- | --- | --- |
| 5 | `H:\tool\silkworm-trajectory\PROJECT_BRIEF.md` | 问题背景 + **自动追踪方案为何被否决**（防止 GPT 又提"上算法自动提取"） |
| 6 | `H:\tool\silkworm-trajectory\docs\SCHEMA_MIGRATION.md` | `curves3d/v1→v2`、`motion-model/v1→v2` 的字段迁移与兼容规则 |
| 7 | `H:\tool\silkworm-trajectory\tests\geometry_tests.mjs` | 几何/参数化导出的既有测试（node 直接跑，改导出逻辑后必须过） |
| 8 | `H:\tool\silkworm-trajectory\HANDOFF_FOR_GPT.md` | 11-10 的旧总览，历史脉络与早期决策（**注意：其中蚕室位置等描述已过时，以新交接文档为准**） |

---

## C. 按需给（视 GPT 的本轮任务裁剪）

| 路径 | 什么时候给 |
| --- | --- |
| `H:\tool\silkworm-trajectory\viewer\motion-preview.html` | 只有当任务要**独立改造运动预览页**时才给（`docs/index.html` 里的预览是它的内嵌版，两处要同步改） |
| `H:\tool\silkworm-trajectory\examples\touchdesigner\README.md` | 任务涉及 TouchDesigner / p5.js 管线时 |
| `H:\tool\silkworm-trajectory\tools\generate_silk.py` | 任务涉及"合成丝线"生成时 |
| `H:\tool\silkworm-trajectory\tracking\track_silkworm.py`、`extract_silk.py`、`link_tracks.py` | **仅作失败对照**给：说明"自动追踪试过、结果被否决"。不要让 GPT 把它们接进主流程 |
| `H:\tool\silkworm-trajectory\CURSOR_IMPLEMENTATION_HANDOFF.md`、`GPT_LOOK_HANDOFF.md`、`GPT_STUDIO_CONDITIONS_HANDOFF.md`、`FILES_FOR_GPT.md`、`REPO_FOR_GPT.md` | 需要更细的早期实现细节 / 视觉规范时再给，属于叠加材料，不是必读 |

---

## D. 不要给（会拖慢或误导）

| 路径 | 原因 |
| --- | --- |
| `H:\tool\silkworm-trajectory\editor\silkworm-tracer.html`、`editor\蚕轨迹描图器.html` | 与 `docs/index.html` 字节一致的冗余副本，已同步；给多份只会让 GPT 改错文件 |
| `H:\tool\silkworm-trajectory\_backup\` 整个目录 | 历史快照 + 校验脚本，体积大；GPT 会把旧版本当参考 |
| `H:\tool\silkworm-trajectory\data\projects\`、`data\archive_videos\` | 2 GB+ 原始 4K 素材，且含自动追踪的废弃产物（`sample*_track.*`、`silk_timeline*.jpg`） |
| `H:\tool\silkworm-trajectory\docs\demo\silkworm_demo.mp4`（15 MB）、`手描视频.mp4`（137 MB） | 二进制素材与代码任务无关 |
| 根目录旧压缩包（`silkworm-gpt_*zip`、`silkworm-trajectory-src.zip`） | 都是 11-10 的过期快照，含旧布局版本 |

---

## E. 怎么发包（两种方式，任选）

**方式 1 · 直接上传**：把 A 组 4 个文件（+ B 组按需）拖进 GPT 对话。总大小 < 300 KB，一次可传完。

**方式 2 · 打一个 zip**（推荐，省得漏文件）：

```powershell
$dst = "H:\tool\silkworm-trajectory\silkworm-gpt_2026-11-16.zip"
$list = @(
  "H:\tool\silkworm-trajectory\docs\index.html",
  "H:\tool\silkworm-trajectory\HANDOFF_FOR_GPT_2026-11-16.md",
  "H:\tool\silkworm-trajectory\docs\使用介绍.md",
  "H:\tool\silkworm-trajectory\README.md",
  "H:\tool\silkworm-trajectory\PROJECT_BRIEF.md",
  "H:\tool\silkworm-trajectory\docs\SCHEMA_MIGRATION.md",
  "H:\tool\silkworm-trajectory\tests\geometry_tests.mjs"
)
Compress-Archive -LiteralPath $list -DestinationPath $dst -Force
```

打出来的包约 100 KB，命名里带日期，和根目录那几个 11-10 的旧包区分开。

---

## F. 给 GPT 的开场白（可直接粘贴）

> 这是一个单文件前端工具（`docs/index.html`，纯原生 JS、无构建、`file://` 可直接打开），服务于我的硕士论文《手绘曲线的三维化》第 X 章的工具章节。
> 请先读 `HANDOFF_FOR_GPT_2026-11-16.md`，重点看「页面结构 / 数据流 / 修改守则」三节，再读 `docs/使用介绍.md` 确认按钮口径。
> 本轮任务：<写清要改什么、验收标准是什么>。
> 硬约束：① 只改 `docs/index.html`；② 改动前把原文件备份到 `_backup/index-vN-日期.html`；③ 不改变导出 schema 的既有字段名，旧工程 JSON 仍要能打开；④ `srcdoc` 内脚本是 HTML 转义文本，校验前先反转义；⑤ 不要恢复"随机演示蚕作为默认个体"，也不要引入自动追踪；⑥ 输出改动点清单（函数名 + 行为变化 + 手工验收步骤）。
