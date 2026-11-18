# -*- coding: utf-8 -*-
"""把 print 版里的 img + 下一行 caption 包成 figure，避免图与说明被分页拆开"""
import io
import re

P = r"H:\tool\silkworm-trajectory\_backup\build_guide_print.py"
s = io.open(P, encoding='utf-8').read()

pat = re.compile(r'<img([^>]*)>\n(<p class="cap">.*?</p>)', re.S)
s = pat.sub(lambda m: '<figure class="fig"><img%s>\n%s</figure>' % (m.group(1), m.group(2)), s)

s = s.replace('img.crop { max-width: 62mm; }',
              'img.crop { max-width: 62mm; }\n.fig { margin: 3mm 0; break-inside: avoid; }\n.fig img { margin: 0 0 1mm; }\n.fig .cap { margin: 0; }')
io.open(P, 'w', encoding='utf-8').write(s)
print(s.count('<figure'))
