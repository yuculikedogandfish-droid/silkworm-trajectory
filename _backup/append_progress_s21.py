# -*- coding: utf-8 -*-
"""追加 §21：P3 母版与导出（场景 / 曲线 / 几何 / native 逐帧渲染）。"""

from pathlib import Path

TEXT = """
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
"""


def main():
    p = Path(r"H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md")
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(TEXT)
    print(p.stat().st_size)


if __name__ == "__main__":
    main()
