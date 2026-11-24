# -*- coding: utf-8 -*-
import io
p = r'H:\tool\silkworm-trajectory\docs\使用说明.html'
s = io.open(p, encoding='utf-8').read()
print('LEN', len(s))
print('TAIL', repr(s[-260:]))
print('MAIN', s.count('</main>'))
print('TOC12', s.count('href="#s12"'))
i = s.find('id="s06"')
print('S06', repr(s[i:i+2000]))
