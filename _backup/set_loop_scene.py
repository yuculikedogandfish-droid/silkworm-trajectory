# -*- coding: utf-8 -*-
"""把母版场景写成循环版：loop=true、cycleFrames=Total（帧数与周期严格对齐）"""
import io, json

p = r'C:\Users\54364\AppData\Local\Temp\qa-master-scene.json'
with io.open(p, encoding='utf-8') as f:
    sc = json.load(f)
sc['loop'] = True
sc['cycleFrames'] = 900
with io.open(p, 'w', encoding='utf-8') as f:
    json.dump(sc, f, ensure_ascii=False, indent=1)
print('loop scene ready', sc['px'], sc['frames'])
