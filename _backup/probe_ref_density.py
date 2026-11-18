# -*- coding: utf-8 -*-
"""对参考图做粗略密度统计：整体覆盖率 + 8x10 分块覆盖率 + 亮点占比"""
import numpy as np
from PIL import Image

p = r"C:\Users\54364\AppData\Roaming\DingTalk\2163372687_v2\resource_cache\9b\9bad4cc30ce1c4907b21d3bce4382b2e.png"
im = Image.open(p).convert("L")
w, h = im.size
a = np.asarray(im, dtype=np.float32) / 255.0
print("size", w, h)

# 阈值：参考图是黑底白丝，取 0.22 作为"有丝"的门限
th = 0.22
mask = a > th
print("整体覆盖率 %.3f" % mask.mean())

# 分块：8 列 10 行
cols, rows = 8, 10
cw, ch = w // cols, h // rows
blocks = []
for r in range(rows):
    line = []
    for c in range(cols):
        blk = mask[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
        line.append(blk.mean())
    blocks.append(line)
arr = np.array(blocks)
print("分块覆盖率 min/median/max: %.3f / %.3f / %.3f" % (arr.min(), np.median(arr), arr.max()))
print("块覆盖率分布（行优先，保留两位）:")
for r in range(rows):
    print(" ".join("%.2f" % arr[r, c] for c in range(cols)))

# 高亮占比（丝的重叠处更亮）
hi = a > 0.55
print("高亮(>0.55)占画面 %.3f" % hi.mean())
