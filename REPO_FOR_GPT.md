# 给外部 GPT / 协作者：仓库入口

仓库（公开）：<https://github.com/yuculikedogandfish-droid/silkworm-trajectory>

## 建议阅读顺序

1. [HANDOFF_FOR_GPT.md](https://github.com/yuculikedogandfish-droid/silkworm-trajectory/blob/main/HANDOFF_FOR_GPT.md)
2. [PROJECT_BRIEF.md](https://github.com/yuculikedogandfish-droid/silkworm-trajectory/blob/main/PROJECT_BRIEF.md)
3. **文件清单（发给 GPT 用）**：[FILES_FOR_GPT.md](./FILES_FOR_GPT.md)

4. 主程序（请用 **英文路径**，避免 raw 404）：

- [docs/index.html](https://github.com/yuculikedogandfish-droid/silkworm-trajectory/blob/main/docs/index.html) · Raw：<https://raw.githubusercontent.com/yuculikedogandfish-droid/silkworm-trajectory/main/docs/index.html>
- [editor/silkworm-tracer.html](https://github.com/yuculikedogandfish-droid/silkworm-trajectory/blob/main/editor/silkworm-tracer.html) · Raw：<https://raw.githubusercontent.com/yuculikedogandfish-droid/silkworm-trajectory/main/editor/silkworm-tracer.html>
- 本地中文名：[editor/蚕轨迹描图器.html](https://github.com/yuculikedogandfish-droid/silkworm-trajectory/blob/main/editor/%E8%9A%95%E8%BD%A8%E8%BF%B9%E6%8F%8F%E5%9B%BE%E5%99%A8.html)

**在线**：<https://yuculikedogandfish-droid.github.io/silkworm-trajectory/>

## 视频

`.gitignore` 排除了本地 `*.mp4`。本机测试用 `data/projects/家蚕_15s/`；若需要带两段 15s 4K 的包，用项目根目录的 `silkworm-gpt_512MB内_两段15s.zip`（仅本地，未上传 GitHub）。

## 优化顺序（与 HANDOFF 一致）

结构 → 算法（点序/弧长重采样/桥接）→ 性能（4K 绘制）→ 导出 → 交互/快捷键
