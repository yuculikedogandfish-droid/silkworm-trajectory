# -*- coding: utf-8 -*-
"""r49：修正说明书标题版本号与 s08 里残留的「时长 5–120 秒」旧口径"""
import io

P = r'H:\tool\silkworm-trajectory\docs\使用说明.html'
s = io.open(P, encoding='utf-8').read()
n0 = len(s)

pairs = [
    ('<title>蚕轨迹描图器 &amp; 数字蚕室 · 使用说明 r48</title>',
     '<title>蚕轨迹描图器 &amp; 数字蚕室 · 使用说明 r49</title>'),
    ('时长 **5–120 秒**', None),  # 仅占位，下面用 HTML 形式匹配
    ('时长 <b>5–120 秒</b>，帧率 <b>24 / 30 / 60</b>，码率 <b>8 / 16 / 28 / 40 Mbps</b>。要更长更清楚：时长按片子定、帧率 30 或 60、码率 28–40，分辨率不低于 2048×1536。',
     '帧率 <b>24 / 30 / 60</b>，码率 <b>8 / 16 / 28 / 40 Mbps</b>。'
     '<b>录多长时间由「模拟区间」决定</b>（见第 13 节），这里不再单独选时长；'
     '要更长更清楚：帧率 30 或 60、码率 28–40，分辨率不低于 2048×1536。'),
]

done = []
for old, new in pairs:
    if new is None:
        continue
    if old in s:
        s = s.replace(old, new, 1)
        done.append(old[:20])

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('len', n0, '->', len(s))
for d in done:
    print('ok', d)
print('r48 title left:', s.count('使用说明 r48'))
print('5-120 left:', s.count('5–120 秒'))
