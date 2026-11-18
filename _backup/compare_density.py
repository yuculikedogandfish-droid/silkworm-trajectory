# -*- coding: utf-8 -*-
"""亮度/密度对照：参考图 vs 当前单格渲染。

用法：python _backup\compare_density.py <参考图> <截图> x0 y0 x1 y1
"""

import sys
from PIL import Image

ref_path = sys.argv[1]
shot_path = sys.argv[2]
box = tuple(int(v) for v in sys.argv[3:7]) if len(sys.argv) > 6 else None


def stats(img, label, box=None):
    if box:
        img = img.crop(box)
    g = img.convert('L')
    px = list(g.getdata())
    n = len(px)
    mean = sum(px) / n
    lit = sum(1 for v in px if v > 90) / n
    dark = sum(1 for v in px if v < 12) / n
    print(f'{label}: size={img.size} mean={mean:.1f} lit>90={lit*100:.1f}% black<12={dark*100:.1f}%')


ref = Image.open(ref_path)
stats(ref, 'reference')
if box:
    stats(Image.open(shot_path), 'render crop', box)
else:
    stats(Image.open(shot_path), 'render')
