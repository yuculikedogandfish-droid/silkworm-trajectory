# -*- coding: utf-8 -*-
import io
P = r"H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md"
S = """

## §37 r29 图片导出 + 蚕/丝逐只隐藏（2026-11-18）

### 37.1 图片导出（PNG，复用同一套分辨率）
- 左栏新增「网页端导出图片」：`导出当前画面 PNG`（`#habImgExport`）。
- 分辨率与视频**共用同一个下拉**（`habVidRes` + 自定义宽高），新增 `1280×960（4:3 快）`；默认改为 `2048×1536`。
- 实现：`ledExportImage()` → `ledScene()`（`loop=false`）→ 按 `habitat.simTime / (frames/fps)` 取当前时刻 → `ledComposeFrame()` 离屏合成 → `toBlob('image/png')` 下载；文件名 `weave_still_<W>x<H>_<秒>s.png`，状态栏报尺寸与 MB。
- 成品图沿用母版口径：只有织块，不含蚕体、编辑手柄、虚线框。

### 37.2 隐藏蚕 / 隐藏丝
| 层级 | 控件 | 行为 |
| --- | --- | --- |
| 全场 | 左栏「隐藏所有蚕体（只留丝）」`habHideAllBody` | `habitat.hideBodies`，所有 route/演示蚕不画身体，丝照常 |
| 全场 | 左栏「隐藏所有丝迹（只留蚕）」`habHideAllSilk` | `habitat.hideSilkAll`，所有丝不画；织块丝也收起，原地留一圈淡虚线框 |
| 单只 | 右栏个体卡片两个小按钮「蚕：显示中/已隐藏」「丝：显示中/已隐藏」 | `agent.hideBody` / `agent.hideSilk`，只影响这一只；织网单元只有「丝」一个按钮 |

实现要点：
- `paintWorld()`：weave 分支按 `habitat.hideSilkAll || agent.hideSilk` 决定画织块还是画虚线占位；route/演示分支分别判 `hideSilk`、`hideBodies || hideBody`。
- 个体卡片点击用 **capture 阶段 pointerdown** 先吃掉（`ev.stopPropagation()`），避免触发“选中 + 拖到场地”的原行为。
- `ledScene()` / `ledBounds()` 跳过被隐藏丝的块（全隐时回退到全部，避免空场景取景出错），所以导出的图片 / 母版 JSON 与画面一致。
- 隐藏只是视图状态，不改 `agents[].silk` 数据；`exportHabitat()` 里丝迹仍完整写出。

### 37.3 QA
- 三态截图（`qa-hide-normal/nobody/nosilk.png`）：normal 有蚕有丝；nobody 蚕没了、丝在；nosilk 丝没了、蚕在、块变成淡虚线框。右栏 chip 文案同步。
- 图片合成探针（`_backup/gen_img_qa.py`）：2048×1536 下 `lit=4.7% / avg=2.0`（12 s 时刻的局部织满，画面非空）；`ledExportImage()` 调用无异常（`export:ok`）。
- `node --check` 三个脚本块通过。

### 37.4 说明书同步
- 网页版 `docs/使用说明.html`：新增「导出单张图片」「五之二、只看丝、只看蚕」两节 + 导出区实拍图。
- PDF `docs/蚕轨迹描图器_使用说明.pdf`：同步两节，新增图 5（裁剪放大的左栏导出区）。
"""
with io.open(P, "a", encoding="utf-8") as f:
    f.write(S)
print("ok")
