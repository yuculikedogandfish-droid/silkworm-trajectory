# -*- coding: utf-8 -*-
"""重生成 WEAVE_MEASURED_PATHS：把 sample 的多笔按时间顺序接成**一条**连续丝路。

与旧版的区别（很重要的保真点）：
- 旧版每笔各自归一化 → 两笔被拉成同样大，比例失真；新版按**全局 bbox 统一缩放**，保留真实长宽比。
- 旧版保留 2 条独立折线，渲染时是"两段互不相干的碎笔"；新版接成一条（端点相距 0.62 mm，直接补上这段）。
- 翻转 y（丝路坐标系 y 向上、画布 y 向下），让朝向和用户看的 sample 一致。

用法：python _backup\gen_measured_paths.py "G:\raby model\trajectories.json" docs\index.html
"""

import json
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
RESAMPLE = 300
PAD = 0.06   # 归一化后四周留 6% 余量，避免满格贴边


def stroke_pts(c):
    pts = []
    for p in c.get("points", []):
        x = p.get("x_mm")
        y = p.get("y_mm")
        if x is None:
            x = p.get("x_px")
        if y is None:
            y = p.get("y_px")
        if x is None or y is None:
            continue
        pts.append((float(x), float(y)))
    return pts


def resample(pts, n):
    seg = [0.0]
    for i in range(1, len(pts)):
        seg.append(seg[-1] + ((pts[i][0] - pts[i - 1][0]) ** 2 + (pts[i][1] - pts[i - 1][1]) ** 2) ** 0.5)
    total = seg[-1] or 1.0
    out = []
    for k in range(n):
        t = total * k / (n - 1)
        i = 1
        while i < len(seg) - 1 and seg[i] < t:
            i += 1
        a = (t - seg[i - 1]) / (seg[i] - seg[i - 1] or 1.0)
        out.append((pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * a,
                    pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * a))
    return out


data = json.loads(SRC.read_text(encoding="utf-8"))
curves = data.get("curves3d") or data.get("curves") or []
routes = [stroke_pts(c) for c in curves]
routes = [r for r in routes if len(r) >= 3]
routes.sort(key=lambda r: 0)  # 保持原顺序：strokeIndex 0 → 1

# 接成一条：上一笔末尾与下一笔开头之间直接补一段直线（实测里这段是抬笔/hover 的缺失）
joined = []
for r in routes:
    if joined:
        joined.extend(r[1:])
    else:
        joined.extend(r)

# 全局等比缩放（保留长宽比）+ 居中 + y 翻转
xs = [p[0] for p in joined]
ys = [p[1] for p in joined]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
extent = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
k = (1.0 - 2 * PAD) / extent
norm = [((x - cx) * k, -(y - cy) * k) for x, y in joined]

norm = resample(norm, RESAMPLE)

flat = []
for x, y in norm:
    flat.append(f"{x:.4f}")
    flat.append(f"{y:.4f}")

lines = []
lines.append("  const WEAVE_MEASURED_PATHS = [")
lines.append("  [")
for i in range(0, len(flat), 16):
    chunk = ",".join(flat[i:i + 16])
    tail = "," if i + 16 < len(flat) else ""
    lines.append("    " + chunk + tail)
lines.append("  ],")
lines.append("  ];")

src_text = DST.read_text(encoding="utf-8")
start = src_text.index("  const WEAVE_MEASURED_PATHS = [")
end = src_text.index("\n  ];", start) + len("\n  ];")
DST.write_text(src_text[:start] + "\n".join(lines).rstrip() + src_text[end:], encoding="utf-8")

total_mm = sum(c.get("length_mm", 0) for c in curves)
print(f"strokes_in={len(routes)} joined_points={len(joined)} resampled={len(norm)} total_len_mm={total_mm:.2f} "
      f"aspect={(max(xs)-min(xs))/(max(ys)-min(ys)):.3f} bytes={DST.stat().st_size}")
