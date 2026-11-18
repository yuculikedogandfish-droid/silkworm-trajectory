# -*- coding: utf-8 -*-
"""追加 §19：蚕的活动范围可选（单格 / 跨格）。"""

from pathlib import Path

TEXT = """
## §19 蚕的活动范围可选：单格内 / 跨格（2026-11-16，第 11 轮）

用户要求「蚕是在一个单元格内活动还是在多个单元格内活动是可以选择的」。

### 19.1 改动

- 右侧「选中调整」面板新增下拉 `habAdjScope`：`整场 / 跨格`（默认）与 `单个单元格内`。
- 每个 route 蚕带 `scope`（`'field'` / `'cell'`）和 `homeUnitId`；导出/导入都带上这两个字段，换机子打开保持原选择。
- `roamPoint` 分两支：
  - `cell`：巡游中心绑到最近的织网单元（首次自动取最近的，之后记住 `homeUnitId`），半径 `min(w,h)*0.30`，蚕只在格内绕爬，丝落在格内。
  - `field`：沿用原来的整场巡游（半径 0.20–0.82 场、角速 2.05、每蚕相位 `wormId*1.7`）。
- 切到「单格内」但场地还没有织网单元时会提示「先放一个/铺一块群」，此时暂时仍按整场跑，放下单元后自动收进格内。

### 19.2 验证（`_backup\\probe_scope.py`，无头 Chrome）

- `scope select=yes`；场地 16 个织网单元。
- `cell` 模式：240 步内 `max |dx|/halfW = 0.60`（≤1，说明始终在单格内）。
- `field` 模式：`max |x| = 134`、`max |y| = 127`（跨整场，远超单格 77/2）。
- `node --check` 三块脚本全绿。

### 19.3 说明与边界

- 这里的「单格/跨格」控制的是**蚕本体（可见爬行 + 自己吐的丝路）**的活动范围；织块的填充进度仍按 `u` 推进（每块从 0 织到 1），两者目前是解耦的。
- 如果要做「蚕在某格吐丝 → 该格随之长满」的真联动，需要把块的 `u` 由格内丝长驱动（P2 余项，下一步候选）。
"""


def main():
    p = Path(r"H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md")
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(TEXT)
    print(p.stat().st_size)


if __name__ == "__main__":
    main()
