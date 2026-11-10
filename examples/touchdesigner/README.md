# TouchDesigner：导入蚕轨迹数据

## 文件

- **实测**：描图器导出的 `curves-3d.json`（`curves3d/v2`，单位 mm，需已标定）
- **生成**：`tools/generate_silk.py` 输出的 `curves-generated.json`（标注 `provenance: synthetic`）

## 推荐流程

1. **DAT 读取 JSON**  
   使用 `Text DAT` + 执行 `json = json.loads(...)`，或 File In DAT 指向导出文件。

2. **点表 → CHOP**  
   从 `unifiedTrajectories[n].points` 读取 `u`, `x_mm`, `y_mm`, `z_mm`。  
   建 `Pattern CHOP` / 脚本 CHOP：`u` 作相位，`length_mm * u` 可作沿丝距离近似。

3. **曲线几何**  
   - 将点列送入 **Add SOP**（polygon）或 **Line SOP**。  
   - 毫米 → TD 场景单位：除以 1000 得米，或自定义 scale 与实验台 1cm 格一致。

4. **Noise**  
   读 `motion-model.json` → `synthesis.stochasticLayer` 的 `sigma`，在 Point SOP / Noise SOP 上叠加位置扰动。**生成轨迹与实测勿混标。**

5. **宽度**  
   `width_mm` + `widthAlongStyle(u)` 可驱动 **Sweep** 或线宽 CHOP。

## 注意

- 无标定数据只有 `x_px/y_px`，不可直接当毫米进 TD 物理模拟。
- 桥接段 `kind: bridge` 在 `segments` 中单独标注。
