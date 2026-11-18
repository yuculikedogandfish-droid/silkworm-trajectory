# -*- coding: utf-8 -*-
"""把视频导出区从整页截图里裁出来，印刷版才看得清控件"""
import os
from PIL import Image

TMP = os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp')

for src, box in (('guide-video.png', (0, 655, 252, 900)), ('guide-video-custom.png', (0, 655, 252, 915))):
    p = os.path.join(TMP, src)
    im = Image.open(p)
    c = im.crop(box)
    out = os.path.join(TMP, src.replace('.png', '-crop.png'))
    c = c.resize((c.width * 2, c.height * 2), Image.LANCZOS)
    c.save(out)
    print(out, c.size)
