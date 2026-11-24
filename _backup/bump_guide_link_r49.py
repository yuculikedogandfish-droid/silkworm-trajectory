# -*- coding: utf-8 -*-
import io
p = r'H:\tool\silkworm-trajectory\docs\index.html'
s = io.open(p, encoding='utf-8').read()
old = 'href="使用说明.html"'
new = 'href="使用说明.html?v=r49"'
n = s.count(old)
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patched', n, 'bytes', len(s))
