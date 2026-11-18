# -*- coding: utf-8 -*-
"""把 §17 追加到进度文档末尾（utf-8，无 BOM）。"""

from pathlib import Path

TEXT = """
## §17 织块线条改用实测丝迹回放（2026-11-16，第 9 轮）

用户指出「现在的线条应该不是实际上的蚕吐丝轨迹模式」，确认属实：上一轮的纤维是「沿格主方向的带 + 随机游走皱褶 + 正弦」合成的，实测折线只用来归纳振幅，不是真回放。

### 17.1 改动

- `WEAVE_MEASURED_PATHS` 用 `_backup\\gen_measured_paths.py` 从 `G:\\raby model\\trajectories.json` 重新生成：两笔完整点列（114 / 158 点），每笔弧长重采样到 140 点、逐笔等比归一化到 [-1,1]，共 280 点（此前是 56 点降采样）。
- `weaveThread` 主体改为「实测折线回放」：每条带取一笔实测折线，缩放到约 0.15–0.19 格宽、随机旋转 ±0.5 rad、随机散布到格内任意位置；`fit/cxx/cyy` 由每带的 rng 决定。线条形状完全来自实测点列。
- 密度与亮度：`bandCount = worms*8`（默认 48 条/格），单条丝 alpha 0.10–0.26（���交 0.25–0.60），叠加后是参考图那种灰阶网状而不是过曝白团；孔周环带照旧由 bi===0 画。
- 顺带修了一个真 bug：`weaveCellContent` 构造的 `cell` 之前漏了 `cell0.outline`，多边形轮廓单元实际按矩形 bbox 织；现已带上 `outline`，`weaveAllowed` 的 `weaveInPoly / weavePolyDist` 才真正生效。

### 17.2 验收

- `node --check` 三块脚本全绿。
- 块群截图 `qa-mosaic9.png`：16 块、每块细密曲线小圈（实测折线的缩略复制）、大圆孔负空间、块间硬黑缝、块亮度分层；不再是单向拉丝或水纹。
- 轮廓单元 `outline` 现在参与裁剪（矩形 bbox 内但多边形外的区域不落丝）。

### 17.3 关于样本

- 当前唯一实测样本就是 `G:\\raby model\\trajectories.json`（curves3d/v2，wormId 1，两笔 29.5mm / 40.9mm，标定 61.06 px/mm）。要换另一只蚕，把它的 trajectories.json 给我，跑一遍 `_backup\\gen_measured_paths.py` 即可替换模板，不用改代码。
- 仍属「假设」的部分：块的排布位置、孔洞位置、块亮度梯度是程序生成的（`source.kind='assumption'`），不进论文与展陈数据；只有丝迹形状来自实测。
"""


def main():
    p = Path(r"H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md")
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(TEXT)
    print(p.stat().st_size)


if __name__ == "__main__":
    main()
