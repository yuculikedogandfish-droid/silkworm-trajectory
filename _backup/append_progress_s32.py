# -*- coding: utf-8 -*-
import io
P = r"H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md"
S = """

## §32 r24 导入数据实测复核：丝迹 0 越界 + 两处崩溃修复（2026-11-17）

### 32.1 复核方法
`_backup/probe_r23_i6.py`：三格 260×260 排在 x=-340/0/+340，导入真实 `trajectories.json`（curves3d 2 笔 wormId=1），三格分别用「全部蚕 / 全部蚕 / 只放蚕1」，`seek(5)` 后逐点判定越界（内缩 0.98）。

### 32.2 结果（实测，非估计）
| 对象 | 丝迹点数 | 越界点 | 最大越界 |
| --- | --- | --- | --- |
| 源蚕 rt-1 | 100 | 0 | 0 |
| rt-1@wv-1 | 99 | 0 | 0 |
| rt-1@wv-2 | 100 | 0 | 0 |
| rt-1@wv-3 | 99 | 0 | 0 |

织块（`weaveCellContent` 生成阶段，修复前 → 修复后）：

| 单元 | 修复前越界点 | 修复前最大越界 | 修复后越界点 |
| --- | --- | --- | --- |
| wv-1 | 925 / 8731 | 149.8 | 0 / 9299 |
| wv-2 | 946 / 10833 | 143.85 | 0 / 6408 |
| wv-3 | 847 / 9246 | 152.04 | 0 / 9296 |

结论：越界真正来源是**织块本身**（跨块压边丝带伸出格约 1.1 个格宽），route 丝迹早已收在格内。修法 = 在 `weaveCellContent` 生成完 `paths` 后逐点夹到 `cell.w/h - 1.2`（不是只靠绘制时 `ctx.clip()`），这样预览、离屏位图、导出三处共用同一份已收口的几何。

### 32.3 顺带修掉的两个崩溃
1. `assignWormToUnit(unitId, 'worm-1')` 这类非纯数字值 → `Number()` 得 NaN → `spawnCellWorm` 找不到源蚕 → 克隆 route 为空 → `applyRouteTransform` 读 `pts[0].x` 抛错，界面表现是「选哪只蚕都没反应」。现改为 `String(val).replace(/[^0-9.-]/g,'')` 再 `Number()`，非法值走「解除绑定」分支。
2. `applyRouteTransform` 增加空轨迹保护：没有轨迹的蚕停在落点，不再抛异常（新建格、刚同步、导入失败等场景都会命中）。

### 32.4 观感对照
`qa-r24-import.png`：中间格已呈参考图的「整块密织 + 一个大圆孔」，孔缘由撞壁收口形成；左右格为同一种蚕在不同格里的独立实例，起点/朝向不同。
遗留：`seek(16)` 在无头 Chrome 里会卡住（`virtual-time-budget` 与满织位图同帧），改用 `seek(8)` 出图；此问题只影响无头截图脚本，不影响真实浏览器。
"""
with io.open(P, "a", encoding="utf-8") as f:
    f.write(S)
print("ok")
