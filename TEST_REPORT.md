# 测试报告

## 自动化

| 项 | 命令 | 状态 |
|----|------|------|
| 几何：resample / chaikin | `node tests/geometry_tests.mjs` | **已通过**（本机执行） |
| generate_silk 可复现 | 需 `motion-model.json` + `python tools/generate_silk.py` | **未在本轮执行**（无标定样例 JSON） |

## 浏览器 / 手工

| 项 | 状态 |
|----|------|
| file:// 双击离线 | **未验证** |
| 4K 视频帧率 | **未验证** |
| 两段 15s 家蚕视频 | **未验证** |
| Rhino DXF 导入 | **未验证** |
| Blender OBJ/glTF 导入 | **未验证** |
| 数位板描线 | **未验证** |

## 已实施待你本机确认

- 未标定 → 3D/DXF/OBJ/glTF/CSV/运动模型弹窗拦截
- Ctrl+Y 重做
- 损坏工程 JSON 不替换当前状态
- glTF min/max 与 LINE 图元
- **并排吐丝预览** + `viewer/motion-preview.html` 单独打开
- 点序播放 / 追踪 JSON 导入 / SVG 丝带导出 / 轨迹层 Canvas

### 预览用法

1. 描图器点 **「并排吐丝预览」** → 右侧播放吐丝；可 **合成新轮** 看重复行为变异  
2. 或打开 `viewer/motion-preview.html`，载入 `motion-model.json`  
3. 勾选循环 + 叠加上一轮残影，观察多轮姿态

请在标定后导出 `motion-model.json`，运行：

```bash
python tools/generate_silk.py -i motion-model.json -o out.json -n 3 --seed 1
python tools/generate_silk.py -i motion-model.json -o out2.json -n 3 --seed 1
```

两次 `seed=1` 输出应一致；`seed=2` 应不同。
