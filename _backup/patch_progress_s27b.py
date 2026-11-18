# -*- coding: utf-8 -*-
"""把 §27.3-B / §27.5 的数值换成最终成片实测"""
import io

DOC = r'H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md'
with io.open(DOC, encoding='utf-8') as f:
    txt = f.read()

old = u"""| frame 0 → 1（普通相邻帧） | 40.35 dB | 正常帧间变化 |
| frame 40 → 41（普通相邻帧） | 42.11 dB | 正常帧间变化 |
| **frame 299 → 0（循环接缝）** | **39.82 dB** | 接缝变化与普通相邻帧同量级（±0.5 dB）⇒ 首尾接得上 |"""
new = u"""| frame 0 → 1（普通相邻帧） | 37.15 dB | 最大的一步（起始段生长最快） |
| frame 40 → 41（普通相邻帧） | 43.79 dB | 正常帧间变化 |
| **frame 299 → 0（循环接缝）** | **44.89 dB** | 三者里**最小**的一步 ⇒ 首尾接得比普通帧还顺，无跳帧 |"""
if old in txt:
    txt = txt.replace(old, new)
else:
    print('WARN B-table not found')

old5 = u"""- 目录 `G:\\led_loop_r19_10s\\`：`frame_0000..0299.png`（2419×1360）、`weave_master_prores.mov`（346.8 MB，ProRes 422 HQ **10-bit** `yuv422p10le`，300 帧 @30 fps）、`weave_playback_h264.mp4`（6.2 MB，`yuv420p` 8-bit，播放版）。
- 渲染：300 帧 / 18 分 29 秒（3.7 s/帧，42 块 @2419×1360）。"""
new5 = u"""- 目录 `G:\\led_loop_r19_10s\\`：`frame_0000..0299.png`（2419×1360）、`weave_master_prores.mov`（354.1 MB，ProRes 422 HQ **10-bit** `yuv422p10le`，300 帧 @30 fps）、`weave_playback_h264.mp4`（4.7 MB，`yuv420p` 8-bit，播放版）。
- 渲染：300 帧 ≈ 18 分钟（3.7 s/帧，42 块 @2419×1360）。中途第 263 帧无头 Chrome 整帧挂死，把整条渲染打断——已在 `render_led_frames.ps1` 加 **单帧超时 + 自动重试**（`-FrameTimeoutSec 90 -FrameRetries 2`，默认值）。续渲时第 294 帧又触发一次超时，重试一次即过；不加重试这套 900 帧的长活一定跑不完。"""
if old5 in txt:
    txt = txt.replace(old5, new5)
else:
    print('WARN 27.5 body not found')

if u'### 27.6' not in txt:
    txt = txt.rstrip('\n') + u'''

### 27.6 这一版留下的判断
- 循环片的"织"是**每块独立重织**，不是整屏一起刷新：任意时刻约 4–5 块处在 62%–80% 稀薄态。这是有意为之——否则整墙同时变黑，就是"整排闪"。
- 想让墙上永远看不到"稀薄块"，两个旋钮：`uFloor`（默认 0.62，抬到 0.85 就几乎没有稀薄感）、`growFrac`（默认 0.42，压到 0.2 就少看到生长）。
- 10-bit 已满足（ProRes 10-bit 母版）；H.264 播放版仍是 8-bit，暗场色带需要在播放器端或 LED 发送卡上处理，没有加 dither。
'''

with io.open(DOC, 'w', encoding='utf-8', newline='') as f:
    f.write(txt)
print('ok', len(txt))
