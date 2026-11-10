# 优化变更日志（Cursor 实施）

## 2026-03-26

### P0 — 结构 / 数据 / 编辑

- 新增 `CURSOR_IMPLEMENTATION_HANDOFF.md` 执行清单
- `validateProjectData` / `validateWorm`；加载失败不覆盖内存
- 工程 `projectVersion: 2`；保存前校验
- `isCalibrated()` / `requireCalibration()`；未标定拦截 mm 类导出
- `toMM()` 未标定返回 `unit: 'px'`，`x_mm/y_mm: null`
- Undo/Redo：`pushUndoSnapshot` + `Ctrl+Y` → `redoEdit()`；界面「重做」
- `resampleUniform`：去重、二分 `pointAtDistance`、单调游标

### P0 — 算法 / 导出

- `buildWormTrajectory`：点→段 O(1) 索引；`u_within_stroke` 按笔画弧长
- `exportMetaBlock` → `curves3d/v2`；运动模型 `silkworm-motion-model/v2`
- `buildSynthesisRecipe`：标注 fitted vs default
- `exportGLTF`：accessor min/max 来自实际缓冲；`mode: 1` LINES

### P1 — 性能

- `scheduleDraw` + `requestAnimationFrame` 合并指针移动重绘
- `getCachedWormTrajectory` 缓存（几何/桥接变化时失效）

### 交付物

- `tools/generate_silk.py`
- `tests/geometry_tests.mjs`
- `docs/SCHEMA_MIGRATION.md`
- `examples/touchdesigner/README.md`

### 2026-03-26（续）预览与收尾

- **`viewer/motion-preview.html`**：蚕体 + 吐丝丝带动画；循环；合成新轮（受控噪声）
- 描图器 **「并排吐丝预览」**：右侧 iframe，实时推送轨迹
- 侧栏 **点序播放**（与视频时间无关）
- **导入追踪 JSON**（像素 `t/x/y`）
- **SVG 可变宽度丝带**（`expSvgRibbon`）
- **双 Canvas**：`#canvas` 视频/网格；`#canvasTraj` 轨迹叠加层

### 仍未实机验收（见 TEST_REPORT.md）

- Rhino/Blender/4K 导入与帧率
- DXF 可变宽度深化
