# silkworm-trajectory（蚕吐丝轨迹）

顶视视频上手描丝线 → 导出 Rhino / Blender / TouchDesigner 曲线与 **motion-model.json**。

## 在线使用（可分享）

**[蚕轨迹描图器 — GitHub Pages](https://yuculikedogandfish-droid.github.io/silkworm-trajectory/)**  
**[吐丝运动预览](https://yuculikedogandfish-droid.github.io/silkworm-trajectory/viewer/motion-preview.html)**（可并排打开描图器内「并排吐丝预览」）

- 视频在浏览器本地解码，**不会上传到服务器**；也可点「载入视频」用自己的 MP4。
- 点「家蚕·段00」可加载站内约 15MB 演示样片；4K 分段素材仍用本地 `data/projects/家蚕_15s/`。

## 给协作者 / GPT：从哪里读

1. **[HANDOFF_FOR_GPT.md](./HANDOFF_FOR_GPT.md)** — 交接总览（必读）
2. **[PROJECT_BRIEF.md](./PROJECT_BRIEF.md)** — 问题背景与自动方案结论
3. **主程序（单文件）**：[`editor/蚕轨迹描图器.html`](./editor/蚕轨迹描图器.html)  
   - 浏览器打开即可用；或通过 GitHub 上的 **Raw** 链接下载该文件。
4. **`tracking/`** — Python 实验脚本（自动追踪，未并入 HTML）

## 视频素材（不在本仓库内）

体积约 2GB+，已 `.gitignore`。本地路径：

- `data/projects/家蚕_15s/` — 每段 15s 4K  
- `data/archive_videos/` — 完整版与旧预览  

发给 GPT 的 zip：`silkworm-gpt_512KB内_代码文档.zip` / `silkworm-gpt_512MB内_两段15s.zip`（本地 `H:\tool\silkworm-trajectory\`）。

## 优化顺序（建议）

结构 → 算法 → 性能 → 导出 → 交互
