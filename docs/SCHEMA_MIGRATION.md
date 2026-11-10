# 数据格式迁移 curves3d / motion-model

## v1 → v2 摘要

| 字段 | v1 | v2 |
|------|----|----|
| `schema` | `curves3d/v1` | `curves3d/v2` |
| `unit` | 常为 `mm`（未标定时实为像素） | `mm` 仅标定后；未标定导出 `px` + `coordinateNote` |
| `calibration` | 可选 | 标定后必填于 CAD 类导出 |
| `schemaLegacy` | — | 记录旧标识便于工具兼容 |

运动模型：`silkworm-motion-model/v1` → `silkworm-motion-model/v2`，`synthesis.stochasticLayer` 内字段标注 `source: fitted_* | default`。

## 读取兼容

- 旧工程 JSON（无 `projectVersion`）仍可打开；校验补全缺省字段。
- 3D / DXF / OBJ / glTF / CSV / 运动模型在未标定时被 UI 拦截。
- `exportJSON` / `SVG` 仍可在像素坐标下导出。
