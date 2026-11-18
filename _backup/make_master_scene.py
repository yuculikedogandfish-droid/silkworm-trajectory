# -*- coding: utf-8 -*-
"""母版场景（silkworm-led-scene/v1）：7×6 规整块群，2419×1360，贴参考图排布"""
import io, json

W, H = 2419, 1360
cols, rows = 7, 6
cw, ch, gapPin = 300, 250, 26
bw = cols * cw + (cols - 1) * gapPin
bh = rows * ch + (rows - 1) * gapPin
x0 = -(bw / 2) + cw / 2
y0 = -(bh / 2) + ch / 2

units = []
i = 0
for r in range(rows):
    for c in range(cols):
        i += 1
        jx = 6 if (r + c) % 2 == 0 else -6
        jy = -5 if (r + c) % 3 == 0 else 5
        units.append({
            'order': i - 1,
            'x': round(x0 + c * (cw + gapPin), 1),
            'y': round(y0 + r * (ch + gapPin), 1),
            'w': cw + jx,
            'h': ch + jy,
            'coverage': 0.62,
            'shape': 'island',
            'worms': 7,
            'seed': 20261116 + i * 977,
            'tone': 1.0,
            'gap': 10,
            'strata': 2,
            'outline': None,
            'custom': {'walls': {}, 'paths': {}, 'shapes': {}},
        })

scene = {
    'schema': 'silkworm-led-scene/v1',
    'createdAt': '2026-11-16T00:00:00.000Z',
    'px': {'w': W, 'h': H},
    'fps': 30,
    'frames': 900,
    'scale': 1,
    'center': {'x': 0.0, 'y': 0.0},
    'source': {'silkPaths': 'measured', 'note': '母版：7×6 规整块群，k=0.9'},
    'units': units,
}

p = r'C:\Users\54364\AppData\Local\Temp\qa-master-scene.json'
with io.open(p, 'w', encoding='utf-8') as f:
    json.dump(scene, f, ensure_ascii=False, indent=1)
print(p, len(units), 'units', bw, bh)
